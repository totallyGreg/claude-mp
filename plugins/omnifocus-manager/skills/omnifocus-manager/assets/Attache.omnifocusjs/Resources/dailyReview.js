/**
 * Daily Review - AI-powered GTD daily review
 *
 * Shows completed work, today's tasks (due + newly deferred), overdue items,
 * and system orientation stats. Uses Apple Foundation Models for GTD coaching.
 * Absorbs Overview and TodaysTasks plugin functionality.
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - macOS 26+
 * - Apple Intelligence enabled
 */

(() => {
    function section(title) {
        const pad = '─'.repeat(Math.max(0, 44 - title.length - 4));
        return `── ${title} ${pad}`;
    }

    const action = new PlugIn.Action(async function(selection, sender) {
        const fmUtils = this.plugIn.library("foundationModelsUtils");

        if (!fmUtils.isAvailable()) {
            fmUtils.showUnavailableAlert();
            return;
        }

        try {
            const prefsManager = this.plugIn.library("preferencesManager");
            const hasCachedPrefs = prefsManager.hasPreferences();
            const metrics = this.plugIn.library("taskMetrics");

            // Single-pass collection for all metrics
            const all = metrics.collectAllMetrics();

            const completedTasks = all.completedToday;
            const todayTasks = all.today;
            const overdueTasks = all.overdue;
            const flaggedTasks = all.flagged;
            const deferredTasks = all.deferredToday;
            const inboxTasks = all.inbox;

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
                ? limitedToday.map(t => `- ${t.flagged ? "* " : ""}${t.name} [${t.project || "Inbox"}]`).join('\n')
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
INBOX: ${inboxTasks.length} items

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

            // FM coaching (optional - degrades gracefully)
            let review = null;
            try {
                const session = fmUtils.createSession(
                    "You are a GTD productivity coach. Be concise and direct. Use specific GTD vocabulary: next actions, projects, contexts. Focus on what is actionable right now."
                );
                const response = await session.respondWithSchema(prompt, schema, opts);
                review = JSON.parse(response);
            } catch (fmError) {
                console.error("FM coaching unavailable:", fmError);
            }

            // Format display message
            let message = "";
            let md = "";

            // Calendar prompt (GTD: date-specific commitments are non-negotiable anchors)
            message += "Review your calendar for today's commitments.\n\n";
            md += "> Review your calendar for today's commitments.\n\n";

            if (review) {
                const healthIcon = {
                    "in-control": "✅",
                    "manageable": "🟡",
                    "overwhelmed": "🔴"
                }[review.systemHealth] || "📊";

                message += `${healthIcon} ${review.workloadNote || ""}\n\n`;
                md += `## ${healthIcon} Status\n${review.workloadNote || ""}\n\n`;

                if (review.completedCelebration) {
                    message += `${section("Wins Today")}\n${review.completedCelebration}\n\n`;
                    md += `## Wins Today\n${review.completedCelebration}\n\n`;
                }

                message += `${section("Top Next Actions")}\n`;
                md += `## Top Next Actions\n`;
                const actions = Array.isArray(review.topNextActions) ? review.topNextActions : [];
                if (actions.length > 0) {
                    actions.forEach((a, i) => {
                        message += `${i + 1}. ${a.task}\n   → ${a.reason}\n`;
                        md += `${i + 1}. **${a.task}** — ${a.reason}\n`;
                    });
                } else {
                    message += "(No tasks found to prioritize)\n";
                    md += "(No tasks found to prioritize)\n";
                }

                if (overdueTasks.length > 0 && review.overdueAdvice) {
                    message += `\n${section("Overdue Triage")}\n${review.overdueAdvice}\n`;
                    md += `\n## Overdue Triage\n${review.overdueAdvice}\n`;
                }
            }

            // Newly available deferred items (absorbed from TodaysTasks)
            if (deferredTasks.length > 0) {
                const deferredLabel = `${deferredTasks.length} deferred item${deferredTasks.length !== 1 ? 's' : ''} now actionable`;
                message += `\n${section("Newly Available")} ${deferredLabel}\n`;
                md += `\n## Newly Available (${deferredTasks.length})\n`;
                deferredTasks.slice(0, 5).forEach(t => {
                    message += `  · ${t.name} [${t.project || "Inbox"}]\n`;
                    md += `- ${t.name} \`[${t.project || "Inbox"}]\`\n`;
                });
                if (deferredTasks.length > 5) {
                    message += `  ··· and ${deferredTasks.length - 5} more\n`;
                    md += `- _…and ${deferredTasks.length - 5} more_\n`;
                }
            }

            // System orientation stats
            message += `\n${'─'.repeat(44)}\n✅ ${completedTasks.length} done · 📋 ${todayTasks.length} today · ⚠️ ${overdueTasks.length} overdue · 🚩 ${flaggedTasks.length} flagged · 📥 ${inboxTasks.length} inbox`;
            md += `\n---\n✅ ${completedTasks.length} done · 📋 ${todayTasks.length} today · ⚠️ ${overdueTasks.length} overdue · 🚩 ${flaggedTasks.length} flagged · 📥 ${inboxTasks.length} inbox`;

            if (!hasCachedPrefs) {
                message += `\n\nTip: Run Attache: System Setup to cache your system map for richer reviews.`;
                md += `\n\n> **Tip:** Run Attache: System Setup to cache your system map for richer reviews.`;
            }

            const resultAlert = new Alert("Attache: Daily Review", message);
            resultAlert.addOption("Copy to Clipboard");
            resultAlert.addOption("Done");
            const choice = await resultAlert.show();

            if (choice === 0) {
                Pasteboard.general.string = md;
            }

        } catch (error) {
            console.error("Daily Review error:", error);
            const errorAlert = new Alert("Daily Review Error",
                `Could not complete review: ${error.message}`
            );
            errorAlert.show();
        }
    });

    action.validate = function(selection, sender) {
        return Device.current.operatingSystemVersion.atLeast(new Version("26"));
    };

    return action;
})();
