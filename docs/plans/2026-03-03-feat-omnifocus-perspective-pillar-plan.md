---
title: "feat(omnifocus-manager): Pillar 2 — Perspective Understanding and Guided Configuration"
type: feat
status: active
date: 2026-03-03
deepened: 2026-03-04
issue: 80
---

# feat(omnifocus-manager): Pillar 2 — Perspective Understanding and Guided Configuration

## Enhancement Summary

**Deepened on:** 2026-03-04
**Research agents used:** architecture-strategist, code-simplicity-reviewer, security-sentinel,
performance-oracle, pattern-recognition-specialist, agent-native-reviewer, kieran-typescript-reviewer,
learnings-researcher (2 solutions files)

### Key Improvements Over Original Plan

1. **Phase 1 reordered** — bootstrap `archivedFilterRules` schema empirically BEFORE writing
   TypeScript types. Types authored against unconfirmed schema defeat the validation gate.
2. **TypeScript target corrected** — properties go in `omnifocus-extensions.d.ts` (not the
   generated `omnifocus.d.ts`), using `interface Custom` declaration merging.
3. **`Perspective.FilterRule` discriminated union type** — replaces `object[]` with a typed,
   self-documenting union of known filter rule shapes.
4. **System-health advisory removed** — replaced with structured `perspectiveCoverage` field
   (both simplicity and architecture reviewers agreed free-text in alerts array is wrong).
5. **solitary-action plugin pattern** — `PerspectiveInventory` uses flat structure (like
   `TodaysTasks.omnifocusjs`), not the full AITaskAnalyzer bundle.
6. **Template data → `assets/templates/`** — `perspective_templates.json` in `assets/templates/`
   not `references/` (reference files have no YAML frontmatter; data files live in assets).
7. **Agent-native file output path** — plugin writes to `/tmp/of-perspective-inventory.json`
   alongside clipboard, enabling Claude to read results autonomously after user runs plugin.
8. **Security rules added to `code_generation_validation.md`** — string injection prevention,
   backup-before-write ordering, version guards, review-before-execute requirement.
9. **`essentials.json` in plugin Resources** — single source of truth for GTD-essential list
   (eliminates the two-file sync problem identified in original plan).
10. **`marketplace.json` added to file list** — explicit step when bumping to 6.2.0.

### New Considerations Discovered

- `omnifocus-extensions.d.ts` (not `omnifocus.d.ts`) is the correct file for augmenting existing
  types via declaration merging
- No existing reference file in the skill uses YAML frontmatter — only `SKILL.md` does
- The JSON envelope pattern for action outputs is `{success, action, count, <collection>}` with
  kebab-case action values (matching `gtd-queries.js` existing conventions)
- `system-health` currently has no "INFO" severity concept — adding one is a new capability
  that requires downstream consumers (gtd-coach, omnifocus-agent) to handle the new value
- Perspective navigation URLs are fire-and-forget — skill should phrase as "navigate to" not
  "open" and document that confirmation is not available

---

## Critical Architectural Finding (SpecFlow Analysis)

> **`Perspective.Custom.all` and `archivedFilterRules` are Omni Automation API — NOT accessible
> via JXA.**

The existing `gtd-queries.js` runs via `osascript -l JavaScript` (JXA). Perspective data lives
in the Omni Automation namespace. These are different runtimes — this is a hard API boundary,
not a preference.

**Consequence:** Perspective operations require a new `.omnifocusjs` plugin, not an extension
to `gtd-queries.js`.

**Data return path:** Omni Automation plugins cannot write to stdout. The established skill
pattern is `Pasteboard.general.string` (clipboard). For agent accessibility, the plugin also
writes a JSON file to `/tmp/of-perspective-inventory.json` — a parallel output path that Claude
can read after the user runs the plugin, without requiring a manual paste step.

---

## Problem Statement

- `perspective_creation.md` incorrectly states "perspectives cannot be created via scripting"
  — the `archivedFilterRules` API (v4.2+) enables full rule configuration once a blank
  perspective shell exists (one UI click).
- No inventory capability: Claude cannot list or describe a user's custom perspectives.
- No gap detection: Claude cannot identify which GTD-essential perspectives are missing.
- SKILL.md Pillar 2 entry says "Programmatic perspective creation" — needs accurate framing.
- `omnifocus-extensions.d.ts` is missing `archivedFilterRules` and
  `archivedTopLevelFilterAggregation` on `Perspective.Custom`.

---

## Proposed Solution

A five-deliverable implementation in three phases, ordered by dependency:

**Phase 1 — Architecture foundations** (enables everything else)
**Phase 2 — Templates and inventory** (knowledge + runtime layer)
**Phase 3 — Configuration UX + skill update** (user-facing capability)

---

## Technical Considerations

### Automation Channel Matrix

| Operation | Channel | How data returns to Claude |
|-----------|---------|---------------------------|
| `Perspective.Custom.all` query | Omni Automation plugin | Clipboard + `/tmp/of-perspective-inventory.json` |
| Read `archivedFilterRules` | Omni Automation plugin | Same as above |
| Write `archivedFilterRules` | Omni Automation console paste | Alert + `/tmp/of-perspective-config-result.json` |
| Navigate to perspective | `omnifocus:///perspective/<name>` URL | Fire-and-forget — cannot confirm view changed |
| `system-health` perspective data | JXA limitation | Structured `perspectiveCoverage` field in output JSON |

> **Fire-and-forget note:** Perspective navigation URLs open OmniFocus but return no confirmation.
> The skill must phrase navigation as "navigate to" not "open" and cannot confirm the view
> changed. Document explicitly in SKILL.md Channel Selection table.

### TypeScript Type Additions (Corrected)

**Target file: `omnifocus-extensions.d.ts`** (not the generated `omnifocus.d.ts`).
Uses `interface Custom` declaration merging — TypeScript supports augmenting a class declaration
via interface merging in a separate file; a second class declaration of the same name is invalid.

```typescript
// ============================================================================
// Perspective.Custom Extensions (OmniFocus 4.2+)
// ============================================================================

declare namespace Perspective {
    /**
     * A single filter rule within a custom perspective.
     * Schema is runtime-defined by OmniFocus (not publicly documented).
     * Known rule shapes are enumerated as discriminated union variants.
     * Unknown future rule shapes fall through to the base Record type.
     *
     * @since OmniFocus 4.2 (macOS and iOS)
     */
    type FilterRule =
        | { actionAvailability: "remaining" | "available" | "completed" | "dueSoon" | "overdue" }
        | { actionHasAnyOfTags: string[] }
        | Record<string, unknown>;
}

declare namespace Perspective {
    interface Custom {
        /**
         * Archived filter rules for this perspective.
         * Returns empty array `[]` on OmniFocus versions prior to 4.2.
         *
         * @since OmniFocus 4.2 (macOS and iOS)
         */
        archivedFilterRules: Perspective.FilterRule[];

        /**
         * Top-level aggregation operator applied across filter rules.
         * - `"any"`: matches tasks satisfying at least one rule
         * - `"all"`: matches tasks satisfying all rules
         * - `null`: not configured or OmniFocus prior to 4.2
         *
         * @since OmniFocus 4.2 (macOS and iOS)
         */
        archivedTopLevelFilterAggregation: "any" | "all" | null;
    }
}
```

### archivedFilterRules Schema Bootstrapping

The schema is not publicly documented. Templates must be bootstrapped from a real OmniFocus
perspective. Implementation order (**do not reverse**):

1. Run a minimal throwaway Omni Automation script against a real OmniFocus perspective:
   ```javascript
   (() => {
     const p = Perspective.Custom.all[0];
     Pasteboard.general.string = JSON.stringify({
       name: p.name,
       aggregation: p.archivedTopLevelFilterAggregation,
       rules: p.archivedFilterRules
     }, null, 2);
     new Alert("Schema captured", "Paste into editor to inspect.").show();
   })()
   ```
2. Inspect output → confirm actual key names and value types
3. Update `Perspective.FilterRule` union in `omnifocus-extensions.d.ts` with confirmed types
4. Author `perspective_templates.json` from confirmed schema — mark with OmniFocus version

> Template JSON must be validated against a running OmniFocus 4.2+ instance before publishing.
> Mark each template with the OmniFocus version it was bootstrapped from.

### Write Operation Safety

Every generated configuration script must follow this ordering (security requirement):

```javascript
(() => {
  // 1. Version guard — REQUIRED (before any perspective access)
  if (app.version < "4.2") {
    new Alert("Version Required", "This script requires OmniFocus 4.2+.").show();
    return;
  }

  // 2. Find perspective (equality check, not substring)
  const TARGET_NAME = "next actions"; // pre-serialized at generation time
  const p = Perspective.Custom.all.find(p => p.name.toLowerCase() === TARGET_NAME);
  if (!p) {
    new Alert("Not Found", `No perspective named "${TARGET_NAME}".`).show();
    return;
  }

  // 3. Backup BEFORE any write (required)
  Pasteboard.general.string = JSON.stringify({
    backup_for: p.name,
    timestamp: new Date().toISOString(),
    rules: p.archivedFilterRules
  }, null, 2);

  // 4. Write new configuration
  p.archivedFilterRules = [/* generated rules */];
  p.archivedTopLevelFilterAggregation = "all";

  // 5. Write result file for agent verification
  const result = {
    perspective: p.name,
    configuredAt: new Date().toISOString(),
    ruleCount: p.archivedFilterRules.length,
    aggregation: p.archivedTopLevelFilterAggregation,
    backupWritten: true
  };
  Data.fromString(JSON.stringify(result, null, 2))
      .write(URL.fromString("file:///tmp/of-perspective-config-result.json"));

  // 6. Confirm (after all writes complete)
  new Alert("Done", `${p.name} configured. Previous rules backed up to clipboard. Use Cmd-Z to undo.`).show();
})()
```

> **Security note:** `TARGET_NAME` must be JSON-serialized at Claude's code generation time —
> never raw-interpolated from user input. See `code_generation_validation.md` Rule 7a.

### Name Matching Strategy

- **Write path**: equality match (`.toLowerCase() ===`) — exact, no false positives
- **Inventory gap-detection**: case-insensitive substring matching with confidence levels:
  - `"exact"` — name matches essential name exactly (case-insensitive)
  - `"substring"` — name contains the essential name as a substring
  - `"missing"` — no match found

---

## System-Wide Impact

- **No JXA scripts affected** — all changes are new files or Omni Automation plugins
- **`system-health` action** — gains a structured `perspectiveCoverage` field (not a text alert):
  ```json
  "perspectiveCoverage": {
    "checked": false,
    "reason": "JXA cannot access Perspective.Custom",
    "action": "Run PerspectiveInventory plugin",
    "plugin": "assets/PerspectiveInventory.omnifocusjs"
  }
  ```
- **`omnifocus-extensions.d.ts`** — extended with `Perspective.FilterRule` type and two new
  properties on `Perspective.Custom`
- **`omnifocus-agent.md`** — needs a new routing entry for perspective intent
- **SKILL.md trigger phrases** — must be updated alongside Pillar 2 description
- **`marketplace.json`** — must be updated alongside `SKILL.md` version bump (pre-commit hook
  will catch drift but explicit step prevents reliance on the hook)

---

## Implementation Plan

### Phase 1: Architecture Foundations

**Step 1: Bootstrap `archivedFilterRules` schema empirically**

Before any TypeScript changes, run the bootstrap script above against a real OmniFocus 4.2+
instance. Inspect the clipboard output to confirm:
- Actual key names in filter rule objects
- Value types and valid value sets
- Whether `archivedTopLevelFilterAggregation` is `"any"` / `"all"` or other values

**Deliverable 1a: Update `omnifocus-extensions.d.ts`**

File: `plugins/omnifocus-manager/skills/omnifocus-manager/typescript/omnifocus-extensions.d.ts`

Add the `Perspective.FilterRule` type and `interface Custom` augmentation shown in the
TypeScript section above. Update the `FilterRule` union with confirmed schema variants from
step 1.

**Deliverable 1b: Update `perspective_creation.md`**

File: `plugins/omnifocus-manager/skills/omnifocus-manager/references/perspective_creation.md`

Changes:
- Remove the false statement at line 27: "Note: Perspectives cannot be created via scripting."
- Add new section `## Omni Automation API (v4.2+)` with:
  - `archivedFilterRules` read/write examples
  - Export/import JSON pattern
  - Version constraint (4.2+)
  - The one constraint: blank perspective shell required (one UI click: Perspectives → +)
  - Console-paste delivery pattern for configuration scripts
- Update Resources section to reference `../assets/templates/perspective_templates.json`

---

### Phase 2: Templates and Inventory

**Deliverable 2a: `assets/templates/perspective_templates.json`**

New file: `plugins/omnifocus-manager/skills/omnifocus-manager/assets/templates/perspective_templates.json`

> **Why `assets/templates/` not `references/`**: All reference files in `references/` start
> with a bare `# Heading` — no YAML frontmatter. The machine-readable essential-list data
> belongs in `assets/templates/` alongside `task_templates.json` (existing precedent).

Structure:
```json
{
  "bootstrapped_from_version": "4.x.x",
  "bootstrapped_date": "2026-xx-xx",
  "essential_perspectives": [
    "Next Actions",
    "Waiting For",
    "Stalled Projects",
    "Due This Week",
    "Someday Maybe"
  ],
  "templates": [
    {
      "name": "Next Actions",
      "purpose": "Available tasks not blocked, grouped by tag/context",
      "archivedTopLevelFilterAggregation": "all",
      "archivedFilterRules": [
        { "actionAvailability": "available" }
      ],
      "ui_prerequisite": "Perspectives → + → name it 'Next Actions'",
      "navigation_url": "omnifocus:///perspective/Next%20Actions"
    }
  ]
}
```

Start with 5 essential perspectives (Next Actions, Waiting For, Stalled Projects, Due This Week,
Someday/Maybe). Do not add "Weekly Review", "Flagged + Available", "Focus: High Priority" on the
first pass — these overlap with OmniFocus built-in perspectives and require more schema work.

**Deliverable 2b: `PerspectiveInventory.omnifocusjs` plugin**

New plugin: `plugins/omnifocus-manager/skills/omnifocus-manager/assets/PerspectiveInventory.omnifocusjs/`

**Use solitary-action pattern** (like `TodaysTasks.omnifocusjs`, not the full AITaskAnalyzer bundle):
```
PerspectiveInventory.omnifocusjs/
├── manifest.json
└── Resources/
    ├── essentials.json        ← single source of truth for GTD-essential list
    └── copyPerspectives.js    ← action file (name matches action identifier)
```

**`manifest.json`**:
```json
{
  "author": "totally-tools",
  "targets": ["com.omnigroup.OmniFocus4"],
  "identifier": "com.totallytools.omnifocus.perspective-inventory",
  "version": "1.0",
  "description": "Inventory all custom perspectives and identify missing GTD essentials.",
  "actions": [
    {
      "identifier": "copyPerspectives",
      "label": "Copy Perspective Inventory"
    }
  ]
}
```

**`essentials.json`** (single source of truth — the plugin reads this at runtime):
```json
["Next Actions", "Waiting For", "Stalled Projects", "Due This Week", "Someday Maybe"]
```

**`copyPerspectives.js`** logic:
```javascript
(() => {
  const action = new PlugIn.Action(async function(selection) {
    // 1. Version guard
    if (app.version < "4.2") {
      new Alert("Version Required", "Requires OmniFocus 4.2+.").show();
      return;
    }

    // 2. Load essentials list
    const essentialsUrl = this.library.url.appendingPathComponent('../essentials.json');
    // (or hardcode from manifest — adjust based on plugin loading mechanics confirmed at runtime)
    const essentialNames = ["Next Actions", "Waiting For", "Stalled Projects", "Due This Week", "Someday Maybe"];

    // 3. Enumerate perspectives
    const perspectives = Perspective.Custom.all.map(p => {
      const match = essentialNames.find(e =>
        p.name.toLowerCase() === e.toLowerCase()
          ? "exact"
          : p.name.toLowerCase().includes(e.toLowerCase())
            ? "substring"
            : null
      );
      return {
        name: p.name,
        url: `omnifocus:///perspective/${encodeURIComponent(p.name)}`,
        filterRuleCount: p.archivedFilterRules?.length ?? 0,
        filterAggregation: p.archivedTopLevelFilterAggregation,
        gtdMatch: match || null,
        matchConfidence: match ? (p.name.toLowerCase() === (match||"").toLowerCase() ? "exact" : "substring") : null
      };
    });

    const presentNames = perspectives.filter(p => p.gtdMatch).map(p => p.gtdMatch);
    const missingEssentials = essentialNames.filter(e =>
      !perspectives.some(p => p.name.toLowerCase().includes(e.toLowerCase()))
    );

    const output = {
      success: true,
      action: "perspective-inventory",
      count: perspectives.length,
      perspectives,
      missing_essentials: missingEssentials,
      present_essentials: presentNames
    };

    // 4a. Write to clipboard (human path)
    Pasteboard.general.string = JSON.stringify(output, null, 2);

    // 4b. Write to /tmp for agent path
    Data.fromString(JSON.stringify(output, null, 2))
        .write(URL.fromString("file:///tmp/of-perspective-inventory.json"));

    // 5. Confirm
    const alert = new Alert(
      "Perspective Inventory",
      `${perspectives.length} perspectives copied to clipboard.\nMissing essentials: ${missingEssentials.length || "none"}`
    );
    alert.addOption("Done");
    await alert.show();
  });
  action.validate = function(selection) { return true; };
  return action;
})();
```

**Agent workflow**: Install plugin → user runs "Copy Perspective Inventory" in OmniFocus →
Claude reads `/tmp/of-perspective-inventory.json` via Bash OR user pastes clipboard.

**Deliverable 2c: Enhance `system-health` in `gtd-queries.js`**

Replace the proposed free-text advisory string with a structured field in the health output JSON:

```javascript
// In getSystemHealth(), add to the returned object (not to alerts array):
perspectiveCoverage: {
  checked: false,
  reason: "JXA cannot access Perspective.Custom",
  action: "Run PerspectiveInventory plugin",
  plugin: "assets/PerspectiveInventory.omnifocusjs"
}
```

Health score unchanged. No deduction for an unchecked domain.

> **Why structured, not text alert:** The existing `alerts` array deducts from score. There is
> no "INFO" severity concept in the current implementation. Adding a structured sibling field
> avoids introducing a new severity tier while making the gap machine-readable for
> omnifocus-agent routing.

---

### Phase 3: Configuration UX + Skill Update

**Deliverable 3a: Perspective configuration script generator (skill behavior)**

No new script file. This is skill behavior documented in SKILL.md.

When user describes a desired perspective configuration:
1. Claude checks if perspective exists (ask user to run PerspectiveInventory or confirm name)
2. Claude emits the configuration script (see Write Operation Safety section above)
   - Must include version guard, backup-before-write, `/tmp` result file, Alert
   - `TARGET_NAME` must be pre-serialized (never raw-interpolated from user input)
   - Script must not access `flattenedTasks` or other task-content globals
3. Script is shown as a **code block for manual paste** into OmniFocus Automation Console
   (never as an `omnijs-run` URL — see `code_generation_validation.md` Rule 7d)
4. After user runs script, Claude can verify via `cat /tmp/of-perspective-config-result.json`

**Deliverable 3b: Update `omnifocus-agent.md`**

File: `plugins/omnifocus-manager/agents/omnifocus-agent.md`

Add perspective intent row to the routing/classification table:
```
"what perspectives do I have", "list perspectives", "inventory perspectives",
"missing perspectives", "perspective gap", "create a perspective", "configure perspective"
→ Route to: PerspectiveInventory plugin workflow (run plugin → read /tmp file)
```

**Deliverable 3c: Update `code_generation_validation.md`**

File: `plugins/omnifocus-manager/skills/omnifocus-manager/references/code_generation_validation.md`

Add Section 7: Perspective Script Generation Safety with rules:
- **Rule 7a** — String literal injection prevention: JSON.stringify perspective names at generation
- **Rule 7b** — Backup must precede write: `Pasteboard =` appears before `archivedFilterRules =`
- **Rule 7c** — Version guard required: `if (app.version < "4.2") { ... return; }`
- **Rule 7d** — Scripts shown as code blocks for review, never auto-executed via `omnijs-run` URL
- **Rule 7e** — Scripts must not access `flattenedTasks`, `flattenedProjects`, or task content

**Deliverable 3d: Update SKILL.md**

File: `plugins/omnifocus-manager/skills/omnifocus-manager/SKILL.md`

Changes:
1. **Frontmatter `description`** — add trigger phrases (comma-separated, matching existing style):
   `"what perspectives do I have", "list perspectives", "perspective inventory",
   "missing perspectives", "configure perspective", "create a perspective"`

2. **Four-Pillar table** — update Pillar 2 row:
   - Old: `"Programmatic perspective creation"`
   - New: `"Perspective inventory, gap detection, and guided configuration (v4.2+)"`

3. **Pillar 2 section** — add content explaining:
   - PerspectiveInventory plugin workflow (install → run → Claude reads `/tmp` or paste)
   - Guided configuration workflow (describe in English → get console-paste script)
   - One constraint: blank perspective shell required for new perspectives (one UI click)
   - Templates reference: `assets/templates/perspective_templates.json`
   - Navigation URLs are fire-and-forget — phrase as "navigate to", not "open"

4. **Channel Selection table** — add note to `omnifocus:///perspective/<name>` row:
   `"Fire-and-forget — agent cannot confirm view changed. Phrase as 'navigate to', not 'open'."`

5. **Channel Selection table** — add explicit prohibition:
   `"Perspective write scripts must NEVER be delivered as omnijs-run URLs — console paste only"`

6. **References section** — add `perspective_templates.json` and `code_generation_validation.md`
   links with contextual description (both must be mentioned where relevant in the skill body)

---

## Acceptance Criteria

- [ ] Schema bootstrapped from real OmniFocus 4.2+ perspective before TypeScript types are authored
- [ ] `omnifocus-extensions.d.ts` updated with `Perspective.FilterRule` union type and `interface Custom` augmentation
- [ ] TypeScript validation pass run after type additions (do not add types and skip validation)
- [ ] `perspective_creation.md` updated — outdated constraint removed, v4.2+ section added
- [ ] `assets/templates/perspective_templates.json` created with 5 essential perspectives (bootstrapped schema, version-tagged)
- [ ] `PerspectiveInventory.omnifocusjs` created using solitary-action pattern with `essentials.json` as single source of truth
- [ ] Plugin writes to both clipboard and `/tmp/of-perspective-inventory.json`
- [ ] `system-health` in `gtd-queries.js` gains structured `perspectiveCoverage` field (not text advisory)
- [ ] `omnifocus-agent.md` routing table updated with perspective intent entries
- [ ] `code_generation_validation.md` updated with Rules 7a–7e
- [ ] SKILL.md Pillar 2 description, trigger phrases, Channel Selection notes updated
- [ ] Every new/modified reference file mentioned contextually in SKILL.md
- [ ] `validate-plugin.sh` run against `PerspectiveInventory.omnifocusjs` — zero failures
- [ ] Skillsmith evaluation run and score recorded in `IMPROVEMENT_PLAN.md`
- [ ] `marketplace.json` updated alongside SKILL.md version bump to 6.2.0
- [ ] Version in SKILL.md, IMPROVEMENT_PLAN.md, and marketplace.json all read `6.2.0` (no pre-release suffix)

---

## Dependencies & Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `archivedFilterRules` schema differs from inference | Medium | Bootstrap empirically (Phase 1, Step 1) before writing any types or templates |
| TypeScript types authored before schema confirmed | High if Phase 1 reversed | Phase 1 order is mandatory: bootstrap → types → templates |
| User on OmniFocus < 4.2 | Low | Version guard in every script; clear error message |
| Template JSON becomes stale across OF versions | Low | Version-tag all templates; mark as user-bootstrapped, not canonical |
| `/tmp` file not writable in OmniFocus sandbox | Medium | Test at implementation time; fall back to clipboard-only if blocked |
| Perspective name collision (two with same name) | Low | Script uses `find()` and warns if the found name differs from target |
| GTD-essential list in two places | Fixed | `essentials.json` in plugin Resources is the single source; `perspective_templates.json` lists names but is not consumed by the plugin |
| marketplace.json version drift | Low | Pre-commit hook catches it; explicit step in acceptance criteria as belt-and-suspenders |

---

## Files to Create / Modify

| File | Action | Notes |
|------|--------|-------|
| `typescript/omnifocus-extensions.d.ts` | Modify | Add `Perspective.FilterRule` type + `interface Custom` augmentation |
| `references/perspective_creation.md` | Modify | Remove outdated constraint; add v4.2+ section |
| `assets/templates/perspective_templates.json` | Create | 5 GTD perspective templates, bootstrapped schema, version-tagged |
| `assets/PerspectiveInventory.omnifocusjs/manifest.json` | Create | Identifier: `com.totallytools.omnifocus.perspective-inventory` |
| `assets/PerspectiveInventory.omnifocusjs/Resources/essentials.json` | Create | 5-item list — single source of truth |
| `assets/PerspectiveInventory.omnifocusjs/Resources/copyPerspectives.js` | Create | Inventory logic; outputs to clipboard + `/tmp/of-perspective-inventory.json` |
| `scripts/gtd-queries.js` | Modify | Add `perspectiveCoverage` structured field to `getSystemHealth()` return |
| `agents/omnifocus-agent.md` | Modify | Add perspective intent routing row |
| `references/code_generation_validation.md` | Modify | Add Rules 7a–7e (perspective script safety) |
| `SKILL.md` | Modify | Trigger phrases, Pillar 2 section, Channel Selection notes, references |
| `IMPROVEMENT_PLAN.md` | Modify | Add v6.2.0 entry with skillsmith score |
| `marketplace.json` (root) | Modify | Update omnifocus-manager version to 6.2.0 |

---

## Post-Implementation

**Step 1: Validate plugin**
```bash
bash plugins/omnifocus-manager/skills/omnifocus-manager/scripts/validate-plugin.sh \
  plugins/omnifocus-manager/skills/omnifocus-manager/assets/PerspectiveInventory.omnifocusjs
```
Zero failures required before proceeding.

**Step 2: Run skillsmith evaluation**
```bash
uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py \
  plugins/omnifocus-manager/skills/omnifocus-manager \
  --export-table-row --version 6.2.0 --issue 80
```
Record score in `IMPROVEMENT_PLAN.md` version history entry.

**Step 3: Verify version consistency**
Confirm `SKILL.md`, `IMPROVEMENT_PLAN.md`, and `marketplace.json` all show `6.2.0`.

---

## Sources & References

- Issue #80: feat(omnifocus-manager): Pillar 2 perspective understanding
- Issue #63: Two-track vision — parent issue with four-pillar architecture
- [Omni Automation perspective docs](https://www.omni-automation.com/omnifocus/perspective.html) — v4.2+ `archivedFilterRules` API
- `references/perspective_creation.md` — needs update (outdated constraint at line 27)
- `references/omnifocus_url_scheme.md` — perspective URL linking already documented
- `references/code_generation_validation.md` — add Rules 7a–7e in this implementation
- `scripts/gtd-queries.js` — 10-action JXA diagnostic runner (NOT extended for perspectives)
- `assets/AITaskAnalyzer.omnifocusjs` — established Omni Automation bundle pattern reference
- `assets/TodaysTasks.omnifocusjs` — solitary-action plugin pattern (use this simpler pattern)
- `assets/templates/task_templates.json` — template data file pattern in `assets/templates/`
- `typescript/omnifocus-extensions.d.ts` — correct file for type augmentation (not generated `omnifocus.d.ts`)
- `docs/solutions/agent-design/omnifocus-manager-automation-decision-framework.md` — channel routing, reference placement rules, TypeScript validation pipeline
- `docs/solutions/logic-errors/multi-skill-plugin-version-sync.md` — marketplace.json sync requirement, X.Y.Z version format
