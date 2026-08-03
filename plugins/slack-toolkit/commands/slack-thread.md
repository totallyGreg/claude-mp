---
description: Pull a Slack thread as readable markdown
argument-hint: [thread-url | channel-id ts]
allowed-tools: Bash(uv run:*)
---

<!--
/slack-thread - Pull a full Slack thread into readable markdown for parsing/reading.
Accepts a thread URL, or a channel ID + parent ts. Resolves user names and links.
-->

Full thread:
!`uv run ${CLAUDE_PLUGIN_ROOT}/skills/slack-toolkit/scripts/slacker.py thread $ARGUMENTS`

Present the thread above cleanly:
- Keep the parent message first, then replies in order.
- Preserve the resolved names, timestamps, and any `[label](url)` links and 📎 file attachments.
- If the user asks for a summary, summarize key points, decisions, and action items with the participant names.
- If the output is an error or empty, say the thread could not be retrieved and show the error. For a large thread, note that `--limit` (default 500, cap 1000) bounds the fetch.
