---
title: "refactor: Attache Plugin Consolidation — Merge ofo-core + Attache + TypeScript"
type: refactor
status: active
date: 2026-03-23
origin: 800 Generated/820 Brainstorms/2026-03-23-attache-plugin-consolidation-requirements.md
---

# refactor: Attache Plugin Consolidation

## Overview

Merge the `ofo-core.omnifocusjs` CLI plugin and `Attache.omnifocusjs` AI analytics plugin into a single consolidated `Attache.omnifocusjs` bundle. Convert all 9 hand-written Attache JS libraries to TypeScript. Eliminate logic drift (e.g., inbox counting bug in v1.4.5), reduce deploy complexity from two plugins to one, and unify the build pipeline.

**Supersedes:** Plan 009 (TypeScript Shared Sync). Phases 1–5 of Plan 009 carry forward (already shipped). Phase 6 (TypeScript Attache compilation) is absorbed into this plan as Phase 3.

## Problem Statement / Motivation

Two OmniFocus plugins share domain logic but maintain independent implementations:

| Dimension | ofo-core | Attache |
|-----------|----------|---------|
| Language | TypeScript → compiled JS | Hand-written JS |
| `normalizeTask` | 11 fields, ISO date strings | 11 fields, Date objects, different fields |
| Inbox counting | `task.inInbox && Task.Status.Available` | `containingProject === null` (WRONG) |
| Stats | `computeStats()` counts only | `collectAllMetrics()` returns task arrays |
| Build | `build-plugin.sh` + tsc | No build step |
| Deploy | `npm run deploy` | `open Attache.omnifocusjs` |

This caused today's bug: Attache Daily Review showed 18 inbox items instead of 7. A one-line fix was needed in two places. The consolidation makes this structurally impossible.

## Proposed Solution

### Architecture: Layered Single Plugin

```
Attache.omnifocusjs (com.totallytools.omnifocus.attache)
├── manifest.json
├── Resources/
│   ├── ofoCore.js          ← Core: CRUD, dispatch, normalizeTask, computeStats
│   ├── taskMetrics.js       ← Core: single-pass collector, WAITING_PATTERNS
│   ├── exportUtils.js       ← Core: format conversion, clipboard/file export
│   ├── taskParser.js        ← Analytics: task clarity scoring
│   ├── projectParser.js     ← Analytics: stalled project detection
│   ├── folderParser.js      ← Analytics: folder hierarchy analysis
│   ├── hierarchicalBatcher.js ← Analytics: batch task creation
│   ├── systemDiscovery.js   ← Analytics: GTD system pattern detection
│   ├── preferencesManager.js ← Analytics: device-scoped preferences
│   ├── foundationModelsUtils.js ← Analytics: Apple Intelligence wrapper
│   ├── dailyReview.js       ← Action
│   ├── weeklyReview.js      ← Action
│   ├── analyzeSelected.js   ← Action
│   ├── analyzeHierarchy.js  ← Action
│   ├── completedSummary.js  ← Action
│   ├── systemSetup.js       ← Action
│   ├── discoverSystem.js    ← Action
│   └── en.lproj/            ← Localization strings
└── (built from TypeScript sources)
```

### Library Cross-Reference Pattern (resolves SpecFlow Q1)

Omni Automation doesn't support ES6 modules. `this.plugIn.library("name")` is only callable inside action handler bodies (`new PlugIn.Action(async function(selection, sender) { ... })`). Libraries themselves are self-contained IIFEs — they cannot load other libraries.

**Pattern: Action wires dependencies via parameters.**

```javascript
// Action script — loads libraries, passes refs to functions that need them
const action = new PlugIn.Action(async function(selection, sender) {
    const core = this.plugIn.library("ofoCore");
    const metrics = this.plugIn.library("taskMetrics");
    const parser = this.plugIn.library("taskParser");

    // Libraries receive dependencies as parameters
    const all = metrics.collectAllMetrics(core);  // metrics uses core.normalizeTask()
    const clarity = parser.assessClarity(all, core);
});
```

```javascript
// taskMetrics library — receives ofoCore ref, uses its normalizeTask
lib.collectAllMetrics = function(core) {
    // ...
    if (task.inInbox && task.taskStatus === Task.Status.Available) {
        result.inbox.push(core.normalizeTask(task));  // single source of truth
    }
    // ...
};
```

This avoids global scope pollution and makes dependencies explicit. Existing action scripts already load libraries this way (e.g., `dailyReview.js` line 20–30). The change is that library functions gain a `core` parameter for shared operations.

### Canonical `normalizeTask` Contract (resolves SpecFlow Q2)

Single implementation in `ofoCore`, returns **Date objects** (native for OmniFocus computation). CLI serialization happens in `ofo-cli.ts` (already does `JSON.stringify` which auto-converts Dates to ISO strings).

```typescript
interface OfoTask {
    id: string;
    name: string;
    projectName: string | null;
    tags: string[];
    flagged: boolean;
    completed: boolean;
    dueDate: Date | null;
    deferDate: Date | null;
    plannedDate: Date | null;
    completionDate: Date | null;
    estimatedMinutes: number | null;
    note: string | null;
    added: Date | null;
    modified: Date | null;
    repetitionRule: string | null;
    taskStatus: string;
}
```

All 15 fields merged from both implementations. `taskMetrics.normalizeTask()` is removed; `taskMetrics.collectAllMetrics(core)` receives the ofoCore library ref from the calling action and uses `core.normalizeTask()` instead of its own implementation.

### CLI Stub Migration (resolves SpecFlow Q3)

The stub identifier changes from `com.totally-tools.ofo-core` to `com.totallytools.omnifocus.attache`. This is a **one-time re-approval** — the user must click "Automatically run" once in the OmniFocus security dialog.

Since this is a single-user tool (see origin: brainstorm resolution), no migration ceremony is needed. Just update the stub, deploy, and approve once.

### Undeployed Library Decision (resolves SpecFlow Q7)

| Library | Lines | Decision | Rationale |
|---------|-------|----------|-----------|
| `insightPatterns.js` | 413 | **Include** | Core analytical capability: stalled project detection, overload analysis, system insights |
| `completedTasksFormatter.js` | 89 | **Exclude** | Covered by `ofoCore.completedToday --markdown` |
| `patterns.js` | 635 | **Exclude** | MCP-oriented, not current need |
| `templateEngine.js` | 361 | **Exclude** | Not used by any action |
| `treeBuilder.js` | 1103 | **Exclude** | Too large, not used |
| `exportUtils.js` (undeployed) | 350 | **Delete** | Duplicate of Attache's deployed version |

### Version Strategy (resolves SpecFlow Q7/Q10)

**Attache plugin version:** `2.0.0` — major version signals the consolidation breaking change. The ofo-core plugin is simply uninstalled after consolidation.

## Technical Considerations

### Build Pipeline

**New unified build command:**

```bash
npm run build        # Compiles all TypeScript → builds Attache.omnifocusjs bundle
npm run build:cli    # Compiles ofo-cli.ts (unchanged)
npm run deploy       # open build/Attache.omnifocusjs
```

The existing `build-plugin.sh` is extended (renamed to `build-attache.sh`) to:
1. Compile `ofo-core.ts` → IIFE-wrapped `ofoCore.js` (existing flow)
2. Compile each Attache library `.ts` → IIFE-wrapped `.js` (new)
3. Copy action scripts (actions remain JS initially, migrate in Phase 3)
4. Copy manifest.json + localization strings
5. Validate all IIFE exports
6. Clean intermediates

**TypeScript configuration:**
- `tsconfig.plugin.json` — compiles ofoCore (existing, unchanged)
- `tsconfig.attache-libs.json` — compiles Attache libraries (new, extends base config)
- `tsconfig.cli.json` — compiles CLI (existing, unchanged)
- `tsconfig.attache.json` — removed (superseded by full compilation)

### Ambient Type Infrastructure

Existing from Plan 009 (carry forward):
- `ofo-contract.d.ts` — shared domain types (OfoTask, OfoArgs, OfoResult)
- `ofo-core-ambient.d.ts` — OmniFocus API stubs (Task, Project, Tag, etc.)
- `omni-attache-ambient.d.ts` — Attache-specific globals (LanguageModel, Alert, Form)

All three are consumed by the new `tsconfig.attache-libs.json`.

## System-Wide Impact

- **CLI (`ofo`):** Stub identifier changes. All commands work unchanged after re-approval.
- **SKILL.md:** Update deploy section, remove separate ofo-core references
- **CONTRIBUTING.md:** Update 5-step action addition workflow for consolidated plugin
- **library_ecosystem.md:** Update to reflect consolidated architecture
- **marketplace (plugin cache):** Version bump triggers marketplace sync
- **Issue #135:** Not addressed here — deploy still requires manual OmniFocus restart for library reload

## Implementation Phases

### Phase 1: Consolidate Plugins (No TypeScript Migration)

Merge ofo-core into Attache as-is. Both keep their current language (ofoCore stays TypeScript-compiled, Attache libraries stay hand-written JS). This phase delivers the core value: one plugin, zero drift risk, one deploy.

**Deliverables:**
- `build-attache.sh` — extended build script that compiles ofoCore into Attache bundle
- `assets/Attache.omnifocusjs/manifest.json` — add `ofoCore` library declaration
- `scripts/src/ofo-stub.js` — update identifier to `com.totallytools.omnifocus.attache`
- `package.json` — update build/deploy scripts
- `taskMetrics.js` — remove local `normalizeTask`; update `collectAllMetrics(core)` to accept ofoCore ref parameter
- Action scripts (dailyReview, weeklyReview, etc.) — pass ofoCore ref to library functions
- Remove `build/ofo-core.omnifocusjs/` from build output

**Acceptance criteria:**
- [ ] `npm run build` produces single `build/Attache.omnifocusjs/` bundle with ofoCore + all libraries + all actions
- [ ] `npm run deploy` opens consolidated bundle in OmniFocus
- [ ] `ofo list inbox` returns correct count (7) via consolidated plugin
- [ ] `ofo stats` returns correct stats via consolidated plugin
- [ ] All 7 Attache actions launch without errors
- [ ] Daily Review shows correct inbox count (matching `ofo list inbox`)
- [ ] IIFE export assertion passes for all 16 ofoCore functions
- [ ] Old `ofo-core.omnifocusjs` uninstalled from OmniFocus

### Phase 2: Unify Shared Logic

Eliminate remaining duplication between ofoCore and Attache libraries. Single canonical implementations in the Core layer.

**Deliverables:**
- `ofo-core.ts` — canonical `normalizeTask()` with full 15-field OfoTask (merge fields from both implementations)
- `ofo-contract.d.ts` — update OfoTask interface to 15 fields
- `systemDiscovery.js` — replace hardcoded `WAITING_PREFIXES` with reference to `taskMetrics.WAITING_PATTERNS` (passed as parameter from action scripts)
- `insightPatterns.js` — copy from undeployed `scripts/libraries/omni/` to `assets/Attache.omnifocusjs/Resources/`, add to manifest.json
- Update `manifest.json` — add `insightPatterns` library declaration
- Delete `scripts/libraries/omni/exportUtils.js` (duplicate of Attache's deployed version)

**Acceptance criteria:**
- [ ] `grep -r "containingProject === null" assets/Attache.omnifocusjs/` returns zero matches
- [ ] `grep -r "WAITING_PREFIXES" assets/Attache.omnifocusjs/` returns zero matches
- [ ] `normalizeTask` exists in exactly one file (ofoCore.js)
- [ ] All action scripts produce identical output to pre-consolidation baseline
- [ ] `diff-task-shapes.js` exits 0

### Phase 3: TypeScript Attache Libraries

Convert all hand-written JS libraries to TypeScript. This is Plan 009 Phase 6, now simpler within the consolidated plugin.

**Migration order** (ascending OmniFocus global dependency, per Plan 009):
1. `taskMetrics.ts` — pure computation, minimal globals
2. `exportUtils.ts` — file I/O only
3. `preferencesManager.ts` — preferences API
4. `folderParser.ts` — OmniFocus read-only
5. `projectParser.ts` — OmniFocus read-only
6. `taskParser.ts` — OmniFocus read-only
7. `insightPatterns.ts` — pattern detection (newly included)
8. `hierarchicalBatcher.ts` — batching logic
9. `systemDiscovery.ts` — reads + writes preferences (1189 lines, most complex)
10. `foundationModelsUtils.ts` — LanguageModel API (most globals)

**Deliverables:**
- `scripts/src/attache/` directory — 10 TypeScript library source files
- `tsconfig.attache-libs.json` — TypeScript compilation config
- `build-attache.sh` — extended to compile Attache libraries from TypeScript
- `omni-attache-ambient.d.ts` — extended with any missing OmniFocus global stubs
- Each compiled `.js` replaces the hand-written version in `Resources/`
- Delete hand-written `.js` originals after each verified migration

**Acceptance criteria:**
- [ ] `npx tsc --noEmit --project src/tsconfig.attache-libs.json` passes with 0 errors
- [ ] All 10 library `.js` files in Resources/ are generated, not hand-written
- [ ] All 7 Attache actions launch without console errors
- [ ] `npm run build` compiles ofoCore + 10 libraries + copies 7 actions in one command
- [ ] IIFE export validation passes for all libraries

### Phase 4: Documentation & Cleanup

**Deliverables:**
- SKILL.md — update deploy section, library architecture description, remove ofo-core references
- CONTRIBUTING.md — update 5-step workflow for consolidated plugin
- library_ecosystem.md — rewrite to reflect consolidated architecture
- README.md — version history entry for 2.0.0
- `references/omni_automation_guide.md` — update plugin generation patterns to reflect consolidated architecture, library parameter-passing pattern, and correct `this.plugIn.library()` constraint documentation
- `references/code_generation_validation.md` — update validation rules for consolidated plugin (library cross-reference pattern, IIFE export lists, shared class exposure per [Omni Automation shared classes](https://omni-automation.com/shared/index.html))
- `references/automation_best_practices.md` — update patterns/anti-patterns for the new architecture
- Delete `scripts/libraries/omni/` (undeployed library collection — included or dropped)
- Delete `scripts/build/ofo-core.omnifocusjs/` directory
- Delete `tsconfig.attache.json` (superseded by full compilation)
- Bump skill version to match plugin consolidation
- Run skillsmith evaluation to validate skill quality after reference updates

**Acceptance criteria:**
- [ ] No references to `com.totally-tools.ofo-core` in any file
- [ ] No hand-written `.js` library files remain in repository
- [ ] `npm run build && npm run deploy` is the complete workflow
- [ ] Reference docs accurately describe the consolidated plugin architecture and library parameter-passing pattern
- [ ] Plugin generation workflow produces plugins compatible with the consolidated Attache plugin
- [ ] Skill evaluation score ≥ 94

## Acceptance Criteria

- [ ] Single `Attache.omnifocusjs` bundle contains all CRUD, analytics, and AI action capabilities
- [ ] `ofo list inbox` and Attache Daily Review return identical inbox counts
- [ ] One deploy command, one plugin to manage, one version to bump
- [ ] All existing CLI commands work unchanged (after one-time re-approval)
- [ ] All existing Attache actions work unchanged
- [ ] All libraries compiled from TypeScript (zero hand-written JS in bundle)
- [ ] Build pipeline validates all IIFE exports across all libraries
- [ ] No OmniFocus console errors after consolidation

## Dependencies & Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| CLI stub re-approval friction | One-time — user must click "Automatically run" | Single user, low friction. Document in deploy output. |
| TypeScript migration breaks actions | Actions fail if library interface changes | Migrate one library at a time. Test all actions after each. |
| OmniFocus library load order | Libraries may load before their dependencies | Manifest order controls load order. List Core before Analytics. |
| Plugin version conflict | Old ofo-core still installed alongside new Attache | Uninstall old plugin in Phase 1. Different identifiers, no conflict. |
| systemDiscovery.ts complexity | 1189 lines, most complex library | Migrate last. Use `@ts-check` as intermediate step if needed. |
| Build time increase | Compiling 10 libraries + ofoCore | tsc is fast (~2s). Single `tsc` invocation with project references. |

## Sources & References

### Origin

- **Origin document:** `800 Generated/820 Brainstorms/2026-03-23-attache-plugin-consolidation-requirements.md` — Key decisions: consolidate into Attache brand, three-layer architecture, macOS 26+ only, single deploy, Phase 6 in scope.

### Internal References

- Plan 009 (superseded): `docs/plans/2026-03-22-009-feat-typescript-shared-sync-plan.md` — Phases 1–5 carry forward, Phase 6 absorbed
- Build pipeline: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/build-plugin.sh`
- TypeScript source: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/src/ofo-core.ts`
- Attache bundle: `plugins/omnifocus-manager/skills/omnifocus-manager/assets/Attache.omnifocusjs/`
- Library ecosystem: `plugins/omnifocus-manager/skills/omnifocus-manager/references/library_ecosystem.md`
- Validation guide: `plugins/omnifocus-manager/skills/omnifocus-manager/references/code_generation_validation.md`
- Action labels lesson: `docs/solutions/logic-errors/omnifocus-plugin-action-labels-manifest-strings.md`

### Related Work

- Issue #114: ofo CLI broken — build artifacts not distributed (fixed in v9.4.1)
- Issue #135: Plugin deploy does not reload libraries — requires OmniFocus restart
- Issue #134: Plan 009 TypeScript Shared Sync (superseded by this plan)
- PR #112: ofo TypeScript plugin library migration (merged)
