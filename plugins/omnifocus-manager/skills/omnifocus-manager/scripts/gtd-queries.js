#!/usr/bin/osascript -l JavaScript
/**
 * GTD Diagnostic Queries for OmniFocus
 *
 * Provides data-grounded answers to common GTD coaching questions.
 * Designed for use by gtd-coach skill and omnifocus-agent during guided reviews.
 *
 * Usage:
 *     osascript -l JavaScript scripts/gtd-queries.js --action <action> [options]
 *
 * Actions:
 *     inbox-count              Count of unprocessed inbox items
 *     stalled-projects         Active projects with no available next actions
 *     waiting-for              Tasks tagged 'Waiting' sorted by age
 *     someday-maybe            On-hold projects (Someday/Maybe list)
 *     overdue                  Tasks past their due date with days overdue
 *     recently-completed       Tasks completed in the last N days
 *     neglected-projects       Active projects not modified in N days
 *     folder-structure         Folder/project hierarchy with task counts
 *     perspective-inventory    List custom perspectives with GTD gap analysis
 *     perspective-rules        Show filter rules for a named perspective
 *     system-health            Aggregated GTD system health summary (includes perspective gaps)
 *     repeating-tasks          Active tasks with a repeat rule + completion cadence vs intended interval
 *     analyze-projects         Batch project sweep: stalled, neglected, overdue accumulation, near-duplicates
 *
 * Options:
 *     --days <N>           Days for recently-completed / repeating-tasks lookback (default: 7 / 90)
 *     --threshold <N>      Days without modification for neglected-projects (default: 30)
 *     --tag <pattern>      Tag name pattern for waiting-for (default: 'waiting')
 *     --name <name>        Perspective name for perspective-rules action
 *
 * Examples:
 *     osascript -l JavaScript scripts/gtd-queries.js --action inbox-count
 *     osascript -l JavaScript scripts/gtd-queries.js --action stalled-projects
 *     osascript -l JavaScript scripts/gtd-queries.js --action waiting-for --tag "waiting"
 *     osascript -l JavaScript scripts/gtd-queries.js --action recently-completed --days 14
 *     osascript -l JavaScript scripts/gtd-queries.js --action neglected-projects --threshold 30
 *     osascript -l JavaScript scripts/gtd-queries.js --action perspective-inventory
 *     osascript -l JavaScript scripts/gtd-queries.js --action perspective-rules --name "Next Actions"
 *     osascript -l JavaScript scripts/gtd-queries.js --action system-health
 *     osascript -l JavaScript scripts/gtd-queries.js --action repeating-tasks --days 90
 *     osascript -l JavaScript scripts/gtd-queries.js --action analyze-projects
 *
 * @version 1.0.0
 */

ObjC.import('stdlib');
ObjC.import('Foundation');

// ============================================================================
// Library Loading
// ============================================================================

/**
 * Load a JXA library by path relative to the skill root (current working directory).
 * Run from the skills/omnifocus-manager/ root so paths resolve correctly.
 * Libraries use IIFE pattern and return their namespace object via eval().
 */
function loadLibrary(relativePath) {
    if (relativePath.includes('..') || relativePath.startsWith('/')) {
        throw new Error('Invalid library path: ' + relativePath);
    }
    const cwd = $.NSFileManager.defaultManager.currentDirectoryPath.js;
    const libPath = cwd + '/' + relativePath;
    const content = $.NSString.alloc.initWithContentsOfFileEncodingError(
        libPath,
        $.NSUTF8StringEncoding,
        null
    );
    if (!content) throw new Error('Cannot load library: ' + libPath);
    return eval(content.js);
}

// ============================================================================
// Argument Parsing
// ============================================================================

function parseArgs(argv) {
    const args = { action: 'help' };

    for (let i = 0; i < argv.length; i++) {
        const arg = argv[i];
        if (arg === '--action' && i + 1 < argv.length) {
            args.action = argv[++i];
        } else if (arg === '--days' && i + 1 < argv.length) {
            args.days = parseInt(argv[++i]) || 7;
        } else if (arg === '--threshold' && i + 1 < argv.length) {
            args.threshold = parseInt(argv[++i]) || 30;
        } else if (arg === '--tag' && i + 1 < argv.length) {
            args.tag = argv[++i];
        } else if (arg === '--child-tag' && i + 1 < argv.length) {
            args.childTag = argv[++i];
        } else if (arg === '--name' && i + 1 < argv.length) {
            args.name = argv[++i];
        }
    }

    return args;
}

// ============================================================================
// Main Entry Point
// ============================================================================

function run(argv) {
    try {
        const taskQuery = loadLibrary('scripts/libraries/jxa/taskQuery.js');
        const app = Application('OmniFocus');
        const doc = app.defaultDocument;
        const args = parseArgs(argv);

        let result;
        switch (args.action) {
            case 'inbox-count':
                result = getInboxCount(doc, taskQuery);
                break;
            case 'stalled-projects':
                result = getStalledProjects(doc, taskQuery);
                break;
            case 'waiting-for':
                result = getWaitingFor(doc, taskQuery, args.tag);
                break;
            case 'someday-maybe':
                result = getSomedayMaybe(doc, taskQuery);
                break;
            case 'overdue':
                result = getOverdueTasks(doc, taskQuery);
                break;
            case 'recently-completed':
                result = getRecentlyCompleted(doc, taskQuery, args.days);
                break;
            case 'neglected-projects':
                result = getNeglectedProjects(doc, taskQuery, args.threshold);
                break;
            case 'folder-structure':
                result = getFolderStructure(doc, taskQuery);
                break;
            case 'perspective-inventory':
                result = getPerspectiveInventory(doc, taskQuery);
                break;
            case 'perspective-rules':
                result = getPerspectiveRules(doc, taskQuery, args.name);
                break;
            case 'system-health':
                result = getSystemHealth(doc, taskQuery);
                break;
            case 'ai-agent-tasks':
                result = getAIAgentTasks(doc, taskQuery, args.tag || 'AI Agent', args.childTag);
                break;
            case 'repeating-tasks':
                result = getRepeatingTasksWithCadence(doc, taskQuery, args.days || 90);
                break;
            case 'analyze-projects':
                result = analyzeProjects(doc, taskQuery, args.threshold || 30);
                break;
            case 'help':
                result = getHelp();
                break;
            default:
                result = { success: false, error: 'Unknown action: ' + args.action + '. Use --action help for usage.' };
        }

        return JSON.stringify(result, null, 2);
    } catch (e) {
        return JSON.stringify({ success: false, error: e.toString() });
    }
}

// ============================================================================
// Actions
// ============================================================================

function getInboxCount(doc, taskQuery) {
    const items = taskQuery.getInboxTasks(doc);
    return {
        success: true,
        action: 'inbox-count',
        count: items.length,
        items: items
    };
}

function getStalledProjects(doc, taskQuery) {
    const projects = taskQuery.getStalledProjects(doc);
    return {
        success: true,
        action: 'stalled-projects',
        count: projects.length,
        projects: projects
    };
}

function getWaitingFor(doc, taskQuery, tagPattern) {
    const tasks = taskQuery.getWaitingForTasks(doc, tagPattern);
    const agingCount = tasks.filter(function(t) { return t.ageDays !== null && t.ageDays > 30; }).length;
    return {
        success: true,
        action: 'waiting-for',
        count: tasks.length,
        agingCount: agingCount,
        tasks: tasks
    };
}

function getSomedayMaybe(doc, taskQuery) {
    const projects = taskQuery.getSomedayMaybeProjects(doc);
    return {
        success: true,
        action: 'someday-maybe',
        count: projects.length,
        projects: projects
    };
}

function getOverdueTasks(doc, taskQuery) {
    const tasks = taskQuery.getOverdueTasks(doc);
    const now = new Date();
    const tasksWithAge = tasks.map(function(t) {
        const daysOverdue = t.dueDate
            ? Math.floor((now - new Date(t.dueDate)) / (1000 * 60 * 60 * 24))
            : null;
        return Object.assign({}, t, { daysOverdue: daysOverdue });
    });
    return {
        success: true,
        action: 'overdue',
        count: tasksWithAge.length,
        tasks: tasksWithAge
    };
}

function getRecentlyCompleted(doc, taskQuery, days) {
    const tasks = taskQuery.getRecentlyCompleted(doc, days);
    return {
        success: true,
        action: 'recently-completed',
        days: days || 7,
        count: tasks.length,
        tasks: tasks
    };
}

function getNeglectedProjects(doc, taskQuery, threshold) {
    const projects = taskQuery.getNeglectedProjects(doc, threshold);
    return {
        success: true,
        action: 'neglected-projects',
        thresholdDays: threshold || 30,
        count: projects.length,
        projects: projects
    };
}

function getFolderStructure(doc, taskQuery) {
    const folders = taskQuery.getFolderHierarchy(doc);
    const totalProjects = folders.reduce(function(sum, f) { return sum + f.projectCount; }, 0);
    const activeProjects = folders.reduce(function(sum, f) { return sum + f.activeProjectCount; }, 0);
    return {
        success: true,
        action: 'folder-structure',
        folderCount: folders.length,
        totalProjects: totalProjects,
        activeProjects: activeProjects,
        folders: folders
    };
}

function getSystemHealth(doc, taskQuery) {
    const inbox = taskQuery.getInboxTasks(doc);
    const stalled = taskQuery.getStalledProjects(doc);
    const waiting = taskQuery.getWaitingForTasks(doc);
    const overdue = taskQuery.getOverdueTasks(doc);
    const neglected = taskQuery.getNeglectedProjects(doc);
    const agingWaiting = waiting.filter(function(t) { return t.ageDays !== null && t.ageDays > 30; });

    // Perspective gap analysis
    var perspectiveGaps = { missing: [] };
    try {
        perspectiveGaps = taskQuery.getGTDPerspectiveGaps(doc);
    } catch (e) {
        // Perspective API not available (pre-v4.2)
    }

    // Score: start at 10, deduct for each issue category
    let score = 10;
    if (inbox.length > 20) score -= 2;
    else if (inbox.length > 10) score -= 1;
    if (stalled.length > 5) score -= 2;
    else if (stalled.length > 0) score -= 1;
    if (agingWaiting.length > 0) score -= 1;
    if (overdue.length > 10) score -= 2;
    else if (overdue.length > 0) score -= 1;
    if (neglected.length > 5) score -= 1;
    if (perspectiveGaps.missing.length > 2) score -= 1;
    score = Math.max(0, score);

    return {
        success: true,
        action: 'system-health',
        healthScore: score,
        summary: {
            inboxCount: inbox.length,
            stalledProjects: stalled.length,
            overdueCount: overdue.length,
            agingWaitingCount: agingWaiting.length,
            neglectedProjects: neglected.length,
            missingGTDPerspectives: perspectiveGaps.missing.length
        },
        alerts: buildAlerts(inbox.length, stalled.length, overdue.length, agingWaiting.length, neglected.length, perspectiveGaps.missing.length),
        missingPerspectives: perspectiveGaps.missing
    };
}

function getAIAgentTasks(doc, taskQuery, tagName, childTag) {
    var options = {};
    if (childTag) options.childTag = childTag;

    var grouped = taskQuery.getTasksByTagGrouped(doc, tagName, options);
    var totalTasks = 0;
    var completedTasks = 0;
    for (var i = 0; i < grouped.length; i++) {
        totalTasks += grouped[i].totalCount;
        completedTasks += grouped[i].completedCount;
    }

    return {
        success: true,
        action: 'ai-agent-tasks',
        tag: tagName,
        childTag: childTag || null,
        projectCount: grouped.length,
        totalTasks: totalTasks,
        completedTasks: completedTasks,
        progress: completedTasks + '/' + totalTasks + ' complete',
        projects: grouped
    };
}

function getPerspectiveInventory(doc, taskQuery) {
    var perspectives = taskQuery.getCustomPerspectives(doc);
    var gaps = taskQuery.getGTDPerspectiveGaps(doc);

    return {
        success: true,
        action: 'perspective-inventory',
        customPerspectiveCount: perspectives.length,
        perspectives: perspectives,
        gtdAnalysis: {
            presentCount: gaps.present.length,
            missingCount: gaps.missing.length,
            present: gaps.present,
            missing: gaps.missing
        }
    };
}

function getPerspectiveRules(doc, taskQuery, name) {
    if (!name) {
        return { success: false, error: 'Missing --name parameter. Usage: --action perspective-rules --name "Perspective Name"' };
    }

    var rules = taskQuery.getPerspectiveRules(doc, name);
    if (!rules) {
        return { success: false, error: 'Perspective not found: ' + name };
    }

    return {
        success: true,
        action: 'perspective-rules',
        perspective: rules
    };
}

function buildAlerts(inboxCount, stalledCount, overdueCount, agingWaitingCount, neglectedCount, missingPerspectiveCount) {
    const alerts = [];
    if (inboxCount > 20) alerts.push({ severity: 'HIGH', message: inboxCount + ' items need processing in inbox' });
    else if (inboxCount > 10) alerts.push({ severity: 'MEDIUM', message: inboxCount + ' items in inbox' });
    if (stalledCount > 0) alerts.push({ severity: 'HIGH', message: stalledCount + ' active projects have no next actions' });
    if (overdueCount > 10) alerts.push({ severity: 'HIGH', message: overdueCount + ' tasks are overdue' });
    else if (overdueCount > 0) alerts.push({ severity: 'MEDIUM', message: overdueCount + ' tasks are overdue' });
    if (agingWaitingCount > 0) alerts.push({ severity: 'MEDIUM', message: agingWaitingCount + ' waiting-for items older than 30 days' });
    if (neglectedCount > 0) alerts.push({ severity: 'LOW', message: neglectedCount + ' active projects not touched in 30+ days' });
    if (missingPerspectiveCount > 2) alerts.push({ severity: 'MEDIUM', message: missingPerspectiveCount + ' GTD-essential perspectives missing — run perspective-inventory for details' });
    else if (missingPerspectiveCount > 0) alerts.push({ severity: 'LOW', message: missingPerspectiveCount + ' GTD-essential perspectives missing' });
    return alerts;
}

// ============================================================================
// Repeating Task / Habit Cadence Analysis
// ============================================================================

function getRepeatingTasksWithCadence(doc, taskQuery, days) {
    var repeating = taskQuery.getRepeatingTasks(doc);
    var results = repeating.map(function(task) {
        var history = taskQuery.getCompletionHistory(doc, task.name, days);
        var cadence = taskQuery.computeHabitCadence(history, task.repeatRule, task.hasDueDate);
        return {
            id: task.id,
            name: task.name,
            project: task.project,
            tags: task.tags,
            dueDate: task.dueDate,
            repeatRule: task.repeatRule,
            cadence: cadence
        };
    });

    return {
        success: true,
        action: 'repeating-tasks',
        count: results.length,
        lookbackDays: days,
        tasks: results
    };
}

// ============================================================================
// Batch Project Sweep
// ============================================================================

function analyzeProjects(doc, taskQuery, neglectedThreshold) {
    var stalled = taskQuery.getStalledProjects(doc);
    var neglected = taskQuery.getNeglectedProjects(doc, neglectedThreshold);

    // Overdue accumulation: active projects with 5+ overdue tasks
    var now = new Date();
    var overdueAccumulation = [];
    doc.flattenedProjects().forEach(function(project) {
        var status = project.status() ? project.status().toString() : '';
        if (!status.includes('active')) return;

        var overdueTasks = project.tasks().filter(function(t) {
            if (t.completed()) return false;
            var due = t.dueDate();
            return due && due < now;
        });

        if (overdueTasks.length >= 5) {
            overdueAccumulation.push({
                id: project.id(),
                name: project.name(),
                overdueCount: overdueTasks.length
            });
        }
    });

    // Near-duplicate detection via word-overlap
    var activeProjects = doc.flattenedProjects().filter(function(p) {
        var status = p.status() ? p.status().toString() : '';
        return status.includes('active');
    }).map(function(p) {
        return { id: p.id(), name: p.name() };
    });

    var nearDuplicates = findNearDuplicateProjects(activeProjects);

    return {
        success: true,
        action: 'analyze-projects',
        projectCount: activeProjects.length,
        signals: {
            stalled: stalled,
            neglected: neglected,
            overdueAccumulation: overdueAccumulation,
            nearDuplicates: nearDuplicates
        }
    };
}

/**
 * Word-overlap near-duplicate detection for project names.
 * Flags pairs sharing 2+ significant words (>=4 chars, not stop words).
 * POSSIBLE_DUPLICATE: 2 shared words. LIKELY_DUPLICATE: 3+ shared words.
 */
function findNearDuplicateProjects(projects) {
    var STOP_WORDS = { a:1, the:1, and:1, to:1, 'for':1, of:1, 'in':1, my:1, our:1, 'with':1, on:1, at:1, by:1 };

    function significantWords(name) {
        return name.toLowerCase()
            .replace(/[^a-z0-9 ]/g, ' ')
            .split(/\s+/)
            .filter(function(w) { return w.length >= 4 && !STOP_WORDS[w]; });
    }

    var results = [];

    for (var i = 0; i < projects.length; i++) {
        for (var j = i + 1; j < projects.length; j++) {
            var wordsA = significantWords(projects[i].name);
            var wordsB = significantWords(projects[j].name);
            var setB = {};
            wordsB.forEach(function(w) { setB[w] = true; });
            var shared = wordsA.filter(function(w) { return setB[w]; });

            if (shared.length >= 2) {
                results.push({
                    confidence: shared.length >= 3 ? 'LIKELY_DUPLICATE' : 'POSSIBLE_DUPLICATE',
                    sharedWords: shared,
                    projects: [
                        { id: projects[i].id, name: projects[i].name },
                        { id: projects[j].id, name: projects[j].name }
                    ]
                });
            }
        }
    }

    return results;
}

function getHelp() {
    return {
        success: true,
        usage: 'osascript -l JavaScript scripts/gtd-queries.js --action <action> [options]',
        actions: {
            'inbox-count': 'Count of unprocessed inbox items',
            'stalled-projects': 'Active projects with no available next actions',
            'waiting-for': 'Tasks tagged Waiting sorted by age (--tag <pattern>)',
            'someday-maybe': 'On-hold projects (Someday/Maybe list)',
            'overdue': 'Tasks past their due date with days overdue',
            'recently-completed': 'Tasks completed in last N days (--days <N>, default: 7)',
            'neglected-projects': 'Active projects not modified in N days (--threshold <N>, default: 30)',
            'folder-structure': 'Folder/project hierarchy with task counts',
            'perspective-inventory': 'List custom perspectives with GTD gap analysis',
            'perspective-rules': 'Show filter rules for a named perspective (--name <name>)',
            'system-health': 'Aggregated GTD system health score and alerts (includes perspective gaps)',
            'ai-agent-tasks': 'Tasks tagged AI Agent grouped by project with progress (--tag <name>, --child-tag <name>)',
            'repeating-tasks': 'Active tasks with repeat rule + completion cadence vs intended interval (--days <N>, default 90)',
            'analyze-projects': 'Batch project sweep: stalled, neglected, overdue accumulation, near-duplicates (--threshold <N>, default 30)'
        }
    };
}
