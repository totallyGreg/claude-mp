# terminal-guru

Terminal diagnostics, tool composition, workflow discovery, and environment expert for Unix systems.

## Components

### Agent: terminal-guru
Terminal and shell expert that diagnoses problems, composes tools into workflows, and discovers usage patterns. Routes to 7 skills across the terminal stack: terminal-emulation (substrate) → zsh → tmux → sesh → TUI apps → git → command capture → mise tasks.

**v5.14.0**: Fixed mute-teammate defect — agent now carries `SendMessage` in its `tools:` frontmatter so it can reply to the lead and other teammates when spawned as a persistent team member via `/team-spawn`. Previously, the agent could receive messages but had no tool to respond, behaving like a mute one-shot subagent despite advertising `/team-spawn` and `/team-list` commands.

| Version | Date | Trigger | Prompt | Coherence | Overall |
|---------|------|---------|--------|-----------|---------|
| 5.14.0 | 2026-08-06 | 100 | 100 | 100 | **100** |
| 5.12.0 | 2026-07-15 | 100 | 100 | 100 | **100** |
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
- Alternative multiplexers: `herdr`, an AI-agent-focused tmux alternative (`references/herdr_alternative.md`)

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

### Commands

- **`/team-spawn <subagent-type> <name> <prompt...>`** — Forcing-function for the persistent-teammate spawn pattern. Calls the `Agent` tool with all three required fields (`subagent_type`, `name`, `prompt`); the `name` field is what distinguishes a persistent, `SendMessage`-addressable teammate from an ephemeral one-shot subagent. Verifies the `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` prerequisite, validates the agent type, and surfaces the new teammate's pane ID and addressing pattern after spawn.
- **`/team-list`** — Lists active teammates in the current session's team by reading `~/.claude/teams/session-*/config.json`. Shows name, agent type, agent ID, and `%N` pane ID (split-pane mode). Includes addressing reminders for SendMessage and graceful shutdown.
- **`/workflow-discover`** — Scans command history, brew inventory, XDG configs, and git log to surface workflow patterns and graduation candidates (zsh function vs mise task vs fzf composition).

### Skill: mise-tooling
mise (jdx/mise) configuration, task automation, and environment management:
- Configuration hierarchy, profiles, lifecycle hooks, monorepo support
- Task system (inline, included files, file-based), DAG execution, task templates
- DRY patterns via shared shell functions and task inheritance
- Environment variables with exec() for dynamic secrets (keychainctl, vault)
- task_config.includes behavior and gotchas, cross-project sharing
- Tool version management, watch mode (runtime-native vs `mise watch`), CLI reference
- Use case patterns: milestone aggregation, confirmation, cleanup, CI/CD, release pipeline ordering, implicit tool dependencies, monorepo affected detection

## Skill: mise-tooling

### Current Metrics

**Score: 98/100** (Excellent) — 2026-07-23

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 2.6.0 | 2026-07-23 | - | Four additions from comparison with terrylica `cc-skills` mise-tasks skill (`terrylica/cc-skills`). To `mise_use_case_patterns.md`: **release pipeline ordering** (build-before-publish DAG discipline — "manual step after X" is not enforcement; hidden guard-task pattern for selective re-run), **implicit tool dependencies** (tools whose flags silently need helpers, e.g. `maturin --zig` → `cargo-zigbuild`; declare all in `[tools]`), **monorepo affected detection** (mise has no native affected detection — git-diff fallback task with its transitive-dependency limitation flagged, plus a graduate-to Pants/Bazel/Turborepo scale table). To `mise_config_guide.md` + SKILL.md §5: **prefer runtime-native watch** (`bun --watch`/`node --watch`/`uvicorn --reload`, 0 overhead) over `mise watch`/`watchexec`. New Authoring Convention: **rich task `description`s** for agent discoverability via `mise tasks ls`. Skillsmith receipt-verified 98/100 (`--verify` exit 0; score corrected from an earlier 97 after fixing the skillsmith frontmatter-inflation bug — see foundry). | 100 | 90 | 100 | 100 | 100 | 98 |
| 2.5.0 | 2026-07-03 | - | Full mise-release refresh (last_verified 2026-05-03 → 2026-07-03, 89 upstream commits reviewed via `/ss-refresh` full audit). Corrected two now-wrong claims: directory paths in `task_config.includes` DO now work for TOML files (PR #10219 — was documented as silently failing, verified against a live sandbox); fixed a broken config-guide source URL (`docs/configuration/` → `docs/configuration.md`). Added: includes ordering (last entry wins, applies uniformly to directory/toml/`git::` includes), `git::` remote task includes, `auto_env` platform environments, monorepo `--monorepo` install + tri-state lockfile union, shell-style `$VAR`/`${VAR:-default}` env expansion (default-on since mise 2026.7.0), `{ default = "..." }` env fallback shorthand, sops `.env.toml` support. New reference file `mise_bootstrap_system.md` covering the experimental declarative `mise bootstrap` machine-provisioning feature (packages/repos/dotfiles/macOS defaults/systemd/login shell) as new Capability #6 in SKILL.md. | 100 | 90 | 100 | 100 | 100 | 98 |
| 2.4.0 | 2026-07-03 | - | Added two homestack-2026-derived environment patterns to `mise_environment_management.md`: multi-cluster/multi-target overlay configs (base `.mise.toml` + per-target overrides, with the "define `CLUSTER_ENDPOINT` explicitly, don't compose it" gotcha since Tera doesn't guarantee same-file env-var evaluation order), and capturing runtime-discovered values (e.g. a LB IP) via `mise set -E <env>` since `export` in a task body doesn't survive to the next `mise run` invocation. Verified `mise set -E` behavior against a live mise 2026.7.0 install. SKILL.md's Environment Management pointer updated to mention both. | 100 | 90 | 100 | 100 | 100 | 98 |
| 2.3.0 | 2026-07-03 | - | Two real-migration gotchas from a homestack-2026 review: (1) Tera doesn't render file-based task scripts at all — `{{config_root}}`-sourced libs silently resolve to a nonexistent path once promoted from inline TOML, fixed with `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`; (2) unquoted heredocs used for shell-side variable interpolation aren't a "quote it and move on" fix — export vars first, read via the child language's env mechanism, then quote. Added `${#arr[@]}` Tera comment-opener collision (previously undocumented) alongside it in `mise_task_patterns.md`. Disambiguated SKILL.md's `{{config_root}}` guidance to inline `run` blocks only. | 100 | 90 | 100 | 100 | 100 | 98 |
| 2.2.1 | 2026-06-30 | - | Reframe script-extraction default: `scripts/` for plain-shell extractions, `.mise/tasks/` only when you want mise-native features (auto-discovery, `#USAGE`, `#MISE` directives, namespacing). Added `scripts/` vs `.mise/tasks/` comparison table to `mise_config_guide.md`. | 100 | 90 | 100 | 100 | 100 | 98 |
| 2.2.0 | 2026-06-30 | - | Authoring conventions: section order (`[settings]`→`[env]`→`[tools]`→`[tasks.*]`), lifecycle task ordering (setup→run→maintenance), ~5-line script-extraction threshold, editing discipline. Borrowed from engineers/mise-toml comparison. | 100 | 90 | 100 | 100 | 100 | 98 |
| 2.0.0 | 2026-05-03 | - | Enriched references: DAG model, task templates, file-based discovery, hooks, monorepo, watch, CLI reference, use case patterns. Freshness metadata on all references. | 100 | 80 | 80 | 100 | 100 | 91 |
| 1.0.0 | 2026-05-01 | - | Initial release: config hierarchy, task patterns, DRY, multi-tenant credentials, tool versioning | - | - | - | - | - | 90 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

## Changelog

| Version | Changes |
|---------|---------|
| 5.14.0 | **Fix: add `SendMessage` to agent tools list.** Agent advertises persistent-teammate commands (`/team-spawn`, `/team-list`) but was missing `SendMessage` in its `tools:` frontmatter — it could receive messages but could never reply. Adding `SendMessage` unblocks teammate-to-lead and teammate-to-teammate communication when terminal-guru is spawned as a persistent team member. Score: 100/100 (no regression). |
| 5.13.0 | **mise-tooling v2.6.0**: four additions from comparison with terrylica `cc-skills` mise-tasks skill. `mise_use_case_patterns.md` gained release pipeline ordering (build-before-publish DAG discipline + guard-task selective re-run), implicit tool dependencies (`maturin --zig` → `cargo-zigbuild`, etc.), and monorepo affected detection (mise has none natively — git-diff fallback with transitive-dep limitation flagged + graduate-to Pants/Bazel/Turborepo scale table). `mise_config_guide.md` + SKILL.md §5 now prefer runtime-native watch (`bun --watch`/`node --watch`/`uvicorn --reload`) over `mise watch`. New Authoring Convention: rich task `description`s for `mise tasks ls` agent discoverability. Skillsmith receipt-verified 98/100 (`--verify` exit 0). |
| 5.12.0 | **herdr awareness.** Agent: one `<example>` + a Terminal Stack parenthetical noting `herdr` as an alternative AI-agent-focused multiplexer to tmux (no procedural detail — routing awareness only, per user feedback that agent-level content should stay light). New tmux-dev reference `herdr_alternative.md`: config (`~/.config/herdr/config.toml`, `--default-config`, `config check` vs `reload-config`), theming (`ui.accent`, `theme.custom` tokens, light/dark sibling themes), an empirical probe-color diagnostic technique for undocumented tokens, and a confirmed sidebar-divider gap (no config workaround). No score regression: agent still 100/100, tmux-dev still 91/100. |
| 5.11.0 | **mise-tooling v2.5.0**: full mise release-notes refresh (89 upstream commits reviewed). Corrected two now-stale claims (`task_config.includes` directory-TOML behavior; broken config-guide URL). Added includes ordering/`git::` remote includes, `auto_env`, monorepo install/lockfile union, shell-style env expansion, sops `.env.toml`. New `mise_bootstrap_system.md` reference for the experimental declarative machine-bootstrap feature. |
| 5.10.0 | **mise-tooling v2.4.0**: added multi-cluster/multi-target overlay pattern and `mise set -E`-based bootstrap output capture to `mise_environment_management.md`, generalized from real homestack-2026 usage (per-target `CLUSTER_ENDPOINT`/`CLUSTER_NAME` conventions, gateway LB IP capture). |
| 5.9.0 | **mise-tooling v2.3.0**: documented two Tera gotchas surfaced during a real inline-task migration — file-based task scripts aren't Tera-rendered (breaks `{{config_root}}`-sourced libs silently), and unquoted heredocs used for shell-side interpolation can't be fixed by just quoting the delimiter. Also documented the previously-undocumented `${#arr[@]}` Tera comment-opener collision. |
| 5.8.1 | **Fix**: `/team-spawn` narrative now references `@alias` (not `@label`) to match the user's live tmux.conf convention — `@powerkit_pane_border_format` reads `@alias`, so setting `@label` left the pane border blank. Discovered by the archivist during the v5.8.0 PKM capture. |
| 5.8.0 | **New commands: `/team-spawn` + `/team-list`** for the persistent-teammate spawn pattern (Agent tool with `name` field + `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` prerequisite). Forcing function prevents the silent-degrade-to-one-shot failure mode. Broadens plugin description to include multi-Claude team orchestration. |
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
