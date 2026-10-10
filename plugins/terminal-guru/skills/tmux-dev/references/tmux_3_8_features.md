# tmux 3.7 / 3.8 Features

What changed in tmux 3.7 and 3.8 that affects automation, plugins, and scripting. Source: upstream `CHANGES` (tag `3.8`) and the 3.8 man page. Recipes marked **verified** were run against tmux 3.8 on an isolated server (`tmux -L <name> -f /dev/null`).

**Always check the version first** — none of this exists before 3.7, most of it needs 3.8:

```bash
tmux -V    # → tmux 3.8
```

When a user's config or script must also run on older tmux, gate on version: `if-shell -F '#{>=:#{version},3.8}' '...' '...'`.

---

## Events, Monitor Hooks, and `wait-for -E` (3.8)

Hooks are now internal **events** that carry a key/value payload. This is the biggest change for automation — it replaces most `capture-pane` polling loops.

### Wait for any hook/event from a script

```bash
tmux wait-for -E pane-command-finished          # block until the event fires
tmux wait-for -E -v pane-command-finished       # also print the payload keys
tmux wait-for -E -F '#{==:#{hook_pane},%3}' pane-command-finished   # return only when the format is true
```

### User events

```bash
tmux wait-for -E @deploy-done &     # waiter
tmux set-hook -E @deploy-done       # fire it (name must start with @)
```

Unlike `wait-for -S <channel>`, this goes through the hook system, so `set-hook -g @deploy-done '...'` handlers also run.

### Monitor hooks — native "fire when a format changes" (verified)

`set-hook -B name:what:format` re-evaluates `format` once a second and fires hook `name` when its value changes. With `-T`, it fires only when the format becomes true. `name` must start with `@`. `what` is empty (attached session), a pane (`%3`), `%*` (all panes), a window (`@1`), or `@*` (all windows).

```bash
# Fire when pane %3's title changes
tmux set-hook -g -B '@titlechg:%3:#{pane_title}' 'display-message "title → #{pane_title}"'

# Fire once a window has more than one pane
tmux set-hook -g -T -B '@split::#{e|>:#{window_panes},1}' 'set -g @was_split 1'

tmux show-hooks -gB            # list monitors
tmux set-hook -gu -B '@split'  # remove a monitor
```

Payload (from `wait-for -E -v`): `event`, `last` (previous value), `value` (new value), plus `pane`/`window`/`session`. In the hook command these are also available as `#{hook_last}`, `#{hook_monitor_format}`, `#{hook_monitor_target}`.

Gotchas (verified):
- Monitors take a baseline sample about a second after creation. A change in that first second is **not** reported. Tests should wait ~1–2 s after `set-hook -B` before triggering.
- Monitor hooks are **not inherited** — they run only from the scope where they were created.
- No attached client is needed; they work on a detached server.

### OSC 133 shell-integration events (verified)

If the shell emits OSC 133 marks (iTerm2/Ghostty/WezTerm-style shell integration), tmux fires:

| Event                   | OSC 133 mark | Use for                         |
| ----------------------- | ------------ | ------------------------------- |
| `pane-shell-prompt`     | `A`          | "pane is idle at a prompt"      |
| `pane-command-started`  | `C`          | "a command just began"          |
| `pane-command-finished` | `D;<status>` | "command done, with exit code"  |

`pane-command-finished` payload: `command_status`, `command_start_time`, `command_end_time`, `command_duration`, `pane`, `window`, `session`.

**Send a command and wait for it to finish** — the reliable replacement for `send-keys` + `sleep` + `capture-pane`:

```bash
tmux send-keys -t %3 'make test' Enter
tmux wait-for -E -v -F '#{==:#{hook_pane},%3}' pane-command-finished | rg command_status | tail -1
# → command_status=0
```

`-v` prints the payload of **every** matching-name event, including ones the `-F` filter rejects (verified). The waiter only returns on the event that passes the filter, so its payload is the **last** block — hence `tail -1`.

Requires shell integration that emits OSC 133 (`D` must include the exit status). Check with `tmux capture-pane -p -F -t %3` — lines flagged `P` (prompt) / `O` (output) mean marks are arriving.

### New hook names (3.8)

`client-created`, `client-closed`, `pane-activity`, `pane-created`, `pane-moved`, `pane-resized`, `pane-mode-entered`, `pane-mode-exited`, `pane-prompt-opened`, `pane-prompt-closed`, `pane-command-started`, `pane-command-finished`, `pane-shell-prompt`, `session-added-to-group`, `session-removed-from-group`, `window-created`, `window-closed`, `window-zoomed`, `window-unzoomed`, `client-light-theme`, `client-dark-theme`. Full list: `man tmux` → HOOKS.

New hook formats: `#{hook_fire_count}`, `#{hook_fire_time}`, `#{hook_pane}`, `#{hook_session}`, `#{hook_client}`.

## Floating and Modal Panes (3.7, extended in 3.8)

Floating panes sit above the tiled layout. They are real panes (with `%N` IDs, `send-keys`, `capture-pane`), not popups. Default binding: `prefix *`.

```bash
# Create a floating pane, get its ID (verified)
tmux new-pane -d -P -F '#{pane_id}' -T helper -x 60% -y 40% 'htop'

# Modal pane: blocks the other panes until it closes
tmux new-pane -O -D 'fzf ...'   # -D: Escape / C-c closes it
tmux new-pane -O -K ...         # -K: send all keys (even prefix) to it
tmux new-pane -O -C ...         # -C: close on click outside

tmux new-pane -W 'cmd'          # wait for the pane's command to exit
tmux new-pane -A 'cmd'          # stays visible above a zoomed pane
```

- `break-pane` floats a tiled pane, `join-pane` tiles a floating one, `swap-pane`/`move-pane`/`resize-pane` all work on floating panes (3.8).
- Formats: `#{pane_floating_flag}`, `#{pane_modal_flag}`, `#{window_modal_pane}`.
- `choose-tree -h` hides the pane running the mode; `-k` kills the pane when the mode exits (good for pickers in floating panes).
- `command-prompt -P` opens the prompt inside a pane instead of the status line.
- `pane-border-status` gained `top-floating` / `bottom-floating`; `prefix g` holds default move/resize bindings.

When to use: a floating pane for a long-lived helper (log tail, agent output) that should stay addressable by `%N`; `display-popup` for a disposable picker; a modal `new-pane -O` when the picker should also be a real pane.

## Smaller Automation Additions

| Feature | Version | Notes |
| ------- | ------- | ----- |
| `capture-pane -I` | 3.8 | Prefix each line with the epoch time it entered history (verified) |
| `capture-pane -F` | 3.8 | Per-line flags: `P` prompt, `O` output (from OSC 133), `H` hyperlinks |
| `new-window -E`, `respawn-pane -E` | 3.8 | Create an empty pane, instead of passing `''` as the command |
| `remain-on-exit failed-key` | 3.8 | Keep the pane after a failed command until a key is pressed |
| `kill-pane -a -f <fmt>` | 3.8 | Filter which other panes/windows/sessions get killed |
| `switch-mode` | 3.8 | Fuzzy session/window switcher; `prefix Tab` windows, `prefix S-Tab` sessions |
| `run-shell 'cmd' a b` → `#{1}`, `#{2}` | 3.7 | Positional args expanded in the command |
| `{current}` / `{active}` targets | 3.7 | `-t {active}` = active pane |
| `list-* -O` sort, `list-keys -F` | 3.7 | Sorting and custom formats for list commands |
| `show-options -F`, `show-hooks -F` | 3.8 | Format each line |
| `pane_last_output_time`, `pane_output_generation` | 3.8 | Detect "has the pane printed anything since X" without capturing |

New format modifiers (3.8): `O:` loop over options, `V:` loop over environment, `t/d` time difference in seconds, `#{A/count:f1,f2,...}` status-line animation, and `m` now supports fuzzy matching (`m/z`).

## Themes and Styling (3.8)

- New `theme` option: `detect` (default) | `terminal` | `light` | `dark`. Set `terminal` to get the pre-3.8 colours back.
- Theme colour names in styles: `themeblack`, `themewhite`, `themegreen`, … (configured by `dark-theme-*` / `light-theme-*`).
- Hooks `client-light-theme` / `client-dark-theme` fire when the terminal changes appearance. Plugins that previously polled macOS appearance can use these instead.
- Style attributes: `dim=`, `link=`, `nolink`.

Colours that look wrong *outside* tmux are still terminal-emulation's job.

## Breaking or Surprising Changes

Check these when a config or plugin "broke after upgrading tmux":

| Change | Version | Fix |
| ------ | ------- | --- |
| `mouse` now defaults to **on** | 3.8 | `set -g mouse off` to restore |
| Default colours follow the detected light/dark theme | 3.8 | `set -g theme terminal` |
| `display-panes` is now a mode; `-b` removed | 3.8 | Drop `-b` from bindings |
| Copy mode `refresh-from-pane` removed | 3.8 | Use `refresh-now` (bound to `r`) or `refresh-on` / `refresh-toggle` |
| Layout strings are a JSON subset | 3.8 | Old format still accepted as input; control-mode clients get old layouts unless they set `new-layouts` |
| Command templates: `%%` is now escaped for single quotes, `%1` stays unquoted | 3.8 | Re-check `choose-tree` / `command-prompt` templates that quote `%%` themselves |
| `active-pane` client flag removed | 3.8 | Remove from `attach -f` / `refresh-client -f` |
| `message-style` needs `fill=` to cover the full width | 3.7 | Add `fill=<colour>` |
| Second status line (`status 2`) default shows a pane list | 3.7 | Set `status-format[1]` explicitly |
| `clear-on-attach` server option (default on) | 3.8 | `set -s clear-on-attach off` keeps pre-attach terminal output in scrollback |
