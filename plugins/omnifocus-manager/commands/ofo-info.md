---
description: Look up an OmniFocus task or project by ID or omnifocus:// URL
argument-hint: [task-id or omnifocus:// URL]
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/*)
---

<!--
/ofo:info - Look up a task or project by ID or omnifocus:// URL.
Parses omnifocus:///task/<id> and omnifocus:///project/<id> URL schemes.
Fetches full details and presents them in a readable summary.
-->

## Step 1: Parse the ID

The argument is: `$ARGUMENTS`

If `$ARGUMENTS` starts with `omnifocus://`, extract the entity ID:
- `omnifocus:///task/<id>` → task ID is `<id>`
- `omnifocus:///project/<id>` → project ID is `<id>` (use project-info)
- `omnifocus:///folder/<id>` → folder ID

If `$ARGUMENTS` is a bare ID (no `://`), treat it as a task ID.

## Step 2: Fetch Details

For a task ID:
```bash
cd "${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager" && osascript -l JavaScript scripts/manage_omnifocus.js task-info --id "<id>"
```

For a project ID:
```bash
cd "${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager" && osascript -l JavaScript scripts/manage_omnifocus.js project-info --id "<id>"
```

## Step 3: Present

Show the details in a clean summary:
- **Name**, Project, Tags, Due, Defer, Estimated time
- Note content (if any)
- For projects: task count, completion status

If no ID provided or lookup fails, say: "Provide a task ID or `omnifocus://` URL as an argument."
