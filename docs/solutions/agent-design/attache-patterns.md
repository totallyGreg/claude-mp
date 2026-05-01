---
title: Attache Agent Patterns
domain: agent-design
created: 2026-04-30
---

# Attache Agent Patterns

Design decisions and learned patterns for the Attache (Chief of Staff) agent.

## Architecture

**Plugin:** `plugins/attache/` (renamed from omnifocus-manager in v11.0.0)

**Four skills:**
- `omnifocus-core` — stateless data access (ofo CLI, queries, perspectives)
- `omnifocus-generator` — OmniFocus plugin scaffolding (.omnifocusjs)
- `attache-analyst` — system learning, AI coaching, tool stack awareness
- `gtd-coach` — pure GTD methodology coaching

**Decomposition rationale:** Follows the archivist pattern (vault-architect / vault-curator split). Each skill owns a clear concern with explicit boundaries. The agent routes between them based on intent classification.

## Key Decisions

### "Plugin" disambiguation
"Plugin" is overloaded in this repo — Claude Code plugins vs OmniFocus plugins. The omnifocus-generator skill's trigger description explicitly requires "OmniFocus plugin" context. Generic "create a plugin" without OmniFocus context should clarify intent first.

### Skill load order
Skills load on-demand, not at startup. The agent reads SKILL.md only when routing to that skill. This minimizes token usage at the orchestrator level.

### Cross-tool delegation
The Attache spawns sibling agents (archivist, terminal-guru) for out-of-domain work rather than trying to handle everything itself. Each sibling preserves its own context (vault profiling, triage routing).

### Tool stack awareness
The Attache reads the vault's Tools.base via the archivist to discover the user's full tool landscape. This extends the OmniFocus-centric System Map to cover all tools.

## Efficiency Observations

- `ofo stats` (single call) preferred over multiple `ofo list` calls — avoids pasteboard collision
- `ofo health` combines inbox + overdue + flagged in one call
- `gtd-queries.js --action system-health` runs 5 diagnostic queries in one JXA invocation
- Slash commands (`/ofo-today`) are lighter than loading full SKILL.md for simple queries

## Agentsmith Scores

| Date | Overall | Trigger | Prompt | Coherence |
|------|---------|---------|--------|-----------|
| 2026-04-30 | 82 | 85 | 78 | 86 |
