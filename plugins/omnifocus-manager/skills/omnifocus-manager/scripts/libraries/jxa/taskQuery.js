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
            completionDate: task.completionDate() ? task.completionDate().toISOString() : null,
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

    /**
     * Get inbox tasks (unprocessed capture items)
     * @param {Document} doc - OmniFocus document
     * @returns {Array<Object>} Array of inbox task objects
     */
    taskQuery.getInboxTasks = function(doc) {
        const tasks = doc.inboxTasks();
        return tasks
            .filter(t => !t.completed())
            .map(task => this.formatTaskInfo(task));
    };

    /**
     * Get active projects with no available next actions (stalled)
     * @param {Document} doc - OmniFocus document
     * @param {number} limit - Max results (default: 50)
     * @returns {Array<Object>} Array of stalled project objects
     */
    taskQuery.getStalledProjects = function(doc, limit) {
        const cap = limit || 50;
        const projects = doc.flattenedProjects();
        const stalled = [];

        projects.forEach(project => {
            const status = project.status() ? project.status().toString() : '';
            if (!status.includes('active')) return;

            const allTasks = project.tasks();
            if (allTasks.length === 0) return; // skip empty projects

            if (project.numberOfAvailableTasks() === 0) {
                stalled.push({
                    id: project.id(),
                    name: project.name(),
                    status: status,
                    totalTasks: allTasks.length,
                    availableTasks: 0,
                    modifiedDate: project.modificationDate() ? project.modificationDate().toISOString() : null
                });
            }
        });

        return stalled.slice(0, cap);
    };

    /**
     * Get tasks tagged with a waiting-for tag, sorted by age (oldest first)
     * @param {Document} doc - OmniFocus document
     * @param {string} tagPattern - Tag name pattern to match (default: 'waiting')
     * @returns {Array<Object>} Array of waiting tasks with ageDays field
     */
    taskQuery.getWaitingForTasks = function(doc, tagPattern) {
        const pattern = (tagPattern || 'waiting').toLowerCase();
        const tasks = doc.flattenedTasks();
        const now = new Date();
        const waitingTasks = [];

        tasks.forEach(task => {
            if (task.completed() || task.dropped()) return;
            const hasWaitingTag = task.tags().some(tag => tag.name().toLowerCase().includes(pattern));
            if (hasWaitingTag) {
                const info = this.formatTaskInfo(task);
                const creationDate = task.creationDate();
                const ageDays = creationDate
                    ? Math.floor((now - creationDate) / (1000 * 60 * 60 * 24))
                    : null;
                waitingTasks.push(Object.assign({}, info, { ageDays: ageDays }));
            }
        });

        return waitingTasks.sort(function(a, b) { return (b.ageDays || 0) - (a.ageDays || 0); });
    };

    /**
     * Get on-hold projects (Someday/Maybe candidates)
     * @param {Document} doc - OmniFocus document
     * @returns {Array<Object>} Array of on-hold project objects
     */
    taskQuery.getSomedayMaybeProjects = function(doc) {
        const projects = doc.flattenedProjects();
        const result = [];

        projects.forEach(project => {
            const status = project.status() ? project.status().toString() : '';
            if (!status.includes('on hold')) return;

            result.push({
                id: project.id(),
                name: project.name(),
                status: status,
                note: project.note() || null,
                modifiedDate: project.modificationDate() ? project.modificationDate().toISOString() : null,
                taskCount: project.tasks().length
            });
        });

        return result;
    };

    /**
     * Get recently completed tasks
     * @param {Document} doc - OmniFocus document
     * @param {number} days - How far back to look (default: 7)
     * @param {number} limit - Max results (default: 100)
     * @returns {Array<Object>} Array of completed task objects, newest first
     */
    taskQuery.getRecentlyCompleted = function(doc, days, limit) {
        const lookback = days || 7;
        const cap = limit || 100;
        const tasks = doc.flattenedTasks();
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - lookback);
        const completed = [];

        tasks.forEach(task => {
            if (!task.completed()) return;
            const completionDate = task.completionDate();
            if (completionDate && completionDate >= cutoffDate) {
                completed.push(task);
            }
        });

        completed.sort(function(a, b) {
            const dateA = a.completionDate() ? a.completionDate().getTime() : 0;
            const dateB = b.completionDate() ? b.completionDate().getTime() : 0;
            return dateB - dateA;
        });

        return completed.slice(0, cap).map(task => this.formatTaskInfo(task));
    };

    /**
     * Get active projects not modified in the last N days (neglected)
     * @param {Document} doc - OmniFocus document
     * @param {number} thresholdDays - Days without modification (default: 30)
     * @returns {Array<Object>} Array of neglected project objects with daysSinceModified
     */
    taskQuery.getNeglectedProjects = function(doc, thresholdDays) {
        const threshold = thresholdDays || 30;
        const projects = doc.flattenedProjects();
        const now = new Date();
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - threshold);
        const neglected = [];

        projects.forEach(project => {
            const status = project.status() ? project.status().toString() : '';
            if (!status.includes('active')) return;

            const modDate = project.modificationDate();
            if (!modDate || modDate < cutoffDate) {
                const daysSinceModified = modDate
                    ? Math.floor((now - modDate) / (1000 * 60 * 60 * 24))
                    : null;
                neglected.push({
                    id: project.id(),
                    name: project.name(),
                    status: status,
                    modifiedDate: modDate ? modDate.toISOString() : null,
                    daysSinceModified: daysSinceModified,
                    availableTasks: project.numberOfAvailableTasks(),
                    totalTasks: project.tasks().length
                });
            }
        });

        return neglected.sort(function(a, b) {
            return (b.daysSinceModified || 9999) - (a.daysSinceModified || 9999);
        });
    };

    /**
     * Get folder/project hierarchy for structural analysis
     * @param {Document} doc - OmniFocus document
     * @returns {Array<Object>} Array of folder objects with nested projects and task counts
     */
    taskQuery.getFolderHierarchy = function(doc) {
        const folders = doc.folders();
        const result = [];

        folders.forEach(folder => {
            const directProjects = folder.projects();
            const projectSummaries = directProjects.map(function(project) {
                const status = project.status() ? project.status().toString() : '';
                return {
                    id: project.id(),
                    name: project.name(),
                    status: status,
                    availableTasks: project.numberOfAvailableTasks(),
                    totalTasks: project.tasks().length
                };
            });

            result.push({
                id: folder.id(),
                name: folder.name(),
                projectCount: directProjects.length,
                activeProjectCount: projectSummaries.filter(function(p) { return p.status.includes('active'); }).length,
                projects: projectSummaries
            });
        });

        return result;
    };

    return taskQuery;
})();
