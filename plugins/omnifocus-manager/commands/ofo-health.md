---
description: Show OmniFocus system health — inbox, overdue, stalled, and waiting counts
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/*)
---

<!--
/ofo:health - Quick GTD system health check.
Runs system-health query and presents a one-line status plus any warnings.
-->

Inbox count:
!`${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo list inbox`

Overdue count:
!`${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo list overdue`

Flagged count:
!`${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo list flagged`

Present the health data as:

**System Health:** `Inbox: N | Overdue: N | Stalled: N | Waiting: N`

Then flag any counts that need attention:
- Inbox > 0 → "Process your inbox"
- Overdue > 10 → "High overdue count — consider a review"
- Stalled > 3 → "Several stalled projects need attention"
- Waiting aging > 20 → "Many aging Waiting items — review and drop or follow up"

When presenting overdue tasks, check `repetitionRule` field to identify repeating tasks:
- If `repetitionRule` is not null → task is repeating. Group separately as **Stale Routines**.
- For each stale routine, check `repetitionCatchUp` and `repetitionScheduleType`:
  - `repetitionCatchUp` is true → "Drop to reset (auto-catches up): `ofo drop <id>`"
  - `repetitionCatchUp` is false + >7 days overdue → "Toggle Catch Up ON in OmniFocus UI, then select Skip to reset"
  - `repetitionScheduleType` is "FromCompletion" + <=7 days → "Was this done? Complete if yes (`ofo complete <id>`), drop if skipped (`ofo drop <id>`)"
  - `repetitionScheduleType` is "Regularly" + <=7 days overdue → "Recently missed — complete if done, drop if skipped"
- Non-repeating overdue tasks: handle as before

If all counts are healthy, say: "System looks healthy."
