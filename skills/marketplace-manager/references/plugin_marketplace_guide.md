# Plugins reference

Claude's plugin system allows you to extend its functionality with custom commands, agents, skills, and more. This document provides a technical reference for creating and managing plugins.

## Plugin Components

A plugin can contain one or more of the following components:

- **Commands:** Custom actions that can be invoked from the chat interface.
- **Agents:** Autonomous agents that can perform tasks in the background.
- **Skills:** Collections of related commands and agents that provide a specific functionality.
- **Hooks:** Scripts that are executed at specific points in the application's lifecycle.
- **MCP Servers:** Multi-context-passing servers that can be used to communicate with external services.
- **LSP Servers:** Language Server Protocol servers that can be used to provide language-specific features.

## Installation Scopes

Plugins can be installed at two different scopes:

- **User:** The plugin is available only to the current user.
- **Project:** The plugin is available to all users of the current project.

The installation scope is determined by the location of the plugin's manifest file.

- **User-scoped plugins** are installed in `~/.claude/plugins/`.
- **Project-scoped plugins** are installed in `.claude/plugins/` at the root of the project.

## Plugin Manifest

Every plugin must have a `plugin.json` manifest file at its root. This file contains metadata about the plugin, such as its name, version, and a list of its components.

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "A brief description of my plugin.",
  "author": "Your Name",
  "components": {
    "commands": ["commands/my-command.json"],
    "agents": ["agents/my-agent.json"],
    "skills": ["skills/my-skill.json"],
    "hooks": ["hooks/my-hook.json"],
    "mcp_servers": ["mcp-servers/my-mcp-server.json"],
    "lsp_servers": ["lsp-servers/my-lsp-server.json"]
  }
}
```

## Caching

To improve performance, Claude caches the components of installed plugins. The cache is located at `~/.claude/cache/`.

To clear the cache, run the following command:

```bash
/claude clear-cache
```

## Directory Structure

The recommended directory structure for a plugin is as follows:

```
my-plugin/
├── plugin.json
├── commands/
│   └── my-command.json
├── agents/
│   └── my-agent.json
├── skills/
│   └── my-skill.json
├── hooks/
│   └── my-hook.json
├── mcp-servers/
│   └── my-mcp-server.json
└── lsp-servers/
    └── my-lsp-server.json
```

## CLI Commands

The following CLI commands are available for managing plugins:

- `/plugin install <plugin-name>`: Installs a plugin from the marketplace.
- `/plugin uninstall <plugin-name>`: Uninstalls a plugin.
- `/plugin list`: Lists all installed plugins.
- `/plugin status <plugin-name>`: Shows the status of a plugin.
- `/plugin marketplace add <url>`: Adds a new marketplace.
- `/plugin marketplace remove <url>`: Removes a marketplace.
- `/plugin marketplace list`: Lists all configured marketplaces.

## Debugging

To debug a plugin, you can use the following tools:

- **Log files:** Log files for plugins are located in `~/.claude/logs/`.
- **Developer tools:** You can open the developer tools by pressing `Ctrl+Shift+I` (or `Cmd+Option+I` on macOS).

## Distribution and Versioning

Plugins can be distributed through a marketplace or by sharing the plugin's source code directly.

When publishing a plugin to a marketplace, it is recommended to use semantic versioning to indicate the nature of changes between versions.

### Semantic Versioning

Use semantic versioning (MAJOR.MINOR.PATCH) for both skills and plugins:
- **MAJOR** - Breaking changes that require user action
- **MINOR** - New features that are backward-compatible
- **PATCH** - Bug fixes that are backward-compatible

Examples:
- `1.0.0` → `1.1.0` - Added new skill to plugin
- `1.1.0` → `1.1.1` - Fixed bug in existing skill
- `1.1.1` → `2.0.0` - Removed skill or introduced breaking change

### Plugin Versioning Strategies

**Single-Component Plugins (Recommended)**
- Plugin contains one skill/component only
- Plugin version automatically matches component version
- Simple, clear, no versioning conflicts
- Use sync script in auto mode (default)

Example:
```json
{
  "name": "terminal-guru",
  "version": "2.0.0",
  "skills": ["./skills/terminal-guru"]
}
```
If terminal-guru skill updates to 2.1.0, plugin auto-updates to 2.1.0

**Multi-Component Plugins (Manual Versioning Required)**
- Plugin contains multiple skills, MCP servers, LSP servers, hooks, or agents
- Plugin version independent from component versions
- Developer manually bumps plugin version when any component changes
- Use sync script in manual mode (`--mode=manual`)

Example problem with auto-versioning:
```
Plugin v1.5.0 contains:
  - skill-a: v1.5.0
  - skill-b: v1.2.0

Developer updates skill-b to v1.3.0
Auto-sync would leave plugin at v1.5.0 = no update signal!
```

**Manual versioning workflow:**
1. Update component version in its SKILL.md
2. Run: `python3 scripts/sync_marketplace_versions.py --mode=manual`
3. Script warns about version mismatch
4. Manually update plugin version in marketplace.json based on impact:
   - **MAJOR**: Any component has breaking changes
   - **MINOR**: Any component adds new features
   - **PATCH**: All components only have bug fixes
5. Commit all changes together

**Best Practice:** Use single-component plugins whenever possible. Only use multi-component plugins for tightly coupled components that are always used together.