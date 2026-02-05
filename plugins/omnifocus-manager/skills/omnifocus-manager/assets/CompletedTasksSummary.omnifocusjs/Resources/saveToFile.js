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

            // Generate date-stamped filename
            const dateStr = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
            const filename = `${dateStr}-completed-tasks.md`;

            // Save to file using FileSaver
            const fileSaver = new FileSaver();
            fileSaver.nameLabel = "Save Completed Tasks";
            fileSaver.types = [FileType.fromExtension('md')];
            fileSaver.defaultFileName = filename;

            const url = await fileSaver.show();

            if (url) {
                url.write(markdown);

                // Show confirmation
                const alert = new Alert(
                    "Saved Successfully",
                    `${tasks.length} completed task${tasks.length !== 1 ? 's' : ''} saved to:\n\n${filename}`
                );
                await alert.show();
            } else {
                // User cancelled
                console.log("Save cancelled by user");
            }

        } catch (error) {
            console.error("Save to file failed:", error);
            const alert = new Alert(
                "Error",
                `Failed to save completed tasks: ${error.message}`
            );
            await alert.show();
        }
    });

    action.validate = function(selection, sender) {
        return true; // Always available
    };

    return action;
})();
