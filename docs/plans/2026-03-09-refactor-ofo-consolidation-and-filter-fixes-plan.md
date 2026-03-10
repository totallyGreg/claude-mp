---
title: "Consolidate ofo Action Scripts and Fix Remaining Weak Filters"
type: refactor
status: completed
date: 2026-03-09
issue: https://github.com/totallyGreg/claude-mp/issues/98
---

# Consolidate ofo Action Scripts and Fix Remaining Weak Filters

## Overview

Two related improvements to omnifocus-manager:

1. **Consolidate** 7 separate `omni-actions/*.js` files into a single inline dispatcher in `scripts/ofo`, eliminating per-script OmniFocus approval and the `ofo setup` command.
2. **Fix** 8 remaining `taskQuery.js` functions that still use weak `task.completed()`/`task.dropped()` filters instead of the correct `effectivelyCompleted()`/`effectivelyDropped()` + `completed()` pattern established in v7.1.0 (#97).

These combine naturally: the dispatcher rewrite is the right time to apply correct filters to the Omni Automation code, and the JXA filter sweep completes the work started in #97.

## Problem Statement

### Consolidation

`ofo setup` requires approving 7 separate scripts in OmniFocus (one per `.js` file). Each edit to any script re-triggers approval for that script. A single dispatcher script means one approval covers all commands.

### Weak Filters

8 functions in `taskQuery.js` still use `task.completed()` / `task.dropped()` instead of the reliable triple-check pattern. These functions feed into system-health, weekly review, and slash commands:

| Function | Line | Current Filter | Bug |
|----------|------|---------------|-----|
| `getTodayTasks` | 156 | `completed() \|\| dropped()` | Misses parent-completed tasks |
| `getDueSoon` | 186 | `completed() \|\| dropped()` | Same |
| `getFlagged` | 207 | `completed() \|\| dropped()` | Same |
| `searchTasks` | 252 | `completed()` | Misses dropped + parent-completed |
| `listTasks` | 130 | `completed()` / `dropped()` | Split checks, misses parent |
| `getWaitingForTasks` | 463 | `completed() \|\| dropped()` | Misses parent-completed |
| `searchTasksByTag` | 311-312 | `completed()` / `dropped()` | Split checks |
| `getRepeatingTasks` | 850-851 | `completed()` / `dropped()` | Split checks |

**Correct pattern** (from #97):
```javascript
// JXA — triple-check for parent completion + repeating instances
if (task.effectivelyCompleted() || task.effectivelyDropped()) return;
if (task.completed()) return;
```

## Proposed Solution

### Phase 1: Consolidate ofo dispatcher

Inline all 7 action scripts into a single heredoc dispatcher in `scripts/ofo`. The dispatcher routes on `args.action`:

```javascript
var args = argument;
var action = args.action;

if (action === "info") { /* ofo-info logic */ }
else if (action === "complete") { /* ofo-complete logic */ }
else if (action === "create") { /* ofo-create logic */ }
else if (action === "update") { /* ofo-update logic */ }
else if (action === "search") { /* ofo-search logic */ }
else if (action === "list") { /* ofo-list logic */ }
else if (action === "perspective") { /* ofo-perspective logic */ }
else { Pasteboard.general.string = JSON.stringify({success: false, error: "Unknown action: " + action}); }
```

Update `run_action()` in the bash wrapper to use the inline script with `action` in the arg JSON instead of reading separate files.

**While inlining, apply `Task.Status.Available`/`Task.Status.Completed`/`Task.Status.Dropped` filters consistently** — these are the Omni Automation equivalents of the JXA triple-check.

### Phase 2: Fix taskQuery.js weak filters

Apply the correct pattern to all 8 functions. Each is a one-line change:

```javascript
// BEFORE (weak)
if (task.completed() || task.dropped()) return;

// AFTER (correct)
if (task.effectivelyCompleted() || task.effectivelyDropped()) return;
if (task.completed()) return;
```

For `listTasks` which has `filter === 'active'` / `filter === 'completed'` branches, only fix the `active` branch.

For `searchTasksByTag` which has `includeCompleted` option, preserve the option but upgrade the default exclusion filter.

### Phase 3: Cleanup and validation

- Delete `scripts/omni-actions/` directory
- Remove `cmd_setup()` from `scripts/ofo`
- Update SKILL.md: remove setup prerequisite, remove omni-actions references, add perspective command docs
- Run `bash scripts/test-queries.sh`
- Run skillsmith evaluation
- Run plugin-dev validation

## Acceptance Criteria

### Consolidation

- [ ] Single inline script in `scripts/ofo` handles all 7 commands (info, complete, create, update, search, list, perspective)
- [ ] First `ofo` command triggers one-time OmniFocus approval — no `ofo setup` needed
- [ ] `cmd_setup()` removed from `scripts/ofo`
- [ ] `scripts/omni-actions/` directory deleted
- [ ] All existing `ofo` commands produce identical JSON output as before
- [ ] `run_action()` updated to use inline script with `action` field routing

### Weak Filters

- [ ] `getTodayTasks` uses `effectivelyCompleted()` + `effectivelyDropped()` + `completed()`
- [ ] `getDueSoon` uses same triple-check
- [ ] `getFlagged` uses same triple-check
- [ ] `searchTasks` uses same triple-check
- [ ] `listTasks` active branch uses same triple-check
- [ ] `getWaitingForTasks` uses same triple-check
- [ ] `searchTasksByTag` default exclusion uses same triple-check
- [ ] `getRepeatingTasks` uses same triple-check

### Validation

- [ ] `bash scripts/test-queries.sh` passes (15+ tests)
- [ ] Skillsmith evaluation >= 90/100
- [ ] Plugin-dev validation passes
- [ ] Manual: `ofo list inbox`, `ofo list overdue`, `ofo info <id>`, `ofo search <term>` all work
- [ ] IMPROVEMENT_PLAN.md updated with version entry and eval score

## Key Files

| File | Change |
|------|--------|
| `scripts/ofo` | Inline all action JS, remove setup, update run_action |
| `scripts/omni-actions/*.js` | Delete all 7 files |
| `scripts/libraries/jxa/taskQuery.js` | Fix 8 functions |
| `SKILL.md` | Remove setup docs, update version |
| `IMPROVEMENT_PLAN.md` | Add version entry |

All paths relative to `plugins/omnifocus-manager/skills/omnifocus-manager/`.

## Risks

| Risk | Mitigation |
|------|-----------|
| Inline script too large for URL encoding | OmniFocus URL scheme handles large scripts; test with actual size |
| Re-approval on any script edit | Scripts are stable after #97 fixes; edits are rare |
| taskQuery.js filter changes affect downstream | All changes are more restrictive (fewer false positives); same pattern proven in #97 |

## Sources

- [#98](https://github.com/totallyGreg/claude-mp/issues/98) — Consolidation proposal
- [#97](https://github.com/totallyGreg/claude-mp/issues/97) — Query accuracy fixes (established the filter pattern)
- `docs/plans/2026-03-09-fix-omnifocus-query-accuracy-plan.md` — v7.1.0 plan with runtime investigation results
- SpecFlow analysis from #97 session — identified the 8 remaining weak-filter functions
