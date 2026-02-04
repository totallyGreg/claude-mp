/**
 * Export Today to Markdown Action
 *
 * Demonstrates using taskMetrics + exportUtils libraries together.
 */

(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        // Load libraries
        const metrics = this.plugIn.library("taskMetrics");
        const exporter = this.plugIn.library("exportUtils");

        // Query today's tasks
        const tasks = metrics.getTodayTasks();

        // Export to markdown via clipboard
        const success = exporter.toClipboard(tasks, {
            format: 'markdown',
            title: "Today's Tasks"
        });

        if (success) {
            const alert = new Alert(
                "Export Complete",
                `${tasks.length} tasks exported to clipboard as Markdown.\n\nYou can now paste into any text editor.`
            );
            await alert.show();
        } else {
            const alert = new Alert(
                "Export Failed",
                "Could not export tasks to clipboard."
            );
            await alert.show();
        }
    });

    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
