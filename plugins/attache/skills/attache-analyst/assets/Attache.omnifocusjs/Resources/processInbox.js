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
 * AI ASSIST (v2.12.0+, when Foundation Models is available)
 *
 * Per-item the action can call FM with the task name + note + categorized
 * tag taxonomy (from the System Map's tags.categories.*) and pre-fill the
 * form's action picker, rename field, and tags field with the model's
 * recommendation. The user accepts, edits, or overrides each field
 * before dispatching.
 *
 * The opt-in is per-run, asked at action start when FM is available.
 * Trade-off: per-item FM calls add 1-3s latency (×N items). Opt out
 * for a fast no-AI walk.
 *
 * Tag suggestions are constrained to the user's existing taxonomy — the
 * AI never invents new tags (see AGENTS.md design principle 1). When the
 * System Map is missing/stale, falls back to a flat list of all existing
 * tags from flattenedTags (no semantic categorization, but the no-
 * invention guarantee still holds).
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - Foundation Models OPTIONAL (used only for opt-in pre-fill)
 * - System Map OPTIONAL (categorized tag suggestions; degrades to flat list)
 */

(() => {
    const SYSTEM_MAP_TASK_NAME = "Attache System Map";
    const EXPECTED_SCHEMA_VERSION = 1;

    const action = new PlugIn.Action(async function(selection, sender) {
        try {
            const ofoCore = this.plugIn.library("ofoCore");
            const fmUtils = this.plugIn.library("foundationModelsUtils");

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

            // === AI assist opt-in (per-run) ===
            const fmAvailable = fmUtils && fmUtils.isAvailable();
            let aiAssistEnabled = false;
            if (fmAvailable) {
                const optInAlert = new Alert(
                    "Process Inbox — AI Assist?",
                    `You have ${items.length} inbox item${items.length === 1 ? '' : 's'} to process.\n\n` +
                    "With AI assist on, each item's form pre-fills with Foundation Models' " +
                    "suggestion for action, rename, and tags (chosen ONLY from your existing " +
                    "tags — never invented).\n\n" +
                    `Trade-off: ~1-3 seconds of FM latency per item (estimated ${items.length}-${items.length * 3} extra seconds total for this run).`
                );
                optInAlert.addOption("Yes — AI assist");
                optInAlert.addOption("No — blank fields");
                optInAlert.addOption("Cancel");
                const choice = await optInAlert.show();
                if (choice === 2) return; // Cancel
                aiAssistEnabled = choice === 0;
            }

            // === AI assist setup (System Map + tag taxonomy + FM session) ===
            let session = null;
            let categorizedTags = null;
            let existingTagsByName = null;
            if (aiAssistEnabled) {
                const sm = loadSystemMapSoft();
                categorizedTags = collectCategorizedTags(sm);
                existingTagsByName = buildTagNameMap();
                session = fmUtils.createSession(
                    "You are a GTD coach helping the user process their OmniFocus inbox. " +
                    "Be concise and direct. Choose tags ONLY from the user's existing tag list. " +
                    "Never invent new tags."
                );
            }

            let processed = 0;
            let skipped = 0;
            let stopped = false;
            const issues = [];

            for (let i = 0; i < items.length; i++) {
                const t = items[i];

                // Get FM suggestion if AI assist is on. Failure is non-fatal —
                // promptForItem gets null and falls back to blank fields.
                let suggestion = null;
                if (aiAssistEnabled && session) {
                    suggestion = await suggestForItem(t, session, categorizedTags, existingTagsByName);
                }

                const decision = await promptForItem(t, i + 1, items.length, suggestion);

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
     *
     * When `suggestion` is non-null (AI assist on + FM returned a result),
     * the picker default + rename + tags fields pre-fill with the model's
     * recommendation. User accepts, edits, or overrides per field.
     */
    async function promptForItem(task, position, total, suggestion) {
        const form = new Form();

        // Map AI's recommendation onto a picker key. FM returns the broad
        // intent (drop / complete / project / clarify) — defer is omitted
        // from the AI schema because date semantics without explicit user
        // input are unreliable. Pre-fill picker default with AI's pick when
        // available; otherwise the safe "skip" default.
        const defaultAction = (suggestion && suggestion.action) || "skip";
        const defaultRename = (suggestion && suggestion.rename) || "";
        const defaultTags = (suggestion && suggestion.tags && suggestion.tags.length > 0)
            ? suggestion.tags.join(", ")
            : "";

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
            defaultAction
        ));
        form.addField(new Form.Field.String("rename", "Rename to (optional)", defaultRename));
        form.addField(new Form.Field.String("tags", "Tags to add (comma-separated, optional)", defaultTags));
        form.addField(new Form.Field.String("folder", "Folder for new project (optional)", ""));

        // Show AI reasoning in the title subtitle so the user understands WHY
        // these defaults were picked. Empty for the no-AI path.
        let title = `Inbox ${position}/${total}: ${task.name}`;
        if (suggestion && suggestion.reasoning) {
            title += `\n\n🤖 AI suggests "${suggestion.action}": ${suggestion.reasoning}`;
        }

        // Defensive: Form.show() has been observed to REJECT rather than
        // resolve-to-null on cancel in some OmniFocus builds (the form-
        // level cancel guard with `if (!result)` is necessary but not
        // sufficient). Wrap in try/catch so cancel always exits the loop
        // cleanly instead of bubbling as a "Process Inbox Error" alert.
        let result;
        try {
            result = await form.show(title, "Apply");
        } catch (e) {
            return { stopped: true };
        }
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

    // ──────── AI assist helpers ────────

    /**
     * Soft-load the System Map for tag categorization. Unlike quickOrganize
     * (hard-block on missing), processInbox's AI assist degrades to a flat
     * tag list when the map is missing — categorization is a nice-to-have,
     * the existing-taxonomy constraint is the must-have.
     */
    function loadSystemMapSoft() {
        const candidates = flattenedTasks.filter(t => t.name === SYSTEM_MAP_TASK_NAME);
        if (candidates.length === 0) return null;
        let sm;
        try {
            sm = JSON.parse(candidates[0].note || "{}");
        } catch (e) { return null; }
        if (typeof sm.schemaVersion !== "number") return null;
        if (sm.schemaVersion < EXPECTED_SCHEMA_VERSION) return null;
        return sm;
    }

    /**
     * Pull categorized tag names from the System Map. Returns an object with
     * arrays per semantic category (contexts / energy / duration / areas),
     * plus a `flat` fallback containing ALL existing tag names walked from
     * the live OF tag tree.
     *
     * The flat fallback is the safety net: when the map is missing or stale,
     * AI suggestion still works — just without semantic categorization.
     * Either way, the model is constrained to existing tags only.
     *
     * Deliberately EXCLUDES people / status / uncategorized from
     * suggestion-time (those are user-managed; AI shouldn't auto-assign
     * "Waiting:Sarah" or "@hold" without explicit signal).
     */
    function collectCategorizedTags(sm) {
        const result = {
            contexts: [],
            energy: [],
            duration: [],
            areas: [],
            flat: collectAllTagNames()
        };
        if (!sm || !sm.tags || !sm.tags.categories) return result;
        const cats = sm.tags.categories;
        result.contexts = extractCategoryNames(cats.contexts);
        result.energy = extractCategoryNames(cats.energy);
        result.duration = extractCategoryNames(cats.duration);
        result.areas = extractCategoryNames(cats.areas);
        return result;
    }

    function extractCategoryNames(catList) {
        if (!Array.isArray(catList)) return [];
        return catList
            .map(entry => entry && entry.name)
            .filter(name => typeof name === "string" && name.length > 0)
            .filter(name => flattenedTags.byName(name) !== null); // user-deleted-since-refresh
    }

    /** Walk the entire OF tag tree, return canonical-case names deduped. */
    function collectAllTagNames() {
        const out = [];
        const seen = {};
        function walk(tagList) {
            tagList.forEach(t => {
                if (t.status === Tag.Status.Dropped) return;
                if (!seen[t.name]) {
                    seen[t.name] = true;
                    out.push(t.name);
                }
                if (t.children && t.children.length > 0) walk(t.children);
            });
        }
        walk(tags); // top-level OF global
        return out;
    }

    /** Case-insensitive lookup map: lowercased name → canonical name. */
    function buildTagNameMap() {
        const map = {};
        collectAllTagNames().forEach(name => {
            map[name.toLowerCase()] = name;
        });
        return map;
    }

    /**
     * Call Foundation Models with the task's content + categorized tag
     * options. Returns a normalized suggestion `{action, rename, tags,
     * reasoning}` or null on any failure (the caller handles null by
     * falling back to blank-field defaults).
     *
     * Action vocabulary deliberately narrow: drop / complete / project /
     * clarify. Defer is OMITTED because date semantics without explicit
     * user input are unreliable — the user can always pick defer themselves
     * from the picker. "Skip" is the safe fallback when AI is unsure
     * (treated by promptForItem as the "no-AI default").
     */
    async function suggestForItem(task, session, cats, existingTagsByName) {
        try {
            const taskContext = buildTaskContext(task);
            const tagSection = buildTagSection(cats);
            const prompt =
                `Help clarify this OmniFocus inbox item.\n\n` +
                `TASK:\n${taskContext}\n\n` +
                `${tagSection}\n\n` +
                `Pick:\n` +
                `1. action — one of: drop (not actionable), complete (already done), project (multi-step), clarify (single next action that needs refinement)\n` +
                `2. rename — a clearer task name, OR empty string if current name is fine\n` +
                `3. tags — 1-3 tag names from the EXISTING TAGS list above, OR empty array if none fit. Prefer one context, one energy, etc — different categories. Never invent.\n` +
                `4. reasoning — one short sentence on why this action / these tags fit`;

            const schema = LanguageModel.Schema.fromJSON({
                name: "inbox-clarify",
                properties: [
                    { name: "action", description: "One of: drop / complete / project / clarify" },
                    { name: "rename", description: "Clearer task name, or empty string", isOptional: true },
                    {
                        name: "tags",
                        description: "1-3 tag names from EXISTING TAGS — empty array if none fit",
                        schema: { arrayOf: { type: "string" } }
                    },
                    { name: "reasoning", description: "One short sentence explaining the action + tag choice" }
                ]
            });

            const opts = new LanguageModel.GenerationOptions();
            opts.maximumResponseTokens = 250;
            const response = await session.respondWithSchema(prompt, schema, opts);
            const parsed = JSON.parse(response);

            // Normalize action to a picker key. Reject unknown values
            // (treat as "skip" — pick default).
            const validActions = { drop: true, complete: true, project: true, clarify: true };
            const action = validActions[parsed.action] ? parsed.action : "skip";

            // Constrain tags to the user's existing taxonomy (case-insensitive
            // match, re-mapped to canonical case). Hallucinations are silently
            // dropped — the form never offers tags the user doesn't have.
            const tags = constrainTagsToExisting(parsed.tags, existingTagsByName);

            const rename = typeof parsed.rename === "string" ? parsed.rename.trim() : "";
            const reasoning = typeof parsed.reasoning === "string" ? parsed.reasoning.trim() : "";

            return { action, rename, tags, reasoning };
        } catch (e) {
            console.error("processInbox suggestForItem:", e);
            return null;
        }
    }

    function buildTaskContext(task) {
        const lines = [`Name: ${task.name}`];
        if (task.note && task.note.length > 0) {
            // Truncate long notes to keep prompt budget reasonable
            const note = task.note.length > 400 ? task.note.substring(0, 400) + "…" : task.note;
            lines.push(`Note: ${note}`);
        }
        if (task.tags && task.tags.length > 0) {
            lines.push(`Current tags: ${task.tags.map(t => t.name).join(", ")}`);
        }
        return lines.join("\n");
    }

    /**
     * Build the "EXISTING TAGS" prompt section. Prefers categorized layout
     * when the System Map provided one; falls back to flat list otherwise.
     * The categorized form gives the model semantic signal — it can pick
     * one context AND one energy (different categories) rather than two
     * mutually-exclusive contexts.
     */
    function buildTagSection(cats) {
        const sections = [];
        if (cats.contexts.length > 0) sections.push(`CONTEXTS (pick 0-1, where am I): ${cats.contexts.join(", ")}`);
        if (cats.energy.length > 0)   sections.push(`ENERGY   (pick 0-1, how I feel): ${cats.energy.join(", ")}`);
        if (cats.duration.length > 0) sections.push(`DURATION (pick 0-1, how long): ${cats.duration.join(", ")}`);
        if (cats.areas.length > 0)    sections.push(`AREAS    (pick 0-1, life area): ${cats.areas.join(", ")}`);

        if (sections.length > 0) {
            return "EXISTING TAGS (choose ONLY from these — never invent):\n" + sections.join("\n");
        }

        // Fallback: flat list (System Map missing or didn't categorize).
        if (cats.flat.length === 0) {
            return "EXISTING TAGS: (none configured — return empty tags array)";
        }
        return "EXISTING TAGS (choose ONLY from this list — never invent):\n" + cats.flat.join(", ");
    }

    /**
     * Filter AI-suggested tag names to those in the user's existing taxonomy.
     * Mirrors the analyzeSelected pattern (37fd08a) — case-insensitive match,
     * remap to canonical case, dedupe.
     */
    function constrainTagsToExisting(suggestedTags, existingTagsByName) {
        if (!Array.isArray(suggestedTags) || !existingTagsByName) return [];
        const out = [];
        const used = {};
        suggestedTags.forEach(raw => {
            if (typeof raw !== "string") return;
            const key = raw.trim().toLowerCase();
            if (!key) return;
            const canonical = existingTagsByName[key];
            if (!canonical || used[canonical]) return;
            used[canonical] = true;
            out.push(canonical);
        });
        return out;
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
