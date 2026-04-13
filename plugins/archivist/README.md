# Archivist

Personal Knowledge Management expert for Obsidian vaults with autonomous orchestration.

## Usage

Ask Claude to help with Obsidian PKM tasks. The `archivist` agent will orchestrate vault analysis, template creation, and content evolution.

### Visualization

- "Create a canvas showing me the entire release process for [project]"
- "Generate a knowledge map of everything connected to [topic]"
- "Show me how my project notes link to each other as a canvas"

### Metadata & Schema

- "What properties should this meeting note have?"
- "Find all notes in my Projects folder with inconsistent frontmatter"
- "Detect schema drift across my Customer fileClass"
- "Suggest missing properties for this note based on similar notes"

### Consolidation & Discovery

- "Find duplicate notes in my [folder]"
- "What notes are most related to this one?"
- "Merge these two notes about [topic] and update all links"
- "Find orphaned notes that aren't linked to anything"

### Vault Structure

- "Analyze my vault and suggest improvements"
- "Create a customer meeting note template"
- "Help me set up a temporal rollup system"
- "Set up a collection folder for [repeating note type]"
- "Run a health check on my vault"

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

1.20.0

## License

MIT

## Agent: archivist

### Agent-Native Audit — 2026-04-13

Overall score: **71%** ([#160](https://github.com/totallyGreg/claude-mp/issues/160))

| Principle | Score | % | Status |
|-----------|-------|---|--------|
| Action Parity | 6/6 | 100% | ✅ |
| Capability Discovery | 6.5/7 | 93% | ✅ |
| Shared Workspace | 7/8 | 87.5% | ✅ |
| Tools as Primitives | 9/12 | 75% | ⚠️ |
| UI Integration | 5/8 | 62.5% | ⚠️ |
| CRUD Completeness | 7/12 | 58% | ⚠️ |
| Context Injection | 12/22 | 54.5% | ⚠️ |
| Prompt-Native Features | 8/20 | 40% | ❌ |

### Version History

| Version | Date | Issue | Summary |
|---------|------|-------|---------|
| 1.20.0 | 2026-04-13 | [#160](https://github.com/totallyGreg/claude-mp/issues/160) | Add workflow classification (known vs novel detection) and session learning tables (Known Workflows + Workflow Candidates) to _vault-profile.md; promotion rule graduates 2+ occurrence candidates to workflow notes |
| 1.19.0 | 2026-04-09 | - | Add Canvas Types taxonomy (Impact/Workflow/Architecture/Knowledge Maps) and Change Impact Map workflow |

## Skill: vault-architect

### Current Metrics

**Score: 93/100** (Good) — 2026-04-11

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 79 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.9.0 | 2026-04-11 | - | Add linking discipline to Design Principles: link aggressively, no backticked vault entities; schema authority: .base default view is canonical, fileClass mirrors it; pointer to linking-discipline.md | 79 | 90 | 100 | 100 | 100 | 93 |
| 1.8.0 | 2026-03-31 | - | Add Vault Profiling workflow, Write Boundaries section, replace hardcoded vault path with ${VAULT_PATH} | 80 | 90 | 100 | 100 | 100 | 94 |
| 1.7.0 | 2026-03-28 | - | Add Linter plugin config read to Vault Discovery; read .obsidian/plugins/obsidian-linter/data.json before writing notes | 98 | 100 | 100 | 100 | 100 | 99 |
| 1.6.0 | 2026-03-28 | - | Add CLI delegation block to Vault Discovery naming obsidian-skills as source; document path= vs file= distinction and folder-note resolution | 98 | 100 | 100 | 100 | 100 | 99 |
| 1.5.0 | 2026-03-26 | - | Reduce to 5 sections for full complexity score; merge Core Principles into intro, Resources into capabilities, Cross-Skill Handoff into Workflows; fix vault analysis to run CLI discovery before asking user | 98 | 100 | 100 | 100 | 100 | 99 |
| 1.4.0 | 2026-03-25 | - | Add Vault Discovery (auto-discover templates/tags/orphans before recommending) and Cross-Skill Handoff sections; add license; add negative trigger clause; compress Workflow Lookup table | 98 | 90 | 100 | 100 | 100 | 97 |
| 1.3.0 | 2026-03-14 | - | Add Workflow Lookup, Capture, and Refinement section: vault discovery via Workflows.base, Workflow fileClass schema, Capture-to-Review pattern reference; add missing `compatibility` field | 83 | 80 | 90 | 100 | 100 | 89 |
| 1.2.0 | 2026-03-05 | - | SKILL.md restructure: 12 trigger phrases, conciseness fix, structural bug fix (#89) | 83 | 80 | 80 | 100 | 100 | 86 |
| 1.1.1 | 2026-03-05 | - | Comprehensive QuickAdd 2.12.0 reference, SKILL.md section update | 34 | 88 | 80 | 100 | 100 | 78 |
| 1.0.0 | 2025-12-15 | - | Initial release with core PKM guidance | - | - | - | - | - | - |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)


## Skill: vault-curator

### Current Metrics

**Score: 96/100** (Excellent) — 2026-04-11

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 83 | 100 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.11.0 | 2026-04-11 | - | Add Wikilinks over backticks rule to Write Quality Gate; graph traversal commands to cli-patterns.md; create linking-discipline.md reference (decision table, schema authority, graph CLI commands) | 83 | 100 | 100 | 100 | 100 | 96 |
| 1.10.0 | 2026-04-01 | - | Demote Write Boundaries to H3; add Base Files and File Relocation rules to cli-patterns.md; offload verbose docs to references/ | 98 | 100 | 100 | 100 | 100 | 99 |
| 1.9.4 | 2026-03-31 | - | Add Write Boundaries section for vault-aware permission zones | 80 | 90 | 100 | 100 | 100 | 94 |
| 1.9.3 | 2026-03-28 | - | Add Vault Write Quality Gate: frontmatter must start on line 1, Linter compliance check, bulk validation pointer | 98 | 90 | 100 | 100 | 100 | 97 |
| 1.9.2 | 2026-03-28 | - | Name obsidian-skills as CLI source in delegation line; reference cli-patterns.md for error handling | 98 | 100 | 100 | 100 | 100 | 99 |
| 1.9.1 | 2026-03-27 | - | Add vault write triggers ("update this note", "write to vault", "create a note from URL") to route content writes through curator | 98 | 100 | 100 | 100 | 100 | 99 |
| 1.9.0 | 2026-03-26 | - | Add opportunistic drift detection to scope selection; surface schema inconsistencies proactively during any vault operation | 98 | 100 | 100 | 100 | 100 | 99 |
| 1.8.1 | 2026-03-25 | - | Reduce section count for complexity score; merge Core Principles into intro, Visualization into Discovery; add markdown-oxide LSP fallback | 98 | 100 | 100 | 100 | 100 | 99 |
| 1.8.0 | 2026-03-25 | - | Add negative trigger clause to prevent overtriggering vs vault-architect; fix git add -A bug in archivist pre-consolidation checkpoint | 98 | 90 | 100 | 100 | 100 | 97 |
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

