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

### Development (5 plugins)

| Plugin | Version | Description |
|--------|---------|-------------|
| **helm-chart-developer** | 1.0.0 | Expert guide for Helm chart development, testing, and security |
| **marketplace-manager** | 2.9.0 | Manages Claude Code plugin marketplace operations including version syncing, skill publishing, and marketplace.json maintenance |
| **skillsmith** | 6.6.0 | Guide for forging effective Claude skills with marketplace integration |
| **swift-dev** | 1.2.0 | Swift development expert for SwiftUI, iOS/macOS frameworks, Server-side Swift, and Objective-C migration |
| **terminal-guru** | 4.0.0 | Terminal diagnostics, configuration, and zsh development expert with triage agent and three focused skills |

### Productivity (3 plugins)

| Plugin | Version | Description |
|--------|---------|-------------|
| **confluence-pages** | 1.1.0 | Create, update, move, and delete Confluence pages via REST API |
| **omnifocus-manager** | 10.2.0 | Interface with OmniFocus to surface insights, create reusable automations and perspectives, and suggest workflow optimizations |
| **pkm-plugin** | 1.9.0 | Personal Knowledge Management expert for Obsidian vaults with dual-skill architecture: vault-architect (create structures) and vault-curator (evolve content) |

### Security (1 plugin)

| Plugin | Version | Description |
|--------|---------|-------------|
| **ai-risk-mapper** | 5.1.0 | AI security risk assessment using CoSAI Risk Map framework |

### Infrastructure (1 plugin)

| Plugin | Version | Description |
|--------|---------|-------------|
| **gateway-manager** | 3.0.0 | Multi-skill plugin for Kubernetes Gateway API (kgateway) and AI/LLM routing (agentgateway) — provider backends, MCP server routing, external processing, version lifecycle management, and traffic policies |

## Repository Structure

```
claude-mp/
├── plugins/                 # Standalone plugins with commands
│   ├── skillsmith/          # Skill creation and validation
│   ├── marketplace-manager/ # Marketplace operations
│   └── gateway-manager/      # Gateway configuration (kgateway + agentgateway)
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
- `/mp-sync` - Sync versions to marketplace.json and README.md
- `/mp-validate` - Validate marketplace structure
- `/mp-add` - Add skill or create plugin
- `/mp-list` - List marketplace plugins
- `/mp-status` - Show version mismatches

### gateway-manager Commands
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
