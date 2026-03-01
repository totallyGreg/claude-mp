# GTD Coach - Improvement Plan

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
| 1.1.0 | 2026-02-28 | #63 | Add Data-Grounded Coaching section with gtd-queries.js command table | 78 | 80 | 80 | 100 | 85 |
| 1.0.0 | 2026-02-28 | #63 | Initial release — pure GTD methodology coaching skill | 78 | 80 | 80 | 100 | 81 |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure (0-100 scale)

## Active Work

- [#63](https://github.com/totallyGreg/claude-mp/issues/63): Four-pillar vision — GTD coaching is Pillar 3
  - ~~Pillar 1 Query integration~~ — Done (v1.1.0, Data-Grounded Coaching section with gtd-queries.js)

See GitHub Issues for detailed plans and task checklists.

## Known Issues

None currently. Report issues at https://github.com/totallyGreg/claude-mp/issues

## Archive

For complete development history:
- Git commit history: `git log --grep="gtd-coach"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:enhancement+is:closed

---

**Development Workflow:**

See repository `/WORKFLOW.md` for complete documentation on:
- GitHub Issues as source of truth for ALL planning
- IMPROVEMENT_PLAN.md format (this lightweight release notes + metrics)
- Two-commit release strategy
- Using `uv run skills/skillsmith/scripts/evaluate_skill.py --export-table-row` to capture metrics
