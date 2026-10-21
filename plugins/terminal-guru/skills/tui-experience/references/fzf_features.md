# fzf Features — What's New and How to Stay Current

**Reviewed through fzf 0.74.5** (2026-10-11). Source: upstream `CHANGELOG.md`. Recipes marked **verified** were run on fzf 0.74.5 + tmux 3.8; the rest are upstream examples, not run here.

fzf releases every 2–4 weeks and keeps adding actions that replace wrapper scripts. Before writing an fzf picker, check what the installed version can do:

```bash
fzf --version          # → 0.74.5 (brew)
```

## Keeping this file current

When `fzf --version` (or the latest release) is newer than the stamp above:

```bash
gh release list -R junegunn/fzf -L 5
gh api repos/junegunn/fzf/contents/CHANGELOG.md -H 'Accept: application/vnd.github.raw' \
  | sed -n '1,/^0\.74\.5$/p'     # everything newer than the stamp
```

1. Read each new version's entries. Add anything that changes how pickers are built (new actions, events, options, env vars, popup/tmux behaviour) to the sections below, with the version it needs.
2. Note behaviour changes that break existing configs under **Breaking changes**.
3. Run a recipe before marking it **verified**.
4. Move the stamp, and bump the skill version.

A `## 0.x.y` heading in the changelog with no matching GitHub release is unreleased — don't recommend it yet.

---

## Prefer fzf for pickers

fzf is the default picker for scripts, tmux popups and shell widgets. Compared with television (tv 0.15.9, the latest as of 2026-10), measured on a 4-source tmux picker:

| Need | fzf | tv 0.15.9 |
|---|---|---|
| Cycle sources both ways | `transform` + `reload-sync`, any keys | `cycle_sources` forward only; repeated actions in one binding collapse |
| Follow light/dark terminal | `--color 16,…` and `-1` = terminal default | no default colour (`reset`/`default` rejected); one bad override silently drops all |
| Startup to first entry | ~140 ms | ~210 ms |
| Release cadence | every 2–4 weeks | none since 2026-06-14 |

Use tv only when its channel library is the point (ad-hoc browsing of its bundled channels). See `tui_tools.md` → television for its limits.

---

## Dynamic UI: transform and friends

`transform:CMD` runs CMD and executes the **actions it prints**. It's the building block for stateful pickers — state lives in what fzf exports (`$FZF_PROMPT`, `$FZF_QUERY`, `$FZF_POS`, …), so no temp files.

| Feature | Version | Notes |
|---|---|---|
| `transform` (0.45), `transform-{prompt,header,query,…}` (0.36+) | 0.45 | `transform-*` sets one thing from CMD's output |
| `bg-transform*`, `bg-cancel` | 0.63 | async; don't block the UI |
| `change-ghost` / `transform-ghost`, `--ghost` | 0.61 | placeholder text in an empty query |
| `change-pointer` / `transform-pointer` | 0.61 | |
| `change-nth`, `change-with-nth`, `change-header-lines` | 0.58 / 0.70 | 0.74.6 (unreleased) changes `change-*nth` rotation |
| `search(...)`, `transform-search` | 0.59 | search with a computed query |
| `exclude`, `exclude-multi` | 0.60 | drop items from the list |
| `trigger(...)` | 0.65 | fire another binding's actions |
| `wait` | 0.74 | block following actions until the search finishes (`start:wait+last`) |
| bare `put` in `transform` output | 0.74 | inserts the triggering key |

### Multi-source picker, Tab / Shift-Tab cycling — **verified**

One stepper script prints the actions; the current source is read back from the prompt:

```sh
#!/bin/sh
# source.sh <0-3> emits a source; source.sh step <1|-1> prints fzf actions.
names="sessions windows panes commands"
if [ "$1" = step ]; then
  i=0; for n in $names; do [ "${FZF_PROMPT%%>*}" = "$n" ] && break; i=$((i + 1)); done
  i=$(( (i + $2 + 4) % 4 ))
  set -- $names; shift $i
  printf 'change-prompt(%s> )+reload-sync(%s %d)+first' "$1" "$0" "$i"
else
  case $1 in 0) sesh list ;; 1) tmux list-windows -a ;; 2) tmux list-panes -a ;; 3) printf '%s\n' a b ;; esac
fi
```

```sh
./source.sh 0 | FZF_DEFAULT_OPTS= fzf --ansi --layout reverse --prompt 'sessions> ' \
  --bind "tab:transform:./source.sh step 1" --bind "btab:transform:./source.sh step -1"
```

- Use **`reload-sync`**, not `reload`: with `reload`, an Enter pressed right after Tab can accept an item from the old list.
- `FZF_DEFAULT_OPTS=` for this call keeps a user's global `--tmux`/`--popup` and hidden-preview defaults out of a picker that already runs in a popup.

---

## Events

| Event | Version | Fires |
|---|---|---|
| `start`, `load`, `focus`, `result`, `change`, `one`, `zero` | ≤0.54 | |
| `click-header` (`$FZF_CLICK_HEADER_WORD`/`_NTH` since 0.59) | 0.52 | clickable header, e.g. to switch mode |
| `multi` | 0.64 | selection changed |
| `click-footer` | 0.65 | |
| `every(N)` + `$FZF_IDLE_TIME`/`_MS` | 0.73 | timer; live lists and auto-accept |
| `result-final` | 0.74 | once after input closes — one-shot per-query actions |

```sh
# Live process list that keeps the cursor on the same PID (upstream example)
fzf --header-lines 1 --track --id-nth 2 --bind 'start,every(2):reload-sync:ps -ef'
```

`--track --id-nth N` (0.71) keeps the focused item, and with `--multi` the selection, across `reload-sync`.

---

## Layout and look

| Feature | Version |
|---|---|
| `--footer`, `--header-border`, `--list-border`, `--input-border`, `--style full\|minimal` | 0.58–0.63 |
| `inline` header/footer borders, `dashed` border | 0.72 |
| `--preview-window=next` | 0.73 |
| `--gap`, `--freeze-left/right`, `--wrap=word` | 0.56 / 0.67 / 0.68 |
| `--raw` + `toggle-raw` (non-matches stay, dimmed), `up-match`/`down-match`, `best` | 0.66 |
| `--accept-nth`, `--with-nth` templates (`{2}|{1}`) | 0.60 |
| `alt-bg` (striped rows), full-line background | 0.62 / 0.63 |

### Colours that follow the terminal

```sh
fzf --color '16,fg+:-1:bold,bg+:-1,hl:9,hl+:9:bold,header:-1:dim,pointer:2,prompt:4'
```

`16` starts from the 16-colour base theme (palette slots, no hex); `-1` is the terminal's own fg/bg. With a terminal that swaps palettes on OS appearance (Ghostty `theme = dark:…,light:…`), fzf follows with no theme switching. Hex colours in `FZF_DEFAULT_OPTS` do not.

---

## tmux and popups

| Feature | Version | Notes |
|---|---|---|
| `--tmux` | 0.53 | popup; needs tmux 3.3+ |
| `--popup` (= `--tmux`, also Zellij) | 0.71 | |
| `--popup` opens a **floating pane** on tmux 3.7+ | 0.74 | non-modal: switch panes, move/resize with the mouse, copy-mode. An explicit `--border` falls back to a popup. `--border-label` becomes the pane title |
| `change/transform-border-label` on the floating pane's border | 0.74.2 | |
| no unzoom over a zoomed pane | 0.74.5 | tmux 3.8+ |

When a tmux binding already opens `display-popup … 'zsh -ic picker'`, run plain fzf inside it — `--popup` would nest. Use `--popup` from a shell or Vim to get a floating pane instead of a modal popup.

---

## Scripting and remote control

- `--listen [SOCKET]` (Unix socket since 0.66; `$FZF_SOCK`), `GET /` returns state with match `positions` (0.71). `progress` = 100 now means the matches belong to the reported query (0.74.4).
- `$FZF_CURRENT_ITEM` (0.73) when quoting `{}` is awkward; skipped for items > 64 KB or with NUL.
- `{*}` all matched items (0.63), `{*n}`/`{*nf}` (0.65), `r` flag for unquoted output (0.61).
- `FZF_PREVIEW_*` exported to every child (0.57); `$FZF_DIRECTION`, `$FZF_RAW` (0.66); `$FZF_WRAP` (0.68).

---

## Breaking changes to watch

| Version | Change |
|---|---|
| 0.66 | `CTRL-N`/`CTRL-P` → `down-match`/`up-match` |
| 0.68 | `ctrl-/`, `alt-/` → `toggle-wrap-word` |
| 0.71 | `--tmux` is an alias of `--popup` |
| 0.74 | `--popup` on tmux 3.7+ is a floating pane, not a popup; `alt-left/right` bound to word motion |
| 0.74.6 (unreleased) | `change-nth`/`change-with-nth` rotate from the value after the current one; `transform-*nth` no longer split on `|` |
