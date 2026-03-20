---
title: "feat: Redesign end-of-day routine with automated daily log"
type: feat
status: completed
date: 2026-03-20
origin: 820 Brainstorms/2026-03-19-end-of-day-routine-redesign-requirements.md
---

# feat: Redesign End-of-Day Routine with Automated Daily Log

## Overview

Rebuild the broken OmniFocus "End of day Routine" into a lean, repeating shutdown procedure that produces a categorized daily completion log in Obsidian. The routine serves as both a mental cutoff ritual and an artifact generator — each step either verifies a "done" criterion or triggers automation.

(see origin: `820 Brainstorms/2026-03-19-end-of-day-routine-redesign-requirements.md`)

## Problem Statement / Motivation

The current routine has 2 stuck tasks, no recurrence, a missing perspective, and no automation. The note's "done" criteria (inbox zero, no unaddressed due items, completed list to Obsidian, track questions/discontents) don't map to the actual tasks. The user captures questions (`Question❓`), discontents (`Discontent⁉️`), and decisions (`Decide😤`) in OmniFocus but has no system to log completions across these categories into Obsidian.

## Proposed Solution

### Phase 1: OmniFocus Project + Perspectives

**1a. Restructure the routine project**

Replace the current 6 tasks with a lean set that maps to the "done" criteria:

| Task | "Done" criterion | Type |
|------|-----------------|------|
| Process inbox to zero | Nothing in inbox | Review |
| Clear due/overdue items | No due items unaddressed | Review |
| Review daily log | Verify completions look right | Review |
| Generate daily log | Completed tasks → Obsidian | Automation trigger |

The project should:
- Be set to sequential (tasks appear one at a time)
- Repeat daily (defer to end-of-work time, e.g., 5:00 PM)
- Keep tags `Evening🕕`, `Routine🔁`
- Update the note to remove references to the missing perspective and reflect the new structure

**1b. Add `perspective-configure` action to ofo-core.ts**

New action that modifies filter rules on an existing custom perspective. The Omni Automation API allows `Perspective.Custom.byName()` retrieval and setting `archivedFilterRules` + `archivedTopLevelFilterAggregation`, but has no constructor — perspectives must be created manually in OmniFocus Pro first.

The action accepts:
- `name` or `id` — perspective to configure
- `rules` — array of filter rule objects (replaces existing rules)
- `aggregation` — "all", "any", or "none" (optional, defaults to "all")

This enables programmatic perspective setup after one-time manual creation.

**1c. Add `ofo perspective-configure` CLI command**

New command in `ofo-cli.ts` that calls the `perspective-configure` action. Accepts `--name`, `--rules` (JSON string), and `--aggregation` flags.

**1d. Create Shutdown Procedure perspective**

Manually create an empty "Shutdown Procedure" perspective in OmniFocus Pro, then configure via `ofo perspective-configure`:
- Rules: inbox items (available), due/overdue items, flagged items
- Aggregation: "any" (show tasks matching any rule)

**1e. Configure existing Completed Today perspective**

Existing perspective (`omnifocus:///perspective/a0hgqFyITwd`) already has correct base rules:
```json
[
  {"actionAvailability": "completed"},
  {"actionDateField": "completed", "actionDateIsToday": true}
]
```
Aggregation: `"all"`. Needs `Routine🔁` tag exclusion added (tag ID: `kyjgspU3bkU`).

Note: The Omni Automation filter rule schema uses tag IDs, not names. Tag exclusion may require nested rules with `"none"` aggregation — test during implementation. If the perspective API can't express tag exclusion in rules, the `completed-today` action handles filtering in code (which it already does).

### Phase 2: Daily Log CLI Command

**Design principle: Perspectives over scripts.** The existing "Completed Today" perspective is the query engine. No new `ofo-core.ts` action is needed — the CLI command queries the perspective and handles filtering/formatting.

**2a. Add `ofo completed-today` CLI command**

New command in `ofo-cli.ts` that:
1. Calls the existing `ofo-perspective` action with `name: "Completed Today"`
2. Filters out `Routine🔁` tagged tasks in the CLI layer
3. Categorizes remaining tasks by tag membership:
   - **Tasks completed** — no special capture tag
   - **Questions answered** — tagged `Question❓`
   - **Discontents resolved** — tagged `Discontent⁉️`
   - **Decisions made** — tagged `Decide😤`
4. Default output: categorized JSON
5. With `--markdown` flag: formatted markdown suitable for piping to `obsidian-cli`

**2b. Obsidian integration via existing tools**

No standalone script needed. Use `obsidian-cli` and the `vault-curator` skill for all Obsidian interactions:
```bash
ofo completed-today --markdown | obsidian append "500 ♽ Cycles/520 🌄 Days/YYYY/YYYY-MM-DD.md"
```

### Phase 3: Wire It Together

- Update the routine's "Generate daily log" task note with the CLI command
- Test the full flow: process inbox → clear overdue → review completions → generate log → check Obsidian
- Verify recurrence works (complete routine → defers to tomorrow)

## Technical Approach

### Key files to modify/create

| File | Change |
|------|--------|
| `scripts/src/ofo-core.ts` | Add `ofoPerspectiveConfigure()` action + dispatch case |
| `scripts/src/ofo-core-ambient.d.ts` | Add writable `archivedFilterRules` / `archivedTopLevelFilterAggregation` declarations |
| `scripts/src/ofo-cli.ts` | Add `perspective-configure` and `completed-today` commands (completed-today queries existing perspective, no new core action) |
| `scripts/build-plugin.sh` | No changes needed (builds from src/) |
| OmniFocus project | Restructure via ofo CLI (update/create/complete tasks) |
| OmniFocus perspectives | Create empty perspectives manually, configure rules via `ofo perspective-configure` |

### Daily log markdown format

```markdown
## Completed Today

### Tasks
- Task name 1 (Project Name)
- Task name 2 (Project Name)

### Questions Answered
- Question text (Project Name)

### Discontents Resolved
- Discontent text (Project Name)

### Decisions Made
- Decision text (Project Name)
```

Sections with zero items are omitted. If nothing was completed, output a simple "No completions logged today."

### Querying completed tasks

The OmniFocus Omni Automation API provides `completionDate` on tasks. The query:
```
flattenedTasks.filter(t =>
  t.completed &&
  t.completionDate >= todayStart &&
  t.completionDate < todayEnd &&
  !t.tags.some(tag => tag.name === 'Routine🔁')
)
```

Categorization by checking tag membership: `Question❓`, `Discontent⁉️`, `Decide😤`.

## Acceptance Criteria

- [ ] OmniFocus routine project restructured with 4 tasks matching "done" criteria
- [ ] Project repeats daily with defer to end-of-work time
- [ ] `ofo perspective-configure` sets filter rules and aggregation on an existing perspective
- [ ] Shutdown Procedure perspective configured with inbox + due/overdue + flagged rules
- [ ] Completed Today perspective configured with completed-today rules minus Routine
- [ ] `ofo completed-today` queries Completed Today perspective and returns categorized JSON (no new core action — perspective is the query engine)
- [ ] `ofo completed-today --markdown` outputs formatted markdown suitable for piping to `obsidian-cli`
- [ ] Routine🔁 tagged tasks excluded from the log
- [ ] Questions, discontents, and decisions appear in their own sections
- [ ] Empty sections are omitted from the output
- [ ] Skillsmith evaluation >= 95 after SKILL.md updates

## Dependencies & Risks

**Dependencies:**
- ofo CLI v2.0.0 (TypeScript plugin library — just shipped)
- obsidian-cli for appending to daily notes
- OmniFocus 4 with Omni Automation enabled
- Tags `Question❓`, `Discontent⁉️`, `Decide😤`, `Routine🔁` exist in OmniFocus

**Risks:**

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `completionDate` not available in Omni Automation API | Low | High | Test with one task first; fall back to JXA if needed |
| obsidian-cli `append` doesn't support targeted insertion | Medium | Low | Append to end of file is acceptable |
| Perspective creation requires manual OmniFocus Pro step | Medium | Low | Only the empty perspective must be created manually; rules are set via `ofo perspective-configure` |
| Filter rule object schema undocumented | Medium | Medium | Inspect existing perspective rules via `ofo perspective` to reverse-engineer the schema |

## Scope Boundaries

- **In scope:** Project restructure, `perspective-configure` action, 2 perspectives, `completed-today` action, CLI command, daily log script
- **Out of scope:** Metrics/analytics (questions per week, discontents per month)
- **Out of scope:** Auto-processing questions (FAQ, research agents)
- **Out of scope:** Auto-delegating discontents to agents
- **Out of scope:** OmniFocus plugin action with keyboard shortcut (stretch goal, defer)

## Sources & References

### Origin

- **Origin document:** [820 Brainstorms/2026-03-19-end-of-day-routine-redesign-requirements.md] — Key decisions: lean routine over checklist, filter by tag not project, dual trigger (CLI + OmniFocus), append not overwrite

### Internal References

- ofo-core.ts: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/src/ofo-core.ts`
- ofo-cli.ts: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/src/ofo-cli.ts`
- CONTRIBUTING.md: `plugins/omnifocus-manager/CONTRIBUTING.md`
- Omni Automation guide: `plugins/omnifocus-manager/skills/omnifocus-manager/references/omni_automation_guide.md`

### Related Work

- Issue #111: Automatic learning pipeline (this adds the first compound action: `completed-today`)
- PR #112: TypeScript plugin library migration (foundation for this work)
