---
description: Full GTD weekly review — saves report to clipboard and OmniFocus note
allowed-tools: Bash(osascript:*), Bash(pbcopy:*), Write
---

<!--
Weekly Review command.
- All OmniFocus data collected in parallel at invocation (5 queries → 1 wait)
- Single analysis pass generates the complete report
- Report saved to clipboard and appended to OmniFocus Weekly Review task note
-->

Today: !`date "+%A, %B %-d, %Y"`

OmniFocus data (5 queries run in parallel):
!`bash "${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/weekly-review-collect.sh"`

Using ALL data above in a single analysis pass, generate a complete GTD Weekly Review report in markdown.

## Report Structure

**# Weekly Review — [today's date]**

**System Health (one line):** `Inbox: N | Overdue: N | Stalled: N | Waiting: N (N aging >30d)`

---

**GET CLEAR — Inbox (N items)**
Table: Item | GTD Decision | Notes
Apply clarify decision tree to each: actionable? → Next Action / Project / Someday / Reference / Trash

**GET CURRENT — Overdue (N tasks)**
Group by: Routine Decay | Work | Financial | Health | Personal
Table: Task | Project | Days Overdue | Recommended Action
Flag ghost recurrences (same name, multiple instances) with 🔁 and recommend batch-complete.

**GET CURRENT — Stalled Projects (N)**
Table: Project | Decision Needed

**GET CURRENT — Waiting For (N total, N aging)**
Urgent/flagged items first, then aging items (>30d) grouped by theme: Work | Homelab | Personal | Financial.
Table: Item | Blocker | Days Waiting | Decision (Follow Up / Drop / Activate)

**Accomplishments This Week**
Meaningful completions only — exclude routine recurrences (Begin the day, etc.)
Group by: Work | Personal | Financial

**Recommended Actions**
Numbered list of 5–7 specific, immediately actionable next steps for today/this week.

---

## Save Report

After generating the report:

1. Write the complete markdown to `/tmp/of-weekly-review.md` using the Write tool.

2. Copy to clipboard:
   `pbcopy < /tmp/of-weekly-review.md`

3. Append to OmniFocus Weekly Review task note:
   `osascript -l JavaScript "${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/update-weekly-note.js" "/tmp/of-weekly-review.md"`

4. Report status to the user:
   - ✅ Report generated
   - ✅/❌ Saved to clipboard
   - ✅/❌ OmniFocus note updated (show task name on success, error details on failure)
   Then display the full report.
