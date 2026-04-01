# Sesh Configuration Guide (v2.24+)

## Overview

Sesh is a tmux session manager that provides smart session creation, switching, and lifecycle management. Its `sesh.toml` config system is the foundation of environment composition -- defining how sessions are created, what startup commands run, and how windows are arranged for each project.

Key capabilities:
- Declarative session definitions with startup commands and multi-window layouts
- Wildcard patterns for directory-based session matching
- Git-aware naming with bare repo and worktree detection
- Integration with tmuxp, tmuxinator, zoxide, and multiple picker UIs
- Config splitting via `import` for work/personal separation

---

## Config System

### Location and Schema

| Item | Value |
|------|-------|
| Default path | `$XDG_CONFIG_HOME/sesh/sesh.toml` (typically `~/.config/sesh/sesh.toml`) |
| Custom path | `sesh -C /path/to/sesh.toml <subcommand>` |
| JSON schema | `https://github.com/joshmedeski/sesh/raw/main/sesh.schema.json` |

### Top-Level Options

```toml
# Enable caching for faster session listing
cache = true

# Strict mode -- fail on unknown config keys
strict_mode = false

# Import additional config files (work/personal split)
import = ["~/.config/sesh/work.toml", "~/.config/sesh/personal.toml"]

# Glob patterns for directories to exclude from listing
blacklist = ["node_modules", ".git", "vendor"]

# Number of directory components in session name (1 = basename, 2 = parent/name)
dir_length = 1

# Treat separators (/, -, _) as word boundaries for fuzzy matching
separator_aware = true

# Custom tmux binary path
tmux_command = "tmux"

# Sort order for session listing: "name", "lastattached"
sort_order = "lastattached"
```

### `[default_session]` -- Defaults for All Sessions

Applied to every session unless overridden by a specific `[[session]]` or `[[wildcard]]` entry:

```toml
[default_session]
startup_command = "nvim"
preview_command = "eza --tree --level=2 {}"
# tmuxp = "default-layout"     # use a tmuxp profile
# tmuxinator = "default"       # use a tmuxinator project

# Default window layout for all sessions
windows = ["editor", "terminal"]
```

The `{}` placeholder is replaced with the session's root path at runtime.

### `[[session]]` -- Named Session Definitions

Explicit session definitions. These take highest priority in connection resolution.

```toml
[[session]]
name = "dotfiles"
path = "~/dotfiles"
startup_command = "nvim"
preview_command = "eza --tree --level=2 {}"

[[session]]
name = "notes"
path = "~/Documents/Notes"
startup_command = "nvim +':Telescope find_files'"
disable_startup_command = false

[[session]]
name = "infra"
path = "~/work/infrastructure"
tmuxp = "infra-layout"          # use a tmuxp profile instead of startup_command
windows = ["editor", "k9s", "logs"]

[[session]]
name = "api-server"
path = "~/work/api"
tmuxinator = "api"              # use a tmuxinator project
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Session name (required) |
| `path` | string | Root directory (required) |
| `startup_command` | string | Command to run on session creation |
| `preview_command` | string | Command for picker preview pane |
| `disable_startup_command` | bool | Skip startup command for this session |
| `tmuxp` | string | tmuxp profile name to use |
| `tmuxinator` | string | tmuxinator project name to use |
| `windows` | list | Window names (referencing `[[window]]` definitions) |

### `[[wildcard]]` -- Pattern-Based Session Matching

Match directories by glob pattern. Explicit `[[session]]` entries always win over wildcards.

```toml
# Match all repos under ~/work/
[[wildcard]]
pattern = "~/work/**"
startup_command = "nvim"
preview_command = "git -C {} log --oneline -10"
windows = ["editor", "terminal"]

# Match nested project directories recursively
[[wildcard]]
pattern = "~/projects/**"
startup_command = "nvim"

# Match Go projects specifically
[[wildcard]]
pattern = "~/go/src/**"
startup_command = "nvim"
windows = ["editor", "terminal", "test-runner"]
disable_startup_command = false
```

| Field | Type | Description |
|-------|------|-------------|
| `pattern` | string | Glob pattern (`/**` for recursive matching) |
| `startup_command` | string | Command to run on session creation |
| `preview_command` | string | Command for picker preview pane |
| `disable_startup_command` | bool | Skip startup command for matched sessions |
| `windows` | list | Window names (referencing `[[window]]` definitions) |

### `[[window]]` -- Reusable Window Definitions

Define windows once, reference by name in `[[session]]` or `[[wildcard]]` entries:

```toml
[[window]]
name = "editor"
startup_script = "nvim"

[[window]]
name = "terminal"
# no startup_script -- opens a plain shell

[[window]]
name = "k9s"
startup_script = "k9s"

[[window]]
name = "logs"
startup_script = "tail -f /var/log/app.log"
path = "/var/log"               # override session path for this window

[[window]]
name = "test-runner"
startup_script = "watchexec -- go test ./..."
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Window name (referenced in session/wildcard `windows` lists) |
| `startup_script` | string | Command to run when window is created |
| `path` | string | Working directory (defaults to session path) |

### Config Splitting with `import`

Split configuration across multiple files for organization:

```toml
# ~/.config/sesh/sesh.toml (main config)
cache = true
sort_order = "lastattached"
import = ["~/.config/sesh/work.toml", "~/.config/sesh/personal.toml"]

[[window]]
name = "editor"
startup_script = "nvim"

[[window]]
name = "terminal"
```

```toml
# ~/.config/sesh/work.toml
[[session]]
name = "api"
path = "~/work/api"
windows = ["editor", "terminal"]

[[wildcard]]
pattern = "~/work/**"
startup_command = "nvim"
```

```toml
# ~/.config/sesh/personal.toml
[[session]]
name = "dotfiles"
path = "~/dotfiles"
startup_command = "nvim"
```

---

## Subcommands

### `connect` (alias: `cn`) -- Connect to a Session

The primary command. Connects to an existing session or creates one based on config.

```bash
# Connect to a session by name or path
sesh connect my-project
sesh cn ~/work/api

# Switch from current tmux session to another
sesh connect --switch my-project

# Override startup command for this connection
sesh connect --command "htop" my-project

# Use a tmuxinator project
sesh connect --tmuxinator api-server

# Specify a root directory
sesh connect --root ~/work/api
```

**Connection resolution order** (first match wins):
1. Existing tmux pane with matching path
2. Existing tmux session by name
3. Tmuxinator project match
4. `[[session]]` config match
5. `[[wildcard]]` config match
6. Directory path match
7. Zoxide query match

### `list` (alias: `l`) -- List Sessions

```bash
# List all sessions (tmux + config + zoxide)
sesh list

# Filter by source
sesh list -t              # tmux sessions only
sesh list -c              # config sessions only
sesh list -z              # zoxide directories only
sesh list -T              # tmuxinator projects only

# Display options
sesh list -i              # show icons
sesh list -H              # hide attached sessions
sesh list -d              # hide duplicates across sources
sesh list -j              # JSON output
sesh list -p              # show panes (not just sessions)

# Combine flags
sesh list -t -c -i -H     # tmux + config, with icons, hide attached
```

### `clone` (alias: `cl`) -- Clone and Connect

One-step git clone + session creation:

```bash
# Clone a repo and immediately create a session for it
sesh clone https://github.com/user/repo.git

# Clone to a specific directory
sesh clone https://github.com/user/repo.git ~/work/repo
```

### `root` (alias: `r`) -- Show Root Path

Print the git repository or worktree root for the current directory:

```bash
sesh root                 # prints repo root path
cd $(sesh root)           # jump to repo root
```

### `preview` (alias: `p`) -- Preview a Session

Run the preview command for a session or directory (used by picker integrations):

```bash
sesh preview my-project
sesh preview ~/work/api
```

### `picker` (alias: `pk`) -- Built-in TUI Picker

Launch the built-in Bubble Tea picker (no external dependency required):

```bash
sesh picker
sesh picker -i            # with icons
sesh picker -s            # separator-aware filtering
```

### `window` (alias: `w`) -- Window Management

List, switch, or create tmux windows:

```bash
sesh window               # list windows in current session
sesh window my-window     # switch to or create a named window
```

### `last` (alias: `L`) -- Switch to Previous Session

```bash
sesh last                 # switch to the last-used tmux session
```

---

## Picker Integrations

Sesh supports four picker options for session selection.

### 1. fzf -- Full-Featured Picker

The canonical integration using a tmux popup with source-switching keybindings:

```bash
# Bind to tmux key (e.g., ctrl-a T)
bind-key "T" display-popup -E -w 40% "sesh connect \"$(
  sesh list -i | fzf-tmux -p 55%,60% \
    --no-sort --ansi --border-label ' sesh ' --prompt '> ' \
    --header '  ^a all ^t tmux ^g config ^x zoxide ^d tmux kill ^f find' \
    --bind 'tab:down,btab:up' \
    --bind 'ctrl-a:change-prompt(> )+reload(sesh list -i)' \
    --bind 'ctrl-t:change-prompt(tmux> )+reload(sesh list -t -i)' \
    --bind 'ctrl-g:change-prompt(config> )+reload(sesh list -c -i)' \
    --bind 'ctrl-x:change-prompt(zoxide> )+reload(sesh list -z -i)' \
    --bind 'ctrl-f:change-prompt(find> )+reload(fd -H -d 2 -t d -E .git . ~)' \
    --bind 'ctrl-d:execute(tmux kill-session -t {})+reload(sesh list -i)' \
    --preview 'sesh preview {}'
)\""
```

### 2. television (tv) -- Simple Integration

Television has a built-in sesh channel:

```bash
# Use tv's sesh channel directly
tv sesh

# Bind to tmux key
bind-key "T" display-popup -E "tv sesh"
```

### 3. gum -- Minimal Picker

```bash
# Basic gum integration
sesh connect "$(sesh list -i | gum filter --limit 1 --fuzzy --no-strip-ansi --placeholder 'Pick a session')"
```

> Note: gum v0.15.0+ requires `--no-strip-ansi` to preserve icon formatting.

### 4. Built-in Picker -- Zero Dependencies

```bash
# Use sesh's built-in Bubble Tea TUI
sesh picker -i

# Bind to tmux key
bind-key "T" display-popup -E "sesh picker -i"
```

---

## Naming Strategy

Sesh uses a git-aware naming strategy when creating sessions from directories.

| Scenario | Name resolution |
|----------|----------------|
| Regular directory | Basename of path (or N components per `dir_length`) |
| Git repository | Repository directory name |
| Git bare repo (`.bare` folder) | Parent directory name |
| Git worktree | Worktree directory name |
| Remote URL clone | Extracted repo name from URL |

### `dir_length` Examples

```toml
# dir_length = 1 (default)
# ~/work/my-api  -->  session name: "my-api"

# dir_length = 2
# ~/work/my-api  -->  session name: "work/my-api"

# dir_length = 3
# ~/projects/work/my-api  -->  session name: "projects/work/my-api"
```

This is useful when you have identically-named directories under different parents (e.g., `~/work/api` vs `~/personal/api`).
