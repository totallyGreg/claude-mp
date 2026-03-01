# Omnifocus Manager - Improvement Plan

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
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

- [#63](https://github.com/totallyGreg/claude-mp/issues/63): Two-track vision — 4-pillar skill capabilities + OmniFocus plugin packaging (Planning)
  - Pillar 1: Query — JXA/Omni Automation live database inspection
  - Pillar 2: Perspectives — programmatic perspective creation from plain English
  - Pillar 3: GTD Coaching — project naming, next-action clarity, system health
  - Pillar 4: Plugins with UI + FM — packaging workflows as standalone plugins
  - Agent routing layer to dispatch user intent to the correct pillar

- [#62](https://github.com/totallyGreg/claude-mp/issues/62): Add dailyReview and weeklyReview actions to AITaskAnalyzer (Planning)
  - Add `dailyReview` action: completed today + GTD-specific FM coaching
  - Add `weeklyReview` action: 6-step guided GTD flow with FM at each step
  - Extend `taskMetrics.js`: `getCompletedThisWeek()`, `getStalledProjects()`, `getOnHoldProjects()`
  - Bump AITaskAnalyzer plugin to v3.4.0 (first Pillar 4 deliverable of #63)

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
