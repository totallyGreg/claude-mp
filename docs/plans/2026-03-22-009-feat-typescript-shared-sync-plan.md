---
title: "feat: TypeScript Shared Sync — ofo-core and Attache Convergence"
type: feat
status: active
date: 2026-03-22
parent_issue: 111
related_plans:
  - docs/plans/2026-03-22-008-feat-attache-gtd-phase-mapping-display-plan.md
---

# feat: TypeScript Shared Sync — ofo-core and Attache Convergence

## Overview

Eliminate the dual-maintenance burden between the `ofo-core.ts` CLI plugin and the hand-written
Attache JS analytics libraries. Seven ranked improvements — from zero-risk type infrastructure to a
bold build-pipeline extension — converge on one goal: a single change in shared logic yields
consistent behaviour in both outputs.

**Parent issue:** [#111 — automatic learning pipeline for OmniFocus interaction patterns](https://github.com/totallyGreg/claude-mp/issues/111).
This plan fulfills #111's remaining Foundation acceptance criteria (build safety) and extends
Layer 1 (compound CLI commands) with GTD-specific intelligence. Layers 2 (pattern logger) and 3
(`/ofo:learn`) of #111 are out of scope here.

**Prerequisite:** [Plan 008](docs/plans/2026-03-22-008-feat-attache-gtd-phase-mapping-display-plan.md)
(Attache v1.4.0 — GTD renames, bug fixes, display polish) must be complete before Phase 6 of
this plan begins. Phase 6 migrates the same Attache library files to TypeScript; porting them
before 008's bug fixes are applied would duplicate the fix work.

## Problem Statement

Two OmniFocus plugins share a domain but diverge at every level:

| Dimension | ofo-core (TypeScript) | Attache (hand-written JS) |
|---|---|---|
| **Language** | TypeScript → compiled JS | Vanilla JS, no build step |
| **Types** | `ofo-types.ts` (importable) | `ofo-core-ambient.d.ts` (fragile `import()`) |
| **Task shape** | `getTask` / `searchTasks` / `listTasks` each inline their own object literal | — |
| **Stats scan** | `getStats()` (line 593) does its own `flattenedTasks` loop | `taskMetrics.collectAllMetrics()` single-pass |
| **GTD intelligence** | None | `taskParser.assessTaskClarity()`, `projectParser.identifyStalledProjects()` |
| **Build integrity** | 16-function IIFE footer hardcoded in `build-plugin.sh`; silent breakage if function renamed | No build gate at all |

The result: a fix to `normalizeTask` logic must be made twice; a rename in `ofo-core.ts` silently
omits a function from the deployed plugin; and Attache's GTD intelligence is invisible to CLI users.

## Ranked Improvement Ideas

Ordered from lowest risk / highest immediacy to boldest structural change.

### Idea 1 (Incremental) — Build Integrity Trifecta

**Three guards that together eliminate silent build breakage.**

#### 1a. Codegen: `ofo-types.ts` → `ofo-core-ambient.d.ts`

Replace the hand-maintained `ofo-core-ambient.d.ts` with a 30-line Node script run as the final
step of `build-plugin.sh`.

```
scripts/
  src/
    ofo-types.ts          ← single source of truth
    ofo-core-ambient.d.ts ← GENERATED (do not edit)
  generate-ambient.js     ← 30-line Node script
  build-plugin.sh         ← call generate-ambient.js at the end
```

The script extracts every exported interface/type from `ofo-types.ts` via regex and writes them as
`declare` statements without `import()` expressions. The fragile:

```typescript
type OfoTask = import('./ofo-types').OfoTask;
```

becomes a generated ambient:

```typescript
declare interface OfoTask { /* fields */ }
```

#### 1b. IIFE Footer Assertion

Add a post-build check in `build-plugin.sh` that reads the built `ofoCore.js` and asserts every
function name in the IIFE footer actually exists in the compiled source. Fail the build if any
name is missing. Prevents the current silent-omission failure mode when a function is renamed.

```bash
# After IIFE_FOOTER cat:
echo "  Verifying IIFE exports..."
for fn in getTask completeTask createTask updateTask searchTasks listTasks \
          getPerspective configurePerspective tagTask getTags createBatch \
          getPerspectiveRules dumpDatabase getStats dispatch; do
  grep -q "^function ${fn}(" "${INTERMEDIATE_DIR}/ofo-core.js" || \
    { echo "ERROR: ${fn} missing from compiled output"; exit 1; }
done
```

#### 1c. Field-Set Diff Script

A Node script `scripts/diff-task-shapes.js` that imports the built `ofoCore.js`, calls
`getTask`, `searchTasks`, and `listTasks` with a stub OmniFocus object, then diffs the returned
field sets and prints any divergence. Run as a pre-commit hook.

### Idea 2 (Incremental) — Shared `ofo-contract.d.ts`

Replace `ofo-core-ambient.d.ts` (Attache-side) and `ofo-types.ts` (CLI-side) with a single pure
ambient declaration file: `scripts/src/ofo-contract.d.ts`.

```typescript
// scripts/src/ofo-contract.d.ts
// Pure ambient — no imports, no exports. Consumed by both tsconfig.cli.json and tsconfig.attache.json.

declare interface OfoTask {
  id: string;
  name: string;
  projectName: string | null;
  tags: string[];
  flagged: boolean;
  completed: boolean;
  dueDate: string | null;   // ISO-8601
  deferDate: string | null;
  estimatedMinutes: number | null;
  note: string | null;
}

declare interface OfoProject { /* ... */ }
declare interface OfoStats { /* ... */ }
declare type OfoArgs = { [key: string]: string };
declare type OfoResult = string | object;
```

Both `tsconfig.cli.json` and `tsconfig.plugin.json` (and the future `tsconfig.attache.json`) add
`ofo-contract.d.ts` to their `files` array. `ofo-types.ts` becomes a thin re-export wrapper
(for Node consumers that need module imports) that imports from `ofo-contract.d.ts` rather than
defining the types itself.

### Idea 3 (Incremental) — Single Canonical Stats Pass

`getStats()` (`ofo-core.ts:593`) independently iterates `flattenedTasks` to count inbox, overdue,
flagged, and due-today items — the same work `taskMetrics.collectAllMetrics()` does with a single
pass in Attache.

**Fix:** Extract a pure `computeStats(tasks: Task[]): OfoStats` function into `ofo-core.ts` that
mimics `collectAllMetrics`'s single-pass pattern. `getStats()` calls it. When the bold Phase 1
(Idea 7) lands, `computeStats` can be replaced by a cross-plugin call to `collectAllMetrics`.

```typescript
// ofo-core.ts — new helper
function computeStats(tasks: Task[]): OfoStats {
  let inbox = 0, overdue = 0, flagged = 0, dueToday = 0, available = 0;
  const now = new Date();
  const todayEnd = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);
  tasks.forEach(function(t) {
    if (!t.completed) {
      if (t.inInbox) inbox++;
      if (t.flagged) flagged++;
      if (t.dueDate && t.dueDate < now) overdue++;
      if (t.dueDate && t.dueDate <= todayEnd) dueToday++;
      if (t.taskStatus === Task.Status.Available) available++;
    }
  });
  return { inbox, overdue, flagged, dueToday, available };
}

function getStats(_args: OfoArgs): OfoResult {
  const tasks = document.flattenedTasks as Task[];
  return JSON.stringify(computeStats(tasks));
}
```

### Idea 4 (Incremental) — `normalizeTask()` Extracted in `ofo-core.ts`

`getTask`, `searchTasks`, and `listTasks` each construct task objects inline with slightly
different field sets. One normalizer eliminates the drift.

```typescript
function normalizeTask(t: Task): OfoTask {
  return {
    id: t.id.primaryKey,
    name: t.name,
    projectName: t.containingProject ? t.containingProject.name : null,
    tags: t.tags.map(function(tag) { return tag.name; }),
    flagged: t.flagged,
    completed: t.completed,
    dueDate: t.dueDate ? t.dueDate.toISOString() : null,
    deferDate: t.deferDate ? t.deferDate.toISOString() : null,
    estimatedMinutes: t.estimatedMinutes || null,
    note: t.note || null,
  };
}
```

All three functions replace their inline object literals with `normalizeTask(t)`. The field-set
diff script (Idea 1c) verifies this.

### Idea 5 (Incremental) — `@ts-check` + `tsconfig.attache.json` Pre-Commit Gate

Add type checking to Attache's hand-written JS without changing the runtime or adding a build step.

**`scripts/src/tsconfig.attache.json`:**
```json
{
  "compilerOptions": {
    "checkJs": true,
    "allowJs": true,
    "noEmit": true,
    "strict": false,
    "lib": ["ES2020"],
    "typeRoots": ["./"],
    "types": []
  },
  "files": [
    "ofo-contract.d.ts",
    "ofo-core-ambient.d.ts"
  ],
  "include": [
    "../../assets/Attache.omnifocusjs/Resources/*.js"
  ]
}
```

Add `// @ts-check` to each Attache JS file header. Wire into pre-commit:

```bash
# pre-commit hook addition
npx tsc --project scripts/src/tsconfig.attache.json && echo "  Attache type check passed"
```

**Risk:** Attache JS uses OmniFocus globals (`document`, `Alert`, `LanguageModel`) that tsc cannot
resolve. Seed `ofo-core-ambient.d.ts` with stubs for these globals before enabling strict mode.

### Idea 6 (Moderate) — CLI Exposure: `ofo clarity` + `ofo stalled`

Wire Attache's GTD intelligence into the CLI dispatch table so `ofo clarity` and `ofo stalled`
work from the terminal.

**New dispatch cases in `ofo-core.ts`:**

```typescript
case 'clarity':  return assessClarity(args);
case 'stalled':  return stalledProjects(args);
```

**`assessClarity()`** — a TypeScript port of `taskParser.assessTaskClarity()`:

```typescript
function assessClarity(args: OfoArgs): OfoResult {
  const limit = parseInt(args['limit'] || '10');
  const tasks = document.flattenedTasks as Task[];
  const results = tasks
    .filter(t => !t.completed && t.taskStatus === Task.Status.Available)
    .map(t => ({
      id: t.id.primaryKey,
      name: t.name,
      score: clarityScore(t),
    }))
    .sort((a, b) => a.score - b.score)
    .slice(0, limit);
  return JSON.stringify(results);
}

function clarityScore(t: Task): number {
  let score = 100;
  if (!t.estimatedMinutes) score -= 30;
  if (t.tags.length === 0) score -= 20;
  if (t.name.length < 10) score -= 20;
  if (!t.containingProject) score -= 30;
  return Math.max(0, score);
}
```

**`stalledProjects()`** — port of `projectParser.identifyStalledProjects()`:

```typescript
function stalledProjects(args: OfoArgs): OfoResult {
  const daysSince = parseInt(args['days'] || '14');
  const cutoff = new Date(Date.now() - daysSince * 86400000);
  const projects = document.flattenedProjects as Project[];
  const stalled = projects
    .filter(p => !p.completed && !p.dropped)
    .filter(p => {
      const na = p.flattenedTasks.find(t => t.taskStatus === Task.Status.Available);
      return !na || (p.modificationDate && p.modificationDate < cutoff);
    })
    .map(p => ({ id: p.id.primaryKey, name: p.name, taskCount: p.flattenedTasks.length }));
  return JSON.stringify(stalled);
}
```

Add to IIFE footer: `lib.assessClarity = assessClarity; lib.stalledProjects = stalledProjects;`
Add to dispatch: `case 'clarity': ... case 'stalled': ...`
Add to IIFE assertion list (Idea 1b).
Update `ofo-cli.ts` argument handling for `--limit` and `--days` flags.

### Idea 7 (Bold) — Compile Attache Analytics from TypeScript

The highest-leverage idea: author Attache's 9 library files in TypeScript and generate the JS
bundle via a new `build-attache-libs.sh` script. Runtime and deployment are unchanged; only the
authoring language changes.

**New directory layout:**

```
scripts/
  src/
    attache/
      taskMetrics.ts
      foundationModelsUtils.ts
      folderParser.ts
      projectParser.ts
      taskParser.ts
      exportUtils.ts
      hierarchicalBatcher.ts
      systemDiscovery.ts
      preferencesManager.ts
  build-attache-libs.sh   ← new script
```

**`build-attache-libs.sh` pattern (mirrors `build-plugin.sh`):**

```bash
#!/usr/bin/env bash
set -euo pipefail
DEST="assets/Attache.omnifocusjs/Resources"

for lib in taskMetrics foundationModelsUtils folderParser projectParser \
           taskParser exportUtils hierarchicalBatcher systemDiscovery preferencesManager; do
  npx tsc --project scripts/src/tsconfig.attache.json \
    --outFile scripts/build/attache/${lib}.js \
    scripts/src/attache/${lib}.ts
  # Strip exports, wrap in PlugIn.Library IIFE
  CORE=$(sed '/^export /d; /^import /d' scripts/build/attache/${lib}.js)
  cat > "${DEST}/${lib}.js" << EOF
(() => {
  var lib = new PlugIn.Library(new Version("1.0"));
${CORE}
  return lib;
})();
EOF
done
```

**Migration path:**

1. Copy each existing `.js` file to `scripts/src/attache/<name>.ts`
2. Add `// @ts-check` (already done via Idea 5) — tsc reveals type errors
3. Fix errors iteratively, starting with `taskMetrics.ts` (fewest OmniFocus globals)
4. Once a library passes tsc, its generated `.js` replaces the hand-written file
5. Delete the hand-written source from `Resources/` once the generated version is verified

**Constraint:** OmniFocus globals (`document`, `PlugIn`, `Alert`, `LanguageModel`) must be declared
in ambient stubs. The `ofo-contract.d.ts` from Idea 2 provides `OfoTask` etc.; a new
`scripts/src/omni-globals.d.ts` declares OmniFocus-specific globals.

## Architecture

### Dependency Order

```
ofo-contract.d.ts          ← pure ambient, no deps (Idea 2)
    ↓
tsconfig.cli.json           ← consumes ofo-contract.d.ts
tsconfig.plugin.json        ← consumes ofo-contract.d.ts
tsconfig.attache.json       ← consumes ofo-contract.d.ts + omni-globals.d.ts (Idea 5)
    ↓
generate-ambient.js         ← codegen from ofo-types.ts (Idea 1a, superseded by Idea 2)
    ↓
normalizeTask()             ← single task shape in ofo-core.ts (Idea 4)
computeStats()              ← single stats pass in ofo-core.ts (Idea 3)
    ↓
assessClarity()             ← CLI exposure (Idea 6)
stalledProjects()           ← CLI exposure (Idea 6)
    ↓
build-attache-libs.sh       ← Attache TS compilation (Idea 7)
```

### What Does NOT Change

- `assets/Attache.omnifocusjs/` runtime structure — unchanged
- `manifest.json` — unchanged
- Action JS files (`analyzeHierarchy.js`, `dailyReview.js`, etc.) — unchanged by this plan
- `build-plugin.sh` core logic — extended, not replaced
- OmniFocus plugin identifiers — unchanged

## Implementation Phases

### Phase 1: Build Integrity Trifecta (Ideas 1a, 1b, 1c) — Zero Risk

No functional changes. All changes are in build tooling.

**Deliverables:**
- `scripts/generate-ambient.js` — codegen script
- `build-plugin.sh` — add IIFE assertion block and call to generate-ambient.js
- `scripts/diff-task-shapes.js` — field-set diff utility
- `scripts/src/ofo-core-ambient.d.ts` — now generated, removed from version control

**Acceptance:**
- `build-plugin.sh` fails if any function in IIFE footer is absent from compiled source
- `ofo-core-ambient.d.ts` is regenerated on every build; manual edits are overwritten
- `diff-task-shapes.js` exits 0 when all three functions return identical field sets

### Phase 2: Shared Type Contract (Idea 2)

**Deliverables:**
- `scripts/src/ofo-contract.d.ts` — canonical pure ambient types
- `tsconfig.cli.json` — add `ofo-contract.d.ts` to `files`
- `tsconfig.plugin.json` — add `ofo-contract.d.ts` to `files`
- `ofo-types.ts` — thin re-export wrapper (backward compat for Node consumers)

**Acceptance:**
- `npx tsc --project scripts/src/tsconfig.cli.json` passes
- `npx tsc --project scripts/src/tsconfig.plugin.json` passes
- No `import()` expressions in any ambient `.d.ts` file

### Phase 3: `normalizeTask()` + `computeStats()` (Ideas 3, 4)

**Deliverables:**
- `ofo-core.ts` — add `normalizeTask()`, `computeStats()` helpers
- `getTask`, `searchTasks`, `listTasks` — replace inline object literals with `normalizeTask()`
- `getStats` — delegate to `computeStats()`
- `diff-task-shapes.js` — verify zero divergence (should be trivially true after change)

**Acceptance:**
- Field-set diff script exits 0
- `ofo stats` output is unchanged (same fields, same counts)
- Build passes IIFE assertion

### Phase 4: `@ts-check` Gate (Idea 5)

**Deliverables:**
- `scripts/src/tsconfig.attache.json` — JS type checking config
- `scripts/src/omni-globals.d.ts` — OmniFocus global stubs
- All 9 Attache library JS files — add `// @ts-check` header
- Pre-commit hook — add `tsc --noEmit --project tsconfig.attache.json`

**Acceptance:**
- `npx tsc --noEmit --project scripts/src/tsconfig.attache.json` passes with 0 errors
- Pre-commit rejects commits that introduce type errors in Attache JS

### Phase 5: CLI Intelligence Exposure (Idea 6)

**Deliverables:**
- `ofo-core.ts` — add `assessClarity()`, `stalledProjects()`, dispatch cases, IIFE exports
- `ofo-cli.ts` — add `--limit` and `--days` flag handling
- `build-plugin.sh` — add new functions to IIFE assertion list

**Acceptance:**
- `ofo clarity` returns JSON array of tasks sorted by clarity score
- `ofo stalled` returns JSON array of projects with no available next action in N days
- IIFE assertion passes with new functions included

### Phase 6: TypeScript Attache Compilation (Idea 7, Bold)

**Prerequisite: Plan 008 must be merged (Attache v1.4.0).** Phase 6 migrates the same library
files that 008 patches. Port after the JS sources are correct, not before.

**Deliverables:**
- `scripts/src/attache/taskMetrics.ts` — TypeScript port (start here, fewest globals)
- `scripts/build-attache-libs.sh` — IIFE wrapper build script
- Remaining 8 library `.ts` files ported iteratively
- `assets/Attache.omnifocusjs/Resources/*.js` — replaced by generated output

**Migration order (by ascending OmniFocus global dependency):**
1. `taskMetrics.ts` — pure computation, minimal globals
2. `exportUtils.ts` — file I/O only
3. `preferencesManager.ts` — preferences API
4. `folderParser.ts` — OmniFocus read-only
5. `projectParser.ts` — OmniFocus read-only
6. `taskParser.ts` — OmniFocus read-only
7. `hierarchicalBatcher.ts` — batching logic
8. `systemDiscovery.ts` — reads + writes preferences
9. `foundationModelsUtils.ts` — LanguageModel API (most globals)

**Acceptance:**
- `build-attache-libs.sh` runs without error
- Generated `.js` files pass `diff` against hand-written originals (modulo whitespace)
- All 7 Attache actions launch without console errors in OmniFocus

## Acceptance Criteria

- [ ] `build-plugin.sh` fails if any IIFE-exported function is absent from compiled source
- [ ] `ofo-core-ambient.d.ts` is generated; no `import()` expressions in any ambient file
- [ ] `ofo-contract.d.ts` exists; `ofo-types.ts` and `ofo-core-ambient.d.ts` both reference it
- [ ] `normalizeTask()` is the sole task-object constructor in `ofo-core.ts`
- [ ] `computeStats()` is the sole stats-counting function in `ofo-core.ts`
- [ ] `diff-task-shapes.js` exits 0 (field sets identical across getTask/searchTasks/listTasks)
- [ ] `tsconfig.attache.json` type-checks all Attache JS files with 0 errors
- [ ] `ofo clarity` and `ofo stalled` commands return valid JSON
- [ ] (Bold) `build-attache-libs.sh` generates all 9 Attache library files from TypeScript
- [ ] No OmniFocus console errors after any phase

## Risks & Notes

- **Omni Automation globals**: `LanguageModel`, `Alert`, `PlugIn`, `Form` are not TypeScript
  builtins. `omni-globals.d.ts` stubs must be comprehensive enough for `tsc` to accept Attache
  JS without requiring `any` everywhere.
- **`build-plugin.sh` IIFE footer sync**: The assertion (Idea 1b) is the guard. Once it exists,
  adding a function to `ofo-core.ts` and forgetting the footer produces a clear build error rather
  than a silent runtime gap.
- **Attache analytics two-layer boundary**: Attache libraries do GTD analysis/scoring; ofo-core
  does CRUD data access. Idea 6 ports a lightweight clarity scorer into ofo-core — this is
  acceptable because it reads data only. The full analytical stack (weighted scoring, batch FM
  calls) remains in Attache.
- **No test harness**: Manual smoke test each phase. `diff-task-shapes.js` (Idea 1c) is the
  closest thing to automated regression coverage today.
- **Phase ordering flexibility**: Phases 1–4 are pure infrastructure and can be done in any order
  or combined. Phase 5 (CLI) depends on Phase 3 (normalizeTask). Phase 6 (bold) depends on
  Phase 4 (@ts-check) to catch port errors early.

## Files Changed

| File | Phase | Change Type | Summary |
|---|---|---|---|
| `scripts/generate-ambient.js` | 1 | New | Codegen `ofo-types.ts` → `ofo-core-ambient.d.ts` |
| `scripts/build-plugin.sh` | 1 | Extend | IIFE assertion block; call generate-ambient.js |
| `scripts/diff-task-shapes.js` | 1 | New | Field-set diff utility |
| `scripts/src/ofo-core-ambient.d.ts` | 1 | Generated | Remove from version control; add to .gitignore |
| `scripts/src/ofo-contract.d.ts` | 2 | New | Pure ambient shared types |
| `scripts/src/ofo-types.ts` | 2 | Refactor | Thin re-export wrapper |
| `scripts/src/tsconfig.cli.json` | 2 | Extend | Add ofo-contract.d.ts to files |
| `scripts/src/tsconfig.plugin.json` | 2 | Extend | Add ofo-contract.d.ts to files |
| `scripts/src/ofo-core.ts` | 3 | Refactor | normalizeTask(), computeStats() helpers |
| `scripts/src/tsconfig.attache.json` | 4 | New | @ts-check config for Attache JS |
| `scripts/src/omni-globals.d.ts` | 4 | New | OmniFocus global stubs |
| `assets/Attache.omnifocusjs/Resources/*.js` | 4 | Extend | Add // @ts-check header |
| `scripts/src/ofo-core.ts` | 5 | Extend | assessClarity(), stalledProjects(), dispatch |
| `scripts/src/ofo-cli.ts` | 5 | Extend | --limit, --days flag handling |
| `scripts/src/attache/*.ts` | 6 | New (bold) | TypeScript ports of all 9 Attache libraries |
| `scripts/build-attache-libs.sh` | 6 | New (bold) | Attache IIFE build script |

## Sources & References

- `scripts/build-plugin.sh:41–60` — IIFE footer with 16 hardcoded function names
- `scripts/src/ofo-core.ts:593` — `getStats()` independent flattenedTasks scan
- `scripts/src/ofo-core.ts:198,247,254,267,278` — inline task object construction (3+ sites)
- `scripts/src/ofo-core-ambient.d.ts` — fragile `import()` expression (current)
- `assets/Attache.omnifocusjs/Resources/taskMetrics.js` — `collectAllMetrics()` single-pass model
- `assets/Attache.omnifocusjs/Resources/taskParser.js` — `assessTaskClarity()` to port
- `assets/Attache.omnifocusjs/Resources/projectParser.js` — `identifyStalledProjects()` to port
- `docs/plans/2026-03-22-001-refactor-ofo-library-separation-plan.md` — library boundary decisions
- `docs/plans/2026-03-22-008-feat-attache-gtd-phase-mapping-display-plan.md` — Attache v1.4.0 work (**must complete before Phase 6**)
- [GitHub issue #111](https://github.com/totallyGreg/claude-mp/issues/111) — parent issue; Layers 2 and 3 remain open after this plan
