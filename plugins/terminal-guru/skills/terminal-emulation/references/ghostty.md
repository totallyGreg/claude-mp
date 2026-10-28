---
last_verified: 2026-10-27
sources:
  - type: web
    url: "https://ghostty.org/docs/install/release-notes/1-4-0"
    description: "Ghostty 1.4.0 release notes"
  - type: web
    url: "https://github.com/Uzaaft/awesome-libghostty"
    description: "Community list of libghostty-based apps and libraries"
---

# Ghostty

Ghostty as the emulator layer, with the focus on running **tmux on top of it**. Covers which Ghostty features reach through tmux and which tmux hides, the 1.4 changes worth acting on, and the libghostty landscape for later decisions.

```bash
ghostty --version                      # 1.4 features need 1.4.0+
ghostty +show-config --default --docs  # every option with docs
ghostty +explain-config copy-on-select # 1.4+: docs for one option or action
```

Config: `~/.config/ghostty/config`.

---

## Ghostty Under tmux: What Reaches Through

tmux is a terminal emulator in its own right. Ghostty draws tmux's screen; programs in panes talk to tmux, not Ghostty. A Ghostty feature only helps if tmux forwards it or the feature is outside the VT stream.

| Ghostty feature | Under tmux | How to get it |
|---|---|---|
| Rendering, fonts, ligatures, themes (`theme = dark:…,light:…`) | Works | Nothing — outside the VT stream |
| Truecolor, styled/coloured underlines | Works | `terminal-features ",xterm-ghostty:RGB:usstyle"` |
| Overline (1.4: `Smol`/`Rmol` in terminfo) | Works once declared | Add `overline` to the `xterm-ghostty` features |
| OSC 8 hyperlinks (`link-osc8`, default on) | Works once declared | Add `hyperlinks` to the features |
| Clipboard via OSC 52 | Works | `set-clipboard on`/`external` + `clipboard` feature |
| Extended keys (Shift+Enter, CSI u) | Works | `extended-keys on` + `extkeys` feature |
| Notifications, progress, Kitty graphics | Works only through passthrough | `allow-passthrough on`; the program must wrap its sequences in tmux DCS passthrough |
| OSC 5522 Kitty clipboard, mode 2033 visibility reports (1.4) | Not forwarded | Only programs running directly in Ghostty |
| Ghostty scrollback, `jump_to_prompt`, OSC 133 prompt clicks | Sees tmux's screen, not your shell's prompts | Use tmux copy mode; tmux 3.8 handles OSC 133 itself (see tmux-dev `tmux_3_8_features.md`) |
| Ghostty splits/tabs | Overlap with tmux windows/panes | Pick one layer to own layout |
| Quick terminal (`toggle_quick_terminal`) | Complementary | Attach a dedicated tmux session in it |
| `tmux -CC` control mode | **Not wired to the GUI** (1.4 still) | No iTerm2-style native tmux windows yet |

Example `xterm-ghostty` line for tmux 3.8 (feature names from `man tmux` → `terminal-features`):

```tmux
set -as terminal-features ",xterm-ghostty:RGB:mouse:usstyle:clipboard:title:extkeys:overline:hyperlinks"
```

Check what tmux detected: `tmux display -p '#{client_termfeatures}'`.

### Environment inside tmux

`GHOSTTY_SURFACE_ID` (1.4) and `TERM_PROGRAM` come from the Ghostty surface that **started the tmux server**. Panes inherit the server environment, so these values are stale for other clients. Don't use them to identify a pane's surface inside tmux. To refresh on attach, add them to `update-environment`. That only updates new panes.

---

## 1.4 Upgrade Checklist

1.4 fixes two crashes (GHSA-hcr9-7hcr-mjm8, GHSA-hp9c-qp4q-cpw3) that let malicious output crash 1.3.0/1.3.1 through tmux control-mode parsing. tmux does not need to be installed for these to trigger. **Upgrade from 1.3.x.**

Breaking or behaviour changes on macOS:

| Change | Effect | Keep the old behaviour |
|---|---|---|
| `copy-on-select` macOS default `true` → `none`; `clipboard` now means system clipboard only | Selecting no longer copies | `copy-on-select = clipboard` (`both` = 1.3 Linux behaviour). Under tmux with mouse on, tmux owns selection anyway |
| `cmd+arrow_up/down` run their binds, default `jump_to_prompt` | No longer scroll to top/bottom | `keybind = cmd+arrow_up=scroll_to_top`, `keybind = cmd+arrow_down=scroll_to_bottom`; `cmd+home/end` also scroll |
| `scrollback-limit` → `scrollback-limit-bytes` (default 10 MB → 50 MB) | Old key still works (deprecated) | Rename; new `scrollback-limit-lines` caps by lines (first limit hit wins) |
| `+ssh-cache` arguments and output reworked | Scripts using the old form break | Positional `host[:port]`, `--prune=30d` |
| `ctrl+l` at a prompt keeps output in scrollback | More scrollback retained | — |

New and useful:

- **`ghostty +ssh`** wraps `ssh`. It installs `xterm-ghostty` terminfo on the remote, cached per host and port, and forwards `COLORTERM`/`TERM_PROGRAM*`. If the install fails it falls back to `TERM=xterm-256color`. Alias: `alias ssh='ghostty +ssh --'`. The `ssh-env`/`ssh-terminfo` shell-integration features now call it. **Inside tmux**, `$TERM` is `tmux-256color`. ssh sends that, so the remote needs `tmux-256color` terminfo, not `xterm-ghostty`.
- **`+explain-config`** prints docs for one option or keybind action. `+show-config` output goes through `$GHOSTTY_PAGER`, then `$PAGER`.
- **Keybind actions:** `move_tab_to_new_window`, `prompt_window_title`.
- **Config:** `middle-click-action`, `clipboard-write-limit-bytes` (64 MiB), `scrollback-compression`, `window-padding-balance = equal`, `theme` expands `~`.
- **Gated VT features (off by default):** `vt-window-resize-allowed` (`CSI 8;rows;cols t`) and `vt-xt-checksum-report` (DECRQCRA/XTCHECKSUM).
- **Protocols:** Kitty graphics animation and relative placements, OSC 133 `click_events=2`, DECSTR, DECBKM (mode 67), DECRQM for ANSI modes. These are parsed but not acted on: OSC 99 notifications, OSC 72 drag-and-drop, OSC 7501 program status (libghostty only), APC `25a1` glyph protocol.
- **zsh integration:** fixes a stray `{` and broken prompt marks when `PS1`/`PS2` end in `%`.

---

## libghostty and the Multiplexer Landscape

The `libghostty-vt` VT core builds standalone on macOS, Linux, Windows, FreeBSD, Android, iOS and WebAssembly, with no libc++. Its C API is **still unstable as of 1.4**. A libghostty 1.0 tag is expected before Ghostty 1.5. Ghostling is the project's minimal reference terminal on that API.

Projects are now embedding a real terminal core instead of shelling out to tmux. Examples: cmux, a macOS workspace that combines tmux with libghostty, and editor or notebook terminal panels. See `awesome-libghostty` for the current list. This overlaps with agent-oriented multiplexers (herdr, see tmux-dev `herdr_alternative.md`) and with tmux plugins. The space is changing quickly, so re-check before recommending a specific tool.

Decision framing for a tmux-on-Ghostty user:

- **Stay on tmux** when you need detach/reattach, remote persistence, scripting by `%pane` ID, or the plugin ecosystem. No libghostty tool yet replaces tmux's server model.
- **Lean on Ghostty directly** for things tmux strips: Kitty clipboard and graphics without passthrough, visibility reports, prompt-click events, native splits for local-only work.
- **Watch for** native `tmux -CC` support in Ghostty, which would merge the two layers, and for libghostty 1.0, the point where third-party multiplexers can build on a stable API.
