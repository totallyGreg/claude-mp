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
  marketplace hook", or "fix version mismatch". Do NOT use for skill content
  improvements (use skillsmith), plugin component creation (use plugin-dev),
  or OmniFocus/Obsidian operations.
license: MIT
metadata:
  conciseness: 100
  complexity: 90
  spec_compliance: 90
  progressive: 100
  overall: 95
  last_evaluated: 2026-03-11
  version: "3.1.0"
  author: J. Greg Williams
compatibility: Requires git repository with .claude-plugin/marketplace.json

---

# Marketplace Manager

Manages Claude Code plugin marketplace operations with automatic version detection and syncing.

| Command | Purpose |
|---------|---------|
| `/mp-sync` | Sync plugin versions to marketplace.json |
| `/mp-validate` | Validate marketplace.json structure |
| `/mp-add` | Add skill or create plugin |
| `/mp-list` | List all marketplace plugins |
| `/mp-status` | Show version mismatches |

## Operations

### Version Syncing

```bash
uv run scripts/sync_marketplace_versions.py               # Auto (default)
uv run scripts/sync_marketplace_versions.py --dry-run      # Preview changes
uv run scripts/sync_marketplace_versions.py --mode=manual   # Multi-skill plugins
```

### Adding Skills

```bash
uv run scripts/add_to_marketplace.py list                                        # List contents
uv run scripts/add_to_marketplace.py add-skill <skill-path> --plugin <name>      # Add to plugin
uv run scripts/add_to_marketplace.py create-plugin <name> --skill <skill-path>   # New plugin
```

### Validation

```bash
uv run scripts/add_to_marketplace.py validate              # Validate structure
uv run scripts/add_to_marketplace.py validate --format json # CI/CD output
```

Checks: required root fields (`name`, `owner`, `plugins` array), unknown root fields, plugin entry `name`/`source`, version format, duplicate names, source path validity.

### Structure & CI

Detect anti-patterns (e.g. multiple plugins sharing `source: "./"`) and enforce version bumps:

```bash
uv run scripts/detect_version_changes.py --check-structure --ci  # Structure check
uv run scripts/detect_version_changes.py --check-staged --ci     # Version bump check
```

See `references/plugin_marketplace_guide.md` → "Single-Plugin vs Multi-Plugin Marketplace Layouts".

## Git Integration & External Repos

Auto-sync marketplace.json before commits via pre-commit hook:

```bash
bash scripts/install_hook.sh           # Install hook
bash scripts/install_hook.sh --dry-run # Preview installation
```

For external repos (marketplace-manager installed as plugin):

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/install_hook.sh
uv run ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/add_to_marketplace.py init
```

## Scaffolding & Version Management

```bash
uv run scripts/create_plugin.py <name> --description "..." --skill <path>  # New plugin
uv run scripts/migrate_to_plugin.py <skill-name> [--dry-run]               # Migrate legacy
uv run scripts/deprecate_skill.py --skill <name> --reason "Reason"         # Deprecate
uv run scripts/analyze_bundling.py                                         # Analyze bundles
```

**Auto Mode** (single-skill plugins): Plugin version syncs from skill version automatically.
**Manual Mode** (multi-component plugins): Warns about mismatches, requires manual update.

## References

| Reference | Content |
|-----------|---------|
| `references/official_docs_index.md` | Official Anthropic documentation links |
| `references/plugin_marketplace_guide.md` | Plugin structure and marketplace schema |
| `references/marketplace_distribution_guide.md` | Distribution workflow and best practices |
| `references/troubleshooting.md` | Common issues and solutions |

Workflow: `plugin-dev` (build) → `skillsmith` (improve) → `marketplace-manager` (publish)
