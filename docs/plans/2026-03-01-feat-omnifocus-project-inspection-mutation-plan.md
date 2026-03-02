---
title: "feat: omnifocus-manager project inspection and mutation commands"
type: feat
date: 2026-03-01
issue: 68
---

# feat: omnifocus-manager project inspection and mutation commands

## Overview

Add four new capabilities to `manage_omnifocus.js` that fill the structural gap between the existing flat task CRUD and full project-level inspection/mutation:

1. `project-info` — read a project's full structure in one call
2. `project-update` — mutate project-level properties (review interval, note, sequential)
3. `create --parent-id` — insert a subtask into an existing project or task group
4. `batch-update` — apply the same mutation to a list of task IDs

This eliminates the pattern of Claude improvising bespoke JXA for every non-trivial project interaction.

## Problem Statement

The current CLI is task-centric and flat. Any request involving project structure, repeat rules, review intervals, or subtask hierarchies forces the agent to write custom JXA on the spot. A single "look at my weekly review project" interaction required 17+ tool calls because no command returned the project structure in one shot. Mutations would have required even more.

## Proposed Solution

Extend the existing CLI architecture:
- Add `getProjectInfo()` to `scripts/libraries/jxa/taskQuery.js`
- Add `findProject()`, `setReviewInterval()`, `removeNoteLineMatching()` to `scripts/libraries/jxa/taskMutation.js`
- Add four new action handlers to `manage_omnifocus.js`
- Register `--sequential` / `--parallel` as boolean flags in `argParser.js`
- Update `omnifocus-agent.md` routing table with the new commands

## Architecture

### File Map

```
scripts/
├── manage_omnifocus.js                   ← add 4 new case branches
└── libraries/jxa/
    ├── taskQuery.js                      ← add getProjectInfo()
    ├── taskMutation.js                   ← add findProject(), setReviewInterval(), removeNoteLineMatching()
    └── argParser.js                      ← add --sequential, --parallel as boolean flags

agents/omnifocus-agent.md                 ← update routing table
references/api_reference.md              ← document new Project API patterns
```

### Key JXA Constraints (from research)

**Property access in JXA:** All reads use `()`, writes use `=` assignment:
```javascript
project.sequential()        // read
project.sequential = true   // write
```

**No `flattenedProjects.byId()` in JXA.** Must look up by name with `.whose()` or iterate:
```javascript
// By name (preferred)
doc.flattenedProjects.whose({ name: projectName })[0]

// By ID — iterate (needed for project-update --id)
const allProjects = doc.flattenedProjects();
const project = allProjects.find(p => p.id() === targetId);

// Alternative: resolve via task lookup (shares ID in OmniFocus JXA)
const task = doc.flattenedTasks.byId(id);
const project = task ? task.containingProject() : null;
```

**`reviewInterval()` is a value object** — never null. Must read the full object and reassign to mutate:
```javascript
const ri = project.reviewInterval();   // returns value object
ri.steps = 1;
ri.unit = 'months';
project.reviewInterval = ri;           // write back
```

**`repetitionRule()` can be null** — always null-check before accessing sub-properties.

---

## Implementation Plan

### Phase 1 — Library additions (taskQuery.js + taskMutation.js)

#### `taskQuery.getProjectInfo(doc, nameOrId)`

```javascript
// Returns:
{
  id, name, note, status, sequential,
  deferDate, dueDate, estimatedMinutes, tags,
  repeatRule: {
    ruleString,         // RRULE string or null
    scheduleType,       // "Regularly" | "FromCompletion" | "None" | null
    catchUpAutomatically, anchorDateKey
  },
  reviewInterval: { steps, unit },   // e.g. { steps: 1, unit: "months" }
  lastReviewDate, nextReviewDate,
  subtasks: [ ...formatTaskInfo() for each task in project.tasks() ]
}
```

Lookup strategy:
1. Try name: `doc.flattenedProjects.whose({ name: nameOrId })[0]`
2. If not found and looks like an ID, iterate `doc.flattenedProjects()` comparing `.id()`
3. Return `{ success: false, error: "Project not found: ..." }` if neither matches

#### `taskMutation.findProject(doc, nameOrId)` (shared helper)

Used by `project-update` and `create --parent-id`:
- Name lookup first, ID iteration fallback
- Returns project or throws

#### `taskMutation.setReviewInterval(project, intervalStr)`

Parse `intervalStr` like `"1month"`, `"2weeks"`, `"3months"` into `{ steps, unit }`:
- Regex: `/^(\d+)(day|week|month|year)s?$/`
- Read current value object, update `steps` and `unit`, reassign

#### `taskMutation.removeNoteLineMatching(entity, text)`

Works on any entity with a `.note` property:
```javascript
const lines = entity.note().split('\n');
const filtered = lines.filter(line => !line.includes(text));
entity.note = filtered.join('\n');
```

---

### Phase 2 — New actions in manage_omnifocus.js

#### `project-info`

```
osascript -l JavaScript manage_omnifocus.js project-info --name "Weekly Review"
osascript -l JavaScript manage_omnifocus.js project-info --id lz6kHB1apf5
```

Handler calls `taskQuery.getProjectInfo(doc, args.name || args.id)`.

#### `project-update`

```
osascript -l JavaScript manage_omnifocus.js project-update --id lz6kHB1apf5 --review-interval 1month
osascript -l JavaScript manage_omnifocus.js project-update --id lz6kHB1apf5 --note-remove-line "Issue Status"
osascript -l JavaScript manage_omnifocus.js project-update --id lz6kHB1apf5 --sequential
osascript -l JavaScript manage_omnifocus.js project-update --id lz6kHB1apf5 --parallel
```

Returns:
```json
{ "success": true, "message": "Updated project: Weekly Review", "project": { "id": "...", "name": "..." } }
```

#### `create --parent-id`

```
osascript -l JavaScript manage_omnifocus.js create --parent-id lz6kHB1apf5 --name "Review Someday/Maybe list" --estimate 10m --tags Routine
```

Lookup: try `doc.flattenedTasks.byId(parentId)` (works for task groups); if not a task, try project lookup via `findProject`. Push new task into the result's `tasks` collection.

#### `batch-update`

```
osascript -l JavaScript manage_omnifocus.js batch-update --ids id1,id2,id3 --defer clear
osascript -l JavaScript manage_omnifocus.js batch-update --ids id1,id2,id3 --due clear --defer clear
```

Returns:
```json
{ "success": true, "message": "Updated 3 tasks", "updated": [...] }
```

Initial supported mutations: `--defer clear`, `--due clear`.
If any ID is not found, report it in a `"skipped"` array but continue.

---

### Phase 3 — argParser.js and agent routing

#### `argParser.js` — register boolean flags

Add `sequential` and `parallel` to the boolean flag list (alongside `flagged`, `completed`, `help`).

#### `omnifocus-agent.md` — routing table additions

| User Intent Pattern | Route To | Command |
|---|---|---|
| "Look at my X project" | omnifocus-manager | `manage_omnifocus.js project-info --name X` |
| "Show me the structure of X" | omnifocus-manager | `manage_omnifocus.js project-info --name X` |
| "Change review interval for X" | omnifocus-manager | `manage_omnifocus.js project-update --id <id> --review-interval 1month` |
| "Make X sequential/parallel" | omnifocus-manager | `manage_omnifocus.js project-update --id <id> --sequential` |
| "Remove line Y from X's note" | omnifocus-manager | `manage_omnifocus.js project-update --id <id> --note-remove-line "Y"` |
| "Clear stale defer dates" | omnifocus-manager | `manage_omnifocus.js batch-update --ids ... --defer clear` |
| "Add subtask to X" | omnifocus-manager | `manage_omnifocus.js create --parent-id <id> --name ...` |

#### `references/api_reference.md` — document Project API additions

Add a "Project-level API" section covering:
- `project.repetitionRule()` — read, null-safe pattern
- `project.reviewInterval()` — value object read/write pattern
- `project.sequential()` / `project.sequential = bool` — read/write
- `doc.flattenedProjects.whose({ name })` vs ID iteration pattern

---

## Technical Considerations

- **`project.repetitionRule()` is untested in existing codebase** — the first implementation should include a smoke test against a known repeating project before relying on it
- **`project.reviewInterval()` is always a value object**, never null — safe to access `.steps` and `.unit` without a null check
- **Subtask depth**: `project-info` returns `project.tasks()` (top-level children only), not `project.flattenedTasks()`. This preserves group structure without flattening everything. Nested groups are returned as tasks with their own children field if they have subtasks.
- **`batch-update` atomicity**: JXA has no transaction support. If it fails mid-batch, already-applied changes are not rolled back. Output must clearly indicate which IDs succeeded and which failed.
- **`--parent-id` resolution order**: Try `doc.flattenedTasks.byId()` first (handles task groups inside a project); fall back to project lookup. This handles both "add to a group within the project" and "add to the project root."
- **`--sequential` / `--parallel` mutex**: If both are passed, return `{ success: false, error: "--sequential and --parallel are mutually exclusive" }`.

## Open Questions — Resolve Before Implementation

These must be answered (via prototyping or decision) before writing any library code:

| # | Question | Blocker for |
|---|---|---|
| 1 | Does `project.reviewInterval = {...}` work as a write in JXA, or does it require a typed constructor? | project-update |
| 2 | What fields does `project.repetitionRule()` expose in JXA (ruleString, scheduleType, etc.)? | project-info |
| 3 | Does `--note-remove-line "text with spaces"` arrive as one argv token in JXA, or is it split? | project-update |
| 4 | batch-update failure model: best-effort (continue, report per-ID) or fail-fast? | batch-update |
| 5 | `project-info --id`: iterate `flattenedProjects()` comparing `.id()`, or use task byId then `.containingProject()`? | project-info, project-update |
| 6 | `subtasks` in project-info: top-level only (`project.tasks()`) or flattened (`project.flattenedTasks()`)? | project-info |

**Recommended:** Write a 15-line prototype JXA script that reads a known project, inspects `repetitionRule()` and `reviewInterval()`, then writes back a mutated `reviewInterval`. Run it on the Weekly Review project before committing to the implementation design.

## Dependencies & Risks

| Risk | Mitigation |
|---|---|
| `project.repetitionRule()` behaves differently than documented | Smoke-test against Weekly Review project (known repeating project) before finalizing |
| ID iteration over large project lists is slow | Use `.whose({ name })` when name is provided; ID iteration only as fallback |
| `reviewInterval()` value object write-back not supported in some OmniFocus versions | Test on OmniFocus 4; document minimum version requirement |
| `batch-update` partial failure leaves data inconsistent | Always return `updated` + `skipped` arrays so agent can report accurately |

## References

- Issue: [#68](https://github.com/totallyGreg/claude-mp/issues/68)
- Existing CLI: `scripts/manage_omnifocus.js`
- Query library: `scripts/libraries/jxa/taskQuery.js`
- Mutation library: `scripts/libraries/jxa/taskMutation.js`
- Arg parser: `scripts/libraries/jxa/argParser.js`
- Agent routing: `agents/omnifocus-agent.md`
- API reference: `references/OmniFocus-API.md` (canonical)
- JXA guide: `references/jxa_guide.md`
