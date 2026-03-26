---

name: marketplace-manager
description: >-
  This skill should be used when managing Claude Code plugin marketplace
  operations including setup, validation, version syncing, and plugin
  scaffolding. Sets up marketplace repos to be self-sufficient with their
  own validation and sync scripts. Triggers on "setup marketplace repo",
  "install repo scripts", "scaffold plugin", "auto-fix marketplace",
  "reverse scan", "sync versions", "validate marketplace", "add to
  marketplace", "check marketplace", or "create plugin". Do NOT use for
  skill content improvements (use skillsmith), plugin component creation
  (use plugin-dev), or OmniFocus/Obsidian operations.
license: MIT
metadata:
  conciseness: 100
  complexity: 90
  spec_compliance: 90
  progressive: 100
  overall: 95
  last_evaluated: 2026-03-11
  version: "4.0.0"
  author: J. Greg Williams
compatibility: Requires git repository with .claude-plugin/marketplace.json

---

# Marketplace Manager

Manages Claude Code plugin marketplace operations. Makes marketplace repos self-sufficient with their own validation and sync scripts.

| Command | Purpose |
|---------|---------|
| `/mp-sync` | Sync plugin versions to marketplace.json |
| `/mp-validate` | Validate marketplace.json against official schema |
| `/mp-add` | Scaffold a new plugin or migrate a legacy skill |
| `/mp-list` | List all marketplace plugins |
| `/mp-status` | Show version mismatches and validation summary |

## Architecture

Two-tier script model:

**Repo-level scripts** -- installed INTO marketplace repos by `setup.py`, making them self-sufficient:
- `scripts/repo/validate.py` -- schema validation, bidirectional disk scan, auto-fix, CI output
- `scripts/repo/sync.py` -- version sync from plugin.json/SKILL.md to marketplace.json

**Skill-level scripts** -- used by the marketplace-manager skill directly:
- `scripts/setup.py` -- initialize repos, copy repo scripts, install pre-commit hook
- `scripts/scaffold.py` -- create new plugins, migrate legacy skills

After `setup.py all`, a marketplace repo is fully self-sufficient with no runtime dependency on marketplace-manager.

## Operations

### Setup (initialize a marketplace repo)

```bash
python3 scripts/setup.py init --name my-marketplace --owner-name "Team"
python3 scripts/setup.py install-scripts    # Copy validate.py + sync.py into repo
python3 scripts/setup.py install-hook       # Install pre-commit hook
python3 scripts/setup.py all               # All of the above in sequence
```

### Validate (official Anthropic schema)

```bash
python3 scripts/repo/validate.py [path]              # Validate marketplace.json
python3 scripts/repo/validate.py --fix                # Auto-add unregistered plugins
python3 scripts/repo/validate.py --format json        # CI/CD output
python3 scripts/repo/validate.py --staged             # Pre-commit version check
python3 scripts/repo/validate.py --check-structure    # Anti-pattern detection
```

### Sync (version alignment)

```bash
python3 scripts/repo/sync.py [path]          # Sync versions to marketplace.json
python3 scripts/repo/sync.py --dry-run       # Preview changes without writing
```

### Scaffold (plugin creation and migration)

```bash
python3 scripts/scaffold.py create my-plugin --description "Does things"
python3 scripts/scaffold.py create my-plugin --with-commands --with-agents
python3 scripts/scaffold.py migrate skills/old-skill --dry-run
```

## References

| Reference | Content |
|-----------|---------|
| `references/official_docs_index.md` | Official Anthropic documentation links |
| `references/plugin_marketplace_guide.md` | Plugin structure and marketplace schema |
| `references/marketplace_distribution_guide.md` | Distribution workflow and best practices |
| `references/troubleshooting.md` | Common issues and solutions |

Workflow: `plugin-dev` (build) → `skillsmith` (improve) → `marketplace-manager` (publish)
