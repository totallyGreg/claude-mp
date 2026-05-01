/**
 * Query Flagged Tasks Action
 *
 * Shows all flagged tasks with summary statistics.
 */

(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        // Load taskMetrics library
        const metrics = this.plugIn.library("taskMetrics");

        // Query flagged tasks
        const tasks = metrics.getFlaggedTasks();

        // Format results
        let message = `Found ${tasks.length} flagged tasks:\n\n`;

        if (tasks.length === 0) {
            message = "No flagged tasks found!";
        } else {
            tasks.forEach((task, index) => {
                message += `${index + 1}. ${task.name}\n`;
                message += `   Project: ${task.project || 'Inbox'}\n`;
                if (task.dueDate) {
                    message += `   Due: ${task.dueDate.toLocaleDateString()}\n`;
                }
                message += '\n';
            });
        }

        // Display alert
        const alert = new Alert("Flagged Tasks", message);
        await alert.show();
    });

    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
