/**
 * AI Task Analyzer - Omni Automation Plug-In
 *
 * Reads today's and overdue tasks, then analyzes them using Apple Foundation Models
 * to provide intelligent insights about your workload, priorities, and recommendations.
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - macOS 15.2+, iOS 18.2+, or later
 * - Apple Silicon or iPhone 15 Pro+ for on-device AI
 */

(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        try {
            // Get all tasks
            const doc = Document.defaultDocument;
            const tasks = doc.flattenedTasks();

            // Calculate date ranges
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);

            // Filter for today's tasks
            const todayTasks = tasks.filter(task => {
                if (task.completed || task.dropped) return false;

                const due = task.dueDate;
                const defer = task.deferDate;

                const isDueToday = due && due >= today && due < tomorrow;
                const isDeferredToday = defer && defer >= today && defer < tomorrow;

                return isDueToday || isDeferredToday;
            });

            // Filter for overdue tasks
            const overdueTasks = tasks.filter(task => {
                if (task.completed || task.dropped) return false;

                const due = task.dueDate;
                return due && due < today;
            });

            // Build task summary for AI analysis
            const taskData = {
                todayCount: todayTasks.length,
                overdueCount: overdueTasks.length,
                todayTasks: todayTasks.map(t => ({
                    name: t.name,
                    project: t.containingProject ? t.containingProject.name : "Inbox",
                    dueTime: t.dueDate ? t.dueDate.toLocaleTimeString('en-US', {hour: 'numeric', minute: '2-digit'}) : null,
                    flagged: t.flagged,
                    tags: t.tags.map(tag => tag.name),
                    estimatedMinutes: t.estimatedMinutes
                })),
                overdueTasks: overdueTasks.map(t => ({
                    name: t.name,
                    project: t.containingProject ? t.containingProject.name : "Inbox",
                    daysOverdue: Math.floor((today - t.dueDate) / (1000 * 60 * 60 * 24)),
                    flagged: t.flagged,
                    tags: t.tags.map(tag => tag.name)
                }))
            };

            // Check if we have any tasks to analyze
            if (taskData.todayCount === 0 && taskData.overdueCount === 0) {
                const alert = new Alert(
                    "AI Task Analyzer",
                    "No tasks found for today or overdue. Great job staying on top of things! 🎉"
                );
                alert.show();
                return;
            }

            // Create AI session
            const session = new LanguageModel.Session();

            // Prepare prompt for AI analysis
            const prompt = `Analyze these OmniFocus tasks and provide actionable insights:

TODAY'S TASKS (${taskData.todayCount}):
${JSON.stringify(taskData.todayTasks, null, 2)}

OVERDUE TASKS (${taskData.overdueCount}):
${JSON.stringify(taskData.overdueTasks, null, 2)}

Please provide:
1. **Priority Recommendations**: Which 3 tasks should I tackle first today and why?
2. **Workload Analysis**: Is today's workload manageable? Any concerns?
3. **Overdue Insights**: What patterns do you see in overdue tasks? Any recommendations?
4. **Time Management**: Based on estimated times, how should I structure my day?
5. **Action Items**: Any immediate actions to take?

Keep the analysis concise, actionable, and GTD-aligned (Getting Things Done methodology).`;

            // Request structured analysis using schema
            const schema = new LanguageModel.Schema({
                type: "object",
                properties: {
                    priorityRecommendations: {
                        type: "array",
                        description: "Top 3 tasks to tackle first",
                        items: {
                            type: "object",
                            properties: {
                                taskName: { type: "string" },
                                reason: { type: "string" }
                            }
                        }
                    },
                    workloadAnalysis: {
                        type: "object",
                        properties: {
                            isManageable: { type: "boolean" },
                            summary: { type: "string" },
                            concerns: { type: "array", items: { type: "string" } }
                        }
                    },
                    overdueInsights: {
                        type: "object",
                        properties: {
                            patterns: { type: "array", items: { type: "string" } },
                            recommendations: { type: "array", items: { type: "string" } }
                        }
                    },
                    timeManagement: {
                        type: "object",
                        properties: {
                            totalEstimatedMinutes: { type: "number" },
                            suggestedSchedule: { type: "array", items: { type: "string" } }
                        }
                    },
                    actionItems: {
                        type: "array",
                        description: "Immediate actions to take",
                        items: { type: "string" }
                    }
                }
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
            message += `📋 WORKLOAD: ${analysis.workloadAnalysis.isManageable ? "✅ Manageable" : "⚠️ Heavy"}\n`;
            message += `${analysis.workloadAnalysis.summary}\n`;
            if (analysis.workloadAnalysis.concerns.length > 0) {
                message += `Concerns:\n`;
                analysis.workloadAnalysis.concerns.forEach(c => message += `• ${c}\n`);
            }
            message += `\n`;

            // Overdue Insights
            if (taskData.overdueCount > 0) {
                message += `⏰ OVERDUE INSIGHTS:\n`;
                if (analysis.overdueInsights.patterns.length > 0) {
                    message += `Patterns:\n`;
                    analysis.overdueInsights.patterns.forEach(p => message += `• ${p}\n`);
                }
                if (analysis.overdueInsights.recommendations.length > 0) {
                    message += `Recommendations:\n`;
                    analysis.overdueInsights.recommendations.forEach(r => message += `• ${r}\n`);
                }
                message += `\n`;
            }

            // Time Management
            if (analysis.timeManagement.suggestedSchedule.length > 0) {
                message += `⏱️ SUGGESTED SCHEDULE:\n`;
                analysis.timeManagement.suggestedSchedule.forEach(s => message += `• ${s}\n`);
                message += `\n`;
            }

            // Action Items
            if (analysis.actionItems.length > 0) {
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
            const errorAlert = new Alert("Error", `Failed to analyze tasks: ${error.message}\n\nRequirements:\n• OmniFocus 4.8+\n• macOS 15.2+ or iOS 18.2+\n• Apple Silicon/iPhone 15 Pro+`);
            errorAlert.show();
        }
    });

    // Always enable this action
    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
