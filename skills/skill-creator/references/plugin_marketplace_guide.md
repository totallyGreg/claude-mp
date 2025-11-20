# Plugin Marketplace Reference

## Quick Overview

Plugin marketplaces are Git repositories containing a `.claude-plugin/marketplace.json` file that defines a collection of skills users can install via `/plugin` commands.

## File Structure

```
repository-root/
├── .claude-plugin/
│   └── marketplace.json          ← Required: Marketplace configuration
├── skills/
│   ├── skill-one/
│   │   └── SKILL.md             ← Required: Skill definition
│   └── skill-two/
│       └── SKILL.md
└── README.md                     ← Recommended: Installation docs
```

## marketplace.json Schema

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "marketplace-name",
  "version": "1.0.0",
  "description": "Description of this marketplace",
  "owner": {
    "name": "Owner Name",
    "email": "owner@example.com"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "description": "Plugin description",
      "category": "development",
      "version": "1.0.0",
      "author": {
        "name": "Author Name",
        "email": "author@example.com"
      },
      "source": "./",
      "skills": ["./skills/skill-one", "./skills/skill-two"]
    }
  ]
}
```

## Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `$schema` | Yes | String | JSON Schema URL for validation |
| `name` | Yes | String | Marketplace identifier (lowercase-with-hyphens) |
| `version` | Yes | String | Semantic version (MAJOR.MINOR.PATCH) |
| `description` | Yes | String | Brief marketplace description |
| `owner` | Yes | Object | Marketplace owner information |
| `owner.name` | Yes | String | Owner/maintainer name |
| `owner.email` | No | String | Contact email |
| `plugins` | Yes | Array | Array of plugin objects |
| `plugins[].name` | Yes | String | Plugin identifier (lowercase-with-hyphens) |
| `plugins[].description` | Yes | String | Plugin description |
| `plugins[].category` | No | String | Plugin category (development, productivity, etc.) |
| `plugins[].version` | Yes | String | Plugin semantic version |
| `plugins[].author` | No | Object | Plugin author info (name, email) |
| `plugins[].source` | No | String | Source directory path (default: "./") |
| `plugins[].skills` | No | Array | Array of skill directory paths |

## Plugin Organization Strategies

### Single Plugin (Related Skills)
```json
{
  "plugins": [{
    "name": "dev-tools",
    "skills": ["./git-helper", "./code-formatter", "./test-runner"]
  }]
}
```
**Use when:** Skills are highly related and users want all of them.

### Multiple Plugins by Domain
```json
{
  "plugins": [
    {"name": "terminal-tools", "skills": ["./terminal-guru", "./shell-config"]},
    {"name": "document-tools", "skills": ["./pdf-tools", "./markdown-tools"]}
  ]
}
```
**Use when:** Skills fall into distinct categories.

### One Plugin Per Skill
```json
{
  "plugins": [
    {"name": "terminal-guru", "skills": ["./terminal-guru"]},
    {"name": "brand-guidelines", "skills": ["./brand-guidelines"]}
  ]
}
```
**Use when:** Skills are unrelated or need independent versioning.

## Installation Commands

### Add Marketplace
```bash
/plugin marketplace add username/repository-name
```

### Install Plugin
```bash
/plugin install plugin-name@marketplace-name
```

## Versioning Guide

Use semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR** - Breaking changes
- **MINOR** - New features (backward-compatible)
- **PATCH** - Bug fixes (backward-compatible)

Examples:
- `1.0.0` → `1.1.0` - Added new skill
- `1.1.0` → `1.1.1` - Fixed bug in skill
- `1.1.1` → `2.0.0` - Removed skill or breaking change

## Complete Example

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "my-marketplace",
  "version": "1.0.0",
  "description": "Collection of development tools",
  "owner": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "plugins": [
    {
      "name": "terminal-tools",
      "description": "Terminal diagnostics and configuration",
      "category": "development",
      "version": "1.0.0",
      "author": {
        "name": "Your Name",
        "email": "you@example.com"
      },
      "source": "./",
      "skills": ["./skills/terminal-guru"]
    }
  ]
}
```
