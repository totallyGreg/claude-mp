---
title: "refactor: Align marketplace-manager with official Anthropic marketplace schema and consolidate scripts"
type: refactor
status: completed
date: 2026-03-26
---

# refactor: Align marketplace-manager with official Anthropic marketplace schema and consolidate scripts

## Overview

The marketplace-manager skill's reference docs, validation logic, and script examples are out of alignment with the official Anthropic marketplace schema. The `skills` field used throughout marketplace.json plugin entries is **not part of the official schema** -- Claude Code auto-discovers skills from plugin directories. Additionally, the 12 scripts (5,787 lines) contain ~1,200 lines of duplicated logic across 4 major areas.

This plan aligns the skill with official guidance, updates reference docs with source links, removes the non-standard `skills` field from validation/generation, adds reverse scan + auto-fix (a feature gap found in jshanks/claude), and replaces 12 scripts with 4 clean, focused scripts written from scratch.

## Problem Frame

Three problems converge:

1. **Schema drift**: The marketplace-manager teaches and validates a `skills` array in marketplace.json plugin entries. The official Anthropic schema (https://docs.anthropic.com/en/docs/claude-code/plugin-marketplaces) defines only `name` and `source` as required plugin entry fields, with `description`, `version`, `author`, `homepage`, `repository`, `license`, `keywords`, `category`, `tags`, and `strict` as optional. There is no `skills` field. Claude Code auto-discovers skills by scanning `<plugin-root>/skills/*/SKILL.md`.

2. **Reference doc staleness**: The reference docs (`plugin_marketplace_guide.md`, `marketplace_distribution_guide.md`) contain a mix of official and invented guidance without source attribution. Users can't distinguish spec-compliant from convention-based advice.

3. **Script sprawl**: 12 scripts with ~1,200 lines of duplicated frontmatter parsing, version resolution, repo root finding, and validation logic across `add_to_marketplace.py`, `marketplace_ci.py`, `detect_version_changes.py`, `sync_marketplace_versions.py`, and others.

## Requirements Trace

- R1. Remove `skills` field from all marketplace.json generation, validation warnings, and examples
- R2. Update reference docs with official Anthropic schema tables, source URLs, and comprehensive marketplace organization patterns (all valid plugin structures including commands, agents, hooks, MCP servers, LSP servers)
- R3. Add reverse scan + auto-fix feature (detect unregistered plugins on disk, optionally add them)
- R4. Replace 12 scripts with 4 clean scripts (written from scratch) while preserving all functionality
- R5. Update SKILL.md command table and script references
- R6. Maintain backward compatibility for existing marketplace.json files that use `skills` (warn, don't error)
- R7. Run skillsmith evaluation after all changes to verify SKILL.md quality, reference doc consistency, and script path accuracy

## Scope Boundaries

- Does NOT restructure existing marketplace repos (jshanks/claude, claude-skills) -- that's user work guided by updated docs
- Does NOT add new marketplace.json fields beyond what the official schema defines
- Does NOT implement the multi-plugin marketplace support from plan `2026-03-23-001` -- that plan is complementary, not overlapping

## Context & Research

### Official Anthropic Schema (source: https://docs.anthropic.com/en/docs/claude-code/plugin-marketplaces)

**Required root fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Marketplace identifier (kebab-case) |
| `owner` | object | Maintainer info (`name` required, `email` optional) |
| `plugins` | array | List of available plugins |

**Optional root metadata:**

| Field | Type | Description |
|-------|------|-------------|
| `metadata.description` | string | Brief marketplace description |
| `metadata.version` | string | Marketplace version |
| `metadata.pluginRoot` | string | Base directory prepended to relative source paths |

**Required plugin entry fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Plugin identifier (kebab-case) |
| `source` | string or object | Where to fetch the plugin |

**Optional plugin entry fields:**

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Brief plugin description |
| `version` | string | Plugin version |
| `author` | object | Author info |
| `homepage` | string | Documentation URL |
| `repository` | string | Source code URL |
| `license` | string | SPDX identifier |
| `keywords` | array | Discovery tags |
| `category` | string | Organization category |
| `tags` | array | Searchability tags |
| `strict` | boolean | Whether plugin.json is authority for components (default: true) |

### plugin.json is Optional (source: https://code.claude.com/docs/en/plugins-reference)

The manifest (`plugin.json`) is **optional**. If omitted, Claude Code auto-discovers components in default locations and derives the plugin name from the directory name. Use a manifest when you need to provide metadata or custom component paths. If present, **only `name` is required** — all other fields are optional.

This means for simple single-skill plugins, no `plugin.json` is needed at all — Claude Code will discover the skill from `skills/*/SKILL.md` automatically.

### Official Marketplace Schema (continued)

**Component configuration fields** (also valid in plugin entries per official docs):

| Field | Type | Description |
|-------|------|-------------|
| `commands` | string or array | Custom paths to command files or directories |
| `agents` | string or array | Custom paths to agent files |
| `hooks` | string or object | Custom hooks configuration or path to hooks file |
| `mcpServers` | string or object | MCP server configurations or path to MCP config |
| `lspServers` | string or object | LSP server configurations or path to LSP config |

**Not in schema:** `skills` (as a marketplace.json field), `metadata` (at plugin level), `components`

### Plugin Component Auto-Discovery (source: https://docs.anthropic.com/en/docs/claude-code/plugins)

Claude Code auto-discovers components by scanning well-known directories inside the plugin root:

| Directory | What it finds | Discovery pattern |
|-----------|--------------|-------------------|
| `commands/` | Slash commands | `*.md` files |
| `agents/` | Custom agents | `*.md` files |
| `skills/` | Agent Skills | `*/SKILL.md` subdirectories |
| `hooks/` | Event handlers | `hooks.json` |
| `.mcp.json` | MCP servers | JSON config at plugin root |
| `.lsp.json` | LSP servers | JSON config at plugin root |
| `settings.json` | Default settings | JSON config at plugin root |

**Important:** Don't put `commands/`, `agents/`, `skills/`, or `hooks/` inside `.claude-plugin/`. Only `plugin.json` goes inside `.claude-plugin/`. All other directories must be at the plugin root level. (source: https://docs.anthropic.com/en/docs/claude-code/plugins#plugin-structure-overview)

### `strict` Mode (source: https://docs.anthropic.com/en/docs/claude-code/plugin-marketplaces, https://code.claude.com/docs/en/plugins-reference)

| Value | Behavior |
|-------|----------|
| `true` (default) | The plugin has its own `plugin.json` and manages its own components. The marketplace entry can add extra commands or hooks on top — both sources are merged. |
| `false` | The plugin doesn't need its own `plugin.json`. The marketplace entry defines everything. If the plugin also has a `plugin.json` that declares components, that's a conflict and the plugin fails to load. |

This is important for Pattern 4 (full-featured plugins) — `strict: false` lets marketplace entries fully define hooks, MCP servers, and other components without requiring a `plugin.json` at the source path.

### `metadata.pluginRoot` (source: https://docs.anthropic.com/en/docs/claude-code/plugin-marketplaces)

Base directory prepended to relative plugin source paths. For example, `"pluginRoot": "./plugins"` lets you write `"source": "formatter"` instead of `"source": "./plugins/formatter"`.

### Path Resolution (source: https://docs.anthropic.com/en/docs/claude-code/plugin-marketplaces)

Paths resolve relative to the marketplace root — the directory containing `.claude-plugin/`. So `./plugins/my-plugin` points to `<repo>/plugins/my-plugin`, even though `marketplace.json` lives at `<repo>/.claude-plugin/marketplace.json`. Do not use `../` to climb out of `.claude-plugin/`.

### Valid Marketplace Organization Patterns

All patterns below are derived from official Anthropic documentation. Each shows the directory structure, the corresponding marketplace.json entry, and when to use it.

#### Pattern 1: Single Plugin, Single Skill (simplest)

One plugin with one skill. The plugin owns the entire repo. Note: `plugin.json` is optional — if omitted, Claude Code auto-discovers components and derives the plugin name from the directory name. Include it when you want to set version, description, or other metadata.

```
my-marketplace/
+-- .claude-plugin/
|   +-- marketplace.json
+-- plugins/
    +-- my-plugin/
        +-- .claude-plugin/
        |   +-- plugin.json        # optional: { "name": "my-plugin", "version": "1.0.0" }
        +-- skills/
            +-- my-skill/
                +-- SKILL.md       # auto-discovered
```

```json
{
  "plugins": [
    { "name": "my-plugin", "source": "./plugins/my-plugin" }
  ]
}
```

**When to use:** Most common case. One focused plugin, one skill. Simple version management. If you omit `plugin.json`, the plugin name defaults to the directory name (`my-plugin`).

#### Pattern 2: Single Plugin, Multiple Skills (bundle)

One plugin bundles several related skills. Still one `plugin.json`.

```
my-marketplace/
+-- .claude-plugin/
|   +-- marketplace.json
+-- plugins/
    +-- terminal-guru/
        +-- .claude-plugin/
        |   +-- plugin.json
        +-- skills/
        |   +-- terminal-emulation/
        |   |   +-- SKILL.md       # auto-discovered
        |   +-- zsh-dev/
        |   |   +-- SKILL.md       # auto-discovered
        |   +-- signals-monitoring/
        |       +-- SKILL.md       # auto-discovered
        +-- commands/
        |   +-- diagnose.md        # auto-discovered
        +-- agents/
            +-- terminal-guru.md   # auto-discovered
```

```json
{
  "plugins": [
    { "name": "terminal-guru", "source": "./plugins/terminal-guru", "version": "2.0.0" }
  ]
}
```

**When to use:** Tightly coupled skills that are always used together. Commands and agents that complement the skills. Manual version management required (plugin version is independent from individual skill versions).

#### Pattern 3: Multiple Independent Plugins (multi-plugin marketplace)

Multiple independent plugins share one marketplace repo. Each plugin has its own `plugin.json`. Users install selectively.

```
my-marketplace/
+-- .claude-plugin/
|   +-- marketplace.json           # catalog only -- no root plugin.json
+-- plugins/
    +-- formatter/
    |   +-- .claude-plugin/
    |   |   +-- plugin.json        # { "name": "formatter", "version": "2.1.0" }
    |   +-- skills/
    |       +-- code-format/
    |           +-- SKILL.md
    +-- deployer/
    |   +-- .claude-plugin/
    |   |   +-- plugin.json        # { "name": "deployer", "version": "1.0.0" }
    |   +-- skills/
    |   |   +-- deploy/
    |   |       +-- SKILL.md
    |   +-- commands/
    |       +-- deploy-status.md
    +-- linter/
        +-- .claude-plugin/
        |   +-- plugin.json        # { "name": "linter", "version": "1.3.0" }
        +-- skills/
            +-- lint-check/
                +-- SKILL.md
```

```json
{
  "plugins": [
    { "name": "formatter", "source": "./plugins/formatter", "version": "2.1.0" },
    { "name": "deployer", "source": "./plugins/deployer", "version": "1.0.0" },
    { "name": "linter", "source": "./plugins/linter", "version": "1.3.0" }
  ]
}
```

**When to use:** A team or individual publishes multiple unrelated plugins from one repo. Each plugin versions independently. Install with `/plugin install formatter@my-marketplace`.

**Anti-pattern:** Do NOT use `source: "./"` for multiple plugins -- they'd all resolve to the same `plugin.json`, causing version enforcement conflicts.

#### Pattern 4: Full-Featured Plugin (all component types)

A plugin using every available component type. Shows how commands, agents, hooks, MCP servers, and LSP servers coexist.

```
my-marketplace/
+-- .claude-plugin/
|   +-- marketplace.json
+-- plugins/
    +-- enterprise-tools/
        +-- .claude-plugin/
        |   +-- plugin.json
        +-- commands/
        |   +-- core/
        |   |   +-- status.md
        |   |   +-- deploy.md
        |   +-- experimental/
        |       +-- preview.md
        +-- agents/
        |   +-- security-reviewer.md
        |   +-- compliance-checker.md
        +-- skills/
        |   +-- code-review/
        |   |   +-- SKILL.md
        |   |   +-- references/
        |   |   +-- scripts/
        |   +-- incident-response/
        |       +-- SKILL.md
        +-- hooks/
        |   +-- hooks.json
        +-- .mcp.json
        +-- .lsp.json
        +-- settings.json
```

The marketplace entry can specify custom component paths and inline hook/MCP configs:

```json
{
  "plugins": [
    {
      "name": "enterprise-tools",
      "source": { "source": "github", "repo": "company/enterprise-plugin" },
      "version": "2.1.0",
      "description": "Enterprise workflow automation tools",
      "commands": ["./commands/core/", "./commands/experimental/preview.md"],
      "agents": ["./agents/security-reviewer.md", "./agents/compliance-checker.md"],
      "hooks": {
        "PostToolUse": [{
          "matcher": "Write|Edit",
          "hooks": [{ "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh" }]
        }]
      },
      "mcpServers": {
        "enterprise-db": {
          "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
          "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"]
        }
      },
      "strict": false
    }
  ]
}
```

**When to use:** Enterprise or complex plugins that need explicit component paths, inline hooks, or MCP server configs in the marketplace entry. Use `strict: false` when the marketplace entry should be the sole authority (no `plugin.json` component declarations).

**Key variables:** `${CLAUDE_PLUGIN_ROOT}` references the plugin's installation directory (required because plugins are copied to a cache). `${CLAUDE_PLUGIN_DATA}` references persistent state that survives plugin updates.

#### Pattern 5: Using `pluginRoot` to Simplify Paths

When all plugins live under a common directory, `metadata.pluginRoot` avoids repetitive path prefixes.

```json
{
  "name": "company-tools",
  "owner": { "name": "DevTools Team" },
  "metadata": {
    "pluginRoot": "./plugins"
  },
  "plugins": [
    { "name": "formatter", "source": "formatter" },
    { "name": "deployer", "source": "deployer" },
    { "name": "linter", "source": "linter" }
  ]
}
```

Equivalent to writing `"source": "./plugins/formatter"` etc. without `pluginRoot`.

**When to use:** Marketplaces with many plugins under a shared parent directory. Reduces boilerplate.

#### Pattern 6: External Source Types

Plugins don't have to live in the marketplace repo. The `source` field supports multiple external source types:

| Source Type | Example | Use Case |
|-------------|---------|----------|
| Relative path | `"./plugins/my-plugin"` | Plugin lives in marketplace repo |
| GitHub | `{ "source": "github", "repo": "owner/repo" }` | Plugin in a separate GitHub repo |
| Git URL | `{ "source": "url", "url": "https://gitlab.com/org/repo.git" }` | Any git host (GitLab, Bitbucket, etc.) |
| Git subdirectory | `{ "source": "git-subdir", "url": "owner/repo", "path": "tools/plugin" }` | Plugin in a monorepo subdirectory |
| npm | `{ "source": "npm", "package": "@org/plugin" }` | Published npm package |

All object source types support optional `ref` (branch/tag) and `sha` (pin to exact commit) fields.

#### Pattern Selection Guide

| Scenario | Recommended Pattern |
|----------|-------------------|
| One plugin, one skill | Pattern 1 |
| One plugin, related skills that always ship together | Pattern 2 |
| Multiple independent plugins from one repo | Pattern 3 |
| Plugin with hooks, MCP servers, or LSP servers | Pattern 4 |
| Many plugins under shared directory | Pattern 5 (pluginRoot) |
| Plugin maintained in separate repo | Pattern 6 (external source) |
| Starting out, unsure of structure | Pattern 1; migrate to Pattern 2 or 3 later |

### Current Script Inventory (12 scripts, 5,787 lines)

| Script | Lines | Purpose |
|--------|-------|---------|
| `add_to_marketplace.py` | 1,105 | Interactive CLI: init, create, add, list, validate, metadata |
| `marketplace_ci.py` | 788 | Vendorable CI: validate, version-check, structure-check |
| `detect_version_changes.py` | 646 | Pre-commit version checking (deprecated for CI) |
| `migrate_to_plugin.py` | 664 | Legacy skill to plugin migration |
| `sync_marketplace_versions.py` | 330 | Auto-sync versions to marketplace.json |
| `create_plugin.py` | 305 | New plugin boilerplate |
| `analyze_bundling.py` | 483 | Recommend skill bundling |
| `deprecate_skill.py` | 411 | Remove plugin + scan refs |
| `sync_readme.py` | 285 | Update README from marketplace.json |
| `validate_hook.py` | 237 | Check hook installation |
| `utils.py` | 366 | Shared utilities |
| `install_hook.sh` | 167 | Install pre-commit hook |

### New Architecture: Repo-Level vs Skill-Level Scripts

The key insight is separating **what the marketplace repo needs to be self-sufficient** from **what the marketplace-manager skill provides as setup tooling**.

**Repo-level scripts** (installed INTO marketplace repos by `setup.py`):

| Script | Lines (est.) | Purpose |
|--------|-------------|---------|
| `validate.py` | ~300 | Validate marketplace.json against official schema + bidirectional disk scan + `--fix` auto-add + `--staged` for pre-commit + `--check-structure` for anti-pattern detection |
| `sync.py` | ~180 | Sync versions from plugin.json/SKILL.md to marketplace.json |

These are small, self-contained, readable scripts that live in the marketplace repo and make it self-sufficient. Inspired by jshanks' 157-line `validate_marketplace.py` but extended with official schema validation. They serve double duty as CI scripts — since they're already stdlib-only with `--format json` output, there's no need for a separate `marketplace_ci.py`.

**Skill-level scripts** (stay in marketplace-manager plugin, used by the skill):

| Script | Lines (est.) | Purpose |
|--------|-------------|---------|
| `setup.py` | ~200 | Initialize marketplace repos: create marketplace.json, copy repo scripts, install pre-commit hook |
| `scaffold.py` | ~250 | Create new plugins with official Anthropic structure, migrate legacy skills |

**Delete entirely** (all 12 old scripts replaced by 4 new ones):
`add_to_marketplace.py`, `marketplace_ci.py`, `detect_version_changes.py`, `migrate_to_plugin.py`, `sync_marketplace_versions.py`, `create_plugin.py`, `analyze_bundling.py`, `deprecate_skill.py`, `sync_readme.py`, `validate_hook.py`, `utils.py`, `install_hook.sh`

**Total:** ~930 lines (down from 5,787) across 4 scripts instead of 12.

### YAML Frontmatter Parsing Strategy

Both `validate.py` and `sync.py` need to extract version info from SKILL.md frontmatter. The approach: **try pyyaml first, fall back to a minimal subset parser**.

```python
def parse_frontmatter(text):
    """Parse YAML frontmatter. Uses pyyaml when available, stdlib fallback."""
    if not text.startswith('---'):
        return {}
    end = text.find('---', 3)
    if end == -1:
        return {}
    raw = text[3:end]

    try:
        import yaml
        return yaml.safe_load(raw) or {}
    except ImportError:
        return _parse_frontmatter_stdlib(raw)


def _parse_frontmatter_stdlib(raw):
    """Minimal YAML subset parser — handles flat keys and one level of nesting.

    Handles:  name: value, metadata:\\n  version: "1.0.0", quoted/unquoted values
    Skips:    multi-line strings (>- |), anchors, aliases, sequences
    """
    result = {}
    current_map = None
    current_key = None
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith('#'):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if ':' not in stripped:
            continue
        key, _, val = stripped.partition(':')
        key = key.strip()
        val = val.strip().strip('"\'')
        if indent == 0:
            if val:
                result[key] = val
                current_map = None
            else:
                result[key] = {}
                current_map = result[key]
                current_key = key
        elif indent > 0 and current_map is not None and isinstance(current_map, dict):
            if val:
                current_map[key] = val
    return result
```

This gives:
- **Robust parsing** when pyyaml is available (virtually every CI image with Python has it — it's the most installed PyPI package)
- **Graceful degradation** in restricted containers (BusyBox, distroless, minimal images)
- **No hard dependency** — no `uv run`, no `pip install`, no `requirements.txt`
- **Honest about limits** — the fallback handles the subset we actually use (flat keys + one nesting level for `metadata.version`), doesn't pretend to be a full YAML parser

### Institutional Learnings

- The jshanks/claude repo has a clean 157-line `validate_marketplace.py` with bidirectional (forward + reverse) validation and `--fix` auto-add -- marketplace-manager lacks this feature
- `marketplace_ci.py` was intentionally stdlib-only and vendorable, but since the new repo-level scripts (validate.py, sync.py) are also stdlib-only and designed for CI, the separate vendorable script is no longer needed
- The `plugin_marketplace_guide.md` reference doc contains a `components` field in its plugin.json example that is not part of the official schema (line 45-53)

## Key Technical Decisions

- **Separate repo-level from skill-level scripts**: A marketplace repo should be self-sufficient with its own small validation and sync scripts. The marketplace-manager skill's job is to *set up* that self-sufficiency, not to be a runtime dependency. This is the jshanks pattern done right -- his `validate_marketplace.py` is a repo-level script that works standalone.

- **Write repo-level scripts from scratch**: Rather than merging 12 existing scripts, write `validate.py` (~300 lines) and `sync.py` (~180 lines) fresh, guided by the official Anthropic schema. Readable by anyone, handle all 6 organization patterns. The existing scripts grew organically around a non-standard `skills` field -- rewriting avoids carrying that baggage.

- **Eliminate `marketplace_ci.py`**: Since validate.py and sync.py are already designed for zero-dependency environments, they serve double duty as CI scripts. validate.py gets `--staged` (pre-commit mode) and `--check-structure` (anti-pattern detection) flags, plus `--format json` for machine-readable CI output. No separate vendorable CI script needed.

- **Try pyyaml, fall back to stdlib subset parser**: Scripts attempt `import yaml` for robust YAML frontmatter parsing. If unavailable (restricted CI containers, minimal images), they fall back to a ~25-line stdlib parser that handles flat keys and one level of nesting -- sufficient for extracting `version` and `metadata.version`. No hard dependency, no `uv run`, no `pip install`.

- **Warn on `skills` field, don't error**: The validator warns when `skills` is found in plugin entries with migration guidance. Too many existing marketplaces use it for a hard error. The auto-fix (`--fix`) generates entries WITHOUT the `skills` field per official schema.

- **`setup.py` replaces `init` + hook installation**: One script that initializes a marketplace repo end-to-end: creates `marketplace.json`, copies `validate.py` and `sync.py` into the repo's `scripts/` directory, installs the pre-commit hook. Makes the repo immediately self-sufficient.

- **`scaffold.py` replaces create + migrate**: One script for plugin creation and legacy migration, generating the official Anthropic directory structure (`.claude-plugin/plugin.json` optional, `skills/*/SKILL.md` auto-discovered).

- **Delete all 12 old scripts**: With 4 focused scripts covering all functionality, the shared `utils.py`, the vendorable `marketplace_ci.py`, and 10 other scripts are all eliminated. DRY is less important than readability and independence when scripts are meant to be copied into other repos.

## Open Questions

### Resolved During Planning

- **Should `skills` be an error or warning?** Warning with migration guidance. Too many existing marketplaces use it to make it a breaking error.
- **Should `metadata` at root level be warned?** Yes -- the official schema puts metadata fields under `metadata.description`, `metadata.version`, `metadata.pluginRoot`. Root-level `version` and `description` are not in the official schema.
- **Should we add `pluginRoot` support?** Yes, in validation (accept it as known field). Not in generation (YAGNI until a user needs it).

### Deferred to Implementation

- Exact error message wording for schema violations -- will be refined during implementation
- Whether validate.py should check for `.claude-plugin/plugin.json` existence (strict mode enforcement) or leave that to Claude Code -- depends on how strict we want to be about guiding users
- Whether the CI example reference files need complete rewrites or just script name substitutions

## Implementation Units

### Phase 1: Reference Documentation

- [ ] **Unit 1: Rewrite reference docs with official schema, organization patterns, and source links**

  **Goal:** Replace all invented schema guidance with official Anthropic schema, comprehensive organization patterns for all component types, and source URLs

  **Requirements:** R2

  **Dependencies:** None

  **Files:**
  - Modify: `plugins/marketplace-manager/skills/marketplace-manager/references/plugin_marketplace_guide.md`
  - Modify: `plugins/marketplace-manager/skills/marketplace-manager/references/marketplace_distribution_guide.md`
  - Modify: `plugins/marketplace-manager/skills/marketplace-manager/references/official_docs_index.md`

  **Approach:**
  - Replace the plugin manifest example (lines 39-54 of `plugin_marketplace_guide.md`) that shows a `components` field with the official plugin.json structure. Note that plugin.json is optional -- if omitted, Claude Code auto-discovers everything
  - Add the official marketplace.json schema tables (required root, owner, optional metadata, plugin entry required, plugin entry optional, component configuration fields) with source URLs
  - Remove all `"skills": ["./"]` from marketplace.json examples
  - Add a "Convention vs Spec" section distinguishing marketplace-manager conventions from official spec
  - Add comprehensive **Marketplace Organization Patterns** section covering all 6 valid patterns from the Context & Research section:
    - Pattern 1: Single plugin, single skill (plugin.json optional)
    - Pattern 2: Single plugin, multiple skills (bundle with commands, agents)
    - Pattern 3: Multiple independent plugins
    - Pattern 4: Full-featured plugin (all component types: commands, agents, skills, hooks, MCP servers, LSP servers, settings)
    - Pattern 5: Using `pluginRoot` to simplify paths
    - Pattern 6: External source types (GitHub, Git URL, git-subdir, npm)
  - Include the Pattern Selection Guide table
  - Document component auto-discovery table (commands/, agents/, skills/, hooks/, .mcp.json, .lsp.json, settings.json)
  - Document `strict` mode (true vs false) with behavioral impact
  - Document `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}` variables
  - Document the anti-pattern: multiple plugins sharing `source: "./"`
  - Update marketplace_distribution_guide.md to remove `skills` array examples and reference the patterns guide
  - Update official_docs_index.md with all 4 source URLs (plugins, plugin-marketplaces, plugins-reference, skills)

  **Test scenarios:**
  - All marketplace.json examples pass official schema validation
  - No example contains a `skills` field in a plugin entry
  - Every schema claim has a source URL
  - All 6 patterns documented with directory tree, marketplace.json snippet, and "when to use"
  - The anti-pattern is explicitly called out

  **Verification:**
  - Manual review confirms alignment with all 4 official Anthropic doc pages

### Phase 2: Repo-Level Scripts (written from scratch)

- [ ] **Unit 2: Write `validate.py` -- standalone marketplace validator**

  **Goal:** Create a clean, readable, stdlib-only validation script that any marketplace repo can use standalone. Combines official schema validation with jshanks' bidirectional disk scan and auto-fix.

  **Requirements:** R1, R3, R6

  **Dependencies:** Unit 1 (schema understanding)

  **Files:**
  - Create: `plugins/marketplace-manager/skills/marketplace-manager/scripts/repo/validate.py`

  **Approach:**
  Write from scratch (~250 lines, stdlib-only). The script does three things:

  1. **Schema validation** -- check marketplace.json against official Anthropic schema:
     - Required root fields: `name`, `owner` (with `name`), `plugins` array
     - Known root fields: `name`, `owner`, `plugins`, `$schema`, `metadata` (with `description`, `version`, `pluginRoot`)
     - Plugin entry required: `name`, `source`
     - Plugin entry known optional: `description`, `version`, `author`, `homepage`, `repository`, `license`, `keywords`, `category`, `tags`, `strict`, `commands`, `agents`, `hooks`, `mcpServers`, `lspServers`
     - Name format: kebab-case regex
     - Version format: semver (warn on `v` prefix)
     - Source path validation: must start with `./`, no `..`, directory must exist for relative paths
     - Duplicate name detection

  2. **Forward validation** -- for each plugin entry with a relative source path:
     - Check source directory exists
     - Check for discoverable components (skills/, commands/, agents/, .mcp.json, etc.)
     - If `strict` is true (default), optionally check for `.claude-plugin/plugin.json`
     - Warn if source directory has no discoverable components at all

  3. **Reverse scan** -- find extensions on disk not listed in marketplace.json:
     - Scan `plugins/*/` for directories with skills/ or .claude-plugin/
     - Scan root `skills/*/SKILL.md` (legacy flat layout)
     - Scan `mcp-servers/*/` with package.json or pyproject.toml
     - Scan `commands/*.md` at root level
     - Report missing entries

  4. **Auto-fix** (`--fix`):
     - Add missing plugins from reverse scan
     - Generated entries use official schema only (no `skills` field)
     - Sort plugins alphabetically, write clean JSON

  **Backward compatibility (R6):**
  - Warn (not error) when `skills` field found: "The 'skills' field is not part of the official marketplace schema. Skills are auto-discovered. Consider removing this field."
  - Warn on root-level `version` or `description` outside `metadata`: "Move to metadata.version / metadata.description per official schema."

  5. **Staged file check** (`--staged`):
     - Check if marketplace.json or any plugin source files are staged in git
     - Verify that version bumps are present when skill/plugin content changed
     - Replaces `detect_version_changes.py --check-staged` and `marketplace_ci.py check-staged`
     - Used by pre-commit hook

  6. **Structure check** (`--check-structure`):
     - Detect anti-patterns: multiple plugins sharing `source: "./"`
     - Group plugins by resolved version source, warn on conflicts
     - Replaces `detect_version_changes.py --check-structure` and `marketplace_ci.py structure-check`

  **CLI interface:**
  ```
  python3 validate.py [path-to-marketplace.json] [--fix] [--format text|json] [--staged] [--check-structure]
  ```

  **Design principles:**
  - Try `import yaml` for robust frontmatter parsing, fall back to stdlib subset parser (see YAML Frontmatter Parsing Strategy above)
  - Single file, no imports from other project scripts
  - Clean, readable output with actionable error messages
  - Exit code 0 on success (warnings OK), 1 on errors
  - Serves as both the repo's daily validator AND its CI script -- no separate marketplace_ci.py needed

  **Test scenarios:**
  - Validates a clean marketplace.json with all 6 organization patterns
  - Catches missing required fields, unknown fields, duplicate names
  - Warns on `skills` field without failing
  - `--fix` detects unregistered plugins under `plugins/`, `skills/`, `mcp-servers/`
  - `--fix` generates entries without `skills` field
  - `--format json` produces machine-readable output for CI
  - `--staged` detects version bump requirements on changed files
  - `--check-structure` catches shared `source: "./"` anti-pattern
  - Works with pyyaml available (robust parsing)
  - Works without pyyaml (stdlib fallback -- handles `metadata.version` nesting)

  **Verification:**
  - Running against jshanks/claude marketplace passes (with warnings for `skills` field)
  - Running against claude-skills marketplace passes cleanly
  - Running against claude-mp marketplace passes cleanly
  - Can replace `marketplace_ci.py validate`, `marketplace_ci.py version-check`, `marketplace_ci.py structure-check`, and `detect_version_changes.py --check-staged` in all CI pipelines

- [ ] **Unit 3: Write `sync.py` -- standalone version sync script**

  **Goal:** Create a clean, readable, stdlib-only version sync script that keeps marketplace.json plugin versions in sync with their source (plugin.json or SKILL.md frontmatter).

  **Requirements:** R4

  **Dependencies:** None

  **Files:**
  - Create: `plugins/marketplace-manager/skills/marketplace-manager/scripts/repo/sync.py`

  **Approach:**
  Write from scratch (~150 lines, stdlib-only). The script:

  1. Loads marketplace.json
  2. For each plugin with a relative source path:
     - Check for `.claude-plugin/plugin.json` -- if found and has `version`, use it
     - Otherwise scan for single skill: `skills/*/SKILL.md` -- extract version from YAML frontmatter
     - Compare source version with marketplace.json entry version
  3. Update marketplace.json with source versions where they differ
  4. Report what changed

  **CLI interface:**
  ```
  python3 sync.py [path-to-marketplace.json] [--dry-run]
  ```

  **Design principles:**
  - Same try-pyyaml-fallback-to-stdlib pattern as validate.py (each script contains its own copy of `parse_frontmatter()` -- both are standalone single-file scripts with no imports between them)
  - Single file, no imports from other project scripts
  - `--dry-run` shows what would change without writing
  - Handles both single-skill (auto mode) and multi-skill (warn-only) plugins

  **Test scenarios:**
  - Syncs version from plugin.json to marketplace.json
  - Falls back to SKILL.md frontmatter version for plugins without plugin.json
  - `--dry-run` shows changes without writing
  - Warns on multi-skill plugins where auto-sync is ambiguous

  **Verification:**
  - Running on claude-mp repo produces correct version sync

### Phase 3: Skill-Level Scripts (written from scratch)

- [ ] **Unit 4: Write `setup.py` -- marketplace repo initializer**

  **Goal:** Replace `add_to_marketplace.py init` and `install_hook.sh` logic with a single script that sets up a marketplace repo for self-sufficiency.

  **Requirements:** R4

  **Dependencies:** Units 2, 3

  **Files:**
  - Create: `plugins/marketplace-manager/skills/marketplace-manager/scripts/setup.py`

  **Approach:**
  Write from scratch (~200 lines). Subcommands:

  - `setup init` -- create `.claude-plugin/marketplace.json` with official schema fields (name, owner, plugins). Interactive prompts for name and owner.
  - `setup install-scripts` -- copy `validate.py` and `sync.py` from the marketplace-manager plugin into the target repo's `scripts/` directory. These become the repo's own self-sufficient scripts.
  - `setup install-hook` -- install a pre-commit hook that runs `python3 scripts/validate.py && python3 scripts/sync.py`
  - `setup all` -- runs init + install-scripts + install-hook in sequence

  **Key design:** After `setup all`, the marketplace repo is fully self-sufficient. It has its own validation, its own sync, its own pre-commit hook. No runtime dependency on marketplace-manager.

  **CLI interface:**
  ```
  python3 setup.py init [--name NAME] [--owner-name NAME] [--owner-email EMAIL]
  python3 setup.py install-scripts [--target-dir ./scripts]
  python3 setup.py install-hook [--dry-run]
  python3 setup.py all [--name NAME] [--owner-name NAME]
  ```

  **Test scenarios:**
  - `setup init` creates valid marketplace.json per official schema
  - `setup install-scripts` copies validate.py and sync.py to target repo
  - `setup install-hook` creates a working pre-commit hook
  - `setup all` produces a fully self-sufficient marketplace repo

  **Verification:**
  - A fresh directory after `setup all` can run `python3 scripts/validate.py` successfully

- [ ] **Unit 5: Write `scaffold.py` -- plugin creator and migrator**

  **Goal:** Replace `create_plugin.py` and `migrate_to_plugin.py` with a clean script that creates plugins using the official Anthropic directory structure.

  **Requirements:** R4

  **Dependencies:** None

  **Files:**
  - Create: `plugins/marketplace-manager/skills/marketplace-manager/scripts/scaffold.py`

  **Approach:**
  Write from scratch (~250 lines). Subcommands:

  - `scaffold create <name>` -- create a new plugin with official structure:
    ```
    plugins/<name>/
    +-- .claude-plugin/
    |   +-- plugin.json      # { "name": "<name>", "version": "1.0.0" }
    +-- skills/
        +-- <name>/
            +-- SKILL.md     # template with frontmatter
    ```
    Optional flags: `--description`, `--no-plugin-json` (rely on auto-discovery), `--with-commands`, `--with-agents`, `--with-mcp`
  - `scaffold migrate <skill-path>` -- move a legacy flat skill into plugin structure:
    - `git mv skills/<name>/ plugins/<name>/skills/<name>/`
    - Create `.claude-plugin/plugin.json` from SKILL.md metadata
    - Update marketplace.json source path
    - `--dry-run` to preview

  **CLI interface:**
  ```
  python3 scaffold.py create my-plugin --description "Does things"
  python3 scaffold.py create my-plugin --with-commands --with-agents
  python3 scaffold.py migrate skills/old-skill --dry-run
  ```

  **Test scenarios:**
  - `scaffold create` produces official Anthropic directory structure
  - `scaffold create --with-commands` adds `commands/` directory
  - `scaffold create --with-mcp` adds `.mcp.json` template
  - `scaffold create --no-plugin-json` omits plugin.json (auto-discovery only)
  - `scaffold migrate --dry-run` shows planned changes

  **Verification:**
  - Created plugins are discoverable by Claude Code auto-discovery

### Phase 4: Cleanup and Integration

- [ ] **Unit 6: Delete old scripts and update all references**

  **Goal:** Remove all 12 obsolete scripts and update SKILL.md, commands, README, and plugin.json

  **Requirements:** R5

  **Dependencies:** Units 2-5

  **Files:**
  - Delete: `scripts/add_to_marketplace.py`
  - Delete: `scripts/marketplace_ci.py`
  - Delete: `scripts/detect_version_changes.py`
  - Delete: `scripts/migrate_to_plugin.py`
  - Delete: `scripts/sync_marketplace_versions.py`
  - Delete: `scripts/create_plugin.py`
  - Delete: `scripts/analyze_bundling.py`
  - Delete: `scripts/deprecate_skill.py`
  - Delete: `scripts/sync_readme.py`
  - Delete: `scripts/validate_hook.py`
  - Delete: `scripts/utils.py`
  - Delete: `scripts/install_hook.sh`
  - Delete: `scripts/pre-commit.template` (replaced by hook content generated inline by `setup.py install-hook`)
  - Delete: `scripts/__pycache__/`
  - Modify: `plugins/marketplace-manager/skills/marketplace-manager/SKILL.md`
  - Modify: `plugins/marketplace-manager/commands/mp-sync.md`
  - Modify: `plugins/marketplace-manager/commands/mp-validate.md`
  - Modify: `plugins/marketplace-manager/commands/mp-add.md`
  - Modify: `plugins/marketplace-manager/commands/mp-list.md`
  - Modify: `plugins/marketplace-manager/commands/mp-status.md`
  - Modify: `plugins/marketplace-manager/README.md`
  - Modify: `plugins/marketplace-manager/.claude-plugin/plugin.json` (version bump to 4.0.0)

  **Approach:**
  - Rewrite SKILL.md with new script architecture:
    - Repo-level scripts (validate.py, sync.py) -- installed into marketplace repos by `setup.py`
    - Skill-level scripts (setup.py, scaffold.py) -- used by the skill directly
    - New section explaining the self-sufficient marketplace repo model
    - Document try-pyyaml-fallback-to-stdlib frontmatter parsing
  - Update slash commands to reference new script names
  - Bump plugin version: 3.1.0 -> 4.0.0 (breaking: `skills` field removed from generation, all scripts replaced, marketplace_ci.py eliminated)
  - Update README with new script inventory, official schema note, setup workflow, and CI integration guide (use validate.py directly in CI pipelines)

  **Test scenarios:**
  - All script paths in SKILL.md and commands point to files that exist
  - Version in plugin.json matches SKILL.md metadata.version
  - No references to deleted script names remain in any file

  **Verification:**
  - All 5 slash commands work with new script paths
  - `setup.py all` on a fresh repo produces a working marketplace
  - Pre-commit hook works with repo-local scripts

### Phase 5: Validation

- [ ] **Unit 7: Run skillsmith evaluation and fix any issues**

  **Goal:** Verify the marketplace-manager skill passes skillsmith evaluation after all changes, ensuring SKILL.md quality, reference doc consistency, script path accuracy, and description triggering effectiveness

  **Requirements:** R7

  **Dependencies:** Unit 6

  **Files:**
  - Possibly modify: `plugins/marketplace-manager/skills/marketplace-manager/SKILL.md`
  - Possibly modify: reference docs if evaluation surfaces issues

  **Approach:**
  Run the full skillsmith evaluation pipeline:

  1. **Evaluate** -- run `uv run scripts/evaluate_skill.py plugins/marketplace-manager/skills/marketplace-manager/` to get baseline scores after the refactor
  2. **Check for regressions** -- compare against the pre-refactor scores (conciseness: 100, complexity: 90, spec_compliance: 90, progressive: 100, overall: 95)
  3. **Fix issues found** -- common post-refactor problems:
     - Stale file references in SKILL.md pointing to deleted scripts
     - SKILL.md line count or token budget violations after rewrite
     - Reference doc cross-references pointing to removed sections
     - Description no longer matching the skill's actual capabilities (e.g., if marketplace_ci.py is mentioned in description triggers)
  4. **Run `--explain`** -- use `uv run scripts/evaluate_skill.py --explain` to surface any over/under-triggering in the description after the refactor
  5. **Verify reference file loading** -- ensure all references listed in SKILL.md still exist and load correctly
  6. **Update metadata scores** -- update SKILL.md frontmatter `metadata` section with new evaluation scores and `last_evaluated` date

  **Specific things to verify:**
  - SKILL.md description no longer mentions `marketplace_ci.py`, `detect_version_changes.py`, or other deleted scripts as triggers
  - SKILL.md description adds triggers for the new architecture: "setup marketplace repo", "install repo scripts", "scaffold plugin", "auto-fix marketplace"
  - References to `references/plugin_marketplace_guide.md` still resolve (file was modified, not deleted)
  - The `compatibility` field still makes sense ("Requires git repository with .claude-plugin/marketplace.json")
  - SKILL.md body stays under 500 lines and 5k tokens after rewrite
  - No broken script paths in SKILL.md code blocks
  - CI example reference files (`references/ci-example-gitlab-ci.yml`, `references/ci-example-github-actions.yml`) are updated to use `validate.py` instead of `marketplace_ci.py`

  **Test scenarios:**
  - `evaluate_skill.py` produces overall score >= 90 (no regression from current 95)
  - `evaluate_skill.py --explain` shows no critical issues
  - All file references in SKILL.md resolve to files that exist
  - Description triggers correctly match the refactored skill's capabilities

  **Verification:**
  - Evaluation passes with no errors
  - Scores are updated in SKILL.md frontmatter metadata
  - `last_evaluated` date is set to today

## System-Wide Impact

- **Slash commands**: All 5 commands (`/mp-sync`, `/mp-validate`, `/mp-add`, `/mp-list`, `/mp-status`) need updated to reference new scripts
- **Pre-commit hook**: Changes from calling skill-level scripts to calling repo-local `scripts/validate.py` + `scripts/sync.py`. Existing repos need `setup.py install-hook` to update.
- **CI pipelines**: Any pipeline using `marketplace_ci.py` must migrate to `validate.py --format json`. The flags map cleanly: `marketplace_ci.py validate` -> `validate.py`, `marketplace_ci.py version-check` -> `sync.py --dry-run`, `marketplace_ci.py structure-check` -> `validate.py --check-structure`.
- **Self-sufficiency model**: After this change, marketplace repos own their validation and sync logic. Updating marketplace-manager only matters for setup/scaffold operations, not daily validation.
- **Backward compatibility**: Existing marketplace.json files with `skills` arrays get warnings, not errors. No forced migration.
- **Other skills**: skillsmith delegates to marketplace-manager -- slash command names don't change, only backing scripts
- **Repo-level script updates**: When validate.py or sync.py are improved in marketplace-manager, repos that already copied them won't auto-update. This is an intentional tradeoff -- self-sufficiency over auto-update. Users can re-run `setup.py install-scripts` to get the latest.

## Risks & Dependencies

- **Risk**: Users who reference old script names (`marketplace_ci.py`, `add_to_marketplace.py`, etc.) in CI pipelines will break. **Mitigation**: Document migration path in README and CHANGELOG with flag mapping table. The version bump (3.1.0 -> 4.0.0) signals a breaking change.
- **Risk**: Pre-commit hooks in external repos reference old script paths. **Mitigation**: `setup.py install-hook` updates the hook.
- **Risk**: Repo-local validate.py/sync.py copies diverge from the latest in marketplace-manager over time. **Mitigation**: This is the intended tradeoff. Scripts are simple enough (~300 + ~180 lines) that divergence is manageable. Users can re-run `setup.py install-scripts` to update.
- **Risk**: pyyaml unavailable in some CI containers, falling back to stdlib subset parser. **Mitigation**: The fallback parser handles the subset we actually use (flat keys + one nesting level). Version strings are always simple `key: value` -- never multi-line, never anchored. The fallback is sufficient for this use case.

## Sources & References

- **Official marketplace guide**: https://docs.anthropic.com/en/docs/claude-code/plugin-marketplaces (marketplace.json schema, source types, strict mode, pluginRoot)
- **Official plugins guide**: https://docs.anthropic.com/en/docs/claude-code/plugins (plugin creation walkthrough, directory structure, auto-discovery)
- **Official plugins reference**: https://code.claude.com/docs/en/plugins-reference (plugin.json schema — optional manifest, only `name` required if present)
- **Official skills reference**: https://code.claude.com/docs/en/skills (SKILL.md frontmatter, skill discovery, monorepo support)
- **Official marketplace JSON schema**: https://anthropic.com/claude-code/marketplace.schema.json (formal schema — note: URL returns 404 but is the conventional reference)
- **jshanks/claude validate_marketplace.py**: `/Users/gregwilliams/Documents/PAN_Projects/jshanks-claude/validate_marketplace.py` (reverse scan + auto-fix pattern)
- Related plan: `docs/plans/2026-03-23-001-feat-multi-plugin-marketplace-support-plan.md` (complementary -- structure detection for shared source paths)
- Related plan: `docs/plans/2026-03-02-fix-marketplace-plugin-json-schema-validation-plan.md` (plugin.json validation -- already implemented)
- Related plan: `docs/plans/2026-03-19-001-feat-marketplace-manager-external-repo-support-plan.md` (external repo hook support -- completed)
