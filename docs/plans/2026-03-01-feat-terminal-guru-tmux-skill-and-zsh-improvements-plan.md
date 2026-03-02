---
title: "terminal-guru: Add tmux-dev skill and improve zsh-dev clarity"
type: feat
status: active
date: 2026-03-01
supersedes: "#41"
---

# terminal-guru: Add tmux-dev skill and improve zsh-dev clarity

## Overview

Issue #41 identified systematic failures when the zsh-dev skill was used for tmux plugin testing — a domain it was never designed for. Rather than bolting tmux knowledge onto zsh-dev, this plan creates a **new `tmux-dev` skill** in the terminal-guru plugin and sharpens the zsh-dev skill's scope boundaries.

## Problem Statement

1. **Tmux is a separate domain from Zsh.** Tmux has its own option system, format strings, plugin architecture (TPM), hooks, and testing patterns. Forcing this into zsh-dev creates confusion about what the skill covers.

2. **zsh-dev scope is unclear.** The skill description lacks trigger phrases (scored 60/100 on description quality). When users ask about tmux plugins, the agent routes to zsh-dev because there's nowhere else to go, leading to the failures documented in #41.

3. **No hypothesis-driven testing guidance.** Both skills would benefit from structured verification patterns, but this is especially critical for tmux where option-watching and format-string evaluation require precise debugging steps.

## Proposed Solution

### Part 1: New `tmux-dev` skill

Create `plugins/terminal-guru/skills/tmux-dev/` with:

**SKILL.md** covering:
- Tmux option system (server/session/window/pane options, user options `@var`)
- Format string syntax and evaluation (`#{?condition,true,false}`, `#{@user_option}`)
- Plugin architecture (TPM, option watching, hooks)
- Testing patterns: verification vs configuration vs debugging
- Hypothesis-driven testing template for tmux
- Common debugging commands (`show-options`, `display-message -p`, `list-keys`)

**References:**
- `references/tmux_options.md` — option hierarchy, reading/writing, format strings
- `references/tmux_plugin_patterns.md` — TPM structure, option watching, dynamic variables

**Key design principle:** This skill handles tmux-specific automation and plugin development. It does NOT cover terminal display issues inside tmux (that's terminal-emulation's job with TERM=tmux-256color).

### Part 2: Improve zsh-dev skill

1. **Add trigger phrases** to description (fix the 60/100 score):
   - "create zsh function", "zsh startup slow", "fpath issues", "autoload function", "test zsh config", "zsh completions"

2. **Add explicit scope boundaries** — what zsh-dev does NOT cover:
   - Tmux configuration/plugins → use tmux-dev
   - Terminal display issues → use terminal-emulation

3. **Add tool preference reminder** at top of skill (addresses #41's CLAUDE.md violations)

### Part 3: Update terminal-guru agent routing

Add tmux-dev to the agent's routing table:

| Symptom | Domain |
|---------|--------|
| Tmux plugin testing/development | tmux-dev |
| Tmux option watching, format strings | tmux-dev |
| Tmux key bindings, hooks | tmux-dev |
| Display issues inside tmux | terminal-emulation |

## Acceptance Criteria

### tmux-dev skill

- [ ] SKILL.md created with proper frontmatter (name, description with trigger phrases, version 1.0.0)
- [ ] Description includes trigger phrases: "tmux plugin", "tmux options", "tmux format string", "tmux hooks", "test tmux plugin"
- [ ] Covers: option system, format strings, plugin architecture, testing patterns
- [ ] Includes hypothesis-driven testing template with HYPOTHESIS/ACTION/EXPECTED/RESULT structure
- [ ] Includes task type determination: verify vs configure vs debug (with guidance on when NOT to modify config)
- [ ] `references/tmux_options.md` — option hierarchy, format string syntax, common commands
- [ ] `references/tmux_plugin_patterns.md` — TPM structure, option watching, dynamic variables
- [ ] Skillsmith evaluation passes `--quick --strict`
- [ ] Skillsmith overall score >= 75

### zsh-dev improvements

- [ ] Description updated with trigger phrases (target: description score >= 80)
- [ ] Scope boundaries documented ("NOT for tmux, terminal display")
- [ ] Skillsmith evaluation passes `--quick --strict`

### Agent routing

- [ ] terminal-guru agent routing table includes tmux-dev skill
- [ ] Agent description updated to mention three skills
- [ ] Agent examples include tmux-dev routing scenario

### Plugin manifest

- [ ] `plugin.json` version bumped (3.0.0 → 3.1.0)
- [ ] `plugin.json` keywords include "tmux"
- [ ] Marketplace sync run

### Verification

- [ ] The `zac toggle` verification scenario from #41 can be correctly handled by the new tmux-dev skill (manual walkthrough of the skill's guidance, not live OmniFocus-style testing)

## Design Constraints

- Follow existing terminal-guru plugin patterns (skill structure, reference organization)
- tmux-dev SKILL.md should be concise — tmux has extensive docs elsewhere, focus on patterns and testing
- Do not duplicate terminal-emulation content (TERM inside tmux stays in terminal-emulation)
- Follow skillsmith guidance: trigger phrases in description, progressive disclosure, references for depth

## Files to Create

- `plugins/terminal-guru/skills/tmux-dev/SKILL.md`
- `plugins/terminal-guru/skills/tmux-dev/references/tmux_options.md`
- `plugins/terminal-guru/skills/tmux-dev/references/tmux_plugin_patterns.md`

## Files to Modify

- `plugins/terminal-guru/skills/zsh-dev/SKILL.md` (description, scope boundaries)
- `plugins/terminal-guru/agents/terminal-guru.md` (routing table, examples)
- `plugins/terminal-guru/.claude-plugin/plugin.json` (version, keywords)

## Sources

- Supersedes: [#41](https://github.com/totallyGreg/claude-mp/issues/41) — original issue documenting zsh-dev failures for tmux tasks
- Existing plugin: `plugins/terminal-guru/` (v3.0.0, 2 skills + 1 agent)
- Skillsmith eval baseline: zsh-dev 81/100, description 60/100
