/**
 * Monthly Review — GTD Horizon 2 (Areas of Focus) walk-through.
 *
 * Iterates folders inferred as `area` in the System Map and asks per
 * area: still active? healthy? needs attention? Coaches with Foundation
 * Models for each area. Surfaces an at-a-glance count of monthly-cadence
 * projects whose nextReviewDate is overdue.
 *
 * This is the Horizon-2 piece of the [R] theme in #186 — the monthly
 * cadence sits between daily/weekly reviews (operational) and
 * quarterly/annual horizons (goals/vision/purpose).
 *
 * SYSTEM MAP DEPENDENCY
 *
 * - sm.structure.topLevelFolders[] (filter: inferredType === 'area')
 *   → the Areas of Focus to walk
 *
 * Hard-blocks on missing/stale map (without it the action has no list
 * of areas to walk). Recovery path: run Setup / `ofo system-map --refresh`.
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - macOS 26+ (Apple Foundation Models for coaching)
 * - Attache System Map present and current
 */

(() => {
    const SYSTEM_MAP_TASK_NAME = "Attache System Map";
    const EXPECTED_SCHEMA_VERSION = 1;

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
            // === System Map pre-flight ===
            const smLoad = loadSystemMap();
            if (!smLoad.ok) {
                const alert = new Alert(smLoad.title, smLoad.message);
                alert.addOption("OK");
                await alert.show();
                return;
            }
            const sm = smLoad.sm;

            // === Collect Areas ===
            const areas = collectAreas(sm);
            if (areas.length === 0) {
                const alert = new Alert(
                    "Monthly Review",
                    "No top-level folders are inferred as Areas of Focus in your System Map. Open a folder you treat as an Area in OmniFocus (or rename it suggestively, e.g. \"Work\" / \"Health\" / \"Family\"), then run Setup again to refresh inferences."
                );
                alert.addOption("OK");
                await alert.show();
                return;
            }

            // === Monthly-cadence projects overdue at-a-glance ===
            const overdueMonthly = collectMonthlyReviewOverdue();

            // === Intro step ===
            const introMessage = buildIntroMessage(areas, overdueMonthly);
            const cont0 = await showStep(0, "Monthly Review — Areas of Focus", introMessage);
            if (!cont0) return;

            // === FM session ===
            const session = fmUtils.createSession(
                "You are a GTD productivity coach helping the user review their Areas of Focus " +
                "(Horizon 2). Be concise, direct, and focused on whether each area is healthy, " +
                "needs attention, or should be retired. Use GTD vocabulary."
            );

            // === Per-area coaching loop ===
            let reviewedCount = 0;
            for (let i = 0; i < areas.length; i++) {
                const area = areas[i];
                const message = await buildAreaMessage(area, session, overdueMonthly);
                const cont = await showStep(
                    i + 1,
                    `Area ${i + 1}/${areas.length}: ${area.name}`,
                    message
                );
                if (!cont) break;
                reviewedCount++;
            }

            // === Persist last-run timestamp ===
            // Written only when the user completes the per-area walk (after
            // the for-loop above) — not at action start. Cancelling mid-walk
            // doesn't fool the cadence-badge system into thinking the
            // review happened. Read by dailyReview / weeklyReview to surface
            // a "🗓 Time for a monthly review" badge when stale (>35d).
            try {
                new Preferences("com.totallytools.omnifocus.attache")
                    .write("lastReviewed_monthly", new Date().toISOString());
            } catch (e) {
                console.error("monthlyReview lastReviewed write:", e);
            }

            // === Closing step ===
            const closingLines = [
                section("Monthly Review Complete"),
                "",
                `Areas reviewed: ${reviewedCount}/${areas.length}`,
                ""
            ];
            if (overdueMonthly.length > 0) {
                closingLines.push("Reminder: " + overdueMonthly.length + " monthly-cadence project" +
                    (overdueMonthly.length === 1 ? "" : "s") +
                    " still overdue for review. Open OmniFocus's Forecast (or Review perspective) to walk them.");
                closingLines.push("");
            }
            closingLines.push("Run again next month — the Areas of Focus level deserves a slower cadence than daily/weekly.");

            const closingAlert = new Alert("Monthly Review", closingLines.join("\n"));
            closingAlert.addOption("Copy to Clipboard");
            closingAlert.addOption("Done");
            const closingChoice = await closingAlert.show();
            if (closingChoice === 0) {
                Pasteboard.general.string = closingLines.join("\n");
            }

        } catch (err) {
            const errAlert = new Alert(
                err && err.name ? err.name : "Monthly Review Error",
                err && err.message ? err.message : String(err)
            );
            errAlert.addOption("OK");
            await errAlert.show();
            console.error("monthlyReview:", err);
        }
    });

    // ──────── System Map ────────

    /**
     * Hard-load the System Map per the doctrine. Without it, monthlyReview
     * has no Areas list — no graceful degradation, only "run Setup."
     */
    function loadSystemMap() {
        const candidates = flattenedTasks.filter(t => t.name === SYSTEM_MAP_TASK_NAME);
        if (candidates.length === 0) {
            return {
                ok: false,
                title: "System Map Missing",
                message: "Monthly Review needs the System Map to find your Areas of Focus. Run Attache → Setup (or `ofo system-map --refresh`) first."
            };
        }
        let sm;
        try {
            sm = JSON.parse(candidates[0].note || "{}");
        } catch (e) {
            return {
                ok: false,
                title: "System Map Corrupt",
                message: "Run Attache → Setup (or `ofo system-map --refresh`) to regenerate."
            };
        }
        if (typeof sm.schemaVersion !== "number") {
            return {
                ok: false,
                title: "System Map Predates Versioning",
                message: "Run Attache → Setup to upgrade the map to the current schema."
            };
        }
        if (sm.schemaVersion < EXPECTED_SCHEMA_VERSION) {
            return {
                ok: false,
                title: "System Map Schema Stale",
                message: `Cached map is v${sm.schemaVersion}; Monthly Review needs v${EXPECTED_SCHEMA_VERSION}. Run Attache → Setup.`
            };
        }
        return { ok: true, sm: sm };
    }

    function collectAreas(sm) {
        const tlf = sm && sm.structure && sm.structure.topLevelFolders;
        if (!Array.isArray(tlf)) return [];
        return tlf
            .filter(f => f && f.inferredType === "area")
            .map(f => ({
                name: f.name,
                projectCount: f.projectCount || 0,
                activeProjectCount: f.activeProjectCount || 0,
                aiInferredType: f.aiInferredType,
                aiReasoning: f.aiReasoning
            }));
    }

    function collectMonthlyReviewOverdue() {
        const now = new Date();
        const overdue = [];
        flattenedProjects.forEach(p => {
            if (p.status !== Project.Status.Active && p.status !== Project.Status.OnHold) return;
            if (!p.reviewInterval) return;
            const unit = String(p.reviewInterval.unit).toLowerCase();
            if (unit.indexOf("month") === -1) return; // monthly-cadence only
            if (!p.nextReviewDate || p.nextReviewDate > now) return;
            overdue.push({
                name: p.name,
                folder: p.parentFolder ? p.parentFolder.name : null,
                nextReviewDate: p.nextReviewDate
            });
        });
        return overdue;
    }

    // ──────── Step formatting ────────

    function buildIntroMessage(areas, overdueMonthly) {
        const lines = [];
        lines.push(section("Areas of Focus"));
        lines.push("");
        lines.push(`${areas.length} top-level folder${areas.length === 1 ? "" : "s"} inferred as Areas of Focus:`);
        lines.push("");
        areas.forEach(a => {
            lines.push(`  · ${a.name} — ${a.activeProjectCount} active project${a.activeProjectCount === 1 ? "" : "s"} of ${a.projectCount} total`);
        });
        lines.push("");
        if (overdueMonthly.length > 0) {
            lines.push(`⏰ ${overdueMonthly.length} monthly-cadence project${overdueMonthly.length === 1 ? "" : "s"} overdue for review.`);
            lines.push("");
        }
        lines.push("Continue to walk each Area with AI coaching.");
        return lines.join("\n");
    }

    async function buildAreaMessage(area, session, overdueMonthly) {
        const lines = [];
        lines.push(section(area.name));
        lines.push("");
        lines.push(`Active projects: ${area.activeProjectCount} of ${area.projectCount} total`);

        // Per-area monthly-overdue subset
        const areaOverdue = overdueMonthly.filter(p => p.folder === area.name);
        if (areaOverdue.length > 0) {
            lines.push(`Monthly-cadence overdue here: ${areaOverdue.length}`);
        }
        lines.push("");

        // FM coaching
        const coaching = await getCoaching(session,
            `Area of Focus: "${area.name}". ${area.activeProjectCount} active projects (of ${area.projectCount} total). ` +
            (areaOverdue.length > 0 ? `${areaOverdue.length} monthly-cadence projects overdue. ` : "") +
            `Coach: is this Area healthy, needs attention, or should it be retired? Be specific.`,
            LanguageModel.Schema.fromJSON({
                name: "area-coaching",
                properties: [
                    {
                        name: "health",
                        description: "One of: healthy / needs-attention / retire-candidate"
                    },
                    {
                        name: "observation",
                        description: "One-sentence observation about this Area's state"
                    },
                    {
                        name: "recommendation",
                        description: "One concrete recommendation (sentence, action-oriented)"
                    }
                ]
            })
        );

        if (coaching) {
            if (coaching.health) lines.push(`Health: ${coaching.health}`);
            if (coaching.observation) lines.push(`Observation: ${coaching.observation}`);
            if (coaching.recommendation) lines.push(`Recommendation: ${coaching.recommendation}`);
        } else {
            lines.push("(AI coaching unavailable for this area — review manually.)");
        }
        return lines.join("\n");
    }

    // ──────── FM helpers (mirrors weeklyReview / dailyReview patterns) ────────

    async function getCoaching(session, prompt, schema) {
        try {
            const opts = new LanguageModel.GenerationOptions();
            opts.maximumResponseTokens = 250;
            const response = await session.respondWithSchema(prompt, schema, opts);
            return JSON.parse(response);
        } catch (e) {
            console.error("monthlyReview coaching:", e);
            return null;
        }
    }

    async function showStep(stepNum, title, message) {
        const alert = new Alert(title, message);
        alert.addOption("Continue");
        alert.addOption("Stop Review");
        const choice = await alert.show();
        return choice === 0;
    }

    // Always available — requires FM at runtime, validated above
    action.validate = function(selection, sender) {
        return Device.current.operatingSystemVersion.atLeast(new Version("26"));
    };

    return action;
})();
