---
description: Show overdue tasks grouped by category with recommended actions
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/*)
---

<!--
/ofo:overdue - Show overdue tasks.
Fetches all overdue tasks and presents them grouped by type with recommended actions.
Ghost recurrences (same name, multiple instances) are flagged for batch-complete.
-->

Overdue tasks:
!`${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo list overdue`

Present the overdue tasks above as a table: **Task | Project | Days Overdue | Recommended Action**

Group by:
- 🔁 **Routine Decay** — tasks tagged Routine with multiple instances of the same name (flag with 🔁, recommend batch-complete)
- **Work** — tasks in work projects
- **Health** — tasks tagged Self Maintenance or in Health projects
- **Financial** — tasks in financial projects
- **Personal** — everything else

If no overdue tasks, say: "No overdue tasks. ✓"
