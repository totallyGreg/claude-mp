# attache

Chief of Staff agent — personal advisor that orchestrates task management, delegates to specialist agents, learns workflow patterns, and manages the full tool stack. Built on the omnifocus-core foundation.

## Components

### Agent: attache
Routes between omnifocus-core (queries/task CRUD), omnifocus-generator (OmniFocus plugins), attache-analyst (system learning), gtd-coach (methodology), and sibling agents (archivist, terminal-guru) based on user intent. Invoke via `subagent_type="attache:attache"` — not the Skill tool.

### Skill: omnifocus-core
Stateless data access — task CRUD, queries, perspectives, reporting via ofo CLI.

### Skill: omnifocus-generator
OmniFocus Automation plugin and script generation (.omnifocusjs).

### Skill: attache-analyst
System learning, pattern detection, and AI-enhanced coaching.

### Skill: gtd-coach
Pure GTD methodology coaching without OmniFocus automation.

### Commands (13)
`/ofo-today`, `/ofo-overdue`, `/ofo-inbox`, `/ofo-health`, `/ofo-search`, `/ofo-info`, `/ofo-tagged`, `/ofo-plan`, `/ofo-work`, `/ofo-expound`, `/ofo-analyze-projects`, `/ofo-analyze-habits`, `/ofo-weekly-review`

## Changelog

| Version | Changes |
|---------|---------|
| 11.0.0 | **Attache rename**: omnifocus-manager → attache. Skill decomposition: omnifocus-core + omnifocus-generator + attache-analyst. Cross-tool delegation (archivist, terminal-guru). Tool stack awareness via Tools.base. Agent score 82/100. |
| 9.0.0 | ofoCore named exports, shared types, ofo dump/stats, open-based deploy |
| 8.4.0 | perspective-list, perspective-rules with ID resolution |
| 8.0.0 | TypeScript plugin library (ofo-core.ts), ofo CLI |
| 7.0.0 | Migrated to plugin structure with agent routing |

## Skill: gtd-coach

### Current Metrics

**Score: 91/100** (Good) — 2026-03-23

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 78 | 80 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.4.0 | 2026-03-23 | [#138](https://github.com/totallyGreg/claude-mp/issues/138) | Add Repeating Tasks & Ticklers section: schedule types, Catch Up Automatically, generic tickler patterns, overdue signal interpretation | 78 | 80 | 100 | 100 | 100 | 91 |
| 1.1.1 | 2026-03-19 | — | Re-eval: no changes, score improved with evaluator updates | 93 | 90 | 100 | 100 | 100 | 96 |
| 1.1.0 | 2026-02-28 | #63 | Add Data-Grounded Coaching section with gtd-queries.js command table | 78 | 80 | 80 | 100 | - | 85 |
| 1.0.0 | 2026-02-28 | #63 | Initial release — pure GTD methodology coaching skill | 78 | 80 | 80 | 100 | - | 81 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)


## Skill: omnifocus-core

### Current Metrics

**Score: 94/100** (Good) — 2026-04-09

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 83 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 10.4.1 | 2026-04-09 | - | Doc: add missing --note (replace) to ofo update command table; --note-append already documented | 83 | 90 | 100 | 100 | 100 | 94 |
| 10.4.0 | 2026-04-09 | - | Agent: add inline-script RED FLAG (tool-agnostic wording) to Pillar 4, add structured-project → bulk-create intent row, make agent default entry point in CLAUDE.md |
| 10.3.0 | 2026-04-09 | - | Add RED FLAG gate: inline Omni Automation script → STOP, check ofo CLI or use bulk-create for structured projects; strengthen STEP 1 classify to route structured-project creation explicitly | 83 | 90 | 100 | 100 | 100 | 94 |
| 10.2.0 | 2026-03-23 | [#138](https://github.com/totallyGreg/claude-mp/issues/138) | Add ofo health single-call command (fixes pasteboard collision), document single-action pattern for slash commands | 83 | 90 | 100 | 100 | 100 | 94 |
| 10.1.0 | 2026-03-23 | [#138](https://github.com/totallyGreg/claude-mp/issues/138) | Add ofo drop command, enrich OfoTask with repetitionCatchUp/repetitionScheduleType, Catch Up-aware health diagnostics, api_reference Catch Up docs | 83 | 90 | 100 | 100 | 100 | 94 |
| 10.0.0 | 2026-03-23 | [#136](https://github.com/totallyGreg/claude-mp/issues/136) | Attache Plugin Consolidation: merge ofo-core into Attache (single plugin, one deploy), canonical 16-field normalizeTask with Date objects, all 10 libraries compiled from TypeScript, insightPatterns included, WAITING_PREFIXES unified, delete obsolete files/references | 83 | 90 | 100 | 100 | 100 | 94 |
| 9.4.1 | 2026-03-23 | [#114](https://github.com/totallyGreg/claude-mp/issues/114) | Fix CLI distribution: track build artifacts in git, update build/.gitignore to ship ofo-cli.js/ofo-stub.js/ofo-types.js to marketplace cache | 83 | 90 | 100 | 100 | 100 | 94 |
| 9.4.0 | 2026-03-23 | [#111](https://github.com/totallyGreg/claude-mp/issues/111) | TypeScript shared sync: ofo-contract.d.ts, normalizeTask/computeStats, assessClarity/stalledProjects CLI cmds, Attache @ts-check gate (tsconfig.attache.json + omni-attache-ambient.d.ts, 0 errors), fix 10 orphaned SKILL.md refs, update code_generation_validation.md build pipeline | 83 | 90 | 100 | 100 | 100 | 94 |
| 9.3.1 | 2026-03-22 | - | Version-stamp System Map, post-deploy refresh instructions, Attache v1.3.0, build process cleanup | 83 | 90 | 100 | 100 | 100 | 94 |
| 9.3.0 | 2026-03-22 | [#125](https://github.com/totallyGreg/claude-mp/issues/125) | Expose native OmniFocus fields: plannedDate, repetitionRule, reviewInterval, estimatedMinutes in list views, enriched stats, systemDiscovery tag split, Attache v1.2.0 | 83 | 90 | 100 | 100 | 100 | 94 |
| 9.2.1 | 2026-03-22 | - | Add plugin version bump rule to generation workflow and conventions | 83 | 90 | 100 | 100 | 100 | 94 |
| 9.2.0 | 2026-03-22 | [#123](https://github.com/totallyGreg/claude-mp/issues/123) | omnifocus-agent System Map bootstrap: lazy Attache System Map retrieval, TIME_PATTERNS split (duration vs. scheduling-context), durationModel derivation, fix Execution Rules to ofo-first hierarchy, ofo stats fast health check, gtd-coach System Context section (v1.3.0) | 98 | 90 | 100 | 100 | 100 | 97 |
| 9.1.0 | 2026-03-22 | [#121](https://github.com/totallyGreg/claude-mp/issues/121) | Script consolidation: delete 4 orphan scripts; ofo list due-soon + update --note-append; fix dead refs in ofo-expound/ofo-plan; update agent routing table + jxa_guide + gtd_guide + CONTRIBUTING.md to ofo CLI | 98 | 90 | 100 | 100 | 100 | 97 |
| 9.0.0 | 2026-03-21 | [#119](https://github.com/totallyGreg/claude-mp/issues/119) | ofoCore named exports (14 functions); shared OfoAction types; ofo dump/stats commands; deploy to iCloud+Containers; CONTRIBUTING.md null-guard pattern; library_ecosystem.md; Attache v1.1.0 | 98 | 90 | 100 | 100 | 100 | 97 |
| 8.4.0 | 2026-03-21 | - | Add ofo perspective-list and perspective-rules commands (with folder/tag ID resolution); document Flexible vs Organized structure; add perspective troubleshooting section; fix perspective-config.js runtime warning | 98 | 90 | 100 | 100 | 100 | 97 |
| 8.3.0 | 2026-03-21 | - | ofo perspective-rules: TypeScript ofo-core action resolving actionWithinFocus/actionHasAnyOfTags IDs to named markdown links | 98 | 90 | 100 | 100 | 100 | 97 |
| 8.2.0 | 2026-03-20 | — | Add perspective-configure action, completed-today CLI command (perspectives-over-scripts pattern); fix license frontmatter placement | 98 | 90 | 100 | 100 | 100 | 97 |
| 8.1.0 | 2026-03-19 | [#116](https://github.com/totallyGreg/claude-mp/pull/116) | ofo CLI: tag command with capture shortcuts, tags hierarchy, create-batch; fix flattenedTags global | 100 | 90 | 90 | 100 | 100 | 95 |
| 8.0.0 | 2026-03-19 | [#111](https://github.com/totallyGreg/claude-mp/issues/111) | Migrate ofo CLI to TypeScript plugin library: ofo-core.ts (7 actions), ofo-cli.ts (arg parsing), installed .omnifocusjs bundle, stable stub script, zero auth prompts after checkbox; CONTRIBUTING.md rewrite | 100 | 90 | 90 | 100 | 100 | 95 |
| 7.5.0 | 2026-03-19 | [#98](https://github.com/totallyGreg/claude-mp/issues/98), [#101](https://github.com/totallyGreg/claude-mp/issues/101) | Tag query perf: flattenedTasks→tag.tasks() (563x speedup), whose() crash fix; consolidate 7 action scripts into ofo-dispatcher.js, remove ofo setup; add /ofo-tagged command; CONTRIBUTING.md; inbox filter fix | 100 | 90 | 90 | 100 | 100 | 95 |
| 7.4.3 | 2026-03-15 | — | ofo-work: use `ofo complete` (Omni Automation) not `manage_omnifocus.js complete` (JXA) — fixes -10003 permission error | 83 | 90 | 90 | 100 | - | 91 |
| 7.4.2 | 2026-03-14 | — | jxa_guide.md: Unicode tag matching, add/remove tag API gotchas; antipattern rule for exact tag name match | 83 | 90 | 90 | 100 | - | 91 |
| 7.4.1 | 2026-03-09 | [#99](https://github.com/totallyGreg/claude-mp/issues/99) | Fix tag lookup: Tag has no flattenedTasks; use remainingTasks | 83 | 90 | 90 | 100 | - | 91 |
| 7.4.0 | 2026-03-09 | [#99](https://github.com/totallyGreg/claude-mp/issues/99) | ofo info tag URL support: detect_type_from_url adds tag branch; ofo-info.js adds Tag.byIdentifier() lookup | 83 | 90 | 90 | 100 | - | 91 |
| 7.3.0 | 2026-03-09 | - | Update omnifocus-agent.md: add /ofo:plan, /ofo:work, /ofo:weekly-review routing entries | 83 | 90 | 90 | 100 | - | 91 |
| 7.2.0 | 2026-03-09 | [#98](https://github.com/totallyGreg/claude-mp/issues/98) | Fix 8 remaining weak filters in taskQuery.js: upgrade to triple-check pattern | 83 | 90 | 90 | 100 | - | 91 |
| 7.1.0 | 2026-03-09 | [#97](https://github.com/totallyGreg/claude-mp/issues/97) | Fix query accuracy: inbox filters, overdue excludes repeating instances; new ofo-perspective.js | 83 | 90 | 90 | 100 | - | 91 |
| 7.0.1 | 2026-03-09 | - | Fix ofo-list.js filters; trim SKILL.md (257→209 lines) | 83 | 90 | 90 | 100 | - | 91 |
| 7.0.0 | 2026-03-09 | [#94](https://github.com/totallyGreg/claude-mp/issues/94) | ofo CLI: Omni Automation script URL execution replacing JXA for core CRUD | 83 | 87 | 90 | 100 | - | 91 |
| 6.6.1 | 2026-03-08 | [#93](https://github.com/totallyGreg/claude-mp/issues/93) | Attache v1.0.4: fix plugin loading | - | - | - | - | - | - |
| 6.6.0 | 2026-03-08 | - | Attache v1.0.0: unified OmniFocus AI plugin (9 actions, 9 libraries) | 83 | 88 | 90 | 100 | - | 91 |
| 6.5.0 | 2026-03-08 | [#84](https://github.com/totallyGreg/claude-mp/issues/84) | Add 6 ofo: slash commands; rename to ofo: prefix | 83 | 88 | 90 | 100 | - | 91 |
| 6.4.0 | 2026-03-07 | [#90](https://github.com/totallyGreg/claude-mp/issues/90) | Phase 1 GTD analysis commands: repeating-tasks + analyze-projects | 83 | 88 | 90 | 100 | - | 91 |
| 6.3.0 | 2026-03-07 | - | Rewrite foundation_models_integration.md with accurate API docs | 83 | 88 | 90 | 100 | - | 91 |
| 6.2.0 | 2026-03-04 | [#80](https://github.com/totallyGreg/claude-mp/issues/80) | Pillar 2 — Perspective inventory, configuration, templates, GTD gap analysis | 30 | 55 | 90 | 100 | - | 74 |
| 6.1.0 | 2026-03-03 | [#76](https://github.com/totallyGreg/claude-mp/issues/76) | Channel Selection Layer + JXA anti-pattern checker + security hardening | 30 | 59 | 90 | 100 | - | 74 |
| 6.0.0 | 2026-03-02 | [#73](https://github.com/totallyGreg/claude-mp/issues/73) | /of:plan, /of:work commands + task-sync hook | 55 | 64 | 90 | 100 | - | 80 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

