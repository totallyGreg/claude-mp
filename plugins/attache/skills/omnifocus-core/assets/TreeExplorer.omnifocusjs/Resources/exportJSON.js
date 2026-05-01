/**
 * Export Hierarchy to JSON
 *
 * Exports the OmniFocus folder/project/task hierarchy as JSON tree structure
 * with full metadata for programmatic use.
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

            // Export to JSON
            const json = treeBuilder.exportToJSON(tree, {
                pretty: true,
                includeOFRefs: false
            });

            // Save to file
            const saved = await exportUtils.toFile(json, {
                format: 'json',
                filename: `omnifocus-hierarchy-${new Date().toISOString().split('T')[0]}.json`
            });

            if (saved) {
                new Alert('Export Successful', 'Hierarchy exported to JSON file').show();
            } else {
                new Alert('Export Cancelled', 'No file was saved').show();
            }

        } catch (error) {
            console.error('Export to JSON failed:', error);
            new Alert('Error', error.message).show();
        }
    });

    // Always enable this action
    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
