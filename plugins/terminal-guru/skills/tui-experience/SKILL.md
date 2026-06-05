---
name: tui-experience
description: This skill should be used when the user asks to "theme lazygit", "configure k9s skin", "set up fzf preview", "create a television channel", "configure tv channel", "customize btop theme", "configure gum prompt", "style glow markdown", "record a terminal session", "play asciinema cast", "convert asciinema to gif", "convert asciinema to svg", "convert cast to mp4", "render terminal recording with vhs", "share asciinema recording", or needs help with TUI application theming/keybindings/quirks (fzf, television/tv, gum, btop, lazygit, k9s, glow, charm) or terminal session recording (asciinema, agg, vhs, svg-term-cli). Do NOT use for the underlying color protocol (ANSI/256/truecolor) — use terminal-emulation. Do NOT use for tmux automation — use tmux-dev. Do NOT use for shell-level fzf composition pipelines — use environment-composition.
metadata:
  version: "1.0.0"
---

# tui-experience

## Overview

The "experience" layer of the terminal stack: interactive TUI applications running inside panes, and the tools that record what happens in those panes. This skill assumes the substrate works (see terminal-emulation for `$TERM`, ANSI, Unicode) and tmux is configured (see tmux-dev for automation/sessions). It covers what users actually see and do inside the running terminal.

Two domains:
1. **TUI applications** — how to theme, keybind, and debug the tools you live in (fzf, television, gum, btop, lazygit, k9s, glow, charm)
2. **Terminal recording** — capturing terminal sessions with asciinema and converting `.cast` files to GIF/SVG/MP4

## When to Use This Skill

- Theming a TUI app (lazygit theme, k9s skin, btop config, fzf colors)
- Configuring TUI app keybindings (fzf bindings, lazygit custom commands, k9s shortcuts)
- Debugging a TUI app that won't render correctly (after ruling out substrate issues)
- Recording a terminal session with asciinema
- Converting an asciinema `.cast` to GIF (`agg`), SVG (`svg-term-cli`), or MP4 (`asciinema` + `agg` + ffmpeg)
- Generating polished recordings with charmbracelet `vhs` (scripted demos)
- Sharing recordings (asciinema.org upload, embedding `.cast` in markdown)

## Stack Boundary

| Belongs HERE (tui-experience)                    | Belongs elsewhere                                   |
| ------------------------------------------------ | --------------------------------------------------- |
| lazygit theme YAML, k9s skin, btop themes        | ANSI escape codes, `$COLORTERM` → terminal-emulation |
| fzf preview windows, fzf keybindings             | fzf as glue in a shell pipeline → environment-composition |
| `asciinema rec/play/upload`                      | macOS log streaming → signals-monitoring             |
| `agg` / `vhs` / `svg-term-cli` rendering         | tmux session capture (`capture-pane`) → tmux-dev    |

If the question is about *how the terminal renders colors*, route to terminal-emulation. If the question is about *which colors a specific app uses*, this is the right skill.

## Core Capabilities

### 1. TUI App Theming

Most TUI apps follow one of three theme models:

| Model                  | Examples            | Config location                            |
| ---------------------- | ------------------- | ------------------------------------------ |
| YAML / TOML config     | lazygit, k9s        | `~/.config/lazygit/config.yml`, `~/.config/k9s/skins/` |
| Theme command          | btop, glow          | `btop` → `Theme` menu / `glow -s dark`     |
| Inherits terminal palette | fzf (default), gum | Uses your 16 ANSI colors directly          |

The "inherits terminal palette" group respects whatever you've set in your terminal emulator (see terminal-emulation/ansi_colors.md → base16/pywal). Setting a new base16 theme automatically updates fzf and gum.

See `references/tui_tools.md` for per-tool theme paths, keybinding overrides, and the most common debugging quirks.

### 2. TUI App Keybindings

```bash
# fzf — custom keybindings
export FZF_DEFAULT_OPTS='
  --bind ctrl-y:execute-silent(echo {} | pbcopy)
  --bind ctrl-o:execute(open {})
  --bind ?:toggle-preview
'

# lazygit — custom commands (in config.yml)
customCommands:
  - key: 'C'
    command: 'git commit -m "{{.Form.Message}}"'
    context: 'global'
    prompts:
      - type: 'input'
        title: 'Message'
        key: 'Message'

# k9s — hotkeys (~/.config/k9s/hotkeys.yml)
hotKey:
  shift-0:
    shortCut: Shift-0
    description: Show all pods
    command: pods
```

Detailed per-tool keybinding reference in `references/tui_tools.md`.

### 3. Terminal Recording with asciinema

```bash
# Record (Ctrl-D or `exit` to stop)
asciinema rec demo.cast

# Record with a max idle wait (compresses long pauses)
asciinema rec -i 2 demo.cast

# Play
asciinema play demo.cast

# Play faster
asciinema play -s 2 demo.cast

# Upload to asciinema.org (returns a shareable URL)
asciinema upload demo.cast
```

`.cast` files are JSONL — first line is header (terminal size, env), subsequent lines are `[time, "o"|"i", data]` events. They're tiny (KB-scale for minute-long recordings) and editable as plain text.

### 4. Recording → GIF / SVG / MP4

```bash
# .cast → GIF (asciinema/agg — animated GIF renderer)
agg demo.cast demo.gif
agg --theme monokai --font-size 16 --speed 1.5 demo.cast demo.gif

# .cast → SVG (svg-term-cli — scalable, looks great in READMEs)
cat demo.cast | svg-term --window --width 80 --height 24 > demo.svg

# .cast → MP4 (via GIF, then ffmpeg)
agg demo.cast demo.gif && ffmpeg -i demo.gif -movflags +faststart demo.mp4
```

See `references/asciinema.md` for the full conversion matrix, theme options, embedding patterns, and `.cast` editing tips.

### 5. Scripted Demos with vhs

Charmbracelet's `vhs` produces deterministic recordings from a `.tape` script — useful for repeatable docs demos that don't need real-time hands:

```vhs
Output demo.gif
Set FontSize 16
Set Width 800
Set Height 400

Type "ls -la"
Enter
Sleep 1s
Type "git status"
Enter
```

```bash
vhs demo.tape    # produces demo.gif
```

See `references/asciinema.md` for vhs vs asciinema decision guidance.

## Common Use Cases

### "I want lazygit to match my terminal theme"

In `~/.config/lazygit/config.yml`:
```yaml
gui:
  theme:
    activeBorderColor:
      - green
      - bold
    inactiveBorderColor:
      - white
    selectedLineBgColor:
      - reverse
```

Use named colors (red/green/blue/etc.) — lazygit reads from your terminal's 16-color palette, so changing the palette propagates. See `references/tui_tools.md` for full theme keys.

### "Record a 30-second demo for my README"

```bash
asciinema rec -i 2 demo.cast    # `-i 2` skips long idle pauses
# ... perform the demo ...
# Ctrl-D to stop

# Convert to SVG (scales, looks crisp in README)
cat demo.cast | svg-term --window --width 90 > demo.svg

# Embed in README.md
echo '![demo](demo.svg)' >> README.md
```

### "Edit out the typo I made during recording"

`.cast` files are plain JSONL. Open in editor, delete the lines for the typo + correction, save. Re-time later events by adjusting their first-element timestamps if needed.

### "k9s colors look ugly"

The issue is almost always the skin, not the terminal. List skins:
```bash
ls ~/.config/k9s/skins/         # built-ins + custom
```
Set in `~/.config/k9s/config.yml`:
```yaml
k9s:
  ui:
    skin: monokai
```
See `references/tui_tools.md` for skin file format and where to find community skins.

## Resources

### references/
- **`tui_tools.md`** — per-tool theming, keybindings, quirks for fzf, gum, btop, lazygit, k9s, glow, charm/bubbletea apps
- **`asciinema.md`** — recording, playback, upload, conversion matrix (agg/svg-term-cli/vhs), `.cast` editing, embedding patterns, vhs vs asciinema

## Related Skills

- **terminal-emulation** — ANSI/256/truecolor protocol, `$COLORTERM`, base16 palette setup (themes that propagate to TUI apps)
- **tmux-dev** — running TUI apps in tmux panes, `capture-pane` to grab TUI output programmatically
- **environment-composition** — fzf as composition glue in shell pipelines (not as a standalone TUI)
- **signals-monitoring** — sending signals to a misbehaving TUI app (`kill -TERM`)
