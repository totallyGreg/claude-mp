---
name: marketplace-manager
description: This skill should be used when managing Claude Code plugin marketplace operations including version syncing, skill publishing, and marketplace.json maintenance. Supports programmatic invocation by other skills for automated version management. Use when adding skills to marketplace, updating skill versions, syncing marketplace.json, or managing plugin distributions.
metadata:
  version: "2.2.0"
  author: J. Greg Williams
  license: MIT
compatibility: Requires git repository with .claude-plugin/marketplace.json
---

# Marketplace Manager

Manages Claude Code plugin marketplace operations with automatic version detection and syncing.

## Overview

This plugin enables marketplace management for Claude Code skills:

- **Version syncing** between SKILL.md and marketplace.json
- **Plugin management** for adding, creating, and validating plugins
- **Git integration** via pre-commit hook for automatic sync
- **Scaffolding tools** for creating new plugins and migrating skills

## Quick Commands

This plugin includes slash commands for common operations:

| Command | Purpose |
|---------|---------|
| `/mp-sync` | Sync SKILL.md versions to marketplace.json |
| `/mp-validate` | Validate marketplace.json structure |
| `/mp-add` | Add skill or create plugin |
| `/mp-list` | List all marketplace plugins |
| `/mp-status` | Show version mismatches |

## When to Use

Use marketplace-manager when:
- Adding new skills to marketplace.json
- Updating skill versions in marketplace
- Syncing versions between SKILL.md and marketplace.json
- Detecting version mismatches
- Creating new plugins or migrating legacy skills

## Core Operations

### Version Syncing

Keeps marketplace.json synchronized with SKILL.md frontmatter:

```bash
# Sync all versions (auto mode - default)
uv run scripts/sync_marketplace_versions.py

# Preview changes
uv run scripts/sync_marketplace_versions.py --dry-run

# Manual mode (for multi-skill plugins)
uv run scripts/sync_marketplace_versions.py --mode=manual
```

### Adding Skills

```bash
# List marketplace contents
uv run scripts/add_to_marketplace.py list

# Add skill to existing plugin
uv run scripts/add_to_marketplace.py add-skill <skill-path> --plugin <plugin-name>

# Create new plugin
uv run scripts/add_to_marketplace.py create-plugin <plugin-name> --skill <skill-path>
```

### Validation

```bash
# Validate marketplace structure
uv run scripts/add_to_marketplace.py validate

# JSON output for CI/CD
uv run scripts/add_to_marketplace.py validate --format json
```

## Git Integration

### Pre-Commit Hook

Auto-sync marketplace.json before commits:

```bash
# Install hook
bash scripts/install_hook.sh

# Preview installation
bash scripts/install_hook.sh --dry-run

# Force reinstall
bash scripts/install_hook.sh --force
```

Hook behavior:
- Detects version mismatches before commit
- Auto-syncs marketplace.json
- Stages updated marketplace.json
- Bypassable with `git commit --no-verify`

## Plugin Scaffolding

### Create New Plugin

```bash
uv run scripts/create_plugin.py <plugin-name> \
  --description "Plugin description" \
  --skill <skill-path>
```

### Migrate Legacy Skill

```bash
# Preview migration
uv run scripts/migrate_to_plugin.py <skill-name> --dry-run

# Execute migration
uv run scripts/migrate_to_plugin.py <skill-name>
```

## Version Management

### Semantic Versioning

- **MAJOR**: Breaking changes
- **MINOR**: New features, backward-compatible
- **PATCH**: Bug fixes, documentation

### Versioning Modes

**Auto Mode** (single-skill plugins): Plugin version syncs from skill version automatically.

**Manual Mode** (multi-component plugins): Warns about mismatches, requires manual plugin version update.

```bash
# Auto mode (default)
uv run scripts/sync_marketplace_versions.py

# Manual mode
uv run scripts/sync_marketplace_versions.py --mode=manual
```

## Programmatic Invocation

marketplace-manager integrates with Skillsmith for automated workflows:

1. Skillsmith completes skill changes
2. Calls marketplace-manager to sync versions
3. marketplace-manager updates marketplace.json
4. Prompts user for commit approval
5. Returns commit status

## Additional Tools

### Deprecating Skills

```bash
uv run scripts/deprecate_skill.py --skill <name> --reason "Reason"
```

### Bundling Analysis

```bash
uv run scripts/analyze_bundling.py
```

### Utils Template Generation

```bash
uv run scripts/generate_utils_template.py --skill <name>
```

## Reference Documentation

For detailed documentation, see:

| Reference | Content |
|-----------|---------|
| `references/official_docs_index.md` | Official Anthropic documentation links |
| `references/plugin_marketplace_guide.md` | Plugin structure and marketplace schema |
| `references/marketplace_distribution_guide.md` | Distribution workflow and best practices |
| `references/troubleshooting.md` | Common issues and solutions |

## Installation

Users install from marketplace:

```bash
/plugin marketplace add totallyGreg/claude-mp
/plugin install marketplace-manager@totally-tools
```

## See Also

- **skillsmith** - Creates and improves skills
