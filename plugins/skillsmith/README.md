# skillsmith

Skill quality evaluation, improvement, and marketplace integration for Claude Code skills.

## Components

### Agent: skill-observer
Analyzes saved Claude Code session transcripts to identify where a skill failed to guide Claude effectively. Returns ranked structural gaps with installed→source path mapping.

### Skill: skillsmith
End-to-end skill development with automated quality metrics:
- Skill evaluation with scored dimensions (conciseness, complexity, spec compliance, progressive disclosure, description quality)
- Improvement loop: evaluate → apply fixes → re-evaluate → update README → bump version
- Marketplace sync via marketplace-manager
- Session transcript analysis for skill gap detection

### Commands (7)
`/ss-evaluate`, `/ss-improve`, `/ss-init`, `/ss-observe`, `/ss-package`, `/ss-research`, `/ss-validate`

### Hooks

| Hook | Trigger | Purpose |
|------|---------|---------|
| `on-skill-edit.sh` | PostToolUse Write\|Edit on `SKILL.md` | Quick skill quality evaluation; score fed back to Claude |
| `on-script-edit.sh` | PostToolUse Write\|Edit on `scripts/*.py` | Enforces PEP 723 header and bans `click`/`typer` (argparse standard) |

## Changelog

| Version | Changes |
|---------|---------|
| 6.5.0 | Add `/ss-package` command for skill.zip packaging; add `on-script-edit.sh` hook to enforce argparse + PEP 723 standard; document argparse standard in `python_uv_guide.md` |
| 6.4.0 | Previous release |
| 6.0.0 | Migrated to plugin structure with skill-observer agent |

## Skill: skillsmith

### Current Metrics

**Score: 100/100** (Excellent) — 2026-03-25

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 100 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 6.7.0 | 2026-03-25 | [#146](https://github.com/totallyGreg/claude-mp/issues/146) | Anthropic guide alignment: use-case definition template, description formula + bad examples, body structure template, 5 skill patterns reference, 3-area testing guide, negative trigger coaching, over/undertrigger --explain signals | 100 | 100 | 100 | 100 | 100 | 100 |
| 6.6.0 | 2026-03-22 | [#96](https://github.com/totallyGreg/claude-mp/issues/96), [#115](https://github.com/totallyGreg/claude-mp/issues/115), [#81](https://github.com/totallyGreg/claude-mp/issues/81), [#82](https://github.com/totallyGreg/claude-mp/issues/82), [#108](https://github.com/totallyGreg/claude-mp/issues/108), [#110](https://github.com/totallyGreg/claude-mp/issues/110) | Qualitative conciseness checks; context-aware ss-observe with --hint; orphan regex fix; IMPROVEMENT_PLAN.md migration; frontmatter auto-patch; commit-gate doc | 100 | 100 | 100 | 100 | 100 | 100 |
| 6.4.0 | 2026-03-19 | [#104](https://github.com/totallyGreg/claude-mp/issues/104) | Phase 6: self-application — all metrics 100/100; closes v6 improvement arc | 100 | 100 | 100 | 100 | 100 | 100 |
| 6.3.0 | 2026-03-19 | - | Phase 5: skill-observer agent + analyze_transcript.py + /ss-observe command | 100 | 100 | 100 | 100 | 100 | 100 |
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

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

