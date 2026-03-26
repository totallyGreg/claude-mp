# PKM Plugin

Personal Knowledge Management expert for Obsidian vaults with autonomous orchestration.

## Usage

Ask Claude to help with Obsidian PKM tasks. The `pkm-manager` agent will orchestrate vault analysis, template creation, and system optimization.

**Examples:**
- "Analyze my vault and suggest improvements"
- "Create a customer meeting note template"
- "Help me set up a temporal rollup system"

## Configuration

Copy `.local.md.example` to `.local.md` and set your vault path:

```markdown
vault_path: /Users/username/Documents/MyVault
```

## Skill Documentation

See `skills/vault-architect/SKILL.md` for creating new structures and `skills/vault-curator/SKILL.md` for evolving existing content.

Progressive disclosure:
- `SKILL.md` - Core capabilities and workflows
- `references/` - Detailed guides (Templater patterns, Bases queries, etc.)
- `scripts/` - Python analysis tools
- `assets/` - Template examples

## Version

1.6.0

## License

MIT

## Skill: vault-architect

### Current Metrics

**Score: 97/100** (Excellent) — 2026-03-25

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 98 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.4.0 | 2026-03-25 | - | Add Vault Discovery (auto-discover templates/tags/orphans before recommending) and Cross-Skill Handoff sections; add license; add negative trigger clause; compress Workflow Lookup table | 98 | 90 | 100 | 100 | 100 | 97 |
| 1.3.0 | 2026-03-14 | - | Add Workflow Lookup, Capture, and Refinement section: vault discovery via Workflows.base, Workflow fileClass schema, Capture-to-Review pattern reference; add missing `compatibility` field | 83 | 80 | 90 | 100 | 100 | 89 |
| 1.2.0 | 2026-03-05 | - | SKILL.md restructure: 12 trigger phrases, conciseness fix, structural bug fix (#89) | 83 | 80 | 80 | 100 | 100 | 86 |
| 1.1.1 | 2026-03-05 | - | Comprehensive QuickAdd 2.12.0 reference, SKILL.md section update | 34 | 88 | 80 | 100 | 100 | 78 |
| 1.0.0 | 2025-12-15 | - | Initial release with core PKM guidance | - | - | - | - | - | - |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)


## Skill: vault-curator

### Current Metrics

**Score: 97/100** (Excellent) — 2026-03-25

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 98 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.8.0 | 2026-03-25 | - | Add negative trigger clause to prevent overtriggering vs vault-architect; fix git add -A bug in pkm-manager pre-consolidation checkpoint | 98 | 90 | 100 | 100 | 100 | 97 |
| 1.7.0 | 2026-03-22 | - | Delegate CLI ops to marketplace skills; promote `create overwrite` write pattern inline; strip generic commands from cli-patterns.md to gotchas-only | 98 | 90 | 100 | 100 | 100 | 97 |
| 1.6.0 | 2026-03-20 | - | Add read/append/insertion CLI patterns to references; add license; move scripts table to reference; add available-scripts.md | 97 | 98 | 90 | 100 | 100 | 100 |
| 1.5.3 | 2026-03-16 | [#103](https://github.com/totallyGreg/claude-mp/issues/103) | Fix: document `obsidian file` is read-only; warn content/overwrite silently ignored | 78 | 88 | 90 | 100 | 100 | 90 |
| 1.5.2 | 2026-03-14 | - | Fix: document create+move pattern; warn folder= in create is unreliable | 88 | 90 | 100 | 90 | - | 78 |
| 1.5.1 | 2026-03-05 | [#89](https://github.com/totallyGreg/claude-mp/issues/89) | Description + conciseness improvement: 11 trigger phrases, CLI moved to ref, planned scripts fixed | 78 | 88 | 90 | 100 | 100 | 90 |
| 1.5.0 | 2026-02-16 | - | Visualization workflows: generate_canvas.py | 66 | 86 | 90 | 100 | 80 | 85 |
| 1.4.0 | 2026-02-16 | [#46](https://github.com/totallyGreg/claude-mp/issues/46) | Discovery workflows: find_related.py, progressive discovery views, auto-linking suggestions | 76 | 88 | 90 | 100 | 80 | 87 |
| 1.3.0 | 2026-02-16 | [#45](https://github.com/totallyGreg/claude-mp/issues/45) | Consolidation workflows: find_similar_notes.py, merge_notes.py, redirect_links.py, consolidation-protocol.md | - | - | - | - | - | 89 |
| 1.2.0 | 2026-02-15 | [#44](https://github.com/totallyGreg/claude-mp/issues/44) | Scope selection, metadata workflows (suggest_properties.py, detect_schema_drift.py), SKILL.md restructure | - | - | - | - | - | - |
| 1.0.0 | 2026-02-10 | - | Initial release with meeting extraction, migration patterns, and pattern detection workflows | - | - | - | - | - | - |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

