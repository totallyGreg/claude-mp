#!/usr/bin/osascript -l JavaScript
/**
 * Append a markdown report to the OmniFocus Weekly Review task note.
 *
 * Finds the first active (not completed) task named "Weekly Review" and
 * appends the file contents to its note, separated by a horizontal rule.
 *
 * Usage:
 *   osascript -l JavaScript update-weekly-note.js <markdown-file-path>
 *
 * Returns JSON: { success, taskName, error? }
 */

ObjC.import('stdlib');
ObjC.import('Foundation');

function run(argv) {
    if (!argv || argv.length === 0) {
        return JSON.stringify({
            success: false,
            error: 'Usage: update-weekly-note.js <markdown-file-path>'
        });
    }

    const filePath = argv[0];

    // Read markdown from the temp file written by Claude
    var nsError = $();
    const content = $.NSString.alloc.initWithContentsOfFileEncodingError(
        filePath,
        $.NSUTF8StringEncoding,
        nsError
    );

    if (!content || !content.js) {
        return JSON.stringify({
            success: false,
            error: 'Cannot read file: ' + filePath
        });
    }

    const markdown = content.js;

    // Find the first active Weekly Review task
    const of = Application('OmniFocus');
    const doc = of.defaultDocument;

    const matches = doc.flattenedTasks.whose({
        name: 'Weekly Review',
        completed: false
    })();

    if (matches.length === 0) {
        return JSON.stringify({
            success: false,
            error: 'No active "Weekly Review" task found in OmniFocus'
        });
    }

    const task = matches[0];
    const existing = task.note() || '';
    const separator = existing.length > 0 ? '\n\n---\n\n' : '';

    task.note = existing + separator + markdown;

    return JSON.stringify({
        success: true,
        taskName: task.name()
    });
}
