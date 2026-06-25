---
name: ss-wtf
description: File a friction report or list accumulated friction
argument-hint: list | show | <description-or-summary-line>
---

File a friction report about dev-experience pain, or review accumulated reports.

## Step 0: Parse arguments

`$ARGUMENTS` may be:

- The literal token **`list`** or **`show`** as the first non-empty word → dispatch to **Listing Reports** below.
- Anything else → treat **the entire `$ARGUMENTS`** (multi-line OK) as the friction **description** and dispatch to **Filing a Report** below. The first line should ideally be a one-line summary; any additional lines are appended to the description body.
- **Empty** → prompt the user interactively (see below).

**MODE** = `list` if the first non-empty word (case-insensitive) is `list` or `show`; otherwise `file`. Never split fields out of structured YAML-ish input — pass the whole blob to `--description`. (If you have structured fields to set, call `submit-issue.sh` directly with explicit flags.)

## Filing a Report

If MODE is `file`:

1. **Gather context** from the current conversation (you decide these, do not parse them out of `$ARGUMENTS`):
   - **Type**: `skill`, `agent`, `tool`, or `workflow` — infer from what was active when friction occurred
   - **Name**: plugin-qualified name (e.g., `foundry:skillsmith`, `archivist:archivist`)
   - **Category**: one of `bad-docs`, `broken-tool`, `misleading-skill`, `missing-prereq`, `auth-failure`, `flaky`, `other`
   - **Project**: current working directory (defaults to `$(pwd)` if omitted)
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

If MODE is `list`:

```bash
reports_dir="$HOME/.claude/agent-issues/reports"

if [[ -d "$reports_dir" ]] && ls "$reports_dir"/*.md >/dev/null 2>&1; then
  for f in "$reports_dir"/*.md; do
    # Parse YAML frontmatter for date, type, name, category, project
    # and the description body. Render as a row in the summary table.
    :
  done
else
  echo "No friction reports found."
fi
```

Present reports as a markdown table:

| Date | Type | Name | Category | Project | Description |
|------|------|------|----------|---------|-------------|

The reports live in the per-user global store (`~/.claude/agent-issues/reports/`), so this list shows friction filed from any repo — the `Project` column records where each was hit.

If no reports exist, say "No friction reports found. Use `/ss-wtf <description>` to file one."
