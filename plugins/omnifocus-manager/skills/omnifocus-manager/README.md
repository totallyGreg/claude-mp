# OmniFocus Manager

Query and manage OmniFocus tasks via Omni Automation script URLs (ofo CLI) and JXA, with GTD methodology coaching via the companion gtd-coach skill. The ofo CLI handles CRUD operations through a single-approval dispatcher, while gtd-queries.js provides diagnostic queries (system health, stalled projects, tag lookups) executed directly via osascript for fast results.

## Capabilities

- Execute OmniFocus task operations (create, complete, update, search, list) via ofo CLI
- Run GTD diagnostic queries (inbox, overdue, stalled, waiting, habits, tag queries) via osascript
- Generate OmniFocus Omni Automation plugins from specifications
- Configure and audit custom perspectives with GTD gap analysis
- Publish implementation plans as OmniFocus projects with phased action groups

## Current Metrics

*Last evaluated: 2026-03-20*

| Metric | Score | Interpretation |
|--------|-------|----------------|
| Conciseness | 98/100 | Excellent |
| Complexity | 90/100 | Good |
| Spec Compliance | 100/100 | Excellent |
| Progressive Disclosure | 100/100 | Excellent |
| Description Quality | 100/100 | Excellent |
| **Overall** | **97/100** | **Excellent** |

Run `uv run scripts/evaluate_skill.py <path> --explain` for improvement suggestions.

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Desc | Overall |
|---------|------|-------|---------|------|------|------|------|------|---------|
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

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure, Desc=Description Quality (0-100 scale)

## Active Work

None currently. See GitHub Issues for future work.

## Known Issues

None currently. Report issues at https://github.com/totallyGreg/claude-mp/issues

## Archive

- Git history: `git log --grep="omnifocus-manager"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:enhancement+is:closed
- Cross-skill learnings: `docs/lessons/`

---

*Run `uv run scripts/evaluate_skill.py <path> --update-readme` to refresh metrics.*
