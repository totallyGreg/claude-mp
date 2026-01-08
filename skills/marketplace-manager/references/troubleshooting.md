# Marketplace Manager - Troubleshooting Guide

This guide provides solutions to common issues when using marketplace-manager.

## Hook Issues

### Hook not syncing marketplace.json

**Check hook status:**
```bash
python3 skills/marketplace-manager/scripts/validate_hook.py

# Reinstall if needed
bash skills/marketplace-manager/scripts/install_hook.sh --force
```

### Hook shows version mismatch warning

This means the installed hook is outdated:
- Run: `bash skills/marketplace-manager/scripts/install_hook.sh`
- Hook will auto-update to latest version

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
- Run sync manually: `python3 skills/marketplace-manager/scripts/sync_marketplace_versions.py`
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

## Validation Issues

### marketplace.json validation fails

Check for:
- Valid JSON syntax (use `python3 -m json.tool marketplace.json`)
- Required fields: `name`, `version`, `description`, `owner`, `plugins`
- Semantic versioning format for all version fields
- Skill paths exist and contain SKILL.md files
- No duplicate plugin names

### Skill validation fails

Ensure skill has:
- Valid SKILL.md file at root
- YAML frontmatter with `name` and `description`
- `metadata.version` or `version` field
- Semantic versioning format (X.Y.Z)
