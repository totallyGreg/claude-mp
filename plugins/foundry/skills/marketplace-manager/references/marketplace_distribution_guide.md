# Marketplace Distribution Guide

Guidance on distributing plugins via the Claude Code marketplace system. For marketplace.json schema details and organization patterns, see `plugin_marketplace_guide.md`.

---

## Overview

Plugins are distributed through the Claude Code marketplace system, making them available for installation by other users. The **marketplace-manager** skill handles versioning, validation, and publication.

---

## Distribution Workflow

### High-Level Process

1. **Develop plugin** -- Complete plugin with skills, commands, agents, etc.
2. **Validate** -- Run `evaluate_skill.py` to ensure quality
3. **Invoke marketplace-manager** -- Delegate marketplace operations
4. **Review changes** -- marketplace-manager shows what will be committed
5. **Commit** -- Approve marketplace.json + plugin changes
6. **Push to remote** -- Optionally push to remote repository

### Preparation Checklist

Before distributing, ensure:
- [ ] Plugin passes validation
- [ ] SKILL.md is complete and accurate (for skill-based plugins)
- [ ] Version number is set in plugin.json or SKILL.md `metadata.version`
- [ ] All bundled resources are tested and working

### Invocation

```bash
# Via skillsmith delegation (recommended)
User: "Publish my-plugin to marketplace"

# Direct invocation
/marketplace-manager add plugins/my-plugin/
```

### What marketplace-manager Does

1. **Adds plugin to marketplace.json** (if new) -- creates entry with `name` and `source`
2. **Validates** -- runs `claude plugin validate` and rejects `version` in marketplace entries
3. **Enforces version bumps** -- the pre-commit hook blocks commits that change a plugin or skill without raising its version

---

## marketplace.json Structure

Source: https://docs.anthropic.com/en/docs/claude-code/plugin-marketplaces

### Minimal Valid Example

```json
{
  "name": "my-marketplace",
  "owner": { "name": "Dev Team" },
  "plugins": [
    { "name": "my-plugin", "source": "./plugins/my-plugin" }
  ]
}
```

### With Optional Fields

```json
{
  "name": "my-marketplace",
  "owner": { "name": "Dev Team", "email": "team@example.com" },
  "metadata": {
    "description": "Internal development tools",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "my-plugin",
      "source": "./plugins/my-plugin",
      "version": "2.1.0",
      "description": "Code formatting and linting",
      "category": "developer-tools",
      "keywords": ["formatting", "linting"]
    }
  ]
}
```

For complete schema tables and all 6 organization patterns, see `plugin_marketplace_guide.md`.

---

## Version Management

### Version Source

`.claude-plugin/plugin.json` `version` is the only plugin version. Marketplace entries don't carry one (Anthropic: "Don't set `version` in both `plugin.json` and the marketplace entry"). Skills carry their own `metadata.version` in SKILL.md.

```json
{
  "plugins": [
    { "name": "my-plugin", "source": "./plugins/my-plugin", "category": "development" }
  ]
}
```

A change to a plugin requires a higher plugin.json version; a change to a skill also requires a higher SKILL.md `metadata.version`. The pre-commit hook enforces both against the merge-base with `origin/main`.

### Semantic Versioning

- **MAJOR (X.0.0)** -- Breaking changes, incompatible workflow changes
- **MINOR (x.X.0)** -- New features, backward-compatible enhancements
- **PATCH (x.x.X)** -- Bug fixes, documentation updates

### Multi-Skill Plugin Versioning

For plugins with multiple skills, plugin version is independent from individual skill versions. Manual version bumps are required. See `plugin_marketplace_guide.md` for details.

---

## Marketplace Validation

marketplace-manager validates against the official Anthropic schema:

- **Required fields** -- `name`, `owner`, `plugins` at root; `name`, `source` per plugin entry
- **Path validation** -- all relative source paths resolve to existing directories
- **Duplicate detection** -- no duplicate plugin names
- **Version format** -- semver (MAJOR.MINOR.PATCH)
- **Structure checks** -- detects anti-patterns like shared `source: "./"` across multiple plugins

```bash
/marketplace-manager validate
```

---

## Post-Distribution

### Verify Installation

```bash
/plugin install my-plugin@my-marketplace
```

### Maintain

- Keep plugin.json or SKILL.md versions current
- Document breaking changes in commit messages
- Use MAJOR version bumps for breaking changes

---

## Troubleshooting

### "marketplace-manager can't find my plugin"

Verify the plugin path is correct and contains discoverable components (skills/, commands/, .claude-plugin/, etc.):

```bash
ls plugins/my-plugin/skills/*/SKILL.md
ls plugins/my-plugin/.claude-plugin/plugin.json
```

### "no version in .../plugin.json"

Add a version to the plugin manifest:

```json
// .claude-plugin/plugin.json
{ "name": "my-plugin", "version": "1.0.0" }
```

Skills need one too:

```yaml
# skills/my-skill/SKILL.md frontmatter
metadata:
  version: "1.0.0"
```

### "marketplace.json validation failed"

Run validation for specific errors:

```bash
/marketplace-manager validate
```

Common issues:
- Missing `name` or `source` in plugin entries
- Invalid version format (use X.Y.Z, not vX.Y.Z)
- Source path does not exist on disk
- Duplicate plugin names

---

## Related References

- `plugin_marketplace_guide.md` -- Schema tables, organization patterns, component auto-discovery
- `official_docs_index.md` -- Links to official Anthropic documentation

---

*This guide describes marketplace distribution workflow. For schema details and organization patterns, see `plugin_marketplace_guide.md`.*
