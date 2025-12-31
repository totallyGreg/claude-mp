/**
 * Task Mutation Library for OmniFocus JXA
 *
 * Provides create, update, delete, and complete operations for OmniFocus tasks.
 *
 * Usage (load in JXA script):
 *   ObjC.import('Foundation');
 *   const taskMutation = eval($.NSString.alloc.initWithContentsOfFileEncodingError(
 *       'libraries/jxa/taskMutation.js', $.NSUTF8StringEncoding, null
 *   ).js);
 *
 *   const app = Application('OmniFocus');
 *   const doc = app.defaultDocument;
 *   const task = taskMutation.createTask(app, doc, {name: "Test task"});
 */

(() => {
    const taskMutation = {};

    /**
     * Find or create a project
     * @param {Application} app - OmniFocus application
     * @param {Document} doc - OmniFocus document
     * @param {string} projectName - Project name
     * @param {boolean} createIfMissing - Create project if it doesn't exist
     * @returns {Project|null} Project object or null
     */
    taskMutation.findOrCreateProject = function(app, doc, projectName, createIfMissing = false) {
        const projects = doc.flattenedProjects.whose({ name: projectName });

        if (projects.length > 0) {
            return projects[0];
        }

        if (createIfMissing) {
            const project = app.defaultDocument.Project({ name: projectName });
            doc.projects.push(project);
            return project;
        }

        return null;
    };

    /**
     * Find or create a tag
     * @param {Application} app - OmniFocus application
     * @param {Document} doc - OmniFocus document
     * @param {string} tagName - Tag name
     * @param {boolean} createIfMissing - Create tag if it doesn't exist
     * @returns {Tag|null} Tag object or null
     */
    taskMutation.findOrCreateTag = function(app, doc, tagName, createIfMissing = false) {
        const tag = doc.flattenedTags.whose({ name: tagName })[0];

        if (tag) {
            return tag;
        }

        if (createIfMissing) {
            const newTag = app.Tag({ name: tagName });
            doc.tags.push(newTag);
            return newTag;
        }

        return null;
    };

    /**
     * Find a task by name or ID
     * @param {Document} doc - OmniFocus document
     * @param {string} nameOrId - Task name or ID
     * @returns {Task|Object} Task object, or object with error/multiple tasks info
     */
    taskMutation.findTask = function(doc, nameOrId) {
        // Try to find by ID first
        try {
            const task = doc.flattenedTasks.byId(nameOrId);
            if (task) {
                return task;
            }
        } catch (e) {
            // ID not found, try by name
        }

        // Find by name
        const tasks = doc.flattenedTasks.whose({ name: nameOrId });

        if (tasks.length === 0) {
            return { error: 'not_found', message: `Task not found: ${nameOrId}` };
        }

        if (tasks.length > 1) {
            return {
                error: 'multiple',
                message: `Multiple tasks found with name: ${nameOrId}. Use ID instead.`,
                tasks: tasks.map(t => ({ id: t.id(), name: t.name() }))
            };
        }

        return tasks[0];
    };

    /**
     * Create a new task
     * @param {Application} app - OmniFocus application
     * @param {Document} doc - OmniFocus document
     * @param {Object} options - Task options
     * @param {string} options.name - Task name (required)
     * @param {string} options.note - Task note
     * @param {Date|string} options.due - Due date
     * @param {Date|string} options.defer - Defer date
     * @param {boolean} options.flagged - Flag status
     * @param {number} options.estimatedMinutes - Time estimate in minutes
     * @param {string} options.project - Project name
     * @param {boolean} options.createProject - Create project if it doesn't exist
     * @param {string} options.tags - Comma-separated tag names
     * @param {boolean} options.createTags - Create tags if they don't exist
     * @returns {Object} Created task information
     */
    taskMutation.createTask = function(app, doc, options) {
        if (!options.name) {
            throw new Error('Task name is required');
        }

        // Find or create project
        let project = null;
        if (options.project) {
            project = this.findOrCreateProject(app, doc, options.project, options.createProject);
        }

        // Build task properties
        const taskProps = {
            name: options.name
        };

        if (options.note) {
            taskProps.note = options.note;
        }

        if (options.due) {
            taskProps.dueDate = options.due instanceof Date ? options.due : new Date(options.due);
        }

        if (options.defer) {
            taskProps.deferDate = options.defer instanceof Date ? options.defer : new Date(options.defer);
        }

        if (options.flagged) {
            taskProps.flagged = true;
        }

        if (options.estimatedMinutes) {
            taskProps.estimatedMinutes = options.estimatedMinutes;
        }

        // Create the task
        let task;
        if (project) {
            task = app.Task(taskProps);
            project.tasks.push(task);
        } else {
            task = app.Task(taskProps);
            doc.inboxTasks.push(task);
        }

        // Add tags
        if (options.tags) {
            const tagNames = typeof options.tags === 'string'
                ? options.tags.split(',').map(t => t.trim())
                : options.tags;

            for (const tagName of tagNames) {
                const tag = this.findOrCreateTag(app, doc, tagName, options.createTags);
                if (tag) {
                    task.addTag(tag);
                }
            }
        }

        return {
            id: task.id(),
            name: task.name(),
            project: project ? project.name() : 'Inbox',
            dueDate: task.dueDate() ? task.dueDate().toISOString() : null,
            flagged: task.flagged()
        };
    };

    /**
     * Update an existing task
     * @param {Application} app - OmniFocus application
     * @param {Document} doc - OmniFocus document
     * @param {string} taskIdentifier - Task name or ID
     * @param {Object} updates - Properties to update
     * @param {string} updates.name - New task name
     * @param {string} updates.note - New task note
     * @param {Date|string|null} updates.due - Due date (null or 'clear' to clear)
     * @param {Date|string|null} updates.defer - Defer date (null or 'clear' to clear)
     * @param {boolean} updates.flagged - Flag status
     * @param {number} updates.estimatedMinutes - Time estimate
     * @param {string} updates.project - Project name ('inbox' for inbox)
     * @param {string|Array} updates.tags - Tags (comma-separated or array)
     * @returns {Object} Updated task information
     */
    taskMutation.updateTask = function(app, doc, taskIdentifier, updates) {
        // Find the task
        const taskResult = this.findTask(doc, taskIdentifier);

        if (taskResult.error) {
            throw new Error(taskResult.message);
        }

        const task = taskResult;

        // Update properties
        if (updates.name !== undefined) {
            task.name = updates.name;
        }

        if (updates.note !== undefined) {
            task.note = updates.note;
        }

        if (updates.due !== undefined) {
            if (updates.due === null || updates.due === 'clear') {
                task.dueDate = null;
            } else {
                task.dueDate = updates.due instanceof Date ? updates.due : new Date(updates.due);
            }
        }

        if (updates.defer !== undefined) {
            if (updates.defer === null || updates.defer === 'clear') {
                task.deferDate = null;
            } else {
                task.deferDate = updates.defer instanceof Date ? updates.defer : new Date(updates.defer);
            }
        }

        if (updates.flagged !== undefined) {
            task.flagged = updates.flagged;
        }

        if (updates.estimatedMinutes !== undefined) {
            task.estimatedMinutes = updates.estimatedMinutes;
        }

        if (updates.project !== undefined) {
            if (updates.project === 'inbox') {
                task.assignedContainer = doc.inboxTasks;
            } else {
                const project = this.findOrCreateProject(app, doc, updates.project, false);
                if (project) {
                    task.assignedContainer = project;
                } else {
                    throw new Error(`Project not found: ${updates.project}`);
                }
            }
        }

        // Update tags
        if (updates.tags !== undefined) {
            task.clearTags();

            if (updates.tags !== '' && updates.tags !== null) {
                const tagNames = typeof updates.tags === 'string'
                    ? updates.tags.split(',').map(t => t.trim())
                    : updates.tags;

                for (const tagName of tagNames) {
                    const tag = this.findOrCreateTag(app, doc, tagName, false);
                    if (tag) {
                        task.addTag(tag);
                    }
                }
            }
        }

        return {
            id: task.id(),
            name: task.name(),
            dueDate: task.dueDate() ? task.dueDate().toISOString() : null,
            flagged: task.flagged()
        };
    };

    /**
     * Mark a task as complete
     * @param {Document} doc - OmniFocus document
     * @param {string} taskIdentifier - Task name or ID
     * @returns {Object} Result object
     */
    taskMutation.completeTask = function(doc, taskIdentifier) {
        // Find the task
        const taskResult = this.findTask(doc, taskIdentifier);

        if (taskResult.error) {
            throw new Error(taskResult.message);
        }

        const task = taskResult;
        const taskName = task.name();

        // Mark as complete
        task.completed = true;

        return {
            success: true,
            message: `Completed task: ${taskName}`,
            id: task.id(),
            name: taskName
        };
    };

    /**
     * Mark a task as incomplete
     * @param {Document} doc - OmniFocus document
     * @param {string} taskIdentifier - Task name or ID
     * @returns {Object} Result object
     */
    taskMutation.markIncomplete = function(doc, taskIdentifier) {
        // Find the task
        const taskResult = this.findTask(doc, taskIdentifier);

        if (taskResult.error) {
            throw new Error(taskResult.message);
        }

        const task = taskResult;
        const taskName = task.name();

        // Mark as incomplete
        task.completed = false;

        return {
            success: true,
            message: `Marked incomplete: ${taskName}`,
            id: task.id(),
            name: taskName
        };
    };

    /**
     * Delete a task
     * @param {Document} doc - OmniFocus document
     * @param {string} taskIdentifier - Task name or ID
     * @returns {Object} Result object
     */
    taskMutation.deleteTask = function(doc, taskIdentifier) {
        // Find the task
        const taskResult = this.findTask(doc, taskIdentifier);

        if (taskResult.error) {
            throw new Error(taskResult.message);
        }

        const task = taskResult;
        const taskName = task.name();
        const taskId = task.id();

        // Delete the task
        task.delete();

        return {
            success: true,
            message: `Deleted task: ${taskName}`,
            id: taskId,
            name: taskName
        };
    };

    return taskMutation;
})();
