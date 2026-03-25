# signals-monitoring

This skill covers two closely paired terminal primitives: Unix process signals (sending, handling, and trapping them in shell scripts) and system monitoring (macOS unified logging, file watching, and process inspection). It solves the problem of scripts that leave temp files behind, apps that misbehave silently, and workflows that require manual attention — replacing them with graceful shutdown handlers, structured log queries, and automatic notifications. Use it when you need to instrument a script with `trap`, diagnose a crashing macOS app via `log stream`, set up automatic rebuild-on-save with `fswatch` or `entr`, or alert yourself when a long-running command finishes.

## Capabilities

- Query and stream macOS unified logs with predicate filtering (`log show`, `log stream`)
- Write structured log entries from shell scripts using `logger`
- Handle Unix signals in zsh scripts with `trap` for graceful shutdown and cleanup
- Send, reload, or force-kill processes using `kill`, `pkill`, and signal names
- Watch files for changes and trigger actions automatically (`fswatch`, `entr`)
- Send macOS notifications from the terminal (`osascript`, `terminal-notifier`, `notify_when_done` pattern)
- Open a real-time filtered log stream in a tmux split pane via the `logwatch` autoload function

## Current Metrics

**Score: 92/100** (Good) — 2026-03-22

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 90 | 80 | 100 | 100 |

## Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.0.0 | - | [#86](https://github.com/totallyGreg/claude-mp/issues/86) | Initial release: macOS logging, Unix signals, file watching, notifications, logwatch tmux function | - | - | - | - | - | 88 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

## Active Work

- None.

## Known Issues

- None.

## Archive

- Git history: `git log --grep="signals-monitoring"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:enhancement+is:closed

---

*Run `uv run scripts/evaluate_skill.py <path> --update-readme` to refresh metrics.*
