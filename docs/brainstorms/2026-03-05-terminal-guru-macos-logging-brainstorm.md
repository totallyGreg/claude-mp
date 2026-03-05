---
title: Signals & Monitoring skill for terminal-guru
date: 2026-03-05
topic: signals-monitoring terminal-guru
status: brainstorm
---

# Signals & Monitoring Skill for terminal-guru

## What We're Building

A new 3rd skill in terminal-guru: **`signals-monitoring`** — covering two closely related terminal primitives:

1. **Signals** — Unix process signals, `trap` in shell scripts, signal handling in zsh functions, sending/catching signals
2. **Monitoring** — observing the system in real-time or historically: macOS unified logging, file watching, process status, and surfacing that information usefully (e.g., in a tmux pane)

The two sides are naturally paired: you monitor a system to detect events, and you use signals to respond to them. macOS logging (the original trigger for this work) is one component of the monitoring side.

## Skill Structure

```
plugins/terminal-guru/
  skills/
    terminal-emulation/    (display, terminfo, unicode)
    zsh-dev/               (autoload, fpath, functions, testing)
    signals-monitoring/    (NEW)
      SKILL.md
      references/
        macos_logging_guide.md
        signals_guide.md
        file_watching_guide.md
      scripts/             (optional: logwatch helper, diagnostic tools)
  agents/terminal-guru.md  (updated routing)
```

---

## Side 1: Signals

### Unix Process Signals

Core signals every terminal user encounters:

| Signal | Number | Default action | Common use |
|--------|--------|---------------|------------|
| SIGINT | 2 | Terminate | Ctrl+C |
| SIGTERM | 15 | Terminate | Graceful shutdown |
| SIGKILL | 9 | Terminate (uncatchable) | Force kill |
| SIGHUP | 1 | Terminate | Terminal closed; config reload |
| SIGSTOP | 19 | Stop (uncatchable) | Ctrl+Z |
| SIGCONT | 18 | Continue | Resume stopped process |
| SIGUSR1/2 | 30/31 | Terminate | App-defined custom signals |

**Sending signals:**
```bash
kill -TERM <pid>       # graceful shutdown
kill -HUP <pid>        # reload config (nginx, sshd, etc.)
kill -9 <pid>          # force kill
pkill -f "process name"
killall Safari
```

### `trap` in Shell Scripts

`trap` intercepts signals in zsh/bash scripts — critical for cleanup and graceful shutdown:

```zsh
# Cleanup on exit (runs on EXIT pseudo-signal)
trap 'rm -f /tmp/my-lockfile; echo "cleaned up"' EXIT

# Graceful shutdown on SIGTERM
trap 'echo "Shutting down..."; cleanup; exit 0' TERM INT

# Reload config on SIGHUP (daemon pattern)
trap 'source ~/.zshrc; echo "config reloaded"' HUP

# Ignore a signal
trap '' PIPE    # ignore SIGPIPE (broken pipe)

# Reset to default
trap - TERM
```

**Signal handling in zsh autoload functions:**
```zsh
# Pattern: long-running function with cleanup
my_watcher() {
    local tmpfile=$(mktemp)
    trap "rm -f '$tmpfile'; return 0" INT TERM EXIT

    while true; do
        # ... do work ...
        sleep 1
    done
}
```

### Signal-based Patterns

- **Daemon reload**: send SIGHUP to reload config without restart
- **Graceful shutdown**: SIGTERM → cleanup → exit (vs SIGKILL which skips cleanup)
- **Job control**: SIGSTOP/SIGCONT for pausing/resuming background jobs
- **Pipe handling**: SIGPIPE when writing to a closed pipe (common in shell pipelines)

---

## Side 2: Monitoring

### macOS Unified Logging (`log` command)

**Reading logs:**
```bash
# Historical: show logs from last hour
sudo log show --last 1h --predicate 'subsystem=="com.apple.sharing"'

# Real-time stream with predicate
sudo log stream --predicate 's=com.apple.networking and type=error'

# Collect archive for later analysis
sudo log collect --output ~/Desktop/system.logarchive --last 20m

# View archive
sudo log show --archive ~/Desktop/system.logarchive

# Stats: what processes are generating the most log volume?
log stats --last 1h --overview
```

**Enabling debug logs for a specific subsystem** (dev workflow):
```bash
sudo log config --mode "level:debug" --subsystem com.mycompany.myapp
# ... reproduce the issue ...
sudo log config --reset --subsystem com.mycompany.myapp
```

**Writing logs from shell** (`logger`):
```bash
logger -t "my-script" -p user.info "task started"
logger -t "my-script" -p user.error "something failed: $?"
logger -t "my-script" -s "also print to stderr"

# Find your messages later:
log show --last 1h --predicate 'process=="logger" and eventMessage contains "my-script"'
```

**From zsh functions — structured logging pattern:**
```zsh
# Consistent logger wrapper for scripts
_log() {
    local level="${1:-info}"; shift
    logger -t "${FUNCNAME[1]:-zsh}" -p "user.$level" "$*"
}

my_function() {
    _log info "starting with args: $*"
    # ... work ...
    _log debug "completed successfully"
}
```

**Predicate filtering:**
- `subsystem=="com.apple.sharing"` — by subsystem (os_log messages only)
- `category IN {"AirDrop", "Bonjour"}` — multiple categories
- `process=="Safari"` — by process name
- `type=error|fault` — by log level
- `eventMessage contains "timeout"` — by message content
- Shorthand: `s=com.apple.sharing and c:airdrop and type=error`

### File Watching

```bash
# fswatch: run command when files change
fswatch -o ~/project/src | xargs -n1 -I{} make build

# entr: re-run tests when source changes
ls src/**/*.swift | entr -c swift test

# Watch a specific file
fswatch ~/Library/Preferences/com.apple.dock.plist | xargs -n1 echo "Dock prefs changed:"
```

### Process Monitoring

```bash
# One-shot process snapshot
ps aux | grep <process>
pgrep -l Safari

# Resource usage
top -pid <pid>
activity_monitor_data() { top -l 1 -pid "$1" }

# File descriptors / open files
lsof -p <pid>
lsof -i :8080   # what's using port 8080?
```

---

## Cross-Cutting: tmux Monitoring Panes

The `logwatch` pattern — the use case the user explicitly called out:

```zsh
# zsh function: open a tmux pane with a filtered log stream
logwatch() {
    local subsystem="${1:-}"
    local predicate="${2:-}"

    # Build predicate from args
    if [[ -n "$subsystem" && -z "$predicate" ]]; then
        predicate="subsystem==\"$subsystem\""
    fi

    local cmd="sudo log stream --level debug"
    [[ -n "$predicate" ]] && cmd+=" --predicate '$predicate'"

    if [[ -n "$TMUX" ]]; then
        tmux split-window -v "$cmd"
    else
        eval "$cmd"
    fi
}

# Usage:
logwatch com.apple.sharing
logwatch "" "process==\"Safari\" and type=error"
```

This is an installable zsh autoload function (fits zsh-dev's generation pattern, references signals-monitoring knowledge).

---

## How Terminal-Guru Agent Routes

Updated routing table for `agents/terminal-guru.md`:

| User says... | Routes to |
|---|---|
| "garbled characters", "wrong colors", "box drawing broken" | terminal-emulation |
| "create a zsh function", "slow startup", "test my config" | zsh-dev |
| "check logs", "stream logs", "why is X doing Y", "debug my app" | **signals-monitoring** |
| "my script isn't handling Ctrl+C", "trap SIGTERM", "kill a process gracefully" | **signals-monitoring** |
| "watch for file changes", "run tests on save" | **signals-monitoring** |

---

## macOS Notification System

Sending notifications from the terminal completes the signal loop: you're monitoring for events and alerting yourself when they happen.

**Native AppleScript** (no dependencies):
```bash
# Basic notification
osascript -e 'display notification "Build finished" with title "Terminal" subtitle "make"'

# With sound
osascript -e 'display notification "Tests passed" with title "CI" sound name "Glass"'
```

**`terminal-notifier`** (brew install terminal-notifier — richer options):
```bash
terminal-notifier -title "Deployment" -message "Production deploy complete" -sound default
terminal-notifier -title "Error" -message "Build failed" -activate com.apple.Terminal
# Click notification to bring Terminal to front; -group to replace previous notification
terminal-notifier -title "Watch" -message "File changed: $file" -group "file-watcher"
```

**Integration pattern** — notify on completion of long-running commands:
```zsh
# zsh function: run command and notify when done
notify_when_done() {
    local cmd="$*"
    eval "$cmd"
    local status=$?
    if (( status == 0 )); then
        osascript -e "display notification \"$cmd\" with title \"Done\" sound name \"Glass\""
    else
        osascript -e "display notification \"$cmd (exit $status)\" with title \"Failed\" sound name \"Basso\""
    fi
    return $status
}
```

Ties directly into the monitoring side: `logwatch` detects an event → triggers a notification.

---

## Key Decisions

1. **Skill name**: `signals-monitoring` — covers both Unix signals and system monitoring.
2. **`logwatch` function**: Lives in **both** — `signals-monitoring/scripts/` (as a skill script) AND generated as a zsh autoload function installable via `zsh-dev`'s `install_autoload.sh`.
3. **`logger` wrapper**: Include a `_log` helper pattern in references.
4. **`log config` (debug enabler)**: Footnote — mention it exists, don't make it a top-level section.
5. **File watching**: Include `fswatch`/`entr` patterns in references.
6. **Advanced tools** (`dtrace`, `dtruss`, `instruments` CLI): Skill is aware of them — note in SKILL.md as future capability, not yet covered in v1.
7. **macOS Notification System**: Included — `osascript` display notification + `terminal-notifier`. Completes the monitor→alert loop.
8. **iOS device logs** (`log collect --device`): Mention but don't deep-dive.

## Resolved Questions

- Structure: **new `signals-monitoring` skill** ✓
- Scope: **Unix signals + macOS logging + file watching + notifications** ✓
- `logwatch` home: **both** (signals-monitoring/scripts/ + zsh autoload function) ✓
- `log config`: **footnote** ✓
- dtrace/dtruss/instruments: **noted as future capability, not v1** ✓
- macOS notifications: **in scope** (`osascript` + `terminal-notifier`) ✓

## Open Questions

_None — ready to plan._

## Sources

- `man log` (macOS 26.3) — unified log command with predicate filtering
- `man logger` (macOS 26.3) — BSD syslog interface
- `man kill`, `man trap` (zsh builtins)
- Reference article: https://the-sequence.com/mac-logging-and-the-log-command-a-guide-for-apple-admins
- Existing skills: `plugins/terminal-guru/skills/terminal-emulation/` and `zsh-dev/`
