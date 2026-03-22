# omnifocus-manager

OmniFocus automation, GTD diagnostics, and perspective management for macOS.

## Components

### Agent: omnifocus-agent
Routes between omnifocus-manager (execution/queries/plugins) and gtd-coach (methodology) based on user intent. Invoke via `subagent_type="omnifocus-manager:omnifocus-agent"` — not the Skill tool.

### Skill: omnifocus-manager
OmniFocus data queries, JXA plugin generation, and perspective configuration:
- Task and project queries (overdue, stalled, inbox, today, waiting)
- GTD health diagnostics and perspective inventory
- Plugin generation via `node scripts/generate_plugin.js`
- AI Agent project publishing and ofo-work execution

### Skill: gtd-coach
GTD methodology coaching without OmniFocus automation:
- Next action clarity, inbox processing, weekly review guidance
- Project definition, someday/maybe triage, waiting-for lists
- Workflow analysis and habit optimization

### Commands (13)
`/ofo-today`, `/ofo-overdue`, `/ofo-inbox`, `/ofo-health`, `/ofo-search`, `/ofo-info`, `/ofo-tagged`, `/ofo-plan`, `/ofo-work`, `/ofo-expound`, `/ofo-analyze-projects`, `/ofo-analyze-habits`, `/ofo-weekly-review`

## Version History

| Version | Changes |
|---------|---------|
| 9.0.0 | ofoCore named exports, shared types, ofo dump/stats, open-based deploy |
| 8.4.0 | perspective-list, perspective-rules with ID resolution |
| 8.0.0 | TypeScript plugin library (ofo-core.ts), ofo CLI |
| 7.0.0 | Migrated to plugin structure with agent routing |
