# foundry

Plugin development lifecycle toolkit — evaluate, improve, and publish skills and agents.

Consolidates three tightly coupled tools into a single plugin:
- **skillsmith** — skill quality evaluation and improvement
- **marketplace-manager** — distribution, versioning, and marketplace.json maintenance
- **agentsmith** — agent quality evaluation and improvement

## Components

### Skills (3)

| Skill | Purpose |
|-------|---------|
| `skillsmith` | Skill evaluation with 5 scored dimensions, improvement loop, and marketplace sync |
| `marketplace-manager` | Self-sufficient marketplace repo model with two-tier script architecture |
| `agentsmith` | Agent evaluation with 3 quality dimensions (Trigger Effectiveness, System Prompt Quality, Coherence) |

### Agent: skill-observer
Analyzes saved Claude Code session transcripts to identify where a skill failed to guide Claude effectively. Returns ranked structural gaps with installed→source path mapping.

### Commands (14)

| Prefix | Commands | Scope |
|--------|----------|-------|
| `ss-*` | `/ss-evaluate`, `/ss-improve`, `/ss-init`, `/ss-observe`, `/ss-package`, `/ss-research`, `/ss-validate` | Skill quality |
| `mp-*` | `/mp-sync`, `/mp-validate`, `/mp-add`, `/mp-list`, `/mp-status` | Marketplace ops |
| `as-*` | `/as-evaluate`, `/as-improve` | Agent quality |

### Hooks

| Hook | Trigger | Purpose |
|------|---------|---------|
| `on-skill-edit.sh` | PostToolUse Write\|Edit on `SKILL.md` | Quick skill quality evaluation; score fed back to Claude |
| `on-script-edit.sh` | PostToolUse Write\|Edit on `scripts/*.py` | Enforces PEP 723 header and bans `click`/`typer` (argparse standard) |
| `on-agent-edit.sh` | PostToolUse Write\|Edit on agent `.md` | Quick agent quality evaluation; score fed back to Claude |

## Changelog

| Version | Changes |
|---------|---------|
| 1.0.0 | Initial release — consolidates skillsmith v6.9.0, marketplace-manager v4.0.0, and new agentsmith v1.0.0 |

## Skill: skillsmith

### Current Metrics

**Score: 100/100** (Excellent) — 2026-04-28

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 100 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 6.9.0 | 2026-04-28 | [#165](https://github.com/totallyGreg/claude-mp/issues/165) | Reference provenance tracking: provenance spec in agentskills_specification.md, check_freshness.py generic script, Reference Currency 6th evaluation dimension, /ss-refresh command, ss-improve/ss-research freshness integration, init_skill.py templates | 100 | 100 | 100 | 100 | 100 | 100 |
| 6.8.0 | 2026-03-25 | [#148](https://github.com/totallyGreg/claude-mp/issues/148) | Migrate skill README to plugin level: plugin-root discovery, scoped section replacement, auto-migration, compact metrics display, clearer column headers, validate_skill_name(), rename readme_template | 100 | 100 | 100 | 100 | 100 | 100 |
| 6.7.0 | 2026-03-25 | [#146](https://github.com/totallyGreg/claude-mp/issues/146) | Anthropic guide alignment: use-case definition template, description formula + bad examples, body structure template, 5 skill patterns reference, 3-area testing guide, negative trigger coaching, over/undertrigger --explain signals | 100 | 100 | 100 | 100 | 100 | 100 |
| 6.6.0 | 2026-03-22 | [#96](https://github.com/totallyGreg/claude-mp/issues/96), [#115](https://github.com/totallyGreg/claude-mp/issues/115), [#81](https://github.com/totallyGreg/claude-mp/issues/81), [#82](https://github.com/totallyGreg/claude-mp/issues/82), [#108](https://github.com/totallyGreg/claude-mp/issues/108), [#110](https://github.com/totallyGreg/claude-mp/issues/110) | Qualitative conciseness checks; context-aware ss-observe with --hint; orphan regex fix; IMPROVEMENT_PLAN.md migration; frontmatter auto-patch; commit-gate doc | 100 | 100 | 100 | 100 | 100 | 100 |
| 6.4.0 | 2026-03-19 | [#104](https://github.com/totallyGreg/claude-mp/issues/104) | Phase 6: self-application — all metrics 100/100; closes v6 improvement arc | 100 | 100 | 100 | 100 | 100 | 100 |
| 6.0.0 | 2026-03-19 | - | **BREAKING**: Plugin migration, skill-observer agent, README replaces IMPROVEMENT_PLAN.md | 100 | 100 | 100 | 100 | 100 | 100 |
| 5.0.0 | 2026-02-05 | [#33](https://github.com/totallyGreg/claude-mp/issues/33) | Align with official plugin-dev patterns | 56 | 77 | 100 | 100 | - | 86 |
| 4.0.0 | 2026-02-03 | [#28](https://github.com/totallyGreg/claude-mp/issues/28) | Migrate to standalone plugin structure | 80 | 90 | 100 | 100 | - | 93 |
| 1.0.0 | - | - | Initial release | - | - | - | - | - | - |

## Skill: marketplace-manager

### Current Metrics

**Score: 100/100** (Excellent) — 2026-03-26

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 100 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 4.0.0 | 2026-03-26 | [#145](https://github.com/totallyGreg/claude-mp/issues/145) | Official schema alignment, self-sufficient repo model, 12 scripts replaced by 4, reverse scan + auto-fix | 100 | 100 | 100 | 100 | 100 | 100 |
| 3.1.0 | 2026-03-25 | - | Fix validator schema guidance, merge SKILL.md sections, add negative trigger clause | 100 | 100 | 100 | 100 | 100 | 100 |
| 2.9.0 | 2026-03-23 | [#139](https://github.com/totallyGreg/claude-mp/issues/139) | Multi-plugin structure detection, CI mode, advisory hook warning | 100 | 87 | 100 | 100 | 100 | 97 |
| 2.0.0 | 2026-02-03 | - | Standalone plugin migration | - | - | - | - | - | - |
| 1.0.0 | 2025-12-21 | - | Initial release | - | - | - | - | - | - |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)
