/**
 * Stale Routine Recovery — diagnose and recover repeating tasks that
 * have fallen >2 weeks past their due date.
 *
 * Repeating tasks ("routines") accumulate overdue instances when life
 * disrupts the cadence (illness, travel, focus shift). OmniFocus's
 * default behavior is to keep advancing the due date forward instance
 * by instance, producing a phantom "I'm always behind" backlog. The
 * GTD-correct recovery is to either:
 *
 *   - Complete the current instance (if the activity actually happened)
 *   - Drop the whole task (cancel the routine)
 *   - Skip overdue instances and resume from today (requires the OF
 *     Catch Up setting — NOT toggleable via Omni Automation)
 *
 * This action surfaces every stale routine, computes the
 * recommended recovery per the decision tree codified in
 * `commands/ofo-overdue.md`, and walks the user through each with a
 * per-item Form. Catch Up can't be flipped via the API; for that case
 * we surface a step-by-step walkthrough the user follows in OF's UI.
 *
 * This is the [T] action from #186 — closes the Repeating/Ticklers
 * theme (minus the at-creation Routine-vs-Tickler distinction, which
 * depends on a quickOrganize-style task-creation flow that doesn't
 * exist yet).
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - No Foundation Models dependency (pure rule-based diagnostic)
 */

(() => {
    const STALE_THRESHOLD_DAYS = 14;
    const REGULARLY_DROP_THRESHOLD_DAYS = 7; // decision tree boundary

    const action = new PlugIn.Action(async function(selection, sender) {
        try {
            const ofoCore = this.plugIn.library("ofoCore");

            // === Scan for stale routines ===
            const stale = collectStaleRoutines();
            if (stale.length === 0) {
                const alert = new Alert(
                    "Stale Routine Recovery",
                    `No stale routines found (no repeating tasks more than ${STALE_THRESHOLD_DAYS} days overdue).`
                );
                alert.addOption("OK");
                await alert.show();
                return;
            }

            // === Intro: scope + breakdown by recommendation ===
            const breakdown = summarizeBreakdown(stale);
            const introMessage = buildIntroMessage(stale, breakdown);
            const introAlert = new Alert("Stale Routine Recovery", introMessage);
            introAlert.addOption("Walk through items");
            introAlert.addOption("Cancel");
            const introChoice = await introAlert.show();
            if (introChoice !== 0) return;

            // === Per-item walk ===
            let recovered = 0;
            let skipped = 0;
            let instructionsShown = 0;
            let stopped = false;
            const issues = [];

            for (let i = 0; i < stale.length; i++) {
                const entry = stale[i];
                const decision = await promptForItem(entry, i + 1, stale.length);
                if (decision.stopped) { stopped = true; break; }

                switch (decision.action) {
                    case "skip":
                        skipped++;
                        break;
                    case "complete": {
                        const res = ofoCore.completeTask({ id: entry.task.id.primaryKey });
                        if (res && !res.success) {
                            issues.push(`${entry.task.name}: ${res.error || 'completeTask failed'}`);
                        } else {
                            recovered++;
                        }
                        break;
                    }
                    case "drop": {
                        const res = ofoCore.dropTask({ id: entry.task.id.primaryKey });
                        if (res && !res.success) {
                            issues.push(`${entry.task.name}: ${res.error || 'dropTask failed'}`);
                        } else {
                            recovered++;
                        }
                        break;
                    }
                    case "instructions":
                        await showCatchUpInstructions(entry);
                        instructionsShown++;
                        break;
                    default:
                        skipped++;
                }
            }

            // === Summary ===
            let summary = `Recovered ${recovered} routine${recovered === 1 ? '' : 's'} via dispatch.`;
            if (instructionsShown > 0) {
                summary += `\nShowed Catch Up walkthrough for ${instructionsShown} (manual fix in OmniFocus).`;
            }
            if (skipped > 0) summary += `\nSkipped ${skipped}.`;
            if (stopped) summary += `\nStopped before reviewing all ${stale.length} items.`;
            if (issues.length > 0) summary += `\n\nIssues:\n  · ${issues.join('\n  · ')}`;

            const summaryAlert = new Alert("Stale Routine Recovery — Summary", summary);
            summaryAlert.addOption("OK");
            await summaryAlert.show();

        } catch (err) {
            const errAlert = new Alert(
                err && err.name ? err.name : "Stale Routine Recovery Error",
                err && err.message ? err.message : String(err)
            );
            errAlert.addOption("OK");
            await errAlert.show();
            console.error("staleRoutineRecovery:", err);
        }
    });

    // ──────── Scan ────────

    /**
     * Walk flattenedTasks looking for repeating tasks that are >N days past
     * their due date. Returns enriched entries with the recommended recovery
     * action per the decision tree (codified in commands/ofo-overdue.md).
     *
     * Sorted by daysOverdue descending so the most-stale items surface first.
     */
    function collectStaleRoutines() {
        const now = new Date();
        const cutoff = new Date(now.getTime() - STALE_THRESHOLD_DAYS * 86400000);
        const stale = [];

        flattenedTasks.forEach(t => {
            if (t.completed || t.dropped) return;
            if (!t.repetitionRule) return;
            if (!t.dueDate || t.dueDate >= cutoff) return;

            const daysOverdue = Math.floor((now.getTime() - t.dueDate.getTime()) / 86400000);
            const scheduleType = readScheduleType(t);
            const catchUp = readCatchUp(t);
            const recommendation = computeRecommendation(catchUp, scheduleType, daysOverdue);

            stale.push({
                task: t,
                daysOverdue: daysOverdue,
                scheduleType: scheduleType,
                catchUp: catchUp,
                recommendation: recommendation
            });
        });

        stale.sort((a, b) => b.daysOverdue - a.daysOverdue);
        return stale;
    }

    /** Best-effort read of repetitionScheduleType — string-cast for cross-version safety. */
    function readScheduleType(task) {
        try {
            const raw = task.repetitionRule && task.repetitionRule.scheduleType;
            return raw ? String(raw) : null;
        } catch (e) {
            return null;
        }
    }

    /** Best-effort read of repetitionCatchUp. */
    function readCatchUp(task) {
        try {
            const raw = task.repetitionRule && task.repetitionRule.catchUp;
            return typeof raw === "boolean" ? raw : null;
        } catch (e) {
            return null;
        }
    }

    /**
     * Decision tree from commands/ofo-overdue.md:
     *   - catchUp === true                    → "drop-reset"  (drop will reset cadence)
     *   - scheduleType === "FromCompletion"   → "complete-or-drop" (depends on what happened)
     *   - scheduleType === "Regularly", >7d   → "drop-forward" (large gap; reset)
     *   - scheduleType === "Regularly", ≤7d   → "complete-or-drop"
     *   - else                                → "complete-or-drop" (safe default)
     *
     * Returns an object with `key` (used to pre-select picker) and `text`
     * (shown to the user). Picker key maps to the user's actual action;
     * "complete-or-drop" pre-selects "skip" (let the user decide between
     * complete and drop based on whether the activity actually happened).
     */
    function computeRecommendation(catchUp, scheduleType, daysOverdue) {
        if (catchUp === true) {
            return {
                key: "drop",
                text: "Drop to reset (Catch Up is ON — drop resets the cadence cleanly)"
            };
        }
        if (scheduleType === "FromCompletion") {
            return {
                key: "skip",
                text: "Decide: complete if the activity actually happened; drop if skipped"
            };
        }
        if (scheduleType === "Regularly" && daysOverdue > REGULARLY_DROP_THRESHOLD_DAYS) {
            return {
                key: "drop",
                text: `Drop to move forward (Regularly-scheduled, ${daysOverdue}d overdue — too far behind to recover instance-by-instance)`
            };
        }
        if (scheduleType === "Regularly") {
            return {
                key: "skip",
                text: "Decide: complete if the activity actually happened; drop if skipped (Regularly-scheduled, within 7d)"
            };
        }
        return {
            key: "skip",
            text: "Decide: complete if the activity actually happened; drop if skipped (schedule type unknown)"
        };
    }

    // ──────── Display ────────

    function summarizeBreakdown(stale) {
        const counts = { complete: 0, drop: 0, skip: 0 };
        stale.forEach(entry => {
            const k = entry.recommendation.key;
            counts[k] = (counts[k] || 0) + 1;
        });
        return counts;
    }

    function buildIntroMessage(stale, counts) {
        const lines = [];
        lines.push(`Found ${stale.length} stale routine${stale.length === 1 ? '' : 's'} (repeating tasks more than ${STALE_THRESHOLD_DAYS} days overdue).`);
        lines.push("");
        lines.push("Recommendations:");
        if (counts.drop > 0)     lines.push(`  · Drop to reset/forward:  ${counts.drop}`);
        if (counts.skip > 0)     lines.push(`  · Manual decide (complete-or-drop): ${counts.skip}`);
        if (counts.complete > 0) lines.push(`  · Complete:               ${counts.complete}`);
        lines.push("");
        lines.push("For routines you want to SKIP and resume from today, the Catch Up setting handles this — but it's not toggleable via Omni Automation. Pick 'Show fix instructions' on those items for the manual walkthrough.");
        lines.push("");
        lines.push("Walk through each item in turn. Cancel any item to stop the loop.");
        return lines.join("\n");
    }

    async function promptForItem(entry, position, total) {
        const t = entry.task;
        const form = new Form();

        // @ts-ignore — 6th arg (nullOptionTitle) is optional at runtime
        form.addField(new Form.Field.Option(
            "action",
            "What to do?",
            ["skip", "complete", "drop", "instructions"],
            [
                "Skip — leave unchanged (decide later)",
                "Complete — the activity actually happened",
                "Drop — cancel this routine entirely",
                "Show Catch Up fix instructions (manual fix in OmniFocus)"
            ],
            entry.recommendation.key
        ));

        const projectName = t.containingProject ? t.containingProject.name : "Inbox";
        const lines = [];
        lines.push(`${entry.daysOverdue} days overdue · project: ${projectName}`);
        if (entry.scheduleType) {
            lines.push(`Schedule type: ${entry.scheduleType}` + (entry.catchUp === true ? " · Catch Up: ON" : entry.catchUp === false ? " · Catch Up: OFF" : ""));
        }
        lines.push("");
        lines.push(`Recommended: ${entry.recommendation.text}`);

        const title = `Stale ${position}/${total}: ${t.name}\n\n${lines.join("\n")}`;

        let result;
        try {
            result = await form.show(title, "Apply");
        } catch (e) {
            return { stopped: true };
        }
        if (!result) return { stopped: true };

        return { action: String(result.values["action"] || "skip") };
    }

    /**
     * Canonical Catch Up walkthrough. Surfaces the manual fix steps the
     * user needs to perform in OmniFocus's UI (the API can't toggle the
     * Catch Up checkbox). Per gtd-coach's repeating-tasks reference.
     */
    async function showCatchUpInstructions(entry) {
        const t = entry.task;
        const message =
            `To SKIP overdue instances and resume the routine from today:\n\n` +
            `1. Open the task "${t.name}" in OmniFocus\n` +
            `2. Tap/click the repeat info (the ⟲ icon next to the task name)\n` +
            `3. Enable "Catch Up Automatically"\n` +
            `4. Mark the task complete\n` +
            `5. The repeat rule will skip the ${entry.daysOverdue} overdue instance(s) and resume the cadence from today\n` +
            `6. (Optional) Disable Catch Up again if you don't want this behavior next time\n\n` +
            `Note: Catch Up is not toggleable via Omni Automation, which is why this step is manual. ` +
            `Attache can drop or complete the task for you, but the Catch-Up-and-skip path requires the OmniFocus UI.`;

        const alert = new Alert("Catch Up Walkthrough", message);
        alert.addOption("Copy Steps");
        alert.addOption("OK");
        const choice = await alert.show();
        if (choice === 0) {
            Pasteboard.general.string = message;
        }
    }

    // Always available — no FM required
    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
