#!/usr/bin/osascript -l JavaScript
/**
 * OmniFocus Task Manager (JavaScript for Automation)
 *
 * Provides comprehensive task management capabilities through OmniFocus AppleScript API.
 *
 * Usage:
 *     osascript -l JavaScript manage_omnifocus.js <action> [options]
 *
 * Actions:
 *     create     Create a new task
 *     update     Update an existing task
 *     complete   Mark a task as complete
 *     delete     Delete a task
 *     info       Get task information
 *     list       List tasks with optional filters
 *     today      Show tasks due or deferred to today
 *     due-soon   Show tasks due within N days
 *     overdue    Show tasks past their due date
 *     flagged    Show all flagged tasks
 *     search     Search for tasks by name or note
 *
 * Examples:
 *     # Create a simple task
 *     osascript -l JavaScript manage_omnifocus.js create --name "Call dentist"
 *
 *     # Create task with project and due date
 *     osascript -l JavaScript manage_omnifocus.js create --name "Review proposal" --project "Work" --due "2025-12-25"
 *
 *     # Create task with tags, note, and flag
 *     osascript -l JavaScript manage_omnifocus.js create --name "Important meeting" --tags "urgent,meeting" --note "Prepare slides" --flagged
 *
 *     # Update a task
 *     osascript -l JavaScript manage_omnifocus.js update --name "Old name" --new-name "New name" --due "2025-12-30"
 *
 *     # Mark task complete
 *     osascript -l JavaScript manage_omnifocus.js complete --name "Task to complete"
 *
 *     # Delete task
 *     osascript -l JavaScript manage_omnifocus.js delete --name "Task to delete"
 *
 *     # Get task info
 *     osascript -l JavaScript manage_omnifocus.js info --name "Task name"
 */

ObjC.import('stdlib');
ObjC.import('Foundation');

/**
 * Load a JXA library by path relative to the skill root (current working directory).
 * Run from the skills/omnifocus-manager/ root so paths resolve correctly.
 * Libraries use IIFE pattern and return their namespace object via eval().
 */
function loadLibrary(relativePath) {
    const cwd = $.NSFileManager.defaultManager.currentDirectoryPath.js;
    const libPath = cwd + '/' + relativePath;
    const content = $.NSString.alloc.initWithContentsOfFileEncodingError(
        libPath, $.NSUTF8StringEncoding, null
    );
    if (!content) throw new Error('Cannot load library: ' + libPath);
    return eval(content.js);
}

const taskQuery    = loadLibrary('scripts/libraries/jxa/taskQuery.js');
const taskMutation = loadLibrary('scripts/libraries/jxa/taskMutation.js');
const argParser    = loadLibrary('scripts/libraries/jxa/argParser.js');
const dateUtils    = loadLibrary('scripts/libraries/jxa/dateUtils.js');

function run(argv) {
    const app = Application('OmniFocus');
    app.includeStandardAdditions = true;

    try {
        const args = argParser.parseArgs(argv);
        const action = args.action;

        switch (action) {
            case 'create':
                return createTask(app, args);
            case 'update':
                return updateTask(app, args);
            case 'complete':
                return completeTask(app, args);
            case 'delete':
                return deleteTask(app, args);
            case 'info':
                return getTaskInfo(app, args);
            case 'list':
                return listTasks(app, args);
            case 'today':
                return getTodayTasks(app, args);
            case 'due-soon':
                return getDueSoon(app, args);
            case 'overdue':
                return getOverdue(app, args);
            case 'flagged':
                return getFlagged(app, args);
            case 'search':
                return searchTasks(app, args);
            case 'project-info':
                return getProjectInfo(app, args);
            case 'project-update':
                return projectUpdate(app, args);
            case 'batch-update':
                return batchUpdate(app, args);
            case 'bulk-create':
                return bulkCreate(app, args);
            case 'help':
                return printHelp();
            default:
                return JSON.stringify({
                    success: false,
                    error: `Unknown action: ${action}. Use 'help' for usage information.`
                });
        }
    } catch (e) {
        return JSON.stringify({
            success: false,
            error: e.toString()
        });
    }
}


/**
 * Create a new task
 */
function createTask(app, args) {
    const doc = app.defaultDocument;

    if (!args.name) {
        throw new Error('Task name is required (use --name)');
    }

    // Mutual exclusion: --parent-id and --project
    if (args['parent-id'] && args.project) {
        return JSON.stringify({
            success: false,
            error: '--parent-id and --project are mutually exclusive'
        });
    }

    // Parse due date
    let dueDate = null;
    if (args.due) {
        dueDate = dateUtils.parseDate(args.due);
    }

    // Parse defer date
    let deferDate = null;
    if (args.defer) {
        deferDate = dateUtils.parseDate(args.defer);
    }

    // Find parent by ID (project or task)
    let parent = null;
    if (args['parent-id']) {
        const parentResult = taskMutation.findParent(doc, args['parent-id']);
        if (typeof parentResult.error === 'string') {
            throw new Error(parentResult.message);
        }
        parent = parentResult;
    }

    // Find or create project
    let project = null;
    if (args.project) {
        const projects = doc.flattenedProjects.whose({ name: args.project });
        if (projects.length > 0) {
            project = projects[0];
        } else if (args['create-project']) {
            // Create project if it doesn't exist and flag is set
            project = app.defaultDocument.Project({
                name: args.project
            });
            doc.projects.push(project);
        }
    }

    // Create task properties
    const taskProps = {
        name: args.name
    };

    if (args.note) {
        taskProps.note = args.note;
    }

    if (dueDate) {
        taskProps.dueDate = dueDate;
    }

    if (deferDate) {
        taskProps.deferDate = deferDate;
    }

    if (args.flagged) {
        taskProps.flagged = true;
    }

    if (args.estimate) {
        const minutes = dateUtils.parseEstimate(args.estimate);
        if (minutes > 0) {
            taskProps.estimatedMinutes = minutes;
        }
    }

    // Create the task
    let task;
    if (parent) {
        task = app.Task(taskProps);
        parent.tasks.push(task);
    } else if (project) {
        task = app.Task(taskProps);
        project.tasks.push(task);
    } else {
        // Add to inbox
        task = app.Task(taskProps);
        doc.inboxTasks.push(task);
    }

    // Add tags
    if (args.tags) {
        const tagNames = args.tags.split(',').map(t => t.trim());
        for (const tagName of tagNames) {
            let tag = doc.flattenedTags.whose({ name: tagName })[0];

            if (!tag && args['create-tags']) {
                // Create tag if it doesn't exist and flag is set
                tag = app.Tag({ name: tagName });
                doc.tags.push(tag);
            }

            if (tag) {
                task.addTag(tag);
            }
        }
    }

    var container = parent ? parent.name() : (project ? project.name() : 'Inbox');
    return JSON.stringify({
        success: true,
        message: `Created task: ${args.name}`,
        task: {
            id: task.id(),
            name: task.name(),
            parent: container,
            dueDate: task.dueDate() ? task.dueDate().toISOString() : null,
            flagged: task.flagged()
        }
    });
}

/**
 * Update an existing task
 */
function updateTask(app, args) {
    const doc = app.defaultDocument;

    if (!args.name && !args.id) {
        throw new Error('Task name or ID is required (use --name or --id)');
    }

    // Find the task
    let task;
    if (args.id) {
        task = doc.flattenedTasks.byId(args.id);
    } else {
        const tasks = doc.flattenedTasks.whose({ name: args.name });
        if (tasks.length === 0) {
            throw new Error(`Task not found: ${args.name}`);
        }
        if (tasks.length > 1) {
            throw new Error(`Multiple tasks found with name: ${args.name}. Use --id instead.`);
        }
        task = tasks[0];
    }

    // Update properties
    if (args['new-name']) {
        task.name = args['new-name'];
    }

    if (args.note !== undefined) {
        task.note = args.note;
    }

    if (args.due !== undefined) {
        if (args.due === 'clear') {
            task.dueDate = null;
        } else {
            task.dueDate = dateUtils.parseDate(args.due);
        }
    }

    if (args.defer !== undefined) {
        if (args.defer === 'clear') {
            task.deferDate = null;
        } else {
            task.deferDate = dateUtils.parseDate(args.defer);
        }
    }

    if (args.flagged !== undefined) {
        task.flagged = args.flagged;
    }

    if (args.estimate !== undefined) {
        const minutes = dateUtils.parseEstimate(args.estimate);
        task.estimatedMinutes = minutes;
    }

    if (args.project !== undefined) {
        if (args.project === 'inbox') {
            task.assignedContainer = doc.inboxTasks;
        } else {
            const projects = doc.flattenedProjects.whose({ name: args.project });
            if (projects.length > 0) {
                task.assignedContainer = projects[0];
            } else {
                throw new Error(`Project not found: ${args.project}`);
            }
        }
    }

    // Update tags
    if (args.tags !== undefined) {
        // Clear existing tags
        task.clearTags();

        // Add new tags
        if (args.tags !== '') {
            const tagNames = args.tags.split(',').map(t => t.trim());
            for (const tagName of tagNames) {
                const tag = doc.flattenedTags.whose({ name: tagName })[0];
                if (tag) {
                    task.addTag(tag);
                } else {
                    throw new Error(`Tag not found: ${tagName}`);
                }
            }
        }
    }

    return JSON.stringify({
        success: true,
        message: `Updated task: ${task.name()}`,
        task: {
            id: task.id(),
            name: task.name(),
            dueDate: task.dueDate() ? task.dueDate().toISOString() : null,
            flagged: task.flagged()
        }
    });
}

/**
 * Mark a task as complete
 */
function completeTask(app, args) {
    const doc = app.defaultDocument;

    if (!args.name && !args.id) {
        throw new Error('Task name or ID is required (use --name or --id)');
    }

    // Find the task
    let task;
    if (args.id) {
        task = doc.flattenedTasks.byId(args.id);
    } else {
        const tasks = doc.flattenedTasks.whose({ name: args.name });
        if (tasks.length === 0) {
            throw new Error(`Task not found: ${args.name}`);
        }
        if (tasks.length > 1) {
            throw new Error(`Multiple tasks found with name: ${args.name}. Use --id instead.`);
        }
        task = tasks[0];
    }

    // Mark as complete
    task.completed = true;

    return JSON.stringify({
        success: true,
        message: `Completed task: ${task.name()}`
    });
}

/**
 * Delete a task
 */
function deleteTask(app, args) {
    const doc = app.defaultDocument;

    if (!args.name && !args.id) {
        throw new Error('Task name or ID is required (use --name or --id)');
    }

    // Find the task
    let task;
    if (args.id) {
        task = doc.flattenedTasks.byId(args.id);
    } else {
        const tasks = doc.flattenedTasks.whose({ name: args.name });
        if (tasks.length === 0) {
            throw new Error(`Task not found: ${args.name}`);
        }
        if (tasks.length > 1) {
            throw new Error(`Multiple tasks found with name: ${args.name}. Use --id instead.`);
        }
        task = tasks[0];
    }

    const taskName = task.name();

    // Delete the task
    task.delete();

    return JSON.stringify({
        success: true,
        message: `Deleted task: ${taskName}`
    });
}

/**
 * Get task information
 */
function getTaskInfo(app, args) {
    if (!args.name && !args.id) {
        throw new Error('Task name or ID is required (use --name or --id)');
    }
    const doc = app.defaultDocument;
    const identifier = args.id || args.name;
    const info = taskQuery.getTaskInfo(doc, identifier);
    if (!info) {
        return JSON.stringify({ success: false, error: `Task not found: ${identifier}` });
    }
    if (info.multiple) {
        return JSON.stringify({ success: false, error: 'Multiple tasks found', tasks: info.tasks });
    }
    return JSON.stringify({ success: true, task: info });
}

/**
 * List tasks with optional filters
 */
function listTasks(app, args) {
    const doc = app.defaultDocument;
    const tasks = taskQuery.listTasks(doc, { filter: args.filter || 'active' });
    return JSON.stringify({ success: true, count: tasks.length, tasks });
}

/**
 * Get tasks due or deferred to today
 */
function getTodayTasks(app) {
    const doc = app.defaultDocument;
    const tasks = taskQuery.getTodayTasks(doc);
    return JSON.stringify({ success: true, count: tasks.length, tasks });
}

/**
 * Get tasks due within N days
 */
function getDueSoon(app, args) {
    const doc = app.defaultDocument;
    const days = args.days ? parseInt(args.days) : 7;
    const tasks = taskQuery.getDueSoon(doc, days);
    return JSON.stringify({ success: true, count: tasks.length, days, tasks });
}

/**
 * Get tasks past their due date
 */
function getOverdue(app) {
    const doc = app.defaultDocument;
    const now = new Date();
    const tasks = taskQuery.getOverdueTasks(doc).map(task => {
        const daysOverdue = Math.floor((now - new Date(task.dueDate)) / (1000 * 60 * 60 * 24));
        return Object.assign({}, task, { daysOverdue });
    });
    return JSON.stringify({ success: true, count: tasks.length, tasks });
}

/**
 * Get all flagged tasks
 */
function getFlagged(app) {
    const doc = app.defaultDocument;
    const tasks = taskQuery.getFlagged(doc);
    return JSON.stringify({ success: true, count: tasks.length, tasks });
}

/**
 * Search for tasks by name or note
 */
function searchTasks(app, args) {
    if (!args.query) throw new Error('Search query is required (use --query)');
    const doc = app.defaultDocument;
    const tasks = taskQuery.searchTasks(doc, args.query);
    return JSON.stringify({ success: true, count: tasks.length, query: args.query, tasks });
}

/**
 * Get project information
 */
function getProjectInfo(app, args) {
    if (!args.name && !args.id) {
        return JSON.stringify({ success: false, error: '--name or --id is required' });
    }
    const doc = app.defaultDocument;
    const identifier = args.id || args.name;
    const info = taskQuery.getProjectInfo(doc, identifier);

    if (!info) {
        return JSON.stringify({ success: false, error: 'Project not found: ' + identifier });
    }
    if (info.multiple) {
        return JSON.stringify({ success: false, error: 'Multiple projects found', projects: info.projects });
    }
    return JSON.stringify({ success: true, project: info });
}

/**
 * Update a project
 */
function projectUpdate(app, args) {
    if (!args.id) {
        return JSON.stringify({ success: false, error: '--id is required for project-update' });
    }

    const doc = app.defaultDocument;
    const project = taskMutation.findProject(doc, args.id);

    if (typeof project.error === 'string') {
        return JSON.stringify({ success: false, error: project.message });
    }

    // Check for mutual exclusion
    if (args.sequential && args.parallel) {
        return JSON.stringify({ success: false, error: '--sequential and --parallel are mutually exclusive' });
    }

    // Check that at least one mutation flag is provided
    var hasMutation = args['review-interval'] || args['note-remove-line'] ||
                      args.sequential || args.parallel;
    if (!hasMutation) {
        return JSON.stringify({ success: false, error: 'No mutation flags provided. Use --review-interval, --note-remove-line, --sequential, or --parallel' });
    }

    // Apply mutations
    if (args['review-interval']) {
        taskMutation.setReviewInterval(project, args['review-interval']);
    }

    if (args['note-remove-line']) {
        taskMutation.removeNoteLineMatching(project, args['note-remove-line']);
    }

    if (args.sequential) {
        project.sequential = true;
    }

    if (args.parallel) {
        project.sequential = false;
    }

    return JSON.stringify({
        success: true,
        message: 'Updated project: ' + project.name(),
        project: { id: project.id(), name: project.name() }
    });
}

/**
 * Batch update multiple tasks
 */
function batchUpdate(app, args) {
    if (!args.ids) {
        return JSON.stringify({ success: false, error: '--ids is required (comma-separated task IDs)' });
    }

    // Check that at least one mutation flag is provided
    if (args.due === undefined && args.defer === undefined) {
        return JSON.stringify({ success: false, error: 'No mutation flags provided. Use --due and/or --defer' });
    }

    const doc = app.defaultDocument;
    const ids = args.ids.split(',').map(function(id) { return id.trim(); });
    var updated = [];
    var skipped = [];

    for (var i = 0; i < ids.length; i++) {
        var taskId = ids[i];
        try {
            var task = doc.flattenedTasks.byId(taskId);
            if (!task) {
                skipped.push({ id: taskId, reason: 'not found' });
                continue;
            }

            if (args.due !== undefined) {
                if (args.due === 'clear') {
                    task.dueDate = null;
                } else {
                    task.dueDate = dateUtils.parseDate(args.due);
                }
            }

            if (args.defer !== undefined) {
                if (args.defer === 'clear') {
                    task.deferDate = null;
                } else {
                    task.deferDate = dateUtils.parseDate(args.defer);
                }
            }

            updated.push({ id: taskId, name: task.name() });
        } catch (e) {
            skipped.push({ id: taskId, reason: e.toString() });
        }
    }

    return JSON.stringify({
        success: true,
        message: 'Updated ' + updated.length + ' tasks (' + skipped.length + ' skipped)',
        updated: updated,
        skipped: skipped
    });
}

/**
 * Bulk-create a project with action groups and tasks from a JSON structure.
 *
 * JSON structure (via --json-file <path>):
 * {
 *   "project": "Project Name",
 *   "note": "Optional project note",
 *   "tags": ["AI Agent", "Claude Code"],  // applied as nested tags
 *   "sequential": false,
 *   "groups": [
 *     {
 *       "name": "Phase 1: Setup",
 *       "sequential": true,
 *       "tasks": [
 *         { "name": "Task 1", "note": "optional" },
 *         { "name": "Task 2" }
 *       ]
 *     }
 *   ]
 * }
 *
 * Returns a mapping of task names to OmniFocus IDs for the mapping file.
 */
function bulkCreate(app, args) {
    var doc = app.defaultDocument;

    if (!args['json-file']) {
        throw new Error('--json-file <path> is required for bulk-create');
    }

    // Read JSON file
    var jsonPath = args['json-file'];
    var jsonContent = $.NSString.alloc.initWithContentsOfFileEncodingError(
        jsonPath, $.NSUTF8StringEncoding, null
    );
    if (!jsonContent) {
        throw new Error('Cannot read JSON file: ' + jsonPath);
    }
    var spec = JSON.parse(jsonContent.js);

    if (!spec.project) {
        throw new Error('JSON must include a "project" field');
    }

    // Check for existing project with same name
    var existingProjects = doc.flattenedProjects.whose({ name: spec.project });
    if (existingProjects.length > 0) {
        return JSON.stringify({
            success: false,
            error: 'Project already exists: ' + spec.project + '. Use a different name or delete the existing project.',
            existingProjectId: existingProjects[0].id()
        });
    }

    // Create the project
    var project = app.defaultDocument.Project({ name: spec.project });
    if (spec.sequential !== undefined) {
        project.sequential = spec.sequential;
    }
    doc.projects.push(project);

    // Set project note
    if (spec.note) {
        project.note = spec.note;
    }

    // Create and apply tags (support nested tags like ["AI Agent", "Claude Code"])
    var tagsToApply = [];
    if (spec.tags && spec.tags.length > 0) {
        // Build nested tag path and apply the leaf tag
        var leafTag = taskMutation.findOrCreateNestedTag(app, doc, spec.tags, true);
        if (leafTag) tagsToApply.push(leafTag);

        // Also apply the parent tag if there are multiple levels
        if (spec.tags.length > 1) {
            var parentTag = taskMutation.findOrCreateTag(app, doc, spec.tags[0], true);
            if (parentTag) tagsToApply.push(parentTag);
        }
    }

    // Apply tags to project
    for (var t = 0; t < tagsToApply.length; t++) {
        project.addTag(tagsToApply[t]);
    }

    // Create groups and tasks, collect ID mapping
    var taskMapping = {};
    var createdCount = 0;

    if (spec.groups && spec.groups.length > 0) {
        for (var g = 0; g < spec.groups.length; g++) {
            var group = spec.groups[g];

            // Create action group (a task that contains subtasks)
            var groupTask = app.Task({ name: group.name });
            project.tasks.push(groupTask);

            if (group.sequential !== undefined) {
                // Note: in OmniFocus, task-level sequential ordering is set
                // by making the containing entity sequential
                // For action groups, we set it on the group task itself
            }

            // Apply tags to group task
            for (var gt = 0; gt < tagsToApply.length; gt++) {
                groupTask.addTag(tagsToApply[gt]);
            }

            taskMapping[group.name] = groupTask.id();
            createdCount++;

            // Create subtasks within the group
            if (group.tasks) {
                for (var ti = 0; ti < group.tasks.length; ti++) {
                    var taskSpec = group.tasks[ti];
                    var taskProps = { name: taskSpec.name };
                    if (taskSpec.note) taskProps.note = taskSpec.note;

                    var subtask = app.Task(taskProps);
                    groupTask.tasks.push(subtask);

                    // Apply tags to each subtask
                    for (var st = 0; st < tagsToApply.length; st++) {
                        subtask.addTag(tagsToApply[st]);
                    }

                    taskMapping[taskSpec.name] = subtask.id();
                    createdCount++;
                }
            }
        }
    }

    return JSON.stringify({
        success: true,
        message: 'Created project with ' + createdCount + ' tasks',
        project: {
            id: project.id(),
            name: project.name()
        },
        taskMapping: taskMapping
    });
}

/**
 * Print help information
 */
function printHelp() {
    const help = `
OmniFocus Task Manager (JXA)

Usage:
    osascript -l JavaScript manage_omnifocus.js <action> [options]

Actions:
    Task Management:
      create         Create a new task
      update         Update an existing task
      complete       Mark a task as complete
      delete         Delete a task
      info           Get task information
      batch-update   Batch update multiple tasks by ID
      bulk-create    Create project with action groups from JSON file

    Project Management:
      project-info   Get project details (subtasks, repeat rule, review interval)
      project-update Update project properties

    Query Tasks:
      list       List tasks with optional filters
      today      Show tasks due or deferred to today
      due-soon   Show tasks due within N days (default: 7)
      flagged    Show all flagged tasks
      search     Search for tasks by name or note

    Other:
      help       Show this help message

Common Options:
    --name <name>          Task name
    --id <id>              Task ID (persistent identifier)
    --note <note>          Task note/description
    --project <project>    Project name
    --tags <tags>          Comma-separated tag names
    --due <date>           Due date (ISO 8601: YYYY-MM-DD)
    --defer <date>         Defer/start date (ISO 8601: YYYY-MM-DD)
    --estimate <time>      Time estimate (e.g., 30m, 2h, 1h30m)
    --flagged              Flag the task (for create/update)

Create-specific Options:
    --create-project       Create project if it doesn't exist
    --create-tags          Create tags if they don't exist
    --parent-id <id>       Add task as subtask of project or task (mutually exclusive with --project)

Update-specific Options:
    --new-name <name>      New task name
    --due clear            Clear due date
    --defer clear          Clear defer date

Project-info Options:
    --name <name>          Project name
    --id <id>              Project ID

Project-update Options (--id required):
    --review-interval <N><unit>  Set review interval (e.g., 1month, 2weeks, 7days)
    --note-remove-line <text>    Remove first matching line from project note
    --sequential                 Set project to sequential ordering
    --parallel                   Set project to parallel ordering

Batch-update Options:
    --ids <id1,id2,...>    Comma-separated task IDs
    --due <date|clear>     Set or clear due date
    --defer <date|clear>   Set or clear defer date

Bulk-create Options:
    --json-file <path>     Path to JSON file with project structure

Examples:
    # Create a simple task
    osascript -l JavaScript manage_omnifocus.js create --name "Call dentist"

    # Create task with all options
    osascript -l JavaScript manage_omnifocus.js create \\
        --name "Important meeting" \\
        --project "Work" \\
        --tags "urgent,meeting" \\
        --due "2025-12-25T14:00:00" \\
        --defer "2025-12-20" \\
        --estimate "1h30m" \\
        --note "Prepare slides and agenda" \\
        --flagged \\
        --create-project \\
        --create-tags

    # Update a task
    osascript -l JavaScript manage_omnifocus.js update \\
        --name "Old task name" \\
        --new-name "New task name" \\
        --due "2025-12-30"

    # Complete a task
    osascript -l JavaScript manage_omnifocus.js complete --name "Task to complete"

    # Delete a task
    osascript -l JavaScript manage_omnifocus.js delete --name "Task to delete"

    # Get task information
    osascript -l JavaScript manage_omnifocus.js info --name "Task name"

    # List active tasks
    osascript -l JavaScript manage_omnifocus.js list --filter active

    # Show today's tasks
    osascript -l JavaScript manage_omnifocus.js today

    # Show tasks due in the next 7 days
    osascript -l JavaScript manage_omnifocus.js due-soon --days 7

    # Show all flagged tasks
    osascript -l JavaScript manage_omnifocus.js flagged

    # Search for tasks
    osascript -l JavaScript manage_omnifocus.js search --query "meeting"

Query Options:
    --filter <status>      Filter tasks: active, completed, dropped, all (for list)
    --days <N>             Number of days to look ahead (for due-soon, default: 7)
    --query <text>         Search term (for search)
`;

    return help;
}
