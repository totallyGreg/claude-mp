# TUI Tools — Theming, Keybindings, Quirks

Per-tool reference for the most-used TUI applications: fzf, television (tv), gum, btop, lazygit, k9s, glow, charm. Covers theme model, keybinding overrides, debugging tips, and the most common gotchas for each.

For the underlying ANSI color protocol and palette setup, see `terminal-emulation/references/ansi_colors.md`.

---

## fzf

Fuzzy finder; the most-used TUI primitive. Theme inherits from the terminal's 16 ANSI colors by default — set a base16 theme system-wide and fzf follows.

### Config

`fzf` is configured via environment variables and command-line flags (no config file):

```bash
# ~/.zshrc
export FZF_DEFAULT_OPTS='
  --height 60%
  --layout=reverse
  --border=rounded
  --preview-window=right:60%:wrap
  --color=fg:#cdd6f4,bg:-1,hl:#f38ba8
  --color=fg+:#cdd6f4,bg+:#313244,hl+:#f38ba8
  --color=border:#585b70,header:#f9e2af,gutter:-1
  --bind ctrl-y:execute-silent(echo {} | pbcopy)
  --bind ctrl-o:execute(open {})
  --bind ?:toggle-preview
  --bind ctrl-/:change-preview-window(down|hidden|)
'

export FZF_DEFAULT_COMMAND='fd --type f --hidden --exclude .git'
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
```

### Custom keybindings inside fzf

```
--bind <key>:<action>[+<action>...]
```

Common keys: `ctrl-y`, `ctrl-o`, `ctrl-r`, `alt-p`, `?`, `tab`
Common actions: `execute(cmd)`, `execute-silent(cmd)`, `toggle-preview`, `change-preview-window(...)`, `become(cmd)` (replaces fzf)

### Quirks

- **`{}` placeholder** expands to the selected item; quote with `{q}` for query string
- **`become(cmd)`** is fzf's clean exit — replaces the fzf process with the target command (no shell wrapper needed)
- **Preview not updating?** Add `--preview-window=follow` if previewing log files
- **Multi-select** with `-m` (multi); `{+}` expands to all selected items

For fzf as **composition glue in shell pipelines** (`source | fzf --preview | action`), see `environment-composition/references/fzf_composition.md`.

---

## television (tv)

Rust-based cross-shell, cross-platform fuzzy picker (alvarofpp/television). Faster than fzf for large datasets, with first-class "channels" — pluggable data sources (files, env vars, git log, custom commands, even MCP-style integrations).

### Config

`~/.config/television/config.toml`:

```toml
[ui]
use_nerd_font_icons = true
ui_scale = 100
show_help_bar = false

[ui.preview_panel]
size = 60
header = " {} "
scrollbar = true

[keybindings]
quit = ["esc", "ctrl-c"]
select_next_entry = ["down", "tab"]
select_prev_entry = ["up", "backtab"]
toggle_preview = "ctrl-o"
toggle_help = "ctrl-h"

[shell_integration.commands]
"git checkout" = "git-branch"
"cd" = "dirs"
```

### Channels (the "what to fuzzy over" model)

```bash
tv                          # default channel (usually files)
tv git-log                  # commits
tv git-branch               # branches
tv env                      # environment variables
tv alias                    # shell aliases
tv files                    # explicit files channel
tv dirs                     # directories
tv text                     # full-text search across files

# Channel reference
tv --list-channels
```

Define a custom channel in `~/.config/television/cable/`:

```toml
# ~/.config/television/cable/my-channel.toml
[metadata]
name = "k8s-pods"
description = "Kubernetes pods across all namespaces"
requirements = ["kubectl"]

[source]
command = "kubectl get pods -A --no-headers"

[preview]
command = "kubectl describe pod {1} -n {0}"
delimiter = "\\s+"

[ui]
preview_panel = { size = 60 }
```

Then: `tv k8s-pods`.

### Useful keybindings (defaults)

| Key            | Action                            |
| -------------- | --------------------------------- |
| `Enter`        | Select and run                    |
| `Tab` / `↓`    | Next entry                        |
| `Shift-Tab` / `↑` | Previous entry                 |
| `Ctrl-O`       | Toggle preview                    |
| `Ctrl-Y`       | Yank current selection            |
| `Ctrl-S`       | Toggle source/remote channel      |
| `?` / `Ctrl-H` | Toggle help                       |
| `Esc` / `Ctrl-C` | Quit                            |

### Shell integration

```bash
# zsh — enable history substitution + key bindings
eval "$(tv init zsh)"
# Then Ctrl-R uses tv instead of fzf for history search.
```

### sesh ↔ television

sesh's picker can drop fzf for tv. In `~/.config/sesh/sesh.toml`:
```toml
[default_session]
startup_command = "..."
```
Wrap sesh in a tv-backed selector by replacing `fzf-tmux` with `tv` in your sesh keybind script (see `environment-composition/references/sesh_config_guide.md` for the keybind pattern).

### tv vs fzf decision

| Use tv when                                              | Use fzf when                                          |
| -------------------------------------------------------- | ----------------------------------------------------- |
| You have a repeatable data source (custom channel)       | One-off shell pipeline (`source \| fzf \| action`)    |
| Dataset is huge (tens of thousands of entries) — tv is faster | You want maximum compatibility / scripts depend on fzf |
| You want pluggable channels users can install            | You're composing a quick interactive selector inline  |
| You want config-driven UI tweaks (themes via toml)       | You want env-var-driven config (`FZF_DEFAULT_OPTS`)   |

### Quirks

- **Channels are first-class** — define one for any recurring picker you build instead of re-writing the same fzf pipeline
- **`tv --working-directory <dir>`** scopes channels to a specific dir without `cd`
- **Theme files** go in `~/.config/television/themes/` (TOML); reference by name in `config.toml` → `[ui] theme = "catppuccin"`
- **Nerd Font icons require** `use_nerd_font_icons = true` AND a Nerd Font in your terminal

---

## gum

Charmbracelet's interactive shell-script primitives — prompts, confirms, choosers, spinners. Inherits ANSI palette by default; override per-command.

### Common commands

```bash
# Prompt
name=$(gum input --placeholder "Your name")

# Confirm
gum confirm "Deploy?" && deploy.sh

# Choose from list
env=$(gum choose "dev" "staging" "prod")

# Multi-select
features=$(gum choose --no-limit "feature-a" "feature-b" "feature-c")

# Spinner around a command
gum spin --spinner dot --title "Building..." -- make build

# Styled output
gum style --foreground 212 --bold "Done!"
```

### Theming per-command

```bash
gum input --prompt.foreground 212 --cursor.foreground 99 --placeholder "..."
gum choose --cursor.foreground 99 --item.foreground 245
```

### Theming via env vars (apply to all `gum` calls)

```bash
export GUM_CHOOSE_CURSOR_FOREGROUND="99"
export GUM_INPUT_PROMPT_FOREGROUND="212"
```

Full list: `gum <command> --help` shows every theme flag, each with a matching `GUM_<COMMAND>_<FLAG>` env var.

### Quirks

- **Exit code = selection.** `gum confirm` returns 0 for yes, 1 for no. `gum choose` exits non-zero on Ctrl-C.
- **Pipe-in support:** `cat list.txt | gum choose` instead of passing args.

---

## btop

Resource monitor with full TUI theming. Config and themes in `~/.config/btop/`.

### Theme selection

```bash
btop                     # press 'M' for menu → Options → Theme
# Or non-interactive:
sed -i '' 's/^color_theme = .*/color_theme = "kyli0x"/' ~/.config/btop/btop.conf
```

Themes are `.theme` files in `~/.config/btop/themes/` (custom) or `/usr/local/share/btop/themes/` (system).

### Useful keybindings

| Key | Action                              |
| --- | ----------------------------------- |
| `q` | Quit                                |
| `m` | Toggle menu                         |
| `+` / `-` | Adjust update interval        |
| `f` | Filter processes                    |
| `t` | Tree view of processes              |
| `e` | Toggle process structure (tree/flat) |
| `k` | Kill selected process               |
| `1`–`4` | Toggle boxes (CPU/MEM/NET/PROC) |

### Quirks

- **GPU monitoring** requires building with GPU support (`make GPU_SUPPORT=true`)
- **Truecolor recommended** — 256-color falls back to approximations of the gradients

---

## lazygit

Git TUI; config in `~/.config/lazygit/config.yml`. Theme uses named ANSI colors (inherits terminal palette).

### Theme config

```yaml
gui:
  theme:
    activeBorderColor:
      - green
      - bold
    inactiveBorderColor:
      - white
    optionsTextColor:
      - blue
    selectedLineBgColor:
      - reverse
    selectedRangeBgColor:
      - blue
    cherryPickedCommitBgColor:
      - cyan
    cherryPickedCommitFgColor:
      - blue
    unstagedChangesColor:
      - red
```

Colors: `default | black | red | green | yellow | blue | magenta | cyan | white` + modifiers `bold | reverse | underline`. For truecolor: hex strings like `'#ff8800'`.

### Custom commands

```yaml
customCommands:
  - key: 'C'
    command: 'git commit -m "{{.Form.Message}}"'
    context: 'global'
    prompts:
      - type: 'input'
        title: 'Message'
        key: 'Message'
  - key: '<c-r>'
    command: 'gh pr create --fill'
    context: 'global'
    output: 'terminal'
```

### Quirks

- **Per-repo overrides** at `<repo>/.git/lazygit-config.yml`
- **Help screen**: press `?` in any panel to see context-specific keybindings
- **Diff context lines**: `git.diffContextSize: 6` in config

---

## k9s

Kubernetes TUI; config in `~/.config/k9s/`. Skins are YAML files.

### Skin selection

```yaml
# ~/.config/k9s/config.yml
k9s:
  ui:
    skin: monokai           # references monokai.yml in skins/
```

```bash
ls ~/.config/k9s/skins/     # built-in + custom skins
```

### Custom skin example

```yaml
# ~/.config/k9s/skins/my-skin.yml
k9s:
  body:
    fgColor: '#cdd6f4'
    bgColor: '#1e1e2e'
    logoColor: '#f38ba8'
  prompt:
    fgColor: '#cdd6f4'
    bgColor: '#1e1e2e'
  frame:
    border:
      fgColor: '#585b70'
      focusColor: '#f9e2af'
    menu:
      fgColor: '#cdd6f4'
      keyColor: '#f9e2af'
      numKeyColor: '#a6e3a1'
    title:
      fgColor: '#cdd6f4'
      bgColor: '#1e1e2e'
```

### Hotkeys

```yaml
# ~/.config/k9s/hotkeys.yml
hotKey:
  shift-0:
    shortCut: Shift-0
    description: View all pods
    command: pods
  shift-1:
    shortCut: Shift-1
    description: View deployments
    command: deployments
```

### Quirks

- **Skin files require restart** of k9s to take effect
- **Context refresh interval**: `refreshRate: 2` in config.yml (seconds)
- **Useful built-in shortcut**: `:` to switch resource type (`:po`, `:deploy`, `:svc`, etc.)
- **Read-only mode** for safety: `k9s --readonly` or `readOnly: true` in config

---

## glow

Markdown reader with built-in themes.

```bash
glow README.md              # opens in pager
glow -p README.md           # paged
glow -s dark README.md      # dark theme (default)
glow -s light README.md
glow -s notty README.md     # no terminal styling (for redirect)
glow -s ~/.config/glow/custom.json README.md   # custom style
```

Custom styles are JSON; clone from the built-in `dark` style as a starting point:
```bash
glow -s dark --show-style > ~/.config/glow/custom.json
```

---

## charm / bubbletea apps

Many newer TUI apps (gum, glow, vhs, sm, soft-serve) are built on Charmbracelet's Bubble Tea framework. They share characteristics:

- **Inherit terminal colors** by default; truecolor support is universal
- **`--help` is consistent** — every command lists every flag with theming support
- **`NO_COLOR=1`** disables all colorization (POSIX convention; charm tools respect it)
- **`CLICOLOR_FORCE=1`** forces colors even when piping output

To detect TUI app issues:
```bash
NO_COLOR=1 gum input    # if works → color issue
echo $TERM              # must be xterm-256color or better
echo $COLORTERM         # truecolor for full color
```

---

## Debugging TUI Apps

1. **Substrate first.** Confirm the substrate works: `tput colors`, `echo $TERM`, `echo $COLORTERM`. Run the truecolor gradient test (see `terminal-emulation/references/ansi_colors.md`).
2. **Tmux passthrough.** If inside tmux, confirm `tmux.conf` has `set -as terminal-features ",xterm-256color:RGB"`.
3. **Font glyphs.** If icons/box drawing is broken (not colors), it's a font issue → use a Nerd Font.
4. **App-specific debug.** Most tools support `--log-level=debug` or write to `~/.cache/<app>/log`.
5. **Strip colors test.** `NO_COLOR=1 <app>` — if the app works without colors, the issue is theming, not rendering.

## Common Issues

### "fzf preview window is blank"

- Preview command is failing silently → run it directly with the placeholder substituted
- Add `--preview-window=wrap` for long lines
- For binary files: `--preview 'file {}; head -c 1000 {}'`

### "lazygit colors look wrong inside tmux"

Almost always a tmux truecolor passthrough issue. Confirm:
```bash
echo $TERM           # should be tmux-256color inside tmux
echo $COLORTERM      # should be truecolor
```
Fix in `~/.config/tmux/tmux.conf`:
```tmux
set -g default-terminal "tmux-256color"
set -as terminal-features ",xterm-256color:RGB"
```

### "k9s skin not applying"

- Restart k9s (skins load at startup only)
- Confirm `skin:` value in `config.yml` matches the filename in `skins/` (without `.yml`)
- Check for YAML syntax errors: `yq . ~/.config/k9s/skins/my-skin.yml`

### "TUI app shows mojibake / boxes-as-letters"

This is Unicode / ACS rendering, not theming. Route to `terminal-emulation/references/unicode_troubleshooting.md`.
