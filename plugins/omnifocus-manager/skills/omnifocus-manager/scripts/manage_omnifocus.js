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
    if (project) {
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

    return JSON.stringify({
        success: true,
        message: `Created task: ${args.name}`,
        task: {
            id: task.id(),
            name: task.name(),
            project: project ? project.name() : 'Inbox',
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
 * Print help information
 */
function printHelp() {
    const help = `
OmniFocus Task Manager (JXA)

Usage:
    osascript -l JavaScript manage_omnifocus.js <action> [options]

Actions:
    Task Management:
      create     Create a new task
      update     Update an existing task
      complete   Mark a task as complete
      delete     Delete a task
      info       Get task information

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

Update-specific Options:
    --new-name <name>      New task name
    --due clear            Clear due date
    --defer clear          Clear defer date

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
