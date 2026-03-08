# Omnifocus Manager - Improvement Plan

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
| 6.4.1 | 2026-03-08 | - | Fix getOverdueTasks: use effectivelyCompleted/effectivelyDropped to exclude tasks in dropped/completed projects; eliminates false positives from archived recurring tasks | - | - | - | - | - |
| 6.4.0 | 2026-03-07 | [#90](https://github.com/totallyGreg/claude-mp/issues/90) | Phase 1 GTD analysis commands: repeating-tasks + analyze-projects in gtd-queries.js; habit cadence math (RRULE parsing, gapRatio, stdDev) in taskQuery.js; /of:analyze-habits, /of:analyze-projects, /of:expound slash commands; agent routing updates | 83 | 88 | 90 | 100 | 91 |
| 6.3.0 | 2026-03-07 | - | Rewrite foundation_models_integration.md with accurate API docs: macOS 26 requirement, LanguageModel.Session, Schema.fromJSON (arrayOf/anyOf/isOptional/maximumElements), GenerationOptions, async pattern, per-call session pattern; remove Shortcuts bridge speculation; update SKILL.md references | 83 | 88 | 90 | 100 | 91 |
| 6.2.0 | 2026-03-04 | [#80](https://github.com/totallyGreg/claude-mp/issues/80) | Pillar 2 — Perspective inventory, configuration, templates, GTD gap analysis; perspective-config.js; system-health perspective warnings | 30 | 55 | 90 | 100 | 74 |
| 6.1.0 | 2026-03-03 | [#76](https://github.com/totallyGreg/claude-mp/issues/76) | Channel Selection Layer + JXA anti-pattern checker + security hardening; fix clearTags/addTag/whose bugs; loadLibrary path validation; URL scheme security docs | 30 | 59 | 90 | 100 | 74 |
| 6.0.0 | 2026-03-02 | [#73](https://github.com/totallyGreg/claude-mp/issues/73) | /of:plan, /of:work commands + task-sync hook; nested tags, bulk-create, ai-agent-tasks | 55 | 64 | 90 | 100 | 80 |
| 5.5.0 | 2026-03-02 | #71 | Fix weekly-review CWD bug; standardize loadLibrary docs + Script Conventions in SKILL.md; add test-queries.sh smoke test | - | - | - | - | - |
| 5.4.3 | 2026-03-01 | - | Fix /weekly-review: use direct script execution + CLAUDE_PLUGIN_ROOT pattern for allowed-tools | - | - | - | - | - |
| 5.4.0 | 2026-03-01 | - | Add /weekly-review command: parallel data collection, clipboard + OmniFocus note output | 62 | 67 | 90 | 100 | 82 |
| 5.3.0 | 2026-03-01 | #68 | Add project-info, project-update, batch-update commands; create --parent-id | 62 | 67 | 90 | 100 | 82 |
| 5.2.0 | 2026-03-01 | - | Unify manage_omnifocus.js with JXA library; delete omnifocus.js + query_omnifocus.py | 68 | 71 | 90 | 100 | 84 |
| 5.1.0 | 2026-02-28 | #63 | Add gtd-queries.js (8 GTD diagnostic actions) + 7 new taskQuery project functions | 68 | 71 | 90 | 100 | 84 |
| 5.0.0 | 2026-02-28 | #63 | Split GTD coaching into gtd-coach skill, four-pillar architecture, omnifocus-agent | 73 | 76 | 90 | 100 | 82 |
| 4.5.0 | 2026-02-27 | #62 | AITaskAnalyzer v3.4.0: dailyReview + weeklyReview actions | 80 | 78 | 90 | 100 | 84 |
| 4.4.0 | 2026-01-18 | - | Deterministic plugin generation workflow, Agent Skill compliance | 76 | 78 | 90 | 100 | 86 |
| 4.1.0 | 2026-01-11 | - | OmniFocus 4 tree API support, bundle generation fixes | - | - | - | - | - |
| 4.0.0 | 2026-01-02 | - | TypeScript-based plugin generation with LSP validation | - | - | - | - | - |
| 3.5.0 | 2026-01-02 | - | Comprehensive plugin generation: all formats (solitary/bundle) | - | - | - | - | - |
| 3.4.2 | 2025-12-31 | - | Integrated linting validation and API anti-pattern warnings | - | - | - | - | - |
| 3.4.1 | 2025-12-31 | - | Added plugin generator and templates for <1 min creation | - | - | - | - | - |
| 3.4.0 | 2025-12-31 | - | Fixed contradictory examples (eliminated Document.defaultDocument) | - | - | - | - | - |
| 3.2.0 | 2025-12-31 | - | API documentation restructuring, code generation validation | - | - | - | - | - |
| 3.1.0 | 2025-12-31 | - | Official template integration, plugin development workflow | - | - | - | - | - |
| 1.3.6 | 2025-12-28 | - | Added PlugIn API reference with validation checklist | - | - | - | - | - |
| 1.3.5 | 2025-12-28 | - | Added PlugIn.Library API reference for shared plugin modules | - | - | - | - | - |
| 1.3.4 | 2025-12-28 | - | Enhanced plugin documentation with .omnijs extension | - | - | - | - | - |
| 1.3.3 | 2025-12-28 | - | Added automation best practices reference | - | - | - | - | - |
| 1.3.2 | 2025-12-27 | - | Added comprehensive plugin bundle structure documentation | - | - | - | - | - |
| 1.3.1 | 2025-12-24 | - | Reorganized skill structure for AgentSkills compliance | - | - | - | - | - |
| 1.1.0 | 2025-12-21 | - | Major quality improvements, new references, task templates | - | - | - | - | - |
| 1.0.0 | 2025-12-19 | - | Initial release | - | - | - | - | - |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure (0-100 scale)

## Active Work

- ~~[#90](https://github.com/totallyGreg/claude-mp/issues/90): Phase 1 GTD Analysis Commands — habit cadence, project sweep, expound~~ — Done (v6.4.0)

- ~~[#68](https://github.com/totallyGreg/claude-mp/issues/68): Project inspection & mutation CLI commands~~ — Done (v5.3.0, PR #69)
- ~~[#63](https://github.com/totallyGreg/claude-mp/issues/63): Two-track vision~~ — All 4 pillars complete
  - ~~Pillar 3: GTD Coaching~~ — Done (v5.0.0, PR #65, gtd-coach skill)
  - ~~Agent routing~~ — Done (v5.0.0, PR #65, omnifocus-agent)
  - ~~Pillar 4: Plugins with UI + FM~~ — Done (v4.5.0, #62, AITaskAnalyzer v3.4.0)
  - ~~Pillar 1: Query~~ — Done (v5.1.0, PR #66, gtd-queries.js + taskQuery project functions)
  - ~~Pillar 2: Perspectives~~ — Done (v6.2.0, #80, perspective-config.js + perspective-inventory + templates)

- ~~[#73](https://github.com/totallyGreg/claude-mp/issues/73): /of:plan and /of:work commands + task-sync hook~~ — Done (v6.0.0)

See GitHub Issues for detailed plans and task checklists.

## Known Issues

None currently. Report issues at https://github.com/totallyGreg/claude-mp/issues

## Archive

For complete development history:
- Git commit history: `git log --grep="omnifocus"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:enhancement+is:closed
- Cross-skill learnings: docs/lessons/
- Previous detailed release notes: See git history for v4.4.0 and earlier comprehensive documentation

---

**Development Workflow:**

See repository `/WORKFLOW.md` for complete documentation on:
- GitHub Issues as source of truth for ALL planning
- IMPROVEMENT_PLAN.md format (this lightweight release notes + metrics)
- Two-commit release strategy
- Using `uv run skills/skillsmith/scripts/evaluate_skill.py --export-table-row` to capture metrics
