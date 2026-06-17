# Attache — Agent Notes

Working notes for any agent (human or LLM) modifying the Attache plugin. Aggregates design decisions, the **why** behind them, and the gotchas discovered while shipping each version. Auto-loaded as context when working in `plugins/attache/`.

Companion docs:

- `README.md` — outward-facing overview (what the plugin does, components)
- `CONTRIBUTING.md` — architectural diagram + ofoCore execution contexts
- `agents/attache.md` — the orchestrator agent's behavior (routing, channel selection)
- `skills/attache-analyst/references/system_map_schema.md` — System Map JSON contract (v1)
- `skills/omnifocus-generator/references/system_map_dependency.md` — doctrine for plugins consuming the map

This file is the **design-principles + gotchas** layer those don't cover.

---

## Action inventory (Attache.omnifocusjs)

| Action | Role | FM required? | System Map use |
|---|---|---|---|
| `healthCheck` | Landing-page diagnostic — names the fix-it action for each unhealthy indicator | No | Soft (checks freshness as a signal) |
| `dailyReview` | Daily operational ritual — completed / today / overdue / coaching | Yes | Drift signal only |
| `whatNow` | Situational Engage filter (context / time / energy → top-5 candidates) | No | Soft (pickers omitted when categories empty) |
| `weeklyReview` | Weekly operational review — 7 scripted steps with FM coaching | Yes | None today (#189 redesign pending) |
| `monthlyReview` | Horizon 2 (Areas of Focus) — per-area coaching | Yes | Hard (needs `inferredType === 'area'` folders) |
| `horizonsReview` | Horizons 3-5 (Goals / Vision / Purpose) — quarterly reflection | Optional | No |
| `processInbox` | Clarify-phase per-item walk (drop / complete / defer / project / clarify) | No | No |
| `analyzeSelected` (Clarify Tasks) | Per-task AI rewrite suggestions with apply-path | Yes | **Should but doesn't** — see #186 tag-categorization bullet |
| `analyzeHierarchy` (Project Health) | Folder/project insights with bottleneck-flag apply-path | Yes | No |
| `quickOrganize` | Per-item bucket picker (Skip / Active / Waiting / Someday / Drop) | No | Hard (waitingTag / somedayTag / contexts) |
| `completedSummary` (Wins Report) | Period completions + capture follow-up tasks | No | No |
| `systemSetup` | First-run + on-demand System Map discovery (writes the map) | Optional | Produces |
| `discoverSystem` | Discovery without caching | Optional | Produces |

Cadence wiring intent: `healthCheck` is the daily-or-weekly landing page that points at the others. `daily → whatNow → weekly → monthly → horizons` is the review-cadence ladder. `processInbox / analyzeSelected / analyzeHierarchy / quickOrganize` are clarify/organize utilities invoked ad-hoc.

---

## Design principles

### 1. Respect the user's existing taxonomy — never invent

Automated actions that suggest or apply tags, categories, or contexts MUST source from the user's existing OmniFocus structure. AI prompts constrain suggestions to existing names; apply-paths post-filter to drop hallucinated entries before they reach the user.

**Why:** User feedback on v2.5.0: *"[Clarify Tasks] provided recommendations for tagging that did not understand the existing tagging structure and suggested making up new tags. This is an anti-pattern in that over time an infinite number of tags could be created. … The point of the system map is for each individual user can have their own organization working structure and any automated actions are part of that structure, not inventing new ones on the fly."*

**How to apply:**

- AI prompts: include the user's tag list verbatim with explicit instruction to choose from it. Set `isOptional: true` on the schema field so the model can return an empty list when nothing fits, rather than confabulating.
- Dispatch layer: post-filter against `flattenedTags.byName(...)` and silently drop any tags that don't resolve — the user never sees an "Add tags: invented-thing" prompt.
- User-typed free-text fields (like `processInbox`'s tags input) are exempt — the constraint is on AI-generated suggestions, not on direct user input.
- Canonical implementation: `analyzeSelected.js` (`collectExistingTagNames` + `constrainTagsToExisting`, shipped in v2.6.1 / commit `37fd08a`).

**Open gap:** the constraint today is *existence* not *semantic role*. AI sees a flat list, not category info from `sm.tags.categories.*`. Tracked as an open bullet under `analyzeSelected` in #186.

### 2. System Map for ALL conventions — never hardcode

When an action needs `@waiting`, `Someday/Maybe`, a default context tag, or any other GTD convention, it reads from the System Map (`sm.conventions.*`, `sm.tags.categories.*`, `sm.structure.topLevelFolders`). Never use string literals like `"@waiting"` — that breaks on every user with a different setup.

**Pre-flight policy** depends on the action's dependence:

| Action type | System Map missing/stale | Pattern |
|---|---|---|
| Hard-blocking (action needs conventions to function) | Alert with "run Setup / `ofo system-map --refresh`" + return | `quickOrganize`, `monthlyReview` |
| Soft-degrading (action partly works without map) | Omit dependent UI; subtitle tells user what's missing | `whatNow` (omits context/energy pickers), `healthCheck` (surfaces missing-map as one indicator among many) |
| Convention-free | Don't touch map | `processInbox`, `completedSummary`, `horizonsReview`, `dailyReview` (drift signal only) |

**Canonical skeleton:** `omnifocus-generator/references/system_map_dependency.md` is the doctrine. `quickOrganize.js` is the canonical in-bundle consumer (commit `2bf6578` / v2.7.0) — `loadSystemMap` + `collectContextTagNames` + `collectMissingConventionNotes`. Copy that shape for new actions.

**Never silently default** when a convention is missing — the whole point is to eliminate guessing.

### 3. ApplyForm helper for per-item confirmation Forms

Multiple actions need "AI analyzed N items, walk the user through Apply / Skip per item." Built once as `Resources/applyForm.js` (commit `ca63d09` / v2.2.0), now consumed by `analyzeSelected`, `analyzeHierarchy` (Flag Bottlenecks), `weeklyReview` Step 3 (waiting-for).

**API:**

```js
const decision = await applyForm.confirmApply({
  itemName: task.name,
  changes: [
    { key: 'name',     label: 'Rename to: "Pay quarterly tax"' },
    { key: 'estimate', label: 'Set estimate: 30 min' },
  ],
})
if (decision.cancelled || !applyForm.anyAccepted(decision)) continue
// caller dispatches via ofoCore.* using decision.apply[key] booleans
```

**Caller composes self-describing labels and owns dispatch.** The helper deliberately does NOT know about ofoCore — that keeps it reusable across different ofoCore methods (`updateTask`, `tagTask`, `updateProject`, `dropTask`).

**When NOT to use it:** when the data shape doesn't fit checkboxes. `completedSummary`'s "capture follow-ups" needs bulk text input — that's a single Form with `Form.Field.String` rows, not the helper. Don't force the helper API to grow when a single Form already does the job (KISS / YAGNI). Documented rationale: commit `fa66147`.

### 4. Persistent state — separate Preferences key per concern

When an action needs to persist user-stated values between sessions:

- **DO NOT** stuff data into the systemMap blob (`preferencesManager.write` overwrites the whole thing on every System Map refresh — lifecycle measured in days/weeks).
- **DO** use `new Preferences("com.totallytools.omnifocus.attache")` directly with a dedicated string key. Lazy-construct inside the action body (per the warning in `preferencesManager.ts` — constructing at IIFE top level disables all actions).

**Canonical consumer:** `horizonsReview.js` (commit `62689b3` / v2.11.0) — `getPrefs()` helper + `readHorizons()` / `writeHorizons()` against key `"horizons"`. The horizons data (user-stated quarterly commitments) has a totally different lifecycle than the System Map and shouldn't be flushed when the map refreshes.

---

## Gotchas

Hard-learned things. If you remove or refactor any of these, document the new replacement in this section.

### G1. Foundation Models schema — use documented types, NOT `number`

Per the authoritative docs at <https://omni-automation.com/shared/alm-schema.html>, supported `type` values are:

| `type` value | Use for |
|---|---|
| `"string"` | text |
| `"integer"` | whole numbers (e.g. minutes, counts, scores 1-10) |
| `"decimal"` | floating-point |

**`type: 'number'` is NOT documented and is rejected** with `Invalid schema specification: Unrecognized Type: number`. This was the v2.10.1 regression (commit `86ed9d2`). The fix at the time removed the schema hint entirely, but the correct fix is `type: "integer"` for whole-number fields like `estimatedMinutes`. See also G6 — runtime coercion stays as defence in depth (FM does not always honor the schema type), but the schema CAN constrain properly when the right type name is used.

Discovered/corrected by checking the docs rather than guessing — verify against the source before introducing a schema type the codebase hasn't used yet.

#### Schema composites worth remembering

```js
// Numeric, optional (CORRECT replacement for what got removed in 86ed9d2)
{ name: 'estimatedMinutes', isOptional: true, schema: { type: 'integer' } }

// Restricted enum — preferred over free-text + post-filter
{ name: 'priority', schema: { anyOf: [
    { constant: 'high' }, { constant: 'medium' }, { constant: 'low' }
]}}

// Array with size bound
{ name: 'tags', schema: { arrayOf: { type: 'string' }, maximumElements: 3 } }

// Recursive (for trees/nested steps)
{ arrayOf: {
    name: 'step',
    properties: [
      { name: 'title' },
      { name: 'substeps', isOptional: true, schema: { arrayOf: { referenceTo: 'step' } } }
    ]
}}
```

The codebase already uses `anyOf` + `constant` (search `weeklyReview.js` for `waiting-rec-enum`). Use enums in preference to free-text + post-filter whenever the value space is small + closed.

### G2. `Task.estimatedMinutes` strictly requires Number

OmniFocus's setter rejects strings with `Property Task.estimatedMinutes requires a Number, but was passed value of type String`. `ofoCore.updateTask` doesn't coerce (it casts via TypeScript `as number` which is type-only) — passing a string from a Foundation Models response throws.

**Pattern:** normalize AI-derived numeric fields once at parse-time, right after `JSON.parse(response)`. Downstream code (display, comparison, dispatch) then sees a Number-or-null.

Discovered: v2.8.0 bug report. Fixed in commit `7cbb10a`. Same parse-time-normalization pattern as `constrainTagsToExisting` (G6).

**Open question:** should `ofoCore.updateTask` itself coerce defensively? Would catch this class of bug for all callers. Out of scope for the v2.8.1 user-reported fix; revisit when [T] or another theme touches the contract.

### G3. `Form.show()` REJECTS on cancel in some OmniFocus builds

The naive pattern `const r = await form.show(...); if (!r) return;` is necessary but not sufficient. In some builds the promise rejects instead of resolving to null, which then bubbles up the outer `try/catch` and surfaces as an error alert.

**Pattern:**

```js
let result;
try {
  result = await form.show(title, "Apply");
} catch (e) {
  return { stopped: true };  // or whatever your "cancel" sentinel is
}
if (!result) return { stopped: true };
```

Apply to **every** `form.show()` call in user-facing per-item walks. Same for `FileSaver.show()` (commit `4c5d5f4` analyzeHierarchy fix).

Discovered: v2.10.1 bug report on `processInbox`. Fixed in commit `05025a8` (also applied defensively to `quickOrganize`).

### G4. `Preferences` lazy construction is mandatory

`new Preferences(...)` at the IIFE top level disables ALL plugin actions silently. Must be lazy — construct inside the action body or a helper called from there.

**Pattern (from `preferencesManager.ts` and `horizonsReview.js`):**

```js
let _prefs = null;
function getPrefs() {
  if (!_prefs) _prefs = new Preferences("com.totallytools.omnifocus.attache");
  return _prefs;
}
```

Explicit bundle ID required — `new Preferences()` without args also throws in library context. Confirmed via Templates.omnifocusjs's pattern (cited in `preferencesManager.ts`).

### G5. In-bundle library access uses `this.plugIn.library("name")`

NOT `PlugIn.find("com.example.x").library("name")` — that pattern is for STANDALONE generated plugins. In-bundle action handlers use `this.plugIn.library(...)` because they're already inside the plugin context.

The wrong form may work in some cases but trips the D8.3 antipattern check (`PlugIn.find()` null-check requirement) and won't survive `validate-plugin.sh`. Always use `this.plugIn.library()` in bundle actions.

### G6. AI-derived fields normalize once at parse-time, not at every consumer

When an FM response has fields that need shape-correction (numeric coercion, taxonomy filtering, enum normalization), do it ONCE right after `JSON.parse(response)`. Then every downstream consumer (display, comparison, dispatch) sees the corrected value with no special handling.

Examples in `analyzeSelected.js`:

```js
const analysis = JSON.parse(response)
analysis.suggestedTags = constrainTagsToExisting(analysis.suggestedTags, existingTagsByName)  // G6 + design principle 1
analysis.estimatedMinutes = coerceEstimateMinutes(analysis.estimatedMinutes)                  // G6 + gotcha G2
```

Symptom of doing it WRONG: comparison like `analysis.estimatedMinutes !== task.estimatedMinutes` is always `true` (string vs number), surfacing the apply prompt for items where the value actually matches; OR a hallucinated tag reaches the apply form because the post-filter ran at the wrong layer.

### G7. `LanguageModel.Schema.fromJSON(...)` — factory, not constructor

Use `LanguageModel.Schema.fromJSON({ name, properties })`. **NOT** `new LanguageModel.Schema(...)` — that's the wrong constructor. Documented in `D8.3 antipatterns` and enforced by `validate-plugin.sh`.

### G8. `updateProject` status is a string, not the enum

`ofoCore.updateProject({id, status: 'active'|'onHold'|'completed'|'dropped'})` — string form. The Phase 2 contract maps these to `Project.Status.*` internally. Don't pass enum values from your action; the dispatch boundary is the string.

### G9. `ofoCore` returns `{success, error?, ...}` — never throws

Check `result.success`; surface `result.error` via `Alert`. No `try/catch` waiting for thrown errors from ofoCore. The contract is total — even "task not found" returns a structured result, not an exception.

If you find yourself wanting to wrap an ofoCore call in `try/catch`, you probably need to wrap the FORM call (G3) — that's the throwy surface.

### G10. Cancel-throws cascade also affects `FileSaver.show()`

Same defensive pattern as G3 — `await fileSaver.show(wrapper)` can throw when the user dismisses the OS save panel. The analyzeHierarchy fix (commit `4c5d5f4`) wraps it and distinguishes user-cancellation (silent return) from real save failures (Alert with the real message).

---

## Build & iteration workflow

For any change to a `Resources/*.js` file or `manifest.json`:

1. **Bump the manifest version** (`assets/Attache.omnifocusjs/manifest.json`). Patch for fixes (2.10.0 → 2.10.1), minor for new actions / behavioral additions (2.10.x → 2.11.0). **Without a bump, OmniFocus won't recognize the update** (memory entry, but worth re-stating here).
2. **Build:** `bash plugins/attache/skills/attache-analyst/scripts/build-attache.sh` → produces `scripts/build/Attache.omnifocusjs/`.
3. **Smoke-test (D8.6):** `node plugins/attache/skills/omnifocus-generator/scripts/smoke-load.js plugins/attache/skills/attache-analyst/scripts/build/Attache.omnifocusjs` — validates that every Resources/*.js parses + evaluates its top-level statements without crashing under stubbed OF globals. THIS IS THE AUTHORITATIVE PRE-INSTALL GATE.
4. **Antipattern grep on changed files:**
   ```bash
   for pat in 'Document\.defaultDocument' 'new Progress' 'FileType\.fromExtension' 'new LanguageModel\.Schema'; do
     grep -E "$pat" plugins/attache/skills/attache-analyst/scripts/build/Attache.omnifocusjs/Resources/<changed-file>.js && echo "❌"
   done
   ```
5. **Install in OmniFocus:** `open plugins/attache/skills/attache-analyst/scripts/build/Attache.omnifocusjs` → OmniFocus prompts "Replace" because the manifest version is higher than what's installed. Click Replace.

### Validator note

`bash plugins/attache/skills/omnifocus-generator/scripts/validate-plugin.sh ...` exits 1 mid-run due to a pre-existing bash 3.2 + `set -e` + missing-typescript-dir issue (TS dir expected at `omnifocus-generator/typescript/`, actually at `omnifocus-core/typescript/`). The earlier smoke-load step is authoritative; the validator's failure is not on your change.

### Don't open the source bundle

`assets/Attache.omnifocusjs/` is the SOURCE stub (action scripts only, no compiled libraries). Double-clicking it produces `Error loading plug-in: Unable to find the script "ofoCore.js"`. Only `scripts/build/Attache.omnifocusjs/` is installable. Tracked in #184 (foot-gun architecture decision pending).

---

## Registering a new action

When adding a new action (e.g. `myNewAction`):

1. **Create the action file:** `assets/Attache.omnifocusjs/Resources/myNewAction.js`
2. **Register in manifest:** add to `actions` array in `assets/Attache.omnifocusjs/manifest.json` with `identifier`, `label`, `image` (SF Symbol name)
3. **Create localized strings:** `assets/Attache.omnifocusjs/Resources/en.lproj/myNewAction.strings` with `label`, `shortLabel`, `mediumLabel`, `longLabel`, `paletteLabel` (copy an existing one as template)
4. **Register in build script:** add to `ATTACHE_ACTIONS=(...)` array in `scripts/build-attache.sh`
5. **Bump manifest version** (minor bump for new action)
6. **Build + smoke + antipattern grep** per the workflow above
7. **Test in OmniFocus** with selection-appropriate state

Skipping ANY of those steps → either broken bundle or hidden action.

---

## Commit + issue discipline

When commits land on items tracked in an issue (typically #186):

1. **`Closes #N`** in commit footer for single-bug issues (auto-closes on push)
2. **For tracking issues** (#186): after pushing, edit the issue body to flip `- [ ]` → `- [x] ~~original text~~ → ✅ shipped in commit abc1234 (vX.Y.Z)` per the strikethrough+ref convention the issue body itself prescribes. Update Priority Themes and Progress tables in the same edit.
3. **Don't file separate issues per feedback item** unless the work is substantial enough for its own multi-commit lifecycle (#189 weeklyReview redesign) or the user explicitly asks. Default: fold as sub-bullet under the relevant action's section in #186.

See user-memory `feedback_issue_hygiene.md` for the full rationale and prior corrections.
