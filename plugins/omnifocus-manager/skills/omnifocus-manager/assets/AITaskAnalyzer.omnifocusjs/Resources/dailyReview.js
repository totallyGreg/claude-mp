/**
 * Daily Review - AI-powered GTD daily review
 *
 * Shows completed work, today's tasks, and overdue items, then uses
 * Apple Foundation Models to provide GTD coaching: celebrating wins,
 * recommending top next actions, and triaging overdue items.
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - macOS 26+
 * - Apple Intelligence enabled
 */

(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        const fmUtils = this.plugIn.library("foundationModelsUtils");

        if (!fmUtils.isAvailable()) {
            fmUtils.showUnavailableAlert();
            return;
        }

        try {
            const metrics = this.plugIn.library("taskMetrics");

            const completedTasks = metrics.getCompletedToday();
            const todayTasks = metrics.getTodayTasks();
            const overdueTasks = metrics.getOverdueTasks();
            const flaggedTasks = metrics.getFlaggedTasks();

            const today = new Date();
            today.setHours(0, 0, 0, 0);

            // Limit inputs for FM token budget
            const maxEach = 10;
            const limitedCompleted = completedTasks.slice(0, maxEach);
            const limitedToday = todayTasks.slice(0, maxEach);
            const limitedOverdue = overdueTasks.slice(0, maxEach);

            // Build concise prompt sections
            const completedSummary = limitedCompleted.length > 0
                ? limitedCompleted.map(t => `- ${t.name} [${t.project || "Inbox"}]`).join('\n')
                : "(none yet today)";

            const todaySummary = limitedToday.length > 0
                ? limitedToday.map(t => `- ${t.flagged ? "🚩 " : ""}${t.name} [${t.project || "Inbox"}]`).join('\n')
                : "(no tasks due today)";

            const overdueSummary = limitedOverdue.length > 0
                ? limitedOverdue.map(t => {
                    const days = Math.floor((new Date() - new Date(t.dueDate)) / (1000 * 60 * 60 * 24));
                    return `- ${t.name} [${t.project || "Inbox"}] (${days}d overdue)`;
                }).join('\n')
                : "(none)";

            const prompt = `GTD daily review for OmniFocus:

COMPLETED TODAY (${completedTasks.length} total, showing ${limitedCompleted.length}):
${completedSummary}

TODAY'S NEXT ACTIONS (${todayTasks.length} total, showing ${limitedToday.length}):
${todaySummary}

OVERDUE (${overdueTasks.length} total, showing ${limitedOverdue.length}):
${overdueSummary}

FLAGGED: ${flaggedTasks.length} tasks

Using GTD principles, provide:
1. Brief celebration of completed work
2. Top 3 concrete next actions for now (specific, physical, doable)
3. Overdue triage: do today / defer / drop
4. Workload assessment: in-control or overwhelmed?`;

            const schema = LanguageModel.Schema.fromJSON({
                name: "daily-review-schema",
                properties: [
                    {
                        name: "completedCelebration",
                        description: "Brief acknowledgment of what was accomplished"
                    },
                    {
                        name: "topNextActions",
                        description: "Top 3 specific next actions to take now",
                        schema: {
                            arrayOf: {
                                name: "next-action",
                                properties: [
                                    {name: "task"},
                                    {name: "reason"}
                                ]
                            },
                            maximumElements: 3
                        }
                    },
                    {
                        name: "overdueAdvice",
                        description: "Triage advice for overdue items",
                        isOptional: true
                    },
                    {
                        name: "systemHealth",
                        schema: {
                            name: "health-enum",
                            anyOf: [
                                {constant: "in-control"},
                                {constant: "manageable"},
                                {constant: "overwhelmed"}
                            ]
                        }
                    },
                    {
                        name: "workloadNote",
                        description: "One sentence honest workload assessment"
                    }
                ]
            });

            const opts = new LanguageModel.GenerationOptions();
            opts.maximumResponseTokens = 300;

            const session = new LanguageModel.Session(
                "You are a GTD productivity coach. Be concise and direct. Use specific GTD vocabulary: next actions, projects, contexts. Focus on what is actionable right now."
            );

            const response = await session.respondWithSchema(prompt, schema, opts);
            const review = JSON.parse(response);

            // Format display message
            const healthIcon = {
                "in-control": "✅",
                "manageable": "🟡",
                "overwhelmed": "🔴"
            }[review.systemHealth] || "📊";

            let message = `${healthIcon} ${review.workloadNote || ""}\n\n`;

            if (review.completedCelebration) {
                message += `🎉 WINS TODAY:\n${review.completedCelebration}\n\n`;
            }

            message += `🎯 TOP NEXT ACTIONS:\n`;
            const actions = Array.isArray(review.topNextActions) ? review.topNextActions : [];
            if (actions.length > 0) {
                actions.forEach((a, i) => {
                    message += `${i + 1}. ${a.task}\n   → ${a.reason}\n`;
                });
            } else {
                message += "(No tasks found to prioritize)\n";
            }

            if (overdueTasks.length > 0 && review.overdueAdvice) {
                message += `\n⏰ OVERDUE TRIAGE:\n${review.overdueAdvice}\n`;
            }

            message += `\n📊 Stats: ${completedTasks.length} done · ${todayTasks.length} today · ${overdueTasks.length} overdue · ${flaggedTasks.length} flagged`;

            const resultAlert = new Alert("Daily Review", message);
            resultAlert.addOption("Copy to Clipboard");
            resultAlert.addOption("Done");
            const choice = await resultAlert.show();

            if (choice === 0) {
                Pasteboard.general.string = message;
            }

        } catch (error) {
            console.error("Daily Review error:", error);
            const fmUtils = this.plugIn.library("foundationModelsUtils");
            const errorAlert = new Alert("Daily Review Error",
                `Could not complete review: ${error.message}\n\n${fmUtils.getUnavailableMessage()}`
            );
            errorAlert.show();
        }
    });

    action.validate = function(selection, sender) {
        return Device.current.operatingSystemVersion.atLeast(new Version("26"));
    };

    return action;
})();
