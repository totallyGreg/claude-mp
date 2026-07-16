# herdr — Alternative Multiplexer

`herdr` is a terminal-workspace multiplexer built around AI agent panes (sidebar of spaces/agents, splits, tabs) — the same role tmux fills, but a separate tool with its own config and addressing model, not a tmux wrapper. Some users run it standalone (e.g. directly in Ghostty) instead of nesting it inside tmux; nesting the two adds no benefit since herdr manages its own panes/splits/tabs, and can produce confusing overlapping border/theme rendering.

## Config

- File: `~/.config/herdr/config.toml`
- `herdr --default-config` dumps every key with defaults and comments — faster than the docs site for discovering what's configurable
- `herdr config check` validates TOML syntax/shape only — it does **not** validate theme-name enums or token semantics
- `herdr server reload-config` applies config changes live, no restart needed

## Theming

- `[theme] name = "<built-in>"`, `auto_switch`, `dark_name` / `light_name` — built-in themes can ship true light/dark sibling pairs (e.g. `solarized` / `solarized-light`, listed separately in the in-app theme picker), so don't assume a bare theme name lacks a sibling without checking the picker or `--default-config`.
- `[ui] accent` controls split-pane border color.
- `[theme.custom]` overrides individual palette tokens (`accent`, `panel_bg`, `overlay0`, `text`, `surface0`/`surface1`, etc.) on top of a built-in theme, but not every documented token has a visible effect in every UI region — verify empirically rather than trusting the docs:
  1. Set each candidate token to a maximally distinct probe color (magenta, green, cyan)
  2. `herdr server reload-config`, then screenshot and pixel-sample the rendered colors
  3. Map probe color → UI region, replace with real palette values, drop tokens with no visible effect

## Known gap

herdr draws no divider between the sidebar and the main content pane, nor between the sidebar's own internal sections — `pane_borders` only applies to actual split panes in the content area, not sidebar chrome. Confirmed empirically (pixel-sampled with all tokens flooded); there's no config workaround today.
