/**
 * Query Today's Tasks Action
 *
 * Demonstrates using taskMetrics library in a plugin action.
 */

(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        // Load taskMetrics library
        const metrics = this.plugIn.library("taskMetrics");

        // Query today's tasks
        const tasks = metrics.getTodayTasks();

        // Format results
        let message = `You have ${tasks.length} tasks today:\n\n`;

        if (tasks.length === 0) {
            message = "No tasks due or deferred to today!";
        } else {
            // Group by project
            const byProject = {};
            tasks.forEach(task => {
                const project = task.project || 'Inbox';
                if (!byProject[project]) byProject[project] = [];
                byProject[project].push(task);
            });

            // Format output
            Object.keys(byProject).sort().forEach(project => {
                message += `${project}:\n`;
                byProject[project].forEach(task => {
                    let line = `  • ${task.name}`;
                    if (task.flagged) line += ' 🚩';
                    message += line + '\n';
                });
                message += '\n';
            });
        }

        // Display alert
        const alert = new Alert("Today's Tasks", message);
        await alert.show();
    });

    action.validate = function(selection, sender) {
        return true; // Always available
    };

    return action;
})();
