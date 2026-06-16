/**
 * AI Selected Task Analyzer - Omni Automation Plug-In
 *
 * Analyzes selected tasks (1-5) using Apple Foundation Models to provide
 * detailed per-task analysis including clarity scoring, improvements, tags,
 * priority recommendations, and missing information.
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - macOS 26+
 * - Apple Silicon (M1 or later)
 */

;(() => {
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
              name: 'estimatedMinutes',
              description: 'Estimated time to complete in minutes (numeric only, e.g. 30)',
              isOptional: true,
              schema: { type: 'number' },
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

        // Craft the prompt. The user's existing tag list is passed verbatim
        // so the AI selects FROM it rather than inventing new tags. If the
        // user has no tags yet, we tell the model to return an empty array
        // (a downstream post-filter also drops any invented tags).
        const tagListSection = existingTagNames.length > 0
          ? `EXISTING TAGS (choose ONLY from this list — do not invent new tags):\n${existingTagNames.join(', ')}`
          : `EXISTING TAGS: (none — return an empty suggestedTags array)`

        const prompt = `Analyze this OmniFocus task and provide structured feedback:

TASK DETAILS:
${taskContext}

${tagListSection}

Please analyze:
1. How clear and actionable is this task? (Rate 1-10)
2. Would a different task name be clearer? If yes, suggest one.
3. What 2-3 tags from the EXISTING TAGS list above would be most relevant? Do NOT invent new tags — if no existing tags fit, return an empty array.
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

        // Coerce estimatedMinutes to a Number. The schema now declares
        // `type: 'number'`, but Foundation Models has been observed to
        // still return string values for numeric properties — and
        // Task.estimatedMinutes is strict ("requires a Number, but was
        // passed value of type String"). Normalize once here so every
        // downstream consumer (display, comparison, dispatch) sees a
        // Number or null.
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
   * Coerce the AI's estimatedMinutes value to a positive integer or null.
   * Foundation Models has been observed to return string values ("30")
   * even when the schema declares type: 'number'; this is the dispatch-
   * site safety net. Returns null for empty/invalid/non-positive values
   * (which makes downstream truthiness guards just-work — null short-
   * circuits the apply prompt).
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
