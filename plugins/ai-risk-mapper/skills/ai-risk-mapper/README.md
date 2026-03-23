# ai-risk-mapper

This skill identifies, analyzes, and mitigates security risks in AI systems using the CoSAI (Coalition for Secure AI) Risk Map framework. It is the go-to tool when a developer needs to assess threats against LLM applications, ML pipelines, or model training/serving infrastructure. What sets it apart is its ability to map findings to multiple compliance frameworks simultaneously — MITRE ATLAS, NIST AI RMF, OWASP Top 10 for LLM, STRIDE, and ISO 22989 — while supporting both automated orchestration and interactive CLI exploration.

## Capabilities

- Run automated end-to-end risk assessments against a codebase, directory, or system description via the orchestrator script
- Search risks and controls by keyword using interactive CLI tools
- Generate persona-specific risk profiles across 8 ISO 22989 stakeholder roles (e.g. ModelProvider, ApplicationDeveloper)
- Perform gap analysis to identify missing controls for a given risk with coverage percentages
- Map any risk to external framework identifiers (MITRE ATLAS, NIST AI RMF, OWASP, STRIDE)
- Operate fully offline using bundled CoSAI schema assets with automatic SSL/network fallback

## Current Metrics

*Last evaluated: 2026-03-22*

| Metric | Score | Interpretation |
|--------|-------|----------------|
| Conciseness | 100/100 | Excellent |
| Complexity | 88/100 | Good |
| Spec Compliance | 100/100 | Excellent |
| Progressive Disclosure | 100/100 | Excellent |
| Description Quality | 100/100 | Excellent |
| **Overall** | **97/100** | **Excellent** |

Run `uv run scripts/evaluate_skill.py <path> --explain` for improvement suggestions.

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Desc | Overall |
|---------|------|-------|---------|------|------|------|------|------|---------|
| 5.1.0 | 2026-03-05 | [#85](https://github.com/totallyGreg/claude-mp/issues/85) | Sync upstream: bundle 3 YAML enum files + riskmap.schema.json (9+11), fix deprecated persona refs in docs, add deprecation warning in CLI, add commit-hash README | 98 | 88 | 100 | 100 | - | 97 |
| 5.0.0 | 2026-02-25 | [#56](https://github.com/totallyGreg/claude-mp/issues/56) | Refresh CoSAI upstream data: 8-persona model (ISO 22989), fix lifecycle/impact parsing bugs, add frameworks.yaml, rewrite exploration guide and personas guide | 98 | 88 | 100 | 100 | - | 93 |
| 4.0.1 | 2026-02-04 | - | Fix: use absolute paths with ${CLAUDE_PLUGIN_ROOT} in SKILL.md | 98 | 88 | 100 | 100 | - | 97 |
| 4.0.0 | 2026-02-04 | [#31](https://github.com/totallyGreg/claude-mp/issues/31) | Migrate to standalone plugin structure, add 6 slash commands | 100 | 88 | 100 | 100 | - | 97 |
| 3.0.1 | 2026-01-29 | - | Fix: rename FORMS.md→forms.md, add .skillignore | 98 | 88 | 100 | 100 | - | 97 |
| 3.0.0 | 2026-01-28 | - | Merge cosai-risk-analyzer: core_analyzer.py (30+ query methods), 6 CLI commands, gap analysis, persona profiles, exploration_guide.md | 60+ | 70 | ✓ | 100 | - | 77+ |
| 2.0.0 | 2026-01-28 | [#3](https://github.com/totallyGreg/claude-mp/issues/3) | Restructure SKILL.md for conciseness: 539→219 lines, 4585→1892 tokens, action-oriented format, workflow_guide.md reference | 60+ | 70 | ✓ | 100 | - | 77 |
| 1.1.0 | 2026-01-28 | [#2](https://github.com/totallyGreg/claude-mp/issues/2) | Add workflow automation, orchestrator script, bundled schemas, SSL offline fallback | 23 | 70 | ✓ | 100 | - | 71 |
| 1.0.0 | 2026-01-07 | - | Initial release with CoSAI framework integration, risk analysis, and multi-format reporting | 23 | 65 | ✓ | 100 | - | 67 |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure, Desc=Description Quality (0-100 scale)

## Active Work

- [#22](https://github.com/totallyGreg/claude-mp/issues/22): Semantic risk detection enhancement (pending)

## Known Issues

- **Keyword-based risk detection:** `analyze_risks.py` uses simplified pattern matching; should be enhanced with semantic analysis (v2.1.0+)
- **Missing test coverage:** No automated tests for Python scripts (v2.1.0+)
- **Troubleshooting guide:** Missing detailed troubleshooting documentation for common error scenarios (v2.1.0+)

## Archive

- Git history: `git log --grep="ai-risk-mapper"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:enhancement+is:closed

---

*Run `uv run scripts/evaluate_skill.py <path> --update-readme` to refresh metrics.*
