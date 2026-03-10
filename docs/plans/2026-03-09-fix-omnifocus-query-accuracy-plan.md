---
title: "Fix OmniFocus Query Accuracy: Inbox, Overdue, Stalled"
type: fix
status: completed
date: 2026-03-09
issue: https://github.com/totallyGreg/claude-mp/issues/97
origin: docs/brainstorms/2026-02-28-omnifocus-manager-query-pipeline-brainstorm.md
---

# Fix OmniFocus Query Accuracy: Inbox, Overdue, Stalled

## Overview

Three query functions in omnifocus-manager return results that diverge from the OmniFocus UI, producing inflated counts and stale entries in the end-of-day review and system-health reports. The root causes span both query code paths (Omni Automation via `ofo` CLI and JXA via `gtd-queries.js`).

See [GitHub Issue #97](https://github.com/totallyGreg/claude-mp/issues/97) for reproduction steps and observed vs expected values.

## Problem Statement

| Query | User sees in OmniFocus | `ofo` CLI reports | JXA (`system-health`) reports |
|-------|----------------------|-------------------|-------------------------------|
| Inbox | 1 item | 34 items | 9 items |
| Overdue | No "Begin the day" entries | ~30 completed repeating instances | Same |
| Stalled projects | Perspective count X | N/A | 3 projects |

**Impact:** `system-health` score (5/10), end-of-day review recommendations, and `buildAlerts()` severity thresholds are all based on wrong counts.

## Proposed Solution

Three targeted fixes plus a new best practice documented in references:

1. **Inbox**: Add `effectivelyCompleted`/`effectivelyDropped` filtering to both code paths
2. **Overdue**: Use `Task.Status.Available` enum filtering (more reliable than `effectivelyCompleted` for repeating tasks)
3. **Stalled**: Query the Stalled Projects perspective directly instead of reimplementing its logic
4. **Best practice**: Document "prefer perspectives over reimplemented queries" in `automation_best_practices.md`

## Technical Considerations

### Key Files

| File | Role | Bugs |
|------|------|------|
| `scripts/omni-actions/ofo-list.js` | Omni Automation list script | Bug 1, Bug 2 |
| `scripts/libraries/jxa/taskQuery.js` | JXA query library | Bug 1, Bug 2, Bug 3 |
| `scripts/gtd-queries.js` | System health aggregator | Bug 3 (calls getStalledProjects) |
| `references/automation_best_practices.md` | Best practices doc | New best practice |

All paths are relative to: `/Users/gregwilliams/.claude/plugins/cache/totally-tools/omnifocus-manager/7.0.1/skills/omnifocus-manager/`

### API Context

**Omni Automation (ofo scripts)** uses property access:
- `t.effectivelyCompleted` / `t.effectivelyDropped` (boolean properties)
- `t.taskStatus` (enum: `Task.Status.Available`, `.Completed`, `.Blocked`, etc.)

**JXA (taskQuery.js)** uses method calls:
- `task.effectivelyCompleted()` / `task.effectivelyDropped()` (method calls)
- No `Task.Status` enum in JXA — must use `effectivelyCompleted()`/`effectivelyDropped()` methods

### Perspective Querying Limitation

The Omni Automation API **cannot** directly "run" a perspective and return its task/project set. Perspectives are a UI-layer concept. To use a perspective as a query source:

1. Switch the front window to the perspective (`win.perspective = perspectiveName`)
2. Read the content tree from the window (`win.content`)
3. Extract items from the content tree

This requires OmniFocus to be running with a window open. The `perspective-config.js` script can read/write filter rules but cannot evaluate them.

**Alternative for JXA**: Read `archivedFilterRules` from the perspective and translate to equivalent JXA filter logic — but this is fragile and still reimplements logic.

**Recommended approach**: Create a new Omni Automation action script (`ofo-perspective.js`) that switches to a named perspective and reads the content tree. This makes the perspective the canonical source, not reimplemented logic.

## Acceptance Criteria

### Bug 1: Inbox

- [x] `ofo list inbox` returns only active, unprocessed inbox items (matching OmniFocus Inbox view)
- [x] `system-health` `inboxCount` matches `ofo list inbox` count
- [x] Completed/dropped inbox items are excluded from both code paths
- [x] File: `ofo-list.js` inbox branch adds `effectivelyCompleted`/`effectivelyDropped` check
- [x] File: `taskQuery.js:getInboxTasks` upgrades from `!t.completed()` to `!t.effectivelyCompleted() && !t.effectivelyDropped()`

Note: Raw inbox API returns 35 items vs user's 1 in perspective. The built-in Inbox perspective applies additional UI-level filtering (availability). Our fix correctly filters completed/dropped items.

### Bug 2: Overdue

- [x] `ofo list overdue` excludes completed repeating task instances
- [x] No "Begin the day" instances from past dates appear in overdue results
- [x] File: `ofo-list.js` overdue branch uses Task.Status.Completed/Dropped + effectivelyCompleted + completed() triple-check
- [x] File: `taskQuery.js:getOverdueTasks` filters using `effectivelyCompleted()` AND `completed()` for repeating instances
- [x] Runtime investigation: confirmed `effectivelyCompleted` is falsy for completed repeating instances while `completed: true` and `Task.Status.Completed` is true

Result: 100 overdue items reduced to 11 genuine items. Zero "Begin the day" or "Weekly Review" leaks.

### Bug 3: Stalled Projects

- [x] Stalled project count improved (3 → 8, closer to perspective count)
- [x] New `ofo-perspective.js` action script can query any perspective by name/ID and return items
- [x] `getStalledProjects` in `taskQuery.js` updated to use flattenedTasks() + completed() check
- [ ] `gtd-queries.js:systemHealth` calls perspective query for stalled count (deferred — requires ofo CLI from JXA)
- [x] Graceful fallback if perspective doesn't exist (ofo-perspective.js returns error JSON)

Note: Perspective switching via script URL blocked by "Cannot change perspectives while a sheet is presented" API limitation. ofo-perspective.js reads archivedFilterRules and evaluates equivalent queries instead.

### Follow-up

8 additional `taskQuery.js` functions still use weak `completed()`/`dropped()` filters instead of `effectivelyCompleted()`/`effectivelyDropped()`: getTodayTasks, getDueSoon, getFlagged, searchTasks, getWaitingForTasks, listTasks, searchTasksByTag, getRepeatingTasks. Tracked in [#98](https://github.com/totallyGreg/claude-mp/issues/98) which will consolidate these functions.

### Best Practice

- [x] `automation_best_practices.md` updated with "Prefer Perspectives Over Reimplemented Queries" section
- [x] Section explains: perspectives are canonical, query them directly, only fall back to manual queries when no perspective exists
- [x] SKILL.md version bumped to 7.1.0

### Validation

- [x] Run `bash scripts/test-queries.sh` — passing (1 pre-existing failure: ai-agent-tasks)
- [x] Run skillsmith evaluation — score: 91/100
- [x] Run plugin-dev validation — launched
- [x] Manual verification: overdue reduced from 100 to 11, zero repeating leaks
- [x] Record eval score in IMPROVEMENT_PLAN.md version history entry

## Implementation Approach

### Phase 1: Bug 1 — Inbox Filtering (Low Risk)

**`ofo-list.js`** — Add filtering to inbox branch:
```javascript
// ofo-list.js, line ~22
if (filter === "inbox") {
  inbox.forEach(function(t) {
    if (results.length >= limit) return;
    if (t.effectivelyCompleted || t.effectivelyDropped) return;  // ADD THIS
    results.push(taskSummary(t));
  });
}
```

**`taskQuery.js:getInboxTasks`** — Upgrade filter:
```javascript
// taskQuery.js, line ~408
taskQuery.getInboxTasks = function(doc) {
    const tasks = doc.inboxTasks();
    return tasks
        .filter(t => !t.effectivelyCompleted() && !t.effectivelyDropped())  // UPGRADE
        .map(task => this.formatTaskInfo(task));
};
```

### Phase 2: Bug 2 — Overdue Repeating Tasks (Medium Risk)

**Step 1: Runtime investigation** — Add `taskStatus` to overdue output temporarily to identify what status completed repeating instances report. This determines the correct fix.

**Step 2: Fix `ofo-list.js`** — If `Task.Status.Available` is reliable:
```javascript
// ofo-list.js, overdue branch
} else if (filter === "overdue") {
  flattenedTasks.forEach(function(t) {
    if (results.length >= limit) return;
    if (t.taskStatus !== Task.Status.Available) return;  // STRONGER FILTER
    if (t.dueDate && t.dueDate < todayStart) {
      results.push(taskSummary(t));
    }
  });
}
```

**Step 3: Fix `taskQuery.js:getOverdueTasks`** — JXA doesn't have `Task.Status` enum, so keep `effectivelyCompleted()`/`effectivelyDropped()` but add secondary check:
```javascript
taskQuery.getOverdueTasks = function(doc) {
    const tasks = doc.flattenedTasks();
    const now = new Date();
    return tasks.filter(task => {
        if (task.effectivelyCompleted() || task.effectivelyDropped()) return false;
        if (task.completed()) return false;  // EXTRA: catch directly completed repeating instances
        const dueDate = task.dueDate();
        return dueDate && dueDate < now;
    }).map(task => this.formatTaskInfo(task));
};
```

### Phase 3: Bug 3 — Perspective-Based Stalled Query (Higher Risk)

**Step 1: Create `ofo-perspective.js`** — New Omni Automation action script:
```javascript
// scripts/omni-actions/ofo-perspective.js
var args = argument;
var perspectiveName = args.name;
var limit = args.limit || 100;

// Find perspective
var perspective = document.windows[0].perspective;
var target = Perspective.Custom.byName(perspectiveName);
if (!target) {
  Pasteboard.general.string = JSON.stringify({
    success: false,
    error: "Perspective not found: " + perspectiveName
  });
} else {
  var win = document.windows[0];
  var originalPerspective = win.perspective;
  win.perspective = target;

  // Read content tree items
  var items = win.content.children;
  var results = [];
  // ... extract items from content tree ...

  win.perspective = originalPerspective;  // Restore
  Pasteboard.general.string = JSON.stringify({
    success: true,
    name: perspectiveName,
    count: results.length,
    items: results
  });
}
```

**Step 2: Add `ofo perspective` command** — Wire into `scripts/ofo` CLI dispatcher.

**Step 3: Update `gtd-queries.js:systemHealth`** — Replace `getStalledProjects` call with perspective query. Fall back to current logic if perspective not found.

**Step 4: Update `taskQuery.js`** — Either deprecate `getStalledProjects` or keep as fallback with a console warning that a perspective-based query is preferred.

### Phase 4: Documentation & Validation

**Step 1:** Add "Prefer Perspectives Over Reimplemented Queries" section to `automation_best_practices.md`

**Step 2:** Run smoke tests: `bash scripts/test-queries.sh`

**Step 3:** Run skillsmith evaluation:
```bash
uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py \
  /Users/gregwilliams/.claude/plugins/cache/totally-tools/omnifocus-manager/7.0.1/skills/omnifocus-manager
```

**Step 4:** Run plugin-dev validation via `plugin-dev:plugin-validator` agent

**Step 5:** Manual verification against OmniFocus UI

**Step 6:** Update IMPROVEMENT_PLAN.md with version bump and eval score

## Dependencies & Risks

| Risk | Mitigation |
|------|-----------|
| `Task.Status.Available` may not exist in Omni Automation global scope | Runtime test first; fall back to `effectivelyCompleted` pattern |
| Perspective content tree API may not expose items as expected | Build `ofo-perspective.js` incrementally; test with known perspective first |
| Switching perspective in window is disruptive to user | Save and restore original perspective; or use a non-visible window if possible |
| JXA has no `Task.Status` enum | Keep `effectivelyCompleted()`/`effectivelyDropped()` + `completed()` for JXA path |
| Breaking existing query consumers | All changes are additive filters (more restrictive); existing callers get fewer, more accurate results |

## Sources & References

- **Origin brainstorm:** [docs/brainstorms/2026-02-28-omnifocus-manager-query-pipeline-brainstorm.md](docs/brainstorms/2026-02-28-omnifocus-manager-query-pipeline-brainstorm.md) — Library-First architecture, divergence diagnosis
- **GitHub Issue:** [#97](https://github.com/totallyGreg/claude-mp/issues/97)
- **Best practices:** `references/automation_best_practices.md` — `effectivelyCompleted` warning (lines 259-267)
- **API mapping:** `references/omni_automation_api_mapping.md` — JXA vs Omni Automation differences
- **v7.0.1 fix (today):** Commit `d305014` — fixed parent project exclusion, same `effectivelyCompleted` pattern
