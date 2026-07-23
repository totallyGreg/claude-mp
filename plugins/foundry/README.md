# foundry

Plugin development lifecycle toolkit — evaluate, improve, and publish skills and agents.

Consolidates three tightly coupled tools into a single plugin:
- **skillsmith** — skill quality evaluation and improvement
- **marketplace-manager** — distribution, versioning, and marketplace.json maintenance
- **agentsmith** — agent quality evaluation and improvement

<!-- BEGIN AUTOGEN:overview (managed by skillsmith --update-components; edits overwritten) -->
## What's inside

Plugin development lifecycle toolkit — evaluate, improve, and publish skills and agents. Consolidates skillsmith (skill quality), marketplace-manager (distribution/versioning), and agentsmith (agent quality) into a single plugin.

**At a glance:** 4 skills · 1 agent · 16 commands · 4 hooks

## Install

```
/plugin marketplace add totallyGreg/claude-mp
/plugin install foundry@totally-tools
```
<!-- END AUTOGEN:overview -->

## Quickstart

```bash
# Improve a skill end-to-end (evaluate → fix → re-eval → README → sync)
/ss-improve plugins/<plugin>/skills/<skill>

# Improve an agent the same way
/as-improve plugins/<plugin>/agents/<agent>

# Refresh this README's What's-inside / Install / Components inventory
uv run plugins/foundry/skills/skillsmith/scripts/evaluate_skill.py <plugin-path> --update-components

# Publish/refresh marketplace metadata after a version bump
/mp-sync
```

File friction from anywhere with `/ss-wtf`; the improve loops read it back automatically.

<!-- BEGIN AUTOGEN:components (managed by skillsmith --update-components; edits overwritten) -->
## Components

### Skills (4)

| Skill | Description |
|-------|-------|
| `agentsmith` | Evaluate and improve agent quality with automated scoring across 3 dimensions. |
| `marketplace-manager` | Manages Claude Code plugin marketplace operations. |
| `skillsmith` | Forge effective skills with automated validation, metrics tracking, and improvement workflows. |
| `wtf` | File friction reports so the foundry's improve workflows can fix real pain. |

### Agents (1)

| Agent | Description |
|-------|-------|
| `skill-observer` | Use this agent to analyze a saved Claude Code session transcript and identify where a skill failed to guide Claude effectively. |

### Commands (16)

| Command | Description |
|-------|-------|
| `/as-evaluate` | Full evaluation of an agent with quality metrics. |
| `/as-improve` | Guided agent improvement loop — evaluate, explain, fix, re-evaluate, update README, sync |
| `/mp-add` | Scaffold a new plugin or migrate a legacy skill into plugin structure. |
| `/mp-list` | List all plugins in the marketplace. |
| `/mp-status` | Show version mismatches and validation summary for the marketplace. |
| `/mp-sync` | Sync plugin versions from plugin.json/SKILL.md to marketplace.json. |
| `/mp-validate` | Validate marketplace.json against the official Anthropic marketplace schema. |
| `/ss-evaluate` | Full evaluation of a skill with quality metrics. |
| `/ss-improve` | Guided skill improvement loop — evaluate, explain, fix, re-evaluate, update README, sync |
| `/ss-init` | Initialize a new skill from template. |
| `/ss-observe` | Analyze a Claude Code session transcript to identify skill gaps |
| `/ss-package` | Package a skill directory into a distributable skill.zip |
| `/ss-refresh` | Detect stale references and guide updates for any skill with provenance-tracked references |
| `/ss-research` | Research a skill to identify improvement opportunities |
| `/ss-validate` | Quick validation of a skill with optional strict mode. |
| `/ss-wtf` | File a friction report or list accumulated friction |

### Hooks (4)

| Hook | Trigger | Purpose |
|-------|-------|-------|
| `on-skill-edit.sh` | PostToolUse Write\|Edit | Fires a quick skill evaluation when a SKILL.md file is edited in the repo source (not installed marketplace copies). |
| `on-script-edit.sh` | PostToolUse Write\|Edit | Fires when a Python file inside a scripts/ directory is written or edited. |
| `on-agent-edit.sh` | PostToolUse Write\|Edit | Fires a quick agent evaluation when an agent .md file is edited in the repo source (not installed marketplace copies). |
| `on-component-edit.sh` | PostToolUse Write\|Edit | Warns (does not write) when a plugin component is added or changed so the plugin README's autogen Components inventory can be refreshed. |
<!-- END AUTOGEN:components -->
## Changelog

| Version | Changes |
|---------|---------|
| 1.5.0 | Human-useful, auto-maintained plugin READMEs (skillsmith 6.10.0): `--update-components` generates What's-inside/Install/Components inventory; MINOR-only Version History enforcement; `on-component-edit.sh` staleness hook ([#190](https://github.com/totallyGreg/claude-mp/issues/190)) |
| 1.3.0 | Add WTF (Work the Foundry) friction reporter skill, `/ss-wtf` command, friction query integration in `/ss-improve` and `/as-improve` |
| 1.0.0 | Initial release — consolidates skillsmith v6.9.0, marketplace-manager v4.0.0, and new agentsmith v1.0.0 |

## Skill: skillsmith

### Current Metrics

**Score: 100/100** (Excellent) — 2026-07-23

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 100 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 6.10.0 | 2026-07-23 | [#190](https://github.com/totallyGreg/claude-mp/issues/190) | Human-useful plugin READMEs: `--update-components` generates What's-inside/Install/Components inventory into autogen fences (hand-authored zones preserved); MINOR-only Version History enforcement (`--export-table-row` refuses/auto-folds PATCH, `--allow-patch` override, `--check-version-history` audit); `on-component-edit.sh` warn-only staleness hook | 100 | 100 | 100 | 100 | 100 | 100 |
| 6.9.0 | 2026-04-28 | [#165](https://github.com/totallyGreg/claude-mp/issues/165) | Reference provenance tracking: provenance spec in agentskills_specification.md, check_freshness.py generic script, Reference Currency 6th evaluation dimension, /ss-refresh command, ss-improve/ss-research freshness integration, init_skill.py templates. +v6.9.1 (2026-04-28): refresh agentskills_specification.md — allowed-tools example, compatibility examples, metadata key uniqueness guidance | 100 | 100 | 100 | 100 | 100 | 100 |
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

## Skill: agentsmith

### Current Metrics

**Score: 98/100** (Excellent) — 2026-04-28

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.1.0 | 2026-04-28 | - | Add code examples, agent-improvement-guide.md reference with delegation model and improvement patterns | 100 | 90 | 100 | 100 | 100 | 98 |
| 1.0.0 | 2026-04-28 | - | Initial release — agent evaluation with 3 quality dimensions | 100 | 80 | 100 | 85 | 100 | 93 |

## Skill: wtf

### Current Metrics

**Score: 100/100** (Excellent) — 2026-06-25

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 100 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.1.0 | 2026-06-25 | - | Global per-user report store (`~/.claude/agent-issues/reports/`) so friction filed from any repo is visible to improvement loops; default `--project` to `$(pwd)`; drop git-repo requirement. Pairs with foundry command arg-parsing fix. | 100 | 100 | 100 | 100 | 100 | 100 |
| 1.0.0 | 2026-05-08 | [#173](https://github.com/totallyGreg/claude-mp/issues/173) | Initial release — proactive friction reporter with submit script and improve integration | 100 | 100 | 100 | 100 | 100 | 100 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)
