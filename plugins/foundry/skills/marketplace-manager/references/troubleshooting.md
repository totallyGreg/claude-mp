# Marketplace Manager - Troubleshooting Guide

This guide provides solutions to common issues when using marketplace-manager.

## Hook Issues

### Hook blocks: "changed since base but version X is not greater than X"

The commit changes a plugin (or a skill inside it) without raising its version relative to the merge-base with `origin/main`. Raise the version named in the message:
- Plugin: `plugins/<p>/.claude-plugin/plugin.json` `version`
- Skill: `plugins/<p>/skills/<s>/SKILL.md` `metadata.version`

Stage the bumped file and commit again. Preview with `python3 scripts/validate.py --check-versions`.

### Hook says "No base commit -- skipped version check"

There is no `origin/main` (or `origin/HEAD`) to compare against. Run `git fetch origin`, or pass `--base <ref>`.

### Hook reports "remove 'version' from its marketplace.json entry"

plugin.json is the only version source. Delete `version` from that entry.

### Outdated hook still syncs marketplace.json

Reinstall: `python3 scripts/setup.py install-hook` (and delete a leftover `scripts/sync.py`).

### Hook not executable

```bash
chmod +x .git/hooks/pre-commit
```

### Want to bypass hook temporarily

```bash
git commit --no-verify
```

### Hook blocking commits

- Check error message for specific issue
- Run validation: `python3 scripts/validate.py --check-versions`
- Fix reported issues, then commit again
- Or bypass with `--no-verify` if urgent

## Script Issues

### Cannot find skill

- Check skill name spelling
- Verify skill is in repository or installed
- Use full path if needed

### Plan already exists

- Check for existing planning branch
- Delete old branch or use different name
- Complete or abandon existing plan first

## Path Resolution Issues

- If auto-detection fails, use `--path` flag
- Use `--verbose` to debug path resolution
- Check for `.git` or `.claude-plugin` directories
- Ensure you're in repository when running scripts

## Version Issues

### Users don't receive an update

Claude Code updates a plugin only when its `plugin.json` version changes. If a change was merged without a bump (e.g. `--no-verify`), raise the version and push again.

## Structure Issues

### Pre-commit hook warns about shared version source

You will see a message like:
```
⚠️  Structural anti-patterns detected (advisory — commit will proceed):
  Plugins sharing a version source: airs-tme, pai-ops, prisma-airs
  Fix: Move each plugin into its own subdirectory...
```

This means multiple plugin entries in `marketplace.json` resolve to the same `plugin.json`, so they share one version. The commit is **not blocked** — this is advisory only.

**To fix:**
1. Create per-plugin subdirectories: `plugins/airs-tme/`, `plugins/pai-ops/`, etc.
2. Add `.claude-plugin/plugin.json` to each subdirectory
3. Move skills under each plugin directory
4. Update `marketplace.json` source paths: `"source": "./plugins/airs-tme"`

**To diagnose:**
```bash
python3 scripts/validate.py --check-structure
python3 scripts/validate.py --check-structure --format json  # JSON output
```

See `plugin_marketplace_guide.md` → "Multi-Plugin Repo" for the canonical layout.

### Version check reports wrong plugin for a version bump

This often indicates the shared-source anti-pattern: multiple plugins resolve to the same `plugin.json`. Run `validate.py --check-structure` to confirm.

## Validation Issues

### marketplace.json validation fails

Check for:
- Valid JSON syntax (use `python3 -m json.tool marketplace.json`)
- Required fields: `name`, `owner`, `plugins`
- Semantic versioning format for all version fields
- Skill paths exist and contain SKILL.md files
- No duplicate plugin names

### Skill validation fails

Ensure skill has:
- Valid SKILL.md file at root
- YAML frontmatter with `name` and `description`
- `metadata.version` or `version` field
- Semantic versioning format (X.Y.Z)
