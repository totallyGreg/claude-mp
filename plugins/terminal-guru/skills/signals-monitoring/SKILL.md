---
name: signals-monitoring
description: This skill should be used when working with Unix process signals, shell trap handlers, macOS unified logging, file watching, process monitoring, and terminal notifications. Use when users ask to "check system logs", "debug my app", "fix script cleanup on Ctrl+C", "add signal handling to a script", "configure log streaming", "build a file watcher", "send a notification from the terminal", or "open a log stream in tmux".
metadata:
  version: "1.0.0"
---

# Signals & Monitoring

## Overview

Two closely paired terminal primitives: **signals** (sending and handling Unix process signals in shell scripts) and **monitoring** (observing system state via macOS unified logging, file watching, and process inspection). Completes the loop with **notifications** — alert yourself when something happens.

## When to Use This Skill

- Checking macOS system logs (`log show`, `log stream`)
- Diagnosing why an app is misbehaving or crashing
- Real-time log streaming in a tmux pane (`logwatch`)
- Writing structured log entries from shell scripts (`logger`)
- Handling Ctrl+C, SIGTERM, SIGHUP in zsh scripts with `trap`
- Graceful shutdown patterns for long-running shell functions
- Sending a signal to reload a process config (SIGHUP)
- Watching files for changes and triggering actions (`fswatch`, `entr`)
- Inspecting process resource usage or open file descriptors
- Sending macOS notifications from the terminal (`osascript`, `terminal-notifier`)
- Notifying yourself when a long command finishes

## Core Capabilities

### 1. macOS System Logging

Read, stream, and write to macOS's unified logging system. See `references/macos_logging_guide.md` for the full reference.

**Common operations:**

```bash
# Show logs from last hour, filtered to a subsystem
sudo log show --last 1h --predicate 'subsystem=="com.apple.sharing"'

# Real-time stream — errors from a process
sudo log stream --predicate 'process=="Safari" and type=error'

# Stream filtered by subsystem in shorthand
sudo log stream --predicate 's=com.apple.networking and type=error|fault'

# Write a log entry from a script
logger -t "my-script" -p user.info "task started"

# Find your entries later
log show --last 1h --predicate 'process=="logger" and eventMessage contains "my-script"'
```

**When to use**: Diagnosing macOS app or system behavior, instrumenting shell scripts, post-mortem investigation of crashes or unexpected behavior.

### 2. Unix Signals

Send, catch, and handle process signals in shell scripts. See `references/signals_guide.md` for the full reference.

**Common operations:**

```bash
# Graceful shutdown
kill -TERM <pid>

# Reload config (nginx, sshd, launchd services)
kill -HUP $(pgrep nginx)

# Force kill (uncatchable)
kill -9 <pid>
pkill -f "process name pattern"
```

**`trap` for script cleanup:**

```zsh
# Cleanup temp files on any exit
trap 'rm -f /tmp/my-lockfile' EXIT

# Graceful shutdown handler
trap 'echo "interrupted, cleaning up..."; cleanup_fn; exit 1' INT TERM

# Reload config on HUP
trap 'source ~/.zshrc' HUP
```

**When to use**: Scripts that create temp files, hold locks, or run background processes — always add an EXIT trap. Long-running functions that should handle Ctrl+C gracefully.

### 3. File Watching

Run commands automatically when files change. See `references/file_watching_guide.md` for the full reference.

```bash
# Run make when any source file changes (requires: brew install fswatch)
fswatch -o ./src | xargs -n1 -I{} make build

# Re-run tests on source changes (requires: brew install entr)
ls src/**/*.swift | entr -c swift test

# Watch and notify on change
fswatch ~/important-file | xargs -n1 -I{} terminal-notifier -message "File changed"
```

**When to use**: Development workflows where you want automatic rebuild/test on save, or monitoring a config file for changes.

### 4. Notifications

Send macOS notifications from the terminal. See `references/notifications_guide.md` for the full reference.

```bash
# Native — no dependencies
osascript -e 'display notification "Build done" with title "Terminal" sound name "Glass"'

# terminal-notifier — richer options (brew install terminal-notifier)
terminal-notifier -title "Deploy" -message "Production live" -sound default
```

**`notify_when_done` pattern** — wrap any command and alert on completion:

```zsh
notify_when_done() {
    "$@"
    local status=$?
    if (( status == 0 )); then
        osascript -e "display notification \"$*\" with title \"Done ✓\" sound name \"Glass\""
    else
        osascript -e "display notification \"$* (exit $status)\" with title \"Failed ✗\" sound name \"Basso\""
    fi
    return $status
}

# Usage: notify_when_done make build
# Usage: notify_when_done kubectl apply -f deployment.yaml
```

**When to use**: Long-running commands (builds, deploys, test suites) where you want to be alerted when done so you can context-switch away.

## `logwatch` — tmux Log Stream Pane

Open a tmux split pane with a filtered real-time log stream. Useful while developing: keep a log stream open alongside your editor or test runner.

```bash
# Install the autoload function
bash /path/to/zsh-dev/scripts/install_autoload.sh logwatch

# Usage after install:
logwatch com.apple.sharing              # stream by subsystem
logwatch "" "process==\"Safari\""       # stream by raw predicate
logwatch                                # stream all (unfiltered)
```

The script is at `scripts/logwatch`. When inside tmux, it opens a new split pane; otherwise streams in the current terminal.

## Diagnostic Workflow

| Symptom | Domain | Reference |
|---------|--------|-----------|
| App misbehaving, crash investigation | macOS Logging | `references/macos_logging_guide.md` |
| Script not handling Ctrl+C, leaving temp files | Signals / trap | `references/signals_guide.md` |
| Want to rebuild/test automatically on file save | File Watching | `references/file_watching_guide.md` |
| Alert when long command finishes | Notifications | `references/notifications_guide.md` |
| Need to kill or pause a process | Signals | `references/signals_guide.md` |

## Common Use Cases

### "Why is [app] doing this?"
1. Stream its logs: `sudo log stream --predicate 'process=="AppName"' --level debug`
2. Narrow with predicate: add `and type=error` to focus on errors
3. Check recent history: `sudo log show --last 30m --predicate 'process=="AppName"'`
4. Refer to `references/macos_logging_guide.md` for predicate syntax

### "My script leaves temp files when I Ctrl+C"
1. Add `trap 'rm -f "$tmpfile"' EXIT` at the top of your script
2. EXIT fires on Ctrl+C (SIGINT), SIGTERM, and normal exit
3. Refer to `references/signals_guide.md` for trap patterns

### "I want tests to run automatically when I save"
1. `brew install entr`
2. `ls src/**/*.swift | entr -c swift test`
3. Or with fswatch: `fswatch -o ./src | xargs -n1 -I{} make test`
4. Refer to `references/file_watching_guide.md`

### "Notify me when my deploy finishes"
1. Use `notify_when_done kubectl apply -f k8s/`
2. Or append: `make deploy && osascript -e 'display notification "Deploy done" with title "CI"'`
3. Refer to `references/notifications_guide.md`

## Resources

### scripts/
- **`logwatch`** — zsh autoload function: open tmux pane with filtered `log stream`

### references/
- **`macos_logging_guide.md`** — macOS unified log command, predicate filtering, writing logs from shell
- **`signals_guide.md`** — Unix signal table, kill/pkill, trap patterns for shell scripts
- **`file_watching_guide.md`** — fswatch, entr, process inspection (pgrep, lsof)
- **`notifications_guide.md`** — osascript notifications, terminal-notifier, notify_when_done pattern

## Advanced / Future Capabilities

The following tools exist for deep system tracing and are known to this skill, but **not yet covered in v1 guidance**. Ask about them and expect a pointer to documentation rather than step-by-step help:

- **`dtrace`** / **`dtruss`** — DTrace-based system call tracing (requires SIP disabled on modern macOS)
- **`instruments` CLI** — Apple's profiling and tracing tool (`xcrun xctrace`)
- **`ktrace`** / **`kdebug`** — kernel-level event tracing
