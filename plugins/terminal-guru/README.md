# terminal-guru

Terminal diagnostics, tool composition, workflow discovery, and environment expert for Unix systems.

## Components

### Agent: terminal-guru
Terminal and shell expert that diagnoses problems, composes tools into workflows, and discovers usage patterns. Routes to 7 skills across the terminal stack: terminal-emulation (substrate) → zsh → tmux → sesh → TUI apps → git → command capture → mise tasks.

| Version | Date | Trigger | Prompt | Coherence | Overall |
|---------|------|---------|--------|-----------|---------|
| 5.7.0 | 2026-06-30 | 100 | 100 | 100 | **100** |
| 5.5.0 | 2026-06-05 | 100 | 90 | 100 | 96 |
| 5.3.0 | 2026-05-03 | 100 | 90 | 100 | 96 |
| 5.2.0 | 2026-05-03 | 100 | 90 | 80 | 90 |
| 5.1.0 | 2026-05-01 | 100 | 90 | 80 | 90 |

### Skill: terminal-emulation
The Unix terminal substrate (`$TERM`, terminfo, ANSI/256/truecolor, Unicode, locale):
- Terminfo database management
- ANSI escape codes, color tiers (16/256/truecolor), `$COLORTERM`, base16 palettes
- Unicode/UTF-8 troubleshooting
- Locale and encoding configuration
- SSH terminal setup
- TUI application display (substrate-level)

### Skill: tmux-dev (NEW in 5.5.0)
tmux as an automation and structural surface (no longer a sub-topic of terminal-emulation):
- Pane/window/session unique IDs (`$N` / `@N` / `%N`) — the centerpiece for stable addressing
- Send / receive between panes (`send-keys`, `capture-pane`, `pipe-pane`, `wait-for`)
- Find / label / select (`choose-tree`, `find-window`, `display-panes`)
- Options & format strings (scopes, user vars, conditionals)
- TPM plugins, hooks, option-watching patterns
- Plugin testing: verify-vs-configure-vs-debug discipline (from #41 retrospective)
- Mouse bindings, named status-bar ranges
- Programmatic session creation, sesh integration (tmux side)

### Skill: tui-experience (NEW in 5.5.0)
The "experience" layer — apps you live in, and recording what happens there:
- TUI app theming/keybindings/quirks: fzf, television (tv), gum, btop, lazygit, k9s, glow, charm/bubbletea
- Terminal recording: asciinema (rec/play/upload), `.cast` editing
- Conversion: agg → GIF, svg-term-cli → SVG, ffmpeg → MP4
- Scripted demos with charmbracelet `vhs` (`.tape` syntax, vhs-vs-asciinema decision)

### Skill: zsh-dev
Zsh shell development and testing (~55% of content):
- Autoload function creation and management
- fpath configuration
- Function generation from established patterns
- Completion system setup
- Isolated testing environments (ZDOTDIR)
- Performance profiling and optimization
- Plugin compatibility validation

### Skill: signals-monitoring
System observability and event-response:
- macOS unified logging (log show/stream/collect, predicate filtering)
- Writing structured log entries from shell scripts (logger, _log pattern)
- Unix process signals (kill, pkill, trap patterns)
- Graceful shutdown and cleanup handlers for zsh scripts
- File watching (fswatch, entr)
- Process inspection (pgrep, lsof, ps)
- macOS notifications (osascript, terminal-notifier)
- `logwatch` — tmux pane with filtered live log stream

### Skill: environment-composition
Tool composition engine and workflow discovery:
- Composition philosophy (Unix principles, Pattern Graduation Pipeline)
- fzf composition patterns (source | fzf --preview | action, recipes, alternatives)
- Workflow discovery (command history, brew inventory, XDG configs, zoxide, git log)
- sesh.toml configuration (sessions, wildcards, windows, startup commands)
- Claude CLI session management (--continue, --resume, --worktree)
- Environment lifecycle workflows (setup, teardown, decay detection)
- Lens framework (Selection, Arrangement, Purpose, Activation)

### Skill: mise-tooling
mise (jdx/mise) configuration, task automation, and environment management:
- Configuration hierarchy, profiles, lifecycle hooks, monorepo support
- Task system (inline, included files, file-based), DAG execution, task templates
- DRY patterns via shared shell functions and task inheritance
- Environment variables with exec() for dynamic secrets (keychainctl, vault)
- task_config.includes behavior and gotchas, cross-project sharing
- Tool version management, watch mode, CLI reference
- Use case patterns: milestone aggregation, confirmation, cleanup, CI/CD

## Skill: mise-tooling

### Current Metrics

**Score: 98/100** (Excellent) — 2026-06-30

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 2.2.1 | 2026-06-30 | - | Reframe script-extraction default: `scripts/` for plain-shell extractions, `.mise/tasks/` only when you want mise-native features (auto-discovery, `#USAGE`, `#MISE` directives, namespacing). Added `scripts/` vs `.mise/tasks/` comparison table to `mise_config_guide.md`. | 100 | 90 | 100 | 100 | 100 | 98 |
| 2.2.0 | 2026-06-30 | - | Authoring conventions: section order (`[settings]`→`[env]`→`[tools]`→`[tasks.*]`), lifecycle task ordering (setup→run→maintenance), ~5-line script-extraction threshold, editing discipline. Borrowed from engineers/mise-toml comparison. | 100 | 90 | 100 | 100 | 100 | 98 |
| 2.0.0 | 2026-05-03 | - | Enriched references: DAG model, task templates, file-based discovery, hooks, monorepo, watch, CLI reference, use case patterns. Freshness metadata on all references. | 100 | 80 | 80 | 100 | 100 | 91 |
| 1.0.0 | 2026-05-01 | - | Initial release: config hierarchy, task patterns, DRY, multi-tenant credentials, tool versioning | - | - | - | - | - | 90 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

## Changelog

| Version | Changes |
|---------|---------|
| 5.7.0 | **terminal-guru agent → 100/100** (was 96). System prompt prompt: Quality Standards rationale + IMPORTANT call-out, structured Output Format report template with fenced markdown, "Profile missing or unreadable" edge-case bullet with fallback/limitation language. All three dimensions now 100/100. |
| 5.6.1 | **mise-tooling v2.2.1**: reframe script-extraction default to plain `scripts/`; `.mise/tasks/` becomes the upgrade path for mise-native features only. Added `scripts/` vs `.mise/tasks/` comparison table to `mise_config_guide.md`. |
| 5.6.0 | **mise-tooling v2.2.0**: added "Authoring Conventions" section to SKILL.md and "Style & Layout" to `mise_config_guide.md` — section order, lifecycle task ordering, ~5-line script-extraction threshold, editing discipline. Borrowed from comparison with `engineers/mise-toml` skill on the AIRS marketplace. Skill score steady at 98/100, agent unchanged at 96/100. |
| 5.5.0 | **Stack model correction + 2 new skills.** Promoted terminal-emulation to first-class substrate layer (Unix substrate: $TERM, terminfo, ANSI/256/truecolor, $COLORTERM, Unicode); promoted tmux out of terminal-emulation into its own first-class skill (tmux-dev). New skills: **tmux-dev** (pane/window/session unique-ID addressing, send/receive, options, format strings, plugins, hooks, testing patterns — closes #70) and **tui-experience** (fzf/television/gum/btop/lazygit/k9s/glow theming + asciinema/agg/vhs recording). Added ansi_colors.md reference to terminal-emulation (90→92). Added unix_composition_primer.md to environment-composition (piping/filtering/transforming + tool preference matrix). Agent stack model expanded to 8 layers with explicit substrate-vs-multiplexer boundary; routing table adds ~20 rows; 5 new routing-guidance paragraphs. Five Skills → Seven Skills. Scores: agent 96, all skills ≥ 90 (zsh-dev 98, mise-tooling 98, tmux-dev 91, tui-experience 92, terminal-emulation 92, signals-monitoring 92, environment-composition 90). |
| 5.2.0 | Enriched mise-tooling (v2.0.0): DAG model, task templates, file-based discovery, hooks, monorepo, watch, CLI reference, use case patterns. Added zsh-vs-mise routing decision table. Reference freshness metadata (check_freshness.py compatible). Terminal stack profile for self-improvement. |
| 5.1.0 | Added mise-tooling skill: config, tasks, includes, DRY patterns, multi-tenant credentials. Agent updated with terminal stack model and quality standards. Replaced direnv with mise as primary env manager. |
| 5.0.0 | Added environment-composition skill: sesh.toml config, claude CLI integration, direnv, worktree workflows, Lens framework |
| 4.0.0 | Added signals-monitoring skill: unified logging, signals/trap, file watching, notifications |
| 3.0.0 | Split monolithic skill into plugin with agent + two focused skills |
| 2.1.0 | Added zsh function patterns, completion guide, Plugin Standard references |
| 2.0.0 | Initial release with terminal diagnostics and zsh configuration |

## Skill: environment-composition

### Current Metrics

**Score: 90/100** (Good) — 2026-05-03

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 80 | 80 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 2.0.0 | 2026-05-03 | - | Evolved into composition engine: composition philosophy, fzf patterns, workflow discovery script, tool landscape analysis. Expanded from sesh-specific to general tool composition. | 100 | 80 | 80 | 100 | 100 | 90 |
| 1.0.0 | 2026-04-01 | - | Initial release: sesh.toml config, claude CLI composition, direnv integration, workflow patterns (setup/worktree/teardown/decay), Lens framework | 100 | 80 | 80 | 100 | 100 | 90 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

## Skill: signals-monitoring

### Current Metrics

**Score: 92/100** (Good) — 2026-03-22

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 90 | 80 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.0.0 | - | [#86](https://github.com/totallyGreg/claude-mp/issues/86) | Initial release: macOS logging, Unix signals, file watching, notifications, logwatch tmux function | - | - | - | - | - | 88 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)


## Skill: zsh-dev

### Current Metrics

**Score: 98/100** (Excellent) — 2026-03-27

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 3.2.0 | 2026-03-27 | - | Add frontmatter, negative trigger, reduce inline content to references | 100 | 90 | 100 | 100 | 100 | 98 |
| 3.0.0 | 2026-02-09 | [#40](https://github.com/totallyGreg/claude-mp/issues/40) | Split from terminal-guru monolith into focused zsh-dev skill within plugin | 80 | 78 | 80 | 100 | - | 81 |
| 2.1.0 | 2026-02-08 | #12 | Add zsh function patterns, completion guide, and Plugin Standard references | 33 | 66 | 80 | 100 | - | 69 |
| 2.0.0 | 2025-11-20 | - | Initial release with terminal diagnostics and zsh configuration support | 20 | 66 | 80 | 100 | - | 66 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)
