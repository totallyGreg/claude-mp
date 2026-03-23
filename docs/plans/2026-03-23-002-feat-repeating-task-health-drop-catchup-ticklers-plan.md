---
title: "feat(omnifocus-manager): Repeating task health — drop command, Catch Up coaching, tickler patterns"
type: feat
status: completed
date: 2026-03-23
issue: https://github.com/totallyGreg/claude-mp/issues/138
---

# Repeating Task Health — Drop Command, Catch Up Coaching, Tickler Patterns

## Overview

The health check and coaching skills lack awareness of OmniFocus repeating task mechanics. This leads to incorrect recommendations — e.g., advising "batch-complete" for overdue routines when dropping the single occurrence is the correct action (avoids inflating completion metrics). This plan adds the `ofo drop` command, enriches the task data model with repetition metadata, teaches the health check to diagnose stale repeating tasks, and adds repeating task coaching to the GTD coach.

## Problem Statement

1. **No `ofo drop` command** — the CLI can complete tasks but can't drop a single occurrence. Dropping is correct for stale repeating tasks (doesn't inflate metrics).

2. **`catchUpAutomatically` not surfaced** — `normalizeTask` returns `repetitionRule` as a string (ruleString only). Health checks can't distinguish Catch Up ON (auto-skips past occurrences) from Catch Up OFF (requires one-by-one catch-up).

3. **Health check doesn't diagnose repeating tasks** — `ofo-health.md` and `ofo-overdue.md` treat all overdue tasks the same. A 38-day-overdue daily push-up routine needs different handling than a 38-day-overdue one-shot deadline.

4. **GTD coach has no repeating task strategy** — no coverage of Catch Up toggle, schedule types (Regularly vs FromCompletion), tickler patterns for long-running projects, or overdue signal interpretation.

## Proposed Solution

Four-phase approach following established ofo CLI patterns:

1. **Data Layer** — Add `ofo drop` command + enrich OfoTask with repetition metadata
2. **Health Check** — Teach diagnostics to categorize overdue repeating tasks and recommend drop vs complete
3. **Coaching** — Add repeating task strategy to gtd-coach, Catch Up reference to api_reference.md
4. **Validate** — Build, test, evaluate, version bump

## Technical Approach

### Key Decisions

**D1: OfoTask schema — additive fields (backward compatible)**

Add three new optional fields rather than changing `repetitionRule` from string to object:

```typescript
// OfoTask additions (ofo-contract.d.ts)
repetitionRule: string | null;           // EXISTING — keep as ruleString
repetitionCatchUp: boolean | null;       // NEW — catchUpAutomatically
repetitionScheduleType: string | null;   // NEW — "Regularly" | "FromCompletion" | null
```

Rationale: Existing consumers parse `repetitionRule` as a string. Breaking that in v10.x would require coordinated updates across CLI parsers, Attache actions, and any external scripts. Additive fields are safe.

**D2: Drop vs Complete decision tree**

```
IF task is NOT repeating:
  → Standard overdue handling (not affected by this feature)

IF task IS repeating:
  IF catchUpAutomatically == true:
    → Recommend DROP — next occurrence auto-schedules to future
    → "This task auto-catches up. Drop this stale occurrence to reset."

  ELSE IF scheduleType == "FromCompletion":
    → Ask: "Was this actually done?"
    → If yes: COMPLETE (next occurrence schedules from completion date)
    → If no: DROP (skip this occurrence)

  ELSE IF scheduleType == "Regularly":
    → IF daysOverdue < 7: Ask if actually done (might just be late)
    → IF daysOverdue >= 7: Recommend DROP
    → "Long overdue regular task. Drop to move forward?"
```

**D3: Tickler coaching is generic, not user-specific**

The GTD coach describes tickler patterns without assuming specific implementations (e.g., "Progress:" prefix). Three pattern types documented: prefix-based, tag-based, perspective-based.

**D4: Health check uses `ofo list overdue` (not perspectives)**

No built-in "Overdue" perspective exists. Keep using the overdue list filter and post-process in the command template. Consistent with current `ofo-health.md`.

**D5: `--all` flag on non-repeating task errors**

`ofo drop <id> --all` on a non-repeating task returns an error: "Task is not repeating; use without --all to drop it."

### Architecture

```
Phase 1 (Data):
  ofo-contract.d.ts ──→ ofo-types.ts ──→ ofo-core-ambient.d.ts
       │ (add OfoAction 'ofo-drop', new OfoTask fields)
       │
  ofo-core.ts ──→ normalizeTask() enrichment + dropTask() function + dispatch case
       │
  ofo-cli.ts ──→ cmdDrop() + switch case + help text
       │
  build-attache.sh ──→ IIFE footer + validation

Phase 2 (Health):
  ofo-health.md ──→ detect repeating overdue, recommend drop vs complete
  ofo-overdue.md ──→ group by repeating vs one-shot

Phase 3 (Coaching):
  gtd-coach/SKILL.md ──→ "Repeating Tasks & Ticklers" section
  references/api_reference.md ──→ Catch Up / RepetitionRule reference
  omnifocus-manager/SKILL.md ──→ ofo drop in Quick Decision Tree
```

### Implementation Phases

#### Phase 1: Data Layer — ofo drop + enriched task shape

**Files (7):**

| File | Change |
|------|--------|
| `scripts/src/ofo-contract.d.ts` | Add `'ofo-drop'` to OfoAction union; add `repetitionCatchUp`, `repetitionScheduleType` to OfoTask |
| `scripts/src/ofo-types.ts` | Mirror contract changes (ESM re-export) |
| `scripts/src/ofo-core-ambient.d.ts` | Auto-generated — run `node scripts/generate-ambient.js` after contract update |
| `scripts/src/ofo-core.ts` | Enrich `normalizeTask()` + add `dropTask()` + add dispatch case |
| `scripts/src/ofo-cli.ts` | Add `cmdDrop()` + switch case + help text |
| `scripts/build-attache.sh` | Add `dropTask` to IIFE footer exports + validation loop |
| `scripts/diff-task-shapes.js` | Add new fields to expected shape |

**normalizeTask enrichment** (`ofo-core.ts`):

```typescript
function normalizeTask(t: Task): OfoTask {
  // ... existing fields ...
  let catchUp: boolean | null = null;
  let schedType: string | null = null;
  if (t.repetitionRule) {
    try { catchUp = t.repetitionRule.catchUpAutomatically; } catch (_) {}
    try { schedType = String(t.repetitionRule.scheduleType); } catch (_) {}
  }
  return {
    // ... existing fields ...
    repetitionRule: t.repetitionRule ? t.repetitionRule.ruleString : null,
    repetitionCatchUp: catchUp,
    repetitionScheduleType: schedType,
    taskStatus: String(t.taskStatus),
  };
}
```

**dropTask function** (`ofo-core.ts`):

```typescript
function dropTask(args: OfoArgs): OfoResult {
  const id = args.id as string;
  const allOccurrences = args.allOccurrences as boolean || false;
  const t = Task.byIdentifier(id);
  if (!t) return { success: false, error: 'Task not found: ' + id };
  if (allOccurrences && !t.repetitionRule) {
    return { success: false, error: 'Task is not repeating; use without --all to drop it.' };
  }
  t.drop(allOccurrences);
  return { success: true, task: { id: t.id.primaryKey, name: t.name, dropped: true } };
}
```

**cmdDrop** (`ofo-cli.ts`):

```typescript
function cmdDrop(args: string[]): void {
  if (args.length < 1) die('Usage: ofo drop <id|omnifocus-url> [--all]');
  const id = parseOmniFocusUrl(args[0]!);
  let allOccurrences = false;
  for (let i = 1; i < args.length; i++) {
    if (args[i] === '--all') allOccurrences = true;
  }
  runAction('ofo-drop', { id, allOccurrences });
}
```

**Acceptance Criteria:**
- [ ] `ofo drop <id>` drops single occurrence of repeating task
- [ ] `ofo drop <id> --all` drops all future occurrences
- [ ] `ofo drop <id> --all` on non-repeating task returns error
- [ ] `ofo list overdue` output now includes `repetitionCatchUp` and `repetitionScheduleType` fields
- [ ] `ofo info <id>` output includes new fields
- [ ] Existing `repetitionRule` string field unchanged (backward compatible)
- [ ] `npm run build` succeeds; `build-attache.sh` validates new export
- [ ] `bash scripts/test-queries.sh` passes
- [ ] `diff-task-shapes.js` passes with new fields

#### Phase 2: Health Check — Repeating task diagnostics

**Files (2):**

| File | Change |
|------|--------|
| `commands/ofo-health.md` | Add repeating task categorization to presentation instructions |
| `commands/ofo-overdue.md` | Add repeating task grouping with drop/complete recommendations |

**ofo-health.md enhancement:**

Add after existing warning rules:

```markdown
When presenting overdue tasks, check `repetitionRule` field:
- If `repetitionRule` is not null → task is repeating
- Group repeating overdue tasks separately as "Stale Routines"
- For each stale routine, check `repetitionCatchUp` and `repetitionScheduleType`:
  - Catch Up ON → "Drop to reset: `ofo drop <id>`"
  - FromCompletion → "Was this done? Complete if yes, drop if no"
  - Regularly + >7 days overdue → "Long overdue — drop to move forward"
  - Regularly + <=7 days overdue → "Recently missed — complete if done, drop if skipped"
```

**ofo-overdue.md enhancement:**

Replace current "Routine Decay" group with enriched version:

```markdown
Group by:
- **Stale Routines** — overdue tasks where repetitionRule is not null
  - Sub-group by repetitionCatchUp:
    - Catch Up ON: "Auto-resets on drop. Run: `ofo drop <id>`"
    - Catch Up OFF + FromCompletion: "Complete if done, drop if skipped"
    - Catch Up OFF + Regularly: recommend based on days overdue
  - Show: Task | Project | Days Overdue | Recurrence | Catch Up | Recommended Action
```

**Acceptance Criteria:**
- [ ] `/ofo:health` separately reports stale routines with Catch Up-aware recommendations
- [ ] `/ofo:overdue` groups repeating tasks with inline `ofo drop` commands
- [ ] Non-repeating overdue tasks unaffected (same behavior as before)

#### Phase 3: Coaching — GTD coach + API reference

**Files (3):**

| File | Change |
|------|--------|
| `skills/gtd-coach/SKILL.md` | Add "Repeating Tasks & Ticklers" section |
| `skills/omnifocus-manager/references/api_reference.md` | Add RepetitionRule / Catch Up quick reference |
| `skills/omnifocus-manager/SKILL.md` | Add `ofo drop` to Quick Decision Tree |

**gtd-coach SKILL.md — new section** (after "Horizons of Focus", before "System Health Indicators"):

```markdown
### Repeating Tasks & Ticklers

Repeating tasks in GTD serve two distinct purposes. Understanding which purpose a task serves determines how to configure it and what to do when it goes overdue.

#### Purpose 1: Routines (Do the thing)

Tasks where the recurrence IS the work: exercise, reviews, maintenance.

**Schedule types:**
- **Regularly** (fixed schedule) — next occurrence anchored to calendar. Use for: weekly reviews, monthly financial checks, daily standups.
- **From Completion** — next occurrence relative to when you finish. Use for: habits where the interval matters more than the day (e.g., "every 3 days" not "every Monday").

**Catch Up Automatically:**
- **ON** — when you resolve a stale routine, OmniFocus skips all missed dates and schedules the next future occurrence. Best for most routines — you don't need to "make up" 38 missed push-up sessions.
- **OFF** — resolving creates the next occurrence at the very next scheduled date (may still be in the past). Requires one-by-one resolution to reach the present. Use only when catching up matters (e.g., medication logs).

#### Purpose 2: Ticklers (Remember to check)

Recurring reminders to review progress on long-running work. The task itself is lightweight — the real work lives elsewhere (a project, a document, a codebase).

**Common tickler patterns:**
- **Prefix convention** — name tasks with a consistent prefix (e.g., "Review:", "Check:", "Progress:") so they're identifiable as ticklers, not deliverables.
- **Tag-based** — apply a dedicated tag (e.g., "Tickler") to recurring check-in tasks. Filter by tag in perspectives.
- **Perspective-based** — create a perspective that surfaces repeating tasks in specific folders or with specific tags. The perspective IS the tickler mechanism.

**Cadence guidelines:**
- Active projects → weekly tickler
- Background/hobby projects → biweekly or monthly
- Dormant projects → drop the tickler, move project to Someday/Maybe

#### Overdue Signal Interpretation

A repeating task going overdue is a signal — but what it means depends on duration and purpose:

| Overdue Duration | Routine Task | Tickler Task |
|-----------------|--------------|--------------|
| 1-3 days | Normal slip — do it or drop this occurrence | Check in soon |
| 1-2 weeks | Habit struggling — review cadence | Project may be stalled |
| 1+ month | Cadence is wrong or task is irrelevant | Project is likely dormant — drop tickler, review project status |

**Key principle:** Dropping a stale occurrence is not failure — it's system maintenance. Complete means "I did this." Drop means "I'm skipping this one and moving forward." Use drop for honest bookkeeping.
```

**api_reference.md — new section** (after existing Repeat Rule section):

```markdown
**Repetition Rule (detailed):**

// RepetitionRule properties (read-only)
var rule = task.repetitionRule();
if (rule) {
    var ruleString = rule.ruleString;                    // ICS recurrence: "FREQ=WEEKLY"
    var scheduleType = rule.scheduleType;                // Regularly | FromCompletion | None
    var catchUp = rule.catchUpAutomatically;             // true = skip past dates on resolve
    var anchor = rule.anchorDateKey;                     // DeferDate | DueDate
    var nextDate = rule.firstDateAfterDate(new Date());  // Next occurrence after given date
}

// Task.RepetitionScheduleType enum
Task.RepetitionScheduleType.Regularly       // Fixed schedule (e.g., every Monday)
Task.RepetitionScheduleType.FromCompletion  // Relative to completion date
Task.RepetitionScheduleType.None            // No repeat

// Catch Up Automatically behavior:
// ON (true):  resolve once → skips all missed dates → next occurrence is in the future
// OFF (false): resolve once → next date is the very next scheduled date (may still be past)

// Dropping a single occurrence (keeps recurrence):
task.drop(false);   // Drop this occurrence only; recurrence generates next
task.drop(true);    // Drop ALL future occurrences (stops repeating)
```

**omnifocus-manager SKILL.md — ofo drop in Quick Decision Tree:**

Add to `### 0. ofo CLI` command list:

```bash
scripts/ofo drop <id-or-omnifocus-url>             # Drop single occurrence (recurrence continues)
scripts/ofo drop <id-or-omnifocus-url> --all       # Drop all occurrences (stops repeating)
```

**Acceptance Criteria:**
- [ ] gtd-coach covers: schedule types, Catch Up toggle, generic tickler patterns, overdue signals
- [ ] Tickler patterns described generically (prefix, tag, perspective) — no user-specific examples
- [ ] api_reference.md documents RepetitionRule properties, scheduleType enum, Catch Up behavior, drop semantics
- [ ] SKILL.md Quick Decision Tree includes `ofo drop`

#### Phase 4: Validate

- [ ] `bash scripts/test-queries.sh` — no regressions in existing queries
- [ ] `bash build-attache.sh` — builds successfully with new `dropTask` export
- [ ] `npm run deploy` — install updated Attache plugin in OmniFocus
- [ ] Manual test: `ofo drop <overdue-repeating-task-id>` — confirm recurrence generates next occurrence
- [ ] Manual test: `ofo drop <non-repeating-id> --all` — confirm error message
- [ ] Manual test: `ofo info <repeating-task-id>` — confirm `repetitionCatchUp` and `repetitionScheduleType` in output
- [ ] `uv run evaluate_skill.py <gtd-coach-path>` — record score
- [ ] `uv run evaluate_skill.py <omnifocus-manager-path>` — record score
- [ ] Version bump: omnifocus-manager 10.1.0 (minor — additive CLI command + fields)
- [ ] Version bump: gtd-coach 1.4.0 (minor — new coaching section)
- [ ] Sync marketplace.json

## System-Wide Impact

- **OfoTask interface change** — additive only (2 new nullable fields). Existing consumers unaffected.
- **Attache plugin** — must be rebuilt and redeployed to include `dropTask` in IIFE exports.
- **ofo-core-ambient.d.ts** — auto-generated from contract; run `node scripts/generate-ambient.js` after contract update.
- **No API surface parity issues** — drop is a new capability, not a modification of existing ones.

## Dependencies & Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `catchUpAutomatically` not available on OF3 | Low | Wrap in try-catch; return null if unavailable |
| `task.drop(false)` doesn't regenerate next occurrence | Low | Documented OmniFocus behavior; test manually |
| Breaking existing `repetitionRule` consumers | None | Additive fields only; existing string field unchanged |
| Health check recommendations are wrong | Medium | Conservative decision tree; always suggest, never auto-act |

## Sources & References

### Internal References
- `scripts/src/ofo-core.ts:20-41` — normalizeTask function (enrichment target)
- `scripts/src/ofo-core.ts:162-168` — completeTask pattern (model for dropTask)
- `scripts/src/ofo-contract.d.ts:42-59` — OfoTask interface (schema change)
- `scripts/build-attache.sh` — IIFE footer exports (add dropTask)
- `references/omnifocus_api.md:2178-2209` — Task.RepetitionRule API
- `commands/ofo-health.md` — health check template (enhancement target)
- `commands/ofo-overdue.md` — overdue display template (enhancement target)

### Institutional Learnings
- `docs/solutions/agent-design/omnifocus-manager-automation-decision-framework.md` — TypeScript validation pipeline, reference file placement
- `docs/plans/2026-03-20-002-feat-ofo-cli-fix-and-extend-plan.md` — 5-step CLI command addition pattern
- `docs/plans/2026-03-22-004-feat-ofo-native-fields-gtd-coaching-plan.md` — normalizeTask enrichment pattern, OF4-only property try-catch

### Related Work
- Issue: [#138](https://github.com/totallyGreg/claude-mp/issues/138)
- Prior art: `clarity` and `stalled` commands added in v9.x following same pattern
