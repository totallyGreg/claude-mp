/**
 * Quick Organize — walk the user's selection (tasks + projects) with a
 * per-item bucket picker and dispatch via ofoCore using the user's own
 * GTD conventions (NOT hardcoded names).
 *
 * For TASKS the buckets are: Skip / Active / Waiting For / Someday-Maybe /
 * Drop, with an optional context-tag picker layered on top.
 *
 * For PROJECTS the buckets are: Skip / Active / On Hold / Drop — pure
 * status changes via updateProject.
 *
 * This is the [O] action from #186 — closes the Organize-phase gap.
 *
 * SYSTEM MAP DEPENDENCY
 *
 * quickOrganize reads conventions from the Attache System Map: it never
 * hardcodes "@waiting" or "Someday/Maybe" — every user has their own
 * naming. The skeleton follows the doctrine in
 * `omnifocus-generator/references/system_map_dependency.md` (schema-
 * version contract, hard-fail-on-missing instead of silent defaults,
 * surface refresh instruction to the user).
 *
 * Buckets whose convention is missing are omitted from the picker
 * (so the user never sees "Waiting For" if their map has no waitingTag);
 * the missing-convention reason is shown in the form title so they
 * know what to do (refresh after tagging some tasks).
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - Selection of at least one task or project
 * - Attache System Map present (run "Setup" / "Map System" first)
 * - No Foundation Models dependency
 */

(() => {
    const SYSTEM_MAP_TASK_NAME = "Attache System Map";
    const EXPECTED_SCHEMA_VERSION = 1;

    const action = new PlugIn.Action(async function(selection, sender) {
        try {
            const ofoCore = this.plugIn.library("ofoCore");

            // === System Map pre-flight ===
            const smLoad = loadSystemMap();
            if (!smLoad.ok) {
                const alert = new Alert(smLoad.title, smLoad.message);
                alert.addOption("OK");
                await alert.show();
                return;
            }
            const sm = smLoad.sm;

            // Resolve conventions — null means "convention not set; omit from picker"
            const waitingTag = sm.conventions && sm.conventions.waitingTag;
            const somedayTag = sm.conventions && sm.conventions.somedayTag;
            const contextTags = collectContextTagNames(sm);
            const missingNotes = collectMissingConventionNotes(waitingTag, somedayTag, contextTags);

            // === Build the work list ===
            const tasks = (selection.tasks || []).filter(t => !t.completed && !t.dropped);
            const projects = (selection.projects || []);
            const total = tasks.length + projects.length;

            if (total === 0) {
                const alert = new Alert(
                    "Quick Organize",
                    "Select one or more tasks or projects, then run Quick Organize."
                );
                alert.addOption("OK");
                await alert.show();
                return;
            }

            let organized = 0;
            let skipped = 0;
            let stopped = false;
            const issues = [];

            // === Walk tasks first, then projects ===
            for (let i = 0; i < tasks.length; i++) {
                const t = tasks[i];
                const r = await promptForTask(t, i + 1, total, waitingTag, somedayTag, contextTags, missingNotes);
                if (r.stopped) { stopped = true; break; }
                if (!r.dispatched) { skipped++; continue; }

                const res = dispatchTaskDecision(r, t, ofoCore, waitingTag, somedayTag);
                if (res && !res.success) {
                    issues.push(`${t.name}: ${res.error || 'dispatch failed'}`);
                } else {
                    organized++;
                }
            }

            if (!stopped) {
                for (let i = 0; i < projects.length; i++) {
                    const p = projects[i];
                    const position = tasks.length + i + 1;
                    const r = await promptForProject(p, position, total, missingNotes);
                    if (r.stopped) { stopped = true; break; }
                    if (!r.dispatched) { skipped++; continue; }

                    const res = dispatchProjectDecision(r, p, ofoCore);
                    if (res && !res.success) {
                        issues.push(`${p.name}: ${res.error || 'dispatch failed'}`);
                    } else {
                        organized++;
                    }
                }
            }

            let summary = `Organized ${organized} item${organized === 1 ? '' : 's'}.`;
            if (skipped > 0) {
                summary += `\nSkipped ${skipped}.`;
            }
            if (stopped) {
                summary += `\nStopped before reviewing all ${total} items.`;
            }
            if (issues.length > 0) {
                summary += `\n\nIssues:\n  · ${issues.join('\n  · ')}`;
            }
            const summaryAlert = new Alert("Quick Organize — Summary", summary);
            summaryAlert.addOption("OK");
            await summaryAlert.show();

        } catch (err) {
            const errAlert = new Alert(
                err && err.name ? err.name : "Quick Organize Error",
                err && err.message ? err.message : String(err)
            );
            errAlert.addOption("OK");
            await errAlert.show();
            console.error("quickOrganize:", err);
        }
    });

    // ──────── System Map ────────

    /**
     * Load + validate the System Map per the doctrine in
     * omnifocus-generator/references/system_map_dependency.md.
     * Returns { ok: true, sm } or { ok: false, title, message } with a
     * user-facing alert payload (always pointing at `ofo system-map --refresh`
     * as the fix). Never silently defaults missing fields — that's the whole
     * point of the doctrine.
     */
    function loadSystemMap() {
        const candidates = flattenedTasks.filter(t => t.name === SYSTEM_MAP_TASK_NAME);
        if (candidates.length === 0) {
            return {
                ok: false,
                title: "System Map Missing",
                message: "Quick Organize uses your OmniFocus conventions (waiting tag, someday tag, contexts). Run Attache → Setup, or `ofo system-map --refresh`, then try again."
            };
        }
        const smTask = candidates[0];
        let sm;
        try {
            sm = JSON.parse(smTask.note || "{}");
        } catch (e) {
            return {
                ok: false,
                title: "System Map Corrupt",
                message: "The Attache System Map note isn't valid JSON. Run Attache → Setup or `ofo system-map --refresh` to regenerate."
            };
        }
        if (typeof sm.schemaVersion !== "number") {
            return {
                ok: false,
                title: "System Map Predates Versioning",
                message: "The cached System Map predates schema versioning. Run Attache → Setup or `ofo system-map --refresh`."
            };
        }
        if (sm.schemaVersion < EXPECTED_SCHEMA_VERSION) {
            return {
                ok: false,
                title: "System Map Schema Stale",
                message: `Cached map is v${sm.schemaVersion}; Quick Organize needs v${EXPECTED_SCHEMA_VERSION}. Run Attache → Setup or \`ofo system-map --refresh\`.`
            };
        }
        if (sm.schemaVersion > EXPECTED_SCHEMA_VERSION) {
            console.log(`System Map schema v${sm.schemaVersion} is newer than expected v${EXPECTED_SCHEMA_VERSION}; proceeding.`);
        }
        return { ok: true, sm: sm };
    }

    /**
     * Extract context-tag names from the System Map's
     * tags.categories.contexts list. Each TagEntry is expected to have a
     * `name` field. Returns names in document order, dropping any that
     * no longer exist in the live OF tag tree (handles the case where the
     * user deleted a tag since the last map refresh).
     */
    function collectContextTagNames(sm) {
        const out = [];
        const ctxList = sm && sm.tags && sm.tags.categories && sm.tags.categories.contexts;
        if (!Array.isArray(ctxList)) return out;
        ctxList.forEach(entry => {
            const name = entry && entry.name;
            if (typeof name !== "string" || !name) return;
            if (!flattenedTags.byName(name)) return; // user deleted since refresh
            out.push(name);
        });
        return out;
    }

    /**
     * Build a single human-readable note about which conventions are missing
     * (used as a subtitle in the per-item form so the user knows WHY a
     * bucket isn't on offer). Returns "" when all conventions are set.
     */
    function collectMissingConventionNotes(waitingTag, somedayTag, contextTags) {
        const missing = [];
        if (!waitingTag) missing.push("waitingTag");
        if (!somedayTag) missing.push("somedayTag");
        if (contextTags.length === 0) missing.push("contexts");
        if (missing.length === 0) return "";
        return `Conventions missing: ${missing.join(", ")} — run Setup to populate.`;
    }

    // ──────── Per-task flow ────────

    async function promptForTask(task, position, total, waitingTag, somedayTag, contextTags, missingNotes) {
        const form = new Form();

        // Build bucket choices dynamically — only include buckets whose
        // convention is set. "Active" is always available (no-op), "Drop" is
        // always available, "Waiting For" / "Someday-Maybe" require their
        // respective tag convention.
        const bucketKeys = ["skip", "active"];
        const bucketLabels = ["Skip — leave unchanged", "Active — keep in normal flow"];
        if (waitingTag) {
            bucketKeys.push("waiting");
            bucketLabels.push(`Waiting For — add tag "${waitingTag}"`);
        }
        if (somedayTag) {
            bucketKeys.push("someday");
            bucketLabels.push(`Someday / Maybe — add tag "${somedayTag}"`);
        }
        bucketKeys.push("drop");
        bucketLabels.push("Drop — not actionable");

        // @ts-ignore — 6th arg (nullOptionTitle) is optional at runtime
        form.addField(new Form.Field.Option(
            "bucket",
            "Bucket",
            bucketKeys,
            bucketLabels,
            "skip"
        ));

        // Context-tag picker (optional). Only shown when the map surfaced
        // contexts; first option is "(none)" so the user can leave it blank.
        if (contextTags.length > 0) {
            const contextKeys = [""].concat(contextTags);
            const contextLabels = ["(no context tag)"].concat(contextTags);
            // @ts-ignore — 6th arg (nullOptionTitle) is optional at runtime
            form.addField(new Form.Field.Option(
                "context",
                "Context tag (optional)",
                contextKeys,
                contextLabels,
                ""
            ));
        }

        const title = `Organize ${position}/${total} — Task: ${task.name}`;
        const result = missingNotes
            ? await form.show(`${title}\n\n${missingNotes}`, "Apply")
            : await form.show(title, "Apply");
        if (!result) {
            return { stopped: true };
        }

        const bucket = String(result.values["bucket"] || "skip");
        const contextTag = contextTags.length > 0
            ? String(result.values["context"] || "")
            : "";

        if (bucket === "skip" && !contextTag) {
            return { dispatched: false };
        }

        return {
            dispatched: true,
            kind: "task",
            bucket: bucket,
            contextTag: contextTag
        };
    }

    function dispatchTaskDecision(decision, task, ofoCore, waitingTag, somedayTag) {
        const id = task.id.primaryKey;
        const tagsToAdd = [];

        switch (decision.bucket) {
            case "skip":
            case "active":
                // No bucket-level change for these; context tag may still apply below.
                break;
            case "waiting":
                if (!waitingTag) {
                    return { success: false, error: "waitingTag convention missing" };
                }
                tagsToAdd.push(waitingTag);
                break;
            case "someday":
                if (!somedayTag) {
                    return { success: false, error: "somedayTag convention missing" };
                }
                tagsToAdd.push(somedayTag);
                break;
            case "drop":
                return ofoCore.dropTask({ id: id });
            default:
                return { success: false, error: "Unknown bucket: " + decision.bucket };
        }

        if (decision.contextTag) {
            tagsToAdd.push(decision.contextTag);
        }

        if (tagsToAdd.length === 0) {
            // "Active" with no context tag — true no-op
            return { success: true };
        }

        return ofoCore.tagTask({ id: id, add: tagsToAdd });
    }

    // ──────── Per-project flow ────────

    async function promptForProject(project, position, total, missingNotes) {
        const form = new Form();
        // @ts-ignore — 6th arg (nullOptionTitle) is optional at runtime
        form.addField(new Form.Field.Option(
            "bucket",
            "Bucket",
            ["skip", "active", "onHold", "drop"],
            [
                "Skip — leave unchanged",
                "Active — set status to active",
                "On Hold — Someday / Maybe equivalent",
                "Drop — abandon the project"
            ],
            "skip"
        ));

        const title = `Organize ${position}/${total} — Project: ${project.name}`;
        const result = missingNotes
            ? await form.show(`${title}\n\n${missingNotes}`, "Apply")
            : await form.show(title, "Apply");
        if (!result) {
            return { stopped: true };
        }

        const bucket = String(result.values["bucket"] || "skip");
        if (bucket === "skip") {
            return { dispatched: false };
        }
        return { dispatched: true, kind: "project", bucket: bucket };
    }

    function dispatchProjectDecision(decision, project, ofoCore) {
        const id = project.id.primaryKey;
        switch (decision.bucket) {
            case "active":  return ofoCore.updateProject({ id: id, status: "active" });
            case "onHold":  return ofoCore.updateProject({ id: id, status: "onHold" });
            case "drop":    return ofoCore.updateProject({ id: id, status: "dropped" });
            default:        return { success: false, error: "Unknown bucket: " + decision.bucket };
        }
    }

    // Require a selection of at least one task or project. No FM dependency.
    action.validate = function(selection, sender) {
        return (selection.tasks && selection.tasks.length > 0)
            || (selection.projects && selection.projects.length > 0);
    };

    return action;
})();
