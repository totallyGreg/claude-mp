---
description: Publish a plan to OmniFocus as a project with phased action groups tagged AI Agent
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/*), Bash(osascript:*), Bash(gh issue create:*), Bash(gh issue view:*), Bash(mkdir:*), Bash(cat:*), Read, Write, AskUserQuestion
---

<!--
/of:plan - Publish a plan document to OmniFocus and/or GitHub Issues.
Reads a plan markdown file, extracts phases and tasks, creates an OmniFocus
project with action groups tagged AI Agent / Claude Code.
-->

## Step 1: Find the Plan

If the user provided a plan file path as an argument, read that file.

Otherwise, find the most recent plan:
```bash
ls -t docs/plans/*.md 2>/dev/null | head -5
```

Present the list and ask which plan to publish. Read the selected plan file.

## Step 2: Choose Destination

Ask the user where to publish using the AskUserQuestion tool:

**Options:**
1. **OmniFocus Project** — Create project with phased action groups in OmniFocus
2. **GitHub Issue** — Create a GitHub issue with task checklist
3. **Both** — Create OmniFocus project AND GitHub issue, linked together
4. **Skip** — Do nothing

## Step 3: Parse the Plan

Read the plan markdown and extract:
- **Title**: From YAML frontmatter `title:` field, or the first H1 heading
- **Phases**: H2 or H3 headings containing "Phase" or "Step" (e.g., "### Phase 1: Setup")
- **Tasks**: Checkbox items (`- [ ]`) under each phase heading
- **Note**: The plan file path and any issue URL

Build a JSON structure:
```json
{
  "project": "<title from frontmatter>",
  "note": "Plan: <plan-file-path>\nPublished: <today's date>",
  "tags": ["AI Agent", "Claude Code"],
  "sequential": false,
  "groups": [
    {
      "name": "<phase heading>",
      "sequential": true,
      "tasks": [
        { "name": "<task text without checkbox>" }
      ]
    }
  ]
}
```

**If the plan has no checkbox items:** Warn the user. Create a single task with the plan title.

**If the plan has tasks but no phase headings:** Put all tasks in a single group named "Tasks".

## Step 4: Create in OmniFocus (if selected)

Write the JSON structure to a temporary file:
```bash
cat > /tmp/of-plan-bulk-create.json << 'JSONEOF'
<the JSON structure>
JSONEOF
```

Then create the project:
```bash
cd "${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager" && osascript -l JavaScript scripts/manage_omnifocus.js bulk-create --json-file /tmp/of-plan-bulk-create.json
```

Parse the output JSON to get the `taskMapping` (task names → OmniFocus IDs).

## Step 5: Save Mapping File

Create the mapping directory and write the mapping file:
```bash
mkdir -p .claude/omnifocus-maps
```

Write the mapping file using the Write tool to `.claude/omnifocus-maps/<plan-filename>.json`:
```json
{
  "project_id": "<from bulk-create output>",
  "project_name": "<project name>",
  "plan_path": "<original plan file path>",
  "tasks": {
    "<task name>": "<omnifocus-task-id>",
    ...
  }
}
```

Also ensure `.claude/omnifocus-maps/` is in `.gitignore`:
```bash
grep -q 'omnifocus-maps' .gitignore 2>/dev/null || echo '.claude/omnifocus-maps/' >> .gitignore
```

## Step 6: Create GitHub Issue (if selected)

```bash
gh issue create --title "<plan title>" --label "plugin:omnifocus-manager" --body "$(cat <<'EOF'
## Summary

<first paragraph from plan overview>

## Tasks

<checkbox items from plan>

## Plan

See [<plan-filename>](<plan-path>)
EOF
)"
```

If "Both" was selected, update the OmniFocus project note with the issue URL:
```bash
cd "${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager" && osascript -l JavaScript scripts/manage_omnifocus.js project-update --id "<project-id>" --note-append "Issue: <issue-url>"
```

## Step 7: Report Results

Report what was created:
- OmniFocus project name, task count, and tag structure
- GitHub issue URL (if created)
- Mapping file location
- Remind user they can use `/of:work` to execute tasks from the OmniFocus project
