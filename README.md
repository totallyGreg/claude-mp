# Claude Marketplace (claude-mp)

A comprehensive marketplace for Claude Code extensions, providing skills, commands, agents, hooks, and MCP servers to enhance your Claude development experience.

## 🚀 Quick Start

### Installing from the Marketplace

```bash
# Install all tools
claude marketplace add https://github.com/totallyGreg/claude-mp

# Or install individual skills
claude skill install totally-tools/terminal-guru
claude skill install totally-tools/helm-chart-developer
````

### What's Included

This marketplace currently includes:

#### 🛠️ Skills (3)

- **terminal-guru** (v2.0) - Terminal diagnostics, testing, and optimization with isolated environments
- **helm-chart-developer** - Helm chart development, testing, and security
- **skill-creator** - Guide for creating custom Claude skills

#### 📦 Coming Soon

- **Commands** - Custom slash commands for project workflows
- **Agents** - Specialized AI agents for autonomous tasks
- **Hooks** - Event handlers for automation
- **MCP Servers** - External tool integrations

## 📚 Documentation

### Skills

See [skills/README.md](./skills/README.md) for detailed information about available skills.

### Commands

See [commands/README.md](./commands/README.md) for custom command documentation.

### Agents

See [agents/README.md](./agents/README.md) for agent documentation.

### Hooks

See [hooks/README.md](./hooks/README.md) for hook documentation.

### MCP Servers

See [mcp-servers/README.md](./mcp-servers/README.md) for MCP server documentation.

## 🏗️ Repository Structure

```
claude-mp/
├── skills/              # Agent Skills for extended capabilities
├── commands/            # Custom slash commands
├── agents/             # Specialized AI agents
├── hooks/              # Event handlers
├── mcp-servers/        # MCP servers for external integrations
└── .claude-plugin/     # Marketplace configuration
```

## 🤝 Contributing

Contributions are welcome! Whether you want to:

- Submit a new skill, command, or agent
- Report bugs or suggest improvements
- Improve documentation

Please feel free to open an issue or submit a pull request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 🙏 Acknowledgments

- Built for [Claude Code](https://github.com/anthropics/claude-code)
- Inspired by the Anthropic skills repository
- Created and maintained by the totally-tools team

## 📧 Contact

- **Author**: J. Greg Williams
- **Email**: totallyGreg@gmail.com
- **Repository**: https://github.com/totallyGreg/claude-mp

---

**Note**: This is an independent community project and is not officially affiliated with Anthropic.
