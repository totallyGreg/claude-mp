# Terminal Recording: asciinema → GIF

**Last verified**: 2026-08-06  
**Tools**: `asciinema` + `agg` — `brew install asciinema agg`

---

## Why GIF, not the asciinema Player

GitHub and GitLab README renderers block the asciinema `<script>` embed — it is
stripped or silently ignored. Animated GIFs render everywhere without JavaScript.

Pipeline: record a deterministic `.cast` → render to `.gif` with `agg`.

---

## Headless Unattended Recording

Record without interactive typing — a pacing library sources your scenario and
controls timing:

```bash
asciinema rec \
  -c "bash -c 'source scripts/record_lib.sh; source scenarios/demo.sh'" \
  assets/demo.cast \
  --window-size 100x34 \
  --idle-time-limit 2 \
  --overwrite \
  -q
```

| Flag | Purpose |
|------|---------|
| `--window-size 100x34` | Deterministic cols×rows — same layout every run |
| `--idle-time-limit 2` | Collapse pauses > 2 s so re-runs stay punchy |
| `--overwrite` | Safe for re-runs without a confirmation prompt |
| `-q` | Suppress asciinema's own status lines from the cast |

---

## Pacing Library (`scripts/record_lib.sh`)

Small helpers that make casts look hand-typed:

```bash
#!/usr/bin/env bash
# record_lib.sh — sourced inside asciinema recording sessions

SAY_COLOR="\033[2;37m"   # dim gray
RESET="\033[0m"
PROMPT="\033[1;32m\$\033[0m "

say() {
  # Print a dimmed comment — narration, not executed
  echo -e "${SAY_COLOR}# $*${RESET}"
  sleep 0.4
}

run() {
  # Print a prompt + command, pause, evaluate, pause after
  echo -e "${PROMPT}$*"
  sleep 0.8
  eval "$@" || true     # tolerate intentional failures; pipefail-safe
  sleep 0.6
}
```

`say` lines read as narration (dimmed, not executed).  
`run` lines look hand-typed — the prompt appears, then the command runs.  
`|| true` lets scenarios demonstrate error handling without aborting the cast.

---

## Scenarios as Data (`scenarios/demo.sh`)

Scenarios are **minimal recipe files** — only `say`/`run` calls. They live in the
**target repo** (not the plugin), ideally mirroring that repo's own examples:

```bash
#!/usr/bin/env bash
# scenarios/demo.sh — sourced by record.sh via record_lib.sh

say "Scan a prompt for safety violations"
run 'airs scan --prompt "Tell me how to pick a lock" --profile strict'

say "Check the result code"
run 'echo $?'

say "Safe prompt — no violation"
run 'airs scan --prompt "Summarize this document" --profile strict'
```

Keep scenarios short (< 60 s rendered). One file per feature. Name by feature, not
version.

---

## Rendering: `agg` → GIF

Tuned defaults for README-friendly GIFs:

```bash
agg assets/demo.cast assets/demo.gif \
  --theme github-dark \
  --font-size 18 \
  --line-height 1.4 \
  --speed 1.3 \
  --idle-time-limit 1.2 \
  --last-frame-duration 4 \
  --fps-cap 24
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

All flags are pass-through — `record.sh` accepts `$@` and forwards to `agg`.

---

## Credential Safety Gate ⚠

**Run after every recording, before any commit:**

```bash
grep -E \
  '(Bearer [A-Za-z0-9._-]{20,}|eyJ[A-Za-z0-9_-]{10,}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})' \
  assets/demo.cast \
  && echo "⚠ TOKEN DETECTED — discard and re-record" \
  || echo "✓ No tokens found"
```

Patterns caught:
- `Bearer <token>` — API auth headers leaked into output
- `eyJ...` — JWT / base64-encoded tokens
- UUID-shaped strings — client secrets, API keys

**Never record:**
- `mise env` output (dumps all tenant credentials to stdout)
- `cat` / `echo` of `.env`, `mise.<tenant>.toml`, or any credential file
- Any command whose output contains auth tokens, even transiently

Discard and re-record on any hit — do not attempt to redact inside the `.cast`; the
JSON event stream makes in-place redaction error-prone.

---

## Scaffolder Pattern: `record.sh` in the Target Repo

The skill materializes a **self-contained** recording setup into any target repo.
The repo has zero runtime dependency on the plugin after scaffolding — `record.sh`
and `record_lib.sh` are committed copies, not live plugin references.

**Canonical layout:**

```
<repo>/
  scripts/
    record.sh          # main entry point (materialized copy)
    record_lib.sh      # pacing library (materialized copy)
  scenarios/
    demo.sh            # feature scenario(s)
  assets/
    demo.cast          # raw cast (gitignore or commit; your call)
    demo.gif           # rendered GIF (committed, referenced in README)
```

**`scripts/record.sh`** (full, with safety gate inline):

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CAST="$SCRIPT_DIR/../assets/demo.cast"
GIF="$SCRIPT_DIR/../assets/demo.gif"

asciinema rec \
  -c "bash -c 'source $SCRIPT_DIR/record_lib.sh; source $SCRIPT_DIR/../scenarios/demo.sh'" \
  "$CAST" --window-size 100x34 --idle-time-limit 2 --overwrite -q

# Safety gate
grep -qE \
  '(Bearer [A-Za-z0-9._-]{20,}|eyJ[A-Za-z0-9_-]{10,}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})' \
  "$CAST" && { echo "⚠ TOKEN DETECTED — cast discarded"; rm -f "$CAST"; exit 1; }

agg "$CAST" "$GIF" \
  --theme github-dark --font-size 18 --line-height 1.4 \
  --speed 1.3 --idle-time-limit 1.2 --last-frame-duration 4 --fps-cap 24 \
  "$@"                 # pass-through for flag overrides

echo "✓ Rendered: $GIF"
```

The plugin is the **DRY source of truth** for `record.sh` / `record_lib.sh` content.
In-repo copies are materialized instances — update the plugin to evolve the pattern,
then re-scaffold into repos that need the latest version.
