# macOS Unified Logging Guide

## Overview

Apple's unified logging system (introduced WWDC 2016) is the canonical way to read what macOS and macOS apps are doing. It replaced fragmented flat files in `/var/log/` with a single, structured, high-performance store accessible via the `log` command and Console.app.

Key properties:
- Covers all Apple platforms (macOS, iOS via `log collect --device`)
- Logs are structured with subsystem, category, process, and level metadata
- Default and info levels are stored in memory and may roll off; debug/fault are always persisted
- Most `log show` and `log stream` operations require `sudo` for full system access

The `log` binary lives at `/usr/bin/log`. Run `man log` for full reference.

---

## Reading Logs

### `log show` — Historical Log Retrieval

Show logs stored in the system datastore or a `.logarchive` file.

```bash
# Last minute of default-level logs
sudo log show --last 1m

# Last hour including info messages
sudo log show --last 1h --info

# Last hour including info + debug messages
sudo log show --last 1h --info --debug

# Specific time range
sudo log show --start "2026-03-05 09:00:00" --end "2026-03-05 09:30:00"

# From last boot
sudo log show --last boot
```

**Output styles** (`--style`):
- `default` — human readable with full metadata (ISO-8601, thread, PID, subsystem, category)
- `compact` — same info, less horizontal space
- `json` — machine-parseable JSON array
- `ndjson` — newline-delimited JSON (one event per line, good for streaming/piping)
- `syslog` — legacy syslog format

```bash
# Machine-readable output
sudo log show --last 1h --style ndjson | jq 'select(.messageType=="error")'
```

**Filtering by process:**
```bash
sudo log show --last 1h --process Safari
sudo log show --last 1h --process 1234       # by PID
```

**View a collected archive:**
```bash
sudo log show --archive ~/Desktop/system.logarchive
sudo log show --archive ~/Desktop/system.logarchive --predicate 'type=error'
```

---

### `log stream` — Real-Time Monitoring

Stream log events as they happen. Press Ctrl+C to stop.

```bash
# All default-level events (very noisy)
sudo log stream

# Only error and fault level
sudo log stream --level default   # default only
sudo log stream --level info      # default + info
sudo log stream --level debug     # all levels

# Auto-stop after 5 minutes
sudo log stream --timeout 5m

# Compact format for easier reading
sudo log stream --style compact --predicate 'process=="Finder"'
```

---

### `log collect` — Snapshot to Archive

Collect logs into a `.logarchive` bundle for offline analysis or sharing.

```bash
# Last 20 minutes to desktop
sudo log collect --output ~/Desktop/system.logarchive --last 20m

# Specific time range
sudo log collect --output ~/Desktop/incident.logarchive \
    --start "2026-03-05 14:00:00" --end "2026-03-05 14:30:00"

# Paired iOS/iPadOS device (first found)
sudo log collect --device --output ~/Desktop/device.logarchive --last 1h

# Named device
sudo log collect --device-name "My iPhone" --output ~/Desktop/device.logarchive --last 30m
```

Then view with:
```bash
sudo log show --archive ~/Desktop/system.logarchive
sudo log show --archive ~/Desktop/system.logarchive --predicate 'type=error' --last 30m
```

> Note: `sysdiagnose` (filed feedback to Apple) automatically includes a `system_logs.logarchive`.

---

### `log stats` — Log Volume Analysis

Understand which processes or senders generate the most log traffic.

```bash
# Overview of last hour
log stats --last 1h --overview

# Per-process breakdown, sorted by event count
log stats --last 1h --per-process --sort events

# Per-sender (library/framework) breakdown
log stats --last 1h --per-sender --sort bytes

# Stats for an archive
log stats --archive ~/Desktop/system.logarchive --overview
```

Useful for identifying noisy processes before narrowing with predicates.

---

## Predicate Filtering

Predicates are the most powerful feature of `log` — they filter by any structured metadata field. Supported by `log show`, `log stream`, and `log collect`.

### NSPredicate Syntax

Full NSPredicate rules (see [Apple Predicate Programming Guide](https://developer.apple.com/library/mac/documentation/Cocoa/Conceptual/Predicates/Articles/pSyntax.html)):

**Supported keys:**

| Key | Description |
|-----|-------------|
| `subsystem` | Reverse-DNS namespace (os_log messages only) |
| `category` | Subdivision within a subsystem (requires subsystem) |
| `process` | Process name |
| `processImagePath` | Full path to process binary |
| `sender` | Library/framework name that originated the event |
| `senderImagePath` | Full path to originating library/framework |
| `eventMessage` | The message text |
| `messageType` | Log level: `default`, `info`, `debug`, `error`, `fault` |
| `eventType` | Event type: `logEvent`, `activityCreateEvent`, etc. |

**Operators:** `==`, `!=`, `CONTAINS`, `CONTAINS[cd]`, `BEGINSWITH`, `ENDSWITH`, `IN`, `&&`, `||`, `!`

```bash
# Specific subsystem
sudo log show --last 1h --predicate 'subsystem == "com.apple.sharing"'

# Subsystem + category
sudo log show --predicate '(subsystem == "com.apple.sharing") && (category == "AirDrop")'

# Multiple categories
sudo log show --predicate '(subsystem == "com.apple.sharing") && (category IN {"AirDrop", "Bonjour"})'

# Process by path suffix
sudo log show --predicate 'processImagePath ENDSWITH "Safari"'

# Message content (case-insensitive)
sudo log show --last 1h --predicate 'eventMessage CONTAINS[ci] "timeout"'

# Errors only from a process
sudo log stream --predicate 'process == "Finder" && messageType == "error"'

# Subsystem + sender framework
sudo log show --predicate \
    '(subsystem == "com.apple.network") && (senderImagePath CONTAINS "CFNetwork")'
```

### Shorthand Syntax

A faster alternative — same `--predicate` flag, different syntax. Run `log help shorthand` for full reference.

| Shorthand key | Full key equivalent |
|--------------|---------------------|
| `s` or `subsystem` | `subsystem` |
| `c` or `category` | `category` |
| `p` or `process` | `process` |
| `pid` | process ID |
| `type` | `messageType` |
| `m` or message | `eventMessage` (omit key to match message) |

**Operators:** `=` (equals), `!=`, `:` (contains), `!:` (not contains), `:^` (starts with), `endswith`, `~/regex/`

**Values:** Use `|` as logical OR on the right side.

```bash
# Subsystem equality
sudo log show --predicate 's=com.apple.sharing'

# Category contains "network"
sudo log stream --predicate 'c:network'

# Process name, error or fault type
sudo log stream --predicate 'p=Safari and type=error|fault'

# Subsystem + category + message content
sudo log show --last 1h \
    --predicate 's=com.apple.sharing and c:airdrop and "connection"'

# Multiple processes
sudo log stream --predicate 'p=Safari|Finder and type=error'
```

---

## Writing Logs from Shell

### `logger` — BSD Syslog Interface

`logger` writes entries into the unified logging system via the syslog interface. Entries appear with `process == "logger"` and are searchable.

```bash
# Basic — tag identifies the source
logger -t "my-script" "task started"

# With priority/facility
logger -t "my-script" -p user.info "processing $# items"
logger -t "my-script" -p user.debug "variable value: $var"
logger -t "my-script" -p user.error "something failed: exit $?"

# Also print to stderr (useful during development)
logger -t "my-script" -s "visible in terminal AND in log"

# Read from file
logger -t "my-script" -f /tmp/output.txt
```

**Priority/facility format** `-p facility.level`:
- Facilities: `user`, `local0`–`local7`, `daemon`, `syslog`
- Levels: `emerg`, `alert`, `crit`, `err`, `warning`, `notice`, `info`, `debug`
- Common: `user.info`, `user.debug`, `user.error`, `user.warning`

**Finding your entries:**
```bash
# All logger entries from last hour
log show --last 1h --predicate 'process=="logger"'

# Your tagged entries
log show --last 1h --predicate 'process=="logger" and eventMessage contains "my-script"'

# Real-time stream of your script's logs
log stream --predicate 'process=="logger" and eventMessage contains "my-script"'
```

> **Note on subsystem/category**: `logger` uses the BSD syslog interface and does not support `subsystem` or `category` (those are `os_log` API concepts available to Swift/C/Obj-C code). Use the `-t` tag as your identifier and filter with `eventMessage contains "your-tag"`.

### `_log` — Consistent Helper Pattern for Zsh Functions

A thin wrapper around `logger` for structured logging in zsh autoload functions:

```zsh
# Add to your function file or a shared autoload helper
_log() {
    local level="${1:-info}"; shift
    # Use calling function name as tag, fall back to "zsh"
    local tag="${funcstack[2]:-zsh}"
    logger -t "$tag" -p "user.$level" "$*"
}

# Usage inside any zsh function:
my_deploy() {
    _log info "starting deploy to $1"
    # ... work ...
    _log debug "upload complete, running migrations"
    # ... work ...
    _log info "deploy finished"
}

# Watch in real time while it runs:
# log stream --predicate 'process=="logger" and eventMessage contains "my_deploy"'
```

---

## `log config` — Enable Debug Logging for a Subsystem

> **Footnote / Advanced**: Requires root. Temporarily enables debug or info messages for a specific subsystem — useful when debugging your own app or a system component that normally only logs at default level.

```bash
# Enable debug logging for a subsystem
sudo log config --mode "level:debug" --subsystem com.mycompany.myapp

# Check current config
sudo log config --status --subsystem com.mycompany.myapp

# Reset to default after debugging
sudo log config --reset --subsystem com.mycompany.myapp
```

Enable → reproduce the issue → collect/show → reset. Forgetting to reset leaves debug logging on system-wide for that subsystem.
