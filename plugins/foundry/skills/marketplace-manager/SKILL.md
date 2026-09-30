---

name: marketplace-manager
description: >-
  This skill should be used when managing Claude Code plugin marketplace
  operations: setup, validation, version-bump enforcement, and plugin
  scaffolding. Keeps plugin.json the single source of truth and blocks
  commits that change a plugin or skill without raising its version.
  Triggers on "setup marketplace repo", "install repo scripts", "scaffold
  plugin", "auto-fix marketplace", "reverse scan", "check version bumps",
  "which plugins need a version bump", "validate marketplace", "add to
  marketplace", "check marketplace", or "create plugin". Do NOT use for
  skill content improvements (use skillsmith), plugin component creation
  (use plugin-dev), or OmniFocus/Obsidian operations.
license: MIT
metadata:
  conciseness: 100
  complexity: 100
  spec_compliance: 100
  progressive: 100
  overall: 100
  last_evaluated: 2026-03-26
  version: "5.0.0"
  author: J. Greg Williams
compatibility: Requires git repository with .claude-plugin/marketplace.json

---

# Marketplace Manager

Manages Claude Code plugin marketplace repos. `plugin.json` is the single source of truth for a plugin's version, description, and author; marketplace entries carry only `name`, `source`, and `category`. Schema checks come from Anthropic's `claude plugin validate`; this skill adds what it doesn't cover.

| Command | Purpose |
|---------|---------|
| `/mp-status` | Show plugins and skills changed since main that still need a version bump |
| `/mp-validate` | `claude plugin validate` plus duplicate-metadata, version-bump, and unregistered-plugin checks |
| `/mp-add` | Scaffold a new plugin or migrate a legacy skill |
| `/mp-list` | List plugins with version and description read from each plugin.json |

## Version rule

Claude Code updates an installed plugin only when its computed version changes, and `plugin.json` `version` wins over everything else. So, against the merge-base of HEAD and `origin/main`:

- Any file changed under `plugins/<p>/` → `<p>/.claude-plugin/plugin.json` version must be semver-greater than at the base
- Any file changed under `plugins/<p>/skills/<s>/` → `<s>/SKILL.md` `metadata.version` must be greater too
- New plugins and skills pass if they declare a version

Bump in the first commit that touches a plugin; later commits on the branch pass. Merging main into the branch moves the base, so parallel releases force a fresh bump instead of colliding silently.

## Architecture

- `scripts/repo/validate.py` -- the checks above; copied into marketplace repos by `setup.py` so they need nothing from this skill at runtime
- `scripts/setup.py` -- create marketplace.json, copy validate.py, install the checks-only pre-commit hook
- `scripts/scaffold.py` -- create new plugins, migrate legacy skills

## Operations

### Setup (initialize a marketplace repo)

```bash
python3 scripts/setup.py all --name my-marketplace --owner-name "Team"
python3 scripts/setup.py install-hook       # Pre-commit: validate.py --staged
```

### Validate and check bumps

```bash
python3 scripts/repo/validate.py                    # claude plugin validate + manifest checks
python3 scripts/repo/validate.py --check-versions   # pending bumps in the working tree
python3 scripts/repo/validate.py --staged           # same against the index (pre-commit)
python3 scripts/repo/validate.py --fix              # register unlisted plugins as {name, source}
python3 scripts/repo/validate.py --check-structure  # shared-source anti-pattern
```

### Scaffold (plugin creation and migration)

```bash
python3 scripts/scaffold.py create my-plugin --description "Does things"
python3 scripts/scaffold.py migrate skills/old-skill --dry-run
```

### Release tags (optional)

After merging, `claude plugin tag plugins/<p> --push` creates `<p>--v<version>`. Tags are only needed when other plugins declare version ranges on `<p>`; update detection uses the version alone.

## References

| Reference | Content |
|-----------|---------|
| `references/official_docs_index.md` | Official Anthropic documentation links |
| `references/plugin_marketplace_guide.md` | Plugin structure and marketplace schema |
| `references/marketplace_distribution_guide.md` | Distribution workflow and best practices |
| `references/troubleshooting.md` | Common issues and solutions |

Workflow: `plugin-dev` (build) → `skillsmith` (improve) → `marketplace-manager` (publish)
