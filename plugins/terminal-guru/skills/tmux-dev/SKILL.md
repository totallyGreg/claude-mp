---
name: tmux-dev
description: This skill should be used when the user asks to "send keys to a tmux pane", "capture a tmux pane", "find my pane id", "address a tmux pane", "configure tmux options", "write a tmux format string", "create a tmux plugin", "add a tmux hook", "test my tmux plugin", "bind a tmux mouse click", or "create a tmux session programmatically". Covers tmux as an automation surface — pane/window/session unique IDs (`%N`/`@N`/`$N`), send-keys/capture-pane/pipe-pane, options and format strings, TPM plugins, hooks, and plugin testing patterns. Do NOT use for tmux display issues (TERM, colors-inside-tmux, Unicode) — use terminal-emulation. Do NOT use for sesh session orchestration — use environment-composition.
metadata:
  version: "1.0.0"
---

# tmux-dev

## Overview

tmux is a multiplexer that runs on top of the terminal substrate (see terminal-emulation for `$TERM`, ANSI, Unicode concerns). This skill covers tmux as an **automation and structural surface**: how to address its entities uniquely, how to move data between panes, how its options and format strings work, and how its plugin/hook system extends behavior.

The skill answers questions like "what's my current pane ID and how do I send a command to a specific pane regardless of where it lives now?" and "why isn't my tmux plugin reacting to an option change?"

## When to Use This Skill

- Need to find, label, or address a pane/window/session uniquely
- Need to send keystrokes or commands to another pane (`send-keys`)
- Need to capture or pipe output from a pane (`capture-pane`, `pipe-pane`)
- Configuring tmux options (server / session / window / pane scopes)
- Writing format strings (`#{...}`, `#{?cond,a,b}`, `#{@user_var}`)
- Writing or debugging a tmux plugin (TPM, hooks, option-watching)
- Testing tmux plugin behavior (verifying dynamic updates, not configuring)
- Programmatically creating sessions, windows, or panes
- Mouse bindings, status-bar click ranges
- tmux session persistence, naming conventions, sesh integration at the tmux level

## Stack Boundary

This skill is the multiplexer layer. It assumes the substrate works.

| Belongs HERE (tmux-dev)                                | Belongs in terminal-emulation                |
| ------------------------------------------------------ | -------------------------------------------- |
| Pane/window/session IDs (`%N`, `@N`, `$N`)             | `$TERM` value, terminfo entry for tmux       |
| `send-keys`, `capture-pane`, `pipe-pane`               | Colors broken inside tmux pane               |
| Options, format strings, hooks, TPM plugins            | Box drawing renders as letters               |
| `tmux new-session`, `choose-tree`, `find-window`       | UTF-8 / locale issues inside tmux            |
| Mouse status-bar bindings                              | Font glyph coverage                          |

When in doubt, the test is: *Does the issue change if I restart tmux but keep the same terminal emulator?* If yes → tmux-dev. If no → terminal-emulation.

## Core Capabilities

### 1. Unique Addressing — `$N` / `@N` / `%N`

tmux assigns a **permanent unique ID** to every session, window, and pane at creation. These IDs survive renames, moves between windows/sessions, and split-window/break-pane operations. They are stable until `tmux kill-server`.

| Entity  | ID format | Example | Listed by                            |
| ------- | --------- | ------- | ------------------------------------ |
| Session | `$N`      | `$0`    | `tmux list-sessions -F '#{session_id} #{session_name}'` |
| Window  | `@N`      | `@5`    | `tmux list-windows -a -F '#{window_id} #{window_name}'` |
| Pane    | `%N`      | `%12`   | `tmux list-panes -a -F '#{pane_id} #{pane_current_command}'` |

**Any tmux command that takes `-t target` accepts these IDs:**

```bash
tmux send-keys -t %12 'git status' Enter   # send to pane %12 wherever it is
tmux select-window -t @5                   # jump to window @5
tmux switch-client -t \$1                  # switch to session $1
```

Detailed reference: `references/tmux_addressing.md` (targeting recipes, persistence rules, listing across the server, finding "the pane I just split off").

### 2. Send / Receive Between Panes

Three primitives for moving data through tmux:

```bash
# Send keystrokes (literal text + key names)
tmux send-keys -t %12 'make build' Enter

# Capture current visible content of a pane (or full scrollback with -p -S -)
tmux capture-pane -t %12 -p

# Stream pane output to a file/command continuously
tmux pipe-pane -o -t %12 'cat >> /tmp/pane-%12.log'

# One-shot status message in a target pane
tmux display-message -t %12 'build done'

# Block until a named event fires (signal coordination)
tmux wait-for build-finished &
# ... build script calls: tmux wait-for -S build-finished
```

Use `send-keys` for *input* (driving a REPL, running commands). Use `capture-pane` for *one-shot reads*. Use `pipe-pane` for *continuous output capture* (logging, agent observation). Use `wait-for` for *synchronization* between panes/scripts.

### 3. Find / Label / Select

```bash
tmux choose-tree -Z                  # interactive session+window+pane picker (full-screen)
tmux find-window 'pattern'           # jump to first window whose name/title matches
tmux display-panes                   # overlay numeric labels on every pane; press number to select
tmux rename-window -t %12 'logs'     # name the window holding pane %12
tmux rename-session -t \$1 'work'    # rename session $1
```

`display-panes` is the fastest "show me what's where" view. `choose-tree -Z` is the navigator. `find-window` is search.

### 4. Options & Format Strings

Four option scopes — `server` (`-s`), `session` (`-g` default), `window` (`-w`), `pane` (`-p`) — with a precedence chain. User variables use the `@` prefix.

```bash
tmux set-option -gp @theme 'dark'                        # session-default user var
tmux show-options -gv @theme                             # → dark
tmux display-message -p '#{?#{==:#{@theme},dark},🌑,☀️}'  # conditional format
```

See `references/tmux_options_and_formats.md` for scopes, precedence, conditional/math format syntax, common variables, and debugging unevaluated `#{}` tokens.

### 5. Plugins & Hooks

TPM plugins live in `~/.config/tmux/plugins/`. Hooks fire on tmux events; plugins use them to react to state:

```bash
tmux set-hook -g after-new-window 'run-shell "$HOME/.config/tmux/scripts/on-new-window.sh"'
```

See `references/tmux_plugins.md` for TPM layout, hook event taxonomy, option-watching patterns (format re-evaluation, refresh-client triggers), and the testing protocol below.

### 6. Testing: Verify vs Configure vs Debug

The most common tmux plugin failure mode (from #41) is misidentifying the task type. Pick one before acting:

- **Verify** — behavior should already work; trigger it and observe (do NOT edit config)
- **Configure** — set up new behavior; edit, source-file, then verify
- **Debug** — behavior is broken; hypothesis-driven cycle (state expected, run one action, compare)

Full task-type table and the hypothesis-driven debug template are in `references/tmux_plugins.md`.

## Diagnostic Process

1. **Identify the entity layer** — is this about a pane, window, session, or the server?
2. **Get the unique ID** — `tmux display-message -p '#{pane_id} #{window_id} #{session_id}'` from the relevant pane
3. **List the landscape** — `tmux list-panes -a -F '#{pane_id} #{window_id} #{session_id} #{pane_current_command}'`
4. **For options/formats** — `tmux show-options -A` (all scopes), `tmux display-message -p '#{var}'` to evaluate a single variable
5. **For plugin debugging** — check hook firing with `set-hook -g <event> 'display-message "fired: <event>"'` temporarily

## Common Use Cases

### "Send `git status` to pane %3"

```bash
tmux send-keys -t %3 'git status' Enter
```

### "Capture the last 50 lines from another pane"

```bash
tmux capture-pane -t %12 -p -S -50
```

### "Find which pane is running my dev server"

```bash
tmux list-panes -a -F '#{pane_id} #{pane_current_command} #{pane_title}' | rg 'node|npm|bun|cargo|rails'
```

### "Open a session picker with sesh"

See `references/tmux_session_management.md` for the full `sesh + fzf` keybinding pattern (`M-backtick`), and the modes table (Ctrl-a all, Ctrl-t tmux, Ctrl-g configs, Ctrl-x zoxide, Ctrl-f find, Ctrl-d kill).

### "Add a per-segment mouse click in the status bar"

See `references/tmux_mouse_bindings.md` for named status ranges (`#[range=user|name]`), the correct event (`MouseDown1Status`, NOT `MouseDown1StatusRight`), and the fallthrough required to keep window-clicking working.

### "Test that my plugin reacts to a user-option change"

Use the hypothesis-driven template in §6. Verify, don't reconfigure.

## Resources

### references/
- **`tmux_addressing.md`** — unique-ID deep dive; targeting recipes; persistence semantics; listing the server
- **`tmux_options_and_formats.md`** — option scopes (server/session/window/pane); user vars (`@`); format string syntax; conditionals; common variables; debugging
- **`tmux_plugins.md`** — TPM layout; hook event taxonomy; option-watching recipe; testing template
- **`tmux_mouse_bindings.md`** — named status ranges, correct mouse events, diagnostic technique, live binding vs bootstrap
- **`tmux_session_management.md`** — sesh integration, naming conventions, direnv environment setup, pane logging, session persistence

## Related Skills

- **terminal-emulation** — for tmux *display* issues (TERM, colors, Unicode inside tmux)
- **environment-composition** — for sesh session orchestration on top of tmux
- **signals-monitoring** — for signal handling inside scripts that tmux spawns (trap, SIGTERM cleanup)
- **zsh-dev** — for zsh functions that wrap tmux commands (e.g., `tmux send-keys` wrappers)
