# skillsmith

Skillsmith is the default companion for skill development and improvement workflows. It evaluates skill quality across five structural metrics, provides per-metric coaching via `--explain` mode, and generates per-skill README.md documentation. Use skillsmith when editing, validating, or improving any skill in this repository — it owns the Evaluate and Iterate steps of the plugin-dev six-step loop.

## Capabilities

- Evaluate skill quality with five automated metrics (conciseness, complexity, spec compliance, progressive disclosure, description quality)
- Explain per-metric scores with actionable improvements and estimated score impact (`--explain`)
- Generate or update per-skill README.md with current metrics and version history (`--update-readme`)
- Validate skill structure, references, and spec compliance (`--validate-references`)
- Detect consolidation opportunities across reference files (`--detect-duplicates`)
- Initialize new skills from templates with README.md, references/, scripts/, and examples/ directories
- Guide the full improvement loop: evaluate → explain → fix → re-evaluate → update README → sync marketplace

## Current Metrics

*Last evaluated: 2026-03-19*

| Metric | Score | Interpretation |
|--------|-------|----------------|
| Conciseness | 100/100 | Excellent |
| Complexity | 100/100 | Excellent |
| Spec Compliance | 100/100 | Excellent |
| Progressive Disclosure | 100/100 | Excellent |
| Description Quality | 100/100 | Excellent |
| **Overall** | **100/100** | **Excellent** |

Run `uv run scripts/evaluate_skill.py <path> --explain` for improvement suggestions.

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Desc | Overall |
|---------|------|-------|---------|------|------|------|------|------|---------|
| 6.2.0 | 2026-03-19 | - | Phase 4: PostToolUse hook on SKILL.md edits; /ss-improve unified improvement loop command | 100 | 100 | 100 | 100 | 100 | 100 |
| 6.1.0 | 2026-03-19 | - | Phase 3: SKILL.md rewrite — plugin-dev 6-step loop backbone, routing table, improvement-specific trigger phrases; delete research_guide.md | 100 | 100 | 100 | 100 | 100 | 100 |
| 6.0.0 | 2026-03-19 | - | **BREAKING**: README.md replaces IMPROVEMENT_PLAN.md; delete deprecated scripts; idempotent --update-readme; Desc column in --export-table-row | 100 | 100 | 100 | 100 | 100 | 100 |
| 5.3.0 | 2026-03-18 | [#104](https://github.com/totallyGreg/claude-mp/issues/104) | Phase 1: fix 5 metric weaknesses; add --explain, --validate-references, --detect-duplicates, --update-readme flags; generate README.md | 100 | 100 | 100 | 100 | 100 | 100 |
| 5.2.1 | 2026-03-14 | - | Fix `validate_skill()` in evaluate_skill.py: replace regex frontmatter parsing with `yaml.safe_load()` | - | - | - | - | - | - |
| 5.2.0 | 2026-02-24 | [#55](https://github.com/totallyGreg/claude-mp/issues/55) | Support remote GitLab/GitHub URLs in evaluate_skill.py | 55 | 77 | 100 | 100 | - | 86 |
| 5.1.0 | 2026-02-16 | [#32](https://github.com/totallyGreg/claude-mp/issues/32) | Add "When NOT to use" redirect section | 55 | 77 | 100 | 100 | - | 86 |
| 5.0.0 | 2026-02-05 | [#33](https://github.com/totallyGreg/claude-mp/issues/33) | Align with official plugin-dev patterns: add Description Quality Score, trigger phrase validation, Common Mistakes section | 56 | 77 | 100 | 100 | - | 86 |
| 4.0.0 | 2026-02-03 | [#28](https://github.com/totallyGreg/claude-mp/issues/28), [#16](https://github.com/totallyGreg/claude-mp/issues/16) | **BREAKING**: Migrate to standalone plugin structure; add slash commands | 80 | 90 | 100 | 100 | - | 93 |
| 3.7.2 | 2026-01-29 | [#24](https://github.com/totallyGreg/claude-mp/issues/24) | Phase 1 script consolidation - deprecated validate_workflow.py, audit_improvements.py | 80 | 90 | 100 | 100 | - | 93 |
| 3.7.0 | 2026-01-25 | [#8](https://github.com/totallyGreg/claude-mp/issues/8) | Phase 4 command integration - unified validation workflow | 81 | 90 | 100 | 100 | - | 93 |
| 3.6.0 | 2026-01-25 | [#8](https://github.com/totallyGreg/claude-mp/issues/8) | Phase 3 content consolidation - reduced SKILL.md | 81 | 90 | 100 | 100 | - | 93 |
| 3.5.0 | 2026-01-24 | [#8](https://github.com/totallyGreg/claude-mp/issues/8) | Phase 2 validation improvements - deterministic scoring and reference validation | 64 | 90 | 100 | 100 | - | 89 |
| 3.4.0 | 2026-01-24 | [#7](https://github.com/totallyGreg/claude-mp/issues/7) | Add --strict validation mode and validation gate workflow | 48 | 90 | 100 | 100 | - | 85 |
| 3.3.0 | 2026-01-23 | [#6](https://github.com/totallyGreg/claude-mp/issues/6) | skillsmith v3.3.0 | 55 | 90 | 100 | 100 | - | 86 |
| 3.2.1 | 2026-01-23 | [#5](https://github.com/totallyGreg/claude-mp/issues/5) | Remove skill-planner references, adopt WORKFLOW.md pattern | 55 | 90 | 100 | 100 | - | 86 |
| 3.2.0 | 2026-01-18 | - | Added table-based README.md format and workflow documentation | - | - | - | - | - | - |
| 1.8.0 | 2025-12-23 | - | Added AgentSkills specification as core domain knowledge | - | - | - | - | - | - |
| 1.7.0 | 2025-12-22 | - | Conciseness optimization - moved research documentation to references/ | 67 | - | - | - | - | 89 |
| 1.5.0 | 2025-12-20 | - | Initial restructuring and rename to skillsmith | - | - | - | - | - | - |
| 1.4.0 | 2025-12-01 | - | Validation and guidance with enhanced validation script | - | - | - | - | - | - |
| 1.3.0 | 2025-11-24 | - | Added README.md as standard skill component with template generation | - | - | - | - | - | - |
| 1.2.0 | 2025-11-20 | - | Fixed script path detection with repository root auto-detection | - | - | - | - | - | - |
| 1.1.0 | 2025-11-20 | - | Added marketplace version sync automation with pre-commit hook | - | - | - | - | - | - |
| 1.0.0 | - | - | Initial release | - | - | - | - | - | - |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure, Desc=Description Quality (0-100 scale)

## Active Work

- [#104](https://github.com/totallyGreg/claude-mp/issues/104): skillsmith v6 — Phase 5: Transcript-Replay Observation Agent (Next)

See GitHub Issues for detailed plans and task checklists.

## Known Issues

No open issues. See [GitHub Issues](https://github.com/totallyGreg/claude-mp/issues?q=label:skillsmith+is:open) for the current tracker.

## Archive

- Git history: `git log --grep="skillsmith"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:enhancement+is:closed
- Cross-skill learnings: `docs/lessons/`

---

*Generated by skillsmith on 2026-03-19. Run `uv run scripts/evaluate_skill.py <path> --update-readme` to refresh.*
