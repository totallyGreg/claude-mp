#!/usr/bin/osascript -l JavaScript

/**
 * AI-Powered Task Analysis using Apple Foundation Models
 *
 * Uses Apple Intelligence (on-device AI) to analyze OmniFocus tasks and provide
 * intelligent insights, categorization, prioritization, and recommendations.
 *
 * Requirements:
 *   - OmniFocus 4.8+
 *   - macOS 15.2+ / iOS 18.2+ / iPadOS 18.2+
 *   - Apple Silicon (Mac) or iPhone 15 Pro+ (iOS)
 *
 * Input: JSON via CLI args or stdin
 *   {
 *     "query": {"filter": "today"},
 *     "prompt": "Analyze and prioritize these tasks",
 *     "schema": { JSON schema for structured output }
 *   }
 *
 * Output: Structured JSON
 *   {
 *     "success": true,
 *     "data": {
 *       "tasks": [...],
 *       "analysis": { AI-generated insights },
 *       "recommendations": [...]
 *     }
 *   }
 *
 * Usage:
 *   osascript -l JavaScript scripts/ai-analyze.js '{"query":{"filter":"today"},"prompt":"suggest priorities"}'
 *
 * Version: 3.0.0 (Foundation Models Integration)
 */

// NOTE: This script is designed for future Foundation Models API availability
// Current implementation uses pattern-based analysis as fallback
// When Foundation Models API is available, uncomment AI sections

// ============================================================================
// Library Loading (would be needed for Foundation Models version)
// ============================================================================

// For now, we'll use a simplified approach that demonstrates the architecture
// When Foundation Models are available, this would load the patterns library

function loadPatterns() {
    // Future: Load patterns.js library for queryAndAnalyzeWithAI()
    // const patterns = loadLibrary('patterns.js');
    // return patterns;

    // Current: Return mock pattern functions
    return {
        queryAndAnalyzeWithAI: function(config) {
            // Fallback to rule-based analysis
            return performRuleBasedAnalysis(config);
        }
    };
}

// ============================================================================
// Input Parsing
// ============================================================================

function parseInput(argv) {
    if (argv.length === 0) {
        throw new Error('No input specified. Provide JSON with query and prompt.');
    }

    let params;
    try {
        params = JSON.parse(argv[0]);
    } catch (error) {
        throw new Error(`Invalid JSON input: ${error.message}`);
    }

    // Validate required fields
    if (!params.query) {
        throw new Error('Missing required field: "query"');
    }

    if (!params.prompt) {
        params.prompt = 'Analyze these tasks and provide insights';
    }

    return params;
}

// ============================================================================
// Task Query (simplified - would use taskQuery library in production)
// ============================================================================

function queryTasks(filter, app) {
    const doc = app.defaultDocument;
    const allTasks = doc.flattenedTasks();

    switch (filter) {
        case 'today':
            return getTodayTasks(allTasks);
        case 'overdue':
            return getOverdueTasks(allTasks);
        case 'flagged':
            return getFlaggedTasks(allTasks);
        default:
            return allTasks.filter(t => !t.completed() && !t.dropped());
    }
}

function getTodayTasks(tasks) {
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);

    return tasks.filter(t => {
        if (t.completed() || t.dropped()) return false;

        const due = t.dueDate();
        const defer = t.deferDate();

        return (due && due >= now && due < tomorrow) ||
               (defer && defer >= now && defer < tomorrow);
    });
}

function getOverdueTasks(tasks) {
    const now = new Date();
    return tasks.filter(t => {
        if (t.completed() || t.dropped()) return false;
        const due = t.dueDate();
        return due && due < now;
    });
}

function getFlaggedTasks(tasks) {
    return tasks.filter(t => !t.completed() && !t.dropped() && t.flagged());
}

// ============================================================================
// Rule-Based Analysis (Fallback until Foundation Models available)
// ============================================================================

function performRuleBasedAnalysis(config) {
    const { tasks, prompt } = config;

    // Analyze task patterns
    const analysis = {
        taskCount: tasks.length,
        flaggedCount: tasks.filter(t => t.flagged).length,
        overdueCount: tasks.filter(t => isOverdue(t)).length,
        projectDistribution: analyzeProjects(tasks),
        urgencyLevels: categorizeByUrgency(tasks),
        recommendations: generateRecommendations(tasks)
    };

    return {
        tasks: tasks,
        analysis: analysis,
        recommendations: analysis.recommendations,
        method: 'rule-based' // Would be 'foundation-models' when AI available
    };
}

function isOverdue(task) {
    if (!task.dueDate) return false;
    const due = new Date(task.dueDate);
    return due < new Date();
}

function analyzeProjects(tasks) {
    const projects = {};

    tasks.forEach(task => {
        const project = task.project || 'Inbox';
        if (!projects[project]) {
            projects[project] = 0;
        }
        projects[project]++;
    });

    return projects;
}

function categorizeByUrgency(tasks) {
    const urgent = [];
    const important = [];
    const normal = [];

    tasks.forEach(task => {
        if (task.flagged || isOverdue(task)) {
            urgent.push(task);
        } else if (task.dueDate) {
            important.push(task);
        } else {
            normal.push(task);
        }
    });

    return {
        urgent: urgent.length,
        important: important.length,
        normal: normal.length
    };
}

function generateRecommendations(tasks) {
    const recommendations = [];

    // Check for overdue tasks
    const overdue = tasks.filter(t => isOverdue(t));
    if (overdue.length > 0) {
        recommendations.push({
            type: 'urgent',
            message: `You have ${overdue.length} overdue task(s). Consider rescheduling or completing these first.`,
            tasks: overdue.map(t => t.name)
        });
    }

    // Check for flagged tasks
    const flagged = tasks.filter(t => t.flagged);
    if (flagged.length > 0) {
        recommendations.push({
            type: 'priority',
            message: `You have ${flagged.length} flagged task(s) that need attention.`,
            tasks: flagged.map(t => t.name)
        });
    }

    // Check for tasks without projects
    const inbox = tasks.filter(t => !t.project);
    if (inbox.length > 3) {
        recommendations.push({
            type: 'organization',
            message: `You have ${inbox.length} tasks in your inbox. Consider organizing them into projects.`,
            tasks: inbox.slice(0, 5).map(t => t.name)
        });
    }

    // Workload assessment
    if (tasks.length > 15) {
        recommendations.push({
            type: 'workload',
            message: `You have ${tasks.length} active tasks. Consider focusing on top priorities to avoid overwhelm.`
        });
    }

    return recommendations;
}

// ============================================================================
// Task Formatting
// ============================================================================

function formatTasks(tasks) {
    return tasks.map(task => ({
        id: task.id(),
        name: task.name(),
        project: task.containingProject() ? task.containingProject().name() : null,
        dueDate: task.dueDate() ? task.dueDate().toISOString() : null,
        deferDate: task.deferDate() ? task.deferDate().toISOString() : null,
        flagged: task.flagged(),
        note: task.note()
    }));
}

// ============================================================================
// Future: Foundation Models Integration
// ============================================================================

/*
// This code would be used when Foundation Models API is available

async function performAIAnalysis(config) {
    const { tasks, prompt, schema } = config;

    // Create AI session
    const session = new LanguageModel.Session();

    // Format context for AI
    const context = formatTasksForAI(tasks);

    // Define default schema if not provided
    const analysisSchema = schema || {
        type: "object",
        properties: {
            priorities: {
                type: "array",
                items: {
                    type: "object",
                    properties: {
                        task: { type: "string" },
                        rank: { type: "number" },
                        reason: { type: "string" }
                    }
                }
            },
            workload: { type: "string" },
            suggestions: {
                type: "array",
                items: { type: "string" }
            }
        }
    };

    // Call Foundation Models
    const response = await session.respondWithSchema(
        `${prompt}\n\nTasks:\n${context}`,
        analysisSchema
    );

    return {
        tasks: tasks,
        analysis: response,
        recommendations: response.suggestions || [],
        method: 'foundation-models'
    };
}

function formatTasksForAI(tasks) {
    return tasks.map((task, index) => {
        return `${index + 1}. ${task.name}
   Project: ${task.project || 'Inbox'}
   Due: ${task.dueDate || 'None'}
   Flagged: ${task.flagged ? 'Yes' : 'No'}
   ${task.note ? 'Note: ' + task.note : ''}`;
    }).join('\n\n');
}
*/

// ============================================================================
// Output Formatting
// ============================================================================

function formatOutput(success, data, duration, error) {
    const output = {
        success: success,
        metadata: {
            duration: duration,
            version: '3.0.0',
            timestamp: new Date().toISOString(),
            capability: 'AI Task Analysis (Foundation Models ready)'
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
        // Parse input
        const input = parseInput(argv);

        // Get OmniFocus application
        const app = Application('OmniFocus');

        // Query tasks
        const filter = input.query.filter || 'today';
        const rawTasks = queryTasks(filter, app);
        const tasks = formatTasks(rawTasks);

        // Load patterns (would use actual patterns.js in production)
        const patterns = loadPatterns();

        // Perform analysis
        const result = patterns.queryAndAnalyzeWithAI({
            tasks: tasks,
            prompt: input.prompt,
            schema: input.schema
        });

        // Return structured output
        const duration = Date.now() - startTime;
        return formatOutput(true, result, duration);

    } catch (error) {
        const duration = Date.now() - startTime;
        return formatOutput(false, null, duration, error);
    }
}
