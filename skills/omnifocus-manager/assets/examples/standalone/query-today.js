/**
 * Standalone Example: Query Today's Tasks
 *
 * Demonstrates loading and using the taskQuery library standalone.
 *
 * Usage:
 *   osascript -l JavaScript query-today.js
 */

ObjC.import('Foundation');

// Load taskQuery library
const libraryPath = $.NSString.alloc.initWithUTF8String(
    '/Users/totally/Documents/Projects/claude-mp/skills/omnifocus-manager/libraries/jxa/taskQuery.js'
);

const taskQuery = eval($.NSString.alloc.initWithContentsOfFileEncodingError(
    libraryPath, $.NSUTF8StringEncoding, null
).js);

function run(argv) {
    // Get OmniFocus document
    const app = Application('OmniFocus');
    const doc = app.defaultDocument;

    // Query today's tasks using library
    const tasks = taskQuery.getTodayTasks(doc);

    // Display results
    console.log(`\n=== Today's Tasks (${tasks.length}) ===\n`);

    if (tasks.length === 0) {
        console.log('No tasks due or deferred to today!');
    } else {
        tasks.forEach((task, index) => {
            console.log(`${index + 1}. ${task.name}`);
            console.log(`   Project: ${task.project || 'Inbox'}`);
            console.log(`   Tags: ${task.tags.join(', ') || 'None'}`);
            if (task.flagged) console.log('   🚩 Flagged');
            if (task.dueDate) console.log(`   Due: ${task.dueDate.toLocaleString()}`);
            console.log('');
        });
    }

    return JSON.stringify({
        success: true,
        count: tasks.length,
        tasks: tasks
    }, null, 2);
}
