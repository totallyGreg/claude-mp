---
title: "feat: GTD coach data-grounded coaching with OmniFocus diagnostic scripts"
type: feat
date: 2026-02-28
issue: 63
skills: [gtd-coach, omnifocus-manager]
---

# feat: GTD Coach Data-Grounded Coaching with OmniFocus Diagnostic Scripts

## Overview

The `gtd-coach` skill currently coaches purely conceptually — it cannot answer questions like "do you have stalled projects?" with real data from OmniFocus. This plan closes that gap by:

1. Creating `gtd-queries.ts` — a dedicated TypeScript JXA CLI script covering every major GTD coaching query
2. Migrating `taskQuery.js` JXA library to TypeScript source (`taskQuery.ts`) with project-level functions added
3. Exposing `overdue` as a CLI action in `manage_omnifocus.js` (already implemented in `taskQuery.js`, just not wired to CLI)
4. Fixing a `completionDate` data bug in `formatTaskInfo()` (affects all "completed tasks" queries)
5. Fixing syntax errors in Omni Automation reference libraries (`insightPatterns.js`, `patterns.js`)
6. Deprecating `query_omnifocus.py` — all scripts should be TypeScript/JavaScript, consistent with OmniFocus's JS-native stack
7. Deprecating `omnifocus.js` — overlaps entirely with `manage_omnifocus.js`, adds no unique capability
8. Updating `gtd-coach` SKILL.md with data-grounded coaching patterns referencing the new scripts

This completes **Pillar 1 (Query)** of Issue #63.

## Language Standard

**All scripts in this plugin are TypeScript.** OmniFocus and the broader automation ecosystem are built on JavaScript/TypeScript. Maintaining a Python script alongside TypeScript sources creates unnecessary language context switches.

| Script Type | Source | Runtime |
|---|---|---|
| JXA CLI scripts | `.ts` → compiled to `.js` via `tsc` | `osascript -l JavaScript <script.js>` |
| JXA libraries | `.ts` → compiled to `.js` | Loaded via `eval()` at runtime by CLI scripts |
| Plugin code (Omni Automation) | `.js` (already in OmniFocus plugin format) | Runs inside OmniFocus |
| Plugin generator | `.ts` → compiled to `.js` via `tsc` | `node generate_plugin.js` |

**TypeScript compilation notes for JXA scripts:**
- JXA is not Node.js — compiled output must not use `require()` or ESM `import`
- Use `"module": "None"` in tsconfig for JXA scripts, or compile to a single bundled IIFE
- OmniFocus type definitions already exist at `typescript/omnifocus.d.ts` and `typescript/omnifocus-extensions.d.ts`
- The existing IIFE pattern in `taskQuery.js` is the correct target output shape

## Problem Statement

### GTD Coaching Questions Without Script Coverage

| GTD Coaching Question | Script Exists? | Gap |
|---|---|---|
| "How many items are in your inbox?" | No | Need `inbox-count` / `inbox-list` |
| "Do all active projects have next actions?" | No CLI | `insightPatterns.js` (Omni Automation only) |
| "What's in your Waiting For list?" | No | Need `waiting-for` (tag-based filter missing from JXA CLI) |
| "What's on your Someday/Maybe?" | No | Need `someday-maybe` (on-hold projects, unverified SQLite value) |
| "What's overdue?" | Partial | `taskQuery.getOverdueTasks` exists but `manage_omnifocus.js` doesn't expose it |
| "What did you complete this week?" | No | Need `recently-completed` with date range; `completionDate` bug blocks this |
| "How healthy is your GTD system?" | No CLI | `insightPatterns.generateInsights` (Omni Automation only) |
| "Which projects are neglected?" | No | Need `neglected-projects` |
| "What's today?" | ✅ `today` | — |
| "What's flagged?" | ✅ `flagged` | — |
| "What's coming up?" | ✅ `due-soon` | — |

### Confirmed Bugs (Fix Regardless of Scope)

**`completionDate` missing from `formatTaskInfo()`** — `taskQuery.js` `formatTaskInfo()` does not include `completionDate`, but `getTaskInfo()` does. This means `list --filter completed` returns tasks with no completion date, breaking all date-range filtering. Fix: add `completionDate: task.completionDate() ? task.completionDate().toISOString() : null` to `formatTaskInfo()`. Same fix needed in `manage_omnifocus.js` (which has its own inline `formatTaskInfo` copy).

**Agent routing table has placeholder without implementation** — `omnifocus-agent.md` weekly review example says "Query stalled projects" but provides no command. Will confuse the agent.

### Library Issues

- `insightPatterns.js` has syntax errors: missing closing `}` and `)` on filter callbacks in `detectStalledProjects`, `detectWaitingForAging`, `detectOverdueAccumulation`, `detectTaglessTasksPattern`
- `patterns.js` also has syntax errors and a placeholder `callFoundationModel()` that throws
- Two CLI scripts (`manage_omnifocus.js`, `omnifocus.js`) overlap entirely — only `manage_omnifocus.js` is documented; `omnifocus.js` adds complexity with no unique capability
- `query_omnifocus.py` is a Python script in a TypeScript/JavaScript project — should be deprecated and replaced

## Proposed Solution

### Architecture Decision

**New `gtd-queries.ts`** — a dedicated TypeScript JXA script for GTD diagnostic queries (project-level + system-level health checks), compiled to `gtd-queries.js`.

**`taskQuery.ts`** — migrate `taskQuery.js` JXA library to TypeScript source with 6 new project-level query functions. Compiled output replaces existing `taskQuery.js`.

The separation stays clean:
- `manage_omnifocus.js` = task-focused CRUD + basic task queries (what to do)
- `gtd-queries.ts` → `gtd-queries.js` = system-level GTD health diagnostics (how the system is doing)

## Technical Approach

### Runtime Environments

There are two distinct runtimes — code cannot be shared between them:

| Runtime | Scripts | Context |
|---|---|---|
| JXA (osascript) | `manage_omnifocus.js`, `gtd-queries.js`, `libraries/jxa/*.js` | Command line, Automation permissions required |
| Omni Automation | `assets/AITaskAnalyzer.omnifocusjs/Resources/*.js`, `libraries/omni/*.js` | Inside OmniFocus plugin |

The Omni Automation environment provides shared utility classes from [omni-automation.com/shared](https://omni-automation.com/shared/index.html) that should be used in Omni Automation libraries:
- `Formatter.Date` — consistent date display (use instead of `.toLocaleDateString()`)
- `Formatter.Duration` — format time estimates
- `Calendar.current` — date arithmetic (use instead of raw JS `setDate()` math)

These shared classes are **not available in JXA** — JXA uses standard JavaScript `Date`.

### Phase 1: Fix `completionDate` Bug in `formatTaskInfo()`

**Files to fix:**
- `scripts/libraries/jxa/taskQuery.js` — add `completionDate` to `formatTaskInfo()` return object
- `scripts/manage_omnifocus.js` — same fix to its inline copy of `formatTaskInfo`

This is the highest priority fix — it's a data correctness bug affecting all completed-task queries.

```js
// Add to formatTaskInfo() return object in both files:
completionDate: task.completionDate() ? task.completionDate().toISOString() : null,
```

### Phase 2: Migrate `taskQuery.js` → `taskQuery.ts` with New Project-Level Functions

**File**: `scripts/libraries/jxa/taskQuery.ts` (TypeScript source; `taskQuery.js` becomes compiled output)

Add 6 new project-level query functions alongside the existing task-level ones:

```typescript
// scripts/libraries/jxa/taskQuery.ts (additions — full type signatures)

interface ProjectInfo {
  name: string;
  status: string;
  taskCount: number;
  availableTaskCount: number;
  lastModified: string | null;
}

interface WaitingForTask {
  name: string;
  project: string;
  tags: string[];
  daysWaiting: number;
  addedDate: string | null;
}

// Get inbox tasks (distinct from flattenedTasks — uses doc.inboxTasks)
taskQuery.getInboxTasks = function(doc: OmniFocusDocument): TaskInfo[] { ... };

// Active projects with 0 available next actions
// Uses numberOfAvailableTasks scalar property for performance (avoids O(n×m) filter)
// Cap: max 50 results
taskQuery.getStalledProjects = function(doc: OmniFocusDocument): ProjectInfo[] { ... };

// Tasks tagged with a name matching waitingTagPattern (default: /waiting/i)
// Includes age in days from addedDate
// Cap: max 50 results
taskQuery.getWaitingForTasks = function(
  doc: OmniFocusDocument,
  waitingTagPattern?: RegExp
): WaitingForTask[] { ... };

// Projects with status = on-hold (OmniFocus's Someday/Maybe equivalent)
taskQuery.getSomedayMaybeProjects = function(doc: OmniFocusDocument): ProjectInfo[] { ... };

// Tasks completed within the last N days (uses completionDate)
// Cap: max 100 results
taskQuery.getRecentlyCompleted = function(
  doc: OmniFocusDocument,
  days?: number
): TaskInfo[] { ... };

// Active projects not modified in > thresholdDays days
taskQuery.getNeglectedProjects = function(
  doc: OmniFocusDocument,
  thresholdDays?: number
): ProjectInfo[] { ... };
```

**Inbox implementation note**: Use `doc.inboxTasks()` directly rather than filtering `flattenedTasks` for `containingProject === null`. This avoids the ambiguity where a project named "Inbox" is confused with the real inbox.

**On-hold status**: Before implementing `getSomedayMaybeProjects`, verify the exact project status enum value using:
```bash
osascript -l JavaScript -e 'const app = Application("OmniFocus"); const doc = app.defaultDocument; console.log(JSON.stringify(doc.flattenedProjects.filter(p => p.status() !== "active").slice(0, 5).map(p => p.status())))'
```

**Performance guard**: Use `p.numberOfAvailableTasks()` scalar instead of `p.flattenedTasks().filter(...)` for stalled project detection to prevent OmniFocus freezes on large databases.

### Phase 3: New `gtd-queries.ts` JXA Script

**File**: `scripts/gtd-queries.ts` → compiled to `scripts/gtd-queries.js`

A JXA CLI script with the same `--flag value` interface pattern as `manage_omnifocus.js`. All output is JSON.

**Actions:**

| Action | Library Call | Returns |
|---|---|---|
| `inbox-count` | `taskQuery.getInboxTasks()` | `{ count, items: [{ name, addedDate }] }` |
| `stalled-projects` | `taskQuery.getStalledProjects()` | `[{ name, taskCount, availableTaskCount }]` |
| `waiting-for` | `taskQuery.getWaitingForTasks()` | `[{ name, project, daysWaiting }]` |
| `someday-maybe` | `taskQuery.getSomedayMaybeProjects()` | `[{ name, taskCount, lastModified }]` |
| `overdue` | `taskQuery.getOverdueTasks()` (existing) | `[{ name, project, dueDate, daysOverdue }]` |
| `recently-completed` | `taskQuery.getRecentlyCompleted()` | `[{ name, project, completionDate }]` |
| `neglected-projects` | `taskQuery.getNeglectedProjects()` | `[{ name, daysSinceModified }]` |
| `system-health` | All above, aggregated | Composite health summary |

**CLI usage (compiled JS):**
```bash
osascript -l JavaScript scripts/gtd-queries.js --action inbox-count
osascript -l JavaScript scripts/gtd-queries.js --action stalled-projects
osascript -l JavaScript scripts/gtd-queries.js --action waiting-for --tag-pattern "waiting"
osascript -l JavaScript scripts/gtd-queries.js --action recently-completed --days 7
osascript -l JavaScript scripts/gtd-queries.js --action system-health
```

**`system-health` output:**
```json
{
  "inbox": { "count": 12 },
  "projects": { "active": 24, "stalled": 3, "onHold": 8, "neglected": 2 },
  "tasks": { "overdue": 7, "waitingFor": 5, "agingWaiting": 2 },
  "timestamp": "2026-02-28T10:00:00Z"
}
```

**TypeScript compilation**: Uses same `tsconfig.json` approach as `generate_plugin.ts`. Output must be self-contained (no `require`/`import` in compiled JS). The JXA library is loaded via the existing IIFE eval pattern.

### Phase 4: Expose `overdue` in `manage_omnifocus.js`

One-line addition to the action dispatch switch — `taskQuery.getOverdueTasks` is already implemented:

```js
// manage_omnifocus.js — add to action switch:
case 'overdue':
  result = taskQuery.getOverdueTasks(doc);
  break;
```

Also update the SKILL.md to document this action.

### Phase 5: Fix Omni Automation Library Syntax Errors

**Files**: `scripts/libraries/omni/insightPatterns.js`, `scripts/libraries/omni/patterns.js`

Fix missing closing braces/parentheses in filter callbacks:
- `detectStalledProjects`: missing `})` closing `projects.forEach` callback (line ~54)
- `detectWaitingForAging`: filter callback missing `}` (line ~74)
- `detectOverdueAccumulation`: filter callback missing `}` (line ~117)
- `detectTaglessTasksPattern`: filter callback missing `}` (line ~181)

Also adopt Omni Automation shared classes where they replace raw JS date math:
- Replace `new Date()` + `setDate()` manipulation with `Calendar.current` operations
- Replace manual date formatting in `formatReport()` with `Formatter.Date`

**Validation after fixing**: Run `scripts/validate-plugin.sh`. The working copies inside `assets/AITaskAnalyzer.omnifocusjs/Resources/` may differ — verify which is authoritative before deciding whether to sync.

### Phase 6: Deprecate `query_omnifocus.py` and `omnifocus.js`

**`query_omnifocus.py`**: This Python script is out of place in a TypeScript/JavaScript project. The `gtd-queries.ts` implementation covers all its capabilities via JXA. Add a deprecation header and document migration path to TypeScript equivalents in SKILL.md.

**`omnifocus.js`**: This duplicate CLI overlaps entirely with `manage_omnifocus.js` (JSON-input style vs. flag-style). The SKILL.md only documents `manage_omnifocus.js`. Add deprecation header, document that `manage_omnifocus.js` is the canonical CLI.

Neither file should be deleted yet — archive period while new scripts are validated.

### Phase 7: Update Agent Routing Table

**File**: `agents/omnifocus-agent.md`

Replace the placeholder "Query stalled projects" in the weekly review example with actual script commands. Add routing entries for the new `gtd-queries.js` actions.

### Phase 8: Skillsmith Evaluation + GTD Coach SKILL.md Integration

Per repository CLAUDE.md: **run skillsmith evaluation before committing any skill changes**.

```bash
# After drafting skill changes, before committing:
uv run plugins/skillsmith/scripts/evaluate_skill.py plugins/omnifocus-manager/skills/gtd-coach/
uv run plugins/skillsmith/scripts/evaluate_skill.py plugins/omnifocus-manager/skills/omnifocus-manager/
```

Use skillsmith feedback to iterate on trigger language, progressive disclosure, and conciseness before committing. Target: beat baseline scores (gtd-coach: 81, omnifocus-manager: 82).

**`gtd-coach` SKILL.md additions** — add a "Data-Grounded Coaching" section:

```markdown
## Data-Grounded Coaching (OmniFocus)

For OmniFocus users, ground coaching in real data using the `omnifocus-manager` skill.
Run the appropriate query, then interpret results through GTD methodology.

### System Health Check
```bash
osascript -l JavaScript plugins/omnifocus-manager/skills/omnifocus-manager/scripts/gtd-queries.js \
  --action system-health
```
Interpret: inbox.count > 20 → Capture/Clarify coaching | projects.stalled > 0 → Project coaching |
tasks.overdue > 10 → Prioritization coaching

### Weekly Review Query Sequence
| Step | Query | Purpose |
|---|---|---|
| Get Clear | `inbox-count` | Guide to inbox zero |
| Get Current | `stalled-projects` | Ensure all projects have next actions |
| Waiting For | `waiting-for` | Follow up on delegated items |
| Someday/Maybe | `someday-maybe` | Promote, keep, or drop |
| Celebrate | `recently-completed --days 7` | Acknowledge wins |
| Plan Week | `manage_omnifocus.js --action due-soon --days 14` | Confirm priorities |

**@waiting tag convention**: Queries assume tag name contains "waiting" (case-insensitive).
If you use a different tag name (e.g., "delegated", "pending"), specify:
`--tag-pattern <your-tag-name>` or the query will return empty results.
```

## Edge Cases

| Scenario | Expected Behavior |
|---|---|
| Empty inbox | Return `{ count: 0 }` — coach celebrates inbox zero |
| No stalled projects | Return `[]` — coach acknowledges healthy system |
| OmniFocus not running | Error: "OmniFocus must be open to run this query" |
| 200+ stalled projects | Cap at 50, include summary count: "Showing 50 of 87" |
| User tags delegated items "pending" not "waiting" | Empty result + note: "No @waiting tasks found. If you use a different tag, use --tag-pattern" |
| Sequential project where first task is blocked | Not counted as stalled (uses `Task.Status.Available` which accounts for sequential dependencies) |
| Project literally named "Inbox" | Not confused with OmniFocus inbox — `getInboxTasks` uses `doc.inboxTasks()`, not `containingProject` filter |
| completionDate is null on completed task | Return `null` for `completionDate` field — do not crash |

## Implementation Phases

### Phase 1: Fix `completionDate` Bug (Immediate, Highest Priority)
- Fix `formatTaskInfo()` in both `taskQuery.js` and `manage_omnifocus.js`
- Run manual test: `manage_omnifocus.js --action list --filter completed` → verify `completionDate` appears

### Phase 2: Migrate `taskQuery.js` → TypeScript + Add Project Functions
- Create `scripts/libraries/jxa/taskQuery.ts` with type annotations + new project-level functions
- Verify on-hold status string value before implementing `getSomedayMaybeProjects`
- Compile to `taskQuery.js` (replaces existing)
- Test each new function via quick osascript call

### Phase 3: Create `gtd-queries.ts`
- New TypeScript JXA script with 8 diagnostic actions
- Compiles to `gtd-queries.js`
- JSON output consistent with `manage_omnifocus.js` format
- Manual testing of each action against live OmniFocus

### Phase 4: Expose `overdue` + Fix Omni Libs
- Add `overdue` case to `manage_omnifocus.js` dispatch
- Fix syntax errors in `insightPatterns.js` and `patterns.js`
- Adopt `Formatter.Date` and `Calendar.current` in omni libs

### Phase 5: Deprecate `query_omnifocus.py` + `omnifocus.js`
- Add deprecation headers to both files
- Update SKILL.md to remove references to these scripts
- Update agent routing table in `omnifocus-agent.md`

### Phase 6: Skillsmith → GTD Coach SKILL.md + omnifocus-manager SKILL.md
- Run skillsmith BEFORE finalizing SKILL.md changes
- Incorporate skillsmith feedback
- Add "Data-Grounded Coaching" section to gtd-coach SKILL.md
- Update omnifocus-manager SKILL.md to document `gtd-queries.js` and new actions

### Phase 7: Validation & Release
- Run `scripts/validate-plugin.sh`
- Run skillsmith (final scores for IMPROVEMENT_PLAN.md)
- Update both IMPROVEMENT_PLAN.md files with new version entry
- Check off Issue #63 Pillar 1 acceptance criteria

## Acceptance Criteria

### Functional
- [ ] `gtd-queries.js --action inbox-count` returns inbox count in ≤2 seconds
- [ ] `gtd-queries.js --action stalled-projects` returns active projects with 0 available next actions (capped at 50)
- [ ] `gtd-queries.js --action waiting-for` returns @waiting-tagged tasks with age in days
- [ ] `gtd-queries.js --action someday-maybe` returns on-hold projects
- [ ] `gtd-queries.js --action overdue` returns tasks past due date with `daysOverdue` field
- [ ] `gtd-queries.js --action recently-completed --days 7` returns completed tasks with `completionDate`
- [ ] `gtd-queries.js --action system-health` returns composite health object
- [ ] `manage_omnifocus.js --action overdue` works
- [ ] `formatTaskInfo()` includes `completionDate` in all list-style outputs
- [ ] All new `taskQuery.ts` functions return `[]` (not errors) on empty databases
- [ ] `insightPatterns.js` syntax errors fixed
- [ ] `gtd-coach` SKILL.md has data-grounded coaching section

### TypeScript & Code Quality
- [ ] `taskQuery.ts` compiles without errors against `typescript/omnifocus.d.ts`
- [ ] `gtd-queries.ts` compiles without errors
- [ ] No `require()` or `import` in compiled JXA output
- [ ] `query_omnifocus.py` has deprecation header
- [ ] `omnifocus.js` has deprecation header

### Non-Functional
- [ ] Results capped: stalled-projects ≤50, recently-completed ≤100
- [ ] JSON output envelope matches `manage_omnifocus.js` format
- [ ] Empty states return `[]` not errors
- [ ] OmniFocus-closed error is actionable

### Quality Gates
- [ ] Both skills' skillsmith eval scores ≥ baseline (gtd-coach: 81, omnifocus-manager: 82)
- [ ] `validate-plugin.sh` passes
- [ ] Issue #63 Pillar 1 criteria checked off

## File Map

### New Files
- `skills/omnifocus-manager/scripts/gtd-queries.ts` — TypeScript source for GTD diagnostic CLI
- `skills/omnifocus-manager/scripts/gtd-queries.js` — compiled JXA output (generated, committed)
- `skills/omnifocus-manager/scripts/libraries/jxa/taskQuery.ts` — TypeScript migration of `taskQuery.js`

### Modified Files
- `skills/omnifocus-manager/scripts/libraries/jxa/taskQuery.js` — compiled output (add completionDate fix + new functions)
- `skills/omnifocus-manager/scripts/manage_omnifocus.js` — add `overdue` action, fix `completionDate` in `formatTaskInfo`
- `skills/omnifocus-manager/scripts/libraries/omni/insightPatterns.js` — fix syntax errors, adopt shared classes
- `skills/omnifocus-manager/scripts/libraries/omni/patterns.js` — fix syntax errors
- `skills/omnifocus-manager/SKILL.md` — add `gtd-queries.js` docs, remove Python/omnifocus.js references
- `agents/omnifocus-agent.md` — replace stalled-projects placeholder with real command
- `skills/gtd-coach/SKILL.md` — add Data-Grounded Coaching section
- `skills/omnifocus-manager/IMPROVEMENT_PLAN.md` — new version entry
- `skills/gtd-coach/IMPROVEMENT_PLAN.md` — new version entry

### Deprecated (Not Deleted Yet)
- `skills/omnifocus-manager/scripts/query_omnifocus.py` — add deprecation header; capabilities replaced by TypeScript
- `skills/omnifocus-manager/scripts/omnifocus.js` — add deprecation header; `manage_omnifocus.js` is canonical

### No Changes
- `assets/AITaskAnalyzer.omnifocusjs/` — plugin assets unchanged; working copies of libs are independent
- `scripts/generate_plugin.js` — plugin generator unchanged
- `scripts/validate-plugin.sh` — validator unchanged
- `agents/omnifocus-agent.md` — routing logic unchanged except for stalled-projects placeholder fix

## Dependencies & Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| `doc.inboxTasks()` behaves differently than expected in JXA | Low | Test early: `osascript -e 'Application("OmniFocus").defaultDocument.inboxTasks().length'` |
| `p.numberOfAvailableTasks()` not available in JXA (vs. Omni Automation) | Medium | Test first; fallback to `p.flattenedTasks().filter(...)` with a 50-project cap |
| On-hold project status string is not "on hold" in JXA | Medium | Verify with live query before implementing |
| TypeScript IIFE compilation is tricky — circular reference with `this.` | Medium | Use explicit module object (existing IIFE pattern already handles this) |
| Fixing `insightPatterns.js` syntax breaks something in AITaskAnalyzer | Low | Reference libs are separate from working asset copies; `validate-plugin.sh` catches mismatches |
| `project.modificationDate()` not exposed in JXA API | Medium | Test first; if unavailable, omit from `neglected-projects` and document |

## References

### Internal
- Issue #63: Two-track vision — Pillar 1 (Query) is primary deliverable
- `skills/omnifocus-manager/scripts/libraries/jxa/taskQuery.js` — JXA query library to migrate
- `skills/omnifocus-manager/scripts/libraries/omni/insightPatterns.js` — Omni pattern lib (fix syntax)
- `skills/omnifocus-manager/scripts/manage_omnifocus.js` — primary JXA CLI (add `overdue`)
- `skills/omnifocus-manager/scripts/generate_plugin.ts` — TypeScript compilation pattern to follow
- `skills/omnifocus-manager/typescript/omnifocus.d.ts` — OmniFocus type definitions for TypeScript source
- `docs/lessons/omnifocus-manager-refinement-2026-01-18.md` — critical gotchas (IIFE scope, validation)
- `docs/plans/2026-02-28-feat-omnifocus-manager-skill-split-plan.md` — v5.0.0 architecture context

### External
- [Omni Automation Shared Classes](https://omni-automation.com/shared/index.html) — Formatter.Date, Calendar
- [OmniFocus Automation Docs](https://omni-automation.com/omnifocus/) — Task, Project, Tag APIs

### Related Issues
- Issue #63: Parent — Query (Pillar 1) is this plan's deliverable
- Issue #62: Completed — dailyReview + weeklyReview (provides in-plugin coaching context)
