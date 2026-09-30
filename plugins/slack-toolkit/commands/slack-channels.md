---
description: List or resolve your Slack channels
argument-hint: [name-to-resolve]
allowed-tools: Bash(uv run:*)
---

<!--
/slack-channels - List the channels you belong to, or resolve a name to channel IDs.
With no argument, lists channels as a table. With a name, returns matching IDs.
-->

Channels:
!`uv run ${CLAUDE_PLUGIN_ROOT}/skills/slack-toolkit/scripts/slacker.py channels ${ARGUMENTS:+--resolve $ARGUMENTS}`

Present the result above:
- With no argument, show the channel table (ID · name · topic); if long, group or trim to the most relevant and note the total count.
- With a name argument, list the matching `{id, name}` pairs so the user can copy an ID into `/slack-thread`, `/slack-catchup`, or `/slack-canvas`.
- If empty, say no matching channels were found and suggest checking the name or token scopes (`channels:read`, `groups:read`).
