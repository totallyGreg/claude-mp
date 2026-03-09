---
description: Search OmniFocus tasks and projects by name
argument-hint: [search term]
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/*)
---

<!--
/ofo:search - Search OmniFocus tasks by name.
Runs a text search and presents matching tasks with project context.
-->

Search results for "$ARGUMENTS":
!`${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo search $ARGUMENTS`

Present the matching tasks as a table: **Task | Project | Due | Tags**

If no results, say: "No tasks found matching '$ARGUMENTS'."
If no search term provided, say: "Provide a search term as an argument, e.g. `/ofo:search end of day`"
