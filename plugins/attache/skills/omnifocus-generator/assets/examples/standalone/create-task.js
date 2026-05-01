/**
 * Standalone Example: Create Task
 *
 * Demonstrates loading and using the taskMutation library to create a task.
 *
 * Usage:
 *   osascript -l JavaScript create-task.js "Task name" [--project "Project"] [--tags "tag1,tag2"]
 */

ObjC.import('Foundation');

// Load libraries
const librariesPath = '${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/libraries/jxa/';

function loadLibrary(filename) {
    const path = librariesPath + filename;
    return eval($.NSString.alloc.initWithContentsOfFileEncodingError(
        path, $.NSUTF8StringEncoding, null
    ).js);
}

const taskMutation = loadLibrary('taskMutation.js');
const dateUtils = loadLibrary('dateUtils.js');

function run(argv) {
    if (argv.length === 0) {
        console.log('Usage: osascript create-task.js "Task name" [--project "Project"] [--tags "tag1,tag2"] [--due "2025-12-30"]');
        return JSON.stringify({ success: false, error: 'No task name provided' });
    }

    // Get OmniFocus application
    const app = Application('OmniFocus');
    const doc = app.defaultDocument;

    // Parse arguments
    const taskName = argv[0];
    const options = { name: taskName };

    for (let i = 1; i < argv.length; i += 2) {
        const flag = argv[i];
        const value = argv[i + 1] || '';

        if (flag === '--project') {
            options.project = value;
            options.createProject = true;
        } else if (flag === '--tags') {
            options.tags = value;
            options.createTags = true;
        } else if (flag === '--due') {
            options.due = dateUtils.parseDate(value);
        } else if (flag === '--flagged') {
            options.flagged = true;
        } else if (flag === '--note') {
            options.note = value;
        }
    }

    // Create task using library
    try {
        const result = taskMutation.createTask(app, doc, options);

        console.log('\n✅ Task created successfully!\n');
        console.log(`Name: ${result.name}`);
        console.log(`Project: ${result.project}`);
        if (result.dueDate) console.log(`Due: ${result.dueDate}`);
        if (result.flagged) console.log('🚩 Flagged');
        console.log(`\nTask ID: ${result.id}`);

        return JSON.stringify({ success: true, task: result }, null, 2);
    } catch (error) {
        console.error(`\n❌ Error: ${error.message}`);
        return JSON.stringify({ success: false, error: error.message });
    }
}
