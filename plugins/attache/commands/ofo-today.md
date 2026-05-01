---
description: Show today's flagged and due tasks from OmniFocus
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core/scripts/*)
---

<!--
/ofo:today - Show today's tasks.
Fetches flagged and due-today tasks from OmniFocus and presents them in a clean list.
-->

Today's tasks:
!`${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core/scripts/ofo list today`

Present the JSON output above as a clean task list grouped by:
- **Due Today** — tasks with a dueDate of today
- **Flagged** — tasks marked flagged (deduplicate with Due Today)

For each task show: task name, project, and estimated time (if set).
If the list is empty, say: "Nothing due or flagged for today."
