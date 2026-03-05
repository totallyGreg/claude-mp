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

## Version History

| Version | Changes |
|---------|---------|
| 4.0.0 | Added signals-monitoring skill: unified logging, signals/trap, file watching, notifications |
| 3.0.0 | Split monolithic skill into plugin with agent + two focused skills |
| 2.1.0 | Added zsh function patterns, completion guide, Plugin Standard references |
| 2.0.0 | Initial release with terminal diagnostics and zsh configuration |
