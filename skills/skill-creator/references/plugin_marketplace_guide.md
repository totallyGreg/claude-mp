# Plugin Marketplace Guide

## Overview

This guide provides detailed information about creating and managing Claude Code plugin marketplaces for distributing skills. Plugin marketplaces enable users to discover and install skills using Claude Code's built-in plugin system.

## When to Use Plugin Marketplaces

Use plugin marketplaces when:
- **Team distribution** - Sharing skills across an organization
- **Multiple skills** - Bundling related skills together
- **Version management** - Managing updates and versions
- **Public distribution** - Publishing skills for community use
- **Automatic updates** - Users get updates when you push changes

Use standalone ZIP files when:
- **Single skill** - Distributing one-off skills
- **Quick sharing** - Immediate sharing without Git setup
- **Private distribution** - Sending to individuals directly

## Plugin Marketplace Structure

### File Organization

```
repository-root/
├── .claude-plugin/
│   └── marketplace.json          ← Marketplace configuration
├── skill-one/
│   ├── SKILL.md
│   ├── scripts/
│   ├── references/
│   └── assets/
├── skill-two/
│   └── SKILL.md
├── skill-three/
│   └── SKILL.md
└── README.md                      ← Installation instructions
```

### marketplace.json Schema

```json
{
  "name": "marketplace-name",           // Unique marketplace identifier
  "owner": {
    "name": "Owner Name",               // Marketplace maintainer
    "email": "email@example.com"        // Contact email
  },
  "metadata": {
    "description": "Marketplace desc",  // What this marketplace provides
    "version": "1.0.0"                  // Semantic version
  },
  "plugins": [                          // Array of plugins
    {
      "name": "plugin-name",            // Plugin identifier
      "description": "Plugin desc",      // What this plugin provides
      "source": "./",                    // Source path (usually "./")
      "strict": false,                   // Strict mode (usually false)
      "skills": [                        // Array of skill paths
        "./skill-one",
        "./skill-two"
      ]
    }
  ]
}
```

### Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Marketplace identifier (lowercase, hyphens) |
| `owner.name` | Yes | Marketplace owner/maintainer name |
| `owner.email` | Yes | Contact email for marketplace |
| `metadata.description` | Yes | Brief description of marketplace |
| `metadata.version` | Yes | Semantic version (e.g., "1.0.0") |
| `plugins` | Yes | Array of plugin objects |
| `plugins[].name` | Yes | Plugin identifier (lowercase, hyphens) |
| `plugins[].description` | Yes | Plugin description |
| `plugins[].source` | Yes | Source directory (usually "./") |
| `plugins[].strict` | No | Strict mode (default: false) |
| `plugins[].skills` | Yes | Array of skill directory paths |

## Creating a Plugin Marketplace

### Step 1: Initialize the Marketplace

Use the `add_to_marketplace.py` script to create the marketplace structure:

```bash
python3 scripts/add_to_marketplace.py init \
  --name my-marketplace \
  --owner-name "Your Name" \
  --owner-email "your.email@example.com" \
  --description "Description of your skill collection"
```

This creates `.claude-plugin/marketplace.json` with the base structure.

### Step 2: Add Skills

After creating skills, add them to the marketplace using one of these methods:

#### Method A: Create Plugin with Multiple Skills

```bash
python3 scripts/add_to_marketplace.py create-plugin my-plugin \
  "Plugin description" \
  --skills ./skill-one ./skill-two ./skill-three
```

This creates a new plugin containing multiple skills.

#### Method B: Create Plugin with Single Skill

```bash
python3 scripts/add_to_marketplace.py create-plugin terminal-guru \
  "Terminal configuration and diagnostics" \
  --skills ./terminal-guru
```

This creates a plugin for a single skill (useful for unrelated skills).

#### Method C: Add to Existing Plugin

```bash
python3 scripts/add_to_marketplace.py add-skill existing-plugin ./new-skill
```

This adds a skill to an already-created plugin.

### Step 3: Verify the Marketplace

List all plugins and skills to verify:

```bash
python3 scripts/add_to_marketplace.py list
```

Output:
```
📦 Marketplace: my-marketplace
   Owner: Your Name
   Version: 1.0.0
   Description: Description of your skill collection

   Plugins (1):

   • my-plugin
     Description: Plugin description
     Skills (3):
       - ./skill-one
       - ./skill-two
       - ./skill-three
```

### Step 4: Create Repository README

Create a README.md with installation instructions:

```markdown
# My Skills Marketplace

Description of your skills collection.

## Installation

### Via Claude Code Plugin System

```bash
# Add the marketplace
/plugin marketplace add username/repository-name

# Install a plugin
/plugin install plugin-name@marketplace-name
```

### From ZIP

Download the skill ZIP from releases and install manually.

## Available Plugins

### plugin-name

Description of plugin and its skills.

**Skills:**
- `skill-one` - Description
- `skill-two` - Description

## Usage

[Usage examples and documentation]
```

### Step 5: Publish to Git

```bash
# Add marketplace files
git add .claude-plugin/
git add skill-one/ skill-two/
git add README.md

# Commit
git commit -m "Add skills marketplace"

# Push to GitHub/GitLab
git push origin main
```

## Organizing Strategies

### Strategy 1: Single Plugin (Simplest)

Best for closely related skills in the same domain.

```json
{
  "plugins": [
    {
      "name": "development-tools",
      "description": "Tools for software development",
      "skills": [
        "./git-helper",
        "./code-formatter",
        "./test-runner"
      ]
    }
  ]
}
```

**Pros:**
- Simple structure
- Easy to maintain
- Clear purpose

**Cons:**
- Users get all skills together
- Can't install individual skills

**Use when:** Skills are highly related and users will want all of them.

### Strategy 2: Multiple Plugins by Domain

Best for skills grouped by functional area.

```json
{
  "plugins": [
    {
      "name": "terminal-tools",
      "description": "Terminal configuration and diagnostics",
      "skills": ["./terminal-guru", "./shell-config"]
    },
    {
      "name": "document-tools",
      "description": "Document processing utilities",
      "skills": ["./pdf-tools", "./markdown-tools"]
    },
    {
      "name": "dev-tools",
      "description": "Development utilities",
      "skills": ["./code-reviewer", "./test-helper"]
    }
  ]
}
```

**Pros:**
- Logical grouping
- Users can choose domains
- Scalable

**Cons:**
- More complex structure
- Requires thoughtful categorization

**Use when:** You have multiple skill categories that users might want separately.

### Strategy 3: One Plugin Per Skill

Best for unrelated skills or maximum flexibility.

```json
{
  "plugins": [
    {
      "name": "terminal-guru",
      "description": "Terminal diagnostics and configuration",
      "skills": ["./terminal-guru"]
    },
    {
      "name": "brand-guidelines",
      "description": "Company brand guidelines",
      "skills": ["./brand-guidelines"]
    },
    {
      "name": "sql-helper",
      "description": "SQL query assistance",
      "skills": ["./sql-helper"]
    }
  ]
}
```

**Pros:**
- Maximum granularity
- Users install exactly what they need
- Independent versioning

**Cons:**
- More plugins to manage
- Can be overwhelming with many skills

**Use when:** Skills are unrelated or users need fine-grained control.

## Version Management

### Semantic Versioning

Use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR** - Breaking changes, incompatible changes
- **MINOR** - New features, backward-compatible
- **PATCH** - Bug fixes, backward-compatible

Examples:
- `1.0.0` - Initial release
- `1.1.0` - Added new skill
- `1.1.1` - Fixed bug in existing skill
- `2.0.0` - Breaking change to skill structure

### Updating Versions

When to update the marketplace version:

1. **Added new skill** - Increment MINOR (1.0.0 → 1.1.0)
2. **Updated skill** - Increment PATCH (1.1.0 → 1.1.1)
3. **Removed skill** - Increment MAJOR (1.1.1 → 2.0.0)
4. **Changed structure** - Increment MAJOR (1.1.1 → 2.0.0)

Update manually in `.claude-plugin/marketplace.json`:

```json
{
  "metadata": {
    "version": "1.2.0"
  }
}
```

## User Installation

### Adding the Marketplace

Users add your marketplace to Claude Code:

```bash
/plugin marketplace add username/repository-name
```

For GitHub, this might be:
```bash
/plugin marketplace add johndoe/my-skills
```

### Installing Plugins

After adding the marketplace, users can install plugins:

**Via command:**
```bash
/plugin install plugin-name@marketplace-name
```

**Via interactive UI:**
1. Type `/plugin` in Claude Code
2. Select "Browse and install plugins"
3. Select your marketplace name
4. Select the plugin to install
5. Click "Install now"

### Multiple Installation Methods

Provide multiple methods in your README:

```markdown
## Installation

### Method 1: Plugin Marketplace (Recommended)
```bash
/plugin marketplace add username/repo
/plugin install plugin-name@marketplace-name
```

### Method 2: From ZIP
Download `skill-name.zip` from releases and extract to:
- `~/.config/claude/skills/` (personal)
- `.claude/skills/` (project)

### Method 3: Git Clone
```bash
git clone https://github.com/username/repo.git
ln -s $(pwd)/repo/skill-name ~/.config/claude/skills/skill-name
```
```

## Best Practices

### Naming Conventions

**Marketplace names:**
- Lowercase with hyphens
- Descriptive and searchable
- Unique within your namespace
- Examples: `dev-tools`, `terminal-utilities`, `acme-corp-skills`

**Plugin names:**
- Lowercase with hyphens
- Match skill domain
- Clear and concise
- Examples: `document-tools`, `terminal-guru`, `code-helpers`

### Descriptions

**Marketplace description:**
- Brief (1-2 sentences)
- Explain the collection's purpose
- Mention target users
- Example: "Professional development tools for software engineers"

**Plugin description:**
- Comprehensive (2-3 sentences)
- List key capabilities
- Mention included skills
- Example: "Terminal configuration, diagnostics, and troubleshooting including terminfo database management, Zsh autoload functions, and Unicode/UTF-8 support"

### Documentation

Include in your repository README:

1. **Overview** - What the marketplace provides
2. **Installation** - All methods (plugin, ZIP, clone)
3. **Available Plugins** - List with descriptions
4. **Usage Examples** - How to use each skill
5. **Requirements** - Dependencies or prerequisites
6. **Contributing** - How to add skills or contribute
7. **License** - Licensing information
8. **Support** - How to get help

### Maintenance

Regular maintenance tasks:

1. **Test skills** - Ensure all skills work with latest Claude Code
2. **Update versions** - Increment when changes are made
3. **Update README** - Keep installation instructions current
4. **Monitor issues** - Respond to user reports
5. **Archive obsolete skills** - Remove outdated skills cleanly

## Advanced Topics

### Multiple Marketplaces

You can create multiple marketplaces in separate repositories:

```
personal-skills/         → personal-tools marketplace
├── .claude-plugin/
└── skill-a/

work-skills/            → company-tools marketplace
├── .claude-plugin/
└── skill-b/

public-skills/          → public-utilities marketplace
├── .claude-plugin/
└── skill-c/
```

Users add each separately:
```bash
/plugin marketplace add user/personal-skills
/plugin marketplace add user/work-skills
/plugin marketplace add user/public-skills
```

### Private Marketplaces

For private/internal distribution:

1. Use private Git repository
2. Users need repository access
3. Same marketplace structure
4. Add via repository URL

```bash
/plugin marketplace add github.com/company/private-skills
```

### Marketplace Migration

When restructuring, provide migration guide:

```markdown
## Migrating from v1 to v2

Version 2.0 reorganized plugins by domain.

**Old structure:**
- `all-tools` plugin with all skills

**New structure:**
- `terminal-tools` plugin
- `document-tools` plugin
- `dev-tools` plugin

**Migration steps:**
1. Uninstall old plugin: `/plugin uninstall all-tools`
2. Install new plugins: `/plugin install terminal-tools@...`
```

## Troubleshooting

### Marketplace Not Found

**Issue:** `/plugin marketplace add` fails

**Solutions:**
1. Verify repository URL is correct
2. Check repository is public (or user has access)
3. Ensure `.claude-plugin/marketplace.json` exists
4. Validate JSON syntax

### Plugin Not Installing

**Issue:** `/plugin install` fails

**Solutions:**
1. Verify plugin name matches `marketplace.json`
2. Check skill directories exist
3. Ensure `SKILL.md` files are present
4. Validate all paths in `marketplace.json`

### Skills Not Loading

**Issue:** Skills installed but not working

**Solutions:**
1. Check `SKILL.md` has valid frontmatter
2. Verify `name` and `description` fields
3. Test skill in isolation
4. Check Claude Code logs

## Examples

### Example 1: Personal Utilities

```json
{
  "name": "personal-utils",
  "owner": {
    "name": "John Doe",
    "email": "john@example.com"
  },
  "metadata": {
    "description": "Personal productivity utilities",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "daily-tools",
      "description": "Daily productivity helpers",
      "source": "./",
      "strict": false,
      "skills": [
        "./time-tracker",
        "./note-organizer",
        "./task-manager"
      ]
    }
  ]
}
```

### Example 2: Company Skills

```json
{
  "name": "acme-corp",
  "owner": {
    "name": "ACME Corp IT",
    "email": "it@acme.com"
  },
  "metadata": {
    "description": "ACME Corporation internal tools",
    "version": "2.1.0"
  },
  "plugins": [
    {
      "name": "brand-tools",
      "description": "Brand guidelines and templates",
      "source": "./",
      "strict": false,
      "skills": ["./brand-guidelines", "./template-generator"]
    },
    {
      "name": "dev-tools",
      "description": "Development utilities",
      "source": "./",
      "strict": false,
      "skills": ["./code-reviewer", "./api-tester"]
    }
  ]
}
```

### Example 3: Public Collection

```json
{
  "name": "awesome-claude-skills",
  "owner": {
    "name": "Community Maintainers",
    "email": "maintainers@example.com"
  },
  "metadata": {
    "description": "Curated collection of Claude skills",
    "version": "3.0.0"
  },
  "plugins": [
    {
      "name": "terminal-guru",
      "description": "Comprehensive terminal configuration and troubleshooting",
      "source": "./",
      "strict": false,
      "skills": ["./terminal-guru"]
    },
    {
      "name": "document-suite",
      "description": "Document processing tools",
      "source": "./",
      "strict": false,
      "skills": ["./pdf-tools", "./docx-tools", "./xlsx-tools"]
    }
  ]
}
```

## Resources

- Claude Code Plugin Documentation
- Semantic Versioning Specification: https://semver.org/
- JSON Schema Validator: https://jsonschema.net/
- Git Repository Hosting: GitHub, GitLab, Bitbucket
