/**
 * AI Selected Task Analyzer - Omni Automation Plug-In
 *
 * Analyzes selected tasks (1-5) using Apple Foundation Models to provide
 * detailed per-task analysis including clarity scoring, improvements, tags,
 * priority recommendations, and missing information.
 *
 * SYSTEM MAP TAG CATEGORIZATION (v2.13.0+)
 *
 * When the System Map is present and current, tag suggestions are sourced
 * from semantically-categorized lists (sm.tags.categories.contexts /
 * energy / duration / areas) so the AI picks ONE context AND ONE energy
 * (different categories) rather than two mutually-exclusive contexts.
 * Falls back to a flat list of existing tags when the map is missing or
 * stale — the no-invention constraint still holds either way.
 *
 * people / status / uncategorized are DELIBERATELY EXCLUDED from
 * suggestion-time (user-managed; AI shouldn't auto-assign Waiting:Sarah
 * or @hold without explicit signal). Same pattern as processInbox's AI
 * pre-fill (commit 59957f7).
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - macOS 26+
 * - Apple Silicon (M1 or later)
 */

;(() => {
  const SYSTEM_MAP_TASK_NAME = "Attache System Map";
  const EXPECTED_SCHEMA_VERSION = 1;

  function section(title) {
    return `── ${title}`;
  }

  const action = new PlugIn.Action(async function (selection, sender) {
    // Load foundationModelsUtils library first
    const fmUtils = this.plugIn.library('foundationModelsUtils')

    // Check availability IMMEDIATELY before doing anything else
    if (!fmUtils.isAvailable()) {
      fmUtils.showUnavailableAlert()
      return
    }

    try {
      if (!this.plugIn.library('preferencesManager').hasPreferences()) {
        console.log('No cached preferences. Run System Setup to enable.')
      }

      // Validation
      const tasks = selection.tasks

      if (tasks.length === 0) {
        throw new Error('Please select at least one task to analyze.')
      }

      // Limit to 5 tasks to avoid long processing times
      if (tasks.length > 5) {
        throw new Error(
          'Please select 5 or fewer tasks. AI analysis can take time for multiple tasks.'
        )
      }

      // AI Analysis - session may be invalid
      const session = fmUtils.createSession(
        "You are a GTD productivity coach. Be concise and direct. Use specific GTD " +
        "vocabulary: next actions, projects, contexts. Focus on what is actionable right now."
      )

      // Collect the user's existing tag taxonomy so we can constrain the AI's
      // tag suggestions to tags that already exist. Without this constraint the
      // AI invents new tags every call, producing unbounded tag sprawl over
      // time. (User feedback on v2.5.0; design principle: automated actions
      // use the user's existing organization, not invented structure.)
      const existingTagNames = collectExistingTagNames()
      const existingTagsByName = {}
      existingTagNames.forEach(n => { existingTagsByName[n.toLowerCase()] = n })

      // Load System Map (soft — null if missing/stale, not a hard block).
      // When present, gives the AI semantic tag categorization rather than a
      // flat name list. Same soft-load pattern as processInbox v2.12.0; see
      // AGENTS.md design principle 2 (System Map for ALL conventions).
      const sm = loadSystemMapSoft()
      const categorizedTags = collectCategorizedTags(sm, existingTagNames)

      const results = []

      for (const task of tasks) {
        // Build context for the AI
        const taskContext = buildTaskContext(task)

        // Define the analysis schema using OmniFocus format
        const schema = LanguageModel.Schema.fromJSON({
          name: 'task-analysis-schema',
          properties: [
            {
              name: 'clarity',
              description: 'How clear and actionable the task is (1-10)',
            },
            {
              name: 'suggestedName',
              description: 'Improved task name if current one could be clearer',
              isOptional: true,
            },
            {
              name: 'suggestedTags',
              description: '2-3 relevant tags chosen ONLY from the user\'s existing tag list (provided in the prompt). Do not invent new tags.',
              schema: { arrayOf: { type: 'string' } },
            },
            {
              name: 'priority',
              description: 'Suggested priority level (high, medium, or low)',
            },
            {
              // Schema type intentionally omitted: Foundation Models' schema
              // language only recognizes `string` (and composite forms like
              // arrayOf). `type: 'number'` was tried in v2.8.1 and rejected
              // with "Invalid schema specification: Unrecognized Type: number".
              // The dispatch path's runtime coercion (coerceEstimateMinutes,
              // below) is the actual safety net — it accepts whatever the
              // model returns (string or number) and normalizes to a positive
              // integer or null.
              name: 'estimatedMinutes',
              description: 'Estimated time to complete in minutes (an integer like 30, 60, 90)',
              isOptional: true,
            },
            {
              name: 'improvements',
              description: 'Specific suggestions for improving the task',
              schema: { arrayOf: { type: 'string' } },
            },
            {
              name: 'missingInfo',
              description: 'Information that would help complete this task',
              isOptional: true,
              schema: { arrayOf: { type: 'string' } },
            },
          ],
        })

        // Craft the prompt. Tag section prefers semantic categorization from
        // the System Map (gives the AI signal to pick across categories rather
        // than within one) and falls back to a flat list when the map is
        // unavailable. Either way the no-invention constraint holds — a
        // downstream post-filter (constrainTagsToExisting) drops anything the
        // model hallucinated.
        const tagListSection = buildTagSection(categorizedTags)

        const prompt = `Analyze this OmniFocus task and provide structured feedback:

TASK DETAILS:
${taskContext}

${tagListSection}

Please analyze:
1. How clear and actionable is this task? (Rate 1-10)
2. Would a different task name be clearer? If yes, suggest one.
3. What 2-3 tags from the EXISTING TAGS sections above would be most relevant? Prefer one tag per category (one context, one energy, etc.) — different categories. Do NOT invent new tags — if no existing tags fit, return an empty array.
4. What priority should this have? (high/medium/low)
5. How long might this take? (in minutes)
6. What specific improvements would make this task better?
7. What information is missing that would help complete this task?

Be specific and practical in your suggestions.`

        // Get AI analysis
        const opts = new LanguageModel.GenerationOptions()
        opts.maximumResponseTokens = 400
        const response = await session.respondWithSchema(prompt, schema, opts)
        const analysis = JSON.parse(response)

        // Defence-in-depth: even with prompt + schema-description constraint,
        // the model can still hallucinate tags. Post-filter to only tags that
        // actually exist in the user's OF database (case-insensitive match,
        // re-mapped to the canonical case). This is the user-visible safety
        // net — the apply-path never offers a tag the user didn't define.
        analysis.suggestedTags = constrainTagsToExisting(
          analysis.suggestedTags,
          existingTagsByName
        )

        // Coerce estimatedMinutes to a Number. Foundation Models' schema
        // language doesn't accept `type: 'number'` (it rejects with
        // "Invalid schema specification: Unrecognized Type: number") — so
        // there's no way to pin the model's output type at the schema layer.
        // The only safety net is here: accept whatever the model returns
        // and normalize to a positive integer or null. Task.estimatedMinutes
        // is strict ("requires a Number, but was passed value of type
        // String"); every downstream consumer below sees a Number or null.
        analysis.estimatedMinutes = coerceEstimateMinutes(analysis.estimatedMinutes)

        results.push({
          task: task,
          analysis: analysis,
        })
      }

      // Display Results (with apply-path)
      const applyForm = this.plugIn.library('applyForm')
      const ofoCore = this.plugIn.library('ofoCore')
      await displayResults(results, applyForm, ofoCore)
    } catch (err) {
      new Alert(err.name, err.message).show()
      console.error(err)
    }
  })

  // Helper Functions

  /**
   * Collect every tag name in the user's OmniFocus database (walks the tag
   * tree recursively so nested tags are included). Returns canonical-case
   * names in document order, deduped. Dropped tags are excluded.
   */
  function collectExistingTagNames() {
    const out = []
    const seen = {}
    function walk(tagList) {
      tagList.forEach(t => {
        if (t.status === Tag.Status.Dropped) return
        if (!seen[t.name]) {
          seen[t.name] = true
          out.push(t.name)
        }
        if (t.children && t.children.length > 0) {
          walk(t.children)
        }
      })
    }
    walk(tags) // top-level OF global
    return out
  }

  /**
   * Soft-load the System Map for tag categorization. Mirrors
   * processInbox v2.12.0's soft-load (commit 59957f7) — null on missing
   * / corrupt / stale rather than hard-blocking, because flat-list
   * fallback still works and the no-invention constraint still holds.
   *
   * NOTE: this helper is duplicated in processInbox.js. When a third
   * consumer needs it (likely the next AI-driven action), extract to a
   * shared library (`Resources/tagTaxonomy.js`) and have both call it.
   * AGENTS.md design principle 3 sets the 3-consumer threshold for
   * extraction; we're at 2.
   */
  function loadSystemMapSoft() {
    const candidates = flattenedTasks.filter(t => t.name === SYSTEM_MAP_TASK_NAME)
    if (candidates.length === 0) return null
    let sm
    try {
      sm = JSON.parse(candidates[0].note || "{}")
    } catch (e) { return null }
    if (typeof sm.schemaVersion !== "number") return null
    if (sm.schemaVersion < EXPECTED_SCHEMA_VERSION) return null
    return sm
  }

  /**
   * Pull categorized tag names from the System Map's tags.categories.*
   * (contexts / energy / duration / areas). `existingTagNames` is passed
   * as the flat-list fallback when the map is missing or didn't categorize
   * a given category.
   *
   * DELIBERATELY EXCLUDES people / status / uncategorized — those are
   * user-managed; AI shouldn't auto-assign Waiting:Sarah or @hold without
   * explicit signal. Same exclusion as processInbox v2.12.0.
   */
  function collectCategorizedTags(sm, existingTagNames) {
    const result = {
      contexts: [],
      energy: [],
      duration: [],
      areas: [],
      flat: existingTagNames || []
    }
    if (!sm || !sm.tags || !sm.tags.categories) return result
    const cats = sm.tags.categories
    result.contexts = extractCategoryNames(cats.contexts)
    result.energy = extractCategoryNames(cats.energy)
    result.duration = extractCategoryNames(cats.duration)
    result.areas = extractCategoryNames(cats.areas)
    return result
  }

  function extractCategoryNames(catList) {
    if (!Array.isArray(catList)) return []
    return catList
      .map(entry => entry && entry.name)
      .filter(name => typeof name === "string" && name.length > 0)
      .filter(name => flattenedTags.byName(name) !== null) // user-deleted-since-refresh
  }

  /**
   * Build the EXISTING TAGS prompt section. Prefers categorized layout
   * when the System Map gave us one; falls back to flat list when not.
   * The categorized form gives the AI semantic signal to pick across
   * categories (one context AND one energy) rather than within one
   * (two mutually-exclusive contexts).
   */
  function buildTagSection(cats) {
    const sections = []
    if (cats.contexts.length > 0) sections.push(`CONTEXTS (pick 0-1, where the task happens): ${cats.contexts.join(", ")}`)
    if (cats.energy.length > 0)   sections.push(`ENERGY   (pick 0-1, effort needed):      ${cats.energy.join(", ")}`)
    if (cats.duration.length > 0) sections.push(`DURATION (pick 0-1, how long):           ${cats.duration.join(", ")}`)
    if (cats.areas.length > 0)    sections.push(`AREAS    (pick 0-1, life area):          ${cats.areas.join(", ")}`)

    if (sections.length > 0) {
      return "EXISTING TAGS (choose ONLY from these — never invent):\n" + sections.join("\n")
    }

    // Fallback: flat list (System Map missing or didn't categorize).
    if (cats.flat.length === 0) {
      return "EXISTING TAGS: (none configured — return empty suggestedTags array)"
    }
    return "EXISTING TAGS (choose ONLY from this list — never invent):\n" + cats.flat.join(", ")
  }

  /**
   * Coerce the AI's estimatedMinutes value to a positive integer or null.
   * Foundation Models' schema language doesn't accept `type: 'number'`
   * (it rejects with "Invalid schema specification: Unrecognized Type:
   * number"), so the model is free to return whatever JSON primitive
   * matches its interpretation of the description — usually a string.
   * This is the dispatch-site safety net. Returns null for empty,
   * invalid, or non-positive values (downstream truthiness guards then
   * just-work — null short-circuits the apply prompt).
   */
  function coerceEstimateMinutes(value) {
    if (value === null || value === undefined || value === '') return null
    const n = Number(value)
    if (!Number.isFinite(n) || n <= 0) return null
    return Math.round(n)
  }

  /**
   * Filter AI-suggested tag names down to those that actually exist in the
   * user's OmniFocus tag list. Case-insensitive comparison; the returned
   * names are remapped to canonical case (so dispatch via tagTask
   * always matches the right Tag object via flattenedTags.byName).
   *
   * This is the user-visible "no invented tags" gate: even if the model
   * ignores the prompt constraint, hallucinated tags are dropped before
   * they reach displayResults or the apply-path form.
   */
  function constrainTagsToExisting(suggestedTags, existingTagsByName) {
    if (!Array.isArray(suggestedTags)) return []
    const out = []
    const used = {}
    suggestedTags.forEach(raw => {
      if (typeof raw !== 'string') return
      const key = raw.trim().toLowerCase()
      if (!key) return
      const canonical = existingTagsByName[key]
      if (!canonical) return
      if (used[canonical]) return
      used[canonical] = true
      out.push(canonical)
    })
    return out
  }

  /**
   * Build comprehensive context about a task for AI analysis
   */
  function buildTaskContext(task) {
    const lines = []

    lines.push(`Name: ${task.name}`)

    if (task.note) {
      lines.push(`Note: ${task.note}`)
    }

    if (task.containingProject) {
      lines.push(`Project: ${task.containingProject.name}`)
    }

    if (task.tags.length > 0) {
      lines.push(`Current Tags: ${task.tags.map((t) => t.name).join(', ')}`)
    }

    if (task.dueDate) {
      const dueStr = task.dueDate.toLocaleDateString()
      lines.push(`Due Date: ${dueStr}`)
    }

    if (task.deferDate) {
      const deferStr = task.deferDate.toLocaleDateString()
      lines.push(`Defer Date: ${deferStr}`)
    }

    if (task.estimatedMinutes) {
      lines.push(`Current Estimate: ${task.estimatedMinutes} minutes`)
    }

    lines.push(`Flagged: ${task.flagged ? 'Yes' : 'No'}`)

    return lines.join('\n')
  }

  /**
   * Display analysis results in a formatted alert
   */
  async function displayResults(results, applyForm, ofoCore) {
    let message = ''

    results.forEach((result, index) => {
      const { task, analysis } = result

      if (index > 0) message += '\n\n' + '─'.repeat(44) + '\n\n'

      message += `${section(task.name)}\n\n`

      // Clarity score
      message += `Clarity Score: ${analysis.clarity}/10\n`

      // Suggested improvements
      if (analysis.suggestedName) {
        message += `\nSuggested Name:\n→ ${analysis.suggestedName}\n`
      }

      // Priority and estimate
      message += `\nPriority: ${analysis.priority.toUpperCase()}\n`
      if (analysis.estimatedMinutes) {
        message += `Est. Time: ${analysis.estimatedMinutes} minutes\n`
      }

      // Tags
      if (analysis.suggestedTags && analysis.suggestedTags.length > 0) {
        message += `\nSuggested Tags:\n`
        analysis.suggestedTags.forEach((tag) => {
          message += `  · ${tag}\n`
        })
      }

      // Improvements
      if (analysis.improvements && analysis.improvements.length > 0) {
        message += `\nImprovements:\n`
        analysis.improvements.forEach((improvement) => {
          message += `  · ${improvement}\n`
        })
      }

      // Missing info
      if (analysis.missingInfo && analysis.missingInfo.length > 0) {
        message += `\nMissing Information:\n`
        analysis.missingInfo.forEach((info) => {
          message += `  · ${info}\n`
        })
      }
    })

    // Show results — offer Apply Changes when libs are available and at least
    // one task has a structured suggestion that can be dispatched via ofoCore.
    const anyApplyable = results.some(hasApplyableChanges)
    const alert = new Alert('Clarify Tasks', message)
    alert.addOption('Copy to Clipboard')
    if (anyApplyable && applyForm && ofoCore) {
      alert.addOption('Apply Changes…')
    }
    alert.addOption('Done')

    const buttonIndex = await alert.show()
    if (buttonIndex === 0) {
      // Copy to clipboard
      Pasteboard.general.string = message
    } else if (anyApplyable && applyForm && ofoCore && buttonIndex === 1) {
      await applyChanges(results, applyForm, ofoCore)
    }
  }

  /**
   * Are any of the AI's suggestions for this task actually applyable?
   * (i.e., differ from the current task state).
   */
  function hasApplyableChanges(result) {
    const { task, analysis } = result
    if (analysis.suggestedName && analysis.suggestedName !== task.name) return true
    if (analysis.estimatedMinutes && analysis.estimatedMinutes !== task.estimatedMinutes) return true
    if (analysis.suggestedTags && analysis.suggestedTags.length > 0) {
      const existing = task.tags.map((t) => t.name)
      if (analysis.suggestedTags.some((t) => existing.indexOf(t) === -1)) return true
    }
    const priority = (analysis.priority || '').toLowerCase()
    if (priority === 'high' && !task.flagged) return true
    return false
  }

  /**
   * Walk each task with applyable suggestions, show per-task confirmation Form,
   * dispatch accepted changes via ofoCore. Surface a summary alert at the end.
   */
  async function applyChanges(results, applyForm, ofoCore) {
    let appliedCount = 0
    let skippedCount = 0
    const issues = []

    for (const result of results) {
      const { task, analysis } = result
      if (!hasApplyableChanges(result)) continue

      const changes = []

      if (analysis.suggestedName && analysis.suggestedName !== task.name) {
        changes.push({
          key: 'name',
          label: `Rename to: "${analysis.suggestedName}"`,
        })
      }

      if (analysis.estimatedMinutes && analysis.estimatedMinutes !== task.estimatedMinutes) {
        const currentEst = task.estimatedMinutes
          ? ` (currently ${task.estimatedMinutes} min)`
          : ''
        changes.push({
          key: 'estimate',
          label: `Set estimate: ${analysis.estimatedMinutes} min${currentEst}`,
        })
      }

      let newTags = []
      if (analysis.suggestedTags && analysis.suggestedTags.length > 0) {
        const existing = task.tags.map((t) => t.name)
        newTags = analysis.suggestedTags.filter((t) => existing.indexOf(t) === -1)
        if (newTags.length > 0) {
          changes.push({
            key: 'tags',
            label: `Add tags: ${newTags.join(', ')}`,
          })
        }
      }

      const priority = (analysis.priority || '').toLowerCase()
      if (priority === 'high' && !task.flagged) {
        changes.push({
          key: 'flag',
          label: 'Flag as high priority',
        })
      }

      if (changes.length === 0) continue

      const decision = await applyForm.confirmApply({
        itemName: task.name,
        changes: changes,
      })

      if (decision.cancelled || !applyForm.anyAccepted(decision)) {
        skippedCount++
        continue
      }

      // Single updateTask call for name/estimate/flag
      const updateArgs = { id: task.id.primaryKey }
      let hasUpdate = false
      if (decision.apply.name) {
        updateArgs.name = analysis.suggestedName
        hasUpdate = true
      }
      if (decision.apply.estimate) {
        updateArgs.estimate = analysis.estimatedMinutes
        hasUpdate = true
      }
      if (decision.apply.flag) {
        updateArgs.flagged = true
        hasUpdate = true
      }
      if (hasUpdate) {
        const upd = ofoCore.updateTask(updateArgs)
        if (!upd.success) {
          issues.push(`${task.name}: ${upd.error || 'updateTask failed'}`)
          continue
        }
      }

      // Separate tagTask call (additive, preserves existing tags)
      if (decision.apply.tags && newTags.length > 0) {
        const tagRes = ofoCore.tagTask({ id: task.id.primaryKey, add: newTags })
        if (!tagRes.success) {
          issues.push(`${task.name} (tags): ${tagRes.error || 'tagTask failed'}`)
          continue
        }
        if (tagRes.warnings && tagRes.warnings.length > 0) {
          tagRes.warnings.forEach((w) => issues.push(`${task.name}: ${w}`))
        }
      }

      appliedCount++
    }

    let summary = `Applied changes to ${appliedCount} task${appliedCount === 1 ? '' : 's'}.`
    if (skippedCount > 0) {
      summary += `\nSkipped ${skippedCount}.`
    }
    if (issues.length > 0) {
      summary += `\n\nIssues:\n  · ${issues.join('\n  · ')}`
    }
    new Alert('Clarify Tasks — Apply Summary', summary).show()
  }

  // Require tasks selected AND macOS 26+ for Apple Foundation Models
  action.validate = function (selection, sender) {
    return (
      selection.tasks.length > 0 &&
      Device.current.operatingSystemVersion.atLeast(new Version('26'))
    )
  }

  return action
})()
