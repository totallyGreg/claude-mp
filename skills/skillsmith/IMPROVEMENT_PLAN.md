# Skillsmith - Improvement Plan

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
| 3.5.0 | 2026-01-24 | [#8](https://github.com/totallyGreg/claude-mp/issues/8) | Phase 2 validation improvements - deterministic scoring and reference validation | 64 | 90 | 100 | 100 | 89 |
| 3.4.0 | 2026-01-24 | [#7](https://github.com/totallyGreg/claude-mp/issues/7) | Add --strict validation mode and validation gate workflow | 48 | 90 | 100 | 100 | 85 |
| 3.3.0 | 2026-01-23 | [#6](https://github.com/totallyGreg/claude-mp/issues/6) | skillsmith v3.3.0 | 55 | 90 | 100 | 100 | 86 |
| 3.2.1 | 2026-01-23 | [#5](https://github.com/totallyGreg/claude-mp/issues/5) | Remove skill-planner references, adopt WORKFLOW.md pattern | 55 | 90 | 100 | 100 | 86 |
| 3.2.0 | 2026-01-18 | - | Added table-based IMPROVEMENT_PLAN.md format and workflow documentation | - | - | - | - | - |
| 1.8.0 | 2025-12-23 | - | Added AgentSkills specification as core domain knowledge | - | - | - | - | - |
| 1.7.0 | 2025-12-22 | - | Conciseness optimization - moved research documentation to references/ | 67 | - | - | - | 89 |
| 1.5.0 | 2025-12-20 | - | IMPROVEMENT_PLAN.md restructuring and rename to skillsmith | - | - | - | - | - |
| 1.4.0 | 2025-12-01 | - | IMPROVEMENT_PLAN.md validation and guidance with enhanced validation script | - | - | - | - | - |
| 1.3.0 | 2025-11-24 | - | Added IMPROVEMENT_PLAN.md as standard skill component with template generation | - | - | - | - | - |
| 1.2.0 | 2025-11-20 | - | Fixed script path detection with repository root auto-detection | - | - | - | - | - |
| 1.1.0 | 2025-11-20 | - | Added marketplace version sync automation with pre-commit hook | - | - | - | - | - |
| 1.0.0 | - | - | Initial release | - | - | - | - | - |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure (0-100 scale)

## Active Work

- [#8](https://github.com/totallyGreg/claude-mp/issues/8): Advanced validation features (Planning)
- [#10](https://github.com/totallyGreg/claude-mp/issues/10): Add interactive mode to skill template (Planning)
- [#11](https://github.com/totallyGreg/claude-mp/issues/11): Review and triage future enhancement ideas (Planning)

See GitHub Issues for detailed plans and task checklists.

## Known Issues

1. ~~**Directory name detection bug in evaluate_skill.py**~~ - **FIXED in Phase 1** - Changed `Path('.').name` to `Path(skill_path).resolve().name` for proper resolution. Verified with absolute, relative, and `.` path formats.

2. ~~**Deep nested reference false positives in validation**~~ - **RESOLVED in Phase 2** - Fixed pattern matching to only flag backtick-wrapped references as actual dependencies. Documentation examples are now ignored, preventing false positives.

3. **Low conciseness score (now 64/100, was 48/100)** - IMPROVED in Phase 2 - Conciseness improved +33% with tiered scoring logic and reference offloading bonus. Target: Further reduce SKILL.md from 309 to <250 lines in Phase 3.

Report new issues at https://github.com/totallyGreg/claude-mp/issues

## Archive

For complete development history:
- Git commit history: `git log --grep="skillsmith"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:enhancement+is:closed
- Cross-skill learnings: docs/lessons/

---

**Development Workflow:**

See repository `/WORKFLOW.md` for complete documentation on:
- GitHub Issues as source of truth for ALL planning
- IMPROVEMENT_PLAN.md format (this lightweight release notes + metrics)
- Two-commit release strategy
- Using `uv run scripts/evaluate_skill.py --export-table-row` to capture metrics
