/**
 * Horizons Review — GTD Horizons 3-5 (Goals / Vision / Purpose).
 *
 * Quarterly or annual cadence. Walks the user through three reflection
 * steps:
 *   - Horizon 3 (Goals)   — 1-2 year objectives
 *   - Horizon 4 (Vision)  — 3-5 year picture
 *   - Horizon 5 (Purpose) — life-arc "why"
 *
 * Each step displays the user's previously-captured value (so this is a
 * REVIEW, not a fresh-start every time), offers an FM-generated
 * reflection prompt to think against, and lets the user edit or leave
 * unchanged. Updates persist between sessions via the Preferences API
 * under a dedicated key (separate from the systemMap blob owned by
 * preferencesManager — horizons data has different lifecycle and
 * shouldn't be flushed when the System Map refreshes).
 *
 * This is the Horizons-3-through-5 piece of the [R] theme in #186 —
 * monthlyReview (commit 64c825d) covers Horizon 2 (Areas of Focus);
 * this fills out the upper horizons. Daily/Weekly/Monthly are
 * operational cadences; horizonsReview is the strategic cadence the
 * other reviews implicitly reference.
 *
 * FM is OPTIONAL — when unavailable, the action skips the reflection
 * prompts and runs as a pure review-and-update flow. The user still
 * gets value from re-reading their own horizons; FM is the multiplier.
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - Foundation Models OPTIONAL (used only for reflection prompts)
 * - No System Map dependency (horizons are user-stated, not inferred)
 */

(() => {
    const PREFS_BUNDLE = "com.totallytools.omnifocus.attache";
    const PREFS_KEY = "horizons";
    const SCHEMA_VERSION = 1;

    function section(title) {
        return `── ${title}`;
    }

    const action = new PlugIn.Action(async function(selection, sender) {
        const fmUtils = this.plugIn.library("foundationModelsUtils");
        const fmAvailable = fmUtils && fmUtils.isAvailable();

        try {
            // === Load existing horizons (or initial empty shape) ===
            const stored = readHorizons();
            const current = {
                schemaVersion: SCHEMA_VERSION,
                lastUpdated: stored.lastUpdated || null,
                purpose: typeof stored.purpose === "string" ? stored.purpose : "",
                vision: typeof stored.vision === "string" ? stored.vision : "",
                goals: typeof stored.goals === "string" ? stored.goals : ""
            };

            // === Intro ===
            const introMessage = buildIntroMessage(current, fmAvailable);
            const cont0 = await showStep("Horizons Review", introMessage);
            if (!cont0) return;

            // === FM session (optional) ===
            const session = fmAvailable
                ? fmUtils.createSession(
                    "You are a coach for strategic life-design reflection. You do NOT propose " +
                    "content for the user — they own their horizons. Your job is to ask ONE " +
                    "thought-provoking question per horizon level that helps them check " +
                    "alignment between what they've stated and what's true for them now. " +
                    "Be brief, specific, and not preachy."
                )
                : null;

            // === Per-horizon coaching loop ===
            const updated = { ...current };
            let anyChanged = false;

            const horizons = [
                {
                    key: "goals",
                    label: "Goals (Horizon 3)",
                    description: "1-2 year objectives — concrete outcomes you're aiming at",
                    placeholder: "e.g. 'Ship product X by Q3', 'Get health metrics back to baseline'"
                },
                {
                    key: "vision",
                    label: "Vision (Horizon 4)",
                    description: "3-5 year picture — what does your life look like if things go well?",
                    placeholder: "e.g. 'Running my own consultancy', 'Family settled in new city'"
                },
                {
                    key: "purpose",
                    label: "Purpose (Horizon 5)",
                    description: "Life-arc 'why' — the core values and direction underneath everything",
                    placeholder: "e.g. 'Make things that help people think more clearly'"
                }
            ];

            for (let i = 0; i < horizons.length; i++) {
                const h = horizons[i];
                const newValue = await promptHorizon(h, updated[h.key], session);
                if (newValue === null) {
                    // User stopped; preserve unsaved progress as a courtesy.
                    if (anyChanged) {
                        writeHorizons(updated);
                    }
                    return;
                }
                if (newValue !== updated[h.key]) {
                    updated[h.key] = newValue;
                    anyChanged = true;
                }
            }

            // === Persist ===
            if (anyChanged) {
                updated.lastUpdated = new Date().toISOString();
                writeHorizons(updated);
            }

            // === Persist last-run timestamp (separate from horizons blob's
            // lastUpdated, which only fires on change). Tracks "user
            // completed a horizons review" for the cadence-badge system in
            // dailyReview / weeklyReview to surface "🌅 Time for a horizons
            // review" when stale (>100d). Always written on completion —
            // a review where nothing changed still counts as a review.
            try {
                new Preferences("com.totallytools.omnifocus.attache")
                    .write("lastReviewed_horizons", new Date().toISOString());
            } catch (e) {
                console.error("horizonsReview lastReviewed write:", e);
            }

            // === Closing ===
            const closingMessage = buildClosingMessage(current, updated, anyChanged);
            const closingAlert = new Alert("Horizons Review", closingMessage);
            closingAlert.addOption("Copy to Clipboard");
            closingAlert.addOption("Done");
            const closingChoice = await closingAlert.show();
            if (closingChoice === 0) {
                Pasteboard.general.string = closingMessage;
            }

        } catch (err) {
            const errAlert = new Alert(
                err && err.name ? err.name : "Horizons Review Error",
                err && err.message ? err.message : String(err)
            );
            errAlert.addOption("OK");
            await errAlert.show();
            console.error("horizonsReview:", err);
        }
    });

    // ──────── Persistence (Preferences key separate from systemMap) ────────

    /**
     * Lazy-construct Preferences only when needed (per the warning in
     * preferencesManager.ts — constructing at IIFE top level disables
     * actions).
     */
    function getPrefs() {
        return new Preferences(PREFS_BUNDLE);
    }

    function readHorizons() {
        try {
            const raw = getPrefs().readString(PREFS_KEY);
            if (!raw) return {};
            const parsed = JSON.parse(raw);
            if (!parsed || typeof parsed !== "object") return {};
            return parsed;
        } catch (e) {
            console.error("horizonsReview readHorizons:", e);
            return {};
        }
    }

    function writeHorizons(data) {
        try {
            getPrefs().write(PREFS_KEY, JSON.stringify(data));
        } catch (e) {
            console.error("horizonsReview writeHorizons:", e);
        }
    }

    // ──────── Prompts ────────

    function buildIntroMessage(current, fmAvailable) {
        const lines = [];
        lines.push(section("Horizons Review (3-5)"));
        lines.push("");
        if (current.lastUpdated) {
            const date = new Date(current.lastUpdated);
            const days = Math.floor((Date.now() - date.getTime()) / 86400000);
            lines.push(`Last updated: ${date.toLocaleDateString()} (${days} days ago)`);
        } else {
            lines.push("First time running Horizons Review.");
        }
        lines.push("");
        lines.push("This is your quarterly (or annual) reflection on the upper GTD horizons:");
        lines.push("  · Goals  (1-2 year objectives)");
        lines.push("  · Vision (3-5 year picture)");
        lines.push("  · Purpose (life-arc 'why')");
        lines.push("");
        lines.push(fmAvailable
            ? "Each step shows what you wrote last time + a fresh reflection prompt. Edit or leave unchanged."
            : "Each step shows what you wrote last time. Edit or leave unchanged. (Foundation Models unavailable — running without reflection prompts.)");
        return lines.join("\n");
    }

    async function promptHorizon(horizon, currentValue, session) {
        const reflectionPrompt = session
            ? await getReflectionPrompt(session, horizon, currentValue)
            : null;

        const lines = [];
        lines.push(section(horizon.label));
        lines.push("");
        lines.push(horizon.description);
        lines.push("");
        if (currentValue) {
            lines.push("Last captured:");
            lines.push(`  ${currentValue}`);
            lines.push("");
        } else {
            lines.push("(not captured yet)");
            lines.push("");
        }
        if (reflectionPrompt) {
            lines.push("Reflection:");
            lines.push(`  ${reflectionPrompt}`);
            lines.push("");
        }
        lines.push(`Edit the field below (leave unchanged to keep, or clear to remove).`);

        const form = new Form();
        form.addField(new Form.Field.String(
            "value",
            horizon.label,
            currentValue || ""
        ));

        // Same defensive Form.show pattern as processInbox / quickOrganize —
        // cancel may reject rather than resolve-to-null in some builds.
        let result;
        try {
            result = await form.show(lines.join("\n"), "Save & Continue");
        } catch (e) {
            return null;
        }
        if (!result) return null;
        return String(result.values["value"] || "").trim();
    }

    async function getReflectionPrompt(session, horizon, currentValue) {
        try {
            const opts = new LanguageModel.GenerationOptions();
            opts.maximumResponseTokens = 120;
            const prompt = currentValue
                ? `For the GTD horizon "${horizon.label}" (${horizon.description}), the user previously captured: "${currentValue}". Ask ONE specific question (1 sentence) to help them check if this is still true and aligned with their current life. Don't propose new content; help them examine what's there.`
                : `For the GTD horizon "${horizon.label}" (${horizon.description}), the user hasn't captured anything yet. Ask ONE concrete question (1 sentence) to help them get started — focused on noticing what's already true, not inventing aspirations.`;
            const response = await session.respondWithSchema(
                prompt,
                LanguageModel.Schema.fromJSON({
                    name: "reflection-prompt",
                    properties: [
                        { name: "question", description: "One thoughtful reflection question (single sentence)" }
                    ]
                }),
                opts
            );
            const parsed = JSON.parse(response);
            return parsed && parsed.question ? String(parsed.question).trim() : null;
        } catch (e) {
            console.error("horizonsReview reflectionPrompt:", e);
            return null;
        }
    }

    function buildClosingMessage(before, after, anyChanged) {
        const lines = [];
        lines.push(section("Horizons Review Complete"));
        lines.push("");
        if (!anyChanged) {
            lines.push("No changes saved. Your horizons remain as previously captured.");
            lines.push("");
        } else {
            lines.push(`Updated ${new Date(after.lastUpdated).toLocaleString()}.`);
            lines.push("");
            ["goals", "vision", "purpose"].forEach(key => {
                const wasBlank = !before[key];
                const isBlank = !after[key];
                const changed = before[key] !== after[key];
                if (!changed) return;
                const label = key.charAt(0).toUpperCase() + key.slice(1);
                if (wasBlank && !isBlank) {
                    lines.push(`  · ${label}: captured for the first time`);
                } else if (!wasBlank && isBlank) {
                    lines.push(`  · ${label}: cleared`);
                } else {
                    lines.push(`  · ${label}: updated`);
                }
            });
            lines.push("");
        }
        if (after.purpose || after.vision || after.goals) {
            lines.push("Current state:");
            if (after.goals)   lines.push(`  Goals:   ${after.goals}`);
            if (after.vision)  lines.push(`  Vision:  ${after.vision}`);
            if (after.purpose) lines.push(`  Purpose: ${after.purpose}`);
            lines.push("");
        }
        lines.push("Suggested cadence: revisit quarterly, or whenever a major life event reshapes the picture.");
        return lines.join("\n");
    }

    async function showStep(title, message) {
        const alert = new Alert(title, message);
        alert.addOption("Continue");
        alert.addOption("Stop Review");
        const choice = await alert.show();
        return choice === 0;
    }

    // Always available — no FM requirement (FM is optional enhancement only)
    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
