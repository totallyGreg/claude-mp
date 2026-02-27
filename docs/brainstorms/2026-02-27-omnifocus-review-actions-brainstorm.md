---
date: 2026-02-27
topic: omnifocus-review-actions
skill: omnifocus-manager
plugin: AITaskAnalyzer
---

# OmniFocus AITaskAnalyzer: Daily & Weekly Review Actions

## What We're Building

Two new Omni Automation actions added to the existing **AITaskAnalyzer** plugin bundle:

1. **`dailyReview`** — Morning/evening planning action that shows completed work from the last 24hrs alongside today's tasks, overdue items, and GTD-specific coaching prompts. Replaces the generic "Analyze My Tasks" for day-to-day use.

2. **`weeklyReview`** — Step-by-step guided GTD weekly review that walks the user through each GTD horizon using sequential Alert/Form dialogs, with Foundation Models providing coaching and insights at each step.

The goal is a self-sufficient OmniFocus plugin — no Claude required during daily use.

## Why This Approach

The existing `analyzeTasksWithAI` has four gaps:
- **No completed tasks** — can't see what was accomplished
- **Generic prompts** — insufficient GTD coaching depth
- **Context overflow** — large hierarchies produce incomplete analysis
- **Read-only results** — analysis shown but no ability to act

Approach B (two new actions, preserve existing) was chosen over retrofitting existing actions or redesigning the hub. It adds targeted functionality without breaking existing behavior.

## Key Decisions

- **Preserve existing actions**: `analyzeTasksWithAI`, `analyzeProjects`, `analyzeSelectedTasks`, `analyzeHierarchy` stay unchanged. New actions are additive.

- **Daily review = completed + upcoming + coaching**: Query completed tasks from last 24hrs using OmniFocus `completionDate` filter. Combine with today + overdue. Send to Foundation Models with richer GTD framing (energy level context, time horizon, project distribution).

- **Weekly review = step-by-step guided flow**: Sequential Alert/Form dialogs for each GTD review step:
  1. **Get Clear** — Inbox count + suggestions for processing
  2. **Project Sweep** — Projects with no next actions, stalled, on hold
  3. **Someday/Maybe** — Review deferred/on-hold items
  4. **Completed last week** — Celebrate/reflect on finished work
  5. **Horizon check** — Overdue + upcoming next week
  6. **Planning** — AI coaching on priorities for coming week

- **GTD prompt improvements**: New prompts use explicit GTD vocabulary — next actions, contexts, projects vs. areas, two-minute rule, weekly horizon. Foundation Models gets richer context (project count, completion rate, tag usage).

- **Better batching**: Improve `hierarchicalBatcher.js` context limits for the weekly review's project sweep step. Use the existing pattern of chunking at folder/project/task levels.

- **Generation via existing toolchain**: All new `.js` files generated through `generate_plugin.js --format bundle` following the existing skill workflow. No hand-writing plugin files.

## What's Out of Scope (For Now)

- **Action on results**: Deferring/flagging tasks from within the review screen — complex to implement in Omni Automation alerts, defer to a future version
- **Perspective creation**: Automated custom perspective generation — separate feature
- **Recurring project revision**: Helping revise the existing weekly review project in OmniFocus — separate feature, needs more design
- **GTD project reorganization coaching**: Re-naming/restructuring projects — separate feature

## Open Questions

- **Completed tasks API**: Does `taskMetrics.js` already expose `completionDate` filtering, or does `manage_omnifocus.js` need a new `--action completed-today` query? Check `references/database_schema.md`.
- **Foundation Models context limit**: What's the practical character limit for `respondWithSchema()` in a weekly review context? The `hierarchicalBatcher.js` currently targets ~20K chars per batch — is this still the right ceiling?
- **Weekly review step persistence**: If the user cancels mid-flow, is there a way to resume? Or is each run always fresh?
- **`completedTasksSummary` overlap**: There's already a `CompletedTasksSummary.omnifocusjs` plugin — how does it query completed tasks? Reuse that pattern.

## Implementation Notes for Planning Phase

Key files to examine/modify:
- `assets/AITaskAnalyzer.omnifocusjs/manifest.json` — add two new action declarations
- `assets/AITaskAnalyzer.omnifocusjs/Resources/taskMetrics.js` — extend with completed task query
- New files to generate: `dailyReview.js`, `weeklyReview.js`
- `references/gtd_guide.md` — use as prompt content source
- `scripts/generate_plugin.js` — use for generating new action files
- `assets/CompletedTasksSummary.omnifocusjs/` — study completed task query pattern

## Next Steps

→ Run `/workflows:plan` to design the implementation with file-level specifics
