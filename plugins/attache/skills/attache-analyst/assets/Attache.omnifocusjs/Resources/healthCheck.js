/**
 * Health Check — diagnostic snapshot of GTD-system health, surfacing
 * each unhealthy indicator as an actionable card with a recommended fix.
 *
 * This is the [H] action from #186 — the "system health" landing page
 * that names the right action to fix each issue. Today's discoverSystem
 * produces a health SCORE but buries it in a discovery report;
 * healthCheck pulls the diagnostic out as a standalone, fast snapshot.
 *
 * Indicators (per gtd-coach "System Health Indicators"):
 *   - Inbox accumulating          → recommends Process Inbox
 *   - Stalled active projects     → recommends Weekly Review (Step 2)
 *   - Overdue accumulating        → recommends Process Inbox / Project Health
 *   - Vague task names            → recommends Clarify Tasks (selection)
 *   - Projects due for review     → recommends Weekly Review
 *   - System Map missing or stale → recommends Setup / refresh
 *
 * v1 design: report-only. Buttons on the Alert can't reliably launch other
 * actions from within the bundle (no documented in-bundle action-invocation
 * API; PlugIn.find()-based launches are a generated-plugin pattern, not an
 * in-bundle one). Each card NAMES the action the user should invoke from
 * the Automation menu. Auto-launch can layer in once a URL-scheme or
 * actions-array pattern is established (deferred for now).
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - No Foundation Models dependency — pure rule-based diagnostics
 * - System Map is OPTIONAL (its absence is itself one of the health
 *   indicators); all other signals work without it
 */

(() => {
    const SYSTEM_MAP_TASK_NAME = "Attache System Map";
    const EXPECTED_SCHEMA_VERSION = 1;

    // Thresholds — collected here so future calibration is single-edit.
    const INBOX_HEALTHY_MAX = 10;
    const OVERDUE_HEALTHY_MAX = 4;        // > 4 is "accumulating"
    const VAGUE_PCT_HEALTHY_MAX = 20;     // > 20% of active tasks with clarity < 50
    const VAGUE_SCORE_THRESHOLD = 50;     // per ofoCore.assessClarity (0-100)
    const VAGUE_SAMPLE_SIZE = 100;        // bottom-N tasks pulled from assessClarity
    const STALLED_DAYS = 14;              // matches ofoCore.stalledProjects default
    const MAP_MAX_AGE_DAYS = 30;          // matches dailyReview drift threshold (D7.4)

    const action = new PlugIn.Action(async function(selection, sender) {
        try {
            const ofoCore = this.plugIn.library("ofoCore");

            const cards = [];
            let healthyCount = 0;
            let unhealthyCount = 0;

            // ──────── Inbox ────────
            const stats = ofoCore.getStats({});
            if (stats.success) {
                const inboxCount = stats.inbox || 0;
                if (inboxCount > INBOX_HEALTHY_MAX) {
                    cards.push(card(
                        "⚠️",
                        "Inbox accumulating",
                        `${inboxCount} item${inboxCount === 1 ? '' : 's'} in inbox (healthy ≤${INBOX_HEALTHY_MAX}).`,
                        "Run Attache → Process Inbox to walk each item with the GTD clarify decision tree."
                    ));
                    unhealthyCount++;
                } else {
                    healthyCount++;
                }

                // ──────── Overdue ────────
                const overdueCount = stats.overdue || 0;
                if (overdueCount > OVERDUE_HEALTHY_MAX) {
                    cards.push(card(
                        "⚠️",
                        "Overdue accumulating",
                        `${overdueCount} overdue task${overdueCount === 1 ? '' : 's'} (healthy ≤${OVERDUE_HEALTHY_MAX}).`,
                        "Triage in OmniFocus (or run Attache → Process Inbox if many are in inbox). Reschedule, drop, or delegate."
                    ));
                    unhealthyCount++;
                } else {
                    healthyCount++;
                }

                // ──────── Review-overdue projects ────────
                const reviewOverdue = stats.reviewOverdue || 0;
                if (reviewOverdue > 0) {
                    cards.push(card(
                        "⚠️",
                        "Projects due for review",
                        `${reviewOverdue} project${reviewOverdue === 1 ? '' : 's'} past their review date.`,
                        "Run Attache → Weekly Review to walk through the projects sweep."
                    ));
                    unhealthyCount++;
                } else {
                    healthyCount++;
                }
            } else {
                cards.push(card(
                    "❓",
                    "Inbox / overdue stats unavailable",
                    stats.error || "ofoCore.getStats returned no data.",
                    "Restart OmniFocus or run Attache → Setup. If the issue persists, file an issue."
                ));
            }

            // ──────── Stalled active projects ────────
            const stalled = ofoCore.stalledProjects({ days: STALLED_DAYS });
            if (stalled.success) {
                const stalledCount = (stalled.projects || []).length;
                if (stalledCount > 0) {
                    cards.push(card(
                        "⚠️",
                        "Stalled active projects",
                        `${stalledCount} active project${stalledCount === 1 ? '' : 's'} have no next action or haven't been touched in ${STALLED_DAYS}+ days.`,
                        "Run Attache → Weekly Review (Step 2 sweeps stalled projects with per-item recommendations)."
                    ));
                    unhealthyCount++;
                } else {
                    healthyCount++;
                }
            } else {
                cards.push(card(
                    "❓",
                    "Stalled-projects check failed",
                    stalled.error || "ofoCore.stalledProjects returned no data.",
                    "Restart OmniFocus or run Attache → Setup."
                ));
            }

            // ──────── Vague task names ────────
            // assessClarity returns the bottom-N tasks by clarity score (0-100).
            // We pull a generous sample and count how many fall below the
            // "vague" threshold; the percentage is over the assessable sample,
            // which gives a stable signal even when activeTasks is large.
            const clarity = ofoCore.assessClarity({ limit: VAGUE_SAMPLE_SIZE });
            if (clarity.success && Array.isArray(clarity.tasks)) {
                const sample = clarity.tasks.length;
                if (sample > 0) {
                    const vague = clarity.tasks.filter(t => t.score < VAGUE_SCORE_THRESHOLD).length;
                    const pct = Math.round((vague / sample) * 100);
                    if (pct > VAGUE_PCT_HEALTHY_MAX) {
                        cards.push(card(
                            "⚠️",
                            "Vague task names",
                            `${pct}% of sampled tasks have clarity score <${VAGUE_SCORE_THRESHOLD} (healthy ≤${VAGUE_PCT_HEALTHY_MAX}%). Sample size: ${sample}.`,
                            "Select the most-vague tasks in OmniFocus, then run Attache → Clarify Tasks for AI-suggested rewrites (with apply-path)."
                        ));
                        unhealthyCount++;
                    } else {
                        healthyCount++;
                    }
                }
            }
            // assessClarity errors aren't fatal — we just omit the card.

            // ──────── System Map presence + age ────────
            const mapStatus = checkSystemMap();
            if (mapStatus.unhealthy) {
                cards.push(card("⚠️", mapStatus.title, mapStatus.finding, mapStatus.recommendation));
                unhealthyCount++;
            } else {
                healthyCount++;
            }

            // ──────── Compose report ────────
            const totalIndicators = healthyCount + unhealthyCount;
            const headerLines = [
                "GTD System Health Snapshot",
                new Date().toLocaleString(),
                `${healthyCount}/${totalIndicators} indicators healthy · ${unhealthyCount} need${unhealthyCount === 1 ? 's' : ''} attention`,
                ""
            ];

            let report;
            if (unhealthyCount === 0) {
                report = headerLines.join("\n") + "✅ All checked indicators healthy. Nothing to do — keep the cadence going.";
            } else {
                report = headerLines.join("\n") + cards.join("\n\n");
            }

            const alert = new Alert("Health Check", report);
            alert.addOption("Copy to Clipboard");
            alert.addOption("Done");
            const choice = await alert.show();
            if (choice === 0) {
                Pasteboard.general.string = report;
            }

        } catch (err) {
            const errAlert = new Alert(
                err && err.name ? err.name : "Health Check Error",
                err && err.message ? err.message : String(err)
            );
            errAlert.addOption("OK");
            await errAlert.show();
            console.error("healthCheck:", err);
        }
    });

    // ──────── Helpers ────────

    /**
     * Format a single indicator card with emoji, title, finding, and
     * recommendation. Multi-line string — newlines separate the sections so
     * the alert renders them as a coherent block.
     */
    function card(emoji, title, finding, recommendation) {
        return `${emoji} ${title}\n   ${finding}\n   → ${recommendation}`;
    }

    /**
     * Check the System Map's presence and age. Returns
     *   { unhealthy: false }                                  — present and fresh
     *   { unhealthy: true, title, finding, recommendation }   — issue to surface
     *
     * Schema-version mismatch is included here (same severity as "missing")
     * since downstream actions that depend on conventions will fail either
     * way. The recommendation always names Setup / refresh as the fix.
     */
    function checkSystemMap() {
        const candidates = flattenedTasks.filter(t => t.name === SYSTEM_MAP_TASK_NAME);
        if (candidates.length === 0) {
            return {
                unhealthy: true,
                title: "System Map missing",
                finding: "No \"Attache System Map\" task found. Convention-aware actions (Quick Organize, Daily Review coaching) will use generic defaults or block.",
                recommendation: "Run Attache → Setup to discover your OmniFocus organization (or `ofo system-map --refresh` from the CLI)."
            };
        }
        const smTask = candidates[0];
        let sm;
        try {
            sm = JSON.parse(smTask.note || "{}");
        } catch (e) {
            return {
                unhealthy: true,
                title: "System Map note is corrupt",
                finding: "The Attache System Map task's note isn't valid JSON.",
                recommendation: "Run Attache → Setup (or `ofo system-map --refresh`) to regenerate."
            };
        }
        if (typeof sm.schemaVersion !== "number") {
            return {
                unhealthy: true,
                title: "System Map predates schema versioning",
                finding: "Cached map has no schemaVersion field — produced by an older Attache.",
                recommendation: "Run Attache → Setup to upgrade the map to the current schema."
            };
        }
        if (sm.schemaVersion < EXPECTED_SCHEMA_VERSION) {
            return {
                unhealthy: true,
                title: "System Map schema is stale",
                finding: `Cached map is v${sm.schemaVersion}; current actions expect v${EXPECTED_SCHEMA_VERSION}.`,
                recommendation: "Run Attache → Setup to refresh against the current schema."
            };
        }
        if (sm.generatedAt) {
            const ageMs = Date.now() - Date.parse(sm.generatedAt);
            const ageDays = Math.floor(ageMs / 86400000);
            if (ageDays > MAP_MAX_AGE_DAYS) {
                return {
                    unhealthy: true,
                    title: "System Map is stale",
                    finding: `Cached map is ${ageDays} days old (threshold ${MAP_MAX_AGE_DAYS}d). Conventions may have drifted.`,
                    recommendation: "Run Attache → Setup (or `ofo system-map --drift-check` for details before refreshing)."
                };
            }
        }
        return { unhealthy: false };
    }

    // Always available — no FM required
    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
