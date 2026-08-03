---
description: Publish a Slack Canvas from a markdown file
argument-hint: "<title>" --file <path.md> [--share-channels C...] [--share-users U...]
allowed-tools: Bash(uv run:*)
---

<!--
/slack-canvas - Publish a readable Slack Canvas from a local markdown file, optionally
shared with channels/users in one shot. Wraps `slacker.py canvas publish`.
Pass a quoted title plus at least --file <path>. H4+ headings auto-downgrade to H3.
-->

Publishing canvas:
!`uv run ${CLAUDE_PLUGIN_ROOT}/skills/slack-toolkit/scripts/slacker.py canvas publish $ARGUMENTS`

Report the result of the command above:
- On success (`{"canvas_id": "F..."}`), confirm the Canvas was created, state the canvas ID, and note any channels/users it was shared with.
- If `--file` was omitted or empty, tell the user a quoted title and `--file <path.md>` are required, e.g. `/slack-canvas "Team Update" --file notes.md --share-channels C0123`.
- If a warning about quip/non-editable canvases appears on stderr but a `canvas_id` was returned, the create still succeeded — report success and mention updates may require recreating on quip workspaces.
- Trust `{"canvas_id": ...}` as authoritative — do not do a verification read.
