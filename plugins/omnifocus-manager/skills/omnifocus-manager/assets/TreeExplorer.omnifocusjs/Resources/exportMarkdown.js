/**
 * Export Hierarchy to Markdown
 *
 * Exports the OmniFocus folder/project/task hierarchy as indented Markdown
 * with metrics and health indicators.
 */

(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        try {
            // Get treeBuilder and exportUtils libraries
            const treeBuilder = this.plugIn.library("treeBuilder");
            const exportUtils = this.plugIn.library("exportUtils");

            // Build tree from database
            const tree = treeBuilder.buildTreeFromDatabase({
                includeMetrics: true,
                includeHealth: true,
                maxDepth: Infinity
            });

            // Export to Markdown
            const markdown = treeBuilder.exportToMarkdown(tree, {
                indent: "  ",
                includeMetrics: true,
                includeHealth: true,
                includeIcons: true
            });

            // Save to file
            const saved = await exportUtils.toFile(markdown, {
                format: 'markdown',
                filename: `omnifocus-hierarchy-${new Date().toISOString().split('T')[0]}.md`
            });

            if (saved) {
                new Alert('Export Successful', 'Hierarchy exported to Markdown file').show();
            } else {
                new Alert('Export Cancelled', 'No file was saved').show();
            }

        } catch (error) {
            console.error('Export to Markdown failed:', error);
            new Alert('Error', error.message).show();
        }
    });

    // Always enable this action
    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
