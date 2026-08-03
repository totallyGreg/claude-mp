---
description: Show tasks with a specific tag, grouped by project with progress
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core/scripts/*), Bash(osascript:*)
---

<!--
/ofo:tagged <tag> - Lightweight tag query bypassing agent routing.
Calls the ofo CLI (first-class `tagged` command) for grouped results.
-->

Query OmniFocus for tasks with the specified tag:
```bash
"${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core/scripts/ofo" tagged "$ARGUMENTS"
```

If no argument was provided, ask the user which tag to query.

Parse the JSON output and present as:

**Tag: "<tag name>"** — N active tasks across M projects (X/Y complete)

For each project:
- **Project Name** (completed/total complete)
  - Task 1 — status, due date if set
  - Task 2 — status, due date if set

If the tag is not found, say: "No tag found matching that name."
If no tasks have the tag, say: "No tasks found with that tag."
