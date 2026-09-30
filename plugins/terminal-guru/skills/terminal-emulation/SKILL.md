---
name: terminal-emulation
description: This skill should be used when the user asks to "fix terminal colors", "configure $TERM", "debug terminfo", "set up truecolor", "test 256 color support", "fix unicode rendering", "fix garbled characters", "fix broken box drawing", "fix emoji rendering", "configure locale", "fix SSH terminal", "check $COLORTERM", "apply ANSI escape codes", "set up base16 theme", "record terminal session", "asciinema to gif", "create demo gif for readme", or needs help with the Unix terminal substrate — `$TERM`, terminfo database, ANSI escape codes, color tiers (16/256/truecolor), `$COLORTERM`, Unicode/UTF-8 rendering, locale configuration, SSH terminal setup, and terminal session recording (asciinema → GIF). Do NOT use for tmux automation (sessions, options, plugins, send-keys) — use tmux-dev. Do NOT use for TUI app theming (lazygit/k9s themes) — use tui-experience. Do NOT use for shell config — use zsh-dev.
metadata:
  version: "4.1.1"
license: MIT
compatibility: claude-code
---

# Terminal Emulation

## Overview

Diagnose and fix Unix terminal display issues: terminfo capabilities, Unicode/UTF-8 rendering, locale configuration, and terminal emulator setup. Covers colors, box drawing, emoji, SSH terminals, and TUI applications.

## When to Use This Skill

- Terminal display issues (garbled characters, wrong colors, broken box drawing)
- Unicode/UTF-8 rendering problems (emoji, CJK characters, combining characters)
- Terminfo database troubleshooting (wrong TERM, missing entries)
- ANSI escape codes, color tier selection (16 / 256 / truecolor)
- `$COLORTERM` detection and truecolor verification
- Color palette setup (base16, pywal, terminal emulator color schemes)
- Locale and encoding configuration
- SSH terminal configuration
- TUI application *display* problems (font glyphs, ACS rendering) — for app theming/keybindings use tui-experience
- `TERM=tmux-256color` setup and substrate-level tmux display issues — for tmux automation use tmux-dev
- Character width and alignment issues
- Font selection for Unicode coverage

## Core Capabilities

### 1. Terminal Diagnostics

Run comprehensive diagnostics to identify terminal, locale, and environment issues:

```bash
python3 scripts/terminal_diagnostics.py
```

The diagnostic script checks:
- Environment variables (TERM, LANG, LC_*, SHELL)
- Locale settings and UTF-8 support
- Terminal capabilities via terminfo/tput
- Unicode rendering (emoji, CJK, box drawing)
- Shell configuration files
- Installed TUI tools

**When to use**: Start with diagnostics when users report any terminal display issues.

### 2. Terminfo Database Management

For detailed terminfo troubleshooting, refer to `references/terminfo_guide.md` which covers:
- Terminal type (TERM) selection and configuration
- Terminfo database locations and structure
- Using infocmp, tic, tput, and toe commands
- Terminal capabilities (colors, cursor movement, text attributes)
- Creating custom terminfo entries
- Fixing common terminfo issues

**Common operations**:

```bash
# Check current terminal's capabilities
infocmp

# Test color support
tput colors

# Verify terminfo entry exists
infocmp $TERM >/dev/null 2>&1 && echo "OK" || echo "Missing"

# Compare terminal types
infocmp -d xterm-256color tmux-256color

# Create custom entry
infocmp xterm-256color > custom.ti
# Edit custom.ti
tic -o ~/.terminfo custom.ti
```

### 3. ANSI Colors

The terminal emulator implements the ANSI color protocol — 16 named colors, the 256-color palette, and 24-bit truecolor. Color tier support is independent of `$TERM`; `$COLORTERM=truecolor` signals 24-bit capability.

```bash
# Tier checks
echo $TERM                                    # terminfo entry (xterm-256color, tmux-256color, ...)
echo $COLORTERM                               # "truecolor" or "24bit" → 16M colors supported
tput colors                                   # numeric: 8, 16, 256, etc.

# Visual tests
printf '\e[31mRED\e[0m\n'                                          # 16-color: red text
printf '\e[38;5;208mORANGE\e[0m\n'                                 # 256-color: palette index 208
printf '\e[38;2;255;128;0mORANGE-truecolor\e[0m\n'                 # 24-bit: R=255 G=128 B=0
```

See `references/ansi_colors.md` for the full ANSI escape sequence reference, palette tiers, `$COLORTERM` detection, color-test tools (pastel, colortest), and terminal palette setup (base16, pywal).

### 4. Unicode and UTF-8 Troubleshooting

For detailed Unicode guidance, refer to `references/unicode_troubleshooting.md` which covers:
- Locale configuration for UTF-8
- Character width issues (narrow, wide, ambiguous, zero-width)
- Combining characters and normalization (NFC, NFD, NFKC, NFKD)
- Emoji rendering (simple, modifiers, ZWJ sequences)
- Box drawing and line characters
- Zero-width characters (ZWSP, ZWJ, ZWNJ)
- BOM detection and removal
- Terminal emulator configuration
- Font selection for Unicode coverage

**Common fixes**:

```bash
# Fix locale for UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Test Unicode rendering
echo "ASCII: Hello"
echo "CJK: 你好世界"
echo "Emoji: 😀 🎉 ✨"
echo "Box: ┌─┐│└┘"

# Fix box drawing (if showing as q, x, m, j)
export NCURSES_NO_UTF8_ACS=0

# Remove BOM from file
sed -i '1s/^\xEF\xBB\xBF//' file.txt
```

### 4. Terminal Recording (asciinema → GIF)

Capture terminal sessions as animated GIFs for GitHub/GitLab READMEs — the asciinema JS player is blocked in README renderers; rendered GIFs work everywhere.

Load `references/terminal_recording.md` for the full pattern: headless deterministic recording via a pacing library (`say`/`run` helpers), tuned `agg` rendering defaults, post-recording credential safety gate (grep for `Bearer`/JWT/UUID tokens — discard and re-record on any hit), and the `record.sh` scaffolder that materializes a self-contained recording setup into any target repo (target stays plugin-free after scaffolding).

Prerequisites: `brew install asciinema agg`

## Diagnostic Workflow

### Step 1: Gather Information

```bash
python3 scripts/terminal_diagnostics.py
```

Key information to verify:
- TERM value (should be xterm-256color, tmux-256color, etc.)
- Locale settings (should include UTF-8)
- Terminal emulator being used

### Step 2: Identify the Problem Domain

| Symptoms | Domain | Reference |
|----------|--------|-----------|
| Wrong colors, broken function keys | Terminfo | `references/terminfo_guide.md` |
| Garbled text, emoji broken, box drawing issues | Unicode/UTF-8 | `references/unicode_troubleshooting.md` |
| Mouse click bindings not firing, wrong range value | tmux automation | Use **tmux-dev** skill (`tmux_mouse_bindings.md`) |
| Need to create/manage tmux sessions, set up logging | tmux automation | Use **tmux-dev** skill (`tmux_session_management.md`) |

### Step 3: Apply Targeted Fixes

**Terminfo issues**:
```bash
echo $TERM
export TERM=xterm-256color
tput colors  # Should show 256
```

**Unicode issues**:
```bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
locale | grep UTF-8
```

### Step 4: Persist Configuration

Add fixes to appropriate shell config file:
- `.zshenv` - Environment variables (LANG, PATH)
- `.zshrc` - Interactive config (TERM overrides)

## Advanced Scenarios

### SSH Terminal Configuration

```bash
# In ~/.zshrc or ~/.bashrc
if [[ -n "$SSH_CONNECTION" ]]; then
    export TERM=xterm-256color
    export LANG=en_US.UTF-8
    export LC_ALL=en_US.UTF-8
fi
```

### Tmux/Screen Terminal Setup

```bash
# For tmux - add to ~/.tmux.conf
set -g default-terminal "tmux-256color"
set -ga terminal-overrides ",*256col*:Tc"

# For screen - add to ~/.screenrc
term screen-256color
```

Then in shell config:
```bash
if [[ -n "$TMUX" ]]; then
    export TERM=tmux-256color
elif [[ -n "$STY" ]]; then
    export TERM=screen-256color
fi
```

## Common Use Cases

### "My terminal colors are wrong"
1. Run diagnostics: `python3 scripts/terminal_diagnostics.py`
2. Check TERM: `echo $TERM`
3. Set correct TERM: `export TERM=xterm-256color`
4. Test: `tput colors` (should show 256)
5. Add to shell config to persist

### "Box drawing characters show as letters"
1. Verify UTF-8 locale: `locale | grep UTF-8`
2. Set if missing: `export LANG=en_US.UTF-8`
3. Try: `export NCURSES_NO_UTF8_ACS=0`
4. Check font supports Unicode
5. Refer to `references/unicode_troubleshooting.md`

### "Emoji aren't rendering correctly"
1. Verify UTF-8 locale: `locale | grep UTF-8`
2. Check terminal supports emoji
3. Verify font has emoji glyphs
4. Test: `echo "😀 🎉 ✨"`
5. Refer to `references/unicode_troubleshooting.md`

## Resources

### scripts/
- **`terminal_diagnostics.py`** - Comprehensive diagnostic tool for terminal, locale, and environment (supports --json mode)
- **`tests/display_tests.py`** - Display consistency tests (Python-based)
- **`tests/base.py`** - Shared test infrastructure

### references/
- **`terminfo_guide.md`** — Terminfo database, `$TERM` selection, infocmp/tic/tput, terminal capabilities
- **`ansi_colors.md`** — ANSI escape codes, 16/256/truecolor tiers, `$COLORTERM`, palette setup (base16), color-test tools
- **`unicode_troubleshooting.md`** — Unicode/UTF-8 character rendering and encoding issues
- **`terminal_recording.md`** — asciinema→GIF pipeline: headless recording, pacing library, agg defaults, credential safety gate, `record.sh` scaffolder

### Related skills
- **tmux-dev** — tmux automation, plugins, session management, mouse bindings, format strings
- **environment-composition** — sesh session orchestration on top of tmux
- **tui-experience** — TUI app theming (lazygit, k9s, fzf) and scripted demos with vhs
