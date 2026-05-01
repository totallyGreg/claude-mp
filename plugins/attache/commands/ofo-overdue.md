---
description: Show overdue tasks grouped by category with recommended actions
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core/scripts/*)
---

<!--
/ofo:overdue - Show overdue tasks.
Fetches all overdue tasks and presents them grouped by type with recommended actions.
Ghost recurrences (same name, multiple instances) are flagged for batch-complete.
-->

Overdue tasks:
!`${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core/scripts/ofo list overdue`

Present the overdue tasks above as a table: **Task | Project | Days Overdue | Recommended Action**

Group by:
- **Stale Routines** — overdue tasks where `repetitionRule` is not null (repeating tasks)
  - Show: Task | Project | Days Overdue | Recurrence | Catch Up | Recommended Action
  - For recommended action, use the drop vs complete decision tree:
    - `repetitionCatchUp` true → "Drop to reset: `ofo drop <id>`"
    - `repetitionScheduleType` "FromCompletion" → "Complete if done, drop if skipped"
    - `repetitionScheduleType` "Regularly" + >7 days overdue → "Drop to move forward: `ofo drop <id>`"
    - `repetitionScheduleType` "Regularly" + <=7 days overdue → "Complete if done, drop if skipped"
- **Work** — non-repeating tasks in work projects
- **Health** — non-repeating tasks tagged Self Maintenance or in Health projects
- **Financial** — non-repeating tasks in financial projects
- **Personal** — everything else (non-repeating)

If no overdue tasks, say: "No overdue tasks."
