---
name: ss-refresh
description: Detect stale references and guide updates for any skill with provenance-tracked references
argument-hint: [skill-path]
allowed_tools: Bash, Read, Edit, Write, Glob, Grep, Agent, AskUserQuestion
---

Run the reference freshness checker and guide updates for a skill at `$ARGUMENTS`.

If no skill path provided, ask the user for it before proceeding.

## Step 1: Verify target is a skill

Check that `$ARGUMENTS` points to a directory containing `SKILL.md`. If not found, inform the user and stop.

## Step 1a: Remap installed-cache paths to source

Resolve `$ARGUMENTS` to a real absolute path, following any symlinks (`realpath` or Python `Path.resolve()`).

Check whether the resolved path starts with `$HOME/.claude/plugins/`. If it does, remap to source using `marketplace.json` (same logic as `/ss-improve` Step 0a).

## Step 2: Choose mode

Ask the user which mode to run:
- **Incremental** (default): Only detect activity newer than `last_verified`
- **Full audit**: Show all source activity — use for initial catchups or thorough reviews

## Step 3: Run the freshness report

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/check_freshness.py \
  "$SKILL_PATH" --probe --verbose
```

For full audit mode, add `--full-audit`.

Present the output to the user. If no gaps or stale references are found, report that and stop.

## Step 4: Identify what changed

If gaps are detected (references with upstream activity or staleness), summarize:
- Which references are stale and by how many days
- Which sources have new commits, messages, or version drift
- Which references need updating

Ask the user: **"Update these references? This will modify reference files and bump the version."**

If the user declines, stop.

## Step 5: Research upstream sources

For each reference that needs updating, read the upstream source content using the source metadata from the reference's YAML frontmatter:

- **`web`**: Fetch via `defuddle parse --md <url>` or `WebFetch`
- **`github`**: Read files via `gh api repos/{repo}/contents/{path}`
- **`gitlab`**: Read files via `glab api projects/{id}/repository/files/{path}/raw?ref=main`
- **`slack`**: Fetch recent messages from the channel via Slack API
- **`plugin`**: Read the upstream plugin's SKILL.md, README.md, or CHANGELOG.md

Focus on:
- New features, endpoints, or capabilities
- Changed schemas, types, or data structures
- Deprecated or removed functionality

## Step 6: Update references

Edit each affected reference file:
1. Incorporate new information from the upstream source
2. Update `last_verified` date to today in the YAML frontmatter
3. Keep existing content intact — only add or modify what changed
4. Maintain the existing style and structure of each reference

**Do NOT:**
- Rewrite entire files — surgical updates only
- Add marketing language — use engineering details
- Remove existing content unless confirmed wrong
- Change the file's overall organization

## Step 7: Update SKILL.md if needed

If new capabilities were added (e.g., new CLI commands, new features), update the SKILL.md to mention them. Keep it concise — details go in references.

## Step 8: Evaluate

Run the skillsmith evaluator to confirm no score regression:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/evaluate_skill.py "$SKILL_PATH"
```

If the foundry plugin's PostToolUse hook is active, it auto-evaluates on SKILL.md edits. If score dropped, fix before proceeding.

## Step 9: Version bump

Determine the version bump:
- **PATCH** (x.y.Z): Only reference content updates, no new capabilities
- **MINOR** (x.Y.0): New capabilities documented, backward-compatible

Update version in:
- `SKILL.md` frontmatter (`metadata.version`)
- Plugin's `.claude-plugin/plugin.json`

Run `--update-readme` and `--export-table-row --version <NEW_VERSION>` to update the plugin-level README.md metrics.

## Step 10: Commit (optional)

Ask the user if they want to commit and push:
1. Stage ONLY the changed files (never `git add .`)
2. Commit with message: `feat(<plugin>): v<VERSION> — refresh references from upstream sources`
3. Optionally push and create branch/PR
