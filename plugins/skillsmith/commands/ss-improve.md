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
/ss-improve targets skills only. For agents → plugin-dev:agent-development,
for hooks → plugin-dev:hook-development, for commands → plugin-dev:command-development.
```

## Step 0b: Auto-migrate IMPROVEMENT_PLAN.md (if present)

If the skill directory contains `IMPROVEMENT_PLAN.md` and no `README.md`, migrate automatically:
1. Generate README.md prose and Capabilities sections (describe the skill's purpose)
2. Copy version history rows from IMPROVEMENT_PLAN.md into README.md Version History table (add `Desc` column with `-` for historical rows)
3. Run `uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/evaluate_skill.py $ARGUMENTS --update-readme` to populate Current Metrics
4. Delete IMPROVEMENT_PLAN.md

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

Update `metadata.version` in the skill's `SKILL.md` frontmatter and the plugin's `plugin.json`.

## Step 6: Sync marketplace

Invoke `marketplace-manager` to sync `marketplace.json` with the new version.
