---
name: marketplace-manager
description: Manages Claude Code plugin marketplace operations including version syncing, skill publishing, and marketplace.json maintenance. Use when adding skills to marketplace, updating skill versions, syncing marketplace.json, or managing plugin distributions. Triggers when user mentions marketplace, version sync, or plugin publishing.
metadata:
  version: "1.0.0"
compatibility: Requires git repository with .claude-plugin/marketplace.json
---

# Marketplace Manager

Manages Claude Code plugin marketplace operations with automatic version detection and syncing.

## About Marketplaces

A Claude Code plugin marketplace enables easy skill distribution and installation. Users can install skills using:

```bash
/plugin marketplace add username/repository
/plugin install plugin-name@marketplace-name
```

## When to Use

Use marketplace-manager when:
- Adding new skills to marketplace.json
- Updating skill versions in marketplace
- Syncing versions between SKILL.md and marketplace.json
- Detecting version mismatches
- Managing plugin metadata
- Validating marketplace structure

## Core Functionality

### Automatic Version Detection

marketplace-manager automatically detects when skill versions change and prompts to sync marketplace.json.

**Detection triggers:**
- After skill edits when metadata.version or version field changes
- Before git commits (via pre-commit hook)
- When explicitly checking sync status

### Version Syncing

Keeps marketplace.json versions synchronized with skill SKILL.md frontmatter:

```bash
# Sync all skill versions to marketplace
python3 scripts/sync_marketplace_versions.py

# Preview changes without saving
python3 scripts/sync_marketplace_versions.py --dry-run
```

**Sync process:**
1. Scans all skills in marketplace.json
2. Reads version from each skill's SKILL.md frontmatter
3. Compares with marketplace.json plugin version
4. Updates marketplace.json if mismatch detected
5. Reports all changes made

**Version field priority:**
- First checks `metadata.version` (Agent Skills spec)
- Falls back to `version` (deprecated but supported)
- Reports warning if using deprecated field

### Adding Skills to Marketplace

Use the add_to_marketplace.py script to add skills:

```bash
# List current marketplace contents
python3 scripts/add_to_marketplace.py list

# Add skill to existing plugin
python3 scripts/add_to_marketplace.py add-skill <skill-path> --plugin <plugin-name>

# Create new plugin with skill
python3 scripts/add_to_marketplace.py create-plugin <plugin-name> --skill <skill-path>
```

**Script features:**
- Auto-detects repository root (works from any directory)
- Validates skill structure before adding
- Updates marketplace.json atomically
- Supports verbose output for debugging

### Marketplace Structure

The marketplace.json defines marketplace metadata and plugins:

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "my-marketplace",
  "version": "2.0.0",
  "description": "Marketplace description",
  "owner": {
    "name": "Your Name",
    "email": "email@example.com"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "description": "Plugin description",
      "category": "development",
      "version": "1.0.0",
      "author": {
        "name": "Your Name",
        "email": "email@example.com"
      },
      "source": "./",
      "skills": ["./skills/skill-one", "./skills/skill-two"]
    }
  ]
}
```

**Key principles:**
- Plugin versions should match skill versions
- Use sync script to maintain synchronization
- Each plugin can contain multiple related skills
- Skills are referenced by relative paths

## Git Integration

### Pre-Commit Hook

Auto-sync marketplace.json before commits:

```bash
# Install pre-commit hook
cp scripts/pre-commit.template .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Hook behavior:**
- Detects version mismatches before commit
- Automatically updates marketplace.json
- Adds marketplace.json to commit
- Prevents commit if sync fails
- Can be bypassed with `git commit --no-verify`

### Workflow Integration

marketplace-manager integrates with skill-planner workflow:

**After skill improvement:**
1. skill-planner completes implementation
2. Skill version updated in SKILL.md
3. marketplace-manager detects mismatch
4. Prompts: "Skill version changed. Sync marketplace.json?"
5. User confirms or manually syncs
6. marketplace.json updated automatically
7. Changes committed together

## Version Management

### Semantic Versioning

Follow semantic versioning for all skills:
- **MAJOR** (1.0.0 → 2.0.0): Breaking changes
- **MINOR** (1.0.0 → 1.1.0): New features, backward-compatible
- **PATCH** (1.0.0 → 1.0.1): Bug fixes, documentation

### Update Workflow

**When updating a skill:**
1. Make changes to SKILL.md or bundled resources
2. Update `metadata.version` in SKILL.md frontmatter
3. Test changes thoroughly
4. Run sync script: `python3 scripts/sync_marketplace_versions.py`
5. Commit SKILL.md and marketplace.json together
6. Push changes

**Automated workflow (with pre-commit hook):**
1. Make changes and update version
2. Git add and commit
3. Hook auto-detects mismatch
4. Hook auto-syncs marketplace.json
5. Hook adds marketplace.json to commit
6. Commit proceeds automatically

## Best Practices

**Version Management:**
1. Always update skill version when making changes
2. Use `metadata.version` (not deprecated `version`)
3. Follow semantic versioning guidelines
4. Sync marketplace.json before pushing
5. Include both files in same commit

**Organization:**
1. Group related skills into plugins
2. Use descriptive plugin names
3. Set appropriate categories
4. Keep plugin versions synchronized
5. Document changes in IMPROVEMENT_PLAN.md

**Automation:**
1. Install pre-commit hook for auto-sync
2. Run validation before pushing
3. Use --dry-run to preview changes
4. Check sync status regularly

**Troubleshooting:**
- If auto-detection fails, use `--path` flag
- Use `--verbose` to debug path resolution
- Check for `.git` or `.claude-plugin` directories
- Ensure you're in repository when running scripts

## See Also

- **skillsmith** - Creates and improves skills
- **skill-planner** - Plans skill improvements
- [THREE_SKILL_ARCHITECTURE.md](../../THREE_SKILL_ARCHITECTURE.md) - Complete system design
