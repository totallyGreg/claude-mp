# Tmux Mouse Bindings and Named Status Bar Ranges

Reference for implementing per-segment mouse click actions in the tmux status bar, covering named ranges, the correct mouse events, and diagnostic techniques.

---

## Named Range Attributes

Wrap any portion of status-right output with `#[range=user|<name>]..#[norange default]` to create a named clickable region:

```
#[range=user|appearance]🌗#[norange default]
```

- The range tag is processed by tmux even when it appears inside `#(command)` output.
- The name becomes accessible via `#{mouse_status_range}` when the user clicks that region.
- Multiple disjoint regions can coexist in the same status bar.

---

## Correct Mouse Event

| Region | Event |
|--------|-------|
| Status bar (windows + user ranges) | `MouseDown1Status` |
| Status-right background (no range) | `MouseDown1StatusRight` |
| Status-left background (no range) | `MouseDown1StatusLeft` |

**User-named ranges (`range=user|*`) fire `MouseDown1Status`, NOT `MouseDown1StatusRight`.**

This is the most common mistake when implementing per-plugin click actions.

---

## `#{mouse_status_range}` Return Value

`#{mouse_status_range}` returns **only the bare name**, not the `user|` prefix.

```
#[range=user|appearance]  →  #{mouse_status_range} == "appearance"
                          ✗  #{mouse_status_range} == "user|appearance"
```

Use this in `if-shell -F` conditions:

```
if-shell -F "#{==:#{mouse_status_range},appearance}" ...
```

---

## Correct Fallthrough for Window Selection

When binding `MouseDown1Status`, always provide a fallthrough command so clicking on windows still works:

```
tmux bind-key -T root MouseDown1Status \
  if-shell -F "#{==:#{mouse_status_range},appearance}" \
  "run-shell 'bash /path/to/toggle.sh'" \
  "switch-client -t ="
```

| Fallthrough | Effect |
|-------------|--------|
| `switch-client -t =` | Preserves window selection (correct) |
| `send-keys -M` | Passes click to the pane, does NOT select windows |
| _(omitted)_ | Click on windows silently ignored |

---

## Binding Syntax from Shell

The quoting required to pass `if-shell` from bash to tmux is error-prone. The most reliable approach is a temp conf file:

```bash
helper="/path/to/toggle.sh"
conf="/tmp/my_bind.conf"
cat > "$conf" <<EOF
bind-key -T root MouseDown1Status if-shell -F "#{==:#{mouse_status_range},appearance}" "run-shell 'bash ${helper}'" "switch-client -t ="
EOF
tmux source-file "$conf"
```

Passing `if-shell` as a positional argument to `tmux bind-key` from bash often fails with "too many arguments" due to shell word splitting on the quoted tokens.

---

## Diagnostic Technique

When a mouse binding is not firing, bind all three status events to `display-message` to identify which one fires and what `#{mouse_status_range}` contains:

```bash
tmux bind-key -T root MouseDown1Status      display-message "Status      x:#{mouse_x} range:[#{mouse_status_range}]"
tmux bind-key -T root MouseDown1StatusLeft  display-message "StatusLeft  x:#{mouse_x} range:[#{mouse_status_range}]"
tmux bind-key -T root MouseDown1StatusRight display-message "StatusRight x:#{mouse_x} range:[#{mouse_status_range}]"
```

Click the target area and read the message to discover:
- Which event fires (tells you which event to bind)
- The range name (tells you the exact string to compare against)

Clean up afterwards:

```bash
tmux unbind-key -T root MouseDown1Status
tmux unbind-key -T root MouseDown1StatusLeft
tmux unbind-key -T root MouseDown1StatusRight
```

---

## Live Binding vs Bootstrap

In plugin frameworks (e.g., tmux-powerkit), keybinding setup functions only run during plugin initialization (bootstrap). After fixing a binding in source code, the live session still holds the old binding.

Apply the corrected binding manually to the running session:

```bash
# Write corrected binding to temp file and source it
conf="/tmp/my_bind.conf"
cat > "$conf" <<'EOF'
bind-key -T root MouseDown1Status if-shell -F "#{==:#{mouse_status_range},myplugin}" "run-shell 'bash /path/to/action.sh'" "switch-client -t ="
EOF
tmux source-file "$conf"
```

The persisted fix will take effect on next tmux reload (`tmux source ~/.config/tmux/tmux.conf`).

---

## Complete Working Example

```bash
# In plugin setup (e.g., plugin_setup_keybindings() in a powerkit plugin):
helper="${POWERKIT_ROOT}/src/helpers/my_toggle.sh"

# Keyboard shortcut (optional)
tmux bind-key C-a run-shell "bash '${helper}'"

# Mouse click on this plugin's segment only
# (segment_builder wraps output with #[range=user|myplugin]..#[norange default])
tmux bind-key -T root MouseDown1Status \
  if-shell -F "#{==:#{mouse_status_range},myplugin}" \
  "run-shell 'bash ${helper}'" \
  "switch-client -t ="
```

```bash
# In status bar renderer (e.g., segment_builder.sh):
# Wrap each plugin segment with its named range so clicks can be targeted.
output+="#[range=user|${plugin_name}]${segment}#[norange default]"
```
