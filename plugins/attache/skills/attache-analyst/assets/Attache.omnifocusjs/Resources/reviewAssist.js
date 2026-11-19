/**
 * Review Assist — one project at a time, inside OmniFocus's own review cycle.
 *
 * Target: the selected project, else the most overdue project in the review
 * queue (Project.nextReviewDate ≤ now). For that project:
 *   1. Facts computed in code (not the model): stalled, overdue, missing
 *      estimates, long-idle tasks, routines, likely duplicates.
 *   2. One Foundation Models pass in a fresh session (context never grows
 *      across projects); prompt capped by length for the 8K window.
 *   3. Structure first: if the model thinks the project is really an area
 *      (single-action list), a folder, two outcomes, or someday, an Alert
 *      asks before anything else.
 *   4. One Form, one row per remaining action (up to MAX_ROWS, most in need
 *      first): name and hints on the left (★ model suggestion, ≈ duplicate,
 *      overdue, idle, routine), a menu of every action on the right (Keep,
 *      ★ suggestion, Complete, Drop, Defer, Flag, Estimate). A row with a
 *      suggestion starts on it, others on Keep. Routines are never renamed;
 *      one suggestion per task.
 *   5. Project outcome: add a next action, change the review interval,
 *      Mark Reviewed / On hold / Drop / Complete / Leave for later.
 *   6. Nothing changes until Done; Cancel leaves the project untouched.
 *      "Next project" continues with the next one due.
 *
 * Works without Apple Intelligence (facts only). Tags are not suggested
 * yet: that would be the third copy of the tag-taxonomy helpers in
 * analyzeSelected/processInbox — extract a shared library first (AGENTS.md
 * design principle 3).
 */

;(() => {
  const PROMPT_CHAR_BUDGET = 14000   // ≈ 3.5K tokens; leaves room in the 8K window
  const MAX_TASKS_CHECKED_FOR_DUPES = 40
  const IDLE_DAYS = 365
  const DAY = 86400000

  const INTERVAL_KEYS = ['keep', '1 weeks', '2 weeks', '1 months', '3 months', '1 years']
  const INTERVAL_LABELS = ['Keep current', 'Every week', 'Every 2 weeks', 'Every month', 'Every 3 months', 'Every year']
  const ROW_LABEL_CHARS = 55
  const TITLE_WRAP_CHARS = 100
  const RULE = '─'.repeat(48)
  const MAX_ROWS = 15
  const ESTIMATE_CHOICES = [5, 15, 30, 60]

  const STRUCTURE_KINDS = ['keep', 'single-actions', 'folder', 'split', 'someday']

  const action = new PlugIn.Action(async function (selection, sender) {
    const ofoCore = this.plugIn.library('ofoCore')
    const fmUtils = this.plugIn.library('foundationModelsUtils')
    const useModel = fmUtils.isAvailable()
    const seen = {}

    try {
      let project = pickSelectedProject(selection) || nextDueProject(ofoCore, seen)
      if (!project) {
        new Alert('Review Assist', 'No projects are due for review. Select a project to review it anyway.').show()
        return
      }
      while (project) {
        seen[project.id.primaryKey] = true
        const outcome = await reviewProject(project, ofoCore, fmUtils, useModel)
        if (outcome.stopped) return
        const next = nextDueProject(ofoCore, seen)
        const alert = new Alert('Review Assist — ' + project.name, outcome.summary +
          (next ? `\n\nNext due: ${next.name}` : '\n\nNo more projects due for review.'))
        if (next) alert.addOption('Next project')
        alert.addOption('Done')
        const choice = await alert.show()
        project = next && choice === 0 ? next : null
      }
    } catch (err) {
      new Alert(err.name || 'Review Assist', err.message || String(err)).show()
      console.error(err)
    }
  })

  // ──────── Target selection ────────

  function pickSelectedProject(selection) {
    const projects = selection.projects || []
    if (projects.length === 1) return projects[0]
    const tasks = selection.tasks || []
    if (tasks.length !== 1) return null
    const only = tasks[0]
    return only.containingProject || null
  }

  function nextDueProject(ofoCore, seen) {
    const res = ofoCore.listProjectsForReview({})
    if (!res.success) return null
    const due = res.projects
      .filter(p => !seen[p.id])
      .sort((a, b) => String(a.nextReviewDate).localeCompare(String(b.nextReviewDate)))
    for (const p of due) {
      const proj = Project.byIdentifier(p.id)
      if (proj) return proj
    }
    return null
  }

  // ──────── One project ────────

  async function reviewProject(project, ofoCore, fmUtils, useModel) {
    try { URL.fromString('omnifocus:///task/' + project.id.primaryKey).open() } catch (e) { /* view only */ }

    const tasks = remainingTasks(project)
    const facts = computeFacts(project, tasks)
    const dupes = findDuplicates(tasks, ofoCore)

    let analysis = { summary: '', nextAction: '', structure: 'keep', structureReason: '', suggestions: [] }
    let modelNote = ''
    if (useModel && tasks.length > 0) {
      try {
        analysis = normalizeAnalysis(await askModel(project, tasks, facts, fmUtils), tasks, project)
      } catch (e) {
        console.error('Review Assist model error:', e)
        modelNote = 'On-device model unavailable for this project; facts only.'
      }
    } else if (!useModel) {
      modelNote = 'Apple Intelligence unavailable; facts only.'
    }

    // Structure first: it changes how the rest of the review reads.
    const structure = await askStructure(project, analysis)
    if (structure === 'stop') return { stopped: true }

    // One row per task (most in need first, shown in project order); every
    // action in each menu; the model's suggestion marked ★. Nothing applies until Done.
    const rows = pickRows(tasks, analysis.suggestions, dupes, ofoCore)
    const form = new Form()
    rows.forEach((r, i) => {
      // Per task: the name itself is the editable field (★ suggested name when
      // there is one), labelled with its hints; the action menu sits under it.
      form.addField(new Form.Field.String('name' + i, rowLabel(r, i), isRename(r) ? r.suggestion.name : r.task.name))
      // @ts-ignore — 6th arg optional at runtime
      form.addField(new Form.Field.Option('row' + i, '↳', r.choices.map(c => c.key), r.choices.map(c => c.label),
        r.suggestion && !isRename(r) ? 'suggested' : 'keep'))
    })
    form.addField(new Form.Field.String('nextAction', 'Add next action',
      facts.stalled ? (analysis.nextAction || '') : ''))
    // @ts-ignore
    form.addField(new Form.Field.Option('interval', `Review (${intervalLabel(project)})`,
      INTERVAL_KEYS, INTERVAL_LABELS, 'keep'))
    // @ts-ignore
    form.addField(new Form.Field.Option('outcome', 'Then',
      ['reviewed', 'onhold', 'drop', 'complete', 'later'],
      ['Mark reviewed', 'On hold, reviewed', 'Drop project', 'Complete project', 'Not reviewed yet'],
      'reviewed'))

    // Form titles are plain text: sections come from emoji headings, capitals
    // and a rule line; wrap() keeps one long paragraph from setting the width.
    const suggested = rows.filter(r => r.suggestion)
    const section = (heading, body) => body ? heading + '\n' + wrap(body, TITLE_WRAP_CHARS) : ''
    const title = [
      project.name.toUpperCase() + '\n' + RULE,
      section('📋  SUMMARY', [analysis.summary, factsLine(facts) + (rows.length < tasks.filter(t => !t.group).length
        ? ` · showing ${rows.length} most in need` : '')].filter(Boolean).join('\n\n')),
      section('💡  SUGGESTIONS', suggested.map(suggestionText).join('\n')),
      section('≈  POSSIBLE DUPLICATES', dupes.map(d => `"${d.name}" and "${d.other}"${d.otherProject ? ' in ' + d.otherProject : ''}`).join('\n')),
      modelNote,
      RULE + '\n✅  TASKS'
    ].filter(Boolean).join('\n\n')

    let result
    try {
      result = await form.show(title, 'Done')
    } catch (e) {
      result = null   // G3: cancel may reject
    }
    if (!result) return { stopped: true }
    const v = result.values
    const done = []
    const issues = []

    if (structure && structure !== 'keep') applyStructure(structure, project, analysis, ofoCore, done, issues)

    // Renames first (independent of the menu), then the menu action.
    rows.forEach((r, i) => {
      const name = String(v['name' + i] || '').trim()
      if (!name || name === r.task.name) return
      const res = ofoCore.updateTask({ id: r.task.task.id.primaryKey, name })
      if (res.success) done.push(`renamed "${r.task.name}" → "${name}"`)
      else issues.push(`${r.task.name}: ${res.error}`)
    })
    rows.forEach((r, i) => {
      const choice = r.choices.find(c => c.key === v['row' + i])
      if (!choice || choice.key === 'keep') return
      const res = choice.apply(r.task.task.id.primaryKey)
      if (res.success) done.push(`${choice.done} "${r.task.name}"`)
      else issues.push(`${r.task.name}: ${res.error}`)
    })

    const nextAction = String(v.nextAction || '').trim()
    if (nextAction) {
      const res = ofoCore.createTask({ name: nextAction, project: project.id.primaryKey })
      if (res.success) done.push(`added next action "${nextAction}"`)
      else issues.push(`next action: ${res.error}`)
    }

    if (v.interval && v.interval !== 'keep') {
      const parts = String(v.interval).split(' ')
      const res = ofoCore.updateProject({ id: project.id.primaryKey, reviewInterval: { steps: Number(parts[0]), unit: parts[1] } })
      if (res.success) done.push(`review interval → ${INTERVAL_LABELS[INTERVAL_KEYS.indexOf(v.interval)].toLowerCase()}`)
      else issues.push(`interval: ${res.error}`)
    }

    // Outcome last: marking reviewed uses the (possibly new) interval.
    const outcome = String(v.outcome || 'reviewed')
    if (outcome === 'drop' || outcome === 'complete') {
      const res = ofoCore.updateProject({ id: project.id.primaryKey, status: outcome === 'drop' ? 'dropped' : 'completed' })
      if (res.success) done.push(outcome === 'drop' ? 'project dropped' : 'project completed')
      else issues.push(`project: ${res.error}`)
    } else if (outcome !== 'later') {
      if (outcome === 'onhold') {
        const res = ofoCore.updateProject({ id: project.id.primaryKey, status: 'onHold' })
        if (res.success) done.push('put on hold')
        else issues.push(`on hold: ${res.error}`)
      }
      const res = ofoCore.markProjectReviewed({ id: project.id.primaryKey })
      if (res.success) {
        const nr = project.nextReviewDate
        done.push('marked reviewed' + (nr ? ` (next ${nr.toLocaleDateString()})` : ''))
      } else issues.push(`mark reviewed: ${res.error}`)
    } else {
      done.push('left for later')
    }
    if (project.status === Project.Status.Done && outcome !== 'complete') {
      issues.push('the project completed itself when its last action was completed')
    }

    let summary = done.length ? done.map(d => '· ' + d).join('\n') : 'No changes.'
    if (issues.length) summary += '\n\nIssues:\n' + issues.map(i => '· ' + i).join('\n')
    return { stopped: false, summary }
  }

  // ──────── Structure ────────

  /** Returns 'keep' | an accepted structure kind | 'stop'. Applied only after Done. */
  async function askStructure(project, analysis) {
    const kind = analysis.structure
    if (!kind || kind === 'keep') return 'keep'
    const what = {
      'single-actions': ['Make it a single-action list', 'This looks like an ongoing area of loose actions, not a project with an end.'],
      'folder': ['Add a task to restructure it into a folder', 'This looks like an area holding several smaller projects.'],
      'split': ['Add a task to split it', 'This looks like two or more outcomes mixed together.'],
      'someday': ['Put it on hold (someday)', 'Nothing here looks active; it may belong in Someday/Maybe.']
    }[kind]
    const alert = new Alert(`Structure: ${project.name}`,
      what[1] + (analysis.structureReason ? '\n\n' + analysis.structureReason : '') +
      '\n\nNothing changes until you click Done in the next step.')
    alert.addOption(what[0])
    alert.addOption('Keep as it is')
    alert.addOption('Stop reviewing')
    const choice = await alert.show()
    if (choice === 2) return 'stop'
    return choice === 0 ? kind : 'keep'
  }

  function applyStructure(kind, project, analysis, ofoCore, done, issues) {
    const id = project.id.primaryKey
    if (kind === 'single-actions') {
      const res = ofoCore.updateProject({ id, singleActions: true })
      if (res.success) done.push('made a single-action list')
      else issues.push(`single-action list: ${res.error}`)
    } else if (kind === 'someday') {
      const res = ofoCore.updateProject({ id, status: 'onHold' })
      if (res.success) done.push('put on hold (someday)')
      else issues.push(`on hold: ${res.error}`)
    } else {
      const name = kind === 'folder' ? `Restructure "${project.name}" into a folder` : `Split "${project.name}" into separate projects`
      const res = ofoCore.createTask({ name, project: id, note: analysis.structureReason || '' })
      if (res.success) done.push(`added task "${name}"`)
      else issues.push(`restructure task: ${res.error}`)
    }
  }

  /** Up to MAX_ROWS actions, most in need first, then shown in project order. */
  function pickRows(tasks, suggestions, dupes, core) {
    const bySuggestion = {}
    suggestions.forEach(s => { bySuggestion[s.index] = s })
    const dupeIds = {}
    dupes.forEach(d => { dupeIds[d.id] = d })
    const need = (t, i) => (bySuggestion[i] ? 8 : 0) + (dupeIds[t.task.id.primaryKey] ? 4 : 0) +
      (t.status === 'overdue' ? 4 : 0) + (t.idleDays > IDLE_DAYS ? 2 : 0) + (t.estimate ? 0 : 1)
    return tasks
      .map((t, i) => ({ task: t, index: i, need: need(t, i) }))
      .filter(r => !r.task.group)
      .sort((a, b) => b.need - a.need)
      .slice(0, MAX_ROWS)
      .sort((a, b) => a.index - b.index)
      .map(r => {
        r.suggestion = bySuggestion[r.index] || null
        r.dupe = dupeIds[r.task.task.id.primaryKey] || null
        r.choices = rowChoices(r, core)
        return r
      })
  }

  /** "3.  ★ drop · routine" — the task's number and hints; the name is in the field. */
  function rowLabel(r, i) {
    const t = r.task
    const hints = []
    if (r.suggestion) hints.push('★ ' + suggestionHint(r.suggestion))
    if (r.dupe) hints.push('≈ possible duplicate')
    if (t.status === 'overdue') hints.push('overdue')
    if (t.idleDays > IDLE_DAYS) {
      const years = Math.floor(t.idleDays / 365)
      hints.push(`untouched ${years} year${years === 1 ? '' : 's'}`)
    }
    if (t.repeats) hints.push('repeats')
    return `${i + 1}.` + (hints.length ? '  ' + hints.join(' · ') : '')
  }

  function suggestionHint(s) {
    if (s.kind === 'rename') return 'renamed, clear to undo'
    if (s.kind === 'estimate') return `estimate ${s.minutes} min`
    if (s.kind === 'likely-done') return 'looks done'
    return 'drop?'
  }

  /**
   * Each choice: key, menu label, past-tense summary, and how to apply it.
   * Every row carries the same labels (the widest, "Estimate 60 min", is in
   * all of them) so every menu is the same width; details of a ★ suggestion
   * are spelled out in the text above the rows.
   */
  function rowChoices(r, core) {
    const t = r.task
    const s = r.suggestion
    const out = [{ key: 'keep', label: 'Keep' }]
    if (s && s.kind !== 'rename') out.push({ key: 'suggested', label: '★ Suggested', done: suggestionDone(s), apply: id => applySuggestion(s, id, core) })
    out.push({ key: 'complete', label: 'Complete', done: 'completed', apply: id => core.completeTask({ id }) })
    if (t.repeats) out.push({ key: 'skip', label: 'Skip once', done: 'skipped once:', apply: id => core.dropTask({ id }) })
    out.push({ key: 'drop', label: 'Drop', done: t.repeats ? 'dropped routine' : 'dropped',
      apply: id => core.dropTask({ id, allOccurrences: t.repeats }) })
    out.push({ key: 'defer7', label: 'Defer 1 week', done: 'deferred 1 week:', apply: id => core.updateTask({ id, defer: daysFromNow(7) }) })
    out.push({ key: 'defer30', label: 'Defer 1 month', done: 'deferred 1 month:', apply: id => core.updateTask({ id, defer: daysFromNow(30) }) })
    const flagged = t.task.flagged
    out.push({ key: 'flag', label: flagged ? 'Unflag' : 'Flag', done: flagged ? 'unflagged' : 'flagged',
      apply: id => core.updateTask({ id, flagged: !flagged }) })
    ESTIMATE_CHOICES.forEach(m => {
      out.push({ key: 'est' + m, label: `Estimate ${m} min`, done: `estimate ${m} min on`,
        apply: id => core.updateTask({ id, estimate: m }) })
    })
    return out
  }

  function isRename(r) {
    return !!(r.suggestion && r.suggestion.kind === 'rename')
  }

  function applySuggestion(s, id, core) {
    if (s.kind === 'rename') return core.updateTask({ id, name: s.name })
    if (s.kind === 'estimate') return core.updateTask({ id, estimate: s.minutes })
    if (s.kind === 'likely-done') return core.completeTask({ id })
    return core.dropTask({ id })
  }

  function suggestionDone(s) {
    if (s.kind === 'rename') return `renamed to "${s.name}":`
    if (s.kind === 'estimate') return `estimate ${s.minutes} min on`
    return s.kind === 'likely-done' ? 'completed' : 'dropped'
  }

  /** Full text of a suggestion, for the list above the rows. */
  function suggestionText(r) {
    const s = r.suggestion
    const what = s.kind === 'rename' ? `rename to "${s.name}"`
      : s.kind === 'estimate' ? `estimate ${s.minutes} min`
      : s.kind === 'likely-done' ? 'complete (looks done)' : 'drop'
    return `★ ${r.task.name}\n      → ${what}${s.reason ? ' — ' + s.reason : ''}`
  }

  /** Hard-wrap so the dialog width is set by the rows, not by one long line. */
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

  function daysFromNow(n) {
    const d = new Date()
    d.setDate(d.getDate() + n)
    const pad = x => String(x).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
  }

  function clip(text, n) {
    const t = String(text || '').replace(/\s+/g, ' ').trim()
    return t.length > n ? t.slice(0, n - 1) + '…' : t
  }

  /** Words of 4+ letters, lowercased — used to check a rename keeps the subject. */
  function keyWords(name) {
    return (String(name).toLowerCase().match(/[\p{L}\p{N}]{4,}/gu) || [])
  }

  // ──────── Facts (deterministic) ────────

  function remainingTasks(project) {
    const now = Date.now()
    return project.flattenedTasks
      .filter(t => t.taskStatus !== Task.Status.Completed && t.taskStatus !== Task.Status.Dropped)
      .map(t => ({
        task: t,
        name: t.name,
        status: statusWord(t.taskStatus),
        group: t.hasChildren,
        repeats: !!t.repetitionRule,
        estimate: t.estimatedMinutes || null,
        idleDays: t.modified ? Math.floor((now - t.modified.getTime()) / DAY) : null,
        ageDays: t.added ? Math.floor((now - t.added.getTime()) / DAY) : null,
        note: (t.note || '').replace(/\s+/g, ' ').trim()
      }))
  }

  function statusWord(st) {
    if (st === Task.Status.Overdue) return 'overdue'
    if (st === Task.Status.DueSoon) return 'due-soon'
    if (st === Task.Status.Blocked) return 'blocked'
    return 'available'
  }

  function computeFacts(project, tasks) {
    const actions = tasks.filter(t => !t.group)
    return {
      remaining: actions.length,
      available: actions.filter(t => t.status !== 'blocked').length,
      overdue: actions.filter(t => t.status === 'overdue').length,
      noEstimate: actions.filter(t => !t.estimate).length,
      idle: actions.filter(t => t.idleDays !== null && t.idleDays > IDLE_DAYS).length,
      routines: actions.filter(t => t.repeats).length,
      stalled: project.status === Project.Status.Active && actions.filter(t => t.status !== 'blocked').length === 0,
      lastReviewed: project.lastReviewDate ? project.lastReviewDate.toLocaleDateString() : 'never'
    }
  }

  function factsLine(f) {
    const parts = [`${f.remaining} remaining`, `${f.available} available`]
    if (f.stalled) parts.unshift('STALLED: no available next action')
    if (f.overdue) parts.push(`${f.overdue} overdue`)
    if (f.noEstimate) parts.push(`${f.noEstimate} without estimate`)
    if (f.idle) parts.push(`${f.idle} untouched > 1 year`)
    if (f.routines) parts.push(`${f.routines} routine${f.routines === 1 ? '' : 's'}`)
    parts.push(`last reviewed ${f.lastReviewed}`)
    return parts.join(' · ')
  }

  function findDuplicates(tasks, ofoCore) {
    const out = []
    const pairs = {}
    tasks.filter(t => !t.group).slice(0, MAX_TASKS_CHECKED_FOR_DUPES).forEach(t => {
      const res = ofoCore.findSimilar({ id: t.task.id.primaryKey, min: 0.7, limit: 2 })
      if (!res.success) return
      res.tasks.forEach(o => {
        const key = [t.task.id.primaryKey, o.id].sort().join('|')
        if (pairs[key]) return
        pairs[key] = true
        out.push({ id: t.task.id.primaryKey, name: t.name, other: o.name, otherProject: o.project || null })
      })
    })
    return out.slice(0, 5)
  }

  function intervalLabel(project) {
    const ri = project.reviewInterval
    if (!ri || !ri.steps) return 'not set'
    const unit = String(ri.unit).replace(/s$/, '')
    return ri.steps === 1 ? `every ${unit}` : `every ${ri.steps} ${unit}s`
  }

  // ──────── Model ────────

  async function askModel(project, tasks, facts, fmUtils) {
    const session = fmUtils.createSession(
      'You are a GTD coach helping with one project in a weekly review. Be concise. ' +
      'Suggest few, clearly useful changes; an empty list is a good answer.'
    )
    const header = [
      `PROJECT: ${project.name}` + (project.parentFolder ? ` (it sits inside the folder "${project.parentFolder.name}")` : ''),
      `TYPE: ${project.containsSingletonActions ? 'single-action list' : (project.sequential ? 'sequential project' : 'parallel project')}`,
      project.note ? `PROJECT NOTE: ${project.note.replace(/\s+/g, ' ').slice(0, 300)}` : '',
      `FACTS: ${factsLine(facts)}`,
      'TASKS (T# = index):'
    ].filter(Boolean).join('\n')
    const rules = `
Return:
- summary: one or two sentences on the project's state and what would move it forward. Name tasks by their names, never by T numbers. Don't list every task, and don't restate counts or idle times (the FACTS line is shown next to your summary).
- nextAction: only if the project is STALLED, one concrete physical next action starting with a verb.
- structure: what this list really is (GTD):
  - keep: a project with a clear finished state, organized well enough.
  - single-actions: an ongoing area of unrelated actions or routines with no finished state.
  - folder: an area that holds several distinct smaller projects.
  - split: two or more different outcomes mixed in one project.
  - someday: nothing in it is actually being worked on.
  Use keep if TYPE is already single-action list and that fits.
- structureReason: when structure is not keep, one or two sentences naming which tasks would go where.
- suggestions (at most 8, at most one per task), each with index (the T number), kind and reason (a few words):
  - rename: the name is vague or not an action. Start with a verb and KEEP the specific subject
    (song, person, tool, place) word for word. Never rename tasks marked "repeats": they are routines.
  - estimate: only for tasks marked "no est"; give minutes (whole number).
  - likely-done: the name or note suggests it is already finished.
  - drop-stale: idle over a year and looks obsolete. Never for tasks marked "repeats".
Skip action-group headers (marked "group") except for rename.`

    let body = ''
    let shown = 0
    for (let i = 0; i < tasks.length; i++) {
      const t = tasks[i]
      const flags = [t.status, t.group ? 'group' : '', t.repeats ? 'repeats' : '',
        t.estimate ? `est ${t.estimate}m` : (t.group ? '' : 'no est'),
        t.idleDays !== null ? `idle ${t.idleDays}d` : ''].filter(Boolean).join(', ')
      const line = `T${i} ${t.name} [${flags}]` + (t.note ? ` — note: ${t.note.slice(0, 100)}` : '') + '\n'
      if (header.length + rules.length + body.length + line.length > PROMPT_CHAR_BUDGET) break
      body += line
      shown++
    }
    if (shown < tasks.length) body += `(${tasks.length - shown} more tasks not shown)\n`

    const schema = LanguageModel.Schema.fromJSON({
      name: 'review-assist-schema',
      properties: [
        { name: 'summary' },
        { name: 'nextAction', isOptional: true },
        { name: 'structure', schema: { name: 'review-structure-enum', anyOf: STRUCTURE_KINDS.map(k => ({ constant: k })) } },
        { name: 'structureReason', isOptional: true },
        {
          name: 'suggestions',
          schema: {
            arrayOf: {
              name: 'suggestion',
              properties: [
                { name: 'index', schema: { type: 'integer' } },
                { name: 'kind', schema: { name: 'review-kind-enum', anyOf: [
                  { constant: 'rename' }, { constant: 'estimate' }, { constant: 'likely-done' }, { constant: 'drop-stale' }] } },
                { name: 'name', isOptional: true },
                { name: 'minutes', isOptional: true, schema: { type: 'integer' } },
                { name: 'reason', isOptional: true }
              ]
            },
            maximumElements: 8
          }
        }
      ]
    })
    const opts = new LanguageModel.GenerationOptions()
    opts.maximumResponseTokens = 800
    const response = await session.respondWithSchema(header + '\n' + body + rules, schema, opts)
    return JSON.parse(response)
  }

  /** G6: normalize once at parse time; drop anything that doesn't fit the task list. */
  function normalizeAnalysis(raw, tasks, project) {
    const out = {
      summary: typeof raw.summary === 'string' ? raw.summary.trim() : '',
      nextAction: typeof raw.nextAction === 'string' ? raw.nextAction.trim() : '',
      structure: STRUCTURE_KINDS.indexOf(raw.structure) >= 0 ? raw.structure : 'keep',
      structureReason: typeof raw.structureReason === 'string' ? raw.structureReason.trim().slice(0, 400) : '',
      suggestions: []
    }
    if (out.structure === 'single-actions' && project.containsSingletonActions) out.structure = 'keep'
    const used = {}
    const list = Array.isArray(raw.suggestions) ? raw.suggestions : []
    list.forEach(s => {
      const index = Number(s && s.index)
      if (!Number.isInteger(index) || index < 0 || index >= tasks.length) return
      const t = tasks[index]
      const kind = String(s.kind || '')
      if (used[index]) return   // one change per task: the first suggestion wins
      const reason = typeof s.reason === 'string' ? s.reason.trim().slice(0, 80) : ''
      if (kind === 'rename') {
        const name = typeof s.name === 'string' ? s.name.trim() : ''
        if (t.repeats || name.length < 3 || name.length > 120 || name.toLowerCase() === t.name.toLowerCase()) return
        // Must keep the subject: share at least one significant word with the old name.
        const oldWords = keyWords(t.name)
        if (oldWords.length && !keyWords(name).some(w => oldWords.indexOf(w) >= 0)) return
        out.suggestions.push({ index, kind, name, reason })
      } else if (kind === 'estimate') {
        const minutes = Math.round(Number(s.minutes))
        if (t.group || t.estimate || !Number.isFinite(minutes) || minutes <= 0 || minutes > 480) return
        out.suggestions.push({ index, kind, minutes, reason })
      } else if (kind === 'likely-done' || kind === 'drop-stale') {
        if (t.group || t.repeats) return
        out.suggestions.push({ index, kind, reason })
      } else return
      used[index] = true
    })
    return out
  }

  action.validate = function (selection, sender) {
    return true
  }

  return action
})()
