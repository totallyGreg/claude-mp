---
title: "feat(omnifocus-manager): Phase 1 — GTD Analysis Commands (Habit Cadence, Project Sweep, Expound)"
type: feat
status: active
date: 2026-03-07
---

# feat(omnifocus-manager): Phase 1 — GTD Analysis Commands

## Overview

Three new analysis capabilities for the omnifocus-manager skill, all implemented as JXA scripts
with Claude Code slash commands. No Foundation Models dependency — Phase 1 is fully deterministic
(rule-based) or uses Claude Code (me) as the reasoning layer. This makes everything shippable today.

**Phase 2** (FM-dependent: system analysis with convention learning, in-plugin expound) is tracked
separately and designed in the session brainstorm of 2026-03-07.

## Deliverables

| # | Deliverable | Where | User entry point |
|---|---|---|---|
| 1 | `getRepeatingTasks()` + `getCompletionHistory()` in `taskQuery.js` | library | (internal) |
| 2 | `repeating-tasks` action in `gtd-queries.js` | script | (internal) |
| 3 | `analyze-projects` action in `gtd-queries.js` (batch sweep + near-duplicate) | script | (internal) |
| 4 | `/of:analyze-habits` slash command | command | user-facing |
| 5 | `/of:analyze-projects` slash command | command | user-facing |
| 6 | `/of:expound` slash command | command | user-facing |

---

## Deliverable 1 — `taskQuery.js` Library Functions

File: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/libraries/jxa/taskQuery.js`

### `getRepeatingTasks(doc)`

Returns all active tasks and projects that have a `repetitionRule`. Does not include completed
or dropped items.

```javascript
// Returns array of objects:
{
  id, name, project, tags,
  dueDate, deferDate,
  repeatRule: {
    recurrence,          // iCal RRULE string e.g. "FREQ=DAILY;INTERVAL=1"
    repetitionMethod,    // "startAfterCompletion" | "fixedRepetition"
    catchUpAutomatically
  }
}
```

JXA safety notes:
- Use `task.repetitionRule()` — returns null if no repeat rule, check before accessing fields
- Do NOT use `whose()` to filter — iterate and filter manually to avoid empty-result throws

### `getCompletionHistory(doc, taskName, days)`

Groups completed tasks by normalized name match, returns chronological completion dates for a
given task name within the lookback window.

```javascript
// Returns array of ISO date strings (completionDate), newest first
// Normalized match: case-insensitive, trim whitespace
// days: default 90
```

### `computeHabitCadence(completionDates, repeatRule)`

Pure function (no OmniFocus API). Given completion dates and the intended repeat rule, computes:

```javascript
{
  completionCount,
  actualAvgGapDays,     // average days between completions
  actualStdDevDays,     // consistency score (lower = more consistent)
  intendedGapDays,      // derived from RRULE (FREQ=DAILY → 1, FREQ=WEEKLY → 7, etc.)
  gapRatio,             // actualAvgGapDays / intendedGapDays (>1.5 = under-performing)
  hasDueDate,
  recommendation: {
    removeDedue,        // boolean: true if due date causing overdue accumulation
    suggestedDeferDays, // Math.round(actualAvgGapDays * 0.8) — conservative target
    rationale           // human-readable string
  }
}
```

Recommendation logic (deterministic rules):
- `gapRatio > 1.5` AND `hasDueDate` → recommend removing due date + set defer-after-completion
- `gapRatio > 3.0` → recommend extending repeat interval to match actual cadence
- `actualStdDevDays > actualAvgGapDays` → "highly inconsistent — consider weekly or removing"
- `gapRatio <= 1.2` → "on track — no change needed"

---

## Deliverable 2 — `repeating-tasks` action in `gtd-queries.js`

File: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/gtd-queries.js`

New action added to the switch and header comment. Thin wrapper pattern matching existing actions:

```javascript
case 'repeating-tasks':
    result = getRepeatingTasksWithCadence(doc, taskQuery, args.days || 90);
    break;
```

Output envelope:
```json
{
  "success": true,
  "action": "repeating-tasks",
  "count": 12,
  "lookbackDays": 90,
  "tasks": [
    {
      "id": "...", "name": "Climb Stairs", "project": "Health",
      "repeatRule": { "recurrence": "FREQ=DAILY;INTERVAL=1", ... },
      "cadence": {
        "completionCount": 23,
        "actualAvgGapDays": 3.9,
        "intendedGapDays": 1,
        "gapRatio": 3.9,
        "hasDueDate": true,
        "recommendation": {
          "removeDueDate": true,
          "suggestedDeferDays": 3,
          "rationale": "Completing every 3.9 days on average. Due date is creating overdue accumulation. Suggest defer-after-completion of 3 days, remove due date."
        }
      }
    }
  ]
}
```

New `--days` argument (default 90) controls completion history lookback window.

---

## Deliverable 3 — `analyze-projects` action in `gtd-queries.js`

New batch sweep action. Combines existing signals with new near-duplicate detection.

### Signals collected (all deterministic JXA)

| Signal | Source | Already exists? |
|---|---|---|
| Stalled (no available next action) | `taskQuery.getStalledProjects()` | Yes |
| Neglected (no activity in 30d) | `taskQuery.getNeglectedProjects()` | Yes |
| Overdue accumulation (≥5 overdue tasks) | new inline query | No |
| No due date on any task | new inline query | No |
| Near-duplicate name | new `findNearDuplicateProjects()` | No |

### `findNearDuplicateProjects(projects)`

Pure function. Word-overlap algorithm — no library needed:

1. Normalize each project name: lowercase, strip punctuation, remove stop words (`a`, `the`, `and`, `to`, `for`, `of`, `in`, `my`, `&`)
2. For each pair of active projects, count shared significant words (≥4 chars)
3. If shared word count ≥ 2: flag as `POSSIBLE_DUPLICATE`
4. If shared word count ≥ 3: flag as `LIKELY_DUPLICATE`

Example:
- "Health & Fitness" + "Health Habits" → 1 shared word → not flagged
- "Home Maintenance Tasks" + "Home Maintenance Projects" → 2 shared ("home", "maintenance") → `POSSIBLE_DUPLICATE`
- "Weekly Planning" + "Weekly Review Planning" → 2 shared → `POSSIBLE_DUPLICATE`

Output envelope:
```json
{
  "success": true,
  "action": "analyze-projects",
  "projectCount": 42,
  "signals": {
    "stalled": [{ "id", "name", "folder", "taskCount" }],
    "neglected": [{ "id", "name", "daysSinceActivity" }],
    "overdueAccumulation": [{ "id", "name", "overdueCount" }],
    "nearDuplicates": [
      {
        "confidence": "LIKELY_DUPLICATE",
        "sharedWords": ["home", "maintenance"],
        "projects": [{ "id", "name" }, { "id", "name" }]
      }
    ]
  }
}
```

---

## Deliverable 4 — `/of:analyze-habits` Slash Command

File: `plugins/omnifocus-manager/commands/of-analyze-habits.md`

**Purpose:** Query repeating task completion history, present cadence analysis, and let Claude
recommend defer/due date changes. User confirms before applying.

```yaml
---
description: Analyze repeating task completion cadence and recommend defer/due date adjustments
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/*), Bash(osascript:*)
---
```

**Workflow:**
1. Run `gtd-queries.js --action repeating-tasks --days 90` from skill root
2. Parse JSON output
3. Present a formatted report grouping tasks by recommendation type:
   - Tasks on track (no change needed)
   - Tasks with due date causing overdue accumulation (recommend removing due date)
   - Tasks with major cadence gap (recommend extending repeat interval)
   - Highly inconsistent tasks (recommend reconsideration)
4. For each flagged task, ask user to confirm or dismiss recommendation
5. On confirm: apply change via `manage_omnifocus.js update --id <id> --due clear` or
   `manage_omnifocus.js update --id <id> --defer <N>d` as appropriate

**Report format example Claude should emit:**
```
Habit Cadence Analysis (last 90 days)

REMOVE DUE DATE (causing overdue accumulation):
  • Climb Stairs — completing every 3.9 days, intended daily
    Suggest: defer-after-completion 3 days, clear due date

  • Do 25 Push-ups — completing every 11.2 days, highly inconsistent
    Suggest: change to weekly repeat, no due date

ON TRACK:
  • Morning Pages — completing every 1.1 days, intended daily ✓
```

---

## Deliverable 5 — `/of:analyze-projects` Slash Command

File: `plugins/omnifocus-manager/commands/of-analyze-projects.md`

**Two modes, one command:**

```
/of:analyze-projects              → batch sweep of all projects
/of:analyze-projects --name "X"   → deep single-project analysis
```

**Batch mode workflow:**
1. Run `gtd-queries.js --action analyze-projects`
2. Parse and present structured report grouped by signal type
3. Flag near-duplicates for user action ("These two projects may overlap — worth merging?")
4. Stalled projects: offer to open in OmniFocus via URL scheme

**Single-project mode workflow:**
1. Run `manage_omnifocus.js project-info --name "X"`
2. Claude reviews:
   - Project name: is it outcome-focused? (noun/result vs. vague label)
   - Tasks: are they phrased as clear next actions (verb-noun)?
   - Structure: sequential vs parallel appropriate for the task set?
   - Missing: effort/duration tags on tasks?
   - Overdue: any tasks past due?
3. Claude provides structured feedback and specific rename suggestions
4. User confirms changes; apply via `manage_omnifocus.js update` for tasks,
   `manage_omnifocus.js project-update` for project properties

---

## Deliverable 6 — `/of:expound` Slash Command

File: `plugins/omnifocus-manager/commands/of-expound.md`

**Purpose:** Improve a single task's name for clarity and apply correct effort/duration tags.
Claude suggests, user confirms, changes applied.

```yaml
---
description: Improve a task name for clarity and apply effort/duration tags. Claude suggests, you confirm.
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/*), Bash(osascript:*)
---
```

**Workflow:**
1. If `--name` argument provided, query via `manage_omnifocus.js info --name "..."`.
   If no argument, ask user: "Which task would you like to expound?"
2. Claude reviews the task: name, project context, existing tags, note
3. Claude suggests:
   - Improved name (verb-noun format, specific, outcome-clear)
   - Effort tag (using user's existing effort tag taxonomy from `list-tags`)
   - Duration estimate (if estimatedMinutes is empty)
4. Present suggestions, ask for confirmation or manual override
5. On confirm: apply via `manage_omnifocus.js update --id <id> --new-name "..." --tags "..." --estimate "<N>m"`

**First-run behavior:** On first use, run `gtd-queries.js --action folder-structure` and
`manage_omnifocus.js list-tags --flat` to understand the user's tag taxonomy before making
suggestions. Cache this in the conversation context.

---

## Technical Considerations

### JXA Safety (from `docs/solutions/agent-design/omnifocus-manager-automation-decision-framework.md`)

All new JXA code must:
- **Never** use `task.addTag(tag)` → use `app.add(tag, { to: task.tags })`
- **Never** use `whose()[0]` without checking `.length > 0` first
- **Never** use `task.clearTags()` → iterate and use `app.remove()`
- Filter repeating tasks by iterating and checking `.repetitionRule() !== null` — do not use `whose()` for null checks

### RRULE parsing for `intendedGapDays`

The `recurrence` field is a standard iCal RRULE. Parse the key parts needed:
- `FREQ=DAILY;INTERVAL=1` → 1 day
- `FREQ=WEEKLY;INTERVAL=1` → 7 days
- `FREQ=WEEKLY;INTERVAL=2` → 14 days
- `FREQ=MONTHLY;INTERVAL=1` → 30 days

Simple regex extraction — no full RRULE parser needed for these common cases.
Unknown patterns → `intendedGapDays: null`, omit from cadence ratio.

### Completion history lookback

`doc.flattenedTasks.whose({ completed: true })` is slow on large databases.
Use `taskQuery.getRecentlyCompleted(doc, days, 500)` which already filters by date and applies
a limit cap. Group results by normalized name in JavaScript after retrieval.

### Near-duplicate stop word list

Keep short and specific to GTD vocabulary:
```javascript
const STOP_WORDS = new Set(['a','the','and','to','for','of','in','my','our','with','on','at','by','&']);
```

### Slash command `--name` argument handling

None of the existing commands parse CLI arguments from the slash command invocation.
They rely on Claude to construct the osascript call. Follow this same pattern — Claude
extracts the name from the user's message and passes it as a flag to the script.

---

## System-Wide Impact

- **`gtd-queries.js`** — 2 new actions (`repeating-tasks`, `analyze-projects`). No changes to existing actions.
- **`taskQuery.js`** — 3 new functions (`getRepeatingTasks`, `getCompletionHistory`, `computeHabitCadence`). Additive only.
- **`manage_omnifocus.js`** — No changes needed. Existing `update` and `project-info` actions are sufficient.
- **`SKILL.md`** — Update Quick Reference table to include new actions; add new commands to command list.
- **`omnifocus-agent.md`** — Add routing entries for "analyze habits", "repeating tasks", "expound task", "improve task name", "analyze projects", "duplicate projects".
- **`IMPROVEMENT_PLAN.md`** + **`marketplace.json`** — Version bump to 6.4.0 on completion.

---

## Acceptance Criteria

- [ ] `taskQuery.getRepeatingTasks(doc)` returns all active tasks/projects with a repeat rule
- [ ] `taskQuery.getCompletionHistory(doc, name, days)` returns completion dates grouped by normalized name
- [ ] `taskQuery.computeHabitCadence()` correctly computes gapRatio and recommendation for daily/weekly/monthly tasks
- [ ] `gtd-queries.js --action repeating-tasks` returns valid JSON with cadence data for each repeating task
- [ ] `gtd-queries.js --action analyze-projects` returns stalled, neglected, overdueAccumulation, and nearDuplicates signals
- [ ] Near-duplicate detection flags "Home Maintenance" + "Home Maintenance Projects" as POSSIBLE_DUPLICATE
- [ ] Near-duplicate detection does NOT flag unrelated projects with one common word
- [ ] `/of:analyze-habits` presents a readable cadence report and applies confirmed changes
- [ ] `/of:analyze-projects` batch mode groups and presents all signal types
- [ ] `/of:analyze-projects --name "X"` deep mode provides specific naming and structure feedback
- [ ] `/of:expound` queries tag taxonomy on first use, suggests verb-noun name + effort tag, applies on confirm
- [ ] All new JXA code passes `scripts/validate-jxa-patterns.js` (no anti-patterns)
- [ ] `omnifocus-agent.md` routing updated for all new entry points
- [ ] `SKILL.md` Quick Reference updated
- [ ] Skillsmith evaluation run, score recorded in IMPROVEMENT_PLAN.md

---

## Dependencies & Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| `repetitionRule()` returns null for some repeating tasks | Low | Always null-check before accessing fields |
| Completion history grouping fails for tasks with name variations | Medium | Normalize: lowercase + trim only; don't stem words |
| Near-duplicate false positives on short project names | Medium | Require words ≥4 chars + ≥2 shared; tune stop word list |
| `getRecentlyCompleted` too slow on large databases | Low | Default 90-day window + 500-task cap already in library |
| Tag taxonomy varies per user (effort tags named differently) | Medium | `/of:expound` reads tag list first; doesn't assume tag names |

---

## Files to Create / Modify

| File | Action |
|---|---|
| `scripts/libraries/jxa/taskQuery.js` | Add `getRepeatingTasks`, `getCompletionHistory`, `computeHabitCadence` |
| `scripts/gtd-queries.js` | Add `repeating-tasks`, `analyze-projects` actions |
| `commands/of-analyze-habits.md` | Create |
| `commands/of-analyze-projects.md` | Create |
| `commands/of-expound.md` | Create |
| `skills/omnifocus-manager/SKILL.md` | Update Quick Reference, command list, agent routing section |
| `agents/omnifocus-agent.md` | Add routing entries for new intents |
| `skills/omnifocus-manager/IMPROVEMENT_PLAN.md` | Add v6.4.0 entry |
| `.claude-plugin/marketplace.json` | Bump version to 6.4.0 |

---

## Sources & References

- **Session brainstorm (2026-03-07):** In-conversation design decisions
  - Repeating task: option (b) — data + rule-based math, no model
  - Project analysis: option (c) — batch sweep + deep single
  - Expound: option (b) for Phase 1 — Claude Code slash command
  - Project scope expanded to "analyze system" (tags, folders, naming) — Phase 2 handles FM-based convention learning
  - Preference storage: option (a) — plugin-primary, living confidence scores (Phase 2)
- `docs/solutions/agent-design/omnifocus-manager-automation-decision-framework.md` — 80/15/5 rule, JXA anti-patterns
- `docs/lessons/omnifocus-manager-refinement-2026-01-18.md` — slash command structure, enforcement language
- `scripts/gtd-queries.js` — action pattern to follow
- `scripts/libraries/jxa/taskQuery.js` — library function patterns
- `commands/of-work.md` — slash command frontmatter + invocation pattern
