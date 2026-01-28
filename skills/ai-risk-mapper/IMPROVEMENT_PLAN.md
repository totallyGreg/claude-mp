# AI Risk Mapper - Improvement Plan

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
| 1.1.0 | 2026-01-28 | [#2](https://github.com/totallyGreg/claude-mp/issues/2) | Add workflow automation, orchestrator script, bundled schemas, SSL offline fallback | 23 | 70 | ✓ | 100 | 71 |
| 1.0.0 | 2026-01-07 | - | Initial release with CoSAI framework integration, risk analysis, and multi-format reporting | 23 | 65 | ✓ | 100 | 67 |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure (0-100 scale)

## Active Work

- [#3](https://github.com/totallyGreg/claude-mp/issues/3): Restructure SKILL.md for conciseness (Open)

See GitHub Issues for detailed plans, task checklists, and discussion.

## Known Issues

- **Keyword-based risk detection:** `analyze_risks.py` uses simplified pattern matching; should be enhanced with semantic analysis
- **Network error handling:** Scripts lack comprehensive error handling for network failures and SSL certificate issues
- **Missing test coverage:** No automated tests for Python scripts
- **SSL certificate failures:** Corporate proxies can block schema downloads; needs graceful offline fallback
- **Documentation gaps:** Missing usage examples with real codebases, troubleshooting guide, and migration guide

## Archive

For complete development history:
- Git commit history: `git log --grep="ai-risk-mapper"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:skill:ai-risk-mapper+is:closed
- Cross-skill learnings: docs/lessons/
- Planning documents: docs/plans/
