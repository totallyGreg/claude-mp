# Claude Marketplace (claude-mp)

A comprehensive marketplace for Claude Code extensions, providing plugins with skills, commands, agents, hooks, and MCP servers to enhance your Claude development experience.

## Quick Start

### Installing from the Marketplace

```bash
# Add the marketplace
/plugin marketplace add totallyGreg/claude-mp

# Install individual plugins
/plugin install foundry@totally-tools
/plugin install terminal-guru@totally-tools
```

## Available Plugins

### Development (6 plugins)

| Plugin | Version | Description |
|--------|---------|-------------|
| **terminal-guru** | 5.13.0 | Terminal diagnostics, tool composition, workflow discovery, and multi-Claude tmux orchestration — triage agent routing to seven skills across the terminal stack (terminal-emulation, zsh-dev, tmux-dev, tui-experience, signals-monitoring, environment-composition, mise-tooling) |
| **helm-chart-developer** | 2.0.0 | Expert guide for Helm chart development, testing, and security |
| **foundry** | 1.6.0 | Plugin development lifecycle toolkit — evaluate, improve, and publish skills and agents. Consolidates skillsmith, marketplace-manager, and agentsmith. |
| **swift-dev** | 1.2.0 | Swift development expert for SwiftUI, iOS/macOS frameworks, Server-side Swift, and Objective-C migration |
| **chronicle** | 0.1.0 | Opinionated guidance for managing change across documents, code, and experiments. Covers git (primary), jujutsu, and historical VCS tools with strong opinions on commit craft, branching, merge strategy, and multi-agent worktree workflows. |
| **handoff** | 0.3.0 | Hand off work to another Claude — teammate via SendMessage, tmux pane via send-keys, clipboard, or file. Structured Markdown payload with goal, state, decisions, and next steps. |

### Productivity (4 plugins)

| Plugin | Version | Description |
|--------|---------|-------------|
| **archivist** | 1.28.0 | Personal Knowledge Management expert for Obsidian vaults with dual-skill architecture: vault-architect (create structures) and vault-curator (evolve content) |
| **attache** | 12.1.2 | Chief of Staff agent — personal advisor that orchestrates task management, delegates to specialist agents, learns workflow patterns, and manages the full tool stack |
| **confluence-pages** | 1.1.0 | Create, update, move, and delete Confluence pages via REST API |
| **slack-toolkit** | 1.5.1 | Slack Web API access via Python CLI — Canvas read/create/update/rewrite, reactions, threads, and channel history without MCP dependency |

### Security (1 plugin)

| Plugin | Version | Description |
|--------|---------|-------------|
| **ai-risk-mapper** | 5.2.2 | AI security risk assessment using CoSAI Risk Map framework |

### Infrastructure (1 plugin)

| Plugin | Version | Description |
|--------|---------|-------------|
| **gateway-manager** | 3.0.0 | Multi-skill plugin for Kubernetes Gateway API (kgateway) and AI/LLM routing (agentgateway) — provider backends, MCP server routing, external processing, version lifecycle management, and traffic policies |

## Repository Structure

```
claude-mp/
├── plugins/                 # All plugins (each self-contained: skills, commands, agents, hooks)
│   ├── foundry/             # Plugin dev lifecycle (skillsmith + marketplace-manager + agentsmith)
│   ├── terminal-guru/       # Terminal stack diagnostics + composition (7 skills)
│   ├── gateway-manager/     # Gateway configuration (kgateway + agentgateway)
│   ├── archivist/           # Obsidian PKM (vault-architect + vault-curator)
│   ├── attache/             # Chief of Staff task orchestration
│   ├── chronicle/           # Change management across git/jujutsu
│   ├── handoff/             # Work handoff between Claudes
│   └── …                    # helm-chart-developer, swift-dev, confluence-pages,
│                            #   slack-toolkit, ai-risk-mapper
├── scripts/                 # Repo-level validate.py + sync.py (from marketplace-manager)
├── docs/                    # plans/ (ephemeral planning) + lessons/ (cross-skill learnings)
└── .claude-plugin/          # marketplace.json — source of truth for the plugin catalog
```

## Standalone Plugins

Several plugins include slash commands for common operations:

### foundry Commands
Skill lifecycle: `/ss-init`, `/ss-validate`, `/ss-evaluate`, `/ss-research`, `/ss-improve`, `/ss-observe`, `/ss-refresh`, `/ss-package`, `/ss-wtf`
Agent lifecycle: `/as-evaluate`, `/as-improve`
Marketplace: `/mp-sync`, `/mp-validate`, `/mp-add`, `/mp-list`, `/mp-status`

### terminal-guru Commands
- `/team-spawn` - Spawn a persistent teammate agent (enforces the `name` field)
- `/team-list` - List active teammates in the session
- `/workflow-discover` - Scan history, brew, XDG configs, and git log for workflow patterns

### gateway-manager Commands
- `/gw-status` - Check gateway status
- `/gw-logs` - View gateway logs
- `/gw-debug` - Debug gateway issues
- `/gw-backend` - Configure backends
- `/gw-route` - Manage routes
- `/gw-upgrade` - Plan a chart upgrade
- `/gw-versions` - Compare installed vs latest versions

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
