# Terminal-Guru - Improvement Plan

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
| 2.1.0 | 2026-02-08 | #12 | Add zsh function patterns, completion guide, and Plugin Standard references; add function generation triggers to SKILL.md | 33 | 66 | 80 | 100 | 69 |
| 2.0.0 | 2025-11-20 | - | Initial release with terminal diagnostics and zsh configuration support | 20 | 66 | 80 | 100 | 66 |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure (0-100 scale)

## Active Work

- [#12](https://github.com/totallyGreg/claude-mp/issues/12): Migrate and triage planned improvements (In Progress)
  - ✅ Zsh function patterns reference created (`references/zsh_function_patterns.md`)
  - ✅ Zsh completion guide created (`references/zsh_completion_guide.md`)
  - ✅ Plugin Standard conventions added to `references/zsh_configuration.md`
  - ✅ SKILL.md updated with function generation trigger phrases
  - Remaining: Triage zsh testing framework design document
  - Remaining: Archive design doc to `docs/plans/2025-11-20-zsh-testing-framework.md`

See GitHub Issues for detailed plans and task checklists.

## Known Issues

None currently. Report issues at https://github.com/totallyGreg/claude-mp/issues

## Archive

For complete development history:
- Git commit history: `git log --grep="terminal-guru"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:enhancement+is:closed
- Cross-skill learnings: docs/lessons/
- Previous planning: docs/plans/2025-11-20-zsh-testing-framework.md (comprehensive design document)
- v2.1.0 planning: docs/plans/2026-02-06-terminal-guru-zsh-function-generation.md

---

**Development Workflow:**

See repository `/WORKFLOW.md` for complete documentation on:
- GitHub Issues as source of truth for ALL planning
- IMPROVEMENT_PLAN.md format (this lightweight release notes + metrics)
- Two-commit release strategy
- Using `uv run skills/skillsmith/scripts/evaluate_skill.py --export-table-row` to capture metrics
