# Plugin Marketplace Guide

Technical reference for Claude Code plugin marketplaces. All schema details are sourced from official Anthropic documentation with URLs cited inline.

---

## Official Sources

| Source | URL |
|--------|-----|
| Marketplace guide | https://docs.anthropic.com/en/docs/claude-code/plugin-marketplaces |
| Plugins guide | https://docs.anthropic.com/en/docs/claude-code/plugins |
| Plugins reference | https://code.claude.com/docs/en/plugins-reference |
| Skills reference | https://code.claude.com/docs/en/skills |

---

## marketplace.json Schema

Source: https://docs.anthropic.com/en/docs/claude-code/plugin-marketplaces

### Required Root Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Marketplace identifier (kebab-case) |
| `owner` | object | Maintainer info (`name` required, `email` optional) |
| `plugins` | array | List of available plugins |

### Optional Root Metadata

| Field | Type | Description |
|-------|------|-------------|
| `metadata.description` | string | Brief marketplace description |
| `metadata.version` | string | Marketplace version |
| `metadata.pluginRoot` | string | Base directory prepended to relative source paths |

### Required Plugin Entry Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Plugin identifier (kebab-case) |
| `source` | string or object | Where to fetch the plugin |

### Optional Plugin Entry Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Brief plugin description |
| `version` | string | Plugin version (semver) |
| `author` | object | Author info |
| `homepage` | string | Documentation URL |
| `repository` | string | Source code URL |
| `license` | string | SPDX identifier |
| `keywords` | array | Discovery tags |
| `category` | string | Organization category |
| `tags` | array | Searchability tags |
| `strict` | boolean | Whether plugin.json is authority for components (default: true) |

### Component Configuration Fields

These fields can appear in plugin entries to specify custom component paths or inline configurations.

Source: https://docs.anthropic.com/en/docs/claude-code/plugin-marketplaces

| Field | Type | Description |
|-------|------|-------------|
| `commands` | string or array | Custom paths to command files or directories |
| `agents` | string or array | Custom paths to agent files |
| `hooks` | string or object | Custom hooks configuration or path to hooks file |
| `mcpServers` | string or object | MCP server configurations or path to MCP config |
| `lspServers` | string or object | LSP server configurations or path to LSP config |

### Fields NOT in the Official Schema

The following are **not** part of the official marketplace.json schema:

- `skills` (as a plugin entry field) -- Claude Code auto-discovers skills from `skills/*/SKILL.md`
- `components` -- there is no `components` wrapper object
- `metadata` at the plugin entry level -- `metadata` is a root-level field only

---

## plugin.json (Plugin Manifest)

Source: https://code.claude.com/docs/en/plugins-reference

The plugin manifest (`plugin.json` inside `.claude-plugin/`) is **optional**. If omitted, Claude Code auto-discovers components in default locations and derives the plugin name from the directory name.

If present, **only `name` is required**. All other fields are optional.

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Brief description of plugin purpose"
}
```

Use a manifest when you need to set version, description, author, license, or custom component paths. For simple single-skill plugins, omitting `plugin.json` entirely is valid.

---

## Component Auto-Discovery

Source: https://docs.anthropic.com/en/docs/claude-code/plugins

Claude Code auto-discovers components by scanning well-known directories inside the plugin root:

| Directory/File | What It Finds | Discovery Pattern |
|----------------|---------------|-------------------|
| `commands/` | Slash commands | `*.md` files |
| `agents/` | Custom agents | `*.md` files |
| `skills/` | Agent skills | `*/SKILL.md` subdirectories |
| `hooks/` | Event handlers | `hooks.json` |
| `.mcp.json` | MCP servers | JSON config at plugin root |
| `.lsp.json` | LSP servers | JSON config at plugin root |
| `settings.json` | Default settings | JSON config at plugin root |

**Important:** Do not put `commands/`, `agents/`, `skills/`, or `hooks/` inside `.claude-plugin/`. Only `plugin.json` goes inside `.claude-plugin/`. All other directories must be at the plugin root level.

Source: https://docs.anthropic.com/en/docs/claude-code/plugins#plugin-structure-overview

---

## `strict` Mode

Source: https://docs.anthropic.com/en/docs/claude-code/plugin-marketplaces, https://code.claude.com/docs/en/plugins-reference

| Value | Behavior |
|-------|----------|
| `true` (default) | The plugin has its own `plugin.json` and manages its own components. The marketplace entry can add extra commands or hooks on top -- both sources are merged. |
| `false` | The plugin does not need its own `plugin.json`. The marketplace entry defines everything. If the plugin also has a `plugin.json` that declares components, that is a conflict and the plugin fails to load. |

Use `strict: false` when the marketplace entry should be the sole authority for component declarations.

---

## Path Variables

Source: https://docs.anthropic.com/en/docs/claude-code/plugin-marketplaces

| Variable | Description |
|----------|-------------|
| `${CLAUDE_PLUGIN_ROOT}` | The plugin's installation directory (required because plugins are copied to a cache) |
| `${CLAUDE_PLUGIN_DATA}` | Persistent state directory that survives plugin updates |

Use these in hook commands, MCP server configs, and other paths that need to reference plugin files at runtime.

---

## `metadata.pluginRoot`

Source: https://docs.anthropic.com/en/docs/claude-code/plugin-marketplaces

Base directory prepended to relative plugin source paths. For example, `"pluginRoot": "./plugins"` lets you write `"source": "formatter"` instead of `"source": "./plugins/formatter"`.

### Path Resolution

Paths resolve relative to the marketplace root -- the directory containing `.claude-plugin/`. So `./plugins/my-plugin` points to `<repo>/plugins/my-plugin`, even though `marketplace.json` lives at `<repo>/.claude-plugin/marketplace.json`. Do not use `../` to escape `.claude-plugin/`.

---

## Marketplace Organization Patterns

All patterns below are derived from official Anthropic documentation. Each shows directory structure, marketplace.json snippet, and when to use.

### Pattern 1: Single Plugin, Single Skill (simplest)

One plugin with one skill. `plugin.json` is optional -- if omitted, Claude Code auto-discovers components and derives the plugin name from the directory name.

```
my-marketplace/
+-- .claude-plugin/
|   +-- marketplace.json
+-- plugins/
    +-- my-plugin/
        +-- .claude-plugin/
        |   +-- plugin.json        # optional
        +-- skills/
            +-- my-skill/
                +-- SKILL.md       # auto-discovered
```

```json
{
  "name": "my-marketplace",
  "owner": { "name": "Dev Team" },
  "plugins": [
    { "name": "my-plugin", "source": "./plugins/my-plugin" }
  ]
}
```

**When to use:** Most common case. One focused plugin, one skill. Simple version management.

### Pattern 2: Single Plugin, Multiple Skills (bundle)

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
        |   |   +-- SKILL.md
        |   +-- zsh-dev/
        |   |   +-- SKILL.md
        |   +-- signals-monitoring/
        |       +-- SKILL.md
        +-- commands/
        |   +-- diagnose.md
        +-- agents/
            +-- terminal-guru.md
```

```json
{
  "name": "terminal-marketplace",
  "owner": { "name": "Terminal Team" },
  "plugins": [
    { "name": "terminal-guru", "source": "./plugins/terminal-guru", "version": "2.0.0" }
  ]
}
```

**When to use:** Tightly coupled skills that always ship together. Commands and agents complement the skills. Plugin version is independent from individual skill versions; manual version management required.

### Pattern 3: Multiple Independent Plugins

Multiple independent plugins in one marketplace repo. Each has its own `plugin.json`. Users install selectively.

```
my-marketplace/
+-- .claude-plugin/
|   +-- marketplace.json
+-- plugins/
    +-- formatter/
    |   +-- .claude-plugin/
    |   |   +-- plugin.json
    |   +-- skills/
    |       +-- code-format/
    |           +-- SKILL.md
    +-- deployer/
    |   +-- .claude-plugin/
    |   |   +-- plugin.json
    |   +-- skills/
    |   |   +-- deploy/
    |   |       +-- SKILL.md
    |   +-- commands/
    |       +-- deploy-status.md
    +-- linter/
        +-- .claude-plugin/
        |   +-- plugin.json
        +-- skills/
            +-- lint-check/
                +-- SKILL.md
```

```json
{
  "name": "devtools-marketplace",
  "owner": { "name": "DevTools Team" },
  "plugins": [
    { "name": "formatter", "source": "./plugins/formatter", "version": "2.1.0" },
    { "name": "deployer", "source": "./plugins/deployer", "version": "1.0.0" },
    { "name": "linter", "source": "./plugins/linter", "version": "1.3.0" }
  ]
}
```

**When to use:** A team publishes multiple unrelated plugins from one repo. Each plugin versions independently. Install with `/plugin install formatter@my-marketplace`.

### Pattern 4: Full-Featured Plugin (all component types)

A plugin using every available component type: commands, agents, skills, hooks, MCP servers, LSP servers, and settings.

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

The marketplace entry can specify custom component paths and inline configurations:

```json
{
  "name": "enterprise-marketplace",
  "owner": { "name": "Platform Team" },
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

**When to use:** Enterprise or complex plugins needing explicit component paths, inline hooks, or MCP server configs. Use `strict: false` when the marketplace entry is the sole authority (no `plugin.json` component declarations).

### Pattern 5: Using `pluginRoot` to Simplify Paths

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

### Pattern 6: External Source Types

Plugins do not have to live in the marketplace repo. The `source` field supports multiple external types.

Source: https://docs.anthropic.com/en/docs/claude-code/plugin-marketplaces

| Source Type | Example | Use Case |
|-------------|---------|----------|
| Relative path | `"./plugins/my-plugin"` | Plugin lives in marketplace repo |
| GitHub | `{ "source": "github", "repo": "owner/repo" }` | Plugin in a separate GitHub repo |
| Git URL | `{ "source": "url", "url": "https://gitlab.com/org/repo.git" }` | Any git host (GitLab, Bitbucket, etc.) |
| Git subdirectory | `{ "source": "git-subdir", "url": "owner/repo", "path": "tools/plugin" }` | Plugin in a monorepo subdirectory |
| npm | `{ "source": "npm", "package": "@org/plugin" }` | Published npm package |

All object source types support optional `ref` (branch/tag) and `sha` (pin to exact commit) fields.

**When to use:** Plugin maintained in a separate repository or published as an npm package.

### Pattern Selection Guide

| Scenario | Recommended Pattern |
|----------|---------------------|
| One plugin, one skill | Pattern 1 |
| One plugin, related skills that always ship together | Pattern 2 |
| Multiple independent plugins from one repo | Pattern 3 |
| Plugin with hooks, MCP servers, or LSP servers | Pattern 4 |
| Many plugins under shared directory | Pattern 5 (pluginRoot) |
| Plugin maintained in separate repo | Pattern 6 (external source) |
| Starting out, unsure of structure | Pattern 1; migrate to Pattern 2 or 3 later |

---

## Anti-Pattern: Shared `source: "./"` with Multiple Plugins

Do NOT list multiple independent plugins with `source: "./"`. All entries resolve to the same `.claude-plugin/plugin.json`, causing version enforcement conflicts.

```json
// WRONG -- all three resolve to the same plugin.json
{
  "plugins": [
    { "name": "plugin-a", "source": "./", "version": "1.0.0" },
    { "name": "plugin-b", "source": "./", "version": "1.0.0" },
    { "name": "plugin-c", "source": "./", "version": "1.0.0" }
  ]
}
```

**Fix:** Give each plugin its own directory under `plugins/` (Pattern 3).

---

## Convention vs Spec

The marketplace-manager skill adds conventions on top of the official spec. This section distinguishes them.

| Aspect | Official Spec | marketplace-manager Convention |
|--------|---------------|-------------------------------|
| `plugin.json` | Optional; only `name` required if present | Recommended for version tracking |
| Plugin entry fields | `name` and `source` required | Also expects `version` for sync |
| Version source | Not specified | SKILL.md `metadata.version` or `plugin.json` `version` |
| Version sync | Not specified | Auto-sync from source to marketplace.json |
| Pre-commit hooks | Not specified | Validates marketplace.json on commit |
| Plugin directory | Any path | Convention: `plugins/<name>/` |
| Kebab-case names | Required by spec | Enforced by validation |

The official spec defines **structure**. marketplace-manager adds **workflow** (version syncing, validation, scaffolding).

---

## Plugin Versioning

### Semantic Versioning

Use semver (MAJOR.MINOR.PATCH):
- **MAJOR** -- Breaking changes requiring user action
- **MINOR** -- New backward-compatible features
- **PATCH** -- Backward-compatible bug fixes

### Single-Skill Plugins (Recommended)

Plugin version matches skill version. Sync script auto-updates marketplace.json.

### Multi-Skill Plugins (Manual Versioning)

Plugin version is independent from individual skill versions. Developer manually bumps plugin version when any component changes.

**Best Practice:** Use single-skill plugins whenever possible. Only use multi-skill bundles for tightly coupled components.

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `/plugin install <name>` | Install a plugin from a marketplace |
| `/plugin uninstall <name>` | Uninstall a plugin |
| `/plugin list` | List installed plugins |
| `/plugin status <name>` | Show plugin status |
| `/plugin marketplace add <url>` | Add a marketplace |
| `/plugin marketplace remove <url>` | Remove a marketplace |
| `/plugin marketplace list` | List configured marketplaces |

---

*This reference is aligned with official Anthropic documentation as of 2026-03-26. Consult the source URLs above for the latest specifications.*
