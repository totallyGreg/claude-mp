---
description: Sweep all projects for stalled work, overdue accumulation, and near-duplicates
argument-hint: [neglected-threshold-days]
allowed-tools: Bash(osascript:*), Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core/scripts/*)
---

<!--
/ofo:analyze-projects - Project health sweep.
Detects stalled projects, neglected projects, overdue task accumulation,
and near-duplicate project names that may represent fragmented capture.
-->

Today: !`date "+%A, %B %-d, %Y"`

Project analysis data (!`cd "${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core" && osascript -l JavaScript scripts/gtd-queries.js --action analyze-projects --threshold ${1:-30}`):

Using the data above, generate a Project Health Report.

## Report Structure

**# Project Health Report — [today's date]**

**Summary line:** `Projects: N | Stalled: N | Neglected: N | Overdue accumulation: N | Possible duplicates: N`

---

**Stalled Projects** (no next action defined)

Table: Project | Folder | Next Step Decision
For each stalled project, suggest one of:
- Add a next action (and suggest what it might be based on the project name)
- Put on hold (if waiting for something external)
- Drop (if no longer relevant)

---

**Neglected Projects** (not touched in 30+ days)

Table: Project | Folder | Days Since Activity | Suggestion
Flag projects neglected > 90 days separately as candidates for "Someday/Maybe".

---

**Overdue Task Accumulation** (5+ overdue tasks)

Table: Project | Folder | Overdue Count | Recommended Action
For heavy accumulation (10+), suggest a "project sweep" — review each task and either complete, defer, or drop.

---

**Possible Duplicate Projects**

For each pair flagged as `POSSIBLE_DUPLICATE` or `LIKELY_DUPLICATE`:
- Show both project names side by side
- Note confidence level
- Suggest: Merge (if same scope), Archive one (if one is superseded), or Rename to clarify distinction

---

**Recommended Actions**

Numbered list of 5-7 specific actions in priority order:
1. Address LIKELY_DUPLICATE pairs first (prevents further fragmented capture)
2. Add next actions to top-N stalled projects
3. Sweep overdue-heavy projects
4. Archive/hold projects neglected > 90 days
