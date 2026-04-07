---
name: ss-observe
description: Analyze a Claude Code session transcript to identify skill gaps
argument-hint: [session-id | observation | both]
---

Analyze session transcripts for skill structural gaps, optionally focused by a user-provided observation.

## Input

`$ARGUMENTS` may be:

- **Session ID or path** (UUID or ends in `.jsonl`) — analyze that session
- **Natural-language observation** ("I noticed X") — analyze the current session, focused on that failure
- **Both** — `<session-id> -- I noticed X` — analyze the specified session, focused on the observation
- **Empty** — analyze the most recent session for this project

## Step 1: Resolve session

If `$ARGUMENTS` contains a session ID or `.jsonl` path, use it. Otherwise default to the most recent session:

```bash
ls -lt ~/.claude/projects/-Users-totally-Documents-Projects-claude-mp/*.jsonl 2>/dev/null | head -1 | awk '{print $NF}'
```

## Step 2: Extract user observation (if any)

If `$ARGUMENTS` contains natural-language context (not a UUID/path), extract it as a **gap hint**. This focuses the analysis on the specified failure mode — the transcript remains the ground truth for what happened; the hint tells the analyzer what to prioritize.

Parse strategy:
- If `$ARGUMENTS` matches a UUID pattern or file path → session ID only, no hint
- If `$ARGUMENTS` contains ` -- ` → split on ` -- `: first part is session ID, rest is hint
- Otherwise → treat entire `$ARGUMENTS` as a hint, use default session from Step 1

## Step 3: Run analysis

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/agents/skill-observer/scripts/analyze_transcript.py \
  --session <resolved-session> \
  [--hint "<user observation>"] \
  [--skill <skill-name>]
```

To filter to a specific skill or agent, append `--skill <name>`. The `--skill` flag matches both skill names and agent `subagent_type` values (e.g., `--skill archivist` matches the `archivist:archivist` agent).

> **Note:** `ss-observe` runs `analyze_transcript.py` as a subprocess rather than launching the
> skill-observer agent directly. This avoids plugin cache path-permission issues that block
> Agent-tool reads of `~/.claude/plugins/cache/` in background mode.

## Step 4: Report and offer improve cycle

Report the gap analysis output. The report includes:

- **Skills and agents active in session** — a unified table with a Type column (`Skill` or `Agent`) showing what was invoked
- **Structural gaps** — per-skill gap analysis for skills; `validate-agent.sh` output for locally-resolved agents; `third-party` note for externally-installed entries

If structural gaps are found:

1. Summarize the top gap (highest occurrence count or hint-matched)
2. Identify the source skill/agent path from the report
3. Offer:
   - **Apply now**: Run `/ss-improve <skill-path>` to fix the top gap immediately
   - **Defer**: Note the gap and continue the current session

**Automatic triggering note:** This command can be invoked programmatically (e.g., by a hook after repeated skill failures) with the failure context passed as the hint. The observe→improve cycle can be automated when gap patterns repeat.
