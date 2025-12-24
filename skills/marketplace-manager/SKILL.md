---
name: marketplace-manager
description: Manages Claude Code plugin marketplace operations including version syncing, skill publishing, and marketplace.json maintenance. Supports programmatic invocation by other skills (e.g., Skillsmith) for automated version management. Use when adding skills to marketplace, updating skill versions, syncing marketplace.json, or managing plugin distributions. Triggers when user mentions marketplace, version sync, or when invoked by other skills.
metadata:
  version: "1.2.0"
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

## Programmatic Invocation

marketplace-manager can be invoked programmatically by other skills (e.g., Skillsmith) for automated version management and git operations.

**When Called by Skillsmith:**
1. Skillsmith completes skill changes (quick update or complex implementation)
2. Skillsmith calls marketplace-manager: "Sync versions and commit these changes"
3. marketplace-manager runs sync_marketplace_versions.py
4. marketplace-manager updates marketplace.json with new skill version
5. marketplace-manager asks user: "Commit these changes? [yes/no]"
6. On approval, commits both SKILL.md and marketplace.json together
7. marketplace-manager asks user: "Push to remote? [yes/no]"
8. Returns commit SHA and status to Skillsmith

**Workflow Integration:**
- **Quick updates**: Skillsmith → marketplace-manager → commit (single flow)
- **Complex updates**: skill-planner → Skillsmith → marketplace-manager → commit to plan branch
- **Manual fallback**: Users can always run scripts directly

**Commands Used:**
```bash
# Sync versions (auto-detects changes)
python3 scripts/sync_marketplace_versions.py

# Preview changes first
python3 scripts/sync_marketplace_versions.py --dry-run

# Detect mismatches
python3 scripts/detect_version_changes.py
```

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

Follow semantic versioning for all skills and plugins:
- **MAJOR** (1.0.0 → 2.0.0): Breaking changes
- **MINOR** (1.0.0 → 1.1.0): New features, backward-compatible
- **PATCH** (1.0.0 → 1.0.1): Bug fixes, documentation

### Plugin Versioning Strategies

marketplace-manager supports two versioning modes for different plugin architectures:

**Auto Mode (Default - Recommended for Single-Skill Plugins)**
- Automatically syncs plugin version from skill version
- Best for plugins with one skill
- Plugin version always matches skill version
- Simple and automatic
- Usage: `python3 scripts/sync_marketplace_versions.py`

**Manual Mode (Recommended for Multi-Component Plugins)**
- Plugin version managed independently from component versions
- Required for plugins with multiple skills, MCP servers, LSP servers, hooks, or agents
- Sync script detects mismatches and warns without auto-updating
- Developer manually bumps plugin version based on changes
- Usage: `python3 scripts/sync_marketplace_versions.py --mode=manual`

**Choosing a Strategy:**
- **Single component** → Use auto mode
- **Multiple components** → Use manual mode
- **When in doubt** → Use manual mode for conscious version control

### Multi-Component Plugin Versioning

For plugins containing multiple components (skills, MCP servers, etc.):

**Problem with auto-sync:**
- Plugin v1.5.0 with skill-a v1.5.0 and skill-b v1.2.0
- Update skill-b to v1.3.0
- Auto-sync would keep plugin at v1.5.0 (no update signal!)

**Manual versioning workflow:**
1. Update component and bump its version
2. Run: `python3 scripts/sync_marketplace_versions.py --mode=manual`
3. Script warns about version mismatch
4. Decide appropriate plugin version bump (major/minor/patch)
5. Manually update plugin version in marketplace.json
6. Commit component + marketplace.json together

**Plugin version decision guide:**
- **MAJOR**: Any component has breaking changes
- **MINOR**: Any component adds new features
- **PATCH**: Any component fixes bugs only

### Update Workflow

**Single-skill plugin workflow:**
1. Make changes to SKILL.md or bundled resources
2. Update `metadata.version` in SKILL.md frontmatter
3. Test changes thoroughly
4. Run sync script: `python3 scripts/sync_marketplace_versions.py`
5. Commit SKILL.md and marketplace.json together
6. Push changes

**Multi-component plugin workflow:**
1. Make changes to component(s)
2. Update `metadata.version` in component's SKILL.md
3. Test changes thoroughly
4. Run sync script: `python3 scripts/sync_marketplace_versions.py --mode=manual`
5. Review warnings about version mismatches
6. Manually update plugin version in marketplace.json
7. Commit component files + marketplace.json together
8. Push changes

**Automated workflow (with pre-commit hook):**
1. Make changes and update version
2. Git add and commit
3. Hook auto-detects mismatch
4. Hook auto-syncs marketplace.json (auto mode) or warns (manual mode)
5. Hook adds marketplace.json to commit if updated
6. Commit proceeds automatically

## Best Practices

**Version Management:**
1. Always update skill version when making changes
2. Use `metadata.version` (not deprecated `version`)
3. Follow semantic versioning guidelines
4. Choose appropriate versioning mode (auto for single-skill, manual for multi-component)
5. Sync marketplace.json before pushing
6. Include both files in same commit
7. For multi-component plugins, manually control plugin version

**Plugin Organization:**
1. **Prefer single-skill plugins** for simplicity and automatic versioning
2. Use multi-skill plugins only for tightly coupled components
3. Use descriptive plugin names
4. Set appropriate categories
5. Document changes in IMPROVEMENT_PLAN.md

**Component Organization:**
1. Group related skills into plugins only if they're always used together
2. Consider separate plugins for independently versioned components
3. For plugins with skills + MCP servers + hooks, use manual versioning mode
4. Keep component versions independent within multi-component plugins

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
