---
title: "feat: terminal-guru 5.5.0 alignment with stated user priorities"
type: feat
status: active
date: 2026-06-05
issue: "#70"
---

# feat: terminal-guru 5.5.0 alignment with stated user priorities

## Overview

terminal-guru is well-built (agent 96/100, skills 90-98/100) but the current coverage map doesn't match the user's stated priorities. The user named six high-priority terminal concerns — `zsh`, `tmux`, `TUI tools`, `signals`, `ASCII/color configurations`, and `asciinema` — and asked the plugin to surface command combinations to achieve a stated goal. Three of those six (tmux, TUI, asciinema) are under-served or absent; ASCII/color is sprinkled across two unrelated references.

This plan corrects the underlying stack model — terminal-emulation is the low-level Unix substrate (`$TERM`, terminfo, ANSI, Unicode), tmux is a multiplexer **on top of** that substrate — and reorganizes content along those lines. It promotes tmux to its own first-class skill (closing open issue #70), strengthens terminal-emulation with a focused ANSI colors reference, adds a new `tui-experience` skill for in-pane apps + recording, and adds a Unix composition primer so the agent can answer "how do I combine X and Y" with explicit tool preferences.

## Stack Model (corrected)

The current agent's stack model puts tmux inside terminal-emulation, which conflates two different layers. The corrected model:

1. **terminal-emulation** — the substrate the emulator implements: `$TERM`, terminfo, ANSI escape codes, color tiers (16/256/truecolor), `$COLORTERM`, Unicode/UTF-8, locale
2. **zsh** — shell running inside the terminal
3. **tmux** — multiplexer on top of the shell (NEW first-class layer)
4. **sesh** — session orchestration on top of tmux
5. **TUI apps** — fzf, lazygit, k9s, btop, etc., launched inside panes
6. **git / command capture / mise** — unchanged

terminal-emulation owns *display protocol* concerns even when tmux is involved (font glyphs failing, ANSI parsing broken, TERM=tmux-256color not set). tmux-dev owns *automation and structure* concerns (addressing, options, plugins, send-keys, hooks).

## Problem Frame

| User priority         | Current coverage                                                  | Gap                                                                |
| --------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------ |
| zsh                   | `zsh-dev` (98/100, 4 refs)                                        | None                                                               |
| Signals send/receive  | `signals-monitoring` (92/100, 4 refs)                             | None                                                               |
| Command composition   | `environment-composition` (90/100, composition + fzf + discovery) | Tool-preference matrix missing (when to use `rg` vs `grep`, etc.)  |
| **tmux**              | Misfiled inside `terminal-emulation` (2 refs)                     | No options/format strings/plugins/hooks/addressing; wrong layer    |
| **TUI tools**         | Mentioned in diagnostic script only                               | No theming/keybinding/debugging guidance for fzf, gum, btop, etc.  |
| **ANSI/colors**       | Sprinkled in `terminfo_guide.md` + `unicode_troubleshooting.md`   | No dedicated ANSI/256/truecolor/`$COLORTERM`/base16 reference      |
| **asciinema**         | Not mentioned                                                     | No recording/conversion/sharing reference                          |

**Layering correction:** `tmux_mouse_bindings.md` and `tmux_session_management.md` are tmux *automation* topics that got misfiled into terminal-emulation because there was no tmux skill. ANSI colors got scattered because there's no dedicated color reference. Both gaps disappear once the stack is reorganized.

User-stated tmux requirement, verbatim: *"i should have clear examples of how i can find, label, select, send and receive information between tmux sessions, windows and panes. Ideally there is a unique way to address every pane and thus it can always be referenced whenever it is moved between windows or sessions."*

**Verified fact for the skill content:** tmux assigns permanent IDs (`$N` session, `@N` window, `%N` pane) at creation. They survive renames and moves until `tmux kill-server`. The user's "ideal" is true and should be the centerpiece of `tmux-dev`.

## Requirements Trace

- R1. Open issue #70 (tmux-dev skill) is satisfied
- R2. tmux-dev skill centers pane/window/session unique-ID addressing (`$/@/%`)
- R3. tmux-dev covers send/receive (`send-keys`, `capture-pane`, `pipe-pane`, `wait-for`)
- R4. tmux-dev covers find/label/select (`rename-*`, `choose-tree`, `find-window`, `display-panes`)
- R5. tmux-dev covers options system + format strings + plugins + hooks
- R6. tmux-dev includes testing patterns (verify vs configure vs debug — addresses #41 failure mode)
- R7. New `terminal-emulation/references/ansi_colors.md` covers ANSI escape codes, 16/256/truecolor, `$COLORTERM`, base16, color-test tools (lives at the substrate layer)
- R8. Existing `tmux_mouse_bindings.md` and `tmux_session_management.md` move from `terminal-emulation/references/` → `tmux-dev/references/`
- R9. terminal-emulation description trimmed: no more tmux automation language; focused on substrate (TERM, terminfo, ANSI, Unicode, locale)
- R10. New `tui-experience` skill covers in-pane apps + recording (no longer holds ANSI colors)
- R11. `tui-experience/references/tui_tools.md` covers fzf, gum, btop, lazygit, k9s, glow (theming, keybindings, debugging)
- R12. `tui-experience/references/asciinema.md` covers `asciinema rec/play/upload`, `agg`/`vhs`/`svg-term-cli` conversion, `.cast` editing
- R13. `environment-composition/references/unix_composition_primer.md` covers piping/filtering/transforming with explicit tool preference matrix
- R14. Agent's terminal stack model corrected: terminal-emulation = foundation, tmux = its own layer above zsh
- R15. Agent routing table includes tmux-dev and tui-experience; tmux automation routes to tmux-dev; tmux display issues (TERM, ANSI inside tmux) route to terminal-emulation
- R16. plugin.json bumped 5.4.0 → 5.5.0; keywords += `tmux, tui, asciinema, ansi-color`
- R17. README version history updated with new agent + skill scores
- R18. marketplace.json synced
- R19. All skills pass skillsmith eval ≥ 90/100; agent re-eval ≥ 96/100 (no regression); terminal-emulation should *improve* from 90 (ansi_colors reference + tightened description should lift Description sub-score)

## Scope Boundaries

- Does NOT rebalance the agent's example blocks — deferred until new skills exist so examples reflect real routing
- Does NOT add a recording skill separate from tui-experience — asciinema fits the "terminal experience" theme
- Does NOT extend signals-monitoring (already strong); cross-link from tui-experience if needed
- Does NOT touch mise-tooling or zsh-dev content (both 98/100 and out of scope for this alignment work)
- Does NOT rewrite `tmux_mouse_bindings.md` or `tmux_session_management.md` — they move *as-is* from terminal-emulation/references/ → tmux-dev/references/ with a `git mv` (preserving history); content edits limited to fixing any inbound cross-links

## Context & Research

### Relevant Existing Files

- `plugins/terminal-guru/agents/terminal-guru.md` — agent definition; will be rewired (stack + routing + skills list)
- `plugins/terminal-guru/skills/terminal-emulation/SKILL.md` — keeps display + tmux *interactive* refs; description trimmed to remove tmux automation overlap
- `plugins/terminal-guru/skills/environment-composition/SKILL.md` — gains unix_composition_primer.md reference
- `plugins/terminal-guru/.claude-plugin/plugin.json` — version + keywords
- `plugins/terminal-guru/README.md` — new skill entries + version history rows
- `.claude-plugin/marketplace.json` — synced via marketplace-manager

### Related Issues

- **#70 (open)** — tmux-dev skill design (this plan supersedes/expands)
- **#41 (closed)** — Original tmux-plugin testing failures; informed #70 and the testing-pattern section of tmux-dev

### Baseline Scores (pre-work)

| Component              | Overall | Notes                            |
| ---------------------- | ------- | -------------------------------- |
| terminal-guru agent    | 96      | Trigger 100, Prompt 90, Coh 100  |
| zsh-dev                | 98      |                                  |
| mise-tooling           | 98      |                                  |
| signals-monitoring     | 92      | Spec 80                          |
| terminal-emulation     | 90      | Spec 80, Description 80          |
| environment-composition| 90      | Complexity 80, Spec 80           |

## Implementation Phases

### Phase 1: tmux-dev skill (closes #70)

- Create `plugins/terminal-guru/skills/tmux-dev/SKILL.md`
  - Frontmatter with trigger phrases: "tmux pane id", "tmux send-keys", "tmux capture-pane", "tmux options", "tmux format string", "tmux plugin", "tmux hooks", "tmux session management"
  - Section: **Addressing** — unique IDs (`$N` session, `@N` window, `%N` pane), listing, targeting, persistence semantics
  - Section: **Send / receive** — send-keys, capture-pane, pipe-pane, wait-for, display-message
  - Section: **Find / label / select** — rename, choose-tree, find-window, display-panes
  - Section: **Options & format strings** — scopes, user vars, conditional formats
  - Section: **Plugins & hooks** — TPM layout, option-watching, hook events
  - Section: **Testing patterns** — verify vs configure vs debug (from #41 lessons)
- `git mv plugins/terminal-guru/skills/terminal-emulation/references/tmux_mouse_bindings.md plugins/terminal-guru/skills/tmux-dev/references/`
- `git mv plugins/terminal-guru/skills/terminal-emulation/references/tmux_session_management.md plugins/terminal-guru/skills/tmux-dev/references/`
- Create `references/tmux_addressing.md` — unique-ID deep dive, targeting recipes
- Create `references/tmux_options_and_formats.md` — options scopes, format-string syntax
- Create `references/tmux_plugins.md` — TPM, option-watching, hooks, testing template
- Fix any inbound cross-links to the moved files (grep for old paths)
- Run skillsmith eval; iterate until ≥ 90/100
- Commit

### Phase 2: Strengthen terminal-emulation

- Trim SKILL.md description: remove tmux automation language ("create a tmux session", "set up pane logging", "sesh", "session naming convention", "direnv"); keep substrate focus (TERM, terminfo, ANSI, Unicode, locale)
- Add trigger phrases for colors: "ansi color", "256 color", "truecolor", "$COLORTERM", "color test", "color palette"
- Add explicit scope boundary: "NOT for tmux automation (use tmux-dev), NOT for TUI app theming (use tui-experience)"
- Create `references/ansi_colors.md` — ANSI escape codes (`\e[3Xm`, `\e[38;5;Nm`, `\e[38;2;R;G;Bm`), 16/256/truecolor tiers, `$COLORTERM` detection, terminal palette setup, `tput setaf`, base16/pywal, color-test tools (`pastel`, `colortest`)
- Update SKILL.md Resources section to reference ansi_colors.md
- Run skillsmith eval; should improve from 90 → 92+ (Description sub-score lift)
- Commit

### Phase 3: tui-experience skill

- Create `plugins/terminal-guru/skills/tui-experience/SKILL.md`
  - Frontmatter trigger phrases: "fzf preview", "fzf composition", "asciinema record", "lazygit theme", "k9s skin", "gum prompt", "btop config", "terminal recording", "tui app debugging"
  - Section: **TUI tools** — survey, theming model, debugging quirks
  - Section: **Terminal recording** — asciinema workflow, rendering, sharing
  - Cross-link to terminal-emulation/ansi_colors.md for color-protocol questions (not duplicated)
- Create `references/tui_tools.md` — per-tool quirks: fzf, gum, btop, lazygit, k9s, glow, charm
- Create `references/asciinema.md` — record/play/upload; agg, vhs, svg-term-cli; .cast editing
- Run skillsmith eval; iterate until ≥ 90/100
- Commit

### Phase 4: Unix composition primer

- Create `plugins/terminal-guru/skills/environment-composition/references/unix_composition_primer.md`
  - Piping: stdin/stdout/stderr, `|`, `<`, `>`, `2>&1`, process substitution `<(...)`
  - Filtering: `rg` (preferred), `grep` (fallback), `fd` (preferred), `find` (POSIX fallback)
  - Transforming: `jq`, `sd` (preferred), `sed` (POSIX fallback), `awk` (text streams), `yq`, `xsv`/`csvkit`
  - Glue: `fzf`, `xargs -I{}`, `tee`, `pv`
  - Tool preference matrix table: situation → preferred tool → fallback → why
- Update environment-composition SKILL.md to load this reference when composition questions arise
- Run skillsmith eval (regression check)
- Commit

### Phase 5: Agent rewire

- Update `agents/terminal-guru.md`:
  - **Terminal Stack** section: corrected 6-layer model with terminal-emulation as foundation, tmux as its own layer above zsh
  - **Five Skills → Seven Skills**: add tmux-dev and tui-experience entries; update terminal-emulation summary to reflect substrate focus
  - **Symptom-to-Domain Routing**: add tmux automation/addressing/options rows (→ tmux-dev); add TUI/asciinema rows (→ tui-experience); color rows (→ terminal-emulation); update tmux display rows to clarify the boundary
  - **Routing guidance**: add tmux-dev vs terminal-emulation tie-break (automation vs display protocol)
  - Defer example rebalance to a future patch
- Run agentsmith eval; confirm ≥ 96/100
- Commit

### Phase 6: Manifest + README + marketplace

- Bump `.claude-plugin/plugin.json` version 5.4.0 → 5.5.0
- Add keywords: `tmux, tui, asciinema, ansi-color`
- Update README.md:
  - New skill sections for tmux-dev and tui-experience
  - Update terminal-emulation section to reflect substrate focus
  - Version history row for agent (5.4.0 → 5.5.0)
  - Changelog entry: "Correct stack model: promote tmux to first-class layer, recast terminal-emulation as Unix substrate. Add tmux-dev skill (closes #70), tui-experience skill, ANSI colors reference, Unix composition primer."
- Run `marketplace-manager/scripts/repo/sync.py .claude-plugin/marketplace.json`
- Commit
- Update issue #70 with implementation summary and close it

## Verification Plan

- All five existing skills re-evaluated; no regressions (≥ current scores); terminal-emulation expected to *improve* 90 → 92+
- Two new skills (tmux-dev, tui-experience) score ≥ 90/100 each on skillsmith
- Agent re-eval ≥ 96/100 (current baseline; expect 96-99)
- `python3 -c "import json; json.load(open('.claude-plugin/marketplace.json'))"` parses cleanly
- Manual smoke 1 — tmux addressing: "what's the pane ID of my current pane and how do I send `git status` to pane %3?" → routes to tmux-dev → `tmux display-message -p '#{pane_id}'` + `tmux send-keys -t %3 'git status' Enter`
- Manual smoke 2 — recording: "record a terminal session and convert to an SVG" → routes to tui-experience/asciinema.md
- Manual smoke 3 — color protocol: "my terminal supports truecolor but ANSI 256 codes look washed out" → routes to terminal-emulation/ansi_colors.md (NOT tui-experience)
- Manual smoke 4 — boundary: "tmux pane shows boxes as letters" → routes to terminal-emulation (Unicode/ACS issue, not tmux automation)
- Manual smoke 5 — composition: "how should I filter JSON and pipe to fzf?" → loads unix_composition_primer.md + fzf_composition.md

## Risks & Open Questions

- **Risk: scope creep on tmux-dev.** Mitigation: hold *new* reference count to 3 (`tmux_addressing.md`, `tmux_options_and_formats.md`, `tmux_plugins.md`); the 2 moved files (`tmux_mouse_bindings.md`, `tmux_session_management.md`) don't count. Defer power-user topics (popup menus, `command-prompt -p`, mouse format strings) to follow-up.
- **Risk: broken cross-links after moving tmux files.** Mitigation: `rg "tmux_mouse_bindings\|tmux_session_management" plugins/` before and after the move; fix any inbound references in agent + sibling skills
- **Risk: terminal-emulation description becomes ambiguous after the split.** Mitigation: trim tmux automation language; explicit "substrate only" boundary; add color trigger phrases to fill the description-quality gap
- **Risk: ANSI colors split between terminfo_guide.md and new ansi_colors.md.** Mitigation: terminfo_guide.md covers terminal-capability *queries* (`tput colors`, `infocmp`); ansi_colors.md covers ANSI *protocol* (escape sequences, palette tiers). Cross-link both ways.
- **Open: should asciinema get its own slash command (`/record`)?** Defer — see how often it's used first
- **Open: should the unix primer become a standalone skill instead of a reference?** Defer — start as a reference, promote if it grows beyond 10K
