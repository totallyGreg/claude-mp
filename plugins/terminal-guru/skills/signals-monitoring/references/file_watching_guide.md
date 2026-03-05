# File Watching Guide

## Overview

File watching triggers actions automatically when files or directories change — useful for rebuilding on save, running tests continuously, syncing files, or monitoring config changes. macOS has built-in FSEvents support; the best CLI tools wrap it.

---

## `fswatch` — Event-Based File Watcher

Monitors paths using macOS FSEvents (or kqueue/inotify on other platforms). Events are printed to stdout; pipe to a command to act on them.

**Install:** `brew install fswatch`

### Basic Usage

```bash
# Watch a directory — print a line for each changed file
fswatch ./src

# Watch and run a command on any change (-o collapses events into a count)
fswatch -o ./src | xargs -n1 -I{} make build

# Watch specific file types
fswatch -e ".*" -i "\.swift$" ./src | xargs -n1 -I{} swift build

# Watch multiple paths
fswatch ./src ./config | xargs -n1 echo "Changed:"

# Watch and run tests
fswatch -o ./src | xargs -n1 -I{} sh -c 'clear && swift test'
```

### Useful Flags

| Flag | Description |
|------|-------------|
| `-o` | Collapse events; print count (use with xargs -n1) |
| `-r` | Recursive (default for directories) |
| `-l <secs>` | Latency between events (default 1s) |
| `-e <regex>` | Exclude paths matching pattern |
| `-i <regex>` | Include only paths matching pattern |
| `--event Created` | Filter by event type (Created, Updated, Removed, Renamed) |
| `-1` | Exit after first event |

```bash
# Rebuild only when .go files change, excluding vendor/
fswatch -o -e "vendor" -i "\.go$" . | xargs -n1 -I{} go build ./...

# Watch a config file and reload a service
fswatch -1 /etc/nginx/nginx.conf && sudo nginx -s reload

# Print full event info (file + event type)
fswatch --event-flags ./src
```

### Notification on Change

```bash
# Notify when a file changes
fswatch ~/Documents/important.txt | \
    xargs -n1 -I{} osascript -e 'display notification "File changed" with title "fswatch"'
```

---

## `entr` — Run Commands on File Change

More ergonomic than fswatch for development loops. Reads a list of files from stdin, re-runs a command when any changes.

**Install:** `brew install entr`

### Basic Usage

```bash
# Re-run tests when any Swift file changes
ls src/**/*.swift | entr -c swift test

# Rebuild when any Go file changes
find . -name "*.go" | entr -c go build ./...

# Reload server when config changes
echo config.yaml | entr -r ./myserver --config config.yaml

# Run shell command
ls *.md | entr -c sh -c 'pandoc index.md -o index.html && echo "Built"'
```

### Useful Flags

| Flag | Description |
|------|-------------|
| `-c` | Clear screen before each run |
| `-r` | Restart a long-running process (send SIGTERM, wait, restart) |
| `-s` | Use `sh -c` to run the command (enables shell features) |
| `-p` | Postpone first run until a file changes |
| `-d` | Track new files added to watched directories |

```bash
# Restart a dev server when source changes (with -r for long-running processes)
find . -name "*.py" | entr -r python server.py

# Watch for new files too
ls src/*.js | entr -d -c npm test

# Postpone first execution
find . -name "*.rb" | entr -p ruby test.rb
```

### Combining with find

```bash
# Recursive with find (more flexible than ls glob)
find src -name "*.swift" | entr -c swift test

# Multiple file types
find . \( -name "*.go" -o -name "*.tmpl" \) | entr -c go build
```

---

## Process Inspection

### `pgrep` / `pkill` — Find Processes

```bash
# Find PIDs by name
pgrep Safari              # PIDs only
pgrep -l Safari           # PIDs + names
pgrep -f "python script"  # match full command line

# Find and display process info
pgrep -a nginx            # full command line

# Count matching processes
pgrep -c nginx
```

### `ps` — Process Snapshot

```bash
# All processes, full detail
ps aux

# Find a specific process
ps aux | grep -i safari

# Tree view (process hierarchy)
ps auxf

# Specific fields for a PID
ps -o pid,ppid,pcpu,pmem,comm -p <pid>

# All processes by a user
ps -u $(whoami) aux
```

### `lsof` — List Open Files and Network Connections

`lsof` ("list open files") shows everything a process has open — files, sockets, pipes.

```bash
# All open files for a process
lsof -p <pid>

# What process is using a port
lsof -i :8080
lsof -i :443
lsof -i TCP:3000

# All network connections
lsof -i

# Files a specific process has open (by name)
lsof -c Safari

# Who has a file open
lsof /path/to/file

# Files in a directory
lsof +D /path/to/dir

# Filter to just network sockets
lsof -i -n -P   # -n = no hostname lookup, -P = no port name lookup
```

### `top` / `htop` — Resource Usage

```bash
# Interactive top (press 'q' to quit)
top

# Non-interactive snapshot — one iteration
top -l 1

# Monitor a specific PID
top -pid <pid>

# Sort by CPU usage
top -o cpu

# Sort by memory
top -o mem

# htop — better UI (brew install htop)
htop
htop --pid <pid>
```

### `vm_stat` / `iostat` — System Resources

```bash
# Memory statistics
vm_stat

# Disk I/O statistics (1-second interval)
iostat -d 1

# Network interface statistics
netstat -i
```

---

## Native File Watch (No Dependencies)

For simple cases without installing fswatch/entr:

```bash
# Poll a file for changes with a loop
watch_file() {
    local file="$1"
    local cmd="${@:2}"
    local prev_hash=""
    while true; do
        local curr_hash
        curr_hash=$(md5 -q "$file" 2>/dev/null)
        if [[ "$curr_hash" != "$prev_hash" ]]; then
            prev_hash="$curr_hash"
            eval "$cmd"
        fi
        sleep 1
    done
}

# Usage: watch_file config.yaml "echo 'config changed'"
```

> This polling approach has ~1s latency and is CPU-intensive for many files. Prefer `fswatch` or `entr` for real use.

---

## Practical Workflows

### Auto-test on save (Swift)
```bash
find . -name "*.swift" | entr -c swift test 2>&1 | head -50
```

### Auto-rebuild and notify (any project)
```bash
fswatch -o ./src | xargs -n1 -I{} sh -c \
    'make build 2>&1 && \
     osascript -e "display notification \"Build OK\" with title \"Make\" sound name \"Glass\"" || \
     osascript -e "display notification \"Build FAILED\" with title \"Make\" sound name \"Basso\""'
```

### Watch a log file (flat file, not unified log)
```bash
tail -f /var/log/install.log
tail -f /var/log/system.log | grep -i error
```

### Monitor when a process finishes
```bash
# Wait for a PID to exit, then notify
wait_for_pid() {
    local pid=$1
    while kill -0 "$pid" 2>/dev/null; do sleep 1; done
    osascript -e "display notification \"Process $pid finished\" with title \"Done\""
}
wait_for_pid 12345
```
