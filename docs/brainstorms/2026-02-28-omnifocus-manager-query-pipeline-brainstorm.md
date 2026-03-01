---
date: 2026-02-28
topic: omnifocus-manager-query-pipeline
---

# OmniFocus Manager: Query Pipeline Overhaul

## What We're Building

A unified query pipeline for the omnifocus-manager skill where:
- A **single library** (`taskQuery.js`) is the canonical source of all query logic
- A **thin CLI wrapper** (`manage_omnifocus.js`) exposes library functions as commands
- Commands are validated with TypeScript and tested before promotion
- Verified commands become both **Claude Code slash commands** and **OmniFocus plugin actions**
- The pipeline stays current with OmniFocus API changes (e.g., PlannedDates)

**Motivation:** A user asked "how many overdue tasks?" — the simplest GTD query — and we
failed. Root cause: `taskQuery.js` has `getOverdueTasks()` but `manage_omnifocus.js` doesn't
expose it. Two parallel systems silently diverged.

## Current State

| Query    | `taskQuery.js` | `manage_omnifocus.js` | SKILL.md shows |
|----------|---------------|----------------------|----------------|
| today    | ✅ | ✅ | ✅ |
| due-soon | ✅ | ✅ | ✅ |
| flagged  | ✅ | ✅ | ❌ missing |
| overdue  | ✅ | ❌ missing | ❌ missing |
| search   | ✅ | ✅ | ✅ |

SKILL.md claims "80% of queries handled by existing scripts" — not true for core GTD queries.

## Approaches Considered

### Approach A: Library-First (Recommended)

`taskQuery.js` is the single source of truth. `manage_omnifocus.js` becomes a thin dispatch
layer that loads and calls the library — no duplicated logic. TypeScript validates the library,
tests validate the CLI output, and the pipeline promotes verified commands to plugins.

**Pros:**
- Single place to add new commands or OmniFocus API properties
- TypeScript validation catches API drift early (e.g., when PlannedDates added)
- CLI and plugins always in sync

**Cons:**
- The `eval()`-based library loading pattern failed in testing — needs investigation
- Bundling approach may be needed (preprocess library into CLI at build time)

**Best when:** We want the system to stay maintainable as OmniFocus evolves.

### Approach B: CLI-First (Simpler)

Keep `manage_omnifocus.js` self-contained (no library dependency), add missing commands
inline (overdue, etc.), and make it the canonical source. Deprecate or only use `taskQuery.js`
for plugin generation.

**Pros:**
- No loading/eval complexity
- Works right now with no infrastructure changes

**Cons:**
- Two codebases to maintain when OmniFocus API changes
- Violates DRY — logic duplicated between CLI and library

**Best when:** We only want a quick fix for overdue.

### Approach C: Status Quo (Rejected)

Maintain parallel systems but document better. This caused the problem — rejected.

## Why Library-First

The user wants "a single dependable source." Library-First is the only approach that achieves
this. The `eval()` loading problem is a solvable implementation detail — consult
[omni-automation.com](https://omni-automation.com/) for correct JXA module loading patterns.

## Key Decisions

- **Single source**: `taskQuery.js` owns all query logic; CLI is a thin wrapper
- **Missing commands**: Add `overdue` immediately; audit for others (inbox count, etc.)
- **PlannedDates**: Add to `taskQuery.js` `formatTaskInfo()` and TypeScript definitions
- **Testing**:
  - Schema/structural tests: validate JSON shape and required fields (CI-friendly)
  - Live tests: manual execution against real OmniFocus before plugin promotion
- **Commands**: Each stable query becomes both a Claude Code `/command` and an OmniFocus plugin action
- **SKILL.md**: Update quick reference to reflect all actual commands accurately

## Open Questions

1. **Library loading in JXA**: The `eval()` pattern failed — look up correct JXA module loading
   at [omni-automation.com](https://omni-automation.com/) before implementing.

2. **PlannedDates**: What fields does OmniFocus expose for planned dates? Check
   [omni-automation.com](https://omni-automation.com/) and `omnifocus.d.ts`.

3. **Command scope**: Which queries are "stable enough" to promote to Claude Code commands now?
   Candidates: overdue, today, flagged, inbox-count.

4. **Test harness**: Where do structural tests live — in the skill directory or a separate
   `tests/` directory in the plugin? How do they run in CI?

## Next Steps

→ `/workflows:plan` for implementation details

**Suggested implementation order:**
1. Research correct JXA module loading pattern (omni-automation.com) → implement in CLI
2. Add `overdue` as first end-to-end test of the unified pipeline
3. Update SKILL.md quick reference to reflect all actual commands
4. Research PlannedDates API → add to `taskQuery.js` + TypeScript defs
5. Add structural test harness
6. Audit + add remaining missing commands (inbox-count, etc.)
7. Create Claude Code commands for each stable query
8. Promote stable commands to OmniFocus plugin actions

**Reference:** [omni-automation.com](https://omni-automation.com/) — authoritative source for
JXA patterns, OmniFocus API, and module loading.
