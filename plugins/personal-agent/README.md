# personal-agent

Personal orchestration agent with dynamic capability discovery across installed plugins.

## Overview

Rather than hardcoding knowledge of specific tools, this agent discovers installed plugins at runtime and routes requests to the appropriate domain. It handles cross-domain workflows, tracks usage patterns, and adapts when capabilities change.

## Usage

Invoke via the Agent tool with `subagent_type="personal-agent:personal-agent"`.

**Examples:**
- "What should I work on next?" — routes to task management
- "After my meeting, create a task and a summary note" — cross-domain orchestration
- "What can you help me with?" — reports discovered capabilities

**Command:**
- `/capabilities` — scan all registered plugins and show a status table

## Configuration

Edit `.local.md` at the plugin root to register your domains and plugins:

```yaml
---
plugin_root: /path/to/your/plugins

domains:
  task_management:
    plugin: omnifocus-manager
    description: GTD task management via OmniFocus
    primary_skill: omnifocus-manager
    agent: omnifocus-agent
  knowledge_management:
    plugin: pkm-plugin
    description: Personal Knowledge Management via Obsidian
    primary_skill: vault-curator
    agent: pkm-manager
---
```

### Adding a domain

Add a new entry under `domains:` with:
- `plugin` — directory name of the plugin under `plugin_root`
- `description` — what this domain handles
- `primary_skill` — skill directory name to load for this domain
- `agent` — agent filename (without `.md`) if the domain has a dedicated agent

### Removing a domain

Delete the entry from `domains:`. The agent will stop routing to it on the next session.

### Switching tools

Change the `plugin` value to point to a different plugin. For example, replacing OmniFocus with Todoist:

```yaml
  task_management:
    plugin: todoist-manager
    description: Task management via Todoist
    primary_skill: todoist-manager
    agent: todoist-agent
```

The agent discovers the new plugin's skills and agents automatically.

## How It Works

### Initialization (each session)

1. Reads `.local.md` to get the domain-to-plugin registry
2. Scans each registered plugin's directory for manifest, skills, agents, and commands
3. Builds a capability index with availability status
4. Reports any missing plugins or structural changes

### Intent classification

1. Classifies user request into one or more domains
2. Checks capability index to confirm the domain is available
3. Loads the domain's SKILL.md on demand and follows its instructions
4. For cross-domain requests, decomposes into per-domain steps and executes sequentially

### Usage pattern tracking

The agent maintains `usage-patterns.md` at the plugin root:
- Records which domains are requested most often
- Tracks cross-domain workflow sequences
- Promotes well-established patterns (5+ occurrences) for faster routing

This file is plaintext on disk, not encrypted. It contains operational metadata (domain names, request summaries), not sensitive personal data.

## Components

### Agent: personal-agent
Orchestration layer that discovers plugins, classifies intent, and routes to domain skills. Does not contain domain expertise itself — that lives in each domain's plugin.

### Command: /capabilities
Scans all registered plugins and reports a summary table of available domains, plugin versions, skill/agent/command counts, and status.

## Architecture Principles

- **Domain expertise stays with domain agents** — this agent orchestrates, it doesn't duplicate knowledge
- **Discover, don't assume** — scan plugin structure at runtime rather than hardcoding paths
- **Learn from usage** — track patterns to improve routing over time
- **Adapt to change** — detect added, removed, or updated plugins automatically

## Version History

| Version | Changes |
|---------|---------|
| 0.1.0 | Initial scaffold: agent, capability registry, /capabilities command, usage tracking |
