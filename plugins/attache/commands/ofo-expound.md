---
description: Clarify a task or project name and apply consistent duration/effort tags
argument-hint: [task-or-project-name]
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core/scripts/*), AskUserQuestion
---

<!--
/ofo:expound - Expound on a task or project.
Fetches current name, note, tags, and duration estimate. Suggests a clearer
action-oriented name, verifies effort/duration tags, and applies confirmed
changes via the ofo CLI.
-->

Today: !`date "+%A, %B %-d, %Y"`

## Step 1: Identify the Target

If `$ARGUMENTS` is provided, use it as the search term directly.

Otherwise ask with AskUserQuestion: "Which task or project would you like to expound on? Provide the name (or part of it)."

Search for it:
```bash
"${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core/scripts/ofo" search "$ARGUMENTS"
```

If multiple matches, show them and ask which one using AskUserQuestion.

## Step 2: Fetch Full Details

```bash
"${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core/scripts/ofo" info "<task-id>"
```

Collect: id, name, note, tags, estimatedMinutes, deferDate, dueDate, project, flagged.

## Step 3: Analyze and Suggest

Using the task details, suggest improvements in three areas:

### Name Clarity
A well-formed GTD next action starts with a verb and is specific enough to know exactly what to do without thinking:
- Current: `<current name>`
- Suggested: `<improved name>`
- Rationale: one sentence explaining the change

If the current name is already clear and action-oriented, say so and skip this.

### Duration Tag
Review existing tags for duration markers (e.g., `15min`, `30min`, `1hr`, `2hr+`).
If missing or inconsistent with the task scope:
- Suggested tag: `<tag>` (based on task name and estimated minutes if set)
- Available tags to apply (fetch from: `"${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core/scripts/ofo" tags`)

### Effort Tag
Review existing tags for effort/energy markers (e.g., `@focus`, `@admin`, `@errand`, `@phone`).
If missing:
- Suggested tag: `<tag>`

## Step 4: Confirm Changes

Present the proposed changes to the user with AskUserQuestion:

```
Proposed changes to: "<current name>"

1. Rename to: "<suggested name>"  [y/n/edit]
2. Add tag: "<duration tag>"      [y/n]
3. Add tag: "<effort tag>"        [y/n]

Apply all confirmed changes?
```

Accept individual y/n responses or "all" / "none".

## Step 5: Apply Confirmed Changes

For each confirmed change, apply via ofo CLI:

**Rename:**
```bash
"${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core/scripts/ofo" update "<id>" --name "<new name>"
```

**Add tag:**
```bash
"${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core/scripts/ofo" tag "<id>" --add "<tag>"
```

## Step 6: Report Results

Show a summary:
- Task: `<final name>`
- Tags applied: `<list>`
- OmniFocus updated: yes/no

If the user declined all changes: "No changes made. The task looks good as-is."
