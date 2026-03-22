---
title: "feat(ofo): expose native OmniFocus fields for richer GTD coaching"
type: feat
status: completed
date: 2026-03-22
github_issue: "https://github.com/totallyGreg/claude-mp/issues/125"
---

# feat(ofo): expose native OmniFocus fields for richer GTD coaching

## Overview

Phase 2 of the System Map bootstrap (#123). The ofo CLI is missing several native OmniFocus
fields that are central to GTD coaching. Currently, coaching on duration falls back to tag
inference (`15min` tags) even when the user has set `estimatedMinutes` on tasks. Scheduled
intent via `plannedDate` is completely invisible. Review cadence (`reviewInterval`,
`nextReviewDate`) and recurrence (`repetitionRule`) cannot be surfaced at all.

This plan exposes all of these fields through the ofo CLI and enriches `ofo stats` with
coaching-relevant counts. It also fixes the `systemDiscovery.js` `TIME_PATTERNS` conflation
so the System Map JSON separates duration tags from scheduling-context tags, eliminating the
manual split the agent currently does at read time.

## Problem Statement

| Field | Location | Gap | Coaching Impact |
|-------|----------|-----|-----------------|
| `plannedDate` | Task + Project | Absent from all ofo output | `ofo list today` misses scheduled tasks; agent cannot surface Forecast intent |
| `estimatedMinutes` | `taskSummary()` | Present in `getTask()` but absent from `listTasks()` output (line 198-208) | List views can't show effort; agent must do a second `ofo info` call |
| `estimatedMinutes` | Project branch of `getTask()` | Absent (lines 19-38) | Project-level effort rollups impossible |
| `reviewInterval` / `nextReviewDate` | Project | Entirely absent | Cannot flag overdue reviews or coach on cadence |
| `repetitionRule` | Task | Entirely absent | Cannot distinguish repeating from one-off tasks |
| `TIME_PATTERNS` | `systemDiscovery.js` line 45 | Duration + scheduling-context mixed in one array | Agent must manually split `tags.categories.time[]` every time it reads the map |
| `ofo stats` | `getStats()` | Only inbox/flagged/overdue/projects/tasks | Missing coaching-relevant counts: review overdue, planned today, tasks with estimates |

## Design Principle

Where OmniFocus provides a native field, use it — do not infer the same signal from text tags.

| Signal | Native field | Tag inference (avoid) |
|--------|-------------|----------------------|
| Task duration/effort | `estimatedMinutes` | `15min`, `30min`, `1hr` tags |
| Scheduled intent | `plannedDate` | Date-in-task-name patterns |
| Review cadence | `reviewInterval` / `nextReviewDate` | Folder naming conventions |
| Recurrence | `repetitionRule` | Naming suffixes like "daily" |

## Technical Approach

### plannedDate migration guard

`plannedDate` on both Task and Project **requires that the OmniFocus database has been migrated
to support planned dates** (OF4 only). Accessing the property before migration throws. Always
wrap in try/catch:

```typescript
// ofo-core.ts read pattern — use at every plannedDate read site
let plannedDate: string | null = null;
try { plannedDate = t.plannedDate ? t.plannedDate.toISOString() : null; } catch (_) {}
```

The same guard is needed on **write** paths (`createTask`, `updateTask`) — setting
`t.plannedDate` on an unmigrated database also throws:

```typescript
// ofo-core.ts write pattern
if (args.plannedDate !== undefined) {
  try { t.plannedDate = args.plannedDate === null ? null : new Date(args.plannedDate as string); } catch (_) {}
}
```

### plannedDate type declaration

`plannedDate` is an OF4-only property **absent from `omnifocus.d.ts`**. Without type
declarations, `npm run build:cli` will fail. Add to `ofo-core-ambient.d.ts`:

```typescript
interface Task { plannedDate: Date | null; }
interface Project { plannedDate: Date | null; }
```

### taskSummary() is a nested function

`taskSummary()` is defined **inside `listTasks()`** (lines 198-208), not at module level. Edits
must target the nested definition specifically — not a top-level function.

### repetitionRule shape

When a task repeats, `t.repetitionRule` is a `Task.RepetitionRule` object. When it doesn't,
it is `null`. Return a lean shape:

```typescript
repetitionRule: t.repetitionRule ? {
  ruleString: t.repetitionRule.ruleString,           // ICS string, e.g. "FREQ=DAILY"
  scheduleType: String(t.repetitionRule.scheduleType) // "Regularly" | "FromCompletion"
} : null
```

### reviewInterval shape

`Project.ReviewInterval` is a value object with `steps` (Number) and `unit` (String):

```typescript
reviewInterval: p.reviewInterval ? {
  steps: p.reviewInterval.steps,   // e.g. 14
  unit: p.reviewInterval.unit       // e.g. "days", "weeks"
} : null,
nextReviewDate: p.nextReviewDate ? p.nextReviewDate.toISOString() : null,
lastReviewDate: p.lastReviewDate ? p.lastReviewDate.toISOString() : null
```

### --planned-date flag pattern

Follows the existing `--due` / `--defer` pattern in `ofo-cli.ts` (lines 234-242):
- Accepts ISO date string (`YYYY-MM-DD`) or `"clear"` to unset
- In `cmdCreate`: add `plannedDate` variable (line 142), case in flag switch, `argObj` construction (line 211-218), **and stdin merge paths** (batch at lines 172-178, single at lines 196-202)
- In `cmdUpdate`: add to the flag switch (same `'clear' ? null : val` pattern)
- In `cmdHelp()`: add `--planned-date` to Create options and Update options sections; update `today` filter description to "Due today, flagged, or planned today"; update `stats` description to include new fields

### systemDiscovery.js split

Replace the single `TIME_PATTERNS` constant with two:

```javascript
// systemDiscovery.js — replace line 45
const DURATION_PATTERNS = ["15min", "30min", "1hr", "2hr"];
const SCHEDULING_CONTEXT_PATTERNS = ["morning", "afternoon", "evening", "weekend", "weekday"];
```

Produce **three** arrays in the output for safe migration:
- `tags.categories.duration[]` — new, duration tags only
- `tags.categories.schedulingContext[]` — new, time-of-day/week tags only
- `tags.categories.time[]` — **retained as-is** for backward compat with omnifocus-agent 9.2.0

The omnifocus-agent will be updated to read from the new arrays and drop the manual split.
`time[]` can be removed in a future version once all consumers have migrated.

### getStats() enrichment

Three new counts require one additional pass over projects:

```typescript
// In getStats():
let reviewOverdue = 0;
let plannedToday = 0;
let withEstimate = 0;
const todayEnd = new Date(todayStart.getTime() + 86400000);

flattenedTasks.forEach(function(t: Task) {
  // ... existing active check ...
  if (t.estimatedMinutes != null && t.estimatedMinutes > 0) withEstimate++;
  try {
    if (t.plannedDate && t.plannedDate >= todayStart && t.plannedDate < todayEnd) plannedToday++;
  } catch (_) {}
});

flattenedProjects.forEach(function(p: Project) {
  if (p.status !== Project.Status.Active) return;
  if (p.nextReviewDate && p.nextReviewDate < todayStart) reviewOverdue++;
});
```

## Implementation Units

| # | File | Change | Depends on |
|---|------|--------|------------|
| 1 | `ofo-core.ts` | `getTask()` task branch: add `plannedDate` (guard) + `repetitionRule` | — |
| 2 | `ofo-core.ts` | `getTask()` project branch: add `estimatedMinutes` + `reviewInterval` + `nextReviewDate` + `lastReviewDate` + `plannedDate` (guard) | — |
| 3 | `ofo-core.ts` | `taskSummary()` (nested in `listTasks()`): add `estimatedMinutes`; today filter: add `plannedDate` guard | — |
| 4a | `ofo-core-ambient.d.ts` | Add `plannedDate: Date \| null` to Task and Project interfaces | — |
| 4b | `ofo-core.ts` | `createTask()` + `updateTask()`: handle `plannedDate` arg with try/catch write guard; update return shapes to include `plannedDate` | 4a |
| 5 | `ofo-cli.ts` | `cmdCreate` + `cmdUpdate`: add `--planned-date` flag (ISO date or `"clear"`), including stdin merge paths; update `cmdHelp()` text | 4b |
| 6 | `ofo-core.ts` | `getStats()`: add `reviewOverdue`, `plannedToday`, `withEstimate` | 1, 3 |
| 7 | Build | `npm run build:cli` + `bash scripts/test-queries.sh` | 1–6 |
| 8 | `systemDiscovery.js` | Split `TIME_PATTERNS` → `DURATION_PATTERNS` + `SCHEDULING_CONTEXT_PATTERNS`; add `duration[]` + `schedulingContext[]` to output; retain `time[]`; bump plugin version | — |
| 9 | Docs | SKILL.md ofo command table; omnifocus-agent routing + System Map section; gtd-coach System Context | 7, 8 |
| 10 | Housekeeping | Skillsmith eval ≥97/100; bump v9.3.0; README version history | 9 |

Units 1–6 are all in `ofo-core.ts` / `ofo-cli.ts` — commit together after build passes (Unit 7).
Unit 8 is an independent Attache plugin change — commit separately.
Unit 9 is markdown only — commit after units 7 and 8.

## Acceptance Criteria

### ofo-core.ts / ofo-cli.ts

- [ ] `ofo info <id>` returns `plannedDate` for tasks (null if unset or DB not migrated)
- [ ] `ofo info <id>` returns `repetitionRule.ruleString` and `repetitionRule.scheduleType` for tasks (null if not repeating)
- [ ] `ofo info <id> --type project` returns `estimatedMinutes`, `reviewInterval`, `nextReviewDate`, `lastReviewDate`, `plannedDate` for projects
- [ ] `ofo list today` includes tasks where `plannedDate = today` (in addition to due today + flagged)
- [ ] `ofo list <filter>` output includes `estimatedMinutes` for each task
- [ ] `ofo create --planned-date 2026-03-25 --name "Task"` sets `plannedDate`
- [ ] `ofo update <id> --planned-date clear` clears `plannedDate`
- [ ] `ofo stats` returns `reviewOverdue`, `plannedToday`, `withEstimate` in addition to existing counts
- [ ] `plannedDate` read and write access never throws — always wrapped in try/catch
- [ ] `createTask()` return shape includes `plannedDate`
- [ ] `updateTask()` return shape includes `plannedDate`
- [ ] `ofo-core-ambient.d.ts` declares `plannedDate` on both Task and Project interfaces
- [ ] `cmdHelp()` text updated for `--planned-date`, `today` filter, and `stats` descriptions
- [ ] `cmdCreate` stdin merge paths (batch + single-object) handle `--planned-date`

### systemDiscovery.js

- [ ] System Map JSON contains `tags.categories.duration[]` with duration-only tags (`15min`, `30min`, `1hr`, etc.)
- [ ] System Map JSON contains `tags.categories.schedulingContext[]` with time-of-day/week tags (`morning`, `afternoon`, etc.)
- [ ] `tags.categories.time[]` still present for backward compat (same content as before)

### omnifocus-agent + gtd-coach

- [ ] omnifocus-agent System Map Context section updated to read from `duration[]` and `schedulingContext[]` (no more manual split)
- [ ] gtd-coach System Context section references `estimatedMinutes` as primary duration signal (coaching: check `ofo info` estimate field)
- [ ] Agent routing table updated with `ofo stats` new fields in health check rows

### Quality

- [ ] `npm run build:cli` passes with zero TypeScript errors
- [ ] `bash scripts/test-queries.sh` passes from skill root
- [ ] Skillsmith eval ≥ 97/100 on omnifocus-manager skill
- [ ] No changes to omnifocus_api.md or jxa_guide.md (these already document the fields)

## Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| `plannedDate` throws on OF3 databases | try/catch guard on every access site |
| `reviewInterval` is null on projects with no review set | Null check before accessing `.steps` / `.unit` |
| `estimatedMinutes` is 0 (falsy) when unset | Use `t.estimatedMinutes != null && t.estimatedMinutes > 0` (loose equality catches both null and undefined) |
| systemDiscovery.js change breaks 9.2.0 agent | `time[]` retained for backward compat; agent updated in same version bump |
| `taskSummary()` is nested — wrong edit target | Edit explicitly targets lines 198-208, nested inside `listTasks()` |
| Build output must match the installed plugin | Run `npm run build:cli` + `npm run deploy` to reinstall after changes |
| `plannedDate` write also throws on unmigrated DB | try/catch guard on write paths in `createTask()` and `updateTask()` |
| `plannedDate` absent from `omnifocus.d.ts` | Add to `ofo-core-ambient.d.ts`; without this, tsc compilation fails |
| `"quick"` / `"deep"` in ENERGY_PATTERNS overlap | Removed from DURATION_PATTERNS; these are energy/focus signals, not duration |
| `ofo list today` behavioral change | Tasks planned for today now appear — document in release notes |

## Deferred: Issue #125 Work Item 7 (Tag Validation)

Work Item 7 ("Cross-reference System Map tags against `ofo tags` live output; surface stale tags
during coaching") is **deferred to a future plan**. Rationale: tag validation is an independent
coaching feature that does not depend on any of the native field changes in this plan, and it
introduces a new runtime cross-check pattern that deserves its own design.

## Sources & References

- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/src/ofo-core.ts`
  - `getTask()` task branch: lines 65-84
  - `getTask()` project branch: lines 19-38
  - `taskSummary()` (nested): lines 198-208
  - `listTasks()` today filter: lines 223-233
  - `createTask()`: lines 99-125
  - `updateTask()`: lines 129-161
  - `getStats()`: lines 561-595
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/src/ofo-cli.ts`
  - `cmdCreate` flag parsing: lines 140-221 (`--estimate` pattern to copy for `--planned-date`)
  - `cmdCreate` stdin merge (batch): lines 168-181
  - `cmdCreate` stdin merge (single): lines 184-206
  - `cmdUpdate` flag parsing: lines 223-253 (`--due` / `--defer` clear pattern to copy)
  - `cmdHelp()`: lines 514-593
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/src/ofo-core-ambient.d.ts`
  - Needs `plannedDate` declarations for Task and Project
- `plugins/omnifocus-manager/skills/omnifocus-manager/references/omnifocus_api.md`
  - `plannedDate` (Task): lines 742-743 — migration guard note
  - `plannedDate` (Project): lines 909-910
  - `reviewInterval`: line 913, shape at lines 1809-1824
  - `repetitionRule`: lines 2178-2198
- `plugins/omnifocus-manager/skills/omnifocus-manager/assets/Attache.omnifocusjs/Resources/systemDiscovery.js`
  - `TIME_PATTERNS`: line 45
  - `ENERGY_PATTERNS`: line 42 (contains "quick"/"deep" — do NOT duplicate in DURATION_PATTERNS)
  - Tag categorization: lines 403-465
  - System Map JSON output: lines 715-776
- Related: #123 (Phase 1, merged PR #124), #125 (this issue)
