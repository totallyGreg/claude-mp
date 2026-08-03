---
description: Digest recent activity across Slack channels
argument-hint: --channels C1 C2 --since 7d  (or --channels-file <path>)
allowed-tools: Bash(uv run:*)
---

<!--
/slack-catchup - Multi-channel digest over a time range. Resolves names, pulls threads.
Requires --since (Nh/Nd/Nw or YYYY-MM-DD) and either --channels or --channels-file.
-->

Catch-up digest:
!`uv run ${CLAUDE_PLUGIN_ROOT}/skills/slack-toolkit/scripts/slacker.py catchup $ARGUMENTS`

Present the digest above:
- Group by channel (already sectioned in the output), most recent activity first.
- Surface decisions, questions, and action items with the participant names and channel.
- Keep `[label](url)` links intact so the user can follow up.
- If output says no activity, tell the user nothing was posted in the given window.
- If arguments are missing, remind the user: `--since` is required, plus `--channels C1 C2` or `--channels-file <path>`. Suggest `/slack-channels <name>` to look up channel IDs.
