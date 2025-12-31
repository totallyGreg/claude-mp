/**
 * Task Metrics Library - PlugIn.Library
 *
 * Composable, reusable functions for collecting task data from OmniFocus.
 * Separates data collection from AI analysis for flexibility and testability.
 *
 * Usage in plugin actions:
 *   const metrics = this.plugIn.library("taskMetrics");
 *   const tasks = metrics.getTodayTasks();
 *
 * @version 3.0.0
 */

(() => {
    const lib = new PlugIn.Library(new Version("3.0"));

    /**
     * Get tasks due or deferred to today
     * @returns {Array} Array of task objects with normalized data
     */
    lib.getTodayTasks = function() {
        const doc = Document.defaultDocument;
        const tasks = doc.flattenedTasks;

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
        });

        return todayTasks.map(this.normalizeTask.bind(this));
    };

    /**
     * Get overdue tasks (past due date)
     * @returns {Array} Array of overdue task objects
     */
    lib.getOverdueTasks = function() {
        const doc = Document.defaultDocument;
        const tasks = doc.flattenedTasks;

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const overdueTasks = tasks.filter(task => {
            if (task.completed || task.dropped) return false;
            const due = task.dueDate;
            return due && due < today;
        });

        return overdueTasks.map(this.normalizeTask.bind(this));
    };

    /**
     * Get all flagged tasks
     * @returns {Array} Array of flagged task objects
     */
    lib.getFlaggedTasks = function() {
        const doc = Document.defaultDocument;
        const tasks = doc.flattenedTasks;

        const flaggedTasks = tasks.filter(task => {
            return task.flagged && !task.completed && !task.dropped;
        });

        return flaggedTasks.map(this.normalizeTask.bind(this));
    };

    /**
     * Get tasks by tag name
     * @param {string} tagName - Name of tag to filter by
     * @returns {Array} Array of tasks with the specified tag
     */
    lib.getTasksByTag = function(tagName) {
        const doc = Document.defaultDocument;
        const tasks = doc.flattenedTasks;

        const filtered = tasks.filter(task => {
            if (task.completed || task.dropped) return false;
            return task.tags.some(tag => tag.name === tagName);
        });

        return filtered.map(this.normalizeTask.bind(this));
    };

    /**
     * Get tasks by project name
     * @param {string} projectName - Name of project to filter by
     * @returns {Array} Array of tasks in the specified project
     */
    lib.getTasksByProject = function(projectName) {
        const doc = Document.defaultDocument;
        const tasks = doc.flattenedTasks;

        const filtered = tasks.filter(task => {
            if (task.completed || task.dropped) return false;
            return task.containingProject && task.containingProject.name === projectName;
        });

        return filtered.map(this.normalizeTask.bind(this));
    };

    /**
     * Get summary statistics across all tasks
     * @returns {Object} Summary statistics object
     */
    lib.getSummaryStats = function() {
        const doc = Document.defaultDocument;
        const tasks = doc.flattenedTasks;

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
        });

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
            modified: task.modified
        };
    };

    return lib;
})();
