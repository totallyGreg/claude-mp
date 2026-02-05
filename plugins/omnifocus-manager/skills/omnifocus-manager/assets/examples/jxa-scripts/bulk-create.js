#!/usr/bin/osascript -l JavaScript

/**
 * Complete JXA Script: Bulk Create Tasks
 *
 * Create multiple tasks from a template or list.
 * Demonstrates batch operations using taskMutation library.
 *
 * Usage:
 *   ./bulk-create.js --template "weekly-review"
 *   ./bulk-create.js --list "tasks.txt" --project "Work"
 *   ./bulk-create.js --interactive
 */

ObjC.import('Foundation');
ObjC.import('stdlib');

// Load libraries
const LIBRARIES_PATH = '../../libraries/jxa/';

function loadLibrary(filename) {
    const scriptDir = $.NSString.alloc.initWithUTF8String($.getenv('_')).stringByDeletingLastPathComponent;
    const libPath = scriptDir.stringByAppendingPathComponent(LIBRARIES_PATH + filename);

    return eval($.NSString.alloc.initWithContentsOfFileEncodingError(
        libPath, $.NSUTF8StringEncoding, null
    ).js);
}

const taskMutation = loadLibrary('taskMutation.js');
const argParser = loadLibrary('argParser.js');

// Template definitions
const TEMPLATES = {
    'weekly-review': [
        { name: 'Process inbox to zero', tags: 'review', estimate: '15m' },
        { name: 'Review projects for stalled items', tags: 'review', estimate: '20m' },
        { name: 'Review waiting-for items', tags: 'review,waiting', estimate: '10m' },
        { name: 'Review upcoming week', tags: 'review', estimate: '15m' },
        { name: 'Clear completed tasks', tags: 'review', estimate: '5m' }
    ],
    'meeting-prep': [
        { name: 'Review meeting agenda', tags: 'meeting', flagged: true },
        { name: 'Prepare talking points', tags: 'meeting', estimate: '30m' },
        { name: 'Send reminder to attendees', tags: 'email,meeting' }
    ],
    'project-kickoff': [
        { name: 'Define project objectives', tags: 'planning', flagged: true },
        { name: 'Identify stakeholders', tags: 'planning' },
        { name: 'Create project plan', tags: 'planning', estimate: '1h' },
        { name: 'Schedule kickoff meeting', tags: 'meeting' }
    ]
};

function run(argv) {
    const app = Application('OmniFocus');
    const doc = app.defaultDocument;

    console.log('\n========================================');
    console.log('  BULK TASK CREATOR');
    console.log('========================================\n');

    // Parse arguments
    let mode = 'interactive';
    let template = null;
    let project = null;
    let tasksToCreate = [];

    for (let i = 0; i < argv.length; i++) {
        if (argv[i] === '--template' && argv[i + 1]) {
            mode = 'template';
            template = argv[i + 1];
            i++;
        } else if (argv[i] === '--list' && argv[i + 1]) {
            mode = 'list';
            // Load tasks from file (simplified for example)
            i++;
        } else if (argv[i] === '--project' && argv[i + 1]) {
            project = argv[i + 1];
            i++;
        } else if (argv[i] === '--interactive') {
            mode = 'interactive';
        }
    }

    // Get tasks based on mode
    if (mode === 'template') {
        if (!TEMPLATES[template]) {
            console.log(`❌ Template '${template}' not found.`);
            console.log(`\nAvailable templates: ${Object.keys(TEMPLATES).join(', ')}\n`);
            return JSON.stringify({ success: false, error: 'Template not found' });
        }

        tasksToCreate = TEMPLATES[template];
        console.log(`Creating tasks from template: ${template}\n`);
    } else if (mode === 'interactive') {
        // Interactive mode: create sample tasks
        console.log('Interactive mode: Creating sample tasks\n');
        tasksToCreate = [
            { name: 'Example task 1', tags: 'demo' },
            { name: 'Example task 2', tags: 'demo', flagged: true },
            { name: 'Example task 3', tags: 'demo', project: 'Examples' }
        ];
    }

    // Create tasks
    const created = [];
    const errors = [];

    console.log(`Creating ${tasksToCreate.length} tasks...\n`);

    tasksToCreate.forEach((taskData, index) => {
        try {
            // Add project if specified via command line
            if (project) {
                taskData.project = project;
                taskData.createProject = true;
            }

            // Add createTags flag
            taskData.createTags = true;

            // Create task
            const result = taskMutation.createTask(app, doc, taskData);

            created.push(result);
            console.log(`✅ Created: ${result.name}`);
            if (result.project !== 'Inbox') {
                console.log(`   Project: ${result.project}`);
            }
        } catch (error) {
            errors.push({ task: taskData.name, error: error.message });
            console.log(`❌ Failed: ${taskData.name} - ${error.message}`);
        }
    });

    // Summary
    console.log('\n========================================');
    console.log('SUMMARY:');
    console.log(`  Created: ${created.length}`);
    console.log(`  Failed: ${errors.length}`);
    console.log('========================================\n');

    if (created.length > 0) {
        console.log('Tasks created successfully!');
        console.log('Open OmniFocus to review.\n');
    }

    return JSON.stringify({
        success: errors.length === 0,
        created: created.length,
        failed: errors.length,
        tasks: created,
        errors: errors
    }, null, 2);
}

// Show help if no arguments
if ($.NSProcessInfo.processInfo.arguments.js.length === 4) {
    console.log('\nUsage:');
    console.log('  ./bulk-create.js --template <name> [--project <project>]');
    console.log('  ./bulk-create.js --interactive');
    console.log('\nAvailable templates:');
    Object.keys(TEMPLATES).forEach(name => {
        console.log(`  - ${name}`);
    });
    console.log('');
    $.exit(0);
}
