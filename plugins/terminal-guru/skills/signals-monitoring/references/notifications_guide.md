# macOS Notifications Guide

## Overview

Send macOS user notifications from the terminal — useful for alerting yourself when long-running commands finish, monitoring scripts detect events, or build systems succeed or fail. Two approaches: native `osascript` (no dependencies) and `terminal-notifier` (richer options, Homebrew).

---

## Native: `osascript` Notifications

No installation required. Uses AppleScript's `display notification` command.

### Basic Syntax

```bash
osascript -e 'display notification "message" with title "Title"'
```

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `"message"` | Yes | The body text |
| `with title "..."` | No | Bold header (recommended) |
| `subtitle "..."` | No | Secondary line below title |
| `sound name "..."` | No | System sound to play |

```bash
# Minimal
osascript -e 'display notification "Done"'

# With title
osascript -e 'display notification "Build finished" with title "Make"'

# With subtitle and sound
osascript -e 'display notification "All tests passed" with title "CI" subtitle "main branch" sound name "Glass"'

# Failure notification
osascript -e 'display notification "Build failed — check output" with title "Make" sound name "Basso"'
```

### Common Sound Names

| Sound | Tone |
|-------|------|
| `Glass` | Soft success chime |
| `Basso` | Deep failure thud |
| `Ping` | Light alert |
| `Purr` | Subtle purr |
| `Sosumi` | Classic Mac alert |
| `Blow` | Soft whoosh |
| `Frog` | Frog croak |
| `Pop` | Sharp pop |

Browse in `/System/Library/Sounds/` — use filename without `.aiff`.

### Shell Variable Interpolation

Use double quotes for the outer string to interpolate variables (but escape inner quotes):

```bash
# Using shell variable in notification
status="success"
osascript -e "display notification \"Deploy $status\" with title \"CI\" sound name \"Glass\""

# Or use heredoc for complex messages
osascript << 'EOF'
display notification "Build done" with title "Make" sound name "Glass"
EOF
```

---

## `terminal-notifier` — Richer Notifications

More control over notification behavior, including click actions, grouping, and app activation.

**Install:** `brew install terminal-notifier`

### Basic Usage

```bash
terminal-notifier -title "Title" -message "Message body"
terminal-notifier -title "Deploy" -message "Production live" -sound default
```

### Key Options

| Flag | Description |
|------|-------------|
| `-title` | Bold notification title |
| `-subtitle` | Secondary line |
| `-message` | Body text (required) |
| `-sound` | Sound name (use `default` for system default) |
| `-group <id>` | Group ID — replaces previous notification with same ID |
| `-activate <bundle>` | App to bring to front when clicked |
| `-open <url>` | URL to open when notification is clicked |
| `-execute <cmd>` | Shell command to run when clicked |
| `-sender <bundle>` | Appear as if from another app (e.g., com.apple.Terminal) |
| `-ignoreDnD` | Show even in Do Not Disturb mode |

```bash
# Basic with sound
terminal-notifier -title "Tests" -message "All passing" -sound default

# Click to open Terminal
terminal-notifier -title "Build done" -message "See output" \
    -activate com.apple.Terminal

# Open a URL on click
terminal-notifier -title "Server ready" -message "localhost:3000" \
    -open "http://localhost:3000"

# Group: replace previous notification with same group ID
# (avoids notification spam during rapid file changes)
terminal-notifier -title "File Watch" -message "Changed: config.yaml" \
    -group "file-watcher"

# Execute a command when clicked
terminal-notifier -title "Deployment done" -message "Click to check logs" \
    -execute "open -a Terminal"
```

### Checking If Installed

Always fall back to `osascript` if `terminal-notifier` isn't available:

```zsh
notify() {
    local title="$1" message="$2" sound="${3:-Glass}"
    if command -v terminal-notifier &>/dev/null; then
        terminal-notifier -title "$title" -message "$message" -sound default
    else
        osascript -e "display notification \"$message\" with title \"$title\" sound name \"$sound\""
    fi
}
```

---

## Practical Patterns

### `notify_when_done` — Wrap Any Command

Run a command and send a success/failure notification when it finishes:

```zsh
# Add to ~/.zshrc or as a zsh autoload function
notify_when_done() {
    if [[ $# -eq 0 ]]; then
        echo "Usage: notify_when_done <command> [args...]" >&2
        return 1
    fi

    local cmd_display="$*"
    "$@"
    local status=$?

    if (( status == 0 )); then
        osascript -e "display notification \"$cmd_display\" \
            with title \"Done ✓\" sound name \"Glass\""
    else
        osascript -e "display notification \"$cmd_display (exit $status)\" \
            with title \"Failed ✗\" sound name \"Basso\""
    fi

    return $status
}

# Usage:
notify_when_done make build
notify_when_done swift test
notify_when_done kubectl apply -f k8s/production.yaml
notify_when_done npm run build
```

### Notify After Long Command (Append Style)

Add to end of a one-off command without a wrapper function:

```bash
# Append && notification for success
make build && osascript -e 'display notification "Build OK" with title "Make" sound name "Glass"'

# Notify regardless of outcome
make build; osascript -e "display notification \"exit $?\" with title \"Make\""

# Full success/failure in one line
make build \
    && osascript -e 'display notification "Build OK" with title "Make" sound name "Glass"' \
    || osascript -e 'display notification "Build FAILED" with title "Make" sound name "Basso"'
```

### Notify When a Process Finishes

```zsh
notify_pid() {
    local pid="$1"
    local label="${2:-Process $pid}"
    if ! kill -0 "$pid" 2>/dev/null; then
        echo "PID $pid not found" >&2
        return 1
    fi
    # Wait for process to finish
    while kill -0 "$pid" 2>/dev/null; do sleep 2; done
    osascript -e "display notification \"$label finished\" with title \"Done\" sound name \"Glass\""
}

# Usage: start something, get its PID, then watch it
./long_running_script.sh &
notify_pid $! "long_running_script"
```

### Notify from File Watcher

```bash
# fswatch + notification on change (with terminal-notifier grouping)
fswatch ./src | while read file; do
    terminal-notifier \
        -title "File Changed" \
        -message "$(basename "$file")" \
        -group "fswatch-src"
done
```

### Scheduled or Delayed Notification

```bash
# Notify in 30 minutes (reminder)
(sleep 1800 && osascript -e 'display notification "Time check!" with title "Reminder"') &

# At a specific time using `at` (if enabled)
echo 'osascript -e "display notification \"Meeting!\" with title \"Calendar\""' | at 14:30
```

---

## Notification Center Permissions

If notifications don't appear, check System Settings → Notifications → Terminal (or the app running the command).

```bash
# Test if notifications are working
osascript -e 'display notification "Test notification" with title "Test" sound name "Ping"'
```

If the notification appears but silently, check:
- System Settings → Notifications → [App] → Alert style (set to "Banners" or "Alerts")
- Focus / Do Not Disturb mode
- For `terminal-notifier`: it may need to be run once manually to request permission
