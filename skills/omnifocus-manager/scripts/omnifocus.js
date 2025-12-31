#!/usr/bin/osascript -l JavaScript

/**
 * OmniFocus CLI Tool with JSON I/O
 *
 * Modern command-line interface for OmniFocus automation using modular libraries.
 *
 * Input: JSON via CLI args or stdin
 * Output: Structured JSON (success, data, error, metadata)
 *
 * Usage:
 *   osascript -l JavaScript scripts/omnifocus.js query '{"filter":"today"}'
 *   echo '{"filter":"today"}' | osascript -l JavaScript scripts/omnifocus.js query
 *   osascript -l JavaScript scripts/omnifocus.js create '{"name":"Task","project":"Work"}'
 *
 * Version: 3.0.0
 */

ObjC.import('Foundation');

// ============================================================================
// Library Loading
// ============================================================================

function loadLibrary(filename) {
    const scriptDir = $.NSString.alloc.initWithUTF8String($.getenv('_'))
        .stringByDeletingLastPathComponent.js;
    const libPath = `${scriptDir}/../libraries/jxa/${filename}`;

    try {
        const content = $.NSString.alloc.initWithContentsOfFileEncodingError(
            libPath,
            $.NSUTF8StringEncoding,
            null
        );

        if (!content) {
            throw new Error(`Library not found: ${libPath}`);
        }

        return eval(content.js);
    } catch (error) {
        throw new Error(`Failed to load library ${filename}: ${error.message}`);
    }
}

// Load required libraries
const taskQuery = loadLibrary('taskQuery.js');
const taskMutation = loadLibrary('taskMutation.js');
const dateUtils = loadLibrary('dateUtils.js');

// ============================================================================
// Input Parsing
// ============================================================================

function parseInput(argv) {
    if (argv.length === 0) {
        throw new Error('No action specified. Usage: omnifocus.js <action> [json]');
    }

    const action = argv[0];
    let params = {};

    // Try to parse JSON from second argument
    if (argv.length > 1) {
        try {
            params = JSON.parse(argv[1]);
        } catch (error) {
            throw new Error(`Invalid JSON input: ${error.message}`);
        }
    }

    // TODO: Support stdin for piped input
    // For now, just use argv[1]

    return { action, params };
}

// ============================================================================
// Action Execution
// ============================================================================

function executeAction(input, app, doc) {
    const { action, params } = input;

    switch (action) {
        case 'query':
            return executeQuery(params, doc);

        case 'create':
            return executeCreate(params, app, doc);

        case 'update':
            return executeUpdate(params, app, doc);

        case 'complete':
            return executeComplete(params, doc);

        case 'delete':
            return executeDelete(params, doc);

        case 'list':
            return executeList(params, doc);

        case 'search':
            return executeSearch(params, doc);

        case 'help':
            return getHelp();

        default:
            throw new Error(`Unknown action: ${action}. Use 'help' for available actions.`);
    }
}

// ============================================================================
// Query Actions
// ============================================================================

function executeQuery(params, doc) {
    const filter = params.filter || 'today';
    let tasks;

    switch (filter) {
        case 'today':
            tasks = taskQuery.getTodayTasks(doc);
            break;

        case 'overdue':
            tasks = taskQuery.getOverdueTasks(doc);
            break;

        case 'flagged':
            tasks = taskQuery.getFlagged(doc);
            break;

        case 'due-soon':
            const days = params.days || 7;
            tasks = taskQuery.getDueSoon(doc, days);
            break;

        default:
            throw new Error(`Unknown filter: ${filter}`);
    }

    return {
        tasks: tasks,
        summary: {
            total: tasks.length,
            filter: filter,
            days: params.days
        }
    };
}

function executeList(params, doc) {
    const filter = params.filter || 'active';
    const allTasks = doc.flattenedTasks();

    let tasks;

    switch (filter) {
        case 'active':
            tasks = allTasks.filter(t => !t.completed() && !t.dropped());
            break;

        case 'completed':
            tasks = allTasks.filter(t => t.completed());
            break;

        case 'dropped':
            tasks = allTasks.filter(t => t.dropped());
            break;

        case 'all':
            tasks = allTasks;
            break;

        default:
            throw new Error(`Unknown filter: ${filter}`);
    }

    return {
        tasks: tasks.map(t => taskQuery.formatTaskInfo(t)),
        summary: {
            total: tasks.length,
            filter: filter
        }
    };
}

function executeSearch(params, doc) {
    const query = params.query || params.q;

    if (!query) {
        throw new Error('Search requires "query" parameter');
    }

    const tasks = taskQuery.searchTasks(doc, query);

    return {
        tasks: tasks,
        summary: {
            total: tasks.length,
            query: query
        }
    };
}

// ============================================================================
// Mutation Actions
// ============================================================================

function executeCreate(params, app, doc) {
    if (!params.name) {
        throw new Error('Create requires "name" parameter');
    }

    const options = {
        name: params.name,
        note: params.note,
        project: params.project,
        tags: params.tags,
        due: params.due ? dateUtils.parseDate(params.due) : null,
        defer: params.defer ? dateUtils.parseDate(params.defer) : null,
        flagged: params.flagged || false,
        estimate: params.estimate,
        createProject: params.createProject || false,
        createTags: params.createTags || false
    };

    const result = taskMutation.createTask(app, doc, options);

    return {
        task: result,
        message: `Created task: ${result.name}`
    };
}

function executeUpdate(params, app, doc) {
    const taskName = params.name;
    const taskId = params.id;

    if (!taskName && !taskId) {
        throw new Error('Update requires "name" or "id" parameter');
    }

    const updates = {
        newName: params.newName,
        note: params.note,
        project: params.project,
        tags: params.tags,
        due: params.due ? (params.due === 'clear' ? null : dateUtils.parseDate(params.due)) : undefined,
        defer: params.defer ? (params.defer === 'clear' ? null : dateUtils.parseDate(params.defer)) : undefined,
        flagged: params.flagged
    };

    const result = taskMutation.updateTask(app, doc, taskName || taskId, updates);

    return {
        task: result,
        message: `Updated task: ${result.name}`
    };
}

function executeComplete(params, doc) {
    const taskName = params.name;
    const taskId = params.id;

    if (!taskName && !taskId) {
        throw new Error('Complete requires "name" or "id" parameter');
    }

    const result = taskMutation.completeTask(doc, taskName || taskId);

    return {
        task: result,
        message: `Completed task: ${result.name}`
    };
}

function executeDelete(params, doc) {
    const taskName = params.name;
    const taskId = params.id;

    if (!taskName && !taskId) {
        throw new Error('Delete requires "name" or "id" parameter');
    }

    const result = taskMutation.deleteTask(doc, taskName || taskId);

    return {
        task: result,
        message: `Deleted task: ${result.name}`
    };
}

// ============================================================================
// Help
// ============================================================================

function getHelp() {
    return {
        version: '3.0.0',
        description: 'OmniFocus CLI tool with JSON I/O',
        usage: 'osascript -l JavaScript scripts/omnifocus.js <action> [json]',
        actions: {
            query: {
                description: 'Query tasks with filters',
                params: {
                    filter: 'today | overdue | flagged | due-soon',
                    days: 'Number of days for due-soon filter (default: 7)'
                },
                example: 'query \'{"filter":"today"}\''
            },
            list: {
                description: 'List tasks with status filter',
                params: {
                    filter: 'active | completed | dropped | all (default: active)'
                },
                example: 'list \'{"filter":"active"}\''
            },
            search: {
                description: 'Search tasks by name/note',
                params: {
                    query: 'Search term (required)'
                },
                example: 'search \'{"query":"meeting"}\''
            },
            create: {
                description: 'Create a new task',
                params: {
                    name: 'Task name (required)',
                    note: 'Task note',
                    project: 'Project name',
                    tags: 'Comma-separated tags',
                    due: 'Due date (ISO 8601)',
                    defer: 'Defer date (ISO 8601)',
                    flagged: 'Boolean',
                    estimate: 'Time estimate (e.g., "1h30m")',
                    createProject: 'Create project if not exists',
                    createTags: 'Create tags if not exist'
                },
                example: 'create \'{"name":"Task","project":"Work","due":"2025-12-31"}\''
            },
            update: {
                description: 'Update an existing task',
                params: {
                    name: 'Task name (or use id)',
                    id: 'Task ID (or use name)',
                    newName: 'New task name',
                    note: 'New note',
                    project: 'New project',
                    tags: 'New tags (comma-separated)',
                    due: 'New due date or "clear"',
                    defer: 'New defer date or "clear"',
                    flagged: 'Boolean'
                },
                example: 'update \'{"name":"Task","due":"2025-12-31"}\''
            },
            complete: {
                description: 'Mark task as complete',
                params: {
                    name: 'Task name (or use id)',
                    id: 'Task ID (or use name)'
                },
                example: 'complete \'{"name":"Task"}\''
            },
            delete: {
                description: 'Delete a task',
                params: {
                    name: 'Task name (or use id)',
                    id: 'Task ID (or use name)'
                },
                example: 'delete \'{"name":"Task"}\''
            },
            help: {
                description: 'Show this help message',
                params: {},
                example: 'help'
            }
        }
    };
}

// ============================================================================
// Output Formatting
// ============================================================================

function formatOutput(success, data, duration, error) {
    const output = {
        success: success,
        metadata: {
            duration: duration,
            version: '3.0.0',
            timestamp: new Date().toISOString()
        }
    };

    if (success) {
        output.data = data;
    } else {
        output.error = {
            message: error.message || String(error),
            stack: error.stack
        };
    }

    return JSON.stringify(output, null, 2);
}

// ============================================================================
// Main Entry Point
// ============================================================================

function run(argv) {
    const startTime = Date.now();

    try {
        // Get OmniFocus application
        const app = Application('OmniFocus');
        const doc = app.defaultDocument;

        // Parse input
        const input = parseInput(argv);

        // Execute action
        const result = executeAction(input, app, doc);

        // Return structured output
        const duration = Date.now() - startTime;
        return formatOutput(true, result, duration);

    } catch (error) {
        const duration = Date.now() - startTime;
        return formatOutput(false, null, duration, error);
    }
}
