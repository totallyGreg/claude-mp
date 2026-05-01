/**
 * Export Hierarchy to OPML
 *
 * Exports the OmniFocus folder/project/task hierarchy as OPML outline
 * compatible with outliner applications (MindNode, OmniOutliner, etc.)
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

            // Export to OPML
            const opml = treeBuilder.exportToOPML(tree, {
                title: "OmniFocus Hierarchy",
                includeMetrics: true
            });

            // Save to file using custom XML handling
            const filename = `omnifocus-hierarchy-${new Date().toISOString().split('T')[0]}.opml`;
            const fileSaver = new FileSaver();
            fileSaver.nameLabel = "Save OPML";
            fileSaver.types = [FileType.fromExtension('opml')];
            fileSaver.defaultFileName = filename;

            const url = await fileSaver.show();
            if (url) {
                const wrapper = FileWrapper.fromString(url.toString(), opml);
                wrapper.write(url);
                new Alert('Export Successful', 'Hierarchy exported to OPML file').show();
            } else {
                new Alert('Export Cancelled', 'No file was saved').show();
            }

        } catch (error) {
            console.error('Export to OPML failed:', error);
            new Alert('Error', error.message).show();
        }
    });

    // Always enable this action
    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
