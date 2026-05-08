---
name: ss-wtf
description: File a friction report or list accumulated friction
argument-hint: [description | list | show]
---

File a friction report about dev-experience pain, or review accumulated reports.

## Input

`$ARGUMENTS` may be:

- **Description** — a one-line summary of the friction (e.g., "the archivist skill didn't handle empty vaults")
- **"list" or "show"** — display accumulated friction reports
- **Empty** — prompt for friction details interactively

## Filing a Report

If `$ARGUMENTS` is a description (not "list" or "show"):

1. **Gather context** from the current conversation:
   - **Type**: `skill`, `agent`, `tool`, or `workflow` — infer from what was active when friction occurred
   - **Name**: plugin-qualified name (e.g., `foundry:skillsmith`, `archivist:archivist`)
   - **Category**: one of `bad-docs`, `broken-tool`, `misleading-skill`, `missing-prereq`, `auth-failure`, `flaky`, `other`
   - **Project**: current working directory
   - **Session**: current session ID (if available)

2. **File the report**:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/wtf/scripts/submit-issue.sh \
  --type <type> \
  --name "<name>" \
  --category <category> \
  --description "$ARGUMENTS" \
  --project "$(pwd)" \
  --session "<session-id>"
```

3. **Confirm** what was filed (directory path, filename) and continue.

If `$ARGUMENTS` is empty, ask the user:
- What went wrong?
- Which skill/agent/tool was involved?
Then file the report with the gathered details.

## Listing Reports

If `$ARGUMENTS` is "list" or "show":

```bash
repo_root=$(git rev-parse --show-toplevel)
reports_dir="$repo_root/.local/agent-issues/reports"

if [[ -d "$reports_dir" ]] && ls "$reports_dir"/*.md >/dev/null 2>&1; then
  # Read and summarize each report
  for f in "$reports_dir"/*.md; do
    # Parse YAML frontmatter for type, name, category, date
    # Display as a summary table
  done
else
  echo "No friction reports found."
fi
```

Present reports as a markdown table:

| Date | Type | Name | Category | Description |
|------|------|------|----------|-------------|

If no reports exist, say "No friction reports found. Use `/ss-wtf <description>` to file one."
