/**
 * Weekly Review — your own OmniFocus checklist, with insight on each item.
 *
 * Rebuilt for #269 (replaces the 7-step walk-through; #268 decision "Weekly
 * Review rebuilt on the Review perspective + push").
 *
 * OmniFocus is the source of truth: the steps are the open items of this
 * week's copy of your weekly-review routine (a repeating project), in order,
 * and progress is what's ticked there. Attache keeps no step list of its own.
 *
 * Each run shows your groups' progress and the first unticked item, with the
 * insight that matches it (by keywords in its name — see KINDS): inbox facts,
 * a Waiting For summary with "not really waiting" and "chase first", projects
 * due for review, stalled projects, the past week, three priorities, on-hold
 * projects, the coming week. Buttons act on the checklist itself:
 *   Open …     the matching perspective, or the item's own group (e.g. Get
 *              Clear) when no perspective fits — work there, run again
 *   Mark done  ticks the item
 *   Skip       moves on to the next item for this run; changes nothing
 * An item is ticked automatically only when the data proves it done (nothing
 * due for review, no stalled projects).
 *
 * When the checklist is finished (or Finish now): the report — what changed
 * during the review, priorities, past and coming
 * week, unticked items, "what got in the way?" — saved to the copy's note, the clipboard and
 * a device-local log for the weekly-note push (task 5); then the copy is
 * completed so the routine repeats.
 *
 * Device-local prefs hold only caches: the routine id, when this copy's review
 * started (for "during this review"), and model answers.
 */

;(() => {
  const PREFS_ID = 'com.totallytools.omnifocus.attache'
  const ROUTINE_KEY = 'weeklyReview_projectId'
  const CACHE_KEY = 'weeklyReview_cache'
  const REPORTS_KEY = 'weeklyReports'
  const REPORTS_MAX = 8
  const WAITING_STALE_DAYS = 14
  const ON_HOLD_UNREVIEWED_DAYS = 90
  const NAME_PATTERN = /weekly review/i
  const LIST_MAX = 5
  const TITLE_WRAP_CHARS = 100
  const RULE = '─'.repeat(48)
  const DAY = 86400000
  const SYSTEM_MAP_TASK = 'Attache System Map'

  const DESTINATIONS = {
    waiting: { label: 'Waiting For', custom: /waiting/i },
    review: { label: 'Review (then Attache › Review Assist)', builtIn: 'Review' },
    stalled: { label: 'Stalled projects', custom: /stalled/i },
    reflection: { label: 'Past week', custom: /weekly reflection|^completed$/i },
    active: { label: 'Active projects', custom: /projects.*active/i },
    inactive: { label: 'On-hold projects', custom: /inactive|on.?hold/i },
    forecast: { label: 'Forecast', builtIn: 'Forecast' }
  }

  /**
   * Checklist item kinds, matched in order against the item name, then
   * "group › item". detail(f, cache) → insight text; auto(f) → true when the
   * data proves the item done (it is then ticked).
   */
  const KINDS = [
    { key: 'waiting', match: /waiting/i, dest: 'waiting', insight: true,
      detail: (f, cache) => waitingDetail(f, cache.waiting) },
    { key: 'stalled', match: /stalled/i, dest: 'stalled',
      detail: f => f.stalled.length ? `Stalled (no next action): ${f.stalled.length}\n` + list(f.stalled.map(p => p.name)) +
        '\n\nGive each a next action, put it on hold, or drop it.' : 'No stalled projects.',
      auto: f => f.stalled.length === 0 },
    { key: 'review', match: /review perspective|projects? for review/i, dest: 'review',
      detail: f => f.dueForReview.length ? `Projects due for review: ${f.dueForReview.length} of ${f.activeProjects} active\n` +
        list(f.dueForReview.map(p => p.name)) + '\n\nSelect one in Review and run Attache › Review Assist.' : 'No projects due for review.',
      auto: f => f.dueForReview.length === 0 },
    { key: 'someday', match: /rainy day|someday/i, dest: 'inactive',
      detail: f => f.onHoldUnreviewed.length ? `On hold, not reviewed in ${ON_HOLD_UNREVIEWED_DAYS}+ days: ${f.onHoldUnreviewed.length}\n` +
        list(f.onHoldUnreviewed.map(p => p.name)) + '\n\nActivate, keep on hold, or drop each.' : `Every on-hold project was reviewed in the last ${ON_HOLD_UNREVIEWED_DAYS} days.` },
    { key: 'reflect', match: /reflect|past week/i, dest: 'reflection',
      detail: f => pastWeek(f) },
    { key: 'prioritize', match: /prioriti/i, dest: 'active', priorities: true,
      detail: (f, cache) => (cache.priorities && cache.priorities.length
        ? '💡  Priorities for the week\n' + cache.priorities.map((p, i) => `${i + 1}. ${p}`).join('\n') + '\n\n' : '') + comingWeek(f) },
    { key: 'plan', match: /weekly plan|forecast|coming week/i, dest: 'forecast',
      detail: f => comingWeek(f) },
    { key: 'inbox', match: /get clear|inbox|brain dump|reminders|capture/i, dest: 'group',
      detail: f => [
        f.inbox ? `Inbox: ${f.inbox} item${f.inbox === 1 ? '' : 's'}, oldest ${f.inboxOldestDays} days.` : 'Inbox is empty.',
        f.completedByProject.length ? 'Open-loop triggers — where you worked this week (any follow-ups, promises, loose ends?):\n' +
          list(f.completedByProject.map(p => `${p.name} (${p.count} done)`)) : ''
      ].filter(Boolean).join('\n\n') }
  ]

  const action = new PlugIn.Action(async function (selection, sender) {
    const ofoCore = this.plugIn.library('ofoCore')
    const fmUtils = this.plugIn.library('foundationModelsUtils')
    try {
      const prefs = new Preferences(PREFS_ID)   // G4: construct lazily
      const routine = await findRoutine(prefs)
      if (!routine) return
      const cache = loadCache(prefs, routine)

      const skippedThisRun = {}   // in memory only: Skip changes nothing in OmniFocus
      for (;;) {
        const f = gatherFacts(ofoCore, new Date(cache.startedAt))
        const items = checklist(routine)
        const next = () => items.find(i => i.open && !skippedThisRun[i.task.id.primaryKey])
        let current = next()

        // Tick items the data proves done, then look again.
        const autoTicked = []
        while (current && current.kind && current.kind.auto && current.kind.auto(f)) {
          const res = ofoCore.completeTask({ id: current.task.id.primaryKey })
          if (!res.success) break
          autoTicked.push(current.label)
          current.open = false
          current = next()
        }
        if (!current) return await finish(ofoCore, fmUtils, prefs, routine, cache)

        const kind = current.kind
        if (kind && kind.insight && !('waiting' in cache) && fmUtils.isAvailable()) {
          try { cache.waiting = await waitingInsight(fmUtils, f) } catch (e) { cache.waiting = null; console.error('Weekly Review insight:', e) }
          saveCache(prefs, cache)
        }
        if (kind && kind.priorities && !('priorities' in cache) && fmUtils.isAvailable()) {
          try { cache.priorities = await askPriorities(fmUtils, f) } catch (e) { cache.priorities = []; console.error('Weekly Review priorities:', e) }
          saveCache(prefs, cache)
        }

        // Where "Open" goes: the matching perspective, else the item's own group in the checklist.
        const container = current.groupTask || current.task
        const perspective = kind && kind.dest !== 'group' ? findPerspective(DESTINATIONS[kind.dest]) : null
        const openLabel = perspective ? `Open ${DESTINATIONS[kind.dest].label}` : `Open ${container.name.trim()}`
        const form = new Form()
        const keys = ['open', 'done', 'skip', 'finish']
        const labels = [openLabel, 'Mark done (tick it)', 'Skip for now (no change)', 'Finish the review now']
        // @ts-ignore — 6th arg optional at runtime
        form.addField(new Form.Field.Option('next', 'Next', keys, labels, keys[0]))

        const note = String(current.task.note || '').trim()
        const title = [
          `${routine.name.toUpperCase()} — ${current.label.toUpperCase()}\n${RULE}`,
          progressLines(routine, current),
          autoTicked.length ? 'Ticked for you (the data shows they\'re done): ' + autoTicked.join('; ') : '',
          RULE + '\n' + wrap([kind ? kind.detail(f, cache) : '', note ? '📝  ' + note : '', stillToDo(items, current)].filter(Boolean).join('\n\n') || current.label, TITLE_WRAP_CHARS)
        ].filter(Boolean).join('\n\n')
        let result
        try {
          result = await form.show(title, 'Go')
        } catch (e) {
          return   // G3: cancel may reject; nothing to save — OmniFocus holds the progress
        }
        if (!result) return
        const v = result.values
        if (v.next === 'open') { if (perspective) openPerspective(perspective); else openTask(container); return }
        if (v.next === 'finish') return await finish(ofoCore, fmUtils, prefs, routine, cache)
        const id = current.task.id.primaryKey
        if (v.next === 'skip') {
          skippedThisRun[id] = true
        } else {
          const res = ofoCore.completeTask({ id })
          if (!res.success) { new Alert('Weekly Review', res.error).show(); return }
        }
      }
    } catch (err) {
      new Alert(err.name || 'Weekly Review', err.message || String(err)).show()
      console.error(err)
    }
  })

  // ──────── Checklist (OmniFocus is the truth) ────────

  /** Leaf items of the copy in outline order: { task, label, group, open, kind }. */
  function checklist(routine) {
    const out = []
    const walk = (tasks, parent) => tasks.forEach(t => {
      if (t.hasChildren) walk(t.children, t)
      else {
        const group = parent ? parent.name.trim() : null
        const label = (group ? group + ' › ' : '') + t.name.trim()
        out.push({ task: t, label, group, groupTask: parent, open: isOpen(t), kind: KINDS.find(k => k.match.test(t.name)) || KINDS.find(k => k.match.test(label)) || null })
      }
    })
    walk(routine.task.children, null)
    return out
  }

  /** Reminder of the rest of the current group: "Still to do in Get Clear: ○ Check Reminders — <note>" */
  function stillToDo(items, current) {
    if (!current.groupTask) return ''
    const rest = items.filter(i => i.groupTask === current.groupTask && i.open && i !== current)
    if (!rest.length) return ''
    return `Still to do in ${current.group}:\n` + rest.map(i => {
      const first = String(i.task.note || '').split('\n')[0].trim()
      return '○ ' + i.task.name.trim() + (first ? ' — ' + first.slice(0, 80) : '')
    }).join('\n')
  }

  /** "✓ Block 1 hour…", "→ Get Clear — 1 of 4", "○ Get Current — 0 of 5" */
  function progressLines(routine, current) {
    return routine.task.children.map(t => {
      if (!t.hasChildren) {
        const sym = t === current.task ? '→' : isOpen(t) ? '○' : (t.taskStatus === Task.Status.Dropped ? '–' : '✓')
        return `${sym}  ${t.name.trim()}`
      }
      const leaves = t.flattenedTasks.filter(x => !x.hasChildren)
      const closed = leaves.filter(x => !isOpen(x)).length
      const here = leaves.some(x => x === current.task)
      const sym = here ? '→' : closed === leaves.length ? '✓' : '○'
      return `${sym}  ${t.name.trim()} — ${closed} of ${leaves.length}`
    }).join('\n')
  }

  function isOpen(t) {
    return t.taskStatus !== Task.Status.Completed && t.taskStatus !== Task.Status.Dropped
  }

  // ──────── Facts (deterministic) ────────

  function gatherFacts(ofoCore, started) {
    const now = Date.now()
    const weekAgo = new Date(now - 7 * DAY)
    const weekAhead = new Date(now + 7 * DAY)
    const sm = loadSystemMap()
    const f = {}

    const inboxOpen = inbox.filter(isOpen)
    f.inbox = inboxOpen.length
    f.inboxOldestDays = inboxOpen.reduce((m, t) => t.added ? Math.max(m, Math.floor((now - t.added.getTime()) / DAY)) : m, 0)

    f.waiting = null
    const waitingTag = sm && sm.conventions ? sm.conventions.waitingTag : null
    if (waitingTag) {
      const all = ofoCore.listWaitingFor({ tag: waitingTag })
      const stale = ofoCore.listWaitingFor({ tag: waitingTag, ageThresholdDays: WAITING_STALE_DAYS })
      if (all.success) f.waiting = { count: all.count, stale: stale.success ? stale.tasks.map(t => ({
        id: t.id, name: t.name, project: t.project || null, note: String(t.note || '').replace(/\s+/g, ' ').trim(),
        days: t.modified ? Math.floor((now - Date.parse(t.modified)) / DAY) : null
      })) : [] }
    }

    const due = ofoCore.listProjectsForReview({})
    f.dueForReview = due.success ? due.projects.map(p => ({ id: p.id, name: p.name })) : []

    const active = flattenedProjects.filter(p => p.status === Project.Status.Active && !inDroppedFolder(p))
    f.activeProjects = active.length
    f.stalled = active.filter(p => !p.containsSingletonActions && p.flattenedTasks.length > 0 && !hasNextAction(p))
      .map(p => ({ id: p.id.primaryKey, name: p.name }))

    const done = ofoCore.listRecentlyCompleted({ sinceDate: weekAgo.toISOString() })
    const byProject = {}
    if (done.success) done.tasks.forEach(t => { const k = t.project || 'Inbox'; byProject[k] = (byProject[k] || 0) + 1 })
    f.completedWeek = done.success ? done.count : 0
    f.completedByProject = Object.keys(byProject).map(k => ({ name: k, count: byProject[k] })).sort((a, b) => b.count - a.count)

    const remaining = flattenedTasks.filter(t => isOpen(t) && !t.hasChildren)
    f.overdue = remaining.filter(t => t.taskStatus === Task.Status.Overdue).map(t => t.name)
    f.dueSoon = remaining.filter(t => t.dueDate && t.dueDate.getTime() >= now && t.dueDate <= weekAhead).map(t => t.name)

    const holdCutoff = now - ON_HOLD_UNREVIEWED_DAYS * DAY
    f.onHoldUnreviewed = flattenedProjects.filter(p => p.status === Project.Status.OnHold && !inDroppedFolder(p) &&
      (!p.lastReviewDate || p.lastReviewDate.getTime() < holdCutoff)).map(p => ({ id: p.id.primaryKey, name: p.name }))

    const since = d => d && d.getTime() >= started.getTime()
    const changed = flattenedProjects.filter(p => p.task && since(p.task.modified))
    f.during = {
      reviewed: flattenedProjects.filter(p => since(p.lastReviewDate)).map(p => p.name),
      completed: flattenedProjects.filter(p => p.status === Project.Status.Done && since(p.completionDate)).map(p => p.name),
      dropped: flattenedProjects.filter(p => p.status === Project.Status.Dropped && since(p.dropDate)).map(p => p.name),
      onHold: changed.filter(p => p.status === Project.Status.OnHold).map(p => p.name),
      tasksCompleted: flattenedTasks.filter(t => since(t.completionDate)).length,
      tasksAdded: flattenedTasks.filter(t => since(t.added)).length
    }
    const named = {}
    ;['reviewed', 'completed', 'dropped', 'onHold'].forEach(k => f.during[k].forEach(n => { named[n] = true }))
    f.during.otherChanged = changed.filter(p => !named[p.name] && p.status === Project.Status.Active).map(p => p.name)
    return f
  }

  function hasNextAction(p) {
    return p.flattenedTasks.some(t => t.taskStatus === Task.Status.Available || t.taskStatus === Task.Status.Next)
  }

  function inDroppedFolder(p) {
    for (let f = p.parentFolder; f; f = f.parent) if (f.status === Folder.Status.Dropped) return true
    return false
  }

  function loadSystemMap() {
    const t = flattenedTasks.find(x => x.name === SYSTEM_MAP_TASK)
    if (!t) return null
    try { return JSON.parse(t.note || '{}') } catch (e) { return null }
  }

  function pastWeek(f) {
    return f.completedWeek
      ? `${f.completedWeek} tasks completed in the last 7 days. Most in:\n` + list(f.completedByProject.map(p => `${p.name} (${p.count})`))
      : 'Nothing completed in the last 7 days.'
  }

  function comingWeek(f) {
    return [
      f.overdue.length ? `Overdue: ${f.overdue.length}\n` + list(f.overdue) : 'Nothing overdue.',
      f.dueSoon.length ? `Due in the next 7 days: ${f.dueSoon.length}\n` + list(f.dueSoon) : 'Nothing due in the next 7 days.'
    ].join('\n')
  }

  // ──────── Waiting For: summary and recommendations ────────

  /** Facts in code; the model only names "not really waiting" and "chase first". */
  function waitingDetail(f, insight) {
    if (!f.waiting) return 'No waiting tag in the System Map (run Attache › Setup).'
    const stale = f.waiting.stale
    if (!stale.length) return `Waiting For: ${f.waiting.count} items, none untouched over ${WAITING_STALE_DAYS} days.`
    const bucket = (lo, hi) => stale.filter(t => t.days !== null && t.days >= lo && t.days < hi).length
    const byProject = {}
    stale.forEach(t => { const k = t.project || 'no project'; byProject[k] = (byProject[k] || 0) + 1 })
    const top = Object.keys(byProject).sort((a, b) => byProject[b] - byProject[a]).slice(0, 4).map(k => `${k} (${byProject[k]})`)
    const oldest = stale.slice().sort((a, b) => (b.days || 0) - (a.days || 0)).slice(0, 3)
    const out = [
      `📊  ${stale.length} of ${f.waiting.count} waiting items untouched over ${WAITING_STALE_DAYS} days: ` +
        `${bucket(WAITING_STALE_DAYS, 30)} under a month, ${bucket(30, 182)} one to six months, ${bucket(182, 100000)} over six months.`,
      'Most in: ' + top.join(', ') + '.',
      'Oldest: ' + oldest.map(t => `${t.name} (${t.days} days)`).join('; ') + '.'
    ]
    if (insight) {
      const current = {}
      stale.forEach(t => { current[t.name] = true })
      const pick = names => (names || []).filter(n => current[n])
      if (insight.summary) out.push('💡  ' + insight.summary)
      const notWaiting = pick(insight.notWaiting)
      if (notWaiting.length) out.push(`Look like your own tasks, not waiting on anyone — consider removing the waiting tag or moving them to Someday (${notWaiting.length}):\n` + list(notWaiting))
      const chase = pick(insight.chase)
      if (chase.length) out.push('Chase first:\n' + list(chase))
    }
    return out.join('\n\n')
  }

  async function waitingInsight(fmUtils, f) {
    const stale = (f.waiting && f.waiting.stale) || []
    if (!stale.length) return null
    const session = fmUtils.createSession('You are a GTD coach. A waiting-for item means someone else owes the user something. Be concise.')
    let body = ''
    stale.forEach((t, i) => {
      const line = `W${i} ${t.name} [${t.project || 'no project'}; untouched ${t.days} days]` + (t.note ? ` — note: ${t.note.slice(0, 80)}` : '') + '\n'
      if (body.length + line.length < 9000) body += line
    })
    const schema = LanguageModel.Schema.fromJSON({
      name: 'waiting-insight-schema',
      properties: [
        { name: 'summary' },
        { name: 'notWaiting', schema: { arrayOf: { name: 'index', schema: { type: 'integer' } }, maximumElements: 20 } },
        { name: 'chase', schema: { arrayOf: { name: 'index', schema: { type: 'integer' } }, maximumElements: 3 } }
      ]
    })
    const opts = new LanguageModel.GenerationOptions()
    opts.maximumResponseTokens = 400
    const prompt = 'WAITING-FOR ITEMS (W# = index):\n' + body + `
Return:
- summary: one or two sentences on the state of this list and what to do about it.
- notWaiting: indexes of items that look like the user's own work (no other person, company or delivery involved), so they don't belong on a waiting list.
- chase: up to three indexes of real waiting items most worth following up now.`
    const raw = JSON.parse(await session.respondWithSchema(prompt, schema, opts))
    const idx = a => (Array.isArray(a) ? a : []).map(Number).filter(i => Number.isInteger(i) && i >= 0 && i < stale.length)
    const names = a => idx(a).map(i => stale[i].name)
    return { summary: typeof raw.summary === 'string' ? raw.summary.trim() : '', notWaiting: names(raw.notWaiting), chase: names(raw.chase) }
  }

  async function askPriorities(fmUtils, f) {
    const session = fmUtils.createSession('You are a GTD coach helping with a weekly review. Be concrete and brief.')
    const facts = [
      `Inbox ${f.inbox}; waiting ${f.waiting ? f.waiting.count : '?'} (stale: ${f.waiting ? f.waiting.stale.slice(0, 5).map(t => t.name).join('; ') : ''})`,
      `Projects due for review ${f.dueForReview.length} of ${f.activeProjects}`,
      `Stalled: ${f.stalled.slice(0, 10).map(p => p.name).join('; ') || 'none'}`,
      `Completed this week ${f.completedWeek}, most in: ${f.completedByProject.slice(0, 5).map(p => p.name).join('; ')}`,
      `Overdue: ${f.overdue.slice(0, 10).join('; ') || 'none'}`,
      `Due next 7 days: ${f.dueSoon.slice(0, 10).join('; ') || 'none'}`
    ].join('\n')
    const schema = LanguageModel.Schema.fromJSON({
      name: 'weekly-priorities-schema',
      properties: [{ name: 'priorities', schema: { arrayOf: { name: 'priority' }, maximumElements: 3 } }]
    })
    const opts = new LanguageModel.GenerationOptions()
    opts.maximumResponseTokens = 300
    const prompt = facts + '\n\nGive at most three priorities for the coming week, each one sentence naming the specific task or project and the action. Prefer clearing stale waiting items, stalled projects and overdue work over new work.'
    const raw = JSON.parse(await session.respondWithSchema(prompt, schema, opts))
    return (Array.isArray(raw.priorities) ? raw.priorities : []).filter(p => typeof p === 'string' && p.trim()).map(p => p.trim()).slice(0, 3)
  }

  // ──────── Finish: report ────────

  async function finish(ofoCore, fmUtils, prefs, routine, cache) {
    const started = new Date(cache.startedAt)
    const f = gatherFacts(ofoCore, started)
    if (!('priorities' in cache) && fmUtils.isAvailable()) {
      try { cache.priorities = await askPriorities(fmUtils, f) } catch (e) { cache.priorities = [] }
    }
    const items = checklist(routine)
    const skipped = items.filter(i => i.task.taskStatus === Task.Status.Dropped).map(i => i.label)
    const unticked = items.filter(i => i.open).map(i => i.label)
    const report = buildReport(f, cache.priorities || [], started, skipped, unticked)

    const form = new Form()
    form.addField(new Form.Field.String('friction', 'What got in the way?', ''))
    // @ts-ignore
    form.addField(new Form.Field.Option('then', 'Then', ['complete', 'save', 'continue'],
      [`Save report and complete ${routine.name}`, 'Save report, keep the checklist open', 'Not yet'], 'complete'))
    let result
    try {
      result = await form.show(`${routine.name.toUpperCase()} — REPORT\n${RULE}\n\n` + wrap(report, TITLE_WRAP_CHARS), 'Done')
    } catch (e) {
      result = null
    }
    if (!result || result.values.then === 'continue') return

    const friction = String(result.values.friction || '').trim()
    const full = report + (friction ? '\n\n🪨  WHAT GOT IN THE WAY\n' + friction : '')
    const saved = saveReport(prefs, ofoCore, routine, full, { f, skipped, unticked, friction, started })
    Pasteboard.general.string = full
    prefs.write('lastReviewed_weekly', new Date().toISOString())

    let msg = 'Report copied to the clipboard' + (saved ? ` and saved in the note of ${routine.name}.` : '.')
    if (result.values.then === 'complete') {
      if (routine.status !== Project.Status.Done) routine.markComplete(null)
      prefs.write(CACHE_KEY, '')
      const next = activeRepeating().find(p => p.name === routine.name && p.id.primaryKey !== routine.id.primaryKey)
      msg += next ? `\n\nNext weekly review: ${(next.dueDate || next.deferDate || new Date()).toLocaleDateString()}.`
        : '\n\nNo next copy found — check the routine\'s repeat.'
    }
    new Alert('Weekly Review saved', msg).show()
  }

  function buildReport(f, priorities, started, skipped, unticked) {
    const s = []
    const d = f.during
    const lines = [`Started ${started.toLocaleString()} · ${d.tasksCompleted} tasks completed · ${d.tasksAdded} added · ${d.reviewed.length} projects reviewed`]
    if (d.reviewed.length) lines.push('Reviewed: ' + d.reviewed.slice(0, 12).join(', ') + (d.reviewed.length > 12 ? '…' : ''))
    if (d.completed.length) lines.push('Completed: ' + d.completed.join(', '))
    if (d.dropped.length) lines.push('Dropped: ' + d.dropped.join(', '))
    if (d.onHold.length) lines.push('Put on hold or changed while on hold: ' + d.onHold.join(', '))
    if (d.otherChanged.length) lines.push('Other projects changed: ' + d.otherChanged.slice(0, 8).join(', ') + (d.otherChanged.length > 8 ? '…' : ''))
    s.push('🔁  DURING THIS REVIEW\n' + lines.join('\n'))
    if (skipped.length || unticked.length) {
      s.push('🧾  CHECKLIST\n' + skipped.map(x => '– dropped: ' + x).concat(unticked.map(x => '○ not done: ' + x)).join('\n'))
    }
    if (priorities.length) s.push('💡  PRIORITIES FOR THE WEEK\n' + priorities.map((p, i) => `${i + 1}. ${p}`).join('\n'))
    s.push('🏆  PAST WEEK\n' + pastWeek(f))
    s.push('📅  COMING WEEK\n' + comingWeek(f))
    return s.join('\n\n')
  }

  // ──────── Routine, cache, saving ────────

  async function findRoutine(prefs) {
    const saved = prefs.readString(ROUTINE_KEY)
    if (saved) {
      const p = Project.byIdentifier(saved)
      if (p && p.status === Project.Status.Active) return p
      if (p) {
        const live = activeRepeating().find(x => x.name === p.name)
        if (live) { prefs.write(ROUTINE_KEY, live.id.primaryKey); return live }
      }
    }
    const repeating = activeRepeating()
    const named = repeating.filter(p => NAME_PATTERN.test(p.name))
    if (named.length === 1) { prefs.write(ROUTINE_KEY, named[0].id.primaryKey); return named[0] }
    const candidates = named.length ? named : repeating
    if (!candidates.length) {
      new Alert('Weekly Review', 'Weekly Review works through your own weekly-review checklist: a repeating project. None was found.').show()
      return null
    }
    const form = new Form()
    // @ts-ignore
    form.addField(new Form.Field.Option('pick', 'Routine', candidates.map(p => p.id.primaryKey), candidates.map(p => p.name), candidates[0].id.primaryKey))
    let result
    try {
      result = await form.show('Which repeating project is your weekly review checklist?', 'Use it')
    } catch (e) {
      result = null
    }
    if (!result) return null
    const p = Project.byIdentifier(result.values.pick)
    if (p) prefs.write(ROUTINE_KEY, p.id.primaryKey)
    return p
  }

  function activeRepeating() {
    return flattenedProjects.filter(p => p.status === Project.Status.Active && p.repetitionRule)
  }

  /** Per-copy cache: when this copy's review started, and model answers. */
  function loadCache(prefs, routine) {
    let c = null
    try { c = JSON.parse(prefs.readString(CACHE_KEY) || 'null') } catch (e) { c = null }
    if (!c || c.routineId !== routine.id.primaryKey) {
      c = { routineId: routine.id.primaryKey, startedAt: new Date().toISOString() }
      saveCache(prefs, c)
    }
    return c
  }

  function saveCache(prefs, c) {
    prefs.write(CACHE_KEY, JSON.stringify(c))
  }

  /** Note on this week's copy + device-local log for the weekly-note push (task 5). */
  function saveReport(prefs, ofoCore, routine, text, data) {
    let log = []
    try { log = JSON.parse(prefs.readString(REPORTS_KEY) || '[]') } catch (e) { log = [] }
    log.push({ date: new Date().toISOString(), started: data.started.toISOString(), routineId: routine.id.primaryKey,
      text, skipped: data.skipped, unticked: data.unticked, friction: data.friction, during: data.f.during })
    prefs.write(REPORTS_KEY, JSON.stringify(log.slice(-REPORTS_MAX)))
    const res = ofoCore.updateTask({ id: routine.task.id.primaryKey, noteAppend: `Weekly review report ${new Date().toLocaleDateString()}\n\n` + text })
    return res.success
  }

  // ──────── Perspectives, text ────────

  function findPerspective(d) {
    if (!d) return null
    if (d.builtIn) return Perspective.BuiltIn[d.builtIn] || null
    return Perspective.Custom.all.find(p => d.custom.test(p.name)) || null
  }

  /** Show a checklist group (or item) in OmniFocus. */
  function openTask(t) {
    try {
      URL.fromString('omnifocus:///task/' + t.id.primaryKey).open()
    } catch (e) {
      console.error('Weekly Review open task:', e)
    }
  }

  function openPerspective(p) {
    try {
      document.windows[0].perspective = p
    } catch (e) {
      console.error('Weekly Review open perspective:', e)
    }
  }

  function list(items) {
    return items.slice(0, LIST_MAX).map(n => '· ' + n).join('\n') +
      (items.length > LIST_MAX ? `\n· …and ${items.length - LIST_MAX} more` : '')
  }

  function wrap(text, width) {
    return String(text).split('\n').map(line => {
      const out = []
      let cur = ''
      line.split(' ').forEach(word => {
        if (cur && (cur + ' ' + word).length > width) { out.push(cur); cur = word } else cur = cur ? cur + ' ' + word : word
      })
      out.push(cur)
      return out.join('\n')
    }).join('\n')
  }

  action.validate = function (selection, sender) {
    return true
  }

  return action
})()
