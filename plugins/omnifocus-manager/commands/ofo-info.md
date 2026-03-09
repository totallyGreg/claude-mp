---
description: Look up an OmniFocus task or project by ID or omnifocus:// URL
argument-hint: [task-id or omnifocus:// URL]
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/*)
---

<!--
/ofo:info - Look up a task or project by ID or omnifocus:// URL.
Uses the ofo CLI which handles URL parsing and type detection automatically.
-->

Fetch details (the ofo CLI handles omnifocus:// URL parsing automatically):
!`${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo info $ARGUMENTS`

Show the details in a clean summary:
- **Name**, Project, Tags, Due, Defer, Estimated time
- Note content (if any)
- For projects: task count, completion status

If no ID provided or lookup fails, say: "Provide a task ID or `omnifocus://` URL as an argument."
