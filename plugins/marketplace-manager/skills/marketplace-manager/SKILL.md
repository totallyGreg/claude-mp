---

name: marketplace-manager
description: >-
  This skill should be used when managing Claude Code plugin marketplace
  operations including version syncing, skill publishing, and marketplace.json
  maintenance. Supports programmatic invocation by other skills for automated
  version management. Use when adding skills to marketplace, updating skill
  versions, syncing marketplace.json, or managing plugin distributions.
  Triggers on "sync versions", "validate plugin", "add to marketplace",
  "check marketplace", "update marketplace", "create plugin", "configure
  marketplace hook", or "fix version mismatch".
license: MIT
metadata:
  conciseness: 100
  complexity: 90
  spec_compliance: 90
  progressive: 100
  overall: 95
  last_evaluated: 2026-03-11
  version: "3.0.0"
  author: J. Greg Williams
compatibility: Requires git repository with .claude-plugin/marketplace.json

---

# Marketplace Manager

Manages Claude Code plugin marketplace operations with automatic version detection and syncing.

## Overview

This plugin enables marketplace management for Claude Code skills:

- **Version syncing** from version sources (plugin.json or SKILL.md) to marketplace.json
- **Plugin management** for adding, creating, and validating plugins
- **Git integration** via pre-commit hook for automatic sync
- **Scaffolding tools** for creating new plugins and migrating skills

## Quick Commands

| Command | Purpose |
|---------|---------|
| `/mp-sync` | Sync plugin versions to marketplace.json |
| `/mp-validate` | Validate marketplace.json structure |
| `/mp-add` | Add skill or create plugin |
| `/mp-list` | List all marketplace plugins |
| `/mp-status` | Show version mismatches |

## Operations

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

Validation checks include:
- Declared skills exist on disk with valid SKILL.md
- **Skills present on disk but missing from the `skills` array** (undeclared skill detection)
- Version format compliance, duplicate plugin names, required fields

## Structure Validation

Detect structural anti-patterns in multi-plugin repos before they cause incorrect version enforcement:

```bash
uv run scripts/detect_version_changes.py --check-structure       # Human-readable
uv run scripts/detect_version_changes.py --check-structure --ci  # JSON, exit 1 if issues
```

**Anti-pattern detected:** Multiple plugin entries in `marketplace.json` resolving to the same `plugin.json`. This happens when independent plugins all use `source: "./"` without their own subdirectories.

**CI pipeline usage** (replaces custom `check-version-bump.sh`):

```bash
uv run scripts/detect_version_changes.py --check-staged --ci     # Version bump check
uv run scripts/detect_version_changes.py --check-structure --ci  # Structure check
```

`--ci` flag: always outputs JSON, exits 1 for any detected issue.

See `references/plugin_marketplace_guide.md` → "Single-Plugin vs Multi-Plugin Marketplace Layouts" for canonical layout examples.

## Git Integration

Auto-sync marketplace.json before commits via pre-commit hook:

```bash
bash scripts/install_hook.sh           # Install hook
bash scripts/install_hook.sh --dry-run # Preview installation
```

Hook detects version mismatches, auto-syncs marketplace.json, and stages updates. Bypassable with `git commit --no-verify`.

## External Repo Usage

When marketplace-manager is installed as a plugin (not vendored in the repo), the hook auto-embeds the script path at install time:

```bash
# Install from plugin cache (run from within target repo)
bash ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/install_hook.sh

# Preview installation
bash ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/install_hook.sh --dry-run
```

**Requirements:** The target repo needs `.claude-plugin/marketplace.json`. Initialize with:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/add_to_marketplace.py init
```

After a plugin version update, re-run `install_hook.sh` to refresh the embedded path.

## Scaffolding & Migration

```bash
# Create new plugin
uv run scripts/create_plugin.py <plugin-name> \
  --description "Plugin description" \
  --skill <skill-path>

# Migrate legacy skill
uv run scripts/migrate_to_plugin.py <skill-name>          # Execute
uv run scripts/migrate_to_plugin.py <skill-name> --dry-run # Preview
```

## Version Management

**Auto Mode** (single-skill plugins): Plugin version syncs from skill version automatically.
**Manual Mode** (multi-component plugins): Warns about mismatches, requires manual update.

```bash
uv run scripts/sync_marketplace_versions.py               # Auto (default)
uv run scripts/sync_marketplace_versions.py --mode=manual  # Manual
```

### Additional Tools

```bash
uv run scripts/deprecate_skill.py --skill <name> --reason "Reason"
uv run scripts/analyze_bundling.py
uv run scripts/generate_utils_template.py --skill <name>
```

## References

| Reference | Content |
|-----------|---------|
| `references/official_docs_index.md` | Official Anthropic documentation links |
| `references/plugin_marketplace_guide.md` | Plugin structure and marketplace schema |
| `references/marketplace_distribution_guide.md` | Distribution workflow and best practices |
| `references/troubleshooting.md` | Common issues and solutions |

## See Also

- **skillsmith** — creates and improves skills
- **plugin-dev** — official Anthropic plugin for plugin components
- Workflow: `plugin-dev` (build) → `skillsmith` (improve) → `marketplace-manager` (publish)
