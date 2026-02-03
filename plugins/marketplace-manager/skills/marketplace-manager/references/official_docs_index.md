# Official Claude Code Documentation

## Overview

This document provides links to official Anthropic documentation for Claude Code plugins and marketplaces. Always consult these sources for the most current specifications.

## Official Documentation URLs

### Plugin Marketplaces

**URL**: https://code.claude.com/docs/en/plugin-marketplaces

Documentation covering:
- Marketplace creation and hosting
- `marketplace.json` structure and fields
- Publishing plugins to marketplaces
- Installing from marketplaces

### Plugins Reference

**URL**: https://code.claude.com/docs/en/plugins-reference

Documentation covering:
- Plugin manifest (`plugin.json`) specification
- Plugin components (commands, agents, skills, hooks, MCP servers, LSP servers)
- Installation scopes (user vs project)
- Plugin directory structure
- Component auto-discovery

### Marketplace Schema

**URL**: https://anthropic.com/claude-code/marketplace.schema.json

The official JSON Schema for validating `marketplace.json` files. Use with JSON schema validators for automated compliance checking.

## Quick Reference

| Topic | URL |
|-------|-----|
| Marketplace docs | https://code.claude.com/docs/en/plugin-marketplaces |
| Plugin reference | https://code.claude.com/docs/en/plugins-reference |
| Marketplace schema | https://anthropic.com/claude-code/marketplace.schema.json |

## Usage

When building or validating marketplace plugins:

1. **Marketplace structure**: Consult plugin-marketplaces docs
2. **Plugin manifest**: Consult plugins-reference docs
3. **Schema validation**: Use marketplace.schema.json for automated checks

## See Also

- `plugin_marketplace_guide.md` - Practical guide with examples
- `marketplace_distribution_guide.md` - Distribution workflow
- `troubleshooting.md` - Common issues and solutions
