---
name: capabilities
description: Show discovered capabilities across all registered plugins
allowed-tools: ["Read", "Glob", "Bash"]
---

# Show Capabilities

Scan all registered plugins and report available capabilities.

## Steps

1. Read `${CLAUDE_PLUGIN_ROOT}/.local.md` to get the plugin registry
2. For each registered domain:
   a. Check if plugin exists at `{plugin_root}/{plugin_name}/.claude-plugin/plugin.json`
   b. Read manifest for version and description
   c. Count skills: `Glob {plugin_root}/{plugin_name}/skills/*/SKILL.md`
   d. Count agents: `Glob {plugin_root}/{plugin_name}/agents/*.md`
   e. Count commands: `Glob {plugin_root}/{plugin_name}/commands/*.md`
3. Present a summary table:

```
## Capability Index

| Domain | Plugin | Version | Skills | Agents | Commands | Status |
|--------|--------|---------|--------|--------|----------|--------|
| task_management | omnifocus-manager | 9.3.1 | 2 | 1 | 12 | available |
| knowledge_management | pkm-plugin | 1.8.0 | 2 | 1 | 0 | available |
```

4. If `${CLAUDE_PLUGIN_ROOT}/usage-patterns.md` exists, show top patterns
5. Flag any registered plugins that are missing or have errors
