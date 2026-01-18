(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        try {
            // Load libraries
            const metrics = this.plugIn.library("taskMetrics");
            const formatter = this.plugIn.library("completedTasksFormatter");

            // Query completed tasks
            const tasks = metrics.getCompletedToday();

            // Format as markdown
            const markdown = formatter.formatAsMarkdown(tasks);

            // Copy to clipboard
            Pasteboard.general.string = markdown;

            // Show confirmation
            const alert = new Alert(
                "Copied to Clipboard",
                `${tasks.length} completed task${tasks.length !== 1 ? 's' : ''} copied to clipboard.\n\nYou can now paste into any application.`
            );
            await alert.show();

        } catch (error) {
            console.error("Copy to clipboard failed:", error);
            const alert = new Alert(
                "Error",
                `Failed to copy completed tasks: ${error.message}`
            );
            await alert.show();
        }
    });

    action.validate = function(selection, sender) {
        return true; // Always available
    };

    return action;
})();
