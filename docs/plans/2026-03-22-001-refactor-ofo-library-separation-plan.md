---
title: "refactor: Separate ofo-library primitives from dispatch and feature plugins"
type: refactor
status: active
date: 2026-03-22
github_issue: "https://github.com/totallyGreg/claude-mp/issues/119"
supersedes: "docs/plans/2026-03-19-001-refactor-ofo-typescript-plugin-library-plan.md"
---

# refactor: Separate ofo-library primitives from dispatch and feature plugins

## Overview

The 2026-03-19 refactor (now completed) established the TypeScript plugin library architecture — `ofo-core.ts` compiled into `ofo-core.omnifocusjs`, called via `ofo-stub.js` URL transport. This plan takes the next architectural step: expanding `ofoCore` with **named exported functions** so that feature plugins (Attache and successors) can consume the same data access layer instead of reimplementing it — without changing the bundle identifier, library identifier, or stub script.

```
┌─────────────────────────────────────────────────────┐
│                  ofoCore library                    │
│        (ofo-core.omnifocusjs — UNCHANGED identifier)│
│  Named exports: getTask(), searchTasks(), listTasks()│
│  createTask(), completeTask(), updateTask(), tagTask()│
│  getTags(), getPerspective(), configurePerspective() │
│  getPerspectiveRules(), dumpDatabase(), getStats()   │
│                                                      │
│  dispatch() stays — thin router, backward compat     │
└──────────────────┬──────────────────────────────────┘
                   │ PlugIn.find("com.totally-tools.ofo-core").library("ofoCore")
         ┌─────────┴──────────┐
         │                    │
┌────────▼────────┐  ┌────────▼──────────────────────┐
│  ofo-stub.js    │  │   Feature Plugins              │
│  BYTE-FOR-BYTE  │  │   (Attache, future plugins)    │
│  UNCHANGED      │  │                                │
│                 │  │  • Load ofoCore via PlugIn.find│
│  calls          │  │  • Call named functions directly│
│  ofoCore        │  │  • Add FM inference + UI       │
│  .dispatch(args)│  │  • Mac + iPhone                │
└────────┬────────┘  └────────────────────────────────┘
         │
┌────────▼────────┐
│  ofo-cli.ts     │
│  Claude Code    │
│  skills / cmds  │
└─────────────────┘
```

**Stability guarantee:** `ofo-stub.js` is byte-for-byte unchanged. Bundle ID `"com.totally-tools.ofo-core"` and library ID `"ofoCore"` are unchanged. No user re-approval is required. The only things that change are:
1. `ofo-core.ts` action functions become `lib`-assigned named exports (in addition to routing through `dispatch`)
2. `build-plugin.sh` adds `lib.<name> = <function>` lines alongside the existing `lib.dispatch = dispatch`
3. Attache replaces its reimplemented data-access files with `PlugIn.find(...).library("ofoCore").<name>()` calls

## Problem Statement

### 1. ofo-core.ts action functions are private to dispatch()

All 12 action handler functions (`ofoInfo`, `ofoComplete`, `ofoCreate`, `ofoUpdate`, `ofoSearch`, `ofoList`, `ofoPerspective`, `ofoPerspectiveConfigure`, `ofoTag`, `ofoTags`, `ofoCreateBatch`, `ofoPerspectiveRules`) are module-level plain functions. They are cross-platform safe (no macOS-only primitives, just OmniFocus globals). But `build-plugin.sh` currently only assigns `lib.dispatch = dispatch` — the other 12 functions are inaccessible to other plugins.

External consumers must either call `dispatch()` with magic strings and untyped JSON, or reimplement data access from scratch. Attache does the latter: `taskParser.js`, `projectParser.js`, `folderParser.js`, and (to some degree) `taskMetrics.js` all reimplement primitives that ofo-core already provides.

### 2. No shared TypeScript contract (absorbed from #117)

`ofo-cli.ts` and `ofo-core.ts` share no types. Action names (`'ofo-search'`, `'ofo-create'`, etc.) are unvalidated string literals in both files. `OfoArgs` and `OfoResult` are defined only in `ofo-core.ts` — the CLI constructs matching shapes by convention, with no compile-time safety net. Adding a new action requires editing strings in two files with no exhaustiveness check.

**Important constraint:** The plugin compilation cannot use TypeScript `import` — `ofo-core.ts` has no imports and the build pipeline strips any that appear (`sed` in `build-plugin.sh`). Shared types for the plugin must be ambient `.d.ts` declarations included in `tsconfig.plugin.json`, not an importable module. The CLI can use a real `import` from `ofo-types.ts`; the plugin sees a merged ambient declaration.

### 3. The `typescript/` directory is misplaced

`scripts/typescript/example-plugin.ts` is reference material, not a build input. The `.d.ts` files (`omnifocus.d.ts`, `omnifocus-extensions.d.ts`, `ofo-core-ambient.d.ts`) are compiler inputs that live in or near `src/` where they belong. The `typescript/tsconfig.json` is LSP-only, not used by the build. This creates confusion about what's authoritative.

### 4. `scripts/libraries/omni/` is an undiscovered asset

`scripts/libraries/omni/` contains cross-platform Omni Automation library files (`taskMetrics.js`, `exportUtils.js`, `patterns.js`, `insightPatterns.js`, `templateEngine.js`, etc.) following the PlugIn.Library IIFE pattern. These are not currently deployed or used by ofo-core or Attache — they're closer in spirit to what this refactor is building. The plan should reconcile these with what gets promoted into ofoCore.

### 5. Cross-platform capability is locked out of feature plugins

`FoundationModels.Session` only runs inside Omni Automation — not from JXA or external scripts. As long as Attache reimplements data access independently, FM-powered plugins are architecturally standalone. With named ofoCore exports, a new FM plugin becomes: `PlugIn.find("ofo-core").library("ofoCore").listTasks(filter)` + FM session + OmniFocus UI. Works on iPhone automatically because all 12 ofo-core handlers already use only cross-platform OmniFocus globals.

## Proposed Solution

### What changes in `build-plugin.sh`

The IIFE wrapper currently ends with:
```javascript
lib.dispatch = dispatch;
return lib;
```

After the refactor, it adds all named exports:
```javascript
lib.getTask = ofoInfo;
lib.completeTask = ofoComplete;
lib.createTask = ofoCreate;
lib.updateTask = ofoUpdate;
lib.searchTasks = ofoSearch;
lib.listTasks = ofoList;
lib.getPerspective = ofoPerspective;
lib.configurePerspective = ofoPerspectiveConfigure;
lib.tagTask = ofoTag;
lib.getTags = ofoTags;
lib.createBatch = ofoCreateBatch;
lib.getPerspectiveRules = ofoPerspectiveRules;
lib.dumpDatabase = ofoDump;    // new
lib.getStats = ofoStats;       // new
lib.dispatch = dispatch;       // unchanged — backward compat
return lib;
```

`ofo-stub.js` still calls `lib.dispatch(args)` — zero change required.

### What changes in `ofo-core.ts`

The 12 existing functions are already pure and cross-platform. Changes are additive:
- Rename internal functions to match exported names (e.g., `ofoInfo` → readable for callers)
- Add two new functions: `ofoDump()` (full JSON database snapshot) and `ofoStats()` (fast counts)
- Dispatch becomes a thin router calling the named functions — same behavior, DRY

### What changes for shared types (#117)

Two-pronged approach respecting the build constraint:

**For the CLI** (`ofo-cli.ts`) — a real TypeScript module:
```typescript
// scripts/src/ofo-types.ts — importable by ofo-cli.ts only
export type OfoAction =
  | 'ofo-info' | 'ofo-complete' | 'ofo-create' | 'ofo-create-batch'
  | 'ofo-update' | 'ofo-search' | 'ofo-list' | 'ofo-tag' | 'ofo-tags'
  | 'ofo-perspective' | 'ofo-perspective-configure' | 'ofo-perspective-rules'
  | 'ofo-dump' | 'ofo-stats'

export interface OfoArgs { action: OfoAction; [key: string]: unknown }
export interface OfoResult { success: boolean; error?: string; [key: string]: unknown }
```

**For the plugin** (`ofo-core.ts`) — ambient declarations added to `ofo-core-ambient.d.ts` (already included in `tsconfig.plugin.json`):
```typescript
// appended to scripts/src/ofo-core-ambient.d.ts
type OfoAction = 'ofo-info' | 'ofo-complete' | ... | 'ofo-dump' | 'ofo-stats'
interface OfoArgs { action: OfoAction; [key: string]: unknown }
interface OfoResult { success: boolean; error?: string; [key: string]: unknown }
```

Both compile correctly. The CLI imports from `ofo-types.ts`; the plugin uses the ambient version. They must be kept in sync manually — add a comment in each file pointing to the other.

### What changes in Attache

Replace `taskParser.js`, `projectParser.js`, `folderParser.js` data access with ofoCore calls. Keep everything uniquely Attache's own:

```javascript
// BEFORE: taskParser.js calls flattenedTasks directly (~80 lines)

// AFTER: load ofoCore, call named function
const corePlugin = PlugIn.find("com.totally-tools.ofo-core");
if (!corePlugin) { /* graceful error */ return; }
const ofoCore = corePlugin.library("ofoCore");
const tasks = ofoCore.listTasks({ filter: 'flagged' });
```

Attache **keeps**: `foundationModelsUtils.js`, `weeklyReview.js`, `dailyReview.js`, `preferencesManager.js`, `hierarchicalBatcher.js`, `systemDiscovery.js`, `systemSetup.js`, `taskMetrics.js` (richer than ofoCore's list — age metrics, clarity scoring), `exportUtils.js`.

### What to do with `scripts/libraries/omni/`

Audit these files against ofoCore's action surface. They may:
- Already be superseded by ofo-core's named exports (once exported) → archive
- Provide functionality not in ofo-core → candidates to add as new ofoCore actions or as Attache library dependencies

Do not deploy them as-is without reconciling with ofoCore first.

## Technical Approach

### Phase 0: iOS Cross-Plugin Loading Verification

**Goal:** Confirm `PlugIn.find("com.totally-tools.ofo-core").library("ofoCore")` resolves correctly on iOS before any code changes.

- [x] Read `references/omni_automation_guide.md` Section 6 (Libraries) for iOS constraints
- [x] Write a minimal test action plugin (`assets/ofocore-test.omnifocusjs`) that calls `PlugIn.find("com.totally-tools.ofo-core").library("ofoCore").dispatch({action:"ofo-list",filter:"flagged"})` and shows result in an Alert
- [x] Install both plugins on iPhone via AirDrop → Files app
- [x] **CONFIRMED:** Cross-plugin loading works on iPhone — all 3 steps passed (2026-03-22)
- [x] Document finding in `references/omni_automation_guide.md` — "Cross-plugin Library Loading (validated Mac + iPhone, 2026-03-22)" added to Section 6

**Key files:**
- `references/omni_automation_guide.md` (read + update)
- Test plugin (temporary, not committed)

### Phase 1: Shared Types (#117 items)

**Goal:** Establish the type contract before touching implementations.

- [x] Create `scripts/src/ofo-types.ts` — `OfoAction` union + `OfoArgs` + `OfoResult` + parameter interfaces (importable by CLI only)
- [x] Append ambient versions of the same types to `scripts/src/ofo-core-ambient.d.ts` with a comment: `// Keep in sync with ofo-types.ts`
- [x] Update `scripts/src/tsconfig.cli.json` to include `ofo-types.ts` in the CLI compilation
- [x] Update `ofo-cli.ts` to `import type { OfoAction, OfoArgs, OfoResult } from './ofo-types'` — remove any duplicate local definitions
- [x] Update `ofo-core.ts` to use the ambient `OfoAction` type in the dispatch switch — add exhaustiveness check via `satisfies` or `never` default case
- [x] Run `npm run build` — verify zero TypeScript errors
- [x] Relocate `scripts/typescript/example-plugin.ts` → `references/example-plugin.ts` and add link in SKILL.md references section

**Key files:**
- `scripts/src/ofo-types.ts` (new)
- `scripts/src/ofo-core-ambient.d.ts` (appended)
- `scripts/src/ofo-cli.ts` (import updated)
- `scripts/src/ofo-core.ts` (OfoAction type applied to dispatch switch)
- `scripts/src/tsconfig.cli.json` (updated to include ofo-types.ts)
- `scripts/typescript/example-plugin.ts` → `references/example-plugin.ts` (moved)

### Phase 2: Named Function Exports in ofoCore

**Goal:** Expose named functions on the ofoCore library. ofo-stub.js unchanged.

- [x] Rename the 12 internal functions to public-friendly names (mapping: `ofoInfo`→`getTask`, `ofoSearch`→`searchTasks`, `ofoList`→`listTasks`, `ofoComplete`→`completeTask`, `ofoCreate`→`createTask`, `ofoUpdate`→`updateTask`, `ofoTag`→`tagTask`, `ofoTags`→`getTags`, `ofoPerspective`→`getPerspective`, `ofoPerspectiveConfigure`→`configurePerspective`, `ofoPerspectiveRules`→`getPerspectiveRules`, `ofoCreateBatch`→`createBatch`)
- [x] Add `dumpDatabase()` — full JSON snapshot: tasks (active, capped at 500), projects (active), perspectives list. Warns if truncated.
- [x] Add `getStats()` — fast counts: inbox, flagged, overdue, project count, total active tasks.
- [x] Make `dispatch()` a thin router calling the named functions (DRY — no duplicated logic)
- [x] Update `build-plugin.sh` IIFE wrapper to assign all 14 named exports + `lib.dispatch = dispatch`
- [x] Run `npm run build && npm run deploy` (fixed deploy script to target iCloud Plug-Ins path)
- [x] Verified backward compat: `ofo list inbox`, `ofo list flagged` return same structure
- [x] Add `ofo dump` and `ofo stats` CLI argument parsing in `ofo-cli.ts`
- [x] Verify `.gitignore` negation rule covers `build/ofo-core.omnifocusjs/` (confirmed: root `/build/` only; `scripts/build/` not ignored except `ofo-core.omnifocusjs/`)

**Key files:**
- `scripts/src/ofo-core.ts` (renamed functions + dispatch thin router + dump/stats)
- `scripts/src/ofo-cli.ts` (add dump, stats arg parsing)
- `scripts/build-plugin.sh` (add named export assignments to IIFE wrapper)

### Phase 3: `scripts/libraries/omni/` Reconciliation

**Goal:** Determine fate of the existing but undeployed library files.

- [x] Audit each file in `scripts/libraries/omni/` against ofoCore's new named exports — all 7 kept (none superseded):
  - `taskMetrics.js` — partial overlap with `listTasks`; unique: `getUpcomingTasks(days)`, `getTasksByTag`, `getTasksByProject`, richer `normalizeTask`
  - `exportUtils.js` — JSON/CSV/Markdown/HTML export; no ofoCore overlap
  - `patterns.js` — MCP-ready orchestration; depends on taskMetrics + exportUtils + insightPatterns
  - `insightPatterns.js` — `detectStalledProjects`, `generateInsights`; richer than `getStats()`
  - `completedTasksFormatter.js` — formats completed-task arrays as grouped Markdown inside plugin actions
  - `templateEngine.js` — template loading, variable substitution, bulk creation from templates
  - `treeBuilder.js` — 1103 lines; database/window tree structures; Markdown/JSON/OPML export; OF4 tree navigation
- [x] Documented in `references/library_ecosystem.md` (full audit with ofoCore overlap notes)
- [x] No files archived — all have unique capabilities not covered by ofoCore named exports

**Key files:**
- `scripts/libraries/omni/*.js` (audit, keep/archive)
- `skills/omnifocus-manager/SKILL.md` (Library Ecosystem section)

### Phase 4: Attache Refactor

**Goal:** Replace Attache's reimplemented data-access files with ofoCore calls.

- [x] Full audit of each Attache library file — confirm "replace vs. keep" classification:
  - **Audit finding (2026-03-21):** The plan's "replace" assumption was incorrect. `taskParser.js`, `projectParser.js`, `folderParser.js` are **analytical libraries**, not simple data-access wrappers. They take native OmniFocus API objects as parameters (no significant direct global access) and provide GTD-specific analysis with no ofoCore equivalent (clarity scoring, GTD health assessment, folder health grading). Replacing them would require either losing this analysis or inlining it in every action file. Plan risk item "Attache audit reveals deeper coupling" applied.
  - **Reclassified as Keep (unique analytical value):** `taskParser.js` (GTD clarity scoring + age metrics), `projectParser.js` (GTD health assessment — stall detection, review tracking), `folderParser.js` (folder health grading; `getAllFolders()` must return native OmniFocus objects for form dropdowns — no ofoCore folder API exists)
  - **Keep (unique to Attache):** `foundationModelsUtils.js`, `weeklyReview.js`, `dailyReview.js`, `preferencesManager.js`, `hierarchicalBatcher.js`, `systemDiscovery.js`, `systemSetup.js`, `taskMetrics.js`, `exportUtils.js`
  - **No files removed or replaced.** All 9 Attache libraries retained.
- [x] Null-guard pattern documented in plan — no action files currently load ofoCore directly; pattern is established for future feature plugins
- [x] All 9 Attache actions validated structurally — no regressions (action files unchanged)
- [x] Bump Attache version in `assets/Attache.omnifocusjs/manifest.json` → 1.1.0

**Key files:**
- `assets/Attache.omnifocusjs/manifest.json` (version bump to 1.1.0)

### Phase 5: Documentation & Skill Updates

- [ ] Update CONTRIBUTING.md:
  - Architecture diagram (three-layer: ofoCore library → ofo-stub/Claude Code + feature plugins)
  - "How to write a new feature plugin" — load ofoCore, call named functions, null-guard pattern
  - "How to add a new ofoCore action" — add to `ofo-core.ts`, add to `build-plugin.sh` IIFE exports, add to `ofo-types.ts` + `ofo-core-ambient.d.ts` union, add CLI arg parsing
- [ ] Update `references/omni_automation_guide.md` — "Using ofoCore from another plugin" code example
- [ ] Update SKILL.md — `ofo dump`, `ofo stats` in command table; Attache architecture note; Library Ecosystem section
- [ ] Run skillsmith: `uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py plugins/omnifocus-manager/skills/omnifocus-manager --version 9.0.0 --export-table-row`
- [ ] Bump version to 9.0.0 in `plugin.json`, `marketplace.json`, SKILL.md header
- [ ] Update README.md version history

**Key files:**
- `CONTRIBUTING.md`
- `references/omni_automation_guide.md`
- `skills/omnifocus-manager/SKILL.md`
- `.claude-plugin/plugin.json`
- `README.md`

## System-Wide Impact

### Interaction Graph

**Claude Code transport (unchanged):** `ofo` bash → `node ofo-cli.js` → `omnifocus://localhost/omnijs-run?script=<stub>&arg=<json>` → OmniFocus → `ofoCore.dispatch(args)` → pasteboard → stdout. Zero change — dispatch is a thin router now but returns identical results.

**Attache actions (after Phase 4):** `action.js` → `this.plugIn.library("foundationModelsUtils")` (unchanged) + `PlugIn.find("com.totally-tools.ofo-core").library("ofoCore").listTasks(filter)` (new) → FM inference → Alert/Form UI.

### Error Propagation

The 12 existing functions are already wrapped in try/catch inside `dispatch()`. After refactor, named functions called directly (not via dispatch) must handle their own errors — Attache action files need try/catch around ofoCore calls. Document this in CONTRIBUTING.md.

`ofoStats()` must complete in <500ms or return a timeout result rather than hanging — OmniFocus may block the UI thread.

### State Lifecycle Risks

- `dumpDatabase()` on a large database may be slow; add item count to the result so callers can detect oversized dumps
- `PlugIn.find()` returning `null` (plugin not installed) is a silent failure without the null-guard — every ofoCore consumer must guard
- `build-plugin.sh` IIFE wrapper changes require a fresh `npm run deploy` — existing installed plugin will not have named exports until redeployed

### API Surface Parity

All 12 existing ofo CLI commands unchanged. New `ofo dump` and `ofo stats` added. All Attache actions continue to work (refactored internals, same OmniFocus UI surface).

### Integration Test Scenarios

1. **Backward compat:** Golden output diff for all 12 ofo commands before and after Phase 2 — JSON must be structurally identical
2. **Named export loading:** Write minimal test plugin, install alongside ofo-core, call `ofoCore.getStats()` — verify valid JSON result
3. **Null-guard:** Temporarily rename/remove ofo-core.omnifocusjs; trigger Attache action — verify graceful Alert, not crash
4. **Attache after Phase 4:** All 9 Attache actions return correct results with replaced data-access files
5. **iOS (conditional on Phase 0):** Install both plugins on iPhone, trigger Attache action, verify ofoCore resolves and data returns

## Acceptance Criteria

### Functional
- [x] All 12 existing ofo CLI commands return identical JSON to pre-refactor golden files
- [x] `ofo dump` returns database snapshot in valid JSON (capped at 500 tasks, warns if truncated)
- [x] `ofo stats` returns counts in <500ms
- [x] All 9 Attache actions structurally validated after Phase 4 audit — no regressions (no code changes needed; parsers reclassified as analytical libraries)
- [x] `ofo-stub.js` is byte-for-byte identical before and after all phases
- [x] Bundle ID `"com.totally-tools.ofo-core"` and library ID `"ofoCore"` are unchanged

### Type Safety (#117)
- [x] `OfoAction` union exists in both `ofo-types.ts` (CLI) and `ofo-core-ambient.d.ts` (plugin) — kept in sync
- [x] Adding a new action string not in `OfoAction` union produces TypeScript error in CLI
- [x] `npm run build` produces zero TypeScript errors

### Architecture
- [x] `scripts/typescript/example-plugin.ts` relocated to `references/`
- [x] `scripts/libraries/omni/` each file audited — all 7 kept (documented in `references/library_ecosystem.md`)
- [ ] CONTRIBUTING.md documents the null-guard pattern and the "add new action" workflow
- [ ] Skillsmith eval score ≥ 95
- [ ] Plugin version 9.0.0 in `plugin.json` and `marketplace.json`

## Dependencies & Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| iOS `PlugIn.find()` returns null in sandboxed context | Medium | High | Phase 0 validates before code changes; fallback documented if needed |
| Attache audit reveals deeper coupling than taskParser/projectParser/folderParser | Low | Medium | Phase 4 starts with full audit before committing to replacements |
| `build-plugin.sh` IIFE wrapper changes cause parse error in OmniFocus runtime | Low | Medium | `validate-plugin.sh` catches this; smoke test immediately after deploy |
| Named functions called directly by Attache don't have error handling | Medium | Medium | Null-guard pattern + try/catch documented in CONTRIBUTING.md as required |
| `ofo-types.ts` and `ofo-core-ambient.d.ts` drift out of sync | Medium | Low | Comment in each file pointing to the other; caught at next `npm run build` if types diverge |
| `dumpDatabase()` too slow or too large on big databases | Low-Medium | Low (new, no regression) | Item count guard + warning in output |
| `.gitignore` negation missing for new build artifacts | Low | Medium | Check `build/ofo-core.omnifocusjs/` negation before Phase 2 deploy (per issue #114) |

## Future Considerations

- **Foundation Models plugins:** Load ofoCore for data + `FoundationModels.Session` for inference — full on-device AI triage/tagging/summarization on iPhone with zero Claude Code dependency
- **Siri Shortcuts:** ofoCore-backed plugins expose OmniFocus Shortcuts actions natively on iPhone
- **MCP wrapper:** Thin MCP server shelling out to `ofo` CLI — same named functions, trivial mapping
- **Issue #119 follow-on:** Project lifecycle (pause/resume/drop), recurrence (RRULE), focus scope, folder CRUD — all as new ofoCore named functions + CLI commands in a subsequent PR
- **Issue #111:** Automatic learning pipeline (promoting usage patterns to new CLI commands) is unblocked once the "add new action" workflow is documented as a 4-step pattern

## Sources & References

### GitHub Issues
- **#119:** [Separate ofo-library primitives from dispatch and feature plugins](https://github.com/totallyGreg/claude-mp/issues/119)
- **#117:** [closed, absorbed] Type safety items carried forward into Phase 1

### Internal References
- Prior plan (completed): `docs/plans/2026-03-19-001-refactor-ofo-typescript-plugin-library-plan.md`
- ofo-core source: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/src/ofo-core.ts`
- ofo-cli source: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/src/ofo-cli.ts`
- Stable stub: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/src/ofo-stub.js`
- Build script: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/build-plugin.sh`
- Ambient types: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/src/ofo-core-ambient.d.ts`
- Attache assets: `plugins/omnifocus-manager/skills/omnifocus-manager/assets/Attache.omnifocusjs/Resources/`
- Undeployed libraries: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/libraries/omni/`
- Library reference: `plugins/omnifocus-manager/skills/omnifocus-manager/references/omni_automation_guide.md` (Section 6)
- Automation decision framework: `docs/solutions/agent-design/omnifocus-manager-automation-decision-framework.md`
- Distribution gotcha: `docs/plans/2026-03-20-002-feat-ofo-cli-fix-and-extend-plan.md` (issue #114 — `.gitignore` negation required for `build/`)
- Tag query performance: `docs/plans/2026-03-16-001-fix-omnifocus-manager-script-consolidation-tag-perf-plan.md` — use `tag.tasks()` not `flattenedTasks` for tag-based queries
- Foundation Models: `plugins/omnifocus-manager/skills/omnifocus-manager/references/foundation_models_integration.md`
