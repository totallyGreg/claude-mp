# Official Claude Code Documentation Index

Links to official Anthropic documentation for Claude Code plugins and marketplaces. Always consult these sources for the most current specifications.

## Official Documentation URLs

### Plugin Marketplaces

**URL**: https://docs.anthropic.com/en/docs/claude-code/plugin-marketplaces

Covers:
- marketplace.json schema (required root fields, plugin entry fields, component configuration)
- Source types (relative path, GitHub, Git URL, git-subdir, npm)
- `strict` mode (true vs false)
- `metadata.pluginRoot` for path simplification
- Path resolution rules
- `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}` variables

### Plugins Guide

**URL**: https://docs.anthropic.com/en/docs/claude-code/plugins

Covers:
- Plugin creation walkthrough
- Plugin directory structure and component layout
- Component auto-discovery (commands/, agents/, skills/, hooks/, .mcp.json, .lsp.json)
- Installation scopes (user vs project)
- Plugin structure overview (what goes where)

### Plugins Reference

**URL**: https://code.claude.com/docs/en/plugins-reference

Covers:
- plugin.json manifest specification (optional; only `name` required if present)
- All plugin.json fields and their types
- Component configuration details
- `strict` mode behavior

### Skills Reference

**URL**: https://code.claude.com/docs/en/skills

Covers:
- SKILL.md frontmatter specification
- Skill discovery (skills/*/SKILL.md pattern)
- Monorepo support
- Skill metadata fields

### Marketplace JSON Schema

**URL**: https://anthropic.com/claude-code/marketplace.schema.json

The formal JSON Schema for validating marketplace.json files. Use with JSON schema validators for automated compliance checking.

## Quick Reference

| Topic | URL |
|-------|-----|
| Marketplace guide | https://docs.anthropic.com/en/docs/claude-code/plugin-marketplaces |
| Plugins guide | https://docs.anthropic.com/en/docs/claude-code/plugins |
| Plugins reference | https://code.claude.com/docs/en/plugins-reference |
| Skills reference | https://code.claude.com/docs/en/skills |
| Marketplace schema | https://anthropic.com/claude-code/marketplace.schema.json |

## See Also

- `plugin_marketplace_guide.md` -- Schema tables, organization patterns, component auto-discovery
- `marketplace_distribution_guide.md` -- Distribution workflow and version management
