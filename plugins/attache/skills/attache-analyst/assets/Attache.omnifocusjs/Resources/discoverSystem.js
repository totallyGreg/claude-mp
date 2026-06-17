/**
 * System Discovery Action - Omni Automation Plug-In
 *
 * Discovers the user's unique OmniFocus organizational structure using
 * a hybrid approach: rule-based pattern matching + Apple Foundation Models
 * for semantic understanding.
 *
 * Features:
 * - Quick discovery (structure only, rule-based)
 * - Full discovery (with AI semantic analysis)
 * - Multiple output formats (alert, markdown, JSON)
 * - GTD health assessment
 * - Actionable recommendations
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - For AI features: macOS 26+, Apple Silicon (M1 or later)
 */

;(() => {
  const action = new PlugIn.Action(async function (selection, sender) {
    // Load required libraries
    const fmUtils = this.plugIn.library('foundationModelsUtils')
    const discovery = this.plugIn.library('systemDiscovery')
    const exportUtils = this.plugIn.library('exportUtils')
    const metrics = this.plugIn.library('taskMetrics')
    const prefsManager = this.plugIn.library('preferencesManager')

    // Check if AI is available (optional enhancement)
    const aiAvailable = fmUtils.isAvailable()

    try {
      // Configuration form
      const form = new Form()

      // Discovery depth
      // @ts-ignore — 6th arg (nullOptionTitle) is optional at runtime
      const depthField = new Form.Field.Option(
        'depth',
        'Discovery Depth',
        ['quick', 'full'],
        ['Quick (structure + GTD health)', 'Full (includes task analysis)'],
        'quick'
      )
      form.addField(depthField)

      // AI enhancement option (only show if AI available)
      const aiField = new Form.Field.Checkbox(
        'useAI',
        'Use Apple Intelligence for semantic analysis',
        aiAvailable
      )
      form.addField(aiField)

      // Output format
      // @ts-ignore — 6th arg (nullOptionTitle) is optional at runtime
      const outputField = new Form.Field.Option(
        'output',
        'Output Format',
        ['alert', 'markdown', 'json'],
        ['Summary Alert', 'Markdown Report', 'JSON Export'],
        'alert'
      )
      form.addField(outputField)

      // Show form
      const formResult = await form.show('System Discovery', 'Discover')

      // Handle cancellation
      if (!formResult) {
        return
      }

      const depth = formResult.values['depth']
      const useAI = formResult.values['useAI']
      const output = formResult.values['output']

      // Run discovery
      let systemMap = discovery.discoverSystem({ depth: depth, waitingPatterns: metrics.WAITING_PATTERNS })

      // Enhance with AI if requested and available
      if (useAI && aiAvailable) {
        try {
          const session = fmUtils.createSession()
          const aiInsights = await discovery.discoverWithAI(session, systemMap)
          systemMap = discovery.mergeAIInsights(systemMap, aiInsights)
        } catch (aiError) {
          // AI enhancement failed, continue with rule-based results
          console.error('AI enhancement failed:', aiError)
          systemMap.aiError = aiError.message
        }
      }

      // Output results based on selected format
      switch (output) {
        case 'alert':
          await showSummaryAlert(discovery, systemMap, prefsManager)
          break

        case 'markdown':
          await exportMarkdown(discovery, exportUtils, systemMap)
          break

        case 'json':
          await exportJSON(exportUtils, systemMap)
          break
      }
    } catch (error) {
      const alert = new Alert('Discovery Error', error.message)
      alert.show()
      console.error('System Discovery Error:', error)
    }
  })

  /**
   * Show summary in an alert dialog. Augments the bare summary with a
   * Horizons-of-Focus section (labels area folders as Horizon 2 with
   * cross-link to monthlyReview) and offers a "Save as System Map"
   * apply-path that persists the discovered map for the convention-
   * dependent actions (quickOrganize, monthlyReview, healthCheck) to
   * consume.
   *
   * @param {Object} discovery   - Discovery library
   * @param {Object} systemMap   - Discovered system map
   * @param {Object} prefsManager - Preferences manager library
   */
  async function showSummaryAlert(discovery, systemMap, prefsManager) {
    const summary = discovery.generateSummary(systemMap)
    const horizons = buildHorizonsSection(systemMap)
    const fullMessage = horizons ? `${summary}\n\n${horizons}` : summary

    const alert = new Alert('Map System', fullMessage)
    alert.addOption('Copy Full Report')
    alert.addOption('Export JSON')
    alert.addOption('💾 Save as System Map')
    alert.addOption('Done')

    const buttonIndex = await alert.show()

    if (buttonIndex === 0) {
      const report = discovery.generateMarkdownReport(systemMap)
      Pasteboard.general.string = report
      const confirmAlert = new Alert(
        'Report Copied',
        'The full markdown report has been copied to your clipboard.'
      )
      confirmAlert.show()
    } else if (buttonIndex === 1) {
      const json = JSON.stringify(systemMap, null, 2)
      Pasteboard.general.string = json
      const confirmAlert = new Alert(
        'JSON Copied',
        'The SystemMap JSON has been copied to your clipboard.'
      )
      confirmAlert.show()
    } else if (buttonIndex === 2) {
      await saveAsSystemMap(systemMap, prefsManager)
    }
  }

  /**
   * Build the "Horizons of Focus" labeling section: surface top-level
   * folders inferred as `area` as GTD Horizon 2 (Areas of Focus) with a
   * cross-link to monthlyReview (the action that walks them at the
   * monthly cadence).
   *
   * Returns "" when no area folders are inferred (offers a nudge instead),
   * or when topLevelFolders isn't populated (shouldn't happen but
   * defensive).
   */
  function buildHorizonsSection(systemMap) {
    const tlf = systemMap && systemMap.structure && systemMap.structure.topLevelFolders
    if (!Array.isArray(tlf)) return ''

    const areas = tlf.filter(f => f && f.inferredType === 'area')

    const lines = []
    lines.push('── Horizons of Focus ──')
    lines.push('')

    if (areas.length === 0) {
      lines.push('No top-level folders are inferred as Areas of Focus (GTD Horizon 2).')
      lines.push('To surface Areas: rename folders to something Area-like (e.g., "Work", "Health", "Family") and re-run System Discovery.')
      return lines.join('\n')
    }

    lines.push(`📐 ${areas.length} Area${areas.length === 1 ? '' : 's'} of Focus (Horizon 2):`)
    areas.forEach(a => {
      const activeText = (typeof a.activeProjectCount === 'number')
        ? `${a.activeProjectCount} active project${a.activeProjectCount === 1 ? '' : 's'}`
        : 'project count unknown'
      lines.push(`  · ${a.name} — ${activeText}`)
    })
    lines.push('')
    lines.push('💡 Run Attache › Monthly Review to walk these Areas at the recommended monthly cadence.')
    return lines.join('\n')
  }

  /**
   * Persist the discovered systemMap via preferencesManager so the
   * convention-dependent actions (quickOrganize, monthlyReview,
   * healthCheck) can consume it. Confirms before overwriting an
   * existing map to avoid losing the user's previous discovery state.
   *
   * Until v2.18.0 discoverSystem could SHOW the map but not SAVE it —
   * only systemSetup wrote to preferencesManager. This closes that gap
   * (the [P] apply-path for discoverSystem).
   */
  async function saveAsSystemMap(systemMap, prefsManager) {
    if (!prefsManager) {
      const errAlert = new Alert(
        'Save Failed',
        'preferencesManager library not available. Run Attache › Setup instead, which uses the same persistence path.'
      )
      errAlert.show()
      return
    }

    if (prefsManager.hasPreferences()) {
      const confirmAlert = new Alert(
        'Replace System Map?',
        'You have a cached System Map already. Saving will replace it with this discovery (which the convention-dependent actions — quickOrganize, monthlyReview, healthCheck — will then read).\n\nContinue?'
      )
      confirmAlert.addOption('Replace')
      confirmAlert.addOption('Cancel')
      const choice = await confirmAlert.show()
      if (choice !== 0) return
    }

    try {
      prefsManager.write(systemMap)
      const successAlert = new Alert(
        'System Map Saved',
        'The discovered system map is now cached. Convention-dependent actions (Quick Organize, Monthly Review, Health Check) will read from it.'
      )
      successAlert.show()
    } catch (e) {
      const errAlert = new Alert(
        'Save Failed',
        e && e.message ? e.message : String(e)
      )
      errAlert.show()
      console.error('saveAsSystemMap:', e)
    }
  }

  /**
   * Export markdown report to file
   * @param {Object} discovery - Discovery library
   * @param {Object} exportUtils - Export utilities library
   * @param {Object} systemMap - Discovered system map
   */
  async function exportMarkdown(discovery, exportUtils, systemMap) {
    const report = discovery.generateMarkdownReport(systemMap)
    const dateStr = new Date().toISOString().split('T')[0]
    const filename = `OmniFocus_SystemMap_${dateStr}.md`

    const reportData = Data.fromString(report)
    const wrapper = FileWrapper.withContents(filename, reportData)

    const fileSaver = new FileSaver()
    fileSaver.nameLabel = 'Save Report'
    fileSaver.defaultFileName = filename

    const url = await fileSaver.show(wrapper)
    if (url) {
      const alert = new Alert(
        'Report Saved',
        `System discovery report saved to:\n${filename}`
      )
      alert.show()
    }
  }

  /**
   * Export JSON to file
   * @param {Object} exportUtils - Export utilities library
   * @param {Object} systemMap - Discovered system map
   */
  async function exportJSON(exportUtils, systemMap) {
    const json = JSON.stringify(systemMap, null, 2)
    const dateStr = new Date().toISOString().split('T')[0]
    const filename = `OmniFocus_SystemMap_${dateStr}.json`

    const jsonData = Data.fromString(json)
    const wrapper = FileWrapper.withContents(filename, jsonData)

    const fileSaver = new FileSaver()
    fileSaver.nameLabel = 'Save JSON'
    fileSaver.defaultFileName = filename

    const url = await fileSaver.show(wrapper)
    if (url) {
      const alert = new Alert(
        'JSON Saved',
        `System map JSON saved to:\n${filename}`
      )
      alert.show()
    }
  }

  // Validation - always available since discovery works without AI
  action.validate = function (selection, sender) {
    // System discovery is always available
    // AI enhancement is optional
    return true
  }

  return action
})()
