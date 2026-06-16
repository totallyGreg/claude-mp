/**
 * Process Inbox — walk inbox items one-by-one with the GTD clarify decision
 * tree. Per-item Form lets the user pick an action (Drop / Complete / Defer /
 * Promote to Project / Clarify in place / Skip) and optionally rename, tag,
 * or assign a folder; dispatches via ofoCore.
 *
 * This is the [I] action from #186 — the biggest GTD methodology gap in
 * Attache today (Capture and Reflect are partly covered, Clarify wasn't
 * actionable until this).
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - No Foundation Models dependency (works regardless of macOS version)
 */

(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        try {
            const ofoCore = this.plugIn.library("ofoCore");

            // Collect available inbox items (skip already-completed/dropped/etc).
            const items = [];
            inbox.forEach(t => {
                if (t.completed || t.dropped) return;
                if (t.taskStatus !== Task.Status.Available) return;
                items.push(t);
            });

            if (items.length === 0) {
                const alert = new Alert("Process Inbox", "Inbox is empty. Nothing to process.");
                alert.addOption("OK");
                await alert.show();
                return;
            }

            let processed = 0;
            let skipped = 0;
            let stopped = false;
            const issues = [];

            for (let i = 0; i < items.length; i++) {
                const t = items[i];
                const decision = await promptForItem(t, i + 1, items.length);

                if (decision.stopped) {
                    stopped = true;
                    break;
                }

                if (!decision.dispatched) {
                    skipped++;
                    continue;
                }

                const result = dispatchDecision(decision, t, ofoCore);
                if (result && !result.success) {
                    issues.push(`${t.name}: ${result.error || 'dispatch failed'}`);
                } else {
                    processed++;
                }
            }

            let summary = `Processed ${processed} inbox item${processed === 1 ? '' : 's'}.`;
            if (skipped > 0) {
                summary += `\nSkipped ${skipped}.`;
            }
            if (stopped) {
                summary += `\nStopped before reviewing all ${items.length} items.`;
            }
            if (issues.length > 0) {
                summary += `\n\nIssues:\n  · ${issues.join('\n  · ')}`;
            }
            const summaryAlert = new Alert("Process Inbox — Summary", summary);
            summaryAlert.addOption("OK");
            await summaryAlert.show();

        } catch (err) {
            const errAlert = new Alert(
                err && err.name ? err.name : "Process Inbox Error",
                err && err.message ? err.message : String(err)
            );
            errAlert.addOption("OK");
            await errAlert.show();
            console.error("processInbox:", err);
        }
    });

    /**
     * Show a per-item Form with action picker + optional fields. Returns:
     *   { stopped: true }                — user cancelled (exit the loop)
     *   { dispatched: false }            — user chose Skip (no dispatch)
     *   { dispatched: true, action, ... }— user chose an actionable decision
     */
    async function promptForItem(task, position, total) {
        const form = new Form();

        // @ts-ignore — 6th arg (nullOptionTitle) is optional at runtime
        form.addField(new Form.Field.Option(
            "action",
            "What to do?",
            ["skip", "drop", "complete", "defer1d", "defer1w", "project", "clarify"],
            [
                "Skip — leave in inbox",
                "Drop — not actionable",
                "Complete — already done",
                "Defer 1 day",
                "Defer 1 week",
                "Promote to Project",
                "Clarify in place (rename / tag)"
            ],
            "skip"
        ));
        form.addField(new Form.Field.String("rename", "Rename to (optional)", ""));
        form.addField(new Form.Field.String("tags", "Tags to add (comma-separated, optional)", ""));
        form.addField(new Form.Field.String("folder", "Folder for new project (optional)", ""));

        const title = `Inbox ${position}/${total}: ${task.name}`;
        const result = await form.show(title, "Apply");
        if (!result) {
            return { stopped: true };
        }

        const action = String(result.values["action"] || "skip");
        if (action === "skip") {
            return { dispatched: false };
        }

        const rename = String(result.values["rename"] || "").trim();
        const tagsInput = String(result.values["tags"] || "").trim();
        const folder = String(result.values["folder"] || "").trim();
        const tagList = tagsInput
            ? tagsInput.split(",").map(s => s.trim()).filter(s => s.length > 0)
            : [];

        return {
            dispatched: true,
            action: action,
            rename: rename,
            tags: tagList,
            folder: folder
        };
    }

    /**
     * Translate a per-item decision into one or two ofoCore calls. Returns the
     * (last) OfoResult so the caller can surface .error if dispatch failed.
     * Some actions issue more than one ofoCore call (Promote to Project =
     * createProject + dropTask); we return the most relevant failure or the
     * final success.
     */
    function dispatchDecision(decision, task, ofoCore) {
        const id = task.id.primaryKey;

        switch (decision.action) {
            case "drop":
                return ofoCore.dropTask({ id: id });

            case "complete":
                return ofoCore.completeTask({ id: id });

            case "defer1d":
                return ofoCore.updateTask({ id: id, defer: addDaysISO(1) });

            case "defer1w":
                return ofoCore.updateTask({ id: id, defer: addDaysISO(7) });

            case "project": {
                const projName = decision.rename || task.name;
                const createArgs = { name: projName };
                if (decision.folder) createArgs.folder = decision.folder;
                const createRes = ofoCore.createProject(createArgs);
                if (!createRes.success) return createRes;
                // Replace the inbox task with the new project — drop the original
                // so the user isn't left with a duplicate placeholder.
                const dropRes = ofoCore.dropTask({ id: id });
                return dropRes.success ? createRes : dropRes;
            }

            case "clarify": {
                const updateArgs = { id: id };
                if (decision.rename) updateArgs.name = decision.rename;
                let res = ofoCore.updateTask(updateArgs);
                if (!res.success) return res;
                // Tag separately via additive tagTask so existing tags survive.
                if (decision.tags.length > 0) {
                    const tagRes = ofoCore.tagTask({ id: id, add: decision.tags });
                    if (!tagRes.success) return tagRes;
                }
                return res;
            }

            default:
                return { success: false, error: "Unknown action: " + decision.action };
        }
    }

    /** Build an ISO date string N days from now (midnight local). */
    function addDaysISO(days) {
        const d = new Date();
        d.setDate(d.getDate() + days);
        d.setHours(9, 0, 0, 0); // 9am default — same convention as OmniFocus defaults
        return d.toISOString();
    }

    // Always available — no FM required
    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
