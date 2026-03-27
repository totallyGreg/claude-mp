# terminal-guru

Terminal diagnostics, configuration, and zsh development expert for Unix systems.

## Components

### Agent: terminal-guru
Diagnostic triage and cross-domain routing. Classifies symptoms and routes to the appropriate skill. Handles ambiguous problems and issues spanning both terminal display and shell configuration.

### Skill: terminal-emulation
Terminal display diagnostics and configuration (~40% of content):
- Terminfo database management
- Unicode/UTF-8 troubleshooting
- Locale and encoding configuration
- SSH terminal setup
- Tmux/Screen configuration
- TUI application display

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

## Changelog

| Version | Changes |
|---------|---------|
| 4.0.0 | Added signals-monitoring skill: unified logging, signals/trap, file watching, notifications |
| 3.0.0 | Split monolithic skill into plugin with agent + two focused skills |
| 2.1.0 | Added zsh function patterns, completion guide, Plugin Standard references |
| 2.0.0 | Initial release with terminal diagnostics and zsh configuration |

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
