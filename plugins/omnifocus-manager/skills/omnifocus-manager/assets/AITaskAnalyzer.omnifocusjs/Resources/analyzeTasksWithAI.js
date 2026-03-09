/**
 * AI Task Analyzer - Omni Automation Plug-In
 *
 * Reads today's and overdue tasks, then analyzes them using Apple Foundation Models
 * to provide intelligent insights about your workload, priorities, and recommendations.
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - macOS 26+
 * - Apple Silicon (M1 or later)
 */

(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        // Load libraries first
        const fmUtils = this.plugIn.library("foundationModelsUtils");

        // Check availability IMMEDIATELY before doing anything else
        if (!fmUtils.isAvailable()) {
            fmUtils.showUnavailableAlert();
            return;
        }

        try {
            if (!this.plugIn.library("preferencesManager").hasPreferences()) {
                console.log("No cached preferences. Run System Setup to enable.");
            }
            const metrics = this.plugIn.library("taskMetrics");

            // Get today's and overdue tasks using library
            const todayTasks = metrics.getTodayTasks();
            const overdueTasks = metrics.getOverdueTasks();

            // Calculate today for days overdue
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            // Limit tasks to avoid context window issues (max 10 each)
            const maxTasks = 10;
            const limitedTodayTasks = todayTasks.slice(0, maxTasks);
            const limitedOverdueTasks = overdueTasks.slice(0, maxTasks);

            // Build concise task summary for AI analysis
            const taskSummary = {
                todayCount: todayTasks.length,
                overdueCount: overdueTasks.length,
                todayTasks: limitedTodayTasks.map(t => ({
                    name: t.name,
                    project: t.project || "Inbox",
                    flagged: t.flagged ? "🚩" : ""
                })),
                overdueTasks: limitedOverdueTasks.map(t => ({
                    name: t.name,
                    project: t.project || "Inbox",
                    daysOverdue: Math.floor((today - new Date(t.dueDate)) / (1000 * 60 * 60 * 24))
                }))
            };

            // Check if we have any tasks to analyze
            if (taskSummary.todayCount === 0 && taskSummary.overdueCount === 0) {
                const alert = new Alert(
                    "AI Task Analyzer",
                    "No tasks found for today or overdue. Great job staying on top of things! 🎉"
                );
                alert.show();
                return;
            }

            // Create AI session - may succeed but be invalid
            const session = fmUtils.createSession();

            // Prepare concise prompt for AI analysis
            const prompt = `Analyze OmniFocus tasks (GTD methodology):

TODAY (${taskSummary.todayCount} total, showing ${limitedTodayTasks.length}):
${limitedTodayTasks.map(t => `- ${t.flagged}${t.name} [${t.project}]`).join('\n')}

OVERDUE (${taskSummary.overdueCount} total, showing ${limitedOverdueTasks.length}):
${limitedOverdueTasks.map(t => `- ${t.name} [${t.project}] (${t.daysOverdue}d overdue)`).join('\n')}

Provide concise insights on:
1. Top 3 priorities today
2. Workload assessment
3. Overdue patterns
4. Key actions`;

            // Request structured analysis using OmniFocus schema format
            const schema = LanguageModel.Schema.fromJSON({
                name: "analysis-schema",
                properties: [
                    {
                        name: "priorityRecommendations",
                        description: "Top 3 tasks to tackle first",
                        schema: {
                            arrayOf: {
                                name: "priority-item",
                                properties: [
                                    {name: "taskName"},
                                    {name: "reason"}
                                ]
                            }
                        }
                    },
                    {
                        name: "workloadAnalysis",
                        schema: {
                            name: "workload-schema",
                            properties: [
                                {name: "isManageable"},
                                {name: "summary"},
                                {
                                    name: "concerns",
                                    schema: {arrayOf: {constant: "concern"}}
                                }
                            ]
                        }
                    },
                    {
                        name: "overdueInsights",
                        schema: {
                            name: "overdue-schema",
                            properties: [
                                {
                                    name: "patterns",
                                    schema: {arrayOf: {constant: "pattern"}}
                                },
                                {
                                    name: "recommendations",
                                    schema: {arrayOf: {constant: "recommendation"}}
                                }
                            ]
                        }
                    },
                    {
                        name: "timeManagement",
                        schema: {
                            name: "time-schema",
                            properties: [
                                {name: "totalEstimatedMinutes"},
                                {
                                    name: "suggestedSchedule",
                                    schema: {arrayOf: {constant: "schedule-item"}}
                                }
                            ]
                        }
                    },
                    {
                        name: "actionItems",
                        description: "Immediate actions to take",
                        schema: {arrayOf: {constant: "action"}}
                    }
                ]
            });

            // Get AI response
            const response = await session.respondWithSchema(prompt, schema);

            // Parse the JSON response
            const analysis = JSON.parse(response);

            // Format results for display
            let message = `📊 AI Analysis of Your Tasks\n\n`;

            // Priority Recommendations
            message += `🎯 TOP PRIORITIES:\n`;
            analysis.priorityRecommendations.forEach((item, i) => {
                message += `${i + 1}. ${item.taskName}\n   → ${item.reason}\n`;
            });
            message += `\n`;

            // Workload Analysis
            if (analysis.workloadAnalysis) {
                message += `📋 WORKLOAD: ${analysis.workloadAnalysis.isManageable ? "✅ Manageable" : "⚠️ Heavy"}\n`;
                if (analysis.workloadAnalysis.summary) {
                    message += `${analysis.workloadAnalysis.summary}\n`;
                }
                if (analysis.workloadAnalysis.concerns && analysis.workloadAnalysis.concerns.length > 0) {
                    message += `Concerns:\n`;
                    analysis.workloadAnalysis.concerns.forEach(c => message += `• ${c}\n`);
                }
                message += `\n`;
            }

            // Overdue Insights
            if (taskSummary.overdueCount > 0 && analysis.overdueInsights) {
                message += `⏰ OVERDUE INSIGHTS:\n`;
                if (analysis.overdueInsights.patterns && analysis.overdueInsights.patterns.length > 0) {
                    message += `Patterns:\n`;
                    analysis.overdueInsights.patterns.forEach(p => message += `• ${p}\n`);
                }
                if (analysis.overdueInsights.recommendations && analysis.overdueInsights.recommendations.length > 0) {
                    message += `Recommendations:\n`;
                    analysis.overdueInsights.recommendations.forEach(r => message += `• ${r}\n`);
                }
                message += `\n`;
            }

            // Time Management
            if (analysis.timeManagement && analysis.timeManagement.suggestedSchedule && analysis.timeManagement.suggestedSchedule.length > 0) {
                message += `⏱️ SUGGESTED SCHEDULE:\n`;
                analysis.timeManagement.suggestedSchedule.forEach(s => message += `• ${s}\n`);
                message += `\n`;
            }

            // Action Items
            if (analysis.actionItems && analysis.actionItems.length > 0) {
                message += `✅ ACTION ITEMS:\n`;
                analysis.actionItems.forEach(a => message += `• ${a}\n`);
            }

            // Show results
            const resultAlert = new Alert("AI Task Analysis", message);
            resultAlert.addOption("Copy to Clipboard");
            resultAlert.addOption("Done");
            const buttonIndex = await resultAlert.show();

            if (buttonIndex === 0) {
                // Copy to clipboard
                Pasteboard.general.string = message;
            }

        } catch (error) {
            console.error("Error:", error);
            const errorAlert = new Alert("Error",
                `Failed to analyze tasks: ${error.message}`
            );
            errorAlert.show();
        }
    });

    // Require macOS 26+ for Apple Foundation Models
    action.validate = function(selection, sender) {
        return (Device.current.operatingSystemVersion.atLeast(new Version("26")));
    };

    return action;
})();
