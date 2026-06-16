/**
 * What Now — situational task filter for the GTD Engage phase.
 *
 * Three-question form (current context, time available, energy level)
 * narrows the user's available tasks to a focused 3-5 candidates based on
 * tag match + estimatedMinutes fit. Unlike dailyReview (a fixed-cadence
 * ritual), whatNow is intended to be invoked any time of day with the
 * user's current state — "I have 20 minutes at my computer, what should
 * I do?".
 *
 * Optional apply-path: after the filtered list, the user can pick
 * specific tasks to flag for focus right now.
 *
 * This is the Engage piece of the [R] theme in #186 — Engage is the GTD
 * phase that's currently absent from Attache (Daily Review implies a
 * top-5 list regardless of the user's actual situation).
 *
 * SYSTEM MAP DEPENDENCY
 *
 * - sm.tags.categories.contexts[] → context picker (the "where am I?")
 * - sm.tags.categories.energy[]   → energy picker (the "how am I feeling?")
 *
 * The action degrades gracefully when one or both lists are missing:
 * the picker for the missing dimension is omitted, and the form's
 * subtitle tells the user how to populate it (run Setup).
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - No Foundation Models dependency — pure rule-based filtering
 * - Attache System Map present for context/energy filtering (other
 *   filters work without it)
 */

(() => {
    const SYSTEM_MAP_TASK_NAME = "Attache System Map";
    const EXPECTED_SCHEMA_VERSION = 1;
    const RESULT_LIMIT = 5;

    const action = new PlugIn.Action(async function(selection, sender) {
        try {
            const ofoCore = this.plugIn.library("ofoCore");

            // Load System Map for context/energy tags (soft — null if missing,
            // we still allow the time-only filter so the action works on a
            // fresh install before Setup is run).
            const smInfo = loadSystemMap();
            const contextTags = smInfo.ok ? collectTagNames(smInfo.sm, "contexts") : [];
            const energyTags = smInfo.ok ? collectTagNames(smInfo.sm, "energy") : [];

            const missingNotes = smInfo.ok
                ? collectMissingTagNotes(contextTags, energyTags)
                : "System Map not loaded — context/energy filters unavailable. Run Setup to enable.";

            const formValues = await promptSituation(contextTags, energyTags, missingNotes);
            if (!formValues) return; // cancelled

            const candidates = filterTasks(formValues);
            if (candidates.length === 0) {
                const alert = new Alert(
                    "What Now",
                    "No available tasks match your situation. Try relaxing the time/context/energy constraints, or run Process Inbox / Clarify Tasks to expand your actionable set."
                );
                alert.addOption("OK");
                await alert.show();
                return;
            }

            const report = formatReport(candidates, formValues);

            // Optional apply-path: let the user flag a subset for focus.
            const alert = new Alert("What Now", report);
            alert.addOption("Copy to Clipboard");
            alert.addOption("Focus on…");
            alert.addOption("Done");
            const choice = await alert.show();

            if (choice === 0) {
                Pasteboard.general.string = report;
            } else if (choice === 1) {
                await focusOnSelected(candidates, ofoCore);
            }

        } catch (err) {
            const errAlert = new Alert(
                err && err.name ? err.name : "What Now Error",
                err && err.message ? err.message : String(err)
            );
            errAlert.addOption("OK");
            await errAlert.show();
            console.error("whatNow:", err);
        }
    });

    // ──────── System Map ────────

    /**
     * Soft-load the System Map. Unlike quickOrganize (which hard-blocks on
     * missing map because every bucket depends on conventions), whatNow can
     * still do TIME-only filtering with no map at all — only the
     * context/energy pickers depend on the map.
     */
    function loadSystemMap() {
        const candidates = flattenedTasks.filter(t => t.name === SYSTEM_MAP_TASK_NAME);
        if (candidates.length === 0) return { ok: false };
        let sm;
        try {
            sm = JSON.parse(candidates[0].note || "{}");
        } catch (e) {
            return { ok: false };
        }
        if (typeof sm.schemaVersion !== "number") return { ok: false };
        if (sm.schemaVersion < EXPECTED_SCHEMA_VERSION) return { ok: false };
        return { ok: true, sm: sm };
    }

    /**
     * Extract tag names from a named category in the System Map's
     * tags.categories block. Drops entries that no longer exist in the
     * live OF tag tree (handles user-deleted-tag-since-refresh case).
     */
    function collectTagNames(sm, categoryKey) {
        const out = [];
        const list = sm && sm.tags && sm.tags.categories && sm.tags.categories[categoryKey];
        if (!Array.isArray(list)) return out;
        list.forEach(entry => {
            const name = entry && entry.name;
            if (typeof name !== "string" || !name) return;
            if (!flattenedTags.byName(name)) return;
            out.push(name);
        });
        return out;
    }

    function collectMissingTagNotes(contextTags, energyTags) {
        const missing = [];
        if (contextTags.length === 0) missing.push("contexts");
        if (energyTags.length === 0) missing.push("energy");
        if (missing.length === 0) return "";
        return `No ${missing.join(" or ")} tags configured — run Setup to enable those filters.`;
    }

    // ──────── Situation prompt ────────

    /**
     * Three-question form. Time picker is always shown; context/energy
     * pickers only show when their tag list is non-empty (so the form
     * stays clean on fresh installs). Returns { context, timeMinutes,
     * energy } or null on cancel. context/energy are strings (tag name)
     * or "" (no filter); timeMinutes is number or 0 (no time filter).
     */
    async function promptSituation(contextTags, energyTags, missingNotes) {
        const form = new Form();

        if (contextTags.length > 0) {
            const keys = [""].concat(contextTags);
            const labels = ["(any context)"].concat(contextTags);
            // @ts-ignore — 6th arg (nullOptionTitle) is optional at runtime
            form.addField(new Form.Field.Option(
                "context", "Context (where am I?)", keys, labels, ""
            ));
        }

        // @ts-ignore — 6th arg (nullOptionTitle) is optional at runtime
        form.addField(new Form.Field.Option(
            "time",
            "Time available",
            ["15", "30", "60", "120", "0"],
            ["15 minutes", "30 minutes", "1 hour", "2 hours", "Open (no limit)"],
            "30"
        ));

        if (energyTags.length > 0) {
            const keys = [""].concat(energyTags);
            const labels = ["(any energy)"].concat(energyTags);
            // @ts-ignore — 6th arg (nullOptionTitle) is optional at runtime
            form.addField(new Form.Field.Option(
                "energy", "Energy level", keys, labels, ""
            ));
        }

        const title = missingNotes
            ? `What Now — focus on what's possible right now\n\n${missingNotes}`
            : "What Now — focus on what's possible right now";
        const result = await form.show(title, "Find");
        if (!result) return null;

        return {
            context: contextTags.length > 0 ? String(result.values["context"] || "") : "",
            timeMinutes: parseInt(String(result.values["time"] || "0"), 10) || 0,
            energy: energyTags.length > 0 ? String(result.values["energy"] || "") : ""
        };
    }

    // ──────── Filter logic ────────

    /**
     * Iterate available tasks and score each against the user's situation.
     * Returns the top RESULT_LIMIT candidates after sorting by:
     *   1. flagged first
     *   2. due date ascending (nulls last)
     *   3. estimatedMinutes ascending (nulls last — unknown estimates last
     *      so user defaults to known-fits)
     *
     * A task is INCLUDED if:
     *   - taskStatus === Available (not deferred, not blocked, not done)
     *   - context tag matches (or no context filter)
     *   - energy tag matches (or no energy filter)
     *   - estimatedMinutes <= timeMinutes (or task has no estimate, or no
     *     time filter — we don't punish unestimated tasks; user can still
     *     pick them and the report flags the missing estimate)
     */
    function filterTasks(situation) {
        const results = [];
        flattenedTasks.forEach(t => {
            if (t.completed || t.dropped) return;
            if (t.taskStatus !== Task.Status.Available) return;

            if (situation.context && !taskHasTag(t, situation.context)) return;
            if (situation.energy && !taskHasTag(t, situation.energy)) return;

            if (situation.timeMinutes > 0) {
                const est = t.estimatedMinutes;
                if (est !== null && est !== undefined && est > situation.timeMinutes) return;
            }

            results.push(t);
        });

        results.sort((a, b) => {
            if (a.flagged !== b.flagged) return a.flagged ? -1 : 1;
            const aDue = a.dueDate ? a.dueDate.getTime() : Infinity;
            const bDue = b.dueDate ? b.dueDate.getTime() : Infinity;
            if (aDue !== bDue) return aDue - bDue;
            const aEst = (a.estimatedMinutes !== null && a.estimatedMinutes !== undefined) ? a.estimatedMinutes : Infinity;
            const bEst = (b.estimatedMinutes !== null && b.estimatedMinutes !== undefined) ? b.estimatedMinutes : Infinity;
            return aEst - bEst;
        });

        return results.slice(0, RESULT_LIMIT);
    }

    function taskHasTag(task, tagName) {
        if (!tagName) return false;
        return task.tags.some(t => t.name === tagName);
    }

    // ──────── Report ────────

    function formatReport(candidates, situation) {
        const lines = [];
        lines.push("── What Can You Do Now? ──");
        const constraints = [];
        if (situation.timeMinutes > 0) constraints.push(`${situation.timeMinutes} min`);
        else constraints.push("any duration");
        if (situation.context) constraints.push(`context: ${situation.context}`);
        if (situation.energy) constraints.push(`energy: ${situation.energy}`);
        lines.push(`Situation: ${constraints.join(" · ")}`);
        lines.push("");

        candidates.forEach((t, i) => {
            const flag = t.flagged ? "* " : "  ";
            const proj = t.containingProject ? `[${t.containingProject.name}]` : "[Inbox]";
            const est = (t.estimatedMinutes !== null && t.estimatedMinutes !== undefined)
                ? `${t.estimatedMinutes}m`
                : "—";
            const due = t.dueDate
                ? ` ⏰ ${t.dueDate.toLocaleDateString()}`
                : "";
            lines.push(`${i + 1}. ${flag}${t.name} ${proj} · ${est}${due}`);
        });

        lines.push("");
        lines.push("Tap \"Focus on…\" to flag one or more of these for right-now focus.");
        return lines.join("\n");
    }

    // ──────── Optional apply: flag selected for focus ────────

    /**
     * Per-candidate Form: checkboxes for each candidate the user might
     * want to focus on. Selected ones are flagged via ofoCore.updateTask
     * (idempotent — already-flagged tasks stay flagged). This is the
     * apply-path for the Engage phase: turn "what could I do" into
     * "what AM I doing right now" with one form.
     */
    async function focusOnSelected(candidates, ofoCore) {
        const form = new Form();
        candidates.forEach((t, i) => {
            const label = t.flagged
                ? `${t.name} (already flagged)`
                : t.name;
            form.addField(new Form.Field.Checkbox(`pick_${i}`, label, false));
        });

        const result = await form.show("Focus on which tasks now?", "Flag");
        if (!result) return;

        let flagged = 0;
        let skipped = 0;
        const issues = [];

        for (let i = 0; i < candidates.length; i++) {
            const pick = !!result.values[`pick_${i}`];
            if (!pick) { skipped++; continue; }
            const t = candidates[i];
            if (t.flagged) { flagged++; continue; } // idempotent: already done

            const res = ofoCore.updateTask({ id: t.id.primaryKey, flagged: true });
            if (!res.success) {
                issues.push(`${t.name}: ${res.error || 'updateTask failed'}`);
            } else {
                flagged++;
            }
        }

        let summary = `Flagged ${flagged} task${flagged === 1 ? '' : 's'}.`;
        if (skipped > 0) summary += `\nUnchecked ${skipped}.`;
        if (issues.length > 0) summary += `\n\nIssues:\n  · ${issues.join('\n  · ')}`;
        const summaryAlert = new Alert("What Now — Focus Summary", summary);
        summaryAlert.addOption("OK");
        await summaryAlert.show();
    }

    // Always available — no FM required
    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
