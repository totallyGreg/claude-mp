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
- Ghostty: features under tmux, 1.4 upgrade checklist, libghostty landscape
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
- tmux 3.7/3.8: events, monitor hooks, OSC 133 command events, floating/modal panes, breaking changes (`references/tmux_3_8_features.md`)
- Alternative multiplexers: `herdr`, an AI-agent-focused tmux alternative (`references/herdr_alternative.md`)

### Skill: tui-experience (NEW in 5.5.0)
The "experience" layer — apps you live in, and recording what happens there:
- TUI app theming/keybindings/quirks: fzf, television (tv), gum, btop, lazygit, k9s, glow, charm/bubbletea
- fzf as the default picker, and fzf features by version with an update procedure (`references/fzf_features.md`)
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

**Score: 98/100** (Excellent) — 2026-08-06

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 2.7.0 | 2026-08-06 | - | **Compact-listing readability warning** for `description`. SKILL.md Authoring Conventions bullet now warns that long descriptions wrap/overlap in the compact `mise tasks` listing and shell completions — over-applying the density rule produced a real `cut -c1-94` workaround. New guidance: lead with a ≤72-char summary that stands alone in the compact listing; push arg-level detail to `#USAGE help=` and the task body; reserve full what/requires/produces/when for `mise tasks --extended`. `mise_task_patterns.md` description-property row updated to note the compact-listing constraint. | 100 | 90 | 100 | 100 | 100 | 98 |
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
| 5.21.0 | **tui-experience v1.1.0, environment-composition v2.3.0** ([#232](https://github.com/totallyGreg/claude-mp/issues/232)): recommend **fzf over television** for pickers. tv 0.15.9 (no release since 2026-06) can't cycle sources backwards or use the terminal's default colours, and one invalid theme override silently drops them all; fzf did all the tv picker did plus Shift-Tab and light/dark-following colours, ~140 vs ~210 ms to first entry. New `references/fzf_features.md`: features by version through fzf 0.74.5 (transform, events, `--popup` floating panes, `--color=16`), the verified Tab/Shift-Tab multi-source picker, breaking changes, and how to keep it current from upstream `CHANGELOG.md`. `tui_tools.md` corrects the tv repo, default keys and decision table; agent routes picker requests to tui-experience. Scores unchanged: tui-experience 92, environment-composition 90. |
| 5.20.0 | **environment-composition v2.2.0**: `finder_surface.sh droplet` now embeds the script (re-run to update; `--link` to reference it instead, `--self-reporting` for scripts that show their own results), shows a progress window with Stop, and reports by exit status (0 done, 3 already reported, other = failure dialog). Double-clicking the droplet opens a settings window that toggles a Finder right-click Quick Action. Scripts drive a real progress bar via `$DROPLET_PROGRESS_FILE`. `macos_finder_surfaces.md` adds the exit contract, progress protocol, and hurdles from a real build (Finder's environment, bash 3.2 traps, GUI-free testing with a stub `osascript`, SSH over one connection). Score 90/100 (unchanged). |
| 5.19.0 | **environment-composition v2.1.0** ([#210](https://github.com/totallyGreg/claude-mp/issues/210)): wrap any script in a Finder **droplet** or **Folder Action** — `scripts/finder_surface.sh` generates both and detaches them, and `references/macos_finder_surfaces.md` gives the core-script contract (absolute paths for `do shell script`'s minimal PATH, no TTY, skip own output) and gotchas. Worked example: receipt image → JSON with Apple's on-device `fm`, verified through both surfaces. **signals-monitoring v1.0.1**: file-watching guide points to Folder Actions. Agent routes droplet/Folder Action requests (100/100, unchanged). Scores unchanged: environment-composition 90, signals-monitoring 92. |
| 5.18.0 | **tmux-dev v1.1.0**: tmux 3.7/3.8 awareness — events, monitor hooks, `wait-for -E`, OSC 133 command-finished events, floating/modal panes, new formats/hooks, themes, and breaking changes (new `references/tmux_3_8_features.md`; tested on tmux 3.8). `tmux_plugins.md` now covers the native option-change trigger. Score 91/100 (unchanged). |
| 5.17.1 | **zsh-dev v3.2.1**: `keychainctl` rewritten in zsh with only macOS built-ins (`security` + `plutil`; `jq` no longer needed). One `get`/`set`/`rm` command set replaces the separate `pair` namespace (kept as a compatibility alias); `-f FIELD` edits one field of a bundle; `-k` selects the keychain. New `import` stores a JSON bundle from a file, stdin, or a hidden paste (nothing in shell history). Items are tagged Kind `secret` or `json`. Guards: refuse to drop a bundle's fields, or store values that look like paste mistakes (whitespace, `$(`, backtick) unless `--force`. Labels kept across writes; `ls` lists item names, not labels. Brings the long-diverged `~/bin` copy (pair support) back into source. **mise-tooling v2.7.2**: keychain examples updated to the new commands. |
| 5.17.0 | **mise-tooling v2.7.1**: documented the `#USAGE`/`#MISE` KDL-escape gotcha — mise parses these as KDL (only its built-in escapes are valid); a stray `\$` fails parsing and silently breaks `mise tasks` + tab-completion. Nuance: the error surfaces only when a task's usage spec is loaded (`mise tasks info <name>`/completion), not a plain `mise tasks`. Added to SKILL.md Authoring Conventions + `mise_task_patterns.md`. |
| 5.16.0 | **terminal-emulation v4.1.1**: corrected `terminal_recording.md` to mirror the canonical `record.sh` pattern — single-script self-replay trick (`--play` mode keeps pacing helpers in scope without a separate lib file), `end()` helper, prereq guards that "fail with the fix", safety gate strips bare UUIDs (legitimate task output). **mise-tooling v2.7.0**: compact-listing readability warning added — long descriptions wrap/overlap in `mise tasks` and completions; lead with ≤72-char summary; guidance updated in SKILL.md and `mise_task_patterns.md`. |
| 5.15.0 | **terminal-emulation v4.1.0**: new recording capability — asciinema→GIF pipeline for GitHub/GitLab READMEs (JS player blocked). Added `references/terminal_recording.md`: single-script self-replay pattern, `say`/`run`/`end` helpers, prereq guards, tuned `agg` defaults, credential safety gate, `record.sh` scaffolder (target stays plugin-free). Spec compliance fixed: `license`+`compatibility` frontmatter. Skill score: 92→98/100. |
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

**Score: 90/100** (Good) — 2026-10-21

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 80 | 80 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 2.3.0 | 2026-10-21 | [#232](https://github.com/totallyGreg/claude-mp/issues/232) | fzf, not tv, for pickers; points to `tui-experience/references/fzf_features.md` for new fzf actions; multi-source picker pattern in `fzf_composition.md`. | 100 | 80 | 80 | 100 | 100 | 90 |
| 2.2.0 | 2026-10-20 | - | Droplets embed the script and show a progress window with Stop; exit contract (0/3/other) and `$DROPLET_PROGRESS_FILE` progress protocol; double-click settings window toggles a right-click Quick Action; `--link` / `--self-reporting`; build hurdles in `macos_finder_surfaces.md`. | 100 | 80 | 80 | 100 | 100 | 90 |
| 2.1.0 | 2026-10-13 | [#210](https://github.com/totallyGreg/claude-mp/issues/210) | macOS Finder surfaces: new `references/macos_finder_surfaces.md` (core-script contract, droplet, Folder Action, Quick Action, launchd) and `scripts/finder_surface.sh` (droplet / folder-action / detach); Script → Finder Surface graduation step; `fm` receipt → JSON worked example. | 100 | 80 | 80 | 100 | 100 | 90 |
| 2.0.0 | 2026-05-03 | - | Evolved into composition engine: composition philosophy, fzf patterns, workflow discovery script, tool landscape analysis. Expanded from sesh-specific to general tool composition. | 100 | 80 | 80 | 100 | 100 | 90 |
| 1.0.0 | 2026-04-01 | - | Initial release: sesh.toml config, claude CLI composition, direnv integration, workflow patterns (setup/worktree/teardown/decay), Lens framework | 100 | 80 | 80 | 100 | 100 | 90 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

## Skill: signals-monitoring

### Current Metrics

**Score: 92/100** (Good) — 2026-10-13

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

## Skill: terminal-emulation

### Current Metrics

**Score: 98/100** (Excellent) — 2026-10-27

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 4.2.0 | 2026-10-27 | - | New `references/ghostty.md` (provenance-tracked, Ghostty 1.4.0): matrix of Ghostty features that reach through tmux vs. ones tmux hides (`-CC` not wired to GUI, OSC 5522/2033 not forwarded, `GHOSTTY_SURFACE_ID` stale in panes); 1.4 upgrade checklist (control-mode crash GHSAs, `copy-on-select` macOS default `none`, `cmd+arrow` → `jump_to_prompt`, `scrollback-limit-bytes`, `+ssh`); libghostty/multiplexer landscape + decision framing. SKILL.md: Ghostty capability + triggers, fixed duplicate §4 numbering, tmux snippet `Tc` → `terminal-features`, removed shell-side `TERM` override anti-pattern. | 100 | 90 | 100 | 100 | 100 | 98 |
| 4.1.0 | 2026-08-06 | - | New capability: **terminal recording (asciinema → GIF)**. Added `references/terminal_recording.md`: headless recording with the **single-script self-replay trick** (`record.sh --play <name>` so pacing helpers are in scope without a separate lib file), `say`/`run`/`end` helpers, prereq guards that "fail with the fix", credential safety gate (Bearer/JWT only — bare UUIDs not flagged), tuned `agg` defaults, and `record.sh` scaffolder (target stays plugin-free). Canonical reference implementation: `examples/casts/record.sh` in airs-tasks. Added `license` + `compatibility` frontmatter (spec compliance 80→100). +v4.1.1 (corrected safety gate — removed UUID pattern; aligned with canonical). | 100 | 90 | 100 | 100 | 100 | 98 |
**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

## Skill: tui-experience

### Current Metrics

**Score: 92/100** (Excellent) — 2026-10-21

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 90 | 80 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.1.0 | 2026-10-21 | [#232](https://github.com/totallyGreg/claude-mp/issues/232) | **fzf as the default picker.** New `references/fzf_features.md` (features by version through 0.74.5, verified Tab/Shift-Tab multi-source picker, terminal-following colours, `--popup` floating panes, breaking changes, update procedure). `tui_tools.md`: tv limits at 0.15.9, corrected repo, default keys and decision table. | 100 | 90 | 80 | 100 | 100 | 92 |
| 1.0.0 | — | — | Initial release (plugin 5.5.0). | - | - | - | - | - | 92 |

## Skill: tmux-dev

### Current Metrics

**Score: 91/100** (Excellent) — 2026-10-09

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 98 | 90 | 80 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.1.0 | 2026-10-09 | - | **tmux 3.7/3.8 awareness.** New `references/tmux_3_8_features.md`, built from upstream `CHANGES` (tag 3.8) and the 3.8 man page: events + `wait-for -E`, monitor hooks (`set-hook -B`), OSC 133 `pane-command-finished` (wait for a command's exit status instead of polling), floating/modal panes (`new-pane`), new formats/hooks, themes, and a table of breaking changes (mouse on by default, theme-driven colours, `display-panes -b` and `refresh-from-pane` removed). Core recipes tested on an isolated tmux 3.8 server; found two gotchas (a monitor misses changes in its first ~1 s; `wait-for -v` prints payloads of events that `-F` rejects). `tmux_plugins.md` corrected: 3.8 has a native option-change trigger (monitor hooks). SKILL.md gets short *(3.8+)* pointers only (no conciseness regression). | 98 | 90 | 80 | 100 | 100 | 91 |
| 1.0.0 | — | — | Initial release (plugin 5.5.0). | - | - | - | - | - | 91 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)
