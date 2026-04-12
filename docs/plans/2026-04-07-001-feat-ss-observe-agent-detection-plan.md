---
title: "feat: ss-observe agent detection and validate-agent.sh integration"
type: feat
status: active
date: 2026-04-07
---

# feat: ss-observe agent detection and validate-agent.sh integration

## Overview

`ss-observe` / `analyze_transcript.py` only tracks `Skill` tool invocations. Agents invoked via the `Agent` tool (`subagent_type: archivist:archivist`) are invisible to it, producing misleading "No Skill tool calls found" reports. As more workflows route through agents rather than skills directly, the observer becomes blind to the dominant invocation pattern.

The fix: detect `Agent` tool calls alongside `Skill` tool calls, resolve the invoked agent's `.md` definition file, and validate it using `validate-agent.sh` from the plugin-dev plugin. Also fix a pre-existing `relative_to(Path.cwd())` crash when a skill/agent source path is outside the working directory.

## Problem Frame

Gap 3 from session analysis: `ss-observe` only detects Skill tool invocations. Agent tool calls (e.g. `subagent_type: archivist:archivist`) produce no entry in the skills table. The observer reports "No Skill tool calls found" on sessions where the archivist agent was the primary entry point, giving a false all-clear.

The user's direction: for agent invocations, call `validate-agent.sh` from the plugin-dev plugin — already used by the plugin validator workflow — rather than building a parallel evaluator.

## Requirements Trace

- R1. Agent tool calls (`block.name == "Agent"` with `block.input.subagent_type`) are tracked in session analysis alongside Skill tool calls
- R2. Agent invocations resolve to their `.md` source file using the `subagent_type` namespace pattern
- R3. For local agent definitions, `validate-agent.sh` is found dynamically and run; output is included in the gap report
- R4. `relative_to(Path.cwd())` crash on out-of-cwd paths is fixed
- R5. Output table distinguishes Skill invocations from Agent invocations

## Scope Boundaries

- Does not implement child-session recursion (following the subagent's own JSONL for internal gaps) — deferred
- Does not change `evaluate_skill.py` or the skillsmith scoring pipeline
- Does not add `--agent` CLI flag; agent detection is always-on alongside skill detection
- `validate-agent.sh` SIGPIPE/pipefail false-positive on the frontmatter check is a known upstream bug — the script output is captured and reported as-is; the exit code is not treated as authoritative

## Context & Research

### Relevant Code

- `plugins/skillsmith/agents/skill-observer/scripts/analyze_transcript.py` — all changes land here
- `plugins/skillsmith/commands/ss-observe.md` — update documentation for agent detection
- `validate-agent.sh` lives in the plugin-dev marketplace plugin, not in this repo:
  - Installed path: `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/skills/agent-development/scripts/validate-agent.sh`
  - Discovery: search `~/.claude/plugins/` for `plugin-dev/skills/agent-development/scripts/validate-agent.sh`

### Agent Tool JSON Structure (from real session JSONL)

```
block.name == "Agent"
block.input.subagent_type  →  "archivist:archivist"
                               "compound-engineering:research:repo-research-analyst"
```

### `subagent_type` → agent `.md` resolution pattern

```
archivist:archivist                         → plugins/archivist/agents/archivist.md
compound-engineering:review:correctness     → plugins/compound-engineering/agents/review/correctness.md
```

Rule: first segment = plugin name; last segment = agent filename; middle segments (if any) = subdirectory under `agents/`.

### Existing invocation detection (lines 97–121)

`extract_skill_invocations()` already walks `msg.message.content[]` looking for `block.type == "tool_use" && block.name == "Skill"`. Agent detection follows the same pattern with `block.name == "Agent"`.

### Crash location (line 522)

```python
source = f"`{Path(s['source_path']).relative_to(Path.cwd()) if s['source_path'] else 'third-party'}`"
```

`relative_to()` raises `ValueError` when `source_path` is not under `Path.cwd()` (e.g. a skill installed in `~/.claude/plugins/`). Fix: wrap in try/except and fall back to the absolute path.

## Key Technical Decisions

- **Always-on detection**: Agent calls detected in the same pass as Skill calls — no new flag needed. Mixed sessions (both Skill and Agent invocations) are handled naturally.
- **Dynamic script discovery**: `validate-agent.sh` is found by walking `~/.claude/plugins/` rather than hardcoding the path. If not found, report the agent as unvalidatable (same behaviour as third-party skills) without crashing.
- **Exit code not authoritative**: `validate-agent.sh` has a known SIGPIPE/pipefail false-positive. Capture stdout regardless of exit code and include it in the report; do not gate on exit code.
- **Unified invocation list**: Skills and agents share the same `invocations` list in the result dict, each tagged with `invocation_type: 'skill' | 'agent'`. The output table adds a Type column.

## Open Questions

### Deferred to Implementation

- Whether `subagent_type` segments for compound-engineering agents (e.g. `compound-engineering:research:repo-research-analyst`) map to subdirectories or flat filenames — verify against the marketplace agent directory structure during implementation before finalising the resolution logic.
- Whether the plugin-dev marketplace may be installed at a different base path on other machines — if `validate-agent.sh` is not found, degrade gracefully and surface a clear message.

## Implementation Units

- [x] **Unit 1: Detect Agent tool invocations in JSONL**

**Goal:** Extend `extract_skill_invocations()` to also capture `Agent` tool calls, returning a unified invocation list tagged by type.

**Requirements:** R1, R5

**Dependencies:** None

**Files:**
- Modify: `plugins/skillsmith/agents/skill-observer/scripts/analyze_transcript.py`

**Approach:**
- Rename or extend `extract_skill_invocations()` — scan the same `msg.message.content[]` block loop; when `block.name == "Agent"`, extract `block.input.subagent_type` as the identifier
- Each record gets an `invocation_type` field: `'skill'` for Skill tool, `'agent'` for Agent tool
- `group_tool_calls_by_skill()` and downstream callers key on the identifier string — no structural change needed there, just pass the `subagent_type` string the same way skill names are passed
- Update `analyze()` to handle the unified list: the `status == 'no_skills_detected'` check and message should reflect that neither skills nor agents were found

**Test scenarios:**
- Happy path: session with one Agent call → appears in invocations list with `invocation_type: 'agent'`
- Happy path: session with both Skill and Agent calls → both appear; Skill entries have `invocation_type: 'skill'`
- Edge case: session with only Agent calls → no longer returns `'no_skills_detected'` status
- Edge case: Agent call missing `subagent_type` → skip the record, do not crash

**Verification:** Running the script against a session that used `archivist:archivist` produces an entry in the skills table instead of "No Skill tool calls found."

---

- [x] **Unit 2: Resolve agent `.md` source files**

**Goal:** Given a `subagent_type` string, find the agent's `.md` definition file in the repo (parallel to how `resolve_skill_to_source()` finds `SKILL.md`).

**Requirements:** R2

**Dependencies:** Unit 1

**Files:**
- Modify: `plugins/skillsmith/agents/skill-observer/scripts/analyze_transcript.py`

**Approach:**
- Add `resolve_agent_to_source(subagent_type, repo_root)` — parse the subagent_type by splitting on `:`, use first segment as plugin name, last as agent filename, middle segments as subdirectory path under `agents/`
- Look for `{repo_root}/plugins/{plugin}/agents/{...subdirs}/{agent}.md`
- If not found in repo, return `None` (third-party agent — same treatment as third-party skills)
- In `analyze()`, dispatch on `invocation_type`: skills go to `resolve_skill_to_source()`, agents go to `resolve_agent_to_source()`

**Test scenarios:**
- Happy path: `archivist:archivist` → resolves to `plugins/archivist/agents/archivist.md`
- Happy path: three-part type → resolves through subdirectory (verify actual path exists first)
- Edge case: unknown plugin → returns None, reported as third-party

**Verification:** `resolve_agent_to_source('archivist:archivist', repo_root)` returns the correct absolute path to the agent file.

---

- [x] **Unit 3: Validate agent definitions via validate-agent.sh**

**Goal:** For locally-resolved agents, find `validate-agent.sh` from plugin-dev and run it; include output in the gap report.

**Requirements:** R3

**Dependencies:** Unit 2

**Files:**
- Modify: `plugins/skillsmith/agents/skill-observer/scripts/analyze_transcript.py`

**Approach:**
- Add `find_validate_agent_script()` — walk `Path.home() / '.claude' / 'plugins'` looking for `plugin-dev/skills/agent-development/scripts/validate-agent.sh`; return the first match or `None`
- In `analyze()`, when `invocation_type == 'agent'` and agent source is found: call `find_validate_agent_script()`; if found, run it via `subprocess.run()` capturing stdout; do not gate on exit code (known SIGPIPE false-positive)
- Package the script's stdout as a gap entry with `type: 'agent_validation'`; if the script is not found, add a gap entry noting it could not be validated
- Agent entries that are third-party (no local source) get the same `'third_party'` gap as skills

**Test scenarios:**
- Happy path: local agent + script found → script output appears in gap report
- Edge case: `validate-agent.sh` not found → gap entry says "validate-agent.sh not found; install plugin-dev to enable agent validation"
- Edge case: script exits non-zero (SIGPIPE false-positive) → output still captured and reported
- Edge case: third-party agent (no local source) → `'third_party'` gap, no script invocation

**Verification:** Running against a session that used `archivist:archivist` produces a gap section containing the validate-agent.sh output (or a clear "not found" message).

---

- [x] **Unit 4: Fix relative_to ValueError for out-of-cwd paths**

**Goal:** Prevent crash when a source path resolves outside `Path.cwd()`.

**Requirements:** R4

**Dependencies:** None (independent fix)

**Files:**
- Modify: `plugins/skillsmith/agents/skill-observer/scripts/analyze_transcript.py` (line 522)

**Approach:**
- Wrap the `relative_to(Path.cwd())` call in a try/except `ValueError`; on exception, display the raw absolute path (or home-relative path using `~`) rather than crashing
- Same fix applies if agent `.md` paths are also displayed through this code path

**Test scenarios:**
- Error path: `source_path` under `~/.claude/plugins/` (outside cwd) → displays path without crashing
- Happy path: `source_path` under repo root → still shows repo-relative path as before

**Verification:** Running `ss-observe` on a session with a marketplace skill (e.g. `obsidian:obsidian-cli`) no longer crashes with `ValueError`.

---

- [x] **Unit 5: Update output format and ss-observe documentation**

**Goal:** Table output distinguishes Skill vs Agent invocations; ss-observe SKILL.md documents the new behaviour.

**Requirements:** R5

**Dependencies:** Unit 1, Unit 3

**Files:**
- Modify: `plugins/skillsmith/agents/skill-observer/scripts/analyze_transcript.py` (format_markdown)
- Modify: `plugins/skillsmith/commands/ss-observe.md`

**Approach:**
- Add a `Type` column to the skills table: `Skill` or `Agent`
- Agent gap sections use a distinct header: `#### <agent-name> (agent)` vs `#### <skill-name> (skill|third-party)`
- `ss-observe.md`: update the Step 3 command description to mention `--skill` also matches agent subagent_type; update the "Skills Active in Session" description to say "Skills and agents active in session"

**Test scenarios:**
- Happy path: mixed session → table shows both Skill and Agent rows with correct Type column values

**Verification:** Table renders with Type column; agent rows clearly distinct from skill rows.

## System-Wide Impact

- **Interaction graph:** `analyze()` is the only caller of `extract_skill_invocations()` — all changes are self-contained within the script
- **Unchanged invariants:** Skill detection, gap analysis, and output format for existing Skill tool invocations are unchanged; this is additive
- **validate-agent.sh coupling:** The script is an external dependency from a marketplace plugin; the plan degrades gracefully if absent

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| `subagent_type` subdirectory mapping is wrong for compound-engineering agents | Verify actual agent directory structure during Unit 2 implementation before finalising |
| `validate-agent.sh` SIGPIPE false-positive makes output noisy | Capture output regardless of exit code; do not gate report on exit code |
| `validate-agent.sh` may not be installed | Degrade gracefully with a clear message; never crash |

## Sources & References

- Agent tool JSONL structure: observed in `~/.claude/projects/*/` session files
- `validate-agent.sh`: `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/skills/agent-development/scripts/validate-agent.sh`
- `analyze_transcript.py`: `plugins/skillsmith/agents/skill-observer/scripts/analyze_transcript.py`
- SIGPIPE/pipefail bug in validate-agent.sh: documented earlier in this session (line 41 of the script)
