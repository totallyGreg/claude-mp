# Tmux Options & Format Strings

Reference for tmux's option system (server / session / window / pane scopes, user variables) and format string language (`#{...}`, `#{?cond,a,b}`, `#{@var}`).

---

## Option Scopes

| Scope   | Flag           | Set / Get commands                         | Inherited by                    |
| ------- | -------------- | ------------------------------------------ | ------------------------------- |
| Server  | `-s`           | `set-option -s` / `show-options -s`        | All sessions                    |
| Session | `-g` (global default) or none | `set-option -g` / `show-options -g` | All windows in the session   |
| Window  | `-w`           | `set-window-option -g` or `set -w`         | All panes in the window         |
| Pane    | `-p`           | `set-option -p` / `show-options -p`        | The pane only                   |

Without `-g`, session-scope options apply to the *current* session only (not as a default for future sessions). The common pattern in `tmux.conf` is to use `-g` everywhere so settings are server-wide defaults.

## Precedence

When tmux resolves an option value for a given pane, it walks this chain:

```
pane → window → session → global-session → server-default
```

The first scope with an explicit value wins. This means:

- A pane-scoped override wins over a window default
- A window option overrides a session option for that window
- An option without `-g` set at session level applies only while that session is current

To inspect precedence:

```bash
tmux show-options -A           # all options + scope provenance for current pane
tmux show-options -gv status   # explicit global value
tmux show-options -pv status   # value as resolved for current pane
```

The `-v` flag returns just the value (useful in scripts); without it, you get `name value` pairs.

## User Variables (`@var`)

Variables prefixed with `@` are user-defined. tmux stores them but does not interpret them — your scripts and format strings read them.

```bash
# Set
tmux set-option -gp @theme 'dark'           # session-default
tmux set-option -wp @logging_enabled '1'    # window-scoped
tmux set-option -p  @last_command 'build'   # current pane

# Read
tmux show-options -gv @theme                # → dark
tmux display-message -p '#{@theme}'         # → dark

# Unset (delete the variable)
tmux set-option -gu @theme
```

User variables are the standard plugin communication channel: a plugin reads its config from `@plugin_name_setting` user vars.

## Format Strings

Format strings are tmux's templating mini-language. They appear in:

- `status-left`, `status-right`, `window-status-format`
- `display-message -p '...'` (evaluate and print)
- `if-shell -F '...'` (use format result as the shell condition)
- `command-prompt -p '...'`
- Many other option values that accept dynamic content

### Variable substitution

```
#{variable_name}                # substitute the value
#{@user_variable}               # substitute a user variable
```

### Conditionals

```
#{?condition,true_value,false_value}
```

`condition` evaluates true if non-empty and not `0`. Examples:

```
#{?pane_active,(active),}                          # show "(active)" if pane is active
#{?#{==:#{@theme},dark},🌑,☀️}                      # emoji depending on @theme
#{?client_prefix,⚡,}                              # show ⚡ when prefix is held
```

### Comparison & string operations

```
#{==:string1,string2}                  # equality (true/false)
#{!=:string1,string2}                  # inequality
#{m:pattern,string}                    # glob match
#{C:pattern}                           # regex match against any of the formats
#{s/find/replace/:string}              # substitute (sed-style)
#{=N:string}                           # truncate to N chars
```

### Math (numeric expressions)

```
#{e|+:5,3}             # → 8
#{e|*:#{window_width},2}
#{e|>:#{pane_height},20}    # boolean: is height > 20?
```

### Common variables

| Variable                  | Meaning                                       |
| ------------------------- | --------------------------------------------- |
| `#{pane_id}`              | `%N` of the pane                              |
| `#{pane_index}`           | numeric index within the window               |
| `#{pane_active}`          | 1 if pane is active                           |
| `#{pane_current_command}` | the command currently running in the pane     |
| `#{pane_current_path}`    | the pane's working directory                  |
| `#{pane_pid}`             | foreground process PID                        |
| `#{window_id}`            | `@N` of the window                            |
| `#{window_index}`         | numeric index in the session                  |
| `#{window_name}`          | window name                                   |
| `#{window_active}`        | 1 if window is active in its session          |
| `#{session_id}`           | `$N` of the session                           |
| `#{session_name}`         | session name                                  |
| `#{client_prefix}`        | 1 if prefix key is being held                 |
| `#{mouse_x}` / `#{mouse_y}` | mouse coords in `MouseDown*` bindings      |
| `#{mouse_status_range}`   | name of clicked status range (see tmux_mouse_bindings.md) |

The complete reference is `man tmux` under `FORMATS`.

## Debugging Format Strings

When a format string isn't producing what you expect:

1. **Print the variable directly:**
   ```bash
   tmux display-message -p '#{the_variable_you_doubt}'
   ```

2. **Print with delimiters to see whitespace:**
   ```bash
   tmux display-message -p '[#{the_variable}]'
   ```

3. **If `#{...}` appears literally in output, the variable name is wrong** — tmux leaves unknown formats unevaluated. Check the spelling against `man tmux` FORMATS.

4. **For conditionals that always show the false branch:**
   ```bash
   tmux display-message -p 'cond=[#{condition_var}] eq=[#{==:#{condition_var},expected}]'
   ```

5. **Status-line formats run periodically.** Force a redraw to see changes immediately:
   ```bash
   tmux refresh-client -S
   ```

## Common Patterns

### Show different content based on user variable

```tmux
set -gp @theme 'dark'
set -g status-right '#{?#{==:#{@theme},dark},🌑 dark,☀️ light}'
```

### Truncate long paths in status bar

```tmux
set -g window-status-format '#I:#{=20:pane_current_path}'
```

### Conditional pane border color (active vs inactive)

```tmux
set -g pane-border-style 'fg=colour238'
set -g pane-active-border-style 'fg=colour220'
```

### Read a user variable into a script

```bash
theme=$(tmux show-options -gv @theme)
if [[ "$theme" == "dark" ]]; then
    # ...
fi
```

## Gotchas

- **`#` is the escape character.** To output a literal `#` in a status bar, use `##`.
- **Commas separate conditional branches.** A literal comma in a value needs escaping or building the string in a shell var first.
- **`-g` for "default for new sessions"** vs no flag for "current session only." Easy to get wrong.
- **Setting a window option without `-g` only affects the current window**, not a default for future windows of that session.
- **`set-option -p` requires being inside the target pane** (or using `-t`). The shell pane you're typing into is not necessarily the pane the option attaches to.
