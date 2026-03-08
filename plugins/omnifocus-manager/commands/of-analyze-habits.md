---
description: Analyze repeating task cadence to optimize defer intervals and due date settings
allowed-tools: Bash(osascript:*), Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/*)
---

<!--
/of:analyze-habits - Habit cadence analysis for repeating tasks.
Pulls all repeating tasks and their completion history, computes actual
vs intended gap days, and gives concrete defer/due recommendations.
-->

Today: !`date "+%A, %B %-d, %Y"`

Repeating task data (!`cd "${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager" && osascript -l JavaScript scripts/gtd-queries.js --action repeating-tasks --days 90`):

Using the data above, generate a Habit Cadence Analysis report.

## Report Structure

**# Habit Cadence Analysis — [today's date]**

**Summary line:** `Repeating tasks: N | On track: N | Adjust interval: N | Remove due date: N`

---

**Tasks by Recommendation**

Group tasks into three sections:

### On Track
Tasks where `gapRatio <= 1.2` (doing them close to the intended frequency).
Table: Task | Project | Intended | Actual Avg | Completions

### Adjust Interval (defer-after-completion)
Tasks where `gapRatio >= 1.5` — the user consistently waits longer than intended.
For each task show the suggested change:
Table: Task | Intended Gap | Actual Avg Gap | Suggested Defer | Rationale

For tasks with `hasDueDate: true` and `gapRatio >= 2.0`, call out: "Consider removing due date — this is a habit, not a deadline."

### Inconsistent / Review
Tasks with high `stdDev > avgGap` — wildly variable completion pattern.
Table: Task | Completions | Avg Gap | Std Dev | Suggestion

---

**Recommended Actions**

Numbered list of the 3-5 most impactful changes to make today:
- Specific task name
- Exactly what to change (e.g., "Change repeat to 'defer 3 days after completion', remove due date")
- Why (one sentence referencing actual data)

---

**GTD Note**

If more than 3 tasks have `hasDueDate: true` and `gapRatio >= 2.0`, add:
> Your system has several routine habits marked as due dates. Overdue habit tasks inflate your Overdue count and make real deadlines harder to see. Consider switching these to defer-after-completion with no due date.
