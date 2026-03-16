---
description: Execute tasks from an OmniFocus AI Agent project step-by-step, marking each complete
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/*), Bash(osascript:*), Bash(mkdir:*), Bash(cat:*), Read, Write, Edit, Glob, Grep, Agent, AskUserQuestion
---

<!--
/ofo:work - Agent-driven task execution from an OmniFocus AI Agent project.
Queries for AI Agent-tagged projects, presents selection, reads tasks in order,
implements step-by-step, marks each complete in OmniFocus.
-->

## Step 1: Select a Project

If the user provided a project name as an argument, use that directly.

Otherwise, query OmniFocus for AI Agent-tagged projects:
```bash
cd "${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager" && osascript -l JavaScript scripts/gtd-queries.js --action ai-agent-tasks
```

Parse the output JSON. Present the list of projects with progress:
```
Found N AI Agent projects:
1. <project name> (<completed>/<total> complete)
2. <project name> (<completed>/<total> complete)
...

Which project would you like to work on?
```

Use AskUserQuestion to let the user select a project.

## Step 2: Load Project Tasks

Get full project details:
```bash
cd "${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager" && osascript -l JavaScript scripts/manage_omnifocus.js project-info --name "<selected project name>"
```

Parse the output. Identify:
- All subtasks (action groups and their children)
- Which tasks are incomplete (not completed)
- The project note (may contain a plan file path)

## Step 3: Load Plan Context (if available)

Check the project note for a plan file reference:
- Look for `Plan: <path>` in the project note
- If found, read that plan file for implementation context

Also check for a mapping file:
```bash
ls .claude/omnifocus-maps/*.json 2>/dev/null
```
If a mapping exists for this project, load it for ID-based task tracking.

If no mapping exists, create one from the project's current tasks:
```bash
mkdir -p .claude/omnifocus-maps
```
Write a mapping file using the project name and task IDs from project-info output.

## Step 4: Execute Tasks

For each **incomplete** task in order:

1. **Present the task**: Show the task name and any note content
2. **Implement**: Use the plan context and codebase to implement the task
3. **Verify**: Run relevant tests or checks to confirm the work is done
4. **Mark complete in OmniFocus**:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo complete "<task-id>"
   ```
5. **Ask to continue**: After each task, ask: "Task complete. Continue to next task?"

**Skip action group headers** — only execute leaf tasks (tasks without children).

**If a task is unclear:** Ask the user for clarification before implementing.

## Step 5: Report Progress

After all tasks are complete (or the user stops):
- Show summary: N/M tasks completed in this session
- Show remaining tasks (if any)
- Suggest next steps

If all tasks in the project are complete:
```
All tasks complete! Project "<name>" is finished.
```
