# Terminal Recording — asciinema, agg, svg-term-cli, vhs

Reference for recording terminal sessions and converting to shareable formats. Covers `asciinema` (the recorder + `.cast` format), `agg` (GIF rendering), `svg-term-cli` (SVG rendering), and `vhs` (scripted recordings).

---

## asciinema — Recording

```bash
# Basic record (Ctrl-D or `exit` to stop)
asciinema rec demo.cast

# Compress idle pauses (max 2 seconds of silence)
asciinema rec -i 2 demo.cast

# Record a specific command (auto-stops on exit)
asciinema rec -c 'htop' htop-demo.cast

# Append to existing cast (continue recording)
asciinema rec --append demo.cast

# Custom title / set environment metadata
asciinema rec --title "Demo: deploy workflow" --env "SHELL,TERM,LANG" demo.cast

# Overwrite existing file (no prompt)
asciinema rec --overwrite demo.cast

# Stdin recording (capture input keystrokes too)
asciinema rec --stdin demo.cast
```

### Recording quality tips

- **Set `-i 2`** for any non-live demo — long pauses are tedious to watch
- **Resize terminal first** — recordings preserve dimensions; 80×24 plays well in embedded SVGs
- **Pre-write the script** — viewers don't want to watch you type-and-correct
- **Set `PS1=' $ '`** or similar minimal prompt to reduce visual noise
- **Disable RPROMPT and async git status** for the duration of recording

---

## asciinema — Playback

```bash
asciinema play demo.cast

# Faster playback
asciinema play -s 2 demo.cast            # 2x speed
asciinema play -s 0.5 demo.cast          # half speed

# Compress idle time on playback (even if recorded with long pauses)
asciinema play -i 1 demo.cast

# Loop playback
asciinema play --loop demo.cast
```

---

## asciinema — Upload & Share

```bash
# Upload to asciinema.org (anonymous by default)
asciinema upload demo.cast
# → returns https://asciinema.org/a/<id>

# Authenticate to associate uploads with your account
asciinema auth
# → prints a URL; open it to link this install to your account

# After auth, future uploads attach to your profile
asciinema upload demo.cast
```

Embed in markdown via the asciinema embed snippet (returned with the URL), or use the player JS for self-hosting:

```html
<script async id="asciicast-XXXXX" src="https://asciinema.org/a/XXXXX.js"></script>
```

---

## `.cast` File Format

`.cast` v2 files are JSONL — first line is a JSON header, subsequent lines are event tuples:

```jsonl
{"version": 2, "width": 80, "height": 24, "timestamp": 1717603200, "env": {"SHELL": "/bin/zsh", "TERM": "xterm-256color"}}
[0.123, "o", "$ "]
[1.456, "o", "ls -la\r\n"]
[1.500, "o", "total 24\r\n"]
```

Event tuple: `[time_seconds, "o"|"i", data]`
- `"o"` — output written to the terminal
- `"i"` — input typed by the user

**Editing** is just text editing — open in vim/vscode, delete the lines for a typo + correction, save. To re-time later events after deletion, run them through a small script or use `asciinema-edit` (third-party).

---

## Convert `.cast` → GIF (agg)

`agg` (asciinema gif generator) is the official asciinema GIF renderer:

```bash
# Default
agg demo.cast demo.gif

# Theme (built-in: asciinema, monokai, solarized-dark, solarized-light, ...)
agg --theme monokai demo.cast demo.gif

# Custom theme via hex palette
agg --theme '000000,ffffff,000000,ff0000,...' demo.cast demo.gif

# Speed adjustment + idle compression
agg --speed 1.5 --idle-time-limit 2 demo.cast demo.gif

# Font + size
agg --font-family 'JetBrains Mono' --font-size 16 demo.cast demo.gif

# Frame rate (default 30; lower = smaller file)
agg --fps-cap 15 demo.cast demo.gif

# Window decoration
agg --renderer fontdue --no-loop demo.cast demo.gif
```

GIFs are best when:
- Recipient may not have JS (GitHub markdown, email)
- Recording is short (<30s) — GIFs balloon for long recordings
- You don't need sharp text at multiple zoom levels

---

## Convert `.cast` → SVG (svg-term-cli)

```bash
# Basic
cat demo.cast | svg-term > demo.svg

# Add window chrome (looks like a terminal app)
cat demo.cast | svg-term --window > demo.svg

# Custom dimensions
cat demo.cast | svg-term --window --width 100 --height 30 > demo.svg

# Theme
cat demo.cast | svg-term --window --term iterm2 --profile 'Solarized Dark' > demo.svg

# From a cast.io URL
svg-term --cast XXXXX --out demo.svg
```

SVGs are best when:
- Embedding in README (GitHub renders them inline, perfectly crisp at any zoom)
- File size matters (text-based, much smaller than GIF for long recordings)
- You want users to be able to select/copy text from the recording (some SVG players support this)

---

## Convert `.cast` → MP4

asciinema has no native MP4 export. The standard route is GIF → MP4 via ffmpeg:

```bash
agg demo.cast demo.gif
ffmpeg -i demo.gif -movflags +faststart -pix_fmt yuv420p demo.mp4

# Or with audio (silent)
ffmpeg -i demo.gif -f lavfi -i anullsrc=cl=stereo -c:v libx264 -c:a aac -shortest demo.mp4
```

For richer MP4 output, use `vhs` instead (below) — it can output MP4 directly.

---

## vhs — Scripted Recordings

Charmbracelet `vhs` produces deterministic, scripted recordings. Better than asciinema for repeatable docs demos that don't need live interaction.

### `.tape` script

```vhs
# demo.tape
Output demo.gif
Output demo.mp4              # vhs can write multiple formats per tape

Set Shell "zsh"
Set FontFamily "JetBrains Mono"
Set FontSize 16
Set Width 1000
Set Height 600
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms
Set PlaybackSpeed 1.0

Hide
Type "clear"
Enter
Show

Type "ls -la"
Sleep 500ms
Enter
Sleep 1s

Type "git status"
Sleep 300ms
Enter
Sleep 1500ms

Type "echo done"
Enter
Sleep 1s
```

### Run

```bash
vhs demo.tape           # produces demo.gif + demo.mp4 per Output directives
vhs new demo.tape       # scaffold a new tape file
vhs validate demo.tape  # syntax-check without rendering
```

### vhs commands reference

| Command         | Purpose                                          |
| --------------- | ------------------------------------------------ |
| `Output <file>` | Add an output format (`.gif`, `.mp4`, `.webm`, `.ascii`) |
| `Set <var> <val>` | Change a setting (theme, font, dimensions, speeds) |
| `Type "<text>"` | Type a string                                    |
| `Enter`         | Press Enter                                      |
| `Backspace [N]` | Press Backspace (N times)                        |
| `Tab`, `Escape`, `Space` | Modifier keys                           |
| `Ctrl+<key>`    | Modifier combos                                  |
| `Sleep <dur>`   | Pause (`500ms`, `2s`, ...)                       |
| `Hide` / `Show` | Don't / do record subsequent commands            |
| `Ctrl+C`        | Send interrupt                                   |
| `Wait+Line+Time` | Wait for a regex match (advanced)               |

---

## vhs vs asciinema — Decision

| Use vhs when                                       | Use asciinema when                                      |
| -------------------------------------------------- | ------------------------------------------------------- |
| Demo needs to be exactly reproducible              | You're capturing a live, exploratory session            |
| You want MP4 output directly                       | You want a small `.cast` file for asciinema.org hosting |
| You're building docs that get regenerated regularly | You want to share a real-time SVG/JS player            |
| You want pixel-perfect framing (font, theme, dims) | You want to capture genuine timing and pauses          |
| You don't want to retype on every revision         | You're showcasing how a CLI actually feels to use       |

---

## Embedding Patterns

### GitHub README — SVG (recommended)

```markdown
![demo](./demo.svg)
```

SVG inline-renders on github.com, scales to any size, text stays sharp.

### GitHub README — GIF (universal)

```markdown
![demo](./demo.gif)
```

Always works; weighs more for long recordings.

### asciinema.org embed

```markdown
[![asciicast](https://asciinema.org/a/XXXXX.svg)](https://asciinema.org/a/XXXXX)
```

Self-updating thumbnail that links to the player.

### Self-hosted player

```html
<asciinema-player src="/path/to/demo.cast" cols="80" rows="24"></asciinema-player>
<script src="/path/to/asciinema-player.min.js"></script>
<link rel="stylesheet" type="text/css" href="/path/to/asciinema-player.css" />
```

---

## Common Issues

### "Colors look wrong in the rendered GIF/SVG"

- agg/svg-term-cli use their own palette — apply a matching theme flag (`--theme`, `--term`)
- Don't expect your local truecolor to render in GIF (which has 256-color limit per palette)

### "GIF is huge"

- Lower `--fps-cap` (try 10 or 15)
- Use `-i 1` on record OR `--idle-time-limit 1` on agg to compress pauses
- Render to SVG instead for >30s recordings

### "Recording captured my secrets"

`.cast` is plain JSONL — open in editor and delete the offending lines BEFORE upload. Re-upload (asciinema.org will give you a new URL; delete the old one in your profile).

### "vhs Type is too fast/slow"

`Set TypingSpeed 75ms` (default ~50ms). Or per-command: `Type@75ms "hello"`.
