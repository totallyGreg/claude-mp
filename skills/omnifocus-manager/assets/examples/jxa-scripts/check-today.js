#!/usr/bin/osascript -l JavaScript

/**
 * Complete JXA Script: Check Today's Tasks
 *
 * Full-featured script that queries and displays today's tasks with
 * priority ranking and actionable summary.
 *
 * Usage:
 *   chmod +x check-today.js
 *   ./check-today.js
 *
 * Or:
 *   osascript -l JavaScript check-today.js
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
const dateUtils = loadLibrary('dateUtils.js');

function run(argv) {
    console.log('\n========================================');
    console.log('  TODAY\'S TASKS REPORT');
    console.log('========================================\n');

    // Get OmniFocus document
    const app = Application('OmniFocus');
    const doc = app.defaultDocument;

    // Query different task categories
    const today = taskQuery.getTodayTasks(doc);
    const overdue = taskQuery.getOverdueTasks(doc);
    const flagged = taskQuery.getFlagged(doc);

    // Calculate summary
    const totalTasks = today.length;
    const overdueCount = overdue.length;
    const flaggedCount = flagged.length;

    // Display summary
    console.log('SUMMARY:');
    console.log(`  Total tasks today: ${totalTasks}`);
    if (overdueCount > 0) {
        console.log(`  ⚠️  Overdue tasks: ${overdueCount}`);
    }
    if (flaggedCount > 0) {
        console.log(`  🚩 Flagged tasks: ${flaggedCount}`);
    }
    console.log('');

    // Display overdue tasks first (highest priority)
    if (overdue.length > 0) {
        console.log('⚠️  OVERDUE TASKS:');
        console.log('─────────────────────────\n');

        overdue.forEach((task, index) => {
            const daysOverdue = Math.floor((new Date() - task.dueDate) / (1000 * 60 * 60 * 24));
            console.log(`${index + 1}. ${task.name}`);
            console.log(`   Project: ${task.project || 'Inbox'}`);
            console.log(`   Due: ${task.dueDate.toLocaleDateString()} (${daysOverdue} days ago)`);
            if (task.flagged) console.log('   🚩 Flagged');
            console.log('');
        });
    }

    // Display today's tasks
    if (today.length > 0) {
        console.log('TODAY\'S TASKS:');
        console.log('─────────────────────────\n');

        // Group by project
        const byProject = {};
        today.forEach(task => {
            const project = task.project || 'Inbox';
            if (!byProject[project]) byProject[project] = [];
            byProject[project].push(task);
        });

        Object.keys(byProject).sort().forEach(project => {
            console.log(`📁 ${project}:`);
            byProject[project].forEach(task => {
                let line = `   • ${task.name}`;
                if (task.flagged) line += ' 🚩';
                if (task.dueDate) {
                    const time = task.dueDate.toLocaleTimeString('en-US', {
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                    line += ` (${time})`;
                }
                console.log(line);
            });
            console.log('');
        });
    } else {
        console.log('✅ No tasks scheduled for today!\n');
    }

    // Provide actionable recommendations
    console.log('NEXT STEPS:');
    console.log('─────────────────────────');

    if (overdueCount > 0) {
        console.log('1. Address overdue tasks first');
    } else if (flaggedCount > 0) {
        console.log('1. Focus on flagged items');
    } else if (totalTasks > 0) {
        console.log('1. Work through today\'s tasks in order');
    } else {
        console.log('1. Review upcoming tasks or process inbox');
    }

    console.log('2. Process inbox to zero');
    console.log('3. Review projects for next actions\n');

    console.log('========================================\n');

    // Return structured data for potential automation
    return JSON.stringify({
        success: true,
        summary: {
            today: totalTasks,
            overdue: overdueCount,
            flagged: flaggedCount
        },
        tasks: {
            today: today,
            overdue: overdue,
            flagged: flagged
        }
    }, null, 2);
}
