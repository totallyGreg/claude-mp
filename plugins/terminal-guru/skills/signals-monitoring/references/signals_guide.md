# Unix Signals Guide

## Overview

Signals are asynchronous notifications sent to a process by the kernel, another process, or the user (e.g., Ctrl+C). Every Unix process can receive signals, and shell scripts can intercept them with `trap` to perform cleanup or change behavior.

Understanding signals is essential for:
- Writing shell scripts that clean up temp files and locks reliably
- Implementing graceful shutdown in long-running functions
- Sending reload signals to daemons without restarting them
- Handling broken pipes in shell pipelines

---

## Signal Reference

Core signals you'll encounter in terminal and shell work:

| Signal | Number | Default action | Catchable? | Common use |
|--------|--------|---------------|-----------|------------|
| `SIGHUP` | 1 | Terminate | Yes | Terminal closed; conventionally: reload config |
| `SIGINT` | 2 | Terminate | Yes | Ctrl+C — user interrupt |
| `SIGQUIT` | 3 | Core dump | Yes | Ctrl+\ — quit with core dump |
| `SIGKILL` | 9 | Terminate | **No** | Force kill — cannot be caught or ignored |
| `SIGTERM` | 15 | Terminate | Yes | Graceful shutdown request (default for `kill`) |
| `SIGSTOP` | 19 | Stop | **No** | Ctrl+Z — pause process (cannot be caught) |
| `SIGCONT` | 18 | Continue | Yes | Resume a stopped process (`fg`, `bg`) |
| `SIGPIPE` | 13 | Terminate | Yes | Write to a broken pipe |
| `SIGUSR1` | 30 | Terminate | Yes | App-defined — custom use |
| `SIGUSR2` | 31 | Terminate | Yes | App-defined — custom use |
| `SIGCHLD` | 20 | Ignore | Yes | Child process stopped or terminated |
| `SIGWINCH` | 28 | Ignore | Yes | Terminal window resized |

> `SIGKILL` (9) and `SIGSTOP` (19) cannot be caught, blocked, or ignored. They always succeed.

---

## Sending Signals

### `kill` — Send Signal by PID

```bash
# Default signal is SIGTERM (15) — graceful shutdown request
kill <pid>
kill -TERM <pid>    # same as above, explicit

# Force kill — use only when SIGTERM doesn't work
kill -KILL <pid>
kill -9 <pid>       # numeric form

# Reload config (nginx, sshd, launchd agents, etc.)
kill -HUP <pid>
kill -1 <pid>

# Send SIGUSR1 (app-defined)
kill -USR1 <pid>

# Send to multiple PIDs
kill -TERM 1234 5678

# Signal by name or number — both work
kill -s TERM <pid>
kill -s 15 <pid>
```

### `pkill` / `pgrep` — Signal by Name

```bash
# Find PIDs by process name
pgrep nginx               # list matching PIDs
pgrep -l nginx            # list with names

# Send signal to matching processes
pkill nginx               # SIGTERM to all nginx processes
pkill -HUP nginx          # reload all nginx workers
pkill -9 -f "python my_script.py"   # -f matches full command line

# Confirm what would be killed first
pgrep -l -f "my pattern"
```

### `killall` — Signal by Name (macOS)

```bash
killall Safari            # SIGTERM to all processes named "Safari"
killall -HUP sshd         # reload sshd config
killall -9 Finder         # force kill Finder (it will relaunch)
```

### Job Control Signals

```bash
# Pause a foreground process (sends SIGSTOP)
Ctrl+Z

# Resume in background
bg

# Resume in foreground
fg

# List jobs
jobs

# Send signal to job by job number
kill -TERM %1    # job 1
kill %2          # SIGTERM to job 2
```

---

## `trap` — Intercepting Signals in Shell Scripts

`trap` registers a command to run when the shell receives a signal. Essential for cleanup in any script that creates temp files, holds locks, or spawns background processes.

### Syntax

```zsh
trap 'command_or_function' SIGNAL [SIGNAL...]
trap - SIGNAL          # reset to default behavior
trap '' SIGNAL         # explicitly ignore the signal
```

**Pseudo-signals** (not real Unix signals, but handled by trap):
- `EXIT` — fires when the shell exits for any reason (normal exit, signal, error)
- `ERR` — fires when a command returns non-zero (bash only, not reliably in zsh)
- `DEBUG` — fires before each command

### Pattern 1: Cleanup on Exit

The most important pattern. `EXIT` fires on Ctrl+C, SIGTERM, and normal exit — use it for all cleanup:

```zsh
#!/usr/bin/env zsh

# Create temp resources
tmpfile=$(mktemp)
lockfile="/tmp/my-script.lock"
touch "$lockfile"

# Register cleanup — runs no matter how the script exits
trap 'rm -f "$tmpfile" "$lockfile"' EXIT

# ... rest of script ...
# Cleanup happens automatically
```

### Pattern 2: Graceful Shutdown with Message

```zsh
#!/usr/bin/env zsh

cleanup() {
    echo "Shutting down..." >&2
    # stop background jobs, flush buffers, etc.
    kill $(jobs -p) 2>/dev/null
    wait
}

trap 'cleanup; exit 130' INT    # 130 = 128 + SIGINT(2)
trap 'cleanup; exit 143' TERM   # 143 = 128 + SIGTERM(15)
trap 'cleanup' EXIT             # also runs on normal exit
```

### Pattern 3: Config Reload on SIGHUP

```zsh
#!/usr/bin/env zsh

CONFIG_FILE="$HOME/.myconfig"
load_config() { source "$CONFIG_FILE" }

load_config  # initial load

trap 'load_config; echo "config reloaded"' HUP

# Long-running loop
while true; do
    do_work
    sleep 5
done
```

Trigger reload from another terminal: `kill -HUP <pid>`

### Pattern 4: Ignore SIGPIPE

When a script writes to a pipeline where the reader exits early:

```zsh
# Suppress SIGPIPE — prevents "write error: Broken pipe" messages
trap '' PIPE

# Example: head exits after 10 lines, but the producer keeps running
produce_output | head -10
```

### Pattern 5: Long-Running Zsh Autoload Function with Cleanup

The canonical pattern for any autoload function that runs indefinitely:

```zsh
# File: ~/.zsh/functions/my_watcher
my_watcher() {
    local tmpdir
    tmpdir=$(mktemp -d)

    # Cleanup fires on Ctrl+C, kill, or normal return
    trap "rm -rf '$tmpdir'; trap - INT TERM EXIT; return 0" INT TERM EXIT

    echo "Watching... (Ctrl+C to stop)"
    while true; do
        # ... do work using $tmpdir ...
        sleep 2
    done
}

my_watcher "$@"
```

Key details:
- `trap - INT TERM EXIT` inside the handler resets traps before returning, preventing double-execution
- `return 0` (not `exit 0`) is correct inside a function
- `trap` inside a function is local to the function's execution context in zsh

### Pattern 6: Nested Traps / Saving and Restoring

```zsh
# Save existing trap, set new one, restore after
old_trap=$(trap -p INT)
trap 'echo "custom handler"' INT
# ... do sensitive work ...
eval "$old_trap"   # restore original trap
```

---

## Common Daemon Reload Patterns

Services that respond to SIGHUP by reloading their config (without restart):

```bash
# nginx
sudo kill -HUP $(cat /var/run/nginx.pid)
# or
sudo pkill -HUP nginx

# sshd
sudo kill -HUP $(pgrep sshd)

# launchd-managed services — use launchctl instead
sudo launchctl kickstart -k system/com.apple.sshd
```

---

## Signal Propagation and Background Jobs

```bash
# Kill a process group (process + all children)
kill -TERM -<pgid>    # negative PID = process group ID

# Find process group
ps -o pgid= -p <pid>

# Kill all children of a script
trap 'kill 0' EXIT    # kill the entire process group on exit
```

```zsh
# In a script, wait for background jobs and forward signals
child_pid=""
long_running_command &
child_pid=$!

trap 'kill -TERM "$child_pid" 2>/dev/null; wait "$child_pid"' INT TERM EXIT
wait "$child_pid"
```
