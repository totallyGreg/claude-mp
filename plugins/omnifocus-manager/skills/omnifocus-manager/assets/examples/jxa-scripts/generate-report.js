#!/usr/bin/osascript -l JavaScript

/**
 * Complete JXA Script: Generate Report
 *
 * Query tasks and export to various formats (JSON, CSV, Markdown).
 * Demonstrates integration of taskQuery with export functionality.
 *
 * Usage:
 *   ./generate-report.js --filter today --format markdown
 *   ./generate-report.js --filter overdue --format csv --output report.csv
 *   ./generate-report.js --filter flagged --format json
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

const taskQuery = loadLibrary('taskQuery.js');

function run(argv) {
    // Parse arguments
    let filter = 'today';
    let format = 'markdown';
    let outputFile = null;

    for (let i = 0; i < argv.length; i++) {
        if (argv[i] === '--filter' && argv[i + 1]) {
            filter = argv[i + 1];
            i++;
        } else if (argv[i] === '--format' && argv[i + 1]) {
            format = argv[i + 1];
            i++;
        } else if (argv[i] === '--output' && argv[i + 1]) {
            outputFile = argv[i + 1];
            i++;
        }
    }

    // Get OmniFocus document
    const app = Application('OmniFocus');
    const doc = app.defaultDocument;

    // Query tasks based on filter
    let tasks = [];
    let reportTitle = '';

    switch (filter) {
        case 'today':
            tasks = taskQuery.getTodayTasks(doc);
            reportTitle = 'Today\'s Tasks';
            break;
        case 'overdue':
            tasks = taskQuery.getOverdueTasks(doc);
            reportTitle = 'Overdue Tasks';
            break;
        case 'flagged':
            tasks = taskQuery.getFlagged(doc);
            reportTitle = 'Flagged Tasks';
            break;
        case 'week':
            tasks = taskQuery.getDueSoon(doc, 7);
            reportTitle = 'Tasks Due This Week';
            break;
        default:
            console.log(`Unknown filter: ${filter}`);
            console.log('Available filters: today, overdue, flagged, week');
            return JSON.stringify({ success: false, error: 'Invalid filter' });
    }

    // Generate report based on format
    let output = '';

    switch (format) {
        case 'json':
            output = formatJSON(tasks, reportTitle);
            break;
        case 'csv':
            output = formatCSV(tasks);
            break;
        case 'markdown':
            output = formatMarkdown(tasks, reportTitle);
            break;
        default:
            console.log(`Unknown format: ${format}`);
            console.log('Available formats: json, csv, markdown');
            return JSON.stringify({ success: false, error: 'Invalid format' });
    }

    // Output to file or console
    if (outputFile) {
        const path = $.NSString.alloc.initWithUTF8String(outputFile);
        const data = $.NSString.alloc.initWithUTF8String(output);
        data.writeToFileAtomicallyEncodingError(path, true, $.NSUTF8StringEncoding, null);
        console.log(`\n✅ Report saved to: ${outputFile}\n`);
    } else {
        console.log(output);
    }

    return JSON.stringify({
        success: true,
        filter: filter,
        format: format,
        count: tasks.length,
        output: outputFile || 'console'
    }, null, 2);
}

function formatJSON(tasks, title) {
    return JSON.stringify({
        title: title,
        generated: new Date().toISOString(),
        count: tasks.length,
        tasks: tasks
    }, null, 2);
}

function formatCSV(tasks) {
    if (tasks.length === 0) return 'No tasks found';

    const headers = ['Name', 'Project', 'Tags', 'Due Date', 'Defer Date', 'Flagged', 'Estimated Minutes'];
    const rows = [headers.join(',')];

    tasks.forEach(task => {
        const row = [
            escapeCSV(task.name),
            escapeCSV(task.project || ''),
            escapeCSV(task.tags.join('; ')),
            task.dueDate ? task.dueDate.toISOString() : '',
            task.deferDate ? task.deferDate.toISOString() : '',
            task.flagged ? 'Yes' : 'No',
            task.estimatedMinutes || ''
        ];
        rows.push(row.join(','));
    });

    return rows.join('\n');
}

function formatMarkdown(tasks, title) {
    let md = `# ${title}\n\n`;
    md += `**Generated:** ${new Date().toLocaleString()}\n`;
    md += `**Task Count:** ${tasks.length}\n\n`;

    if (tasks.length === 0) {
        md += 'No tasks found.\n';
        return md;
    }

    // Group by project
    const byProject = {};
    tasks.forEach(task => {
        const project = task.project || 'Inbox';
        if (!byProject[project]) byProject[project] = [];
        byProject[project].push(task);
    });

    // Output each project
    Object.keys(byProject).sort().forEach(project => {
        md += `## ${project}\n\n`;

        byProject[project].forEach(task => {
            md += `- **${task.name}**`;
            if (task.flagged) md += ' 🚩';
            md += '\n';

            if (task.tags.length > 0) {
                md += `  - Tags: ${task.tags.join(', ')}\n`;
            }
            if (task.dueDate) {
                md += `  - Due: ${task.dueDate.toLocaleDateString()}\n`;
            }
            if (task.estimatedMinutes) {
                const hours = Math.floor(task.estimatedMinutes / 60);
                const minutes = task.estimatedMinutes % 60;
                const estimate = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
                md += `  - Estimate: ${estimate}\n`;
            }
            if (task.note) {
                md += `  - Note: ${task.note.substring(0, 100)}${task.note.length > 100 ? '...' : ''}\n`;
            }
            md += '\n';
        });
    });

    return md;
}

function escapeCSV(str) {
    if (!str) return '';
    str = String(str);
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
        return '"' + str.replace(/"/g, '""') + '"';
    }
    return str;
}

// Show help if no arguments
if ($.NSProcessInfo.processInfo.arguments.js.length === 4) {
    console.log('\nUsage:');
    console.log('  ./generate-report.js --filter <filter> --format <format> [--output <file>]');
    console.log('\nFilters:');
    console.log('  today    - Tasks due or deferred to today');
    console.log('  overdue  - Past due tasks');
    console.log('  flagged  - Flagged tasks');
    console.log('  week     - Tasks due within 7 days');
    console.log('\nFormats:');
    console.log('  json     - JSON format');
    console.log('  csv      - CSV format');
    console.log('  markdown - Markdown format');
    console.log('\nExamples:');
    console.log('  ./generate-report.js --filter today --format markdown');
    console.log('  ./generate-report.js --filter overdue --format csv --output overdue.csv\n');
    $.exit(0);
}
