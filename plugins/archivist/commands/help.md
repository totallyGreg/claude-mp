---
name: help
description: List all available archivist slash commands with a one-line description of each.
---

Invoke the archivist agent to list all available slash commands.

The agent should:
1. Initialize normally (load skills, discover vault location)
2. Read all files matching `${CLAUDE_PLUGIN_ROOT}/commands/*.md` (Glob)
3. For each command file, extract the `description` field from its YAML frontmatter
4. Present a formatted table with two columns: the slash command (e.g., `/canvas`) and its description
5. Note that deeper capability documentation is available in the skill files:
   - `${CLAUDE_PLUGIN_ROOT}/skills/vault-architect/SKILL.md` — vault structure, templates, schemas
   - `${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/SKILL.md` — content evolution, consolidation, visualization
