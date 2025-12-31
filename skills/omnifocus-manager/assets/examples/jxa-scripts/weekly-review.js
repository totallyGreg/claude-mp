#!/usr/bin/osascript -l JavaScript

/**
 * Complete JXA Script: Weekly Review
 *
 * Comprehensive GTD weekly review workflow that analyzes projects,
 * detects issues, and generates actionable report.
 *
 * Usage:
 *   ./weekly-review.js [--format json|text]
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
    const format = argv.includes('--format') && argv[argv.indexOf('--format') + 1] === 'json'
        ? 'json'
        : 'text';

    const app = Application('OmniFocus');
    const doc = app.defaultDocument;

    // Collect review data
    const reviewData = {
        timestamp: new Date().toISOString(),
        tasks: {
            overdue: taskQuery.getOverdueTasks(doc),
            today: taskQuery.getTodayTasks(doc),
            dueSoon: taskQuery.getDueSoon(doc, 7),
            flagged: taskQuery.getFlagged(doc)
        },
        projects: analyzeProjects(doc),
        inbox: doc.inboxTasks().filter(t => !t.completed()).length
    };

    // Calculate metrics
    const metrics = {
        totalOverdue: reviewData.tasks.overdue.length,
        totalActive: reviewData.tasks.today.length,
        totalDueSoon: reviewData.tasks.dueSoon.length,
        totalFlagged: reviewData.tasks.flagged.length,
        inboxCount: reviewData.inbox,
        stalledProjects: reviewData.projects.filter(p => p.status === 'stalled').length,
        activeProjects: reviewData.projects.filter(p => p.status === 'active').length
    };

    // Generate recommendations
    const recommendations = generateRecommendations(metrics, reviewData);

    // Output results
    if (format === 'json') {
        return JSON.stringify({
            success: true,
            review: reviewData,
            metrics: metrics,
            recommendations: recommendations
        }, null, 2);
    } else {
        printTextReport(reviewData, metrics, recommendations);
        return '';
    }
}

function analyzeProjects(doc) {
    const projects = doc.flattenedProjects().filter(p =>
        p.status() === Project.Status.Active
    );

    const analyzed = [];

    projects.forEach(project => {
        const tasks = project.tasks();
        const activeTasks = tasks.filter(t => !t.completed() && !t.dropped());
        const availableTasks = activeTasks.filter(t =>
            t.taskStatus() === Task.Status.Available
        );

        let status = 'active';
        if (availableTasks.length === 0 && activeTasks.length > 0) {
            status = 'stalled'; // Has tasks but none available
        } else if (activeTasks.length === 0) {
            status = 'empty'; // No active tasks
        }

        analyzed.push({
            name: project.name(),
            status: status,
            totalTasks: tasks.length,
            activeTasks: activeTasks.length,
            availableTasks: availableTasks.length
        });
    });

    return analyzed;
}

function generateRecommendations(metrics, reviewData) {
    const recs = [];

    // Overdue tasks
    if (metrics.totalOverdue > 0) {
        recs.push({
            priority: 'HIGH',
            category: 'Overdue',
            action: `Reschedule or complete ${metrics.totalOverdue} overdue tasks`,
            reason: 'Overdue tasks indicate planning issues or blocked work'
        });
    }

    // Inbox overflow
    if (metrics.inboxCount > 20) {
        recs.push({
            priority: 'HIGH',
            category: 'Inbox',
            action: `Process ${metrics.inboxCount} inbox items to zero`,
            reason: 'Large inbox prevents proper task organization'
        });
    }

    // Stalled projects
    if (metrics.stalledProjects > 0) {
        recs.push({
            priority: 'MEDIUM',
            category: 'Projects',
            action: `Add next actions to ${metrics.stalledProjects} stalled projects`,
            reason: 'Projects without available actions can\'t make progress'
        });
    }

    // Flag overuse
    const flagPercentage = (metrics.totalFlagged / (metrics.totalActive || 1)) * 100;
    if (flagPercentage > 30) {
        recs.push({
            priority: 'LOW',
            category: 'Flags',
            action: 'Review flagged items - unflag non-priorities',
            reason: `${Math.round(flagPercentage)}% of tasks are flagged (should be <10%)`
        });
    }

    // Upcoming workload
    if (metrics.totalDueSoon > 50) {
        recs.push({
            priority: 'MEDIUM',
            category: 'Workload',
            action: 'Review upcoming week - consider deferring non-critical tasks',
            reason: `${metrics.totalDueSoon} tasks due in next 7 days may be overcommitted`
        });
    }

    return recs;
}

function printTextReport(reviewData, metrics, recommendations) {
    console.log('\n========================================');
    console.log('  WEEKLY REVIEW REPORT');
    console.log(`  ${new Date().toLocaleDateString()}`);
    console.log('========================================\n');

    // Metrics
    console.log('METRICS:');
    console.log('─────────────────────────');
    console.log(`  Projects: ${metrics.activeProjects} active, ${metrics.stalledProjects} stalled`);
    console.log(`  Inbox: ${metrics.inboxCount} items`);
    console.log(`  Overdue: ${metrics.totalOverdue} tasks`);
    console.log(`  Today: ${metrics.totalActive} tasks`);
    console.log(`  This week: ${metrics.totalDueSoon} tasks`);
    console.log(`  Flagged: ${metrics.totalFlagged} tasks\n`);

    // Stalled projects
    if (metrics.stalledProjects > 0) {
        console.log('STALLED PROJECTS:');
        console.log('─────────────────────────');
        reviewData.projects
            .filter(p => p.status === 'stalled')
            .forEach(p => {
                console.log(`  ⚠️  ${p.name}`);
                console.log(`      ${p.activeTasks} tasks but none available`);
            });
        console.log('');
    }

    // Recommendations
    if (recommendations.length > 0) {
        console.log('RECOMMENDATIONS:');
        console.log('─────────────────────────');
        recommendations.forEach((rec, index) => {
            const icon = rec.priority === 'HIGH' ? '🔴' :
                        rec.priority === 'MEDIUM' ? '🟡' : '🔵';
            console.log(`${index + 1}. ${icon} [${rec.priority}] ${rec.action}`);
            console.log(`   Reason: ${rec.reason}\n`);
        });
    } else {
        console.log('✅ No issues detected! System looks healthy.\n');
    }

    // Next steps
    console.log('WEEKLY REVIEW CHECKLIST:');
    console.log('─────────────────────────');
    console.log('  ☐ Process inbox to zero');
    console.log('  ☐ Review all projects for next actions');
    console.log('  ☐ Review waiting-for items');
    console.log('  ☐ Review someday/maybe list');
    console.log('  ☐ Plan top 3 priorities for week');
    console.log('  ☐ Clear completed tasks\n');

    console.log('========================================\n');
}
