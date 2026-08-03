---
description: Search Slack messages across all your channels
argument-hint: <query>  (supports in:#channel, from:@me, after:YYYY-MM-DD)
allowed-tools: Bash(uv run:*)
---

<!--
/slack-search - Search messages across every channel and DM you can access or have
contributed to (Slack search.messages, user token only). Supports query modifiers.
-->

Search results:
!`uv run ${CLAUDE_PLUGIN_ROOT}/skills/slack-toolkit/scripts/slacker.py search "$ARGUMENTS"`

Present the matches above:
- Group or order by relevance (default) — each match shows author, `#channel`, timestamp, text, and a permalink.
- If the user asked a question, synthesize an answer across matches and cite the channels/permalinks.
- Use query modifiers when helpful: `in:#channel`, `from:@someone`, `after:YYYY-MM-DD`, `before:`, `during:`. Suggest narrowing if there are too many results.
- If the output reports a missing scope (`search:read`) or empty results, tell the user: cross-channel search needs the `search:read` user-token scope — run `/slack-auth` to check.
