/**
 * Standalone Example: Build OmniFocus URL
 *
 * Demonstrates loading and using the urlBuilder library.
 *
 * Usage:
 *   osascript -l JavaScript build-url.js "Task name" [--project "Project"] [--tags "tag1,tag2"]
 */

ObjC.import('Foundation');

// Load urlBuilder library
const libraryPath = $.NSString.alloc.initWithUTF8String(
    '${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/libraries/shared/urlBuilder.js'
);

const urlBuilder = eval($.NSString.alloc.initWithContentsOfFileEncodingError(
    libraryPath, $.NSUTF8StringEncoding, null
).js);

function run(argv) {
    if (argv.length === 0) {
        console.log('Usage: osascript build-url.js "Task name" [--project "Project"] [--tags "tag1,tag2"] [--due "2025-12-30"]');

        // Show examples
        console.log('\nExamples:\n');

        // Simple task
        const url1 = urlBuilder.buildTaskURL({ name: 'Buy groceries' });
        console.log('Simple task:');
        console.log(url1 + '\n');

        // Task with project and tags
        const url2 = urlBuilder.buildTaskURL({
            name: 'Call dentist',
            project: 'Health',
            tags: ['phone', 'urgent'],
            flagged: true
        });
        console.log('Task with project and tags:');
        console.log(url2 + '\n');

        // Task with due date
        const url3 = urlBuilder.buildTaskURL({
            name: 'Submit report',
            project: 'Work',
            due: '2025-12-30T14:00:00',
            estimate: '2h'
        });
        console.log('Task with due date and estimate:');
        console.log(url3 + '\n');

        // Markdown link
        const md = urlBuilder.buildMarkdownLink('Review document', {
            name: 'Review document',
            project: 'Work',
            tags: 'review'
        });
        console.log('Markdown link:');
        console.log(md);

        return;
    }

    // Parse arguments
    const taskName = argv[0];
    const params = { name: taskName };

    for (let i = 1; i < argv.length; i += 2) {
        const flag = argv[i];
        const value = argv[i + 1] || '';

        if (flag === '--project') {
            params.project = value;
        } else if (flag === '--tags') {
            params.tags = value.split(',');
        } else if (flag === '--due') {
            params.due = value;
        } else if (flag === '--flagged') {
            params.flagged = true;
        } else if (flag === '--note') {
            params.note = value;
        } else if (flag === '--estimate') {
            params.estimate = value;
        }
    }

    // Build URL
    const url = urlBuilder.buildTaskURL(params);

    console.log('\n=== Generated OmniFocus URL ===\n');
    console.log(url);
    console.log('\n=== Markdown Link ===\n');
    console.log(urlBuilder.buildMarkdownLink(taskName, params));

    // Validate parameters
    const validation = urlBuilder.validateParams(params);
    if (validation.errors.length > 0) {
        console.log('\n⚠️  Validation Errors:');
        validation.errors.forEach(err => console.log(`  - ${err}`));
    }
    if (validation.warnings.length > 0) {
        console.log('\n⚠️  Warnings:');
        validation.warnings.forEach(warn => console.log(`  - ${warn}`));
    }

    return JSON.stringify({ success: true, url: url, validation: validation }, null, 2);
}
