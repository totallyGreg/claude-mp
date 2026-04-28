---
name: ss-improve
description: Guided skill improvement loop — evaluate, explain, fix, re-evaluate, update README, sync
argument-hint: [skill-path]
---

Run the full skillsmith improvement loop for a skill at `$ARGUMENTS`.

If no skill path provided, ask the user for it before proceeding.

## Step 0: Verify target is a skill

Check that `$ARGUMENTS` points to a directory containing `SKILL.md`. If not found, output:

```
/ss-improve targets skills only. For agents → /as-improve,
for hooks → plugin-dev:hook-development, for commands → plugin-dev:command-development.
```

## Step 0a: Remap installed-cache paths to source

Resolve `$ARGUMENTS` to a real absolute path, following any symlinks (`realpath` or Python `Path.resolve()` — not `abspath()`).

Check whether the resolved path starts with `$HOME/.claude/plugins/`. If it does not, skip the rest of this step and continue with the resolved path.

If it does start with `$HOME/.claude/plugins/`:

1. Extract the **skill name** from the resolved path: it is the final path component (the leaf directory name). For example, from `~/.claude/plugins/marketplaces/totally-tools/plugins/foundry/skills/skillsmith/` the skill name is `skillsmith`.
2. Read the repo's `.claude-plugin/marketplace.json`. For each plugin entry that has a local `source` field: check whether the file `<source>/skills/<skill-name>/SKILL.md` exists on disk. Collect all matching entries.
3. If **exactly one** match is found:
   - Notify the user: `Path remapped from installed cache to source: <source>/skills/<skill-name>/`
   - Set the effective path to `<source>/skills/<skill-name>/` and continue
4. If **zero** matches (third-party plugin not in this repo) or **multiple** matches (ambiguous):
   - Abort with: `The path points to the installed cache — no unique source found in marketplace.json. Pass the source repo path manually.`

After this step, all subsequent steps use the remapped source path.

## Step 0b: Auto-migrate IMPROVEMENT_PLAN.md (if present)

If the skill directory contains `IMPROVEMENT_PLAN.md` and no `README.md`, migrate automatically:
1. Generate README.md prose and Capabilities sections (describe the skill's purpose)
2. Copy version history rows from IMPROVEMENT_PLAN.md into README.md Version History table (add `Desc` column with `-` for historical rows)
3. Run `uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/evaluate_skill.py $ARGUMENTS --update-readme` to populate Current Metrics
4. Delete IMPROVEMENT_PLAN.md

## Step 0c: Auto-patch missing recommended frontmatter

Run:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/evaluate_skill.py $ARGUMENTS --explain
```

If the output identifies missing recommended frontmatter fields (`license`, `compatibility`), patch them automatically before continuing:

1. Apply sensible defaults — do NOT silently apply wrong values:
   - `license: MIT` — confirm with the user if a different license file exists
   - `compatibility: claude-code` — if the skill has Python scripts in `scripts/`, append `, Requires uv for Python script execution`
2. Patch the `SKILL.md` frontmatter using the Edit tool
3. Note the expected score delta (+3–6 pts per missing field pair) to document in Step 4

## Step 1: Evaluate current state

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/evaluate_skill.py $ARGUMENTS --explain
```

Report scores and the top-3 improvements identified.

## Step 2: Apply improvements

Work through the top-3 improvements from `--explain` output. For structural guidance (skill anatomy, writing style), invoke `plugin-dev:skill-development`.

## Step 3: Re-evaluate

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/evaluate_skill.py $ARGUMENTS
```

Confirm scores improved. If any score regressed, fix before proceeding.

## Step 4: Update README

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/evaluate_skill.py $ARGUMENTS --update-readme
```

Then generate the version history row for the new version:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/evaluate_skill.py $ARGUMENTS --export-table-row --version X.Y.Z
```

Paste the row into README.md Version History (newest first).

## Step 5: Version bump

Determine bump type:
- **PATCH**: Bug fixes, docs, minor wording updates
- **MINOR**: New capabilities, backward-compatible improvements
- **MAJOR**: Breaking changes (remove flags, change output format)

**Pre-flight**: Before writing any version changes, verify that `../../.claude-plugin/plugin.json` exists relative to the skill directory (e.g., for a skill at `plugins/foundry/skills/skillsmith/`, the file is `plugins/foundry/.claude-plugin/plugin.json`). If the file is not found at that path, abort Step 5 with an advisory — do not modify SKILL.md until the file is confirmed present.

Then update both files:
1. Update `metadata.version` in the skill's `SKILL.md` frontmatter
2. Update `"version"` in `../../.claude-plugin/plugin.json` — where `../../` is relative to the skill directory

Verify both files show the same version string before proceeding to Step 6. (`scripts/sync.py` reads `plugin.json` first — if it is not updated, `marketplace.json` will not reflect the new version.)

## Step 6: Sync marketplace

Sync `marketplace.json` with the updated plugin version:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/repo/sync.py .claude-plugin/marketplace.json
```
