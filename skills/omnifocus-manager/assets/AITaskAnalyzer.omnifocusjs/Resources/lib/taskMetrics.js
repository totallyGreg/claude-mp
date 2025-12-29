/**
 * Task Metrics Utility Module
 *
 * Composable, reusable functions for collecting task data from OmniFocus.
 * Separates data collection from AI analysis for flexibility and testability.
 *
 * Usage:
 *   // In plugin actions (not yet implemented - Phase 2)
 *   // const TaskMetrics = PlugIn.library.moduleNamed('lib/taskMetrics');
 *   // const tasks = TaskMetrics.getTodayTasks();
 *
 * @version 2.2.0
 */

(() => {
    /**
     * Get tasks due or deferred to today
     * @returns {Array} Array of task objects with normalized data
     */
    function getTodayTasks() {
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

        return todayTasks.map(normalizeTask);
    }

    /**
     * Get overdue tasks (past due date)
     * @returns {Array} Array of overdue task objects
     */
    function getOverdueTasks() {
        const doc = Document.defaultDocument;
        const tasks = doc.flattenedTasks;

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const overdueTasks = tasks.filter(task => {
            if (task.completed || task.dropped) return false;
            const due = task.dueDate;
            return due && due < today;
        });

        return overdueTasks.map(normalizeTask);
    }

    /**
     * Get all flagged tasks
     * @returns {Array} Array of flagged task objects
     */
    function getFlaggedTasks() {
        const doc = Document.defaultDocument;
        const tasks = doc.flattenedTasks;

        const flaggedTasks = tasks.filter(task => {
            return task.flagged && !task.completed && !task.dropped;
        });

        return flaggedTasks.map(normalizeTask);
    }

    /**
     * Get tasks by tag name
     * @param {string} tagName - Name of tag to filter by
     * @returns {Array} Array of tasks with the specified tag
     */
    function getTasksByTag(tagName) {
        const doc = Document.defaultDocument;
        const tasks = doc.flattenedTasks;

        const filtered = tasks.filter(task => {
            if (task.completed || task.dropped) return false;
            return task.tags.some(tag => tag.name === tagName);
        });

        return filtered.map(normalizeTask);
    }

    /**
     * Get tasks by project name
     * @param {string} projectName - Name of project to filter by
     * @returns {Array} Array of tasks in the specified project
     */
    function getTasksByProject(projectName) {
        const doc = Document.defaultDocument;
        const tasks = doc.flattenedTasks;

        const filtered = tasks.filter(task => {
            if (task.completed || task.dropped) return false;
            return task.containingProject && task.containingProject.name === projectName;
        });

        return filtered.map(normalizeTask);
    }

    /**
     * Get summary statistics across all tasks
     * @returns {Object} Summary statistics object
     */
    function getSummaryStats() {
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
    }

    /**
     * Normalize task object to consistent data structure
     * @param {Task} task - OmniFocus task object
     * @returns {Object} Normalized task data
     * @private
     */
    function normalizeTask(task) {
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
    }

    /**
     * Export task data as JSON string
     * @param {Array|Object} data - Task data to export
     * @param {boolean} pretty - Whether to pretty-print the JSON
     * @returns {string} JSON string
     */
    function exportJSON(data, pretty = true) {
        return JSON.stringify(data, null, pretty ? 2 : 0);
    }

    /**
     * Export task array as CSV string
     * @param {Array} tasks - Array of normalized task objects
     * @returns {string} CSV string
     */
    function exportCSV(tasks) {
        if (!tasks || tasks.length === 0) {
            return "";
        }

        // CSV headers
        const headers = [
            "Name",
            "Project",
            "Tags",
            "Due Date",
            "Defer Date",
            "Flagged",
            "Completed",
            "Estimated Minutes",
            "Note"
        ];

        const rows = [headers.join(",")];

        tasks.forEach(task => {
            const row = [
                escapeCSV(task.name),
                escapeCSV(task.project || ""),
                escapeCSV(task.tags.join("; ")),
                task.dueDate ? task.dueDate.toISOString() : "",
                task.deferDate ? task.deferDate.toISOString() : "",
                task.flagged ? "Yes" : "No",
                task.completed ? "Yes" : "No",
                task.estimatedMinutes || "",
                escapeCSV(task.note)
            ];
            rows.push(row.join(","));
        });

        return rows.join("\n");
    }

    /**
     * Escape string for CSV format
     * @param {string} str - String to escape
     * @returns {string} Escaped string
     * @private
     */
    function escapeCSV(str) {
        if (!str) return "";
        const needsEscape = str.includes(",") || str.includes('"') || str.includes("\n");
        if (!needsEscape) return str;
        return '"' + str.replace(/"/g, '""') + '"';
    }

    // Public API
    // Note: Module export pattern to be determined in Phase 2
    // For now, these functions can be copied/used inline
    return {
        getTodayTasks,
        getOverdueTasks,
        getFlaggedTasks,
        getTasksByTag,
        getTasksByProject,
        getSummaryStats,
        exportJSON,
        exportCSV
    };
})();
