/**
 * Today's Tasks - Omni Automation Plug-In
 *
 * Shows all tasks that are due or deferred to today, grouped by project.
 * This provides a quick view of what should be worked on today.
 */

(() => {
    const action = new PlugIn.Action(function(selection, sender) {
        try {
            // Get all tasks
            const doc = Document.defaultDocument;
            const tasks = doc.flattenedTasks;

            // Calculate today's date range
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);

            // Filter for today's tasks
            const todayTasks = tasks.filter(task => {
                // Skip completed and dropped tasks
                if (task.completed || task.dropped) return false;

                const due = task.dueDate;
                const defer = task.deferDate;

                // Check if due or deferred to today
                const isDueToday = due && due >= today && due < tomorrow;
                const isDeferredToday = defer && defer >= today && defer < tomorrow;

                return isDueToday || isDeferredToday;
            });

            // Group tasks by project
            const tasksByProject = {};
            todayTasks.forEach(task => {
                const project = task.containingProject;
                const projectName = project ? project.name : "Inbox";

                if (!tasksByProject[projectName]) {
                    tasksByProject[projectName] = [];
                }

                tasksByProject[projectName].push(task);
            });

            // Build message
            let message = `Found ${todayTasks.length} task${todayTasks.length !== 1 ? 's' : ''} for today:\n\n`;

            if (todayTasks.length === 0) {
                message = "No tasks found for today!";
            } else {
                // Sort projects alphabetically
                const projectNames = Object.keys(tasksByProject).sort();

                projectNames.forEach(projectName => {
                    message += `${projectName}:\n`;
                    tasksByProject[projectName].forEach(task => {
                        const flag = task.flagged ? "🚩 " : "";
                        const dueTime = task.dueDate ?
                            ` (Due: ${task.dueDate.toLocaleTimeString('en-US', {hour: 'numeric', minute: '2-digit'})})` : "";
                        message += `  ${flag}• ${task.name}${dueTime}\n`;
                    });
                    message += "\n";
                });
            }

            // Show alert
            const alert = new Alert("Today's Tasks", message);
            alert.show();

        } catch (error) {
            console.error("Error:", error);
            new Alert("Error", error.message).show();
        }
    });

    // Always enable this action
    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
