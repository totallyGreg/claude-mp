---
description: Show OmniFocus system health — inbox, overdue, stalled, and waiting counts
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core/scripts/*)
---

<!--
/ofo:health - Quick GTD system health check.
Single ofo health call avoids pasteboard collisions from multiple sequential ofo calls.
-->

System health data:
!`${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core/scripts/ofo health`

Present the health data as:

**System Health:** `Inbox: N | Overdue: N | Flagged: N`

Use the `count` fields from `inbox`, `overdue`, and `flagged` in the JSON response.

Then flag any counts that need attention:
- Inbox > 0 → "Process your inbox"
- Overdue > 10 → "High overdue count — consider a review"

When presenting overdue tasks, check `repetitionRule` field to identify repeating tasks:
- If `repetitionRule` is not null → task is repeating. Group separately as **Stale Routines**.
- For each stale routine, apply the canonical decision tree (matches `/ofo:overdue` and the `staleRoutineRecovery` Attache action):
  - `repetitionCatchUp` is true → "Drop to reset (Catch Up auto-advances cadence): `ofo drop <id>`"
  - `repetitionScheduleType` is "FromCompletion" → "Was this done? Complete if yes (`ofo complete <id>`), drop if skipped (`ofo drop <id>`)"
  - `repetitionScheduleType` is "Regularly" + >7 days overdue → "Drop to move forward: `ofo drop <id>`"
  - `repetitionScheduleType` is "Regularly" + ≤7 days overdue → "Recently missed — complete if done (`ofo complete <id>`), drop if skipped (`ofo drop <id>`)"
- If the user wants to preserve the recurrence WITHOUT dropping (skip-and-resume), note that toggling `repetitionCatchUp` is not exposed by Omni Automation today. Point them at **Attache › Recover Stale Routines** for a per-task walkthrough that includes the manual Catch Up UI steps with a Copy Steps button.
- Non-repeating overdue tasks: handle as before

If all counts are healthy, say: "System looks healthy."
