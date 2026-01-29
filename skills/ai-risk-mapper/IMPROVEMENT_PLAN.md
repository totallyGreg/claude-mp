# AI Risk Mapper - Improvement Plan

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
| 3.0.1 | 2026-01-29 | - | Fix: rename FORMS.md→forms.md, add .skillignore | 98 | 88 | 100 | 100 | 97 |
| 3.0.0 | 2026-01-28 | - | Merge cosai-risk-analyzer: core_analyzer.py (30+ query methods), 6 CLI commands, gap analysis, persona profiles, exploration_guide.md | 60+ | 70 | ✓ | 100 | 77+ |
| 2.0.0 | 2026-01-28 | [#3](https://github.com/totallyGreg/claude-mp/issues/3) | Restructure SKILL.md for conciseness: 539→219 lines, 4585→1892 tokens, action-oriented format, workflow_guide.md reference | 60+ | 70 | ✓ | 100 | 77 |
| 1.1.0 | 2026-01-28 | [#2](https://github.com/totallyGreg/claude-mp/issues/2) | Add workflow automation, orchestrator script, bundled schemas, SSL offline fallback | 23 | 70 | ✓ | 100 | 71 |
| 1.0.0 | 2026-01-07 | - | Initial release with CoSAI framework integration, risk analysis, and multi-format reporting | 23 | 65 | ✓ | 100 | 67 |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure (0-100 scale)

## Active Work

- [#4](https://github.com/totallyGreg/claude-mp/issues/4): Semantic risk detection enhancement (pending)

See GitHub Issues for detailed plans, task checklists, and discussion.

## Known Issues

- **Keyword-based risk detection:** `analyze_risks.py` uses simplified pattern matching; should be enhanced with semantic analysis (v2.1.0+)
- **Missing test coverage:** No automated tests for Python scripts (v2.1.0+)
- **Troubleshooting guide:** Missing detailed troubleshooting documentation for common error scenarios (v2.1.0+)

## Archive

For complete development history:
- Git commit history: `git log --grep="ai-risk-mapper"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:skill:ai-risk-mapper+is:closed
- Cross-skill learnings: docs/lessons/
- Planning documents: docs/plans/
