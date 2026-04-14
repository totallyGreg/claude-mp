---
title: "fix: Resolve health check workflow friction — script defaults, agent context loss, and result clarity"
type: fix
status: completed
date: 2026-03-31
---

# fix: Resolve health check workflow friction — script defaults, agent context loss, and result clarity

## Overview

The `/health` command and subsequent workflows (duplicates, collection fixes, orphan triage) have significant friction: scripts return capped results without the agent requesting more, orphan metrics are inconsistent between tools, the health command produces no structured summary, and multi-step remediation loses context across agent respawns. This plan addresses the gaps observed in a real health check session on 2026-03-31.

## Problem Frame

A user ran `/archivist:health` to assess vault health, then wanted to drill into duplicates and create a vault profile. The session required 4+ agent spawns, hit permission denials, lost accumulated context between agents, and produced inconsistent orphan counts (3,020 vs 846) with no explanation of the discrepancy. The duplicate finder capped at 20 groups out of 325 because the agent never passed `--max-groups`. Collection health found only 2 collections when dozens of folders have collection-like structure. The vault profile creation required 3 agent attempts before succeeding.

These are not fundamental architecture issues — they're workflow instruction gaps in the agent and command definitions that cause the agent to use tools suboptimally.

## Requirements Trace

- R1. Health command produces a structured, actionable report with consistent metrics and explained discrepancies
- R2. Script invocations use appropriate defaults for vault-scale operations (not development defaults)
- R3. Multi-step remediation workflows preserve context within a single agent session instead of requiring respawns
- R4. Collection detection covers folders with collection-like patterns, not just those with explicit infrastructure

## Scope Boundaries

- No changes to Python scripts — only agent/command/skill markdown files
- No new Python dependencies or scripts
- Does not address permission zone enforcement (covered by plan 001)
- Does not address vault profile creation (covered by plan 001, Unit 1)
- Focus is on the health → diagnose → remediate flow, not all archivist workflows

## Context & Research

### Relevant Code and Patterns

- `commands/health.md` — thin wrapper, 4 lines of instruction, no structured output guidance
- `agents/archivist.md` — orchestrator loads both skills, routes workflows, has script usage tables
- `find_similar_notes.py` — `--max-groups` defaults to 20, supports any value
- `check_collection_health.py` — detects collections by folder note presence, misses folders without folder notes
- `obsidian orphans` CLI command — counts notes with no *incoming* links
- `analyze_vault.py` — counts notes with no links *in or out* (fully isolated)

### Friction Points Observed (2026-03-31 session)

1. **Orphan count inconsistency**: CLI `obsidian orphans` = 3,020 (no incoming links). `analyze_vault.py` = 846 (no links at all). Neither the health command nor the agent explains this difference.
2. **Duplicate finder capped at 20/325**: Agent invoked `find_similar_notes.py` without `--max-groups`, getting default 20. The script found 325 groups total. Agent should pass `--max-groups 100` for health assessments.
3. **Collection detection gaps**: `check_collection_health.py` only detected 2 collections (000 Pillars, 800 Generated). Folders like People, Companies, Meetings, Tools, Terminology have collection-like patterns (shared fileClass, consistent structure) but no folder notes, so they're invisible to the script.
4. **Context loss across agent spawns**: Health → duplicates → vault profile required 3 separate agent spawns. Each lost the accumulated vault context, metrics, and user decisions from prior steps.
5. **Permission denials on write**: Agent couldn't write `_vault-profile.md` — both Bash and Write tool permissions were denied. No fallback or guidance in the agent instructions.
6. **Health output is unstructured prose**: No summary table, no priority tiers, no "here's what to fix first" — just raw script output interpreted ad hoc.

## Key Technical Decisions

- **Fix in command and agent instructions, not scripts**: The scripts already support the needed parameters (`--max-groups`, `--scope`). The gap is that agent/command instructions don't guide the agent to use them appropriately. Fixing instructions is lower-risk and faster than modifying Python.

- **Add a "Health Report Template" to the health command**: Rather than letting the agent improvise report structure, define the expected output format — summary table, metric explanations, prioritized issues, next actions. This makes reports consistent across sessions.

- **Add "Continuation Workflows" to the health command**: Instead of ending with "offer to fix top issues" (which requires the user to respawn the agent), define explicit follow-on workflows that run within the same agent session: "drill into duplicates", "fix collection health", "triage orphans".

- **Explain orphan metric discrepancy in the health template**: Document that `obsidian orphans` counts notes with no incoming links (may still link out), while `analyze_vault.py` counts fully isolated notes (no links in or out). Present both with labels.

- **Add "candidate collections" detection guidance**: When `check_collection_health.py` finds few collections, instruct the agent to also scan for folders with 10+ notes sharing a fileClass or consistent frontmatter pattern — these are collection candidates that need infrastructure (folder note, Bases file).

## Open Questions

### Resolved During Planning

- **Should we modify the Python scripts?** → No. The scripts already support the needed parameters. The gap is in how the agent invokes them.
- **Should health run in the main context or as a subagent?** → As a subagent (current behavior via `/health` command), but with structured output that the parent can act on. The key fix is making the subagent's session long enough to include follow-on workflows.

### Deferred to Implementation

- Exact threshold for "candidate collection" detection (10+ notes with shared fileClass is a starting point)
- Whether the health report should be saved to a vault file (e.g., `800 Generated/health-report-YYYY-MM-DD.md`) — useful for tracking trends but adds write complexity

## Implementation Units

- [ ] **Unit 1: Improve health command with structured report template and continuation workflows**

  **Goal:** Replace the thin health command with structured output guidance and in-session follow-on workflows.

  **Requirements:** R1, R3

  **Dependencies:** None

  **Files:**
  - Modify: `commands/health.md`

  **Approach:**
  - Add a "Report Template" section to the health command that defines the expected output structure: summary scorecard table (metric | value | status), metric explanations (especially orphan count discrepancy), prioritized issue list with tiers (Critical / Structural / Housekeeping), and a numbered menu of continuation workflows
  - Add continuation workflows that run within the same agent session:
    1. "Deep-dive duplicates" → run `find_similar_notes.py` with `--max-groups 100` on a user-selected scope
    2. "Fix collection health" → run `check_collection_health.py` then scaffold missing infrastructure
    3. "Triage orphans" → scope to a specific import folder, batch-review orphans
    4. "Schema drift detection" → pick a fileClass, run `detect_schema_drift.py`
    5. "Create/update vault profile" → run vault profiling workflow
  - Each continuation workflow should be a self-contained instruction block that the agent can follow without needing to respawn

  **Patterns to follow:**
  - Existing `commands/vault.md` structure
  - Existing workflow sections in `agents/archivist.md` (Consolidation: Find Duplicates, etc.)

  **Test scenarios:**
  - Happy path: User runs `/health` → agent produces structured report with summary table, explained metrics, prioritized issues, and numbered continuation menu
  - Happy path: User selects "Deep-dive duplicates" from continuation menu → agent runs duplicate finder with `--max-groups 100` within same session, no respawn needed
  - Edge case: All health metrics are clean (no orphans, no duplicates) → report shows healthy status, continuation menu still available for proactive workflows
  - Edge case: Script execution fails (uv not installed, Python version mismatch) → agent reports the failure clearly and suggests manual alternatives

  **Verification:**
  - Health command produces a consistent, structured report with summary table
  - Continuation workflows execute within the same agent session
  - Orphan count discrepancy is explained in the report

- [ ] **Unit 2: Fix script invocation defaults in agent orchestration**

  **Goal:** Update agent workflow instructions to use vault-appropriate script parameters instead of development defaults.

  **Requirements:** R2

  **Dependencies:** None (can be implemented in parallel with Unit 1)

  **Files:**
  - Modify: `agents/archivist.md` (Consolidation: Find Duplicates section, Vault Analysis section, Collection Health Check section)

  **Approach:**
  - In "Consolidation: Find Duplicates" workflow: change the `find_similar_notes.py` invocation to include `--max-groups 100` by default. Add a note: "For health assessments (broad survey), use `--max-groups 100`. For targeted duplicate resolution (acting on results), use `--max-groups 20` or the default."
  - In "Vault Analysis" section: add a step after running `analyze_vault.py` to also run `obsidian orphans` and reconcile the two orphan counts. Add explanation text: "analyze_vault.py counts fully isolated notes (no links in or out). `obsidian orphans` counts notes with no incoming links (may still link out). Present both with clear labels."
  - In "Collection Health Check" section: after running `check_collection_health.py`, add a "Candidate Collections" scan step: "If fewer than 5 collections are detected, scan top-level folders for collection candidates — folders with 10+ notes sharing a `fileClass` value or consistent frontmatter pattern. Report these as 'potential collections needing infrastructure.'"

  **Patterns to follow:**
  - Existing script invocation patterns in `agents/archivist.md`
  - Script CLI documentation in `skills/vault-curator/references/available-scripts.md`

  **Test scenarios:**
  - Happy path: Agent runs duplicate finder during health check → passes `--max-groups 100`, gets full picture instead of capped at 20
  - Happy path: Agent runs vault analysis → reports both orphan metrics with labels explaining the difference
  - Happy path: Collection health finds 2 formal collections → agent scans for candidates, identifies Tools (100+ notes with fileClass=tool) as a candidate collection
  - Edge case: Vault has many formal collections (>5) → candidate scan is skipped (not needed)
  - Edge case: No folders meet the candidate threshold (10+ notes with shared fileClass) → agent reports "no candidate collections found"

  **Verification:**
  - Duplicate finder returns 100+ groups instead of 20 for health assessments
  - Orphan report shows two metrics with explanations
  - Collection health report includes candidate collections when formal collection count is low

- [ ] **Unit 3: Add write failure fallback guidance to agent**

  **Goal:** Give the agent explicit fallback instructions when write operations are denied, so it doesn't stall on permission denials.

  **Requirements:** R3

  **Dependencies:** None (can be implemented in parallel)

  **Files:**
  - Modify: `agents/archivist.md` (add a "Write Fallback" section near Bounded Autonomy)

  **Approach:**
  - Add a "Write Fallback" section that instructs the agent:
    1. If `Write` tool is denied → try `obsidian create path="..." content="..." overwrite silent` via Bash
    2. If Bash is also denied → compose the file content in the response and ask the user to save it manually, providing the exact path
    3. Never stall silently on permission denial — always try the next fallback or communicate clearly
  - Add to the vault profile creation workflow: "If unable to write `_vault-profile.md` after trying both Write and Bash, output the composed content and ask the user to save it"

  **Patterns to follow:**
  - Existing "Verify vault connection" fallback pattern in initialization (step 4: "If it fails, fall back to file tools")

  **Test scenarios:**
  - Happy path: Write tool works → file is saved normally
  - Edge case: Write tool denied → agent tries Bash with `obsidian create` → succeeds
  - Edge case: Both Write and Bash denied → agent outputs composed content with path, asks user to save
  - Edge case: Bash works but `obsidian create` fails (app not running) → agent falls back to `cat > path` via Bash or outputs content

  **Verification:**
  - Agent never stalls silently when writes are denied
  - All write operations have a documented fallback chain

## System-Wide Impact

- **Interaction graph:** Changes are contained to the health command and agent orchestration. No new tools, scripts, or dependencies. The health command becomes a richer entry point that chains into existing workflows.
- **Error propagation:** Write fallback chain ensures graceful degradation. Script failures already have fallback guidance in the agent.
- **State lifecycle risks:** None — no new state files or persistent data. Health reports are ephemeral (shown in agent output, not saved to vault unless explicitly requested).
- **API surface parity:** The health command's output format changes, but it's consumed by humans (not other tools), so there's no breaking change.
- **Unchanged invariants:** All Python scripts remain unchanged. Vault-architect and vault-curator skill files are not modified. The `.local.md` schema is not modified.

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Health command instructions become too long, overwhelming the agent's context | Keep instructions focused — report template + continuation menu + 5 workflow blocks. Total should be under 150 lines. |
| Agent still doesn't follow `--max-groups 100` guidance | The instruction is explicit and in the exact invocation line. If it still fails, the next step would be changing the script's default. |
| Candidate collection detection produces too many false positives | Threshold of 10+ notes with shared fileClass is conservative. Can be tuned based on usage. |

## Sources & References

- Plugin source: `/Users/gregwilliams/Documents/Projects/claude-mp/plugins/archivist/`
- Session transcript: 2026-03-31 vault health check (this session)
- Related plan: `docs/plans/2026-03-31-001-feat-archivist-permissions-vault-state-commands-plan.md`
