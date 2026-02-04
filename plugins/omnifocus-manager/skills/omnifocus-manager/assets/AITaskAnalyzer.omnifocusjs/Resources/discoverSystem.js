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
 * - For AI features: macOS 15.2+, iOS 18.2+, Apple Silicon
 */

;(() => {
  const action = new PlugIn.Action(async function (selection, sender) {
    // Load required libraries
    const fmUtils = this.plugIn.library('foundationModelsUtils')
    const discovery = this.plugIn.library('systemDiscovery')
    const exportUtils = this.plugIn.library('exportUtils')

    // Check if AI is available (optional enhancement)
    const aiAvailable = fmUtils.isAvailable()

    try {
      // Configuration form
      const form = new Form()

      // Discovery depth
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
      let systemMap = discovery.discoverSystem({ depth: depth })

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
          await showSummaryAlert(discovery, systemMap)
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
   * Show summary in an alert dialog
   * @param {Object} discovery - Discovery library
   * @param {Object} systemMap - Discovered system map
   */
  async function showSummaryAlert(discovery, systemMap) {
    const summary = discovery.generateSummary(systemMap)

    const alert = new Alert('System Discovery Results', summary)
    alert.addOption('Copy Full Report')
    alert.addOption('Export JSON')
    alert.addOption('Done')

    const buttonIndex = await alert.show()

    if (buttonIndex === 0) {
      // Copy markdown report to clipboard
      const report = discovery.generateMarkdownReport(systemMap)
      Pasteboard.general.string = report

      const confirmAlert = new Alert(
        'Report Copied',
        'The full markdown report has been copied to your clipboard.'
      )
      confirmAlert.show()
    } else if (buttonIndex === 1) {
      // Export JSON
      const json = JSON.stringify(systemMap, null, 2)
      Pasteboard.general.string = json

      const confirmAlert = new Alert(
        'JSON Copied',
        'The SystemMap JSON has been copied to your clipboard.'
      )
      confirmAlert.show()
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
