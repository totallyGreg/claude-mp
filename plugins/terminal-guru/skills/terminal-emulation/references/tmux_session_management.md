# Tmux Session Management

Reference for creating, naming, and managing tmux sessions using `sesh`, `direnv`, and the `tmux-logging` plugin. Based on the "Creating Tmux sessions" workflow.

---

## Session Manager: sesh

`sesh` (v2.24+) integrates tmux, zoxide, and fzf for session management.

### Keybinding (M-backtick)

Bound in `~/.config/tmux/tmux.conf`:

```tmux
bind-key -n "M-`" run-shell "sesh connect \"$(
    sesh list -tzi | fzf-tmux -p 55%,60% \
        --ansi --no-sort --border-label ' sesh ' --prompt '⚡  ' \
        --header '  ^a all ^t tmux ^g configs ^x zoxide ^d tmux kill ^f find' \
        --bind 'tab:down,btab:up' \
        --bind 'ctrl-a:change-prompt(⚡  )+reload(sesh list -i)' \
        --bind 'ctrl-t:change-prompt(   )+reload(sesh list -ti)' \
        --bind 'ctrl-g:change-prompt(⚙️  )+reload(sesh list -ci)' \
        --bind 'ctrl-x:change-prompt(   )+reload(sesh list -zi)' \
        --bind 'ctrl-f:change-prompt(󰥨   )+reload(fd -H -d 2 -t d -E .Trash . ~)' \
        --bind 'ctrl-d:execute(tmux kill-session -t {})+change-prompt(⚡  )+reload(sesh list)'
)\""
```

### Modes

| Shortcut | Mode | Source |
|----------|------|--------|
| Ctrl-a | All | tmux + zoxide + configs |
| Ctrl-t | Tmux | Existing tmux sessions only |
| Ctrl-g | Configs | Configured session definitions |
| Ctrl-x | Zoxide | Frecent directories |
| Ctrl-f | Find | `fd` search under `~` |
| Ctrl-d | Kill | Kill selected tmux session |

Selecting a zoxide directory creates a new tmux session named after the directory basename with the working directory set to that path.

---

## Session Naming Convention

### Customer/Ticket Work

Pattern: `CUSTOMER-TICKET-TOPIC`

```bash
CUSTOMER="CBP"
TICKET="ZD_3053"
ISSUE="${CUSTOMER}-${TICKET}"
TOPIC="SSE"
SESSION_NAME=${ISSUE}-${TOPIC}    # CBP-ZD_3053-SSE
WORKDIR=$AMER/${ISSUE/-/\/}       # Replace dash with slash for path
CLUSTER_NAME=${SESSION_NAME}      # Must be alphanumeric + hyphens, lowercase, start with letter
```

### Project Work

Use a descriptive slug: `airs-demo-env`, `guardian-local-scan`, etc.

---

## Environment Setup with direnv

Place a `.envrc` in the working directory. `direnv` loads it automatically when entering the directory (including new tmux panes).

```bash
# Customer context example
export CUSTOMER="CBP"
export TICKET="ZD_3053"
export ISSUE="${CUSTOMER}-${TICKET}"
export TOPIC="SSE"
export SESSION_NAME=${ISSUE}-${TOPIC}

# API credentials (customer-specific)
export GUARDIAN_API_CLIENT_ID="..."
export GUARDIAN_API_CLIENT_SECRET="..."
```

---

## Pane Logging (tmux-logging plugin)

Configuration in `tmux.conf`:

```tmux
set -g @plugin 'tmux-plugins/tmux-logging'
set -g @logging-path "$HOME/Library/Logs/Terminal-Logs"
set -g @screen-capture-path "#{pane_current_path}"
set -g @save-complete-history-path "#{pane_current_path}"
set -g @save-complete-history-key "F7"
```

### Commands

| Keybinding | Action | Output Location |
|------------|--------|-----------------|
| prefix + Shift-P | Toggle continuous pane logging | `~/Library/Logs/Terminal-Logs/` |
| prefix + Alt-P | Screen capture (visible content) | `#{pane_current_path}` |
| F7 | Save complete pane history | `#{pane_current_path}` |

### Programmatic Logging

For agent-driven workflows that need to read pane output:

```bash
# Enable logging to a specific file
tmux pipe-pane -o -t "${SESSION_NAME}:${WINDOW}.${PANE}" 'cat >> /tmp/pane-${SESSION_NAME}-${WINDOW}-${PANE}.log'

# Disable logging
tmux pipe-pane -t "${SESSION_NAME}:${WINDOW}.${PANE}"

# Read pane contents directly (no logging needed)
tmux capture-pane -t "${SESSION_NAME}:${WINDOW}.${PANE}" -p
```

---

## Session Persistence

Managed by `tmux-resurrect` + `tmux-continuum`:

```tmux
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @plugin 'tmux-plugins/tmux-continuum'
set -g @continuum-save-interval '5'
set -g @continuum-restore 'off'
```

| Keybinding | Action |
|------------|--------|
| prefix + Ctrl-S | Manual save |
| prefix + Ctrl-R | Manual restore |

`detach-on-destroy` is off — closing a session switches to the next one rather than detaching from tmux.

---

## Key tmux.conf Settings

```tmux
# Prefix
set-option -g prefix C-a

# Session behavior
set-option -g detach-on-destroy off
set-option -g base-index 1
set-option -g pane-base-index 1
set-option -g renumber-windows on

# Terminal
set -g default-terminal "tmux-256color"
set -as terminal-features ",xterm-256color:RGB"

# Mouse
set-option -g mouse on

# Environment passthrough
set -g update-environment "DISPLAY AWS_SSO_PROFILE ExpressVPN SSH_ASKPASS SSH_AUTH_SOCK SSH_AGENT_PID SSH_CONNECTION SSH_TTY WINDOWID XAUTHORITY"
```

---

## Creating a Session Programmatically

```bash
# Create a named session at a specific directory
tmux new-session -d -s "${SESSION_NAME}" -c "${WORKDIR}"

# Add windows/panes
tmux new-window -t "${SESSION_NAME}" -n "logs" -c "${WORKDIR}"
tmux split-window -t "${SESSION_NAME}:logs" -v -c "${WORKDIR}"

# Enable logging on all panes
for pane in $(tmux list-panes -t "${SESSION_NAME}" -F '#{window_index}.#{pane_index}'); do
    tmux pipe-pane -o -t "${SESSION_NAME}:${pane}" \
        "cat >> /tmp/${SESSION_NAME}-${pane//\./-}.log"
done

# Attach
tmux attach-session -t "${SESSION_NAME}"
```
