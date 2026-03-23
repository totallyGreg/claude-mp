---
title: "feat: Attache GTD Phase Mapping, Gap Analysis & Display Polish"
type: feat
status: active
date: 2026-03-22
---

# feat: Attache GTD Phase Mapping, Gap Analysis & Display Polish

## Overview

Rename Attache's 7 remaining actions to reflect GTD phases, close two confirmed
functionality gaps, fix a critical runtime crash, and standardize Alert display
formatting across all actions. Produces Attache v1.4.0.

## Problem Statement

After consolidating from 9 → 7 actions, the set needs alignment work in three areas:

1. **Names are technical, not GTD-vocabulary.** "Analyze Hierarchy" and "Analyze
   Selected" tell the user nothing about what GTD phase they support.
2. **Two functionality gaps** exist: Waiting-For detection patterns are duplicated
   with inconsistent membership across files; `analyzeSelected` lacks a GTD coaching
   persona, making its FM output generic rather than GTD-aligned.
3. **Display is inconsistent.** `ALLCAPS:` headers, mixed bullet styles (`-` / `•` /
   `→`), a `=`.repeat(40) separator, and no visual rhythm across actions.
4. **One critical runtime bug**: `analyzeHierarchy.js` crashes at the aggregation step
   due to a `this` reference inside a standalone function.

## GTD Phase Mapping

### Current → Proposed Labels

The `"Attache: "` prefix is **required** — it prevents alphabetical scattering in the
OmniFocus Automation menu, where all plug-in actions appear flat and ungrouped.
Identifiers (and JS filenames) are **not renamed** to minimize blast radius.

| Identifier | Current Label | Proposed Label | GTD Phase |
|---|---|---|---|
| `dailyReview` | Attache: Daily Review | **Attache: Daily Review** | Reflect + Engage |
| `weeklyReview` | Attache: Weekly Review | **Attache: Weekly Review** | Reflect (all phases) |
| `analyzeSelected` | Attache: Analyze Selected | **Attache: Clarify Tasks** | Clarify |
| `analyzeHierarchy` | Attache: Analyze Hierarchy | **Attache: Project Health** | Reflect (Organize) |
| `completedSummary` | Attache: Completed Summary | **Attache: Wins Report** | Reflect (Celebrate) |
| `systemSetup` | Attache: System Setup | **Attache: Setup** | Infrastructure |
| `discoverSystem` | Attache: Discover System | **Attache: Map System** | Infrastructure |

### GTD Phase Coverage After Rename

| GTD Phase | Action(s) | Verdict |
|---|---|---|
| **Capture** | ofo CLI (intentional) | ✅ No Attache action needed |
| **Clarify** | Clarify Tasks (analyzeSelected) | ✅ Per-task AI analysis, 1–5 tasks |
| **Organize** | ofo CLI + Weekly Review Step 1 | ✅ Inbox processing is CLI territory |
| **Reflect** | Daily Review · Weekly Review · Project Health · Wins Report | ✅ Comprehensive |
| **Engage** | Daily Review (Top Next Actions section) | ⚠️ See Gap 1 |

## Gap Analysis

### Gap 1: Engage Phase — Dedicated "What next?" Action (Deferred)

**Status:** Intentionally deferred. The removed `analyzeTasksWithAI` was the Engage
action but overlapped Daily Review's Top Next Actions too heavily. The correct fix is
to enrich Daily Review's AI prompt with context/energy/time framing (GTD's four
engagement criteria) rather than adding a new action.

**Future iteration:** Enhance `dailyReview.js` prompt to explicitly ask FM to filter
top actions by `@context`, available time block, and energy level when `systemMap` is
cached (cached tags expose the user's actual context names).

### Gap 2: Waiting-For Detection Inconsistency (Fix in Phase 2)

Two files independently define "waiting for" tag patterns with different members:

| File | Constant | Patterns |
|---|---|---|
| `weeklyReview.js:30` | `WAITING_PATTERNS` | `["waiting", "delegated", "pending", "w:"]` |
| `systemDiscovery.js` | `WAITING_PREFIXES` | `["waiting:", "w:", "delegate:"]` |

**Fix:**
- Add `WAITING_PATTERNS = ["waiting", "delegated", "pending", "w:"]` to `taskMetrics.js`
  as an exported constant on the library object.
- Move `isWaitingFor()` in `weeklyReview.js` **inside** the action handler body (where
  `this.plugIn` is available) and reference `metrics.WAITING_PATTERNS`.
- Update `systemDiscovery.js` to align its prefix array with the canonical list.

### Gap 3: analyzeSelected Lacks GTD Coaching Persona (Fix in Phase 2)

`analyzeSelected.js` calls `fmUtils.createSession()` with no system prompt. The FM
output is generic — it has no GTD vocabulary or next-action framing.

`foundationModelsUtils.createSession(systemPrompt)` already accepts an optional system
prompt (verified in `foundationModelsUtils.js:92`). No library change needed.

**Fix:** Pass GTD system prompt identical to dailyReview/weeklyReview:
```javascript
const session = fmUtils.createSession(
    "You are a GTD productivity coach. Be concise and direct. Use specific GTD " +
    "vocabulary: next actions, projects, contexts. Focus on what is actionable right now."
);
```

### Gap 4: Token Budgets Not Standardized (Fix in Phase 2)

| Action | `maximumResponseTokens` |
|---|---|
| `dailyReview` | 300 |
| `weeklyReview` | 250 (per step) |
| `analyzeSelected` | ❌ default (unbounded) |
| `analyzeHierarchy` | ❌ default (per batch) |

**Fix:** Set explicit budgets in `analyzeSelected` (400 per task — richer per-task
analysis than a daily review) and note in `hierarchicalBatcher.js` that per-batch
token budget should be added when schemas are generated.

## Bug Fixes

### Bug 1: `analyzeHierarchy.js` — `this` Binding Crash (Critical)

**Location:** `analyzeHierarchy.js`, `aggregateInsights()` standalone function, ~line 271

```javascript
// WRONG: `this` is undefined inside a standalone function
function aggregateInsights(results, parsedData, depthLevel) {
    const metrics = this.plugIn.library("folderParser")  // ← TypeError at runtime
        .aggregateMetrics(parsedData.folders);
```

**Fix:** Hoist the `folderParser` reference from the action closure and pass it as a
parameter. The action body already loads `folderParser` via `this.plugIn.library()`:

```javascript
// In action body (where `this` is correctly bound):
const folderParser = this.plugIn.library("folderParser");
// ...
const aggregatedInsights = aggregateInsights(results, parsedData, depthLevel, folderParser);

// Updated function signature:
function aggregateInsights(results, parsedData, depthLevel, folderParser) {
    const metrics = folderParser.aggregateMetrics(parsedData.folders);
    // ...
}
```

### Bug 2: `systemDiscovery.js` — Stale Version Constant (Minor)

`ATTACHE_VERSION = "1.3.0"` inside `systemDiscovery.js` is behind manifest `1.3.1`
(and will fall further behind after this plan's `1.4.0` bump).

**Fix:** Update to `"1.4.0"` or remove the constant entirely (it is not referenced
externally and the preference cache already writes `lastWritten` timestamp).

## Display Standard

### Proposed Alert Body Format

OmniFocus Alert dialogs render plain monospace text. Replace `ALLCAPS:` section headers
with Unicode section dividers for visual rhythm without markdown.

**Section divider pattern:**
```
── Section Name ───────────────────────────
```
Total width ~44 chars. Implementation as an inline helper in each action's IIFE:

```javascript
function section(title) {
    const pad = '─'.repeat(Math.max(0, 44 - title.length - 4));
    return `── ${title} ${pad}`;
}
```

**Full example — Daily Review body (before/after):**

Before:
```
WINS TODAY:
Finished quarterly review

TOP NEXT ACTIONS:
1. Draft client proposal
   > Highest value today
STATS: 3 done | 5 today | 2 overdue | 1 flagged | 4 inbox
```

After:
```
── Wins Today ─────────────────────────────
Finished quarterly review

── Top Next Actions ───────────────────────
1. Draft client proposal
   → Highest value today

──────────────────────────────────────────
✅ 3 done · 📋 5 today · ⚠️ 2 overdue · 🚩 1 flagged · 📥 4 inbox
```

**Display rules (apply uniformly across all 7 actions):**

| Element | Before | After |
|---|---|---|
| Section header | `HEADER:\n` | `── Header ──────────────────────────────\n` |
| Bullet item | `  - text` or `  • text` | `  · text` (U+00B7 middle dot) |
| Numbered sub-line | `   > reason` | `   → reason` (consistent arrow) |
| Task separator | `'='.repeat(40)` | `'─'.repeat(44)` |
| Stats footer | `STATS: N done \| N today \|…` | `──────…\n✅ N done · 📋 N today · ⚠️ N overdue · 🚩 N flagged · 📥 N inbox` |
| Truncation | `  ... and N more` | `  ··· and N more` |
| Alert title | Mixed (`"AI Task Analysis"`, `"Attache: X"`) | Always `"Attache: {Menu Label}"` |

**Weekly Review step Alerts:** Keep `"Step N of 7: {Name}"` title pattern — it provides
clear progress framing. Apply section dividers to the body only.

**Markdown copy format (dailyReview clipboard):** Already good — keep `## Header`,
`> blockquote`, and backtick project names. No changes.

## Implementation Phases

### Phase 1: Manifest Renames (manifest.json) — ~5 min

- Update 5 action `label` fields per the mapping table above
- Bump `"version"` from `"1.3.1"` → `"1.4.0"`
- Daily Review and Weekly Review labels unchanged

### Phase 2: Bug Fixes & Gap Closures — ~45 min

**`analyzeHierarchy.js`**
- Add `folderParser` parameter to `aggregateInsights()` signature
- Pass `folderParser` from action body at call site
- Remove `this.plugIn` reference from `aggregateInsights()`

**`taskMetrics.js`**
- Add `lib.WAITING_PATTERNS = ["waiting", "delegated", "pending", "w:"];` before `return lib`

**`weeklyReview.js`**
- Move `isWaitingFor()` function inside the action handler (after `const metrics = this.plugIn.library("taskMetrics")`)
- Replace hardcoded `WAITING_PATTERNS` array with `metrics.WAITING_PATTERNS`

**`analyzeSelected.js`**
- Add GTD system prompt string to `fmUtils.createSession(...)` call
- Add `const opts = new LanguageModel.GenerationOptions(); opts.maximumResponseTokens = 400;` and pass to `respondWithSchema(prompt, schema, opts)`

**`systemDiscovery.js`**
- Update `ATTACHE_VERSION` constant to `"1.4.0"` (or remove)
- Align `WAITING_PREFIXES` / `WAITING_PATTERNS` with `taskMetrics` canonical list

### Phase 3: Display Polish — ~60 min

Add `section()` helper inline to each action's IIFE. Apply to each file:

| File | Sections to update |
|---|---|
| `dailyReview.js` | `WINS TODAY:`, `TOP NEXT ACTIONS:`, `OVERDUE TRIAGE:`, `NEWLY AVAILABLE:`, stats footer |
| `weeklyReview.js` | `INBOX:`, `STALLED PROJECTS:`, `WAITING FOR:`, `SOMEDAY/MAYBE:`, `COMPLETED THIS WEEK:`, `OVERDUE:`, `DUE NEXT 7 DAYS:`, `REVIEW SUMMARY:`, `TOP PRIORITIES THIS WEEK:`, `SYSTEM HEALTH:` |
| `analyzeSelected.js` | `TASK:` header, `=`.repeat(40) separator, `Clarity Score:`, section labels |
| `analyzeHierarchy.js` | Alert body path (non-markdown mode) |
| `completedSummary.js` | Project group headers, overall header |
| `systemSetup.js` | Confirmation alert body |
| `discoverSystem.js` | `showSummaryAlert()` body |

Normalize all Alert titles to match the new menu labels:
- `"AI Task Analysis"` → `"Attache: Clarify Tasks"`
- `"System Discovery Results"` → `"Attache: Map System"`
- `"Analysis Complete"` → `"Attache: Project Health"`

## Acceptance Criteria

- [ ] `manifest.json`: 5 labels updated, version is `1.4.0`
- [ ] `analyzeHierarchy.js`: `aggregateInsights()` receives `folderParser` as parameter; no `this.plugIn` reference inside the function
- [ ] `taskMetrics.js`: `lib.WAITING_PATTERNS` exported and accessible from action files
- [ ] `weeklyReview.js`: `isWaitingFor()` defined inside action handler using `metrics.WAITING_PATTERNS`
- [ ] `systemDiscovery.js`: waiting patterns aligned with `taskMetrics` canonical list
- [ ] `analyzeSelected.js`: `fmUtils.createSession("…GTD coach prompt…")` with explicit prompt; `maximumResponseTokens = 400` set
- [ ] All 7 action Alert bodies use `── Section ──────` dividers; no `ALLCAPS:` headers remain
- [ ] `=`.repeat(40) separator in `analyzeSelected` replaced with `─`.repeat(44)
- [ ] All Alert titles match `"Attache: {New Menu Label}"` pattern
- [ ] `systemDiscovery.js` version constant updated to `1.4.0` or removed
- [ ] Plugin installs and all 7 actions launch without console errors in OmniFocus

## Files Changed

| File | Change Type | Summary |
|---|---|---|
| `manifest.json` | Rename + version | 5 labels, bump to 1.4.0 |
| `analyzeHierarchy.js` | Bug fix + display | Fix `this` binding; section headers |
| `taskMetrics.js` | Gap fix | Export `WAITING_PATTERNS` constant |
| `weeklyReview.js` | Gap fix + display | Use shared patterns; section headers |
| `analyzeSelected.js` | Gap fix + display | Add system prompt; token budget; section headers |
| `dailyReview.js` | Display | Section headers, stats footer |
| `completedSummary.js` | Display | Project group headers |
| `systemSetup.js` | Display | Confirmation alert body |
| `discoverSystem.js` | Bug fix + display | Version constant; waiting patterns; alert body |

## Risks & Notes

- **Unicode rendering:** Verify `─` (U+2500) renders correctly in OmniFocus Alert dialogs
  on macOS. If not, fall back to `-`.repeat(44).
- **`WAITING_PATTERNS` in library context:** `PlugIn.Library` exports only what is
  explicitly attached to `lib`. Verify `metrics.WAITING_PATTERNS` is accessible from
  action files before shipping.
- **`isWaitingFor()` scope change:** Moving it inside the action handler means it is
  re-defined on each action invocation. Negligible cost; correct tradeoff for library
  access.
- **No test harness:** Smoke test each action manually after each phase. Automated
  testing is a known gap (tracked separately).
- **File save / clipboard:** `saveToFile` remains a deliberate non-feature per
  architecture spec. No change.

## Sources & References

- `assets/Attache.omnifocusjs/manifest.json` — current labels and identifiers
- `assets/Attache.omnifocusjs/Resources/analyzeHierarchy.js:271` — `this` binding bug
- `assets/Attache.omnifocusjs/Resources/weeklyReview.js:30` — `WAITING_PATTERNS` definition
- `assets/Attache.omnifocusjs/Resources/taskMetrics.js` — target for shared constant
- `assets/Attache.omnifocusjs/Resources/foundationModelsUtils.js:92` — `createSession(systemPrompt)` signature confirmed
- `docs/plans/2026-03-08-feat-attache-omnifocus-unified-plugin-plan.md` — FM patterns, action label prefix requirement, architecture spec
- `docs/plans/2026-03-22-005-feat-attache-gtd-audit-superseded-cleanup-plan.md` — v1.3.0 state, `saveToFile` deliberate exclusion
- `docs/solutions/agent-design/omnifocus-manager-automation-decision-framework.md` — JXA anti-patterns, Attache + ofo CLI boundary
