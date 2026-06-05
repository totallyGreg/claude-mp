# ANSI Colors

Reference for the ANSI color protocol implemented by terminal emulators: the three color tiers (16 / 256 / truecolor), the escape sequences that select them, capability detection via `$COLORTERM` and `tput`, palette/theme setup (base16, pywal), and color-test tools.

---

## The Three Color Tiers

| Tier         | Range            | Escape sequence form            | Required terminal capability  |
| ------------ | ---------------- | ------------------------------- | ----------------------------- |
| 16-color     | 0–15             | `\e[30m`–`\e[37m` (fg), `\e[90m`–`\e[97m` (bright fg) | Universal — every TTY supports this |
| 256-color    | 0–255            | `\e[38;5;Nm` (fg), `\e[48;5;Nm` (bg) | `$TERM` ending in `-256color` |
| Truecolor    | 16,777,216 (24-bit) | `\e[38;2;R;G;Bm` (fg), `\e[48;2;R;G;Bm` (bg) | `$COLORTERM=truecolor` or `=24bit` |

`\e` is ESC (`\x1b`, `\033`, octal 27). All three forms end with `m`. Reset with `\e[0m`.

## Capability Detection

```bash
# What terminfo says (16 or 256)
tput colors                     # → 8, 16, 256

# What the emulator promises (the truecolor signal)
echo "$COLORTERM"               # truecolor / 24bit / (empty)

# What $TERM advertises
echo "$TERM"                    # xterm-256color, tmux-256color, ...
```

**Why `$COLORTERM` matters:** terminfo's `colors` capability tops out at 256. Truecolor support is signaled out-of-band via `$COLORTERM` because terminfo predates 24-bit color. Apps that want truecolor MUST check `$COLORTERM` — `tput colors` will always say 256 even on a truecolor terminal.

Common emulators that set `$COLORTERM=truecolor` automatically: iTerm2, Alacritty, kitty, WezTerm, Ghostty, Terminal.app (recent), Windows Terminal, recent gnome-terminal.

## ANSI Escape Sequence Anatomy

```
\e[ <params> m
```

`params` is a semicolon-separated list of SGR (Select Graphic Rendition) codes. Multiple effects in one escape:

```bash
printf '\e[1;38;5;208;48;5;234mBOLD ORANGE ON DARK\e[0m\n'
#       │ │      │   │      │
#       │ │      │   │      └── reset
#       │ │      │   └────────── bg=palette[234]
#       │ │      └────────────── (separator)
#       │ └───────────────────── fg=palette[208]
#       └─────────────────────── bold
```

### Common SGR codes

| Code     | Effect                              |
| -------- | ----------------------------------- |
| `0`      | Reset all attributes                |
| `1`      | Bold / bright                       |
| `2`      | Dim / faint                         |
| `3`      | Italic (not universally supported)  |
| `4`      | Underline                           |
| `5`      | Blink                               |
| `7`      | Reverse video                       |
| `8`      | Hidden                              |
| `9`      | Strikethrough                       |
| `22`–`29` | Disable the corresponding attribute |
| `30`–`37` | Set 16-color foreground            |
| `40`–`47` | Set 16-color background            |
| `38;5;N` | Set 256-color foreground (N=0–255)  |
| `48;5;N` | Set 256-color background            |
| `38;2;R;G;B` | Set truecolor foreground        |
| `48;2;R;G;B` | Set truecolor background        |
| `90`–`97` | Set bright 16-color foreground     |
| `100`–`107` | Set bright 16-color background   |

### Reset patterns

```bash
\e[0m       # full reset
\e[39m      # reset fg only
\e[49m      # reset bg only
\e[22m      # disable bold
\e[24m      # disable underline
```

## The 256-Color Palette

The 256-color palette is structured:

- **0–7**: standard ANSI colors (black, red, green, yellow, blue, magenta, cyan, white)
- **8–15**: bright ANSI colors
- **16–231**: 6×6×6 RGB cube (R, G, B each 0–5). Index = `16 + 36*R + 6*G + B`
- **232–255**: grayscale ramp (24 levels)

Useful index ranges:

| Range   | What it is                       |
| ------- | -------------------------------- |
| 0–15    | The basic 16                     |
| 16–51   | The "blue half" of the RGB cube  |
| 196     | Pure red                         |
| 46      | Pure green                       |
| 21      | Pure blue                        |
| 208     | Orange                           |
| 232–255 | Grayscale ramp (dark → light)    |

## Truecolor

```bash
# Pure red, green, blue
printf '\e[38;2;255;0;0mRED\e[0m\n'
printf '\e[38;2;0;255;0mGREEN\e[0m\n'
printf '\e[38;2;0;0;255mBLUE\e[0m\n'

# Custom shades
printf '\e[38;2;102;204;255mSKY\e[0m\n'
printf '\e[38;2;255;128;0mORANGE\e[0m\n'
```

### Verify truecolor in your terminal

```bash
# If you see a smooth gradient, truecolor works
awk 'BEGIN{
  for (colnum = 0; colnum<77; colnum++) {
    r = 255-(colnum*255/76);
    g = (colnum*510/76);
    b = (colnum*255/76);
    if (g>255) g = 510-g;
    printf "\033[48;2;%d;%d;%dm ", r,g,b;
  }
  printf "\n\033[0m";
}'
```

Banded output instead of a smooth gradient = no truecolor (terminal is approximating to 256).

## `tput` Wrapper

`tput` queries terminfo and emits the correct escape for the current `$TERM`. Use it instead of hardcoding sequences when you need terminfo-driven portability:

```bash
tput setaf 1           # foreground = red (basic 16)
tput setab 4           # background = blue
tput setaf 208         # 256-color orange (if terminal supports)
tput bold
tput sgr0              # reset

# Capability queries
tput colors            # number of colors
tput Tc 2>/dev/null    # truecolor capability (custom user-defined cap)
```

`tput` does NOT emit truecolor escapes; for 24-bit, you must write the `\e[38;2;...m` form directly.

## Palette / Theme Setup

The terminal emulator's color palette controls how the 16 basic ANSI colors are rendered. Apps then refer to color *numbers*, and the emulator paints them in whatever hex values the palette defines.

### base16

A 16-color palette spec adopted across editors and terminals:

```
base00–base07   background → foreground gradient
base08–base0F   accent colors (red, orange, yellow, green, cyan, blue, purple, brown)
```

Tools that apply base16 themes:
- **base16-shell** — set the terminal's 16 ANSI slots
- **flavours** (Rust port of base16) — generate themes from any 16-color palette
- Editor-specific: base16-vim, base16-helix, etc.

### pywal

Generate palettes from an image, apply across terminal, shell, wm, etc.:

```bash
wal -i ~/Pictures/wallpaper.png
```

Writes `~/.cache/wal/colors.sh` (and many other formats) — source it from `.zshrc` for automatic palette switching.

### Per-emulator palette config

| Emulator        | Palette config location                            |
| --------------- | -------------------------------------------------- |
| iTerm2          | Preferences → Profiles → Colors (or `.itermcolors`) |
| Alacritty       | `~/.config/alacritty/alacritty.toml` → `[colors]` |
| kitty           | `~/.config/kitty/kitty.conf` → `color0`–`color15` |
| WezTerm         | `~/.config/wezterm/wezterm.lua` → `colors`         |
| Ghostty         | `~/.config/ghostty/config` → `palette = 0=#...`   |
| Terminal.app    | Preferences → Profiles → Colors                    |

## Color-Test Tools

```bash
# pastel — color manipulation + display (brew install pastel)
pastel color "#ff8800"                 # display + info on one color
pastel format ansi-truecolor "#ff8800" # output escape sequence
pastel paint -f red "hello world"      # foreground-paint text

# colortest — old-school comprehensive palette display
colortest-16
colortest-256
colortest-rgb

# Built-in 256-color grid
for i in {0..255}; do
  printf '\e[48;5;%dm %3d \e[0m' "$i" "$i"
  (( (i + 1) % 16 == 0 )) && echo
done
```

## Common Issues

### "Colors look washed out / dim"

- Terminal has a low-contrast palette → adjust the 16 ANSI slot definitions in emulator preferences
- Background is too close in luminance to foreground colors → pick a higher-contrast theme

### "256-color codes show as approximations"

- `$TERM` doesn't advertise 256-color support → set `TERM=xterm-256color` (or `tmux-256color` inside tmux)
- Inside tmux: `tmux.conf` needs `set -g default-terminal "tmux-256color"`

### "Truecolor not working in tmux"

```tmux
# In ~/.config/tmux/tmux.conf — required for truecolor passthrough
set -g default-terminal "tmux-256color"
set -as terminal-features ",xterm-256color:RGB"   # tmux 3.2+
# Or the older form:
set -as terminal-overrides ",*256col*:Tc"
```

Then verify inside tmux: `echo $COLORTERM` and run the gradient test above.

### "Italic / underline doesn't render"

- Terminfo entry lacks the capability → use `xterm-256color` (has italic) over older `xterm`
- Font lacks an italic face → use a font with italic glyphs (e.g., Fira Code Italic)

### "Colors broken in SSH"

```bash
# In ~/.zshrc — propagate appropriate $TERM and $COLORTERM
if [[ -n "$SSH_CONNECTION" ]]; then
    export TERM=xterm-256color
    [[ -z "$COLORTERM" ]] && export COLORTERM=truecolor
fi
```

Remote `$TERM` must have a corresponding terminfo entry on the remote host (`infocmp $TERM` to check).

## Related References

- `terminfo_guide.md` — terminfo capabilities, `tput` extended usage, custom terminfo entries
- `unicode_troubleshooting.md` — character rendering separate from color (combining chars, ZWJ, BOM)
- `tui-experience/tui_tools.md` — applying themes inside TUI apps (lazygit/k9s/btop)
