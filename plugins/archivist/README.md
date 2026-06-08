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

1.27.0

## License

MIT

## Agent: archivist

### Agent-Native Audit — 2026-04-14

Overall score: **71%** ([#160](https://github.com/totallyGreg/claude-mp/issues/160))

| Principle | Score | % | Status |
|-----------|-------|---|--------|
| Shared Workspace | 7.5/8 | 94% | ✅ |
| Capability Discovery | 6.5/7 | 93% | ✅ |
| Prompt-Native Features | 28/32 | 88% | ✅ |
| Tools as Primitives | 8/10 | 80% | ✅ |
| Context Injection | 5/7 | 71% | ⚠️ |
| CRUD Completeness | 4/7 | 57% | ⚠️ |
| Action Parity | 12/24 | 50% | ⚠️ |
| UI Integration | 6/17 | 35% | ❌ |

### Version History

| Version | Date | Issue | Summary |
|---------|------|-------|---------|
| 1.28.0 | 2026-06-08 | - | Auto-discover write zones from vault profile when `.local.md` lacks them. Init step 3 now derives `architect_write_zones`/`curator_write_zones`/`designated_output_zones` from `_vault-profile.md` "Directory Trust Levels" table using mapping: `infrastructure` → architect, `personal/guarded`+`project-scoped` → curator, `automated/generated` → designated_output. Derived zones apply for the session; one-time AskUserQuestion offer to persist to `.local.md`. Policy-based refusals now prefix `Archivist policy:` to disambiguate from Claude Code tooling-layer denials (the "denied" wording was sending users down the wrong debugging path — see today's friction report). Empirical evidence: today's session spent ~90 min chasing a Claude Code permission bug that turned out to be the archivist's own bounded-autonomy refusing due to missing `.local.md`. Agent eval 93 (no change — substantive logic, not example/length metrics). |
| 1.27.0 | 2026-06-06 | [#176](https://github.com/totallyGreg/claude-mp/issues/176) | Pass A (friction batch 2026-06-05). A1: Denial Handling — Mode 1/Mode 2 recovery guidance with `permissions.allow` schema + JSON example; Mode 2 labeled "observed empirically, not root-caused." A2: Subagent Input Volume Guard — token-count + file-path-count trigger (not category labels); soft-confirm path before refusal; defense-in-depth framing. A3: External-System Handoffs — new table in §Post-Workflow routing meeting-extraction action items to `attache:attache`. Agent eval 93 (no change). |
| 1.26.0 | 2026-06-04 | [#160](https://github.com/totallyGreg/claude-mp/issues/160), [#129](https://github.com/totallyGreg/claude-mp/issues/129) | Friction fixes (2026-06-04 + 2026-05-28 reports) + Tier-1 wins from #160. Strict Denial Handling (stop on first denial across primitives, Read tool ≠ obsidian read ≠ Write's internal gate, pre-flight refusal when zones missing). Reference Formatting rule (wikilink intra-vault, file:// external, backticks code-only). Index refresh after Python writes. Init drift signal on primary fileClass. New `duplicate-detection-thresholds.md` policy reference. Closed #129 as superseded by current architecture. Agent eval 92→93 (Prompt 91→95). |
| 1.25.0 | 2026-05-03 | - | Safety hardening: Write Path (read-prepare-write protocol), Issue Learning, Fast Init, anti-cascade principle, Drift Triage in curator (mechanical vs semantic). Body trim 4955→3033 words (session-logging + canvas-types moved to references). Agent eval 89→92 (Role:3→15, Prompt:83→91). |
| 1.24.2 | 2026-04-24 | - | Refactor session-log to dispatch through logEntries.js; add resume/pause subcommands; entry enrichment with phase/outcome; linking conventions; progressive frontmatter updates |
| 1.21.0 | 2026-04-14 | [#160](https://github.com/totallyGreg/claude-mp/issues/160) | Agent-native improvements: init vault signals (Context Injection), delete workflows (CRUD), multi-vault .local.md (Shared Workspace), --no-write primitives (Tools as Primitives), index refresh after writes (UI Integration), /help + /workflows commands (Capability Discovery + Action Parity) |
| 1.20.0 | 2026-04-13 | [#160](https://github.com/totallyGreg/claude-mp/issues/160) | Add workflow classification (known vs novel detection) and session learning tables (Known Workflows + Workflow Candidates) to _vault-profile.md; promotion rule graduates 2+ occurrence candidates to workflow notes |
| 1.19.0 | 2026-04-09 | - | Add Canvas Types taxonomy (Impact/Workflow/Architecture/Knowledge Maps) and Change Impact Map workflow |

## Skill: vault-architect

### Current Metrics

**Score: 93/100** (Good) — 2026-06-08

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 76 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.12.0 | 2026-06-08 | - | Align §Write Boundaries with auto-discovery: "No zones configured in `.local.md`" now references the agent's profile-derived zones (mapping doc) rather than refusing outright; refusals prefixed `Archivist policy:` to disambiguate from Claude Code tooling-layer denials. Score 94→93 (Concs 77→76 from added prose; substantive consistency with agent v1.28.0). | 76 | 90 | 100 | 100 | 100 | 93 |
| 1.11.0 | 2026-06-06 | [#176](https://github.com/totallyGreg/claude-mp/issues/176) | Pass C (friction batch 2026-06-05). C1: notation hygiene added to Design Principles "Do:" — per-template pick, prefer Obsidian-native `- [ ]`/`- [x]`, extended markers require Tasks plugin verification, no proactive retrofit. §10 Vault System Documentation updated to include Notation Conventions entry. Also fixed SKILL.md version drift (was stuck at 1.9.0 while README was at 1.10.0). Score 94 (Concs 79→77 from added text; overall floor met). | 77 | 90 | 100 | 100 | 100 | 94 |
| 1.10.0 | 2026-04-14 | [#160](https://github.com/totallyGreg/claude-mp/issues/160) | Add vault-analysis-checks.md (analyze_vault.py check reference) and frontmatter-schema-reference.md (validate_frontmatter.py fields, severity, violations); update SKILL.md to reference both | 79 | 90 | 100 | 100 | 100 | 93 |
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

**Score: 96/100** (Excellent) — 2026-06-08

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 78 | 100 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.16.0 | 2026-06-08 | - | Align §Write Boundaries with agent's profile-derived zone discovery: "No zones configured in `.local.md`" no longer terminates — derived zones from `_vault-profile.md` apply if present. Refusal phrasing standardized to `Archivist policy:` prefix to disambiguate from Claude Code tooling-layer denials. Score 96 (Concs 79→78 from added refusal-phrasing rule; overall unchanged). | 78 | 100 | 100 | 100 | 100 | 96 |
| 1.15.0 | 2026-06-06 | [#176](https://github.com/totallyGreg/claude-mp/issues/176) | Pass B (friction batch 2026-06-05). B1: fileClass validation gate (item 6) — re-read `_vault-profile.md` from disk per write (freshness), parse Active fileClasses (table→bullet→warn-and-skip), refuse+surface gap if value absent. B2: entity wikilink check (item 3a) — batch scan with stop-list, code-fence skip, ~20 cap, single consolidated end-of-scan prompt (no per-candidate blocking). B3: schema-change guard in §Write Boundaries — hard-stop on fileClass/folder-convention/template-schema creation, explicit vault-architect routing. Score 96 (Concs 80→79 from added prose, overall unchanged). | 79 | 100 | 100 | 100 | 100 | 96 |
| 1.14.0 | 2026-06-04 | [#160](https://github.com/totallyGreg/claude-mp/issues/160) | Add `duplicate-detection-thresholds.md` reference (canvas, similarity, coverage thresholds with tuning guidance); link from Find Similar Notes and Canvas Map Generation sections | 80 | 100 | 100 | 100 | 100 | 96 |
| 1.13.0 | 2026-05-03 | - | Add Write Quality Gate rule #5 (read before write), Drift Triage protocol (mechanical vs semantic), session-logging.md reference | 80 | 100 | 100 | 100 | 100 | 96 |
| 1.12.0 | 2026-04-14 | [#160](https://github.com/totallyGreg/claude-mp/issues/160) | Add collection-health-criteria.md reference; add --no-write to generate_canvas.py, merge_notes.py, redirect_links.py (50-file cap on redirect); add --node-width/--node-height/--coverage-threshold CLI args; add fileClass group nodes + edge direction markers to canvas | 83 | 100 | 100 | 100 | 100 | 96 |
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

