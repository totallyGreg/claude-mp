/**
 * {{PLUGIN_NAME}} - OmniFocus Database Statistics Plugin
 *
 * {{DESCRIPTION}}
 */

(() => {
    /**
     * Format a number with thousand separators
     * @param {number} num - Number to format
     * @returns {string} Formatted number string
     */
    function formatNumber(num) {
        return num.toLocaleString('en-US');
    }

    /**
     * Calculate and format percentage
     * @param {number} part - Part value
     * @param {number} total - Total value
     * @returns {string} Formatted percentage string
     */
    function formatPercentage(part, total) {
        if (total === 0) return '0%';
        return Math.round((part / total) * 100) + '%';
    }

    /**
     * Build the overview message with all statistics
     * @param {Object} taskStats - Task statistics object
     * @param {Object} projectStats - Project statistics object
     * @param {number} folderCount - Total folder count
     * @param {number} tagCount - Total tag count
     * @param {number} inboxCount - Inbox item count
     * @param {Object} stats - Additional statistics object
     * @returns {string} Formatted overview message
     */
    function buildOverviewMessage(taskStats, projectStats, folderCount, tagCount, inboxCount, stats) {
        let message = '=== {{PLUGIN_NAME}} ===\n\n';

        // TASKS section
        message += 'TASKS\n';
        message += `  Total: ${formatNumber(taskStats.total)}\n`;
        message += `  Active: ${formatNumber(taskStats.active)} (${formatPercentage(taskStats.active, taskStats.total)})\n`;
        message += `  Completed: ${formatNumber(taskStats.completed)} (${formatPercentage(taskStats.completed, taskStats.total)})\n`;
        message += `  Dropped: ${formatNumber(taskStats.dropped)} (${formatPercentage(taskStats.dropped, taskStats.total)})\n`;
        message += '\n';

        // PROJECTS section
        message += 'PROJECTS\n';
        message += `  Total: ${formatNumber(projectStats.total)}\n`;
        message += `  Active: ${formatNumber(projectStats.active)} (${formatPercentage(projectStats.active, projectStats.total)})\n`;
        message += `  On Hold: ${formatNumber(projectStats.onHold)} (${formatPercentage(projectStats.onHold, projectStats.total)})\n`;
        message += `  Completed: ${formatNumber(projectStats.completed)} (${formatPercentage(projectStats.completed, projectStats.total)})\n`;
        message += `  Dropped: ${formatNumber(projectStats.dropped)} (${formatPercentage(projectStats.dropped, projectStats.total)})\n`;
        message += '\n';

        // ORGANIZATION section
        message += 'ORGANIZATION\n';
        message += `  Folders: ${formatNumber(folderCount)}\n`;
        message += `  Tags: ${formatNumber(tagCount)}\n`;
        message += `  Inbox: ${formatNumber(inboxCount)}\n`;
        message += '\n';

        // STATISTICS section
        message += 'STATISTICS\n';
        message += `  Flagged: ${formatNumber(stats.flagged)}\n`;
        message += `  Overdue: ${formatNumber(stats.overdue)}\n`;

        return message;
    }

    const action = new PlugIn.Action(function(selection, sender) {
        try {
            // Access OmniFocus data using global variables
            const tasks = flattenedTasks;
            const projects = flattenedProjects;
            const folders = flattenedFolders;
            const allTags = flattenedTags;
            const inboxTasks = inbox;

            // Count tasks by status
            const taskStats = {
                total: tasks.length,
                active: 0,
                completed: 0,
                dropped: 0
            };

            tasks.forEach(task => {
                if (task.completed) {
                    taskStats.completed++;
                } else if (task.dropped) {
                    taskStats.dropped++;
                } else {
                    taskStats.active++;
                }
            });

            // Count projects by status
            const projectStats = {
                total: projects.length,
                active: 0,
                onHold: 0,
                completed: 0,
                dropped: 0
            };

            projects.forEach(project => {
                if (project.status === Project.Status.Active) {
                    projectStats.active++;
                } else if (project.status === Project.Status.OnHold) {
                    projectStats.onHold++;
                } else if (project.status === Project.Status.Done) {
                    projectStats.completed++;
                } else if (project.status === Project.Status.Dropped) {
                    projectStats.dropped++;
                }
            });

            // Count simple statistics
            const folderCount = folders.length;
            const tagCount = allTags.length;
            const inboxCount = inboxTasks.length;

            // Calculate additional statistics
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            const stats = {
                flagged: 0,
                overdue: 0
            };

            tasks.forEach(task => {
                // Count flagged tasks (active only)
                if (task.flagged && !task.completed && !task.dropped) {
                    stats.flagged++;
                }

                // Count overdue tasks (active only)
                if (!task.completed && !task.dropped && task.dueDate && task.dueDate < today) {
                    stats.overdue++;
                }
            });

            // Build and display message
            const message = buildOverviewMessage(
                taskStats,
                projectStats,
                folderCount,
                tagCount,
                inboxCount,
                stats
            );

            const alert = new Alert('{{PLUGIN_NAME}}', message);
            alert.show();

        } catch (error) {
            console.error('Error:', error);
            new Alert('Error', error.message).show();
        }
    });

    // Always enable this action
    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
