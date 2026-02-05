/**
 * Task Query Library for OmniFocus JXA
 *
 * Provides query operations for OmniFocus tasks.
 *
 * Usage (load in JXA script):
 *   ObjC.import('Foundation');
 *   const taskQuery = eval($.NSString.alloc.initWithContentsOfFileEncodingError(
 *       'libraries/jxa/taskQuery.js', $.NSUTF8StringEncoding, null
 *   ).js);
 *
 *   const app = Application('OmniFocus');
 *   const doc = app.defaultDocument;
 *   const tasks = taskQuery.getTodayTasks(doc);
 */

(() => {
    const taskQuery = {};

    /**
     * Format task information for output
     * @param {Task} task - OmniFocus task object
     * @returns {Object} Formatted task information
     */
    taskQuery.formatTaskInfo = function(task) {
        const project = task.containingProject();
        const tags = task.tags().map(t => t.name());

        return {
            id: task.id(),
            name: task.name(),
            note: task.note(),
            completed: task.completed(),
            flagged: task.flagged(),
            dueDate: task.dueDate() ? task.dueDate().toISOString() : null,
            deferDate: task.deferDate() ? task.deferDate().toISOString() : null,
            estimatedMinutes: task.estimatedMinutes(),
            project: project ? project.name() : 'Inbox',
            tags: tags
        };
    };

    /**
     * Get task information by name or ID
     * @param {Document} doc - OmniFocus document
     * @param {string} nameOrId - Task name or ID
     * @returns {Object|null} Task information or null if not found
     */
    taskQuery.getTaskInfo = function(doc, nameOrId) {
        let task;

        // Try to find by ID first
        try {
            task = doc.flattenedTasks.byId(nameOrId);
            if (task) {
                const project = task.containingProject();
                const tags = task.tags().map(t => t.name());

                return {
                    id: task.id(),
                    name: task.name(),
                    note: task.note(),
                    completed: task.completed(),
                    flagged: task.flagged(),
                    dueDate: task.dueDate() ? task.dueDate().toISOString() : null,
                    deferDate: task.deferDate() ? task.deferDate().toISOString() : null,
                    completionDate: task.completionDate() ? task.completionDate().toISOString() : null,
                    estimatedMinutes: task.estimatedMinutes(),
                    project: project ? project.name() : 'Inbox',
                    tags: tags
                };
            }
        } catch (e) {
            // ID not found, try by name
        }

        // Find by name
        const tasks = doc.flattenedTasks.whose({ name: nameOrId });
        if (tasks.length === 0) {
            return null;
        }

        if (tasks.length > 1) {
            // Multiple tasks found, return array
            return {
                multiple: true,
                tasks: tasks.map(t => ({
                    id: t.id(),
                    name: t.name(),
                    project: t.containingProject() ? t.containingProject().name() : 'Inbox'
                }))
            };
        }

        task = tasks[0];
        const project = task.containingProject();
        const tags = task.tags().map(t => t.name());

        return {
            id: task.id(),
            name: task.name(),
            note: task.note(),
            completed: task.completed(),
            flagged: task.flagged(),
            dueDate: task.dueDate() ? task.dueDate().toISOString() : null,
            deferDate: task.deferDate() ? task.deferDate().toISOString() : null,
            completionDate: task.completionDate() ? task.completionDate().toISOString() : null,
            estimatedMinutes: task.estimatedMinutes(),
            project: project ? project.name() : 'Inbox',
            tags: tags
        };
    };

    /**
     * List tasks with optional filters
     * @param {Document} doc - OmniFocus document
     * @param {Object} options - Filter options
     * @param {string} options.filter - Filter: 'active', 'completed', 'dropped', 'all'
     * @returns {Array<Object>} Array of formatted task objects
     */
    taskQuery.listTasks = function(doc, options = {}) {
        const tasks = doc.flattenedTasks();
        const filter = options.filter || 'active';
        const filteredTasks = [];

        tasks.forEach(task => {
            if (filter === 'all') {
                filteredTasks.push(task);
            } else if (filter === 'active' && !task.completed() && !task.dropped()) {
                filteredTasks.push(task);
            } else if (filter === 'completed' && task.completed()) {
                filteredTasks.push(task);
            } else if (filter === 'dropped' && task.dropped()) {
                filteredTasks.push(task);
            }
        });

        return filteredTasks.map(task => this.formatTaskInfo(task));
    };

    /**
     * Get tasks due or deferred to today
     * @param {Document} doc - OmniFocus document
     * @param {Object} options - Query options (currently unused)
     * @returns {Array<Object>} Array of tasks due or deferred to today
     */
    taskQuery.getTodayTasks = function(doc, options = {}) {
        const tasks = doc.flattenedTasks();
        const now = new Date();
        const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const todayEnd = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
        const todayTasks = [];

        tasks.forEach(task => {
            if (task.completed() || task.dropped()) return;

            const dueDate = task.dueDate();
            const deferDate = task.deferDate();

            const isDueToday = dueDate && dueDate >= todayStart && dueDate < todayEnd;
            const isDeferredToday = deferDate && deferDate >= todayStart && deferDate < todayEnd;

            if (isDueToday || isDeferredToday) {
                todayTasks.push(task);
            }
        });

        return todayTasks.map(task => this.formatTaskInfo(task));
    };

    /**
     * Get tasks due within N days
     * @param {Document} doc - OmniFocus document
     * @param {number} days - Number of days to look ahead (default: 7)
     * @returns {Array<Object>} Array of tasks due soon
     */
    taskQuery.getDueSoon = function(doc, days = 7) {
        const tasks = doc.flattenedTasks();
        const now = new Date();
        const futureDate = new Date();
        futureDate.setDate(futureDate.getDate() + days);
        const dueSoonTasks = [];

        tasks.forEach(task => {
            if (task.completed() || task.dropped()) return;

            const dueDate = task.dueDate();
            if (dueDate && dueDate >= now && dueDate <= futureDate) {
                dueSoonTasks.push(task);
            }
        });

        return dueSoonTasks.map(task => this.formatTaskInfo(task));
    };

    /**
     * Get all flagged tasks
     * @param {Document} doc - OmniFocus document
     * @returns {Array<Object>} Array of flagged tasks
     */
    taskQuery.getFlagged = function(doc) {
        const tasks = doc.flattenedTasks();
        const flaggedTasks = [];

        tasks.forEach(task => {
            if (task.completed() || task.dropped()) return;

            if (task.flagged()) {
                flaggedTasks.push(task);
            }
        });

        return flaggedTasks.map(task => this.formatTaskInfo(task));
    };

    /**
     * Get overdue tasks
     * @param {Document} doc - OmniFocus document
     * @returns {Array<Object>} Array of overdue tasks
     */
    taskQuery.getOverdueTasks = function(doc) {
        const tasks = doc.flattenedTasks();
        const now = new Date();
        const overdueTasks = [];

        tasks.forEach(task => {
            if (task.completed() || task.dropped()) return;

            const dueDate = task.dueDate();
            if (dueDate && dueDate < now) {
                overdueTasks.push(task);
            }
        });

        return overdueTasks.map(task => this.formatTaskInfo(task));
    };

    /**
     * Search for tasks by name or note
     * @param {Document} doc - OmniFocus document
     * @param {string} searchTerm - Search term
     * @returns {Array<Object>} Array of matching tasks
     */
    taskQuery.searchTasks = function(doc, searchTerm) {
        const tasks = doc.flattenedTasks();
        const lowerSearchTerm = searchTerm.toLowerCase();
        const matchingTasks = [];

        tasks.forEach(task => {
            if (task.completed()) return;

            const name = task.name() ? task.name().toLowerCase() : '';
            const note = task.note() ? task.note().toLowerCase() : '';

            if (name.includes(lowerSearchTerm) || note.includes(lowerSearchTerm)) {
                matchingTasks.push(task);
            }
        });

        return matchingTasks.map(task => this.formatTaskInfo(task));
    };

    return taskQuery;
})();
