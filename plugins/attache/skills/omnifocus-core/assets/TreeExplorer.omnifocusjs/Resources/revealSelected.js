/**
 * Reveal Selected in Window (OmniFocus 4)
 *
 * Uses OmniFocus 4 TreeNode API to reveal and select items in the window tree.
 * Demonstrates interactive window manipulation capabilities.
 */

(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        try {
            // Get treeBuilder library
            const treeBuilder = this.plugIn.library("treeBuilder");

            // Check OmniFocus 4 support
            if (!treeBuilder.checkOF4TreeSupport()) {
                new Alert(
                    'OmniFocus 4 Required',
                    'This action requires OmniFocus 4 window tree API.\n\n' +
                    'The tree API is not available in OmniFocus 3.'
                ).show();
                return;
            }

            // Get window
            const window = document.windows[0];
            if (!window) {
                new Alert('No Window', 'No OmniFocus window is open').show();
                return;
            }

            // Get selected items
            const selectedTasks = selection.tasks;
            const selectedProjects = selection.projects;
            const selectedFolders = selection.folders;

            // Collect IDs to reveal
            const ids = [];
            selectedTasks.forEach(t => ids.push(t.id.primaryKey));
            selectedProjects.forEach(p => ids.push(p.id.primaryKey));
            selectedFolders.forEach(f => ids.push(f.id.primaryKey));

            if (ids.length === 0) {
                new Alert('No Selection', 'Please select one or more items to reveal').show();
                return;
            }

            // Reveal nodes in window
            const success = treeBuilder.revealNodes(window, ids, "content");

            if (success) {
                new Alert(
                    'Items Revealed',
                    `Successfully revealed ${ids.length} item(s) in window tree`
                ).show();
            } else {
                new Alert(
                    'Reveal Failed',
                    'Could not reveal selected items. They may not be in the current view.'
                ).show();
            }

        } catch (error) {
            console.error('Reveal selected failed:', error);
            new Alert('Error', error.message).show();
        }
    });

    // Enable when there is a selection
    action.validate = function(selection, sender) {
        return (
            selection.tasks.length > 0 ||
            selection.projects.length > 0 ||
            selection.folders.length > 0
        );
    };

    return action;
})();
