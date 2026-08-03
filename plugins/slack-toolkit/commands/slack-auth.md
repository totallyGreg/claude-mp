---
description: Verify Slack token and required scopes
allowed-tools: Bash(uv run:*)
---

<!--
/slack-auth - Verify the Slack token is valid and report which required scopes are
granted vs missing. Run this first when other slack-toolkit commands fail.
-->

Auth + scope check:
!`uv run ${CLAUDE_PLUGIN_ROOT}/skills/slack-toolkit/scripts/slacker.py auth-check`

Interpret the result above:
- Confirm the authenticated user and team.
- If `missing` is empty, state that all required scopes are present.
- If `missing` is non-empty, list the missing scopes and explain what breaks: `im:*`/`mpim:read` affect DM/group-DM reads, `reactions:write` affects react/unreact, `canvases:*` affect Canvas ops. Advise adding them to the token's OAuth scopes.
- If auth failed entirely, tell the user to set `$SLACK_USER_TOKEN` (or store it via `keychainctl`).
