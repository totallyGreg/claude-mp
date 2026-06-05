# Tmux Plugins & Hooks

Reference for the tmux plugin ecosystem (TPM), the hook event system, and patterns for writing plugins that react dynamically to state changes. Includes the testing protocol that addresses the failure mode from issue #41.

---

## TPM Layout

Tmux Plugin Manager (TPM) lives at `~/.config/tmux/plugins/tpm` (or `~/.tmux/plugins/tpm`). Plugins are declared in `tmux.conf`:

```tmux
set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @plugin 'tmux-plugins/tmux-continuum'
set -g @plugin 'tmux-plugins/tmux-logging'

# Plugin-specific config — convention: @plugin-name-setting
set -g @resurrect-strategy-vim 'session'
set -g @continuum-save-interval '5'

# TPM init must be the LAST line
run '~/.config/tmux/plugins/tpm/tpm'
```

Keybindings (default prefix is `C-b`; many users rebind to `C-a`):

| Bind     | Action                          |
| -------- | ------------------------------- |
| prefix + I | Install new plugins from config |
| prefix + U | Update all plugins              |
| prefix + alt-u | Uninstall plugins removed from config |

## Plugin Anatomy

A TPM plugin is a git repo with an entry script (`<name>.tmux`) at the root. TPM clones the repo into `~/.config/tmux/plugins/<name>/` and sources the entry script during tmux startup.

```
my-plugin/
├── my-plugin.tmux              # entry — sets bindings, hooks, options
├── scripts/
│   ├── do_thing.sh             # action scripts called by bindings/hooks
│   └── refresh_status.sh
└── README.md
```

`my-plugin.tmux` is run **once** at tmux start (or on TPM install). It registers bindings, hooks, and initial options. It does NOT loop or stay running.

## Hooks

Hooks fire tmux commands when events occur. Register with `set-hook`:

```bash
tmux set-hook -g <event> '<tmux-command>'
```

### Common hook events

| Event                       | Fires when                                       |
| --------------------------- | ------------------------------------------------ |
| `after-new-window`          | a new window is created                          |
| `after-new-session`         | a new session is created                         |
| `after-kill-pane`           | a pane is killed                                 |
| `pane-exited`               | a pane's foreground process exits                |
| `session-window-changed`    | the active window in a session changes           |
| `client-attached`           | a client attaches to the server                  |
| `client-detached`           | a client detaches                                |
| `client-focus-in` / `-out`  | the terminal emulator gains/loses focus          |
| `window-pane-changed`       | the active pane in a window changes              |
| `window-resized`            | a window's dimensions change                     |
| `alert-bell` / `-activity` / `-silence` | per-window monitor alerts            |

Inspect available hooks: `tmux show-hooks -g`.

### Hook patterns

```bash
# Run a script after each new window
tmux set-hook -g after-new-window 'run-shell "$HOME/.config/tmux/scripts/on-new-window.sh"'

# Multiple commands per hook — use \; separator
tmux set-hook -g session-window-changed \
  'display-message "switched window" \; run-shell "$HOME/.config/tmux/scripts/refresh_status.sh"'

# Conditional hook with if-shell -F
tmux set-hook -g after-new-window \
  'if-shell -F "#{==:#{window_name},logs}" "split-window -v" ""'
```

### Removing hooks

```bash
tmux set-hook -gu <event>   # unset
tmux show-hooks -g          # list all
```

## Option Watching (Dynamic Plugin Behavior)

tmux does NOT have a native "fire on option change" event. Plugins that react to user-variable changes use one of these patterns:

### Pattern 1: Format-string re-evaluation

Status-bar format strings re-evaluate on every redraw (status-interval, default 15s). A `@user_var` referenced in `status-right` updates automatically:

```tmux
set -g status-right '#{?#{==:#{@theme},dark},🌑,☀️}'
```

Change `@theme` and the status bar updates on the next redraw. `tmux refresh-client -S` forces immediate redraw.

### Pattern 2: Wrapper command that sets var + triggers redraw

```bash
# In your plugin's toggle script
new_value=$([ "$(tmux show-options -gv @theme)" = "dark" ] && echo "light" || echo "dark")
tmux set-option -gp @theme "$new_value"
tmux refresh-client -S            # force status redraw
```

### Pattern 3: Hook on `session-window-changed` for window-scoped refresh

Some plugins re-read state when the user switches windows — a heuristic for "the user is paying attention right now":

```bash
tmux set-hook -g session-window-changed 'run-shell "$HOME/.config/tmux/plugins/my-plugin/scripts/refresh.sh"'
```

### Anti-pattern: polling loops

Do NOT use `while sleep 1; do tmux show-options ...; done` background scripts. They consume CPU, fight with TPM lifecycle, and miss the actual events. Use hooks or rely on status redraw.

## Testing Plugin Behavior

### The three task types (from issue #41 retrospective)

| Task type   | What it means                                          | First action                                      | Anti-pattern                                            |
| ----------- | ------------------------------------------------------ | ------------------------------------------------- | ------------------------------------------------------- |
| **Verify**  | The plugin should already do X. Confirm X happens.     | Trigger the input; observe; check format vars      | Editing `tmux.conf` to "fix" what's already correct     |
| **Configure** | The user wants new behavior. Set it up.              | Edit config, source-file or reload, verify         | Skipping reload, then debugging stale state             |
| **Debug**   | Behavior is broken. Find why.                          | Hypothesis → action → expected → observed          | Adding more config without isolating the failing piece  |

### Hypothesis-Driven Debug Template

```
HYPOTHESIS:  setting @dark_appearance to 1 should cause the status bar
             background to redraw using the dark theme color
ACTION:      tmux set-option -gp @dark_appearance 1
             tmux refresh-client -S
EXPECTED:    tmux show-options -gv @dark_appearance        → "1"
             tmux display-message -p '#{@dark_appearance}' → "1"
             tmux display-message -p '#{?#{==:#{@dark_appearance},1},dark,light}' → "dark"
             status bar redraws with dark background      (visual)
OBSERVED:    [run and record]
GAP:         [if OBSERVED ≠ EXPECTED, name the gap and stop]
```

Rules:
- State each hypothesis BEFORE running the action
- Run ONE action per cycle, then check
- If OBSERVED diverges from EXPECTED, surface the gap before continuing
- Maximum 3 cycles before pausing to reconsider the model

### Verifying a Hook Fires

Add a debug hook temporarily:

```bash
tmux set-hook -g <event> 'display-message "fired: <event> at #{T:%H:%M:%S}"'
```

Trigger the event; the message appears in the status line. Remove with:

```bash
tmux set-hook -gu <event>
# (then re-source your real hook from tmux.conf if needed)
```

### Verifying a Format String Result

```bash
tmux display-message -p '#{your_format_expression}'
```

If unevaluated `#{...}` appears literally in the output, the variable name is wrong.

### Verifying an Option Value

```bash
tmux show-options -gv @your_option       # global default
tmux show-options -pv @your_option       # as resolved for current pane
tmux show-options -A | rg @your_option   # all scopes + provenance
```

## Live Binding vs Bootstrap

A plugin's `<name>.tmux` script runs ONCE at tmux start. Editing the script does NOT update the live session — the bindings/hooks already registered persist with their old definitions.

To apply a fix to the running session:

```bash
# Source just the corrected binding (no full tmux.conf reload needed)
conf="/tmp/my_bind.conf"
cat > "$conf" <<'EOF'
bind-key -T root MouseDown1Status if-shell -F "#{==:#{mouse_status_range},myplugin}" "run-shell 'bash /path/to/action.sh'" "switch-client -t ="
EOF
tmux source-file "$conf"
```

Or reload the full config:

```bash
tmux source-file ~/.config/tmux/tmux.conf
```

The persisted edit takes effect on next tmux start regardless.

## Plugin Development Checklist

- [ ] Entry script at `<name>.tmux` in repo root
- [ ] User-configurable options use `@plugin-name-setting` convention
- [ ] Options have sensible defaults set inside the entry script
- [ ] Hooks registered with `set-hook -g` (not session-scoped unless intentional)
- [ ] Action scripts live under `scripts/` and are executable
- [ ] No background polling loops
- [ ] Cleanup path documented in README (how to unset hooks/bindings)
- [ ] Tested via hypothesis-driven cycles, not by editing-until-it-works
