/**
 * Task Metrics Library for OmniFocus
 *
 * Composable, reusable functions for collecting task data from OmniFocus.
 * Separates data collection from analysis for flexibility and testability.
 *
 * Usage (in OmniFocus plugin):
 *   // In manifest.json, declare as library:
 *   "libraries": ["taskMetrics"]
 *
 *   // In action script:
 *   const metrics = this.plugIn.library("taskMetrics");
 *   const tasks = metrics.getTodayTasks();
 *
 * Usage (in Omni Automation console):
 *   // Load library code and evaluate
 *   const metrics = <paste this code>;
 *   const tasks = metrics.getTodayTasks();
 *
 * @version 3.0.0
 */

(() => {
    var lib = new PlugIn.Library(new Version("1.0"));

        /**
         * Get tasks due or deferred to today
         * @returns {Array} Array of task objects with normalized data
         */
        lib.getTodayTasks = function() {
            const tasks = flattenedTasks;

            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);

            const todayTasks = tasks.filter(task => {
                if (task.completed || task.dropped) return false;

                const due = task.dueDate;
                const defer = task.deferDate;

                const isDueToday = due && due >= today && due < tomorrow;
                const isDeferredToday = defer && defer >= today && defer < tomorrow;

                return isDueToday || isDeferredToday;
            

            return todayTasks.map(task => this.normalizeTask(task));
        };

        /**
         * Get overdue tasks (past due date)
         * @returns {Array} Array of overdue task objects
         */
        lib.getOverdueTasks = function() {
            const tasks = flattenedTasks;

            const today = new Date();
            today.setHours(0, 0, 0, 0);

            const overdueTasks = tasks.filter(task => {
                if (task.completed || task.dropped) return false;
                const due = task.dueDate;
                return due && due < today;
            

            return overdueTasks.map(task => this.normalizeTask(task));
        };

        /**
         * Get upcoming tasks (due within N days)
         * @param {number} days - Number of days to look ahead (default: 7)
         * @returns {Array} Array of upcoming task objects
         */
        lib.getUpcomingTasks = function(days = 7) {
            const tasks = flattenedTasks;

            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const futureDate = new Date(today);
            futureDate.setDate(futureDate.getDate() + days);

            const upcomingTasks = tasks.filter(task => {
                if (task.completed || task.dropped) return false;
                const due = task.dueDate;
                return due && due >= today && due < futureDate;
            

            return upcomingTasks.map(task => this.normalizeTask(task));
        };

        /**
         * Get all flagged tasks
         * @returns {Array} Array of flagged task objects
         */
        lib.getFlaggedTasks = function() {
            const tasks = flattenedTasks;

            const flaggedTasks = tasks.filter(task => {
                return task.flagged && !task.completed && !task.dropped;
            

            return flaggedTasks.map(task => this.normalizeTask(task));
        };

        /**
         * Get available tasks (not blocked, not deferred, not completed)
         * @returns {Array} Array of available task objects
         */
        lib.getAvailableTasks = function() {
            const tasks = flattenedTasks;

            const availableTasks = tasks.filter(task => {
                if (task.completed || task.dropped) return false;
                return task.taskStatus === Task.Status.Available;
            

            return availableTasks.map(task => this.normalizeTask(task));
        };

        /**
         * Get tasks by tag name
         * @param {string} tagName - Name of tag to filter by
         * @returns {Array} Array of tasks with the specified tag
         */
        lib.getTasksByTag = function(tagName) {
            const tasks = flattenedTasks;

            const filtered = tasks.filter(task => {
                if (task.completed || task.dropped) return false;
                return task.tags.some(tag => tag.name === tagName);
            

            return filtered.map(task => this.normalizeTask(task));
        };

        /**
         * Get tasks by project name
         * @param {string} projectName - Name of project to filter by
         * @returns {Array} Array of tasks in the specified project
         */
        lib.getTasksByProject = function(projectName) {
            const tasks = flattenedTasks;

            const filtered = tasks.filter(task => {
                if (task.completed || task.dropped) return false;
                return task.containingProject && task.containingProject.name === projectName;
            

            return filtered.map(task => this.normalizeTask(task));
        };

        /**
         * Get tasks completed today
         * @returns {Array} Array of completed task objects with completion metadata
         */
        lib.getCompletedToday = function() {
            const tasks = flattenedTasks;

            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);

            const completedToday = tasks.filter(task => {
                if (!task.completed) return false;
                const completionDate = task.completionDate;
                return completionDate && completionDate >= today && completionDate < tomorrow;
            });

            return completedToday.map(task => {
                return {
                    name: task.name,
                    project: task.containingProject ? task.containingProject.name : null,
                    completionDate: task.completionDate,
                    completionTime: task.completionDate ?
                        task.completionDate.toLocaleTimeString('en-US', {
                            hour: 'numeric',
                            minute: '2-digit',
                            hour12: true
                        }) : null
                };
            });
        };

        /**
         * Get summary statistics across all tasks
         * @returns {Object} Summary statistics object
         */
        lib.getSummaryStats = function() {
            const tasks = flattenedTasks;

            const stats = {
                total: tasks.length,
                active: 0,
                completed: 0,
                dropped: 0,
                flagged: 0,
                overdue: 0,
                dueToday: 0,
                totalEstimatedMinutes: 0,
                tasksWithEstimates: 0,
                uniqueTags: new Set(),
                uniqueProjects: new Set()
            };

            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);

            tasks.forEach(task => {
                if (task.completed) {
                    stats.completed++;
                } else if (task.dropped) {
                    stats.dropped++;
                } else {
                    stats.active++;
                }

                if (task.flagged) stats.flagged++;

                if (task.dueDate) {
                    if (task.dueDate < today && !task.completed) {
                        stats.overdue++;
                    } else if (task.dueDate >= today && task.dueDate < tomorrow) {
                        stats.dueToday++;
                    }
                }

                if (task.estimatedMinutes) {
                    stats.totalEstimatedMinutes += task.estimatedMinutes;
                    stats.tasksWithEstimates++;
                }

                task.tags.forEach(tag => stats.uniqueTags.add(tag.name));

                if (task.containingProject) {
                    stats.uniqueProjects.add(task.containingProject.name);
                }
            

            stats.uniqueTags = Array.from(stats.uniqueTags).sort();
            stats.uniqueProjects = Array.from(stats.uniqueProjects).sort();
            stats.averageEstimatedMinutes = stats.tasksWithEstimates > 0
                ? Math.round(stats.totalEstimatedMinutes / stats.tasksWithEstimates)
                : 0;

            return stats;
        };

        /**
         * Normalize task object to consistent data structure
         * @param {Task} task - OmniFocus task object
         * @returns {Object} Normalized task data
         */
        lib.normalizeTask = function(task) {
            return {
                name: task.name,
                project: task.containingProject ? task.containingProject.name : null,
                tags: task.tags.map(tag => tag.name),
                dueDate: task.dueDate,
                deferDate: task.deferDate,
                flagged: task.flagged,
                completed: task.completed,
                estimatedMinutes: task.estimatedMinutes,
                note: task.note || "",
                added: task.added,
                modified: task.modified,
                taskStatus: task.taskStatus
            };
        };

    

    return lib;
})();
