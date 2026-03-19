---
name: ss-observe
description: Analyze a Claude Code session transcript to identify skill gaps
argument-hint: [session-id-or-path]
---

Analyze session `$ARGUMENTS` for skill structural gaps.

If no session ID provided, list recent sessions and ask the user which to analyze:

```bash
ls -lt ~/.claude/projects/-Users-totally-Documents-Projects-claude-mp/*.jsonl | head -10
```

Then run the skill-observer agent:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/agents/skill-observer/scripts/analyze_transcript.py --session $ARGUMENTS
```

To filter to a specific skill:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/agents/skill-observer/scripts/analyze_transcript.py --session $ARGUMENTS --skill <skill-name>
```

Report the gap analysis and suggest specific improvements to apply via `/ss-improve`.
