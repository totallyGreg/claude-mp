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
        return `── ${title}`;
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
            const core = this.plugIn.library("ofoCore");
            const metrics = this.plugIn.library("taskMetrics");

            // D7.4 — System Map drift check (non-blocking).
            // Surfaces a soft warning prepended to the review output if the
            // cached map is missing, corrupt, schema-stale, or older than
            // 30 days. Daily Review still proceeds — drift is information,
            // not failure. Full drift signals: ofo system-map --drift-check.
            const SYSTEM_MAP_TASK_NAME = "Attache System Map";
            const EXPECTED_SCHEMA_VERSION = 1;
            const MAX_AGE_DAYS = 30;
            let systemMapDriftWarning = "";
            try {
                const smTasks = flattenedTasks.filter(t => t.name === SYSTEM_MAP_TASK_NAME);
                if (smTasks.length === 0) {
                    systemMapDriftWarning = "⚠️ System Map not found — coaching will use generic GTD terms. Run: `ofo system-map --refresh`";
                } else {
                    const sm = JSON.parse(smTasks[0].note || "{}");
                    if (typeof sm.schemaVersion !== "number") {
                        systemMapDriftWarning = "⚠️ System Map predates schema versioning. Run: `ofo system-map --refresh`";
                    } else if (sm.schemaVersion < EXPECTED_SCHEMA_VERSION) {
                        systemMapDriftWarning = `⚠️ System Map schema v${sm.schemaVersion} is stale (expected v${EXPECTED_SCHEMA_VERSION}). Run: \`ofo system-map --refresh\``;
                    } else if (sm.generatedAt) {
                        const ageDays = Math.floor((Date.now() - Date.parse(sm.generatedAt)) / 86400000);
                        if (ageDays > MAX_AGE_DAYS) {
                            systemMapDriftWarning = `⚠️ System Map is ${ageDays} days old (threshold ${MAX_AGE_DAYS}d). Conventions may have drifted. Run: \`ofo system-map --drift-check\` for details.`;
                        }
                    }
                }
            } catch (_) {
                systemMapDriftWarning = "⚠️ System Map note is corrupt. Run: `ofo system-map --refresh`";
            }

            // Single-pass collection for all metrics
            const all = metrics.collectAllMetrics(core);

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
                    const days = Math.floor((+new Date() - +new Date(t.dueDate)) / (1000 * 60 * 60 * 24));
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

            // D7.4 — Prepend System Map drift warning (non-blocking; informational only)
            if (systemMapDriftWarning) {
                message += systemMapDriftWarning + "\n\n";
                md += `> ${systemMapDriftWarning}\n\n`;
            }

            // Cadence badges — surface "time for a monthly/horizons review"
            // when the user is overdue per the recommended cadence. Read
            // timestamps written by monthlyReview / horizonsReview at their
            // closing-step completion. Never blocks the review; pure nudge.
            const cadenceBadges = getCadenceBadges();
            if (cadenceBadges.length > 0) {
                cadenceBadges.forEach(badge => {
                    message += badge + "\n";
                    md += `> ${badge}\n`;
                });
                message += "\n";
                md += "\n";
            }

            // Calendar prompt (GTD: date-specific commitments are non-negotiable anchors).
            // Plain text in the message; an "📅 Open Calendar" button below the
            // alert invokes calshow: to launch Apple Calendar to today's view.
            message += "📅 Review your calendar for today's commitments. (Open Calendar button below.)\n\n";
            md += "> 📅 Review your calendar for today's commitments.\n\n";

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

            // GTD Engage cross-link: dailyReview surfaces a static "top N
            // next actions" list, but Engage criteria (context / time /
            // energy) re-filter that list situationally. whatNow already
            // does this — cross-link rather than duplicate the form +
            // filter logic in two places (AGENTS.md design principle 3).
            message += `\n\n💡 For a context / time / energy filter on these actions, run Attache › What Now.`;
            md += `\n\n> 💡 **Engage filter:** run Attache › What Now to narrow these actions by current context, time available, and energy.`;

            if (!hasCachedPrefs) {
                message += `\n\nTip: Run Attache › Setup to cache your system map for richer reviews.`;
                md += `\n\n> **Tip:** Run Attache › Setup to cache your system map for richer reviews.`;
            }

            const resultAlert = new Alert("Daily Review", message);
            resultAlert.addOption("Copy to Clipboard");
            resultAlert.addOption("📅 Open Calendar");
            resultAlert.addOption("Done");
            const choice = await resultAlert.show();

            if (choice === 0) {
                Pasteboard.general.string = md;
            } else if (choice === 1) {
                // calshow: opens Apple Calendar to the default view (Today on
                // current day). Failure is non-fatal — log and continue.
                try {
                    URL.fromString("calshow:").open();
                } catch (e) {
                    console.error("Could not open Calendar:", e);
                }
            }

        } catch (error) {
            console.error("Daily Review error:", error);
            const errorAlert = new Alert("Daily Review Error",
                `Could not complete review: ${error.message}`
            );
            errorAlert.show();
        }
    });

    /**
     * Read the last-run timestamps for the upper-cadence reviews and return
     * any badges that should surface to the user as nudges. monthlyReview
     * threshold is 35 days (slightly longer than 4 weeks so a once-monthly
     * cadence doesn't pop a badge the moment it's overdue); horizonsReview
     * threshold is 100 days (quarterly cadence with a buffer).
     *
     * Inlined here AND in weeklyReview.js (~30 lines duplicated). Per
     * AGENTS.md design principle 3, extract to a shared library when a
     * third reader emerges (likely candidate: healthCheck's missing-
     * cadence indicators, which could grow from monthly-only to a richer
     * cadence-grid). Until then, inline is the right trade-off.
     *
     * Never throws — Preferences failures log to console and return an
     * empty badge list. Cadence nudges are informational, not blocking.
     */
    function getCadenceBadges() {
        const badges = [];
        try {
            const prefs = new Preferences("com.totallytools.omnifocus.attache");
            const monthlyRaw = prefs.readString("lastReviewed_monthly");
            if (monthlyRaw) {
                const days = Math.floor((Date.now() - Date.parse(monthlyRaw)) / 86400000);
                if (days > 35) {
                    badges.push(`🗓 Time for a monthly review — last ran ${days} days ago. Run Attache › Monthly Review.`);
                }
            } else {
                badges.push("🗓 You haven't run a monthly review yet. Try Attache › Monthly Review for an Areas-of-Focus check.");
            }
            const horizonsRaw = prefs.readString("lastReviewed_horizons");
            if (horizonsRaw) {
                const days = Math.floor((Date.now() - Date.parse(horizonsRaw)) / 86400000);
                if (days > 100) {
                    badges.push(`🌅 Time for a horizons review — last ran ${days} days ago. Run Attache › Horizons Review.`);
                }
            }
            // No "never-run" nudge for horizons — fresh installs shouldn't
            // be pushed into Horizon 3-5 work on day one.
        } catch (e) {
            console.error("dailyReview getCadenceBadges:", e);
        }
        return badges;
    }

    action.validate = function(selection, sender) {
        return Device.current.operatingSystemVersion.atLeast(new Version("26"));
    };

    return action;
})();
