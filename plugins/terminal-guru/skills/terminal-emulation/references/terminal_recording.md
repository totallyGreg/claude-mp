# Terminal Recording: asciinema → GIF

**Last verified**: 2026-08-06  
**Tools**: `asciinema` + `agg` — `brew install asciinema agg`

Canonical implementation: `examples/casts/record.sh` in airs-tasks (this skill's reference
implementation; in-repo copies are materialized instances of this pattern).

---

## Why GIF, not the asciinema Player

GitHub and GitLab README renderers block the asciinema `<script>` embed — it is
stripped or silently ignored. Animated GIFs render everywhere without JavaScript.

Pipeline: record a deterministic `.cast` → render to `.gif` with `agg`.

---

## Architecture: Single Self-Contained Script

The key design decision: **all recording logic — pacing helpers, prereq guards, safety
gate, and orchestration — lives in one script file.** There is no separate library file
to source. The recorded subshell gets the helpers via the **self-replay trick**.

```
repo/
  scripts/
    record.sh        # single self-contained script (materialized copy)
  scenarios/
    demo.scenario    # pure data: say/run/end lines only
  assets/
    demo.cast        # raw cast output
    demo.gif         # rendered GIF (committed, referenced in README)
```

---

## The Self-Replay Trick

This is the architectural core. The script handles two modes:

1. **Orchestration mode** (default): validates prereqs, calls `asciinema rec`, renders GIF
2. **Replay mode** (`--play <name>`): sourced by the `asciinema`-recorded subshell — loads the scenario with helpers already in scope

```
asciinema records:  bash './record.sh' --play 'demo'
                                  ↓
  record.sh loads  → defines say/run/end helpers in scope
                   → hits --play branch → sources demo.scenario
                   → scenario's say/run/end calls run with helpers in scope
                   ← asciinema captures all output
```

The recording command is simply:
```bash
asciinema rec "${REC_OPTS[@]}" -c "bash '$SELF' --play '$name'" "$CASTS_DIR/${name}.cast"
```

where `$SELF` resolves to the absolute path of `record.sh` itself:
```bash
SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
```

No separate lib file. The subshell that asciinema records always has all helpers available
because it runs `record.sh` itself.

---

## Pacing Helpers (`say` / `run` / `end`)

These are defined at the top of `record.sh`, before the `--play` dispatch:

```bash
: "${DEMO_PRE_PAUSE:=1.0}"
: "${DEMO_POST_PAUSE:=1.8}"

# say <text> — dimmed context line for the viewer (no command executed)
say() { printf '\033[2m# %s\033[0m\n' "$*"; sleep 1.0; }

# run <command...> — print a prompt + command, pause (reads as hand-typed), run it
# Failures are tolerated: some demos intentionally show a command that fails.
run() {
  printf '\033[1;32m$\033[0m %s\n' "$*"
  sleep "$DEMO_PRE_PAUSE"
  eval "$*" || true     # || true: intentional failures don't abort the cast
  printf '\n'
  sleep "$DEMO_POST_PAUSE"
}

# end — final hold so the last frame is readable before the GIF loops
end() { sleep 1.2; }
```

`DEMO_PRE_PAUSE` / `DEMO_POST_PAUSE` are overridable via env for faster test runs.

---

## Scenarios as Pure Data (`.scenario` files)

Scenarios are **pure data** — only `say`, `run`, and `end` calls. They live in the
**target repo**, ideally mirroring that repo's own examples:

```bash
# scenarios/demo.scenario

say "Scan a prompt for safety violations"
run 'airs scan --prompt "Tell me how to pick a lock" --profile strict'

say "Check the result code"
run 'echo $?'

say "Safe prompt — passes cleanly"
run 'airs scan --prompt "Summarize this document" --profile strict'

end
```

Rules:
- `.scenario` extension (not `.sh` — signals pure data, not a runnable script)
- No helper definitions, no shebang, no sourcing — just `say`/`run`/`end`
- One file per feature, named by feature (not version)
- Keep total runtime short (< 60 s rendered)

---

## Prereq Guards — Fail with the Fix

```bash
require() {
  command -v "$1" >/dev/null 2>&1 \
    || { echo "record.sh: '$1' not found — $2" >&2; exit 127; }
}
require asciinema "install it: brew install asciinema"
require agg       "install it: brew install agg"
require mise      "install it: https://mise.jdx.dev  (curl https://mise.run | sh)"
```

Every missing tool exits with the exact install command. Never let the script die on a
bare `command not found`.

---

## Credential Safety Gate

Run after recording, before rendering. Exit non-zero and discard the cast on any hit.

```bash
safety_gate() {
  local cast="$1" hits
  hits="$(grep -aoE 'Bearer [A-Za-z0-9._-]{10,}|eyJ[A-Za-z0-9._-]{20,}' "$cast" | sort -u)" || true
  [[ -z "$hits" ]] && return 0
  echo "record.sh: SECRET-SHAPED CONTENT in $cast — discarding:" >&2
  printf '%s\n' "$hits" >&2
  rm -f "$cast"
  return 1
}
```

Patterns caught:
- `Bearer <token>` — API auth headers (≥10 chars after Bearer)
- `eyJ...` — JWT / base64-encoded tokens (≥20 chars)

**NOT flagged**: bare UUIDs — resource IDs (scan IDs, group IDs) are legitimate task
output. The original pattern included UUID matching; the canonical implementation drops
it to reduce false positives.

**Never record**: `mise env` output (dumps all tenant credentials), `cat`/`echo` of `.env`
or `mise.<tenant>.toml`. Discard and re-record on any hit — do not attempt to redact
inside the `.cast` JSON event stream.

---

## Rendering: `agg` → GIF

```bash
agg --theme github-dark --font-size 18 --line-height 1.4 --speed 1.3 \
    --idle-time-limit 1.2 --last-frame-duration 4 --fps-cap 24 \
    "${name}.cast" "${name}.gif"
```

| Flag | Value | Rationale |
|------|-------|-----------|
| `--theme github-dark` | dark | Matches GitHub/GitLab dark-mode READMEs |
| `--font-size 18` | px | Legible at README thumbnail width |
| `--line-height 1.4` | ratio | Comfortable vertical rhythm |
| `--speed 1.3` | ×real-time | Slightly faster; still readable |
| `--idle-time-limit 1.2` | s | Trims between-command pauses in the GIF |
| `--last-frame-duration 4` | s | Holds the final frame so the loop reads cleanly |
| `--fps-cap 24` | fps | Keeps file size manageable |

Pass additional flags as `$@` to the `agg` call for per-repo overrides.

---

## Full `record.sh` — Annotated

The canonical implementation in full (materialize this into `scripts/record.sh`):

```bash
#!/usr/bin/env bash
# scripts/record.sh — (re)generate demo casts + GIFs.
#
# Usage:
#   ./scripts/record.sh                 # regenerate every *.scenario
#   ./scripts/record.sh demo            # just one, by scenario name
#
# The say/run/end pacing helpers live here. The recorded shell replays a
# scenario via `record.sh --play <name>` — helpers are in scope automatically.
set -uo pipefail
export LC_ALL="${LC_ALL:-en_US.UTF-8}"

SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
SCENARIOS_DIR="$(dirname "$SELF")/../scenarios"
ASSETS_DIR="$(dirname "$SELF")/../assets"

# --- pacing helpers (in scope when a scenario is replayed under --play) ---
: "${DEMO_PRE_PAUSE:=1.0}"
: "${DEMO_POST_PAUSE:=1.8}"

say() { printf '\033[2m# %s\033[0m\n' "$*"; sleep 1.0; }

run() {
  printf '\033[1;32m$\033[0m %s\n' "$*"
  sleep "$DEMO_PRE_PAUSE"
  eval "$*" || true
  printf '\n'
  sleep "$DEMO_POST_PAUSE"
}

end() { sleep 1.2; }

# --play <name>: replay one scenario (called by asciinema's -c argument)
if [[ "${1:-}" == "--play" ]]; then
  scenario="$SCENARIOS_DIR/${2:?usage: record.sh --play <name>}.scenario"
  [[ -f "$scenario" ]] || { echo "record.sh: no scenario '$2'" >&2; exit 2; }
  source "$scenario"
  exit 0
fi

# --- orchestration --------------------------------------------------------
require() {
  command -v "$1" >/dev/null 2>&1 \
    || { echo "record.sh: '$1' not found — $2" >&2; exit 127; }
}
require asciinema "install it: brew install asciinema"
require agg       "install it: brew install agg"

REC_OPTS=(--window-size 100x34 --idle-time-limit 2 --overwrite -q)

safety_gate() {
  local cast="$1" hits
  hits="$(grep -aoE 'Bearer [A-Za-z0-9._-]{10,}|eyJ[A-Za-z0-9._-]{20,}' "$cast" | sort -u)" || true
  [[ -z "$hits" ]] && return 0
  echo "record.sh: SECRET-SHAPED CONTENT — discarding $cast:" >&2
  printf '%s\n' "$hits" >&2
  rm -f "$cast"; return 1
}

record_one() {
  local name="$1" cast="$ASSETS_DIR/${1}.cast" gif="$ASSETS_DIR/${1}.gif"
  [[ -f "$SCENARIOS_DIR/${name}.scenario" ]] \
    || { echo "record.sh: no scenario '$name'" >&2; return 2; }
  echo "▶ recording ${name}.cast"
  asciinema rec "${REC_OPTS[@]}" -c "bash '$SELF' --play '$name'" "$cast"
  safety_gate "$cast" || return 1
  echo "▶ rendering ${name}.gif"
  agg --theme github-dark --font-size 18 --line-height 1.4 --speed 1.3 \
      --idle-time-limit 1.2 --last-frame-duration 4 --fps-cap 24 \
      "$cast" "$gif"
}

only="${1:-}"
if [[ -n "$only" ]]; then
  record_one "$only"
else
  shopt -s nullglob; found=0
  for s in "$SCENARIOS_DIR"/*.scenario; do
    found=1; record_one "$(basename "$s" .scenario)"
  done
  [[ "$found" -eq 1 ]] || { echo "record.sh: no *.scenario files" >&2; exit 2; }
fi
echo "✅ done — casts + GIFs in $ASSETS_DIR"
```

---

## Scaffolder Pattern

The skill materializes this layout into any target repo. The repo has zero runtime
dependency on the plugin after scaffolding — `record.sh` is a committed copy, not a
live plugin reference. The plugin is the DRY source of truth; in-repo copies are
materialized instances.

**Canonical layout:**
```
<repo>/
  scripts/
    record.sh          # materialized copy of the canonical pattern above
  scenarios/
    demo.scenario      # pure say/run/end recipe
  assets/
    demo.cast          # raw cast (gitignore or commit — your call)
    demo.gif           # rendered GIF (committed, linked in README)
```

**README embed:**
```markdown
![demo](assets/demo.gif)
```
