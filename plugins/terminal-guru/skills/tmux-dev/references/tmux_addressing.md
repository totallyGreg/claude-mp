# Tmux Addressing — Unique IDs for Sessions, Windows, Panes

Reference for tmux's permanent ID system. Every session, window, and pane has a unique ID assigned at creation that survives all renames, moves, and re-arrangements until `tmux kill-server`.

---

## The Three ID Spaces

| Entity  | Prefix | Example | Notes                                          |
| ------- | ------ | ------- | ---------------------------------------------- |
| Session | `$`    | `$0`    | Created by `new-session`. Counter starts at 0. |
| Window  | `@`    | `@5`    | Created by `new-window` or `new-session`.      |
| Pane    | `%`    | `%12`   | Created by `new-window`, `split-window`, or `new-session`. |

Counters are **per server, monotonically increasing, and never reused**. If you create and kill 10 panes, the 11th will be `%11` (or higher), not `%0` again.

## Listing

```bash
# All sessions
tmux list-sessions -F '#{session_id} #{session_name} (#{session_windows} windows)'

# All windows across all sessions
tmux list-windows -a -F '#{session_id}:#{window_id} #{window_name}'

# All panes across all sessions
tmux list-panes -a -F '#{session_id}:#{window_id}.#{pane_id} #{pane_current_command} [#{pane_title}]'
```

The `-a` flag widens scope to "all sessions on the server" — without it, listing is scoped to the current session/window.

## Discovering "What Am I In?"

From inside a pane:

```bash
tmux display-message -p '#{session_id} #{window_id} #{pane_id}'
# → $1 @3 %7
```

This is the foundational query — most automation starts here.

Common variants:

```bash
# Just the pane ID
tmux display-message -p '#{pane_id}'

# Full triple with names
tmux display-message -p 'session=#{session_name}($S{session_id}) window=#{window_name}(#{window_id}) pane=#{pane_id}'

# Current pane's working directory
tmux display-message -p '#{pane_current_path}'
```

## Targeting with `-t`

Every tmux command that operates on a session/window/pane accepts `-t target`. The target can be:

| Form              | Resolves to                                          |
| ----------------- | ---------------------------------------------------- |
| `%12`             | Pane with that exact ID (anywhere on the server)     |
| `@5`              | Window with that exact ID                            |
| `$1`              | Session with that exact ID                           |
| `session_name`    | Session by name                                      |
| `session:window`  | Window by name within session                        |
| `session:window.pane_index` | Pane by index within window               |
| `:.+`             | Next pane in current window                          |
| `=`               | Currently-attached client / current pane             |

**Prefer ID targets (`%12`) over index targets (`:0.1`) for automation.** Indices renumber on `renumber-windows` or pane close; IDs do not.

### Examples

```bash
# Send keystrokes to pane %12 wherever it lives now
tmux send-keys -t %12 'make build' Enter

# Switch to session $1 even if its name changed
tmux switch-client -t \$1

# Kill window @5 across all sessions
tmux kill-window -t @5

# Capture content of pane %12 to stdout
tmux capture-pane -t %12 -p
```

## Persistence Semantics

| Operation                                | IDs preserved?                          |
| ---------------------------------------- | --------------------------------------- |
| `rename-session`, `rename-window`        | Yes — name changes, ID stays            |
| `move-window`, `move-pane`               | Yes — IDs follow the entity             |
| `break-pane` (pane → new window)         | Pane ID preserved; new window gets a new `@N` |
| `join-pane`                              | Pane ID preserved                       |
| `swap-window`, `swap-pane`               | All IDs preserved                       |
| `kill-pane`, `kill-window`, `kill-session` | ID is gone forever (not reused)       |
| Detach / re-attach                       | All IDs preserved                       |
| `tmux kill-server`                       | All IDs reset; counters return to 0 on next start |

**The ID is the only stable handle.** Names can collide and be renamed. Indices renumber. Window positions shift. Only the `$`/`@`/`%` ID survives every operation short of a server restart.

## Finding "The Thing I Just Created"

When automation creates a session/window/pane, capture its ID immediately:

```bash
# Create a session and capture its ID
session_id=$(tmux new-session -d -s 'work' -P -F '#{session_id}')
echo "$session_id"   # → $3

# Create a window and capture its ID
window_id=$(tmux new-window -t "$session_id" -P -F '#{window_id}')

# Split a pane and capture the new pane's ID
new_pane=$(tmux split-window -t "$window_id" -P -F '#{pane_id}')
```

The `-P` flag tells the command to print, and `-F` controls the format. Without `-P -F`, the command runs but you have no handle to the result.

## Listing Recipes

```bash
# Find which pane is running a dev server (any node/cargo/rails)
tmux list-panes -a -F '#{pane_id} #{pane_current_command}' \
  | rg 'node|cargo|rails|bun|npm'

# Find panes whose current working dir matches a project
tmux list-panes -a -F '#{pane_id} #{pane_current_path}' \
  | rg "$PWD"

# Count panes per session
tmux list-sessions -F '#{session_id} #{session_name} #{session_windows} windows'

# Find windows with no active client
tmux list-windows -a -F '#{window_id} #{window_name} active:#{window_active}'
```

## Common Pitfalls

1. **Quoting `$N` in shell.** `$1` is a shell positional parameter. Always quote literal session IDs in shell scripts: `tmux switch-client -t '\$1'` or escape with `\$1`.
2. **Assuming low IDs.** After a long session, IDs may be in the hundreds. Never hardcode `%0` — always discover.
3. **Reusing IDs across server restarts.** A script that saves `%12` to disk and runs after `tmux kill-server` will target the wrong pane. Store names + paths as fallback, IDs as preferred.
4. **`-t :` ambiguity.** Without an explicit target, commands operate on the current pane *of the attached client*. Always specify `-t` in automation.
