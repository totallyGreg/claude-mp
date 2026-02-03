# Claude Marketplace (claude-mp)

A comprehensive marketplace for Claude Code extensions, providing plugins with skills, commands, agents, hooks, and MCP servers to enhance your Claude development experience.

## Quick Start

### Installing from the Marketplace

```bash
# Add the marketplace
/plugin marketplace add totallyGreg/claude-mp

# Install individual plugins
/plugin install skillsmith@totally-tools
/plugin install marketplace-manager@totally-tools
```

## Available Plugins

### Development (6 plugins)

| Plugin | Version | Description |
|--------|---------|-------------|
| **skillsmith** | 4.0.0 | Create, evaluate, and improve Claude skills with validation tools and slash commands |
| **marketplace-manager** | 2.0.0 | Manage marketplace operations including version syncing and plugin publishing |
| **terminal-guru** | 2.0.0 | Terminal diagnostics and configuration expert for Unix systems |
| **helm-chart-developer** | 1.0.0 | Helm chart development, testing, and security best practices |
| **swift-dev** | 1.2.0 | Swift/SwiftUI development for iOS/macOS with Objective-C migration |
| **gateway-proxy** | 1.0.0 | kgateway and agentgateway configuration for AI/LLM and MCP routing |

### Productivity (2 plugins)

| Plugin | Version | Description |
|--------|---------|-------------|
| **omnifocus-manager** | 4.4.0 | Query and manage OmniFocus tasks with automation and workflow optimization |
| **obsidian-pkm-manager** | 1.0.0 | Manage Obsidian-based Personal Knowledge Management systems |

### Security (1 plugin)

| Plugin | Version | Description |
|--------|---------|-------------|
| **ai-risk-mapper** | 3.0.1 | AI security risk assessment using CoSAI Risk Map framework |

## Repository Structure

```
claude-mp/
├── plugins/                 # Standalone plugins with commands
│   ├── skillsmith/          # Skill creation and validation
│   ├── marketplace-manager/ # Marketplace operations
│   └── gateway-proxy/       # Gateway configuration
├── skills/                  # Legacy skill-only plugins
│   ├── terminal-guru/
│   ├── helm-chart-developer/
│   ├── swift-dev/
│   ├── obsidian-pkm-manager/
│   ├── omnifocus-manager/
│   └── ai-risk-mapper/
├── commands/                # Shared commands
├── agents/                  # Specialized AI agents
├── hooks/                   # Event handlers
├── mcp-servers/             # MCP server integrations
└── .claude-plugin/          # Marketplace configuration
```

## Standalone Plugins

Standalone plugins include slash commands for common operations:

### skillsmith Commands
- `/ss-validate` - Quick skill validation
- `/ss-evaluate` - Full evaluation with metrics
- `/ss-init` - Initialize new skill from template
- `/ss-research` - Research skill improvements

### marketplace-manager Commands
- `/mp-sync` - Sync versions to marketplace.json
- `/mp-validate` - Validate marketplace structure
- `/mp-add` - Add skill or create plugin
- `/mp-list` - List marketplace plugins
- `/mp-status` - Show version mismatches

### gateway-proxy Commands
- `/gw-status` - Check gateway status
- `/gw-logs` - View gateway logs
- `/gw-debug` - Debug gateway issues
- `/gw-backend` - Configure backends
- `/gw-route` - Manage routes

## Contributing

Contributions are welcome! Whether you want to:

- Submit a new skill or plugin
- Report bugs or suggest improvements
- Improve documentation

Please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Contact

- **Author**: J. Greg Williams
- **Repository**: https://github.com/totallyGreg/claude-mp

---

**Note**: This is an independent community project and is not officially affiliated with Anthropic.
