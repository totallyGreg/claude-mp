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

function run(argv) {
    const app = Application('OmniFocus');
    app.includeStandardAdditions = true;

    try {
        const args = parseArgs(argv);
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
 * Parse command line arguments
 */
function parseArgs(argv) {
    const args = {
        action: argv[0] || 'help'
    };

    for (let i = 1; i < argv.length; i++) {
        const arg = argv[i];

        if (arg.startsWith('--')) {
            const key = arg.substring(2);

            // Boolean flags
            if (key === 'flagged' || key === 'completed' || key === 'help') {
                args[key] = true;
            } else {
                // Value arguments
                i++;
                if (i < argv.length) {
                    args[key] = argv[i];
                }
            }
        }
    }

    return args;
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
        dueDate = parseDate(args.due);
    }

    // Parse defer date
    let deferDate = null;
    if (args.defer) {
        deferDate = parseDate(args.defer);
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
        const minutes = parseEstimate(args.estimate);
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
            task.dueDate = parseDate(args.due);
        }
    }

    if (args.defer !== undefined) {
        if (args.defer === 'clear') {
            task.deferDate = null;
        } else {
            task.deferDate = parseDate(args.defer);
        }
    }

    if (args.flagged !== undefined) {
        task.flagged = args.flagged;
    }

    if (args.estimate !== undefined) {
        const minutes = parseEstimate(args.estimate);
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
            const taskList = tasks.map(t => ({
                id: t.id(),
                name: t.name(),
                project: t.containingProject() ? t.containingProject().name() : 'Inbox'
            }));
            return JSON.stringify({
                success: false,
                error: 'Multiple tasks found',
                tasks: taskList
            });
        }
        task = tasks[0];
    }

    // Get task information
    const project = task.containingProject();
    const tags = task.tags().map(t => t.name());

    const info = {
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

    return JSON.stringify({
        success: true,
        task: info
    });
}

/**
 * List tasks with optional filters
 */
function listTasks(app, args) {
    const doc = app.defaultDocument;
    const tasks = doc.flattenedTasks();

    let filteredTasks = [];
    const filter = args.filter || 'active';

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

    const taskList = filteredTasks.map(task => formatTaskInfo(task));

    return JSON.stringify({
        success: true,
        count: taskList.length,
        tasks: taskList
    });
}

/**
 * Get tasks due or deferred to today
 */
function getTodayTasks(app, args) {
    const doc = app.defaultDocument;
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

    const taskList = todayTasks.map(task => formatTaskInfo(task));

    return JSON.stringify({
        success: true,
        count: taskList.length,
        tasks: taskList
    });
}

/**
 * Get tasks due within N days
 */
function getDueSoon(app, args) {
    const doc = app.defaultDocument;
    const tasks = doc.flattenedTasks();
    const days = args.days ? parseInt(args.days) : 7;

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

    const taskList = dueSoonTasks.map(task => formatTaskInfo(task));

    return JSON.stringify({
        success: true,
        count: taskList.length,
        days: days,
        tasks: taskList
    });
}

/**
 * Get all flagged tasks
 */
function getFlagged(app, args) {
    const doc = app.defaultDocument;
    const tasks = doc.flattenedTasks();

    const flaggedTasks = [];

    tasks.forEach(task => {
        if (task.completed() || task.dropped()) return;

        if (task.flagged()) {
            flaggedTasks.push(task);
        }
    });

    const taskList = flaggedTasks.map(task => formatTaskInfo(task));

    return JSON.stringify({
        success: true,
        count: taskList.length,
        tasks: taskList
    });
}

/**
 * Search for tasks by name or note
 */
function searchTasks(app, args) {
    const doc = app.defaultDocument;
    const tasks = doc.flattenedTasks();

    if (!args.query) {
        throw new Error('Search query is required (use --query)');
    }

    const searchTerm = args.query.toLowerCase();
    const matchingTasks = [];

    tasks.forEach(task => {
        if (task.completed()) return;

        const name = task.name() ? task.name().toLowerCase() : '';
        const note = task.note() ? task.note().toLowerCase() : '';

        if (name.includes(searchTerm) || note.includes(searchTerm)) {
            matchingTasks.push(task);
        }
    });

    const taskList = matchingTasks.map(task => formatTaskInfo(task));

    return JSON.stringify({
        success: true,
        count: taskList.length,
        query: args.query,
        tasks: taskList
    });
}

/**
 * Format task information for output
 */
function formatTaskInfo(task) {
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
}

/**
 * Parse date string to Date object
 */
function parseDate(dateStr) {
    // Try parsing ISO date: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
    const date = new Date(dateStr);

    if (isNaN(date.getTime())) {
        throw new Error(`Invalid date format: ${dateStr}. Use ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)`);
    }

    return date;
}

/**
 * Parse time estimate string to minutes
 */
function parseEstimate(estimateStr) {
    // Format: 30m, 2h, 1h30m
    const hoursMatch = estimateStr.match(/(\d+)h/);
    const minutesMatch = estimateStr.match(/(\d+)m/);

    let totalMinutes = 0;

    if (hoursMatch) {
        totalMinutes += parseInt(hoursMatch[1]) * 60;
    }

    if (minutesMatch) {
        totalMinutes += parseInt(minutesMatch[1]);
    }

    return totalMinutes;
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
