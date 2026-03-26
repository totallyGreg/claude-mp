# Marketplace Manager - Troubleshooting Guide

This guide provides solutions to common issues when using marketplace-manager.

## Hook Issues

### Hook not syncing marketplace.json

**Reinstall the hook:**
```bash
python3 scripts/setup.py install-hook
```

### Hook shows version mismatch warning

This means the installed hook is outdated:
- Run: `python3 scripts/setup.py install-hook`
- Hook will be updated to use the latest repo-local scripts

### Hook not found errors

The hook uses dynamic path discovery:
- If scripts are moved/renamed, hook will find them automatically
- First checks specific path, then searches entire repository

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
- Run sync manually: `python3 scripts/sync.py`
- Run validation: `python3 scripts/validate.py`
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

## Version Sync Issues

### Versions not updating in marketplace.json

Check that:
1. Skill uses `metadata.version` in SKILL.md frontmatter
2. Version follows semantic versioning (X.Y.Z)
3. marketplace.json is writable
4. Run with `--verbose` to see what's detected

### Script reports "no changes needed" but versions are mismatched

This can happen with manual mode:
- Manual mode only warns, doesn't auto-update plugin version
- You must manually update the plugin version in marketplace.json
- See "Multi-Component Plugin Versioning" in main SKILL.md

## Structure Issues

### Pre-commit hook warns about shared version source

You will see a message like:
```
⚠️  Structural anti-patterns detected (advisory — commit will proceed):
  Plugins sharing a version source: airs-tme, pai-ops, prisma-airs
  Fix: Move each plugin into its own subdirectory...
```

This means multiple plugin entries in `marketplace.json` resolve to the same `plugin.json`, which causes incorrect version enforcement. The commit is **not blocked** — this is advisory only.

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
