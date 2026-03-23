/**
 * Weekly Review - Step-by-step GTD weekly review with Apple Foundation Models
 *
 * Guides user through 7 GTD horizons via sequential Alerts, with on-device
 * AI coaching at each step. User can stop at any point.
 *
 * Steps:
 *   1. Get Clear (Inbox)
 *   2. Projects Sweep (stalled projects)
 *   3. Waiting For (delegated/waiting items)
 *   4. Someday/Maybe (on-hold projects not reviewed in 90+ days)
 *   5. Celebrate & Reflect (completed this week)
 *   6. Horizon Check (overdue + upcoming 7 days)
 *   7. Plan the Week (synthesis)
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

    // Concurrency guard — scoped to IIFE closure so it persists across perform() calls
    let _reviewInProgress = false;

    const GTD_COACH = "You are a GTD productivity coach. Be concise and direct. Use specific GTD vocabulary. Focus on actionable recommendations.";
    const TOTAL_STEPS = 7;

    /**
     * Call Foundation Models with a shared session.
     * Returns coaching object or null if FM fails.
     */
    async function getCoaching(session, prompt, schema) {
        try {
            const opts = new LanguageModel.GenerationOptions();
            opts.maximumResponseTokens = 250;
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
    async function showStep(stepNum, title, message) {
        const alert = new Alert(`Step ${stepNum} of ${TOTAL_STEPS}: ${title}`, message);
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

        // Accumulate summary scalars for step 7 synthesis
        const reviewSummary = {
            inboxCount: 0,
            stalledCount: 0,
            waitingForCount: 0,
            onHoldCount: 0,
            completedThisWeek: 0,
            overdueCount: 0,
            upcomingCount: 0
        };

        try {
            const prefsManager = this.plugIn.library("preferencesManager");
            const hasCachedPrefs = prefsManager.hasPreferences();
            const metrics = this.plugIn.library("taskMetrics");
            const projectParser = this.plugIn.library("projectParser");

            // Waiting For detection — uses canonical patterns from taskMetrics library
            function isWaitingFor(task) {
                const tagNames = task.tags.map(t => t.name.toLowerCase());
                return tagNames.some(name =>
                    metrics.WAITING_PATTERNS.some(pattern => name.includes(pattern))
                );
            }
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            // Create one FM session for the entire review (reuse across all steps)
            const session = fmUtils.createSession(GTD_COACH);

            // == Step 1: Get Clear (Inbox) ==
            const inboxTasks = flattenedTasks.filter(
                t => t.containingProject === null && !t.completed && !t.dropped
            );

            reviewSummary.inboxCount = inboxTasks.length;

            let step1Message = "";
            if (inboxTasks.length === 0) {
                step1Message = "Inbox is empty — great job!\n\nNothing to process here.";
            } else {
                const oldest = inboxTasks.reduce((a, b) =>
                    (a.added && b.added && a.added < b.added) ? a : b
                );
                const oldestDays = oldest.added
                    ? Math.floor((new Date() - oldest.added) / (1000 * 60 * 60 * 24))
                    : 0;

                const coaching = await getCoaching(session,
                    `GTD inbox: ${inboxTasks.length} items. Oldest is ${oldestDays} days old. Provide 2-3 concise tips for processing to zero.`,
                    LanguageModel.Schema.fromJSON({
                        name: "inbox-schema",
                        properties: [
                            {name: "strategy", description: "How to approach processing this inbox"},
                            {name: "tips", schema: {arrayOf: {constant: "tip"}, maximumElements: 3}}
                        ]
                    })
                );

                step1Message = `${section("Inbox")} ${inboxTasks.length} items (oldest: ${oldestDays}d ago)\n\n`;
                if (coaching) {
                    step1Message += `Strategy: ${coaching.strategy || ""}\n`;
                    const tips = Array.isArray(coaching.tips) ? coaching.tips : [];
                    if (tips.length > 0) {
                        step1Message += tips.map(t => `  · ${t}`).join('\n');
                    }
                } else {
                    step1Message += "Process each item: do (2 min), delegate, defer, or drop.";
                }
            }

            const cont1 = await showStep(1, "Get Clear — Inbox", step1Message);
            if (!cont1) { return; }

            // == Step 2: Projects Sweep (stalled) ==
            const activeProjects = flattenedProjects
                .filter(p => p.status === Project.Status.Active)
                .slice(0, 50);
            const parsedActive = projectParser.parseProjects(activeProjects, false);
            const stalledProjects = projectParser.identifyStalledProjects(parsedActive);
            reviewSummary.stalledCount = stalledProjects.length;

            let step2Message = "";
            if (stalledProjects.length === 0) {
                step2Message = "No stalled projects — every active project has a next action!";
            } else {
                const stalledNames = stalledProjects.slice(0, 10).map(p => p.name);
                const coaching = await getCoaching(session,
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
                                            {name: "action", schema: {name: "stall-action-enum", anyOf: [{constant: "add-next-action"}, {constant: "put-on-hold"}, {constant: "drop"}]}},
                                            {name: "nextAction", isOptional: true}
                                        ]
                                    },
                                    maximumElements: 5
                                }
                            }
                        ]
                    })
                );

                step2Message = `${section("Stalled Projects")} ${stalledProjects.length}\n\n`;
                step2Message += stalledProjects.slice(0, 10).map(p =>
                    `  · ${p.name}${p.folder ? ` (${p.folder})` : ""} — ${p.reason}`
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

            const cont2 = await showStep(2, "Projects Sweep — Stalled", step2Message);
            if (!cont2) { return; }

            // == Step 3: Waiting For (delegated items) ==
            const waitingTasks = flattenedTasks.filter(t =>
                !t.completed && !t.dropped && isWaitingFor(t)
            );
            reviewSummary.waitingForCount = waitingTasks.length;

            let step3Message = "";
            if (waitingTasks.length === 0) {
                step3Message = "No waiting-for items found.\n\nIf you have delegated work, tag those tasks with a 'waiting' tag to track them.";
            } else {
                const waitingNames = waitingTasks.slice(0, 10).map(t => {
                    const age = t.modified
                        ? Math.floor((new Date() - t.modified) / (1000 * 60 * 60 * 24))
                        : null;
                    return age !== null ? `${t.name} (${age}d)` : t.name;
                });

                const coaching = await getCoaching(session,
                    `${waitingTasks.length} waiting-for items in OmniFocus: ${waitingNames.join(', ')}. For each, recommend: follow up, keep waiting, or drop.`,
                    LanguageModel.Schema.fromJSON({
                        name: "waiting-schema",
                        properties: [
                            {name: "overview"},
                            {
                                name: "actions",
                                schema: {
                                    arrayOf: {
                                        name: "waiting-action",
                                        properties: [
                                            {name: "item"},
                                            {name: "recommendation", schema: {name: "waiting-rec-enum", anyOf: [{constant: "follow-up"}, {constant: "keep-waiting"}, {constant: "drop"}]}}
                                        ]
                                    },
                                    maximumElements: 5
                                }
                            }
                        ]
                    })
                );

                step3Message = `${section("Waiting For")} ${waitingTasks.length} items\n\n`;
                step3Message += waitingNames.map(n => `  · ${n}`).join('\n');

                if (coaching) {
                    step3Message += `\n\n${coaching.overview || ""}\n`;
                    const actions = Array.isArray(coaching.actions) ? coaching.actions : [];
                    actions.forEach(a => {
                        const label = {
                            "follow-up": "→ Follow up",
                            "keep-waiting": "→ Keep waiting",
                            "drop": "→ Drop"
                        }[a.recommendation] || "→ Review";
                        step3Message += `\n${a.item}: ${label}`;
                    });
                }
            }

            const cont3 = await showStep(3, "Waiting For Review", step3Message);
            if (!cont3) { return; }

            // == Step 4: Someday/Maybe (on-hold, 90+ days) ==
            const onHoldProjects = metrics.getOnHoldProjects();
            reviewSummary.onHoldCount = onHoldProjects.length;

            let step4Message = "";
            if (onHoldProjects.length === 0) {
                step4Message = "No neglected Someday/Maybe projects.\n\nAll on-hold projects have been touched in the last 90 days.";
            } else {
                const onHoldNames = onHoldProjects.slice(0, 8).map(p => {
                    const age = p.lastModified
                        ? Math.floor((new Date() - p.lastModified) / (1000 * 60 * 60 * 24))
                        : null;
                    return age ? `${p.name} (${age}d)` : p.name;
                });

                const coaching = await getCoaching(session,
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
                                            {name: "recommendation", schema: {name: "someday-decision-enum", anyOf: [{constant: "activate"}, {constant: "keep-on-hold"}, {constant: "archive"}]}}
                                        ]
                                    },
                                    maximumElements: 5
                                }
                            }
                        ]
                    })
                );

                step4Message = `${section("Someday / Maybe")} ${onHoldProjects.length} neglected projects\n\n`;
                step4Message += onHoldNames.map(n => `  · ${n}`).join('\n');

                if (coaching) {
                    step4Message += `\n\n${coaching.overview || ""}\n`;
                    const decisions = Array.isArray(coaching.decisions) ? coaching.decisions : [];
                    decisions.forEach(d => {
                        const label = {
                            "activate": "→ Activate",
                            "keep-on-hold": "→ Keep",
                            "archive": "→ Archive"
                        }[d.recommendation] || "→ Review";
                        step4Message += `\n${d.project}: ${label}`;
                    });
                }
            }

            const cont4 = await showStep(4, "Someday/Maybe Review", step4Message);
            if (!cont4) { return; }

            // == Step 5: Celebrate & Reflect (completed this week) ==
            const completedTasks = metrics.getCompletedThisWeek();
            reviewSummary.completedThisWeek = completedTasks.length;

            let step5Message = "";
            if (completedTasks.length === 0) {
                step5Message = "No tasks recorded as completed this week.\n\nIf you completed work, make sure to check tasks off in OmniFocus.";
            } else {
                const byProject = {};
                completedTasks.slice(0, 20).forEach(t => {
                    const proj = t.project || "Inbox";
                    if (!byProject[proj]) byProject[proj] = [];
                    byProject[proj].push(t.name);
                });

                const projectList = Object.entries(byProject)
                    .map(([proj, tasks]) => `${proj} (${tasks.length})`)
                    .join(', ');

                const coaching = await getCoaching(session,
                    `Completed ${completedTasks.length} tasks this week across projects: ${projectList}. Celebrate wins and identify completion patterns.`,
                    LanguageModel.Schema.fromJSON({
                        name: "celebrate-schema",
                        properties: [
                            {name: "celebration", description: "Acknowledge the wins"},
                            {name: "pattern", description: "What does the completion pattern suggest about how this person works best?"}
                        ]
                    })
                );

                step5Message = `${section("Completed This Week")} ${completedTasks.length} tasks\n\n`;
                Object.entries(byProject).slice(0, 6).forEach(([proj, tasks]) => {
                    step5Message += `  · ${proj}: ${tasks.length} task${tasks.length !== 1 ? 's' : ''}\n`;
                });

                if (coaching) {
                    step5Message += `\n${coaching.celebration || ""}\n`;
                    if (coaching.pattern) {
                        step5Message += `\nPattern: ${coaching.pattern}`;
                    }
                }
            }

            const cont5 = await showStep(5, "Celebrate & Reflect", step5Message);
            if (!cont5) { return; }

            // == Step 6: Horizon Check (overdue + next 7 days) ==
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

            let step6Message = "";
            const hasHorizonData = overdueTasks.length > 0 || upcomingTasks.length > 0;

            if (!hasHorizonData) {
                step6Message = "No overdue tasks and no upcoming due dates in the next 7 days.\n\nYour horizon looks clear!";
            } else {
                const overdueList = overdueTasks.slice(0, 5).map(t => {
                    const days = Math.floor((new Date() - new Date(t.dueDate)) / (1000 * 60 * 60 * 24));
                    return `${t.name} (${days}d)`;
                }).join(', ');

                const upcomingList = upcomingTasks.slice(0, 5).map(t => t.name).join(', ');

                const coaching = await getCoaching(session,
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

                step6Message = "";
                if (overdueTasks.length > 0) {
                    step6Message += `${section("Overdue")} ${overdueTasks.length} tasks\n`;
                    overdueTasks.slice(0, 5).forEach(t => {
                        const days = Math.floor((new Date() - new Date(t.dueDate)) / (1000 * 60 * 60 * 24));
                        step6Message += `  · ${t.name} [${t.project || "Inbox"}] — ${days}d\n`;
                    });
                    if (overdueTasks.length > 5) step6Message += `  ··· and ${overdueTasks.length - 5} more\n`;
                    step6Message += "\n";
                }

                step6Message += `${section("Due Next 7 Days")} ${upcomingTasks.length} tasks\n`;
                upcomingTasks.slice(0, 5).forEach(t => {
                    step6Message += `  · ${t.name}\n`;
                });
                if (upcomingTasks.length > 5) step6Message += `  ··· and ${upcomingTasks.length - 5} more\n`;

                if (coaching) {
                    if (coaching.overdueAdvice) step6Message += `\n${coaching.overdueAdvice}\n`;
                    if (coaching.rescheduleRecommendation) step6Message += `\n${coaching.rescheduleRecommendation}`;
                }
            }

            const cont6 = await showStep(6, "Horizon Check", step6Message);
            if (!cont6) { return; }

            // == Step 7: Plan the Week (synthesis) ==
            const coaching7 = await getCoaching(session,
                `GTD weekly review complete. System snapshot: inbox=${reviewSummary.inboxCount}, stalled projects=${reviewSummary.stalledCount}, waiting for=${reviewSummary.waitingForCount}, someday/maybe neglected=${reviewSummary.onHoldCount}, completed this week=${reviewSummary.completedThisWeek}, overdue=${reviewSummary.overdueCount}, due next 7 days=${reviewSummary.upcomingCount}. Provide top 3 weekly priorities and a system health score (1-10).`,
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

            let step7Message = `${section("Review Summary")}\n`;
            step7Message += `  · Inbox: ${reviewSummary.inboxCount} items\n`;
            step7Message += `  · Stalled projects: ${reviewSummary.stalledCount}\n`;
            step7Message += `  · Waiting for: ${reviewSummary.waitingForCount}\n`;
            step7Message += `  · Someday/Maybe neglected: ${reviewSummary.onHoldCount}\n`;
            step7Message += `  · Completed this week: ${reviewSummary.completedThisWeek}\n`;
            step7Message += `  · Overdue: ${reviewSummary.overdueCount}\n`;
            step7Message += `  · Due next 7 days: ${reviewSummary.upcomingCount}\n\n`;

            if (coaching7) {
                const priorities = Array.isArray(coaching7.weeklyPriorities) ? coaching7.weeklyPriorities : [];
                if (priorities.length > 0) {
                    step7Message += `${section("Top Priorities This Week")}\n`;
                    priorities.forEach((p, i) => step7Message += `${i + 1}. ${p}\n`);
                    step7Message += "\n";
                }
                if (coaching7.systemHealthScore) {
                    step7Message += `${section("System Health")}\n${coaching7.systemHealthScore}\n\n`;
                }
                if (coaching7.keyInsight) {
                    step7Message += `${coaching7.keyInsight}`;
                }
            }

            if (!hasCachedPrefs) {
                step7Message += `\n\nTip: Run Attache: System Setup to cache your system map for richer reviews.`;
            }

            const finalAlert = new Alert("Attache: Weekly Review", step7Message);
            finalAlert.addOption("Copy Summary");
            finalAlert.addOption("Done");
            const finalChoice = await finalAlert.show();

            if (finalChoice === 0) {
                Pasteboard.general.string = step7Message;
            }

        } catch (error) {
            console.error("Weekly Review error:", error);
            const errorAlert = new Alert("Weekly Review Error",
                `Review failed: ${error.message}`
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
