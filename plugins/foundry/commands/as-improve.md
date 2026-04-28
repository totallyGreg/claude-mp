---
name: as-improve
description: Guided agent improvement loop — evaluate, explain, fix, re-evaluate, update README, sync
argument-hint: [agent-path]
---

Run the full agentsmith improvement loop for an agent at `$ARGUMENTS`.

If no agent path provided, ask the user for it before proceeding.

## Step 0: Verify target is an agent

Check that `$ARGUMENTS` points to an agent file (`.md` with `<example>` blocks in description frontmatter) or a directory containing `AGENT.md`.

If target is a `SKILL.md` or skill directory:
```
/as-improve targets agents only. For skills → /ss-improve.
```

If target is a hook or command file:
```
/as-improve targets agents only. For hooks → plugin-dev:hook-development,
for commands → plugin-dev:command-development.
```

## Step 0a: Remap installed-cache paths to source

Resolve `$ARGUMENTS` to a real absolute path, following any symlinks (`realpath` or Python `Path.resolve()`).

Check whether the resolved path starts with `$HOME/.claude/plugins/`. If it does not, skip the rest of this step and continue with the resolved path.

If it does start with `$HOME/.claude/plugins/`:

1. Determine the agent name from the path. For flat agents: the filename without `.md`. For directory agents: the directory name containing `AGENT.md`.
2. Read the repo's `.claude-plugin/marketplace.json`. For each plugin entry with a local `source` field: check whether an agent file exists at `<source>/agents/<agent-name>.md` or `<source>/agents/<agent-name>/AGENT.md`.
3. If **exactly one** match is found:
   - Notify the user: `Path remapped from installed cache to source: <matched-path>`
   - Set the effective path and continue
4. If **zero** or **multiple** matches:
   - Abort with: `The path points to the installed cache — no unique source found in marketplace.json. Pass the source repo path manually.`

After this step, all subsequent steps use the remapped source path.

## Step 1: Evaluate current state

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/agentsmith/scripts/evaluate_agent.py $ARGUMENTS --explain
```

Report scores and the top-3 quality improvements identified.

## Step 1b: Evaluate sibling skills (if any)

Find the plugin root by walking up from the agent path to find `.claude-plugin/plugin.json`. If the plugin has a `skills/` directory with SKILL.md files, run skillsmith evaluation on each:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/evaluate_skill.py <each-skill-path>
```

Report a holistic plugin quality summary alongside agent scores.

## Step 2: Apply improvements

Work through the top-3 improvements from `--explain` output. For structural guidance on agent anatomy, invoke `plugin-dev:agent-development`.

## Step 3: Re-evaluate

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/agentsmith/scripts/evaluate_agent.py $ARGUMENTS
```

Compare against baseline scores. If overall score regressed, fix before proceeding. The baseline is stored in `.agentsmith-baselines.json` in the plugin's source directory.

## Step 4: Update README

Generate the version history row for the new version:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/agentsmith/scripts/evaluate_agent.py $ARGUMENTS --export-table-row --version X.Y.Z
```

Paste the row into the plugin's README.md Version History section (newest first).

## Step 5: Version bump

Agents don't carry their own version — they are part of the plugin release unit. Bump `plugin.json` version only:

Determine bump type:
- **PATCH**: Bug fixes, minor wording updates
- **MINOR**: New capabilities, improved scoring
- **MAJOR**: Breaking changes

Update `"version"` in the plugin's `.claude-plugin/plugin.json`.

## Step 6: Sync marketplace

Sync `marketplace.json` with the updated plugin version:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/repo/sync.py .claude-plugin/marketplace.json
```
