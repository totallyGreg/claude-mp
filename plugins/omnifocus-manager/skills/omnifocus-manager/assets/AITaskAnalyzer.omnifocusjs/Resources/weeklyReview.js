/**
 * Weekly Review - Step-by-step GTD weekly review with Apple Foundation Models
 *
 * Guides user through 6 GTD horizons via sequential Alerts, with on-device
 * AI coaching at each step. User can stop at any point.
 *
 * Steps:
 *   1. Get Clear (Inbox)
 *   2. Projects Sweep (stalled projects)
 *   3. Someday/Maybe (on-hold projects not reviewed in 90+ days)
 *   4. Celebrate & Reflect (completed this week)
 *   5. Horizon Check (overdue + upcoming 7 days)
 *   6. Plan the Week (synthesis)
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - macOS 26+
 * - Apple Intelligence enabled
 */

// Module-level concurrency guard — prevents double-invocation during FM calls
let _reviewInProgress = false;

(() => {
    const GTD_COACH = "You are a GTD productivity coach. Be concise and direct. Use specific GTD vocabulary. Focus on actionable recommendations.";

    /**
     * Call Foundation Models with per-step isolation.
     * Returns coaching object or null if FM is unavailable/fails.
     */
    async function getCoaching(prompt, schema) {
        try {
            const opts = new LanguageModel.GenerationOptions();
            opts.maximumResponseTokens = 250;
            const session = new LanguageModel.Session(GTD_COACH);
            const response = await session.respondWithSchema(prompt, schema, opts);
            return JSON.parse(response);
        } catch (err) {
            console.error("FM coaching error:", err);
            return null;
        }
    }

    /**
     * Show a review step Alert.
     * Returns true to continue, false to stop.
     */
    async function showStep(stepNum, totalSteps, title, message) {
        const alert = new Alert(`Step ${stepNum} of ${totalSteps}: ${title}`, message);
        alert.addOption("Continue");
        alert.addOption("Stop Review");
        const choice = await alert.show();
        return choice === 0;
    }

    const action = new PlugIn.Action(async function(selection, sender) {
        const fmUtils = this.plugIn.library("foundationModelsUtils");

        if (!fmUtils.isAvailable()) {
            fmUtils.showUnavailableAlert();
            return;
        }

        // Concurrency guard
        if (_reviewInProgress) {
            const alert = new Alert("Weekly Review", "A review is already in progress.");
            alert.addOption("OK");
            await alert.show();
            return;
        }

        _reviewInProgress = true;

        // Accumulate summary scalars for step 6 synthesis
        const reviewSummary = {
            inboxCount: 0,
            stalledCount: 0,
            onHoldCount: 0,
            completedThisWeek: 0,
            overdueCount: 0,
            upcomingCount: 0
        };

        try {
            const metrics = this.plugIn.library("taskMetrics");
            const projectParser = this.plugIn.library("projectParser");
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            // ── Step 1: Get Clear (Inbox) ──────────────────────────────────────
            // Filter inbox tasks: tasks not assigned to any project
            // OmniFocus may expose an `inboxTasks` global; we use flattenedTasks filter for reliability
            const inboxTasks = flattenedTasks.filter(
                t => t.containingProject === null && !t.completed && !t.dropped
            );

            reviewSummary.inboxCount = inboxTasks.length;

            let step1Message = "";
            if (inboxTasks.length === 0) {
                step1Message = "✓ Inbox is empty — great job!\n\nNothing to process here.";
            } else {
                const oldest = inboxTasks.reduce((a, b) =>
                    (a.added && b.added && a.added < b.added) ? a : b
                );
                const oldestDays = oldest.added
                    ? Math.floor((new Date() - oldest.added) / (1000 * 60 * 60 * 24))
                    : 0;

                const coaching = await getCoaching(
                    `GTD inbox: ${inboxTasks.length} items. Oldest is ${oldestDays} days old. Provide 2-3 concise tips for processing to zero.`,
                    LanguageModel.Schema.fromJSON({
                        name: "inbox-schema",
                        properties: [
                            {name: "strategy", description: "How to approach processing this inbox"},
                            {name: "tips", schema: {arrayOf: {constant: "tip"}, maximumElements: 3}}
                        ]
                    })
                );

                step1Message = `📥 INBOX: ${inboxTasks.length} items (oldest: ${oldestDays}d ago)\n\n`;
                if (coaching) {
                    step1Message += `Strategy: ${coaching.strategy || ""}\n`;
                    const tips = Array.isArray(coaching.tips) ? coaching.tips : [];
                    if (tips.length > 0) {
                        step1Message += tips.map(t => `• ${t}`).join('\n');
                    }
                } else {
                    step1Message += "Process each item: do (2 min), delegate, defer, or drop.";
                }
            }

            const cont1 = await showStep(1, 6, "Get Clear — Inbox", step1Message);
            if (!cont1) { return; }

            // ── Step 2: Projects Sweep (stalled) ──────────────────────────────
            const activeProjects = flattenedProjects
                .filter(p => p.status === Project.Status.Active)
                .slice(0, 50);
            const parsedActive = projectParser.parseProjects(activeProjects, false);
            const stalledProjects = projectParser.identifyStalledProjects(parsedActive);
            reviewSummary.stalledCount = stalledProjects.length;

            let step2Message = "";
            if (stalledProjects.length === 0) {
                step2Message = "✓ No stalled projects — every active project has a next action!";
            } else {
                const stalledNames = stalledProjects.slice(0, 10).map(p => p.name);
                const coaching = await getCoaching(
                    `${stalledProjects.length} stalled OmniFocus projects (no next actions): ${stalledNames.join(', ')}. Suggest how to unstall each — add a next action, put on hold, or drop.`,
                    LanguageModel.Schema.fromJSON({
                        name: "stalled-schema",
                        properties: [
                            {name: "overview", description: "Brief pattern assessment"},
                            {
                                name: "suggestions",
                                schema: {
                                    arrayOf: {
                                        name: "suggestion",
                                        properties: [
                                            {name: "project"},
                                            {name: "action", schema: {anyOf: [{constant: "add-next-action"}, {constant: "put-on-hold"}, {constant: "drop"}]}},
                                            {name: "nextAction", isOptional: true}
                                        ]
                                    },
                                    maximumElements: 5
                                }
                            }
                        ]
                    })
                );

                step2Message = `⚠️ STALLED PROJECTS: ${stalledProjects.length}\n\n`;
                step2Message += stalledProjects.slice(0, 10).map(p =>
                    `• ${p.name}${p.folder ? ` (${p.folder})` : ""} — ${p.reason}`
                ).join('\n');

                if (coaching) {
                    step2Message += `\n\n${coaching.overview || ""}\n`;
                    const suggestions = Array.isArray(coaching.suggestions) ? coaching.suggestions : [];
                    suggestions.forEach(s => {
                        const actionLabel = {
                            "add-next-action": "→ Add next action",
                            "put-on-hold": "→ Put on hold",
                            "drop": "→ Drop"
                        }[s.action] || "→ Review";
                        step2Message += `\n${s.project}: ${actionLabel}`;
                        if (s.nextAction) step2Message += ` — "${s.nextAction}"`;
                    });
                }
            }

            const cont2 = await showStep(2, 6, "Projects Sweep — Stalled", step2Message);
            if (!cont2) { return; }

            // ── Step 3: Someday/Maybe (on-hold, 90+ days) ─────────────────────
            const onHoldProjects = metrics.getOnHoldProjects();
            reviewSummary.onHoldCount = onHoldProjects.length;

            let step3Message = "";
            if (onHoldProjects.length === 0) {
                step3Message = "✓ No neglected Someday/Maybe projects.\n\nAll on-hold projects have been touched in the last 90 days.";
            } else {
                const onHoldNames = onHoldProjects.slice(0, 8).map(p => {
                    const age = p.lastModified
                        ? Math.floor((new Date() - p.lastModified) / (1000 * 60 * 60 * 24))
                        : null;
                    return age ? `${p.name} (${age}d)` : p.name;
                });

                const coaching = await getCoaching(
                    `${onHoldProjects.length} on-hold OmniFocus projects not reviewed in 90+ days: ${onHoldNames.join(', ')}. For each, recommend: activate, keep on hold, or archive/drop.`,
                    LanguageModel.Schema.fromJSON({
                        name: "someday-schema",
                        properties: [
                            {name: "overview"},
                            {
                                name: "decisions",
                                schema: {
                                    arrayOf: {
                                        name: "decision",
                                        properties: [
                                            {name: "project"},
                                            {name: "recommendation", schema: {anyOf: [{constant: "activate"}, {constant: "keep-on-hold"}, {constant: "archive"}]}}
                                        ]
                                    },
                                    maximumElements: 5
                                }
                            }
                        ]
                    })
                );

                step3Message = `📋 SOMEDAY/MAYBE: ${onHoldProjects.length} neglected projects\n\n`;
                step3Message += onHoldNames.map(n => `• ${n}`).join('\n');

                if (coaching) {
                    step3Message += `\n\n${coaching.overview || ""}\n`;
                    const decisions = Array.isArray(coaching.decisions) ? coaching.decisions : [];
                    decisions.forEach(d => {
                        const label = {
                            "activate": "▶️ Activate",
                            "keep-on-hold": "⏸ Keep",
                            "archive": "🗄 Archive"
                        }[d.recommendation] || "→ Review";
                        step3Message += `\n${d.project}: ${label}`;
                    });
                }
            }

            const cont3 = await showStep(3, 6, "Someday/Maybe Review", step3Message);
            if (!cont3) { return; }

            // ── Step 4: Celebrate & Reflect (completed this week) ─────────────
            const completedTasks = metrics.getCompletedThisWeek();
            reviewSummary.completedThisWeek = completedTasks.length;

            let step4Message = "";
            if (completedTasks.length === 0) {
                step4Message = "No tasks recorded as completed this week.\n\nIf you completed work, make sure to check tasks off in OmniFocus.";
            } else {
                // Group by project for display
                const byProject = {};
                completedTasks.slice(0, 20).forEach(t => {
                    const proj = t.project || "Inbox";
                    if (!byProject[proj]) byProject[proj] = [];
                    byProject[proj].push(t.name);
                });

                const projectList = Object.entries(byProject)
                    .map(([proj, tasks]) => `${proj} (${tasks.length})`)
                    .join(', ');

                const coaching = await getCoaching(
                    `Completed ${completedTasks.length} tasks this week across projects: ${projectList}. Celebrate wins and identify completion patterns.`,
                    LanguageModel.Schema.fromJSON({
                        name: "celebrate-schema",
                        properties: [
                            {name: "celebration", description: "Acknowledge the wins"},
                            {name: "pattern", description: "What does the completion pattern suggest about how this person works best?"}
                        ]
                    })
                );

                step4Message = `🎉 COMPLETED THIS WEEK: ${completedTasks.length} tasks\n\n`;
                Object.entries(byProject).slice(0, 6).forEach(([proj, tasks]) => {
                    step4Message += `• ${proj}: ${tasks.length} task${tasks.length !== 1 ? 's' : ''}\n`;
                });

                if (coaching) {
                    step4Message += `\n${coaching.celebration || ""}\n`;
                    if (coaching.pattern) {
                        step4Message += `\nPattern: ${coaching.pattern}`;
                    }
                }
            }

            const cont4 = await showStep(4, 6, "Celebrate & Reflect", step4Message);
            if (!cont4) { return; }

            // ── Step 5: Horizon Check (overdue + next 7 days) ─────────────────
            const overdueTasks = metrics.getOverdueTasks();
            const upcomingTasks = flattenedTasks.filter(t => {
                if (t.completed || t.dropped) return false;
                const due = t.dueDate;
                if (!due) return false;
                const sevenDays = new Date(today);
                sevenDays.setDate(sevenDays.getDate() + 7);
                return due >= today && due < sevenDays;
            }).slice(0, 20);

            reviewSummary.overdueCount = overdueTasks.length;
            reviewSummary.upcomingCount = upcomingTasks.length;

            let step5Message = "";
            const hasHorizonData = overdueTasks.length > 0 || upcomingTasks.length > 0;

            if (!hasHorizonData) {
                step5Message = "✓ No overdue tasks and no upcoming due dates in the next 7 days.\n\nYour horizon looks clear!";
            } else {
                const overdueList = overdueTasks.slice(0, 5).map(t => {
                    const days = Math.floor((new Date() - new Date(t.dueDate)) / (1000 * 60 * 60 * 24));
                    return `${t.name} (${days}d)`;
                }).join(', ');

                const upcomingList = upcomingTasks.slice(0, 5).map(t => t.name).join(', ');

                const coaching = await getCoaching(
                    `Overdue: ${overdueTasks.length} tasks${overdueTasks.length > 0 ? " including: " + overdueList : ""}. Due next 7 days: ${upcomingTasks.length} tasks${upcomingTasks.length > 0 ? " including: " + upcomingList : ""}. Advise on realistic rescheduling.`,
                    LanguageModel.Schema.fromJSON({
                        name: "horizon-schema",
                        properties: [
                            {name: "overdueAdvice", description: "What to do with overdue items", isOptional: true},
                            {name: "weekPreview", description: "What to expect in the coming week"},
                            {name: "rescheduleRecommendation", description: "How many overdue items to tackle this week"}
                        ]
                    })
                );

                step5Message = "";
                if (overdueTasks.length > 0) {
                    step5Message += `⏰ OVERDUE: ${overdueTasks.length} tasks\n`;
                    overdueTasks.slice(0, 5).forEach(t => {
                        const days = Math.floor((new Date() - new Date(t.dueDate)) / (1000 * 60 * 60 * 24));
                        step5Message += `  • ${t.name} [${t.project || "Inbox"}] — ${days}d\n`;
                    });
                    if (overdueTasks.length > 5) step5Message += `  … and ${overdueTasks.length - 5} more\n`;
                    step5Message += "\n";
                }

                step5Message += `📅 DUE NEXT 7 DAYS: ${upcomingTasks.length} tasks\n`;
                upcomingTasks.slice(0, 5).forEach(t => {
                    step5Message += `  • ${t.name}\n`;
                });
                if (upcomingTasks.length > 5) step5Message += `  … and ${upcomingTasks.length - 5} more\n`;

                if (coaching) {
                    if (coaching.overdueAdvice) step5Message += `\n${coaching.overdueAdvice}\n`;
                    if (coaching.rescheduleRecommendation) step5Message += `\n${coaching.rescheduleRecommendation}`;
                }
            }

            const cont5 = await showStep(5, 6, "Horizon Check", step5Message);
            if (!cont5) { return; }

            // ── Step 6: Plan the Week (synthesis) ────────────────────────────
            const coaching6 = await getCoaching(
                `GTD weekly review complete. System snapshot: inbox=${reviewSummary.inboxCount}, stalled projects=${reviewSummary.stalledCount}, someday/maybe neglected=${reviewSummary.onHoldCount}, completed this week=${reviewSummary.completedThisWeek}, overdue=${reviewSummary.overdueCount}, due next 7 days=${reviewSummary.upcomingCount}. Provide top 3 weekly priorities and a system health score (1-10).`,
                LanguageModel.Schema.fromJSON({
                    name: "plan-schema",
                    properties: [
                        {
                            name: "weeklyPriorities",
                            schema: {
                                arrayOf: {constant: "priority"},
                                maximumElements: 3
                            }
                        },
                        {name: "systemHealthScore", description: "System health 1-10 with brief reason"},
                        {name: "keyInsight", description: "One sentence insight from this review"}
                    ]
                })
            );

            let step6Message = `📊 REVIEW SUMMARY:\n`;
            step6Message += `  • Inbox: ${reviewSummary.inboxCount} items\n`;
            step6Message += `  • Stalled projects: ${reviewSummary.stalledCount}\n`;
            step6Message += `  • Someday/Maybe neglected: ${reviewSummary.onHoldCount}\n`;
            step6Message += `  • Completed this week: ${reviewSummary.completedThisWeek}\n`;
            step6Message += `  • Overdue: ${reviewSummary.overdueCount}\n`;
            step6Message += `  • Due next 7 days: ${reviewSummary.upcomingCount}\n\n`;

            if (coaching6) {
                const priorities = Array.isArray(coaching6.weeklyPriorities) ? coaching6.weeklyPriorities : [];
                if (priorities.length > 0) {
                    step6Message += `🎯 TOP PRIORITIES THIS WEEK:\n`;
                    priorities.forEach((p, i) => step6Message += `${i + 1}. ${p}\n`);
                    step6Message += "\n";
                }
                if (coaching6.systemHealthScore) {
                    step6Message += `💚 SYSTEM HEALTH: ${coaching6.systemHealthScore}\n\n`;
                }
                if (coaching6.keyInsight) {
                    step6Message += `💡 ${coaching6.keyInsight}`;
                }
            }

            const finalAlert = new Alert("Weekly Review Complete", step6Message);
            finalAlert.addOption("Copy Summary");
            finalAlert.addOption("Done");
            const finalChoice = await finalAlert.show();

            if (finalChoice === 0) {
                Pasteboard.general.string = step6Message;
            }

        } catch (error) {
            console.error("Weekly Review error:", error);
            const fmUtils = this.plugIn.library("foundationModelsUtils");
            const errorAlert = new Alert("Weekly Review Error",
                `Review failed: ${error.message}\n\n${fmUtils.getUnavailableMessage()}`
            );
            errorAlert.show();
        } finally {
            _reviewInProgress = false;
        }
    });

    action.validate = function(selection, sender) {
        return Device.current.operatingSystemVersion.atLeast(new Version("26"));
    };

    return action;
})();
