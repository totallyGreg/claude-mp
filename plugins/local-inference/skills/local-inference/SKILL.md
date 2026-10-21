---
name: local-inference
description: This skill should be used when the user says "use pi", "use the local model", "local inference", "run it on the local model", "offload this to pi", "run it locally", "local teammate", "claude on omlx", "update the local model tiers", "a new local model came out", "decide locally", "classify these", "spawn a pi teammate", "pi in a tmux pane", "use fm", "extract this receipt", "OCR this image", or when a quick constrained judgment (pick a label, yes/no, extract fields into JSON, also from an image) is needed, or when a mechanical, well-specified task (bulk reading or summarizing files or logs, first-pass triage, extracting facts from many files, exact-spec edits) can run on a local model — via Pi or via Claude Code launched on the local server — instead of spending Claude tokens. Do NOT use for root-cause debugging, design decisions, security-sensitive changes, or anything whose failure is silent — local models are wrong more often and their output must be verified.
metadata:
  version: "2.4.0"
compatibility: macOS on Apple silicon; oMLX server on 127.0.0.1:8000; macOS 27+ for `fm`; pi; tmux 3.5+ for pane teammates; uv for the Python scripts
license: MIT
---

# local-inference

Delegate work to models running on this Mac, picked by task tier, not by model
or tool. The tiers stay; the stack underneath changes as better tools arrive.

**Current stack** (2026-10): the [oMLX](https://github.com/jundot/omlx) server
serves the models and the tier profiles; two agents use them —

- **Pi** (`pi`) — a coding agent with an `omlx` provider
  (`~/.pi/agent/models.json`), run one-shot or as a pane teammate.
- **Claude Code on oMLX** — `omlx launch claude`, a real cross-session teammate
  (`scripts/claude_team.sh`; see § Pi vs Claude Code on oMLX).

When a part of the stack is replaced (a new server, a Splash-style speculative
decoder, another agent), keep the tier names and the evidence files, and
record the swap in references/tiers.md and references/pi-vs-claude.md.

Claude Code (this session, on Anthropic's models) stays the orchestrator: it
writes the brief, runs the local agent, and **verifies the result** before
using it.

## Tiers — pick by task, never by model

Each tier is an oMLX profile exposed as a model. Call it by tier name
(`omlx/<tier>`); which model backs it changes over time.

| Tier | Use for | Context | Thinking |
|------|---------|---------|----------|
| `omlx/fast` | Bulk reading, extraction, summarizing, reformatting, exact-spec edits — the default for this skill | 64K | off |
| `omlx/code` | Multi-step agentic work: tool loops, multi-file edits | 128K | on, 4K budget |
| `omlx/deep` | One hard question: design reasoning, tricky analysis. Slow to answer — it thinks up to 16K tokens first | 128K | on, 16K budget |
| `decide` | System-1 calls: pick one label, yes/no, or fill a small JSON schema. Not through Pi — see below | 16K | off |
| `see` | Images → text or JSON via `scripts/see.sh`, Pi's `see`: oMLX `:fast` if up, else `fm`; codes `fm` — [apple-fm.md](references/apple-fm.md) | 64K / 8K | off |

The current model behind each tier, how the tiers were derived, and the
procedure for a new model are in
[references/tiers.md](references/tiers.md) — read it when the user asks to
update tiers or a tier is failing.

## Run

**Preflight** — is the server up?

```bash
curl -s -o /dev/null -w '%{http_code}\n' -m 3 http://127.0.0.1:8000/v1/models   # 401 = up (auth required); 000 = down
```

Down → `omlx start`, or tell the user; do not fall back to guessing.

```bash
pi -p --no-session -nc -ns \
   --model omlx/fast \
   --tools read,grep,find,ls \
   "<brief>" </dev/null
```

| Flag | Why |
|------|-----|
| `-p --no-session` | One-shot: prints the answer, leaves no session |
| `-nc`, `-ns` | Skip AGENTS.md and skill discovery — they eat a small model's attention; put the rules that matter in the brief |
| `--model omlx/<tier>` | By tier name. No globs (`omlx/*:deep`): `:` is read as a thinking level |
| no `--thinking` | The tier's oMLX profile owns thinking |
| `--tools` | **Pi has no permission prompts.** Read-only: `read,grep,find,ls`; edits (in a git tree only): add `edit,write`. Bash: only via § Gated edit |
| `</dev/null` | **Required** — without it `pi -p` waits on stdin forever |

Run under `run_in_background`, **one at a time**: parallel runs add ~no
throughput and delay every answer (tiers.md derivation 11).

## Decide — one constrained answer, ~1–1.5 s

For a quick judgment that doesn't need an agent loop: triage, routing,
classification, yes/no, extracting a few fields. oMLX constrains the output
with a grammar, so the answer is always one of the choices or schema-valid JSON:

```bash
S=${CLAUDE_PLUGIN_ROOT}/skills/local-inference/scripts/decide.py
$S --choices bug,improvement --system "Classify the backlog item." "<text>"
$S --choices yes,no --system "<the criterion, stated exactly>" "<text>"
$S --schema fields.json "<text to extract from>"      # JSON Schema file
cat item.txt | $S --choices a,b,c --system "..."      # question from stdin
```

- Always give the criterion in `--system`, including what each choice means, and say how to treat the ambiguous case — the measured 93% on 11-way area classification was with a one-line definition per area, and an exact bug/improvement definition gained 2–3 items in 45.
- Wording moves the score as much as the model: longer area descriptions dropped the same model from 42 to 37 of 45. Keep a definition per choice short and literal, and compare models only on identical wording.
- It was right 69–93% of the time on real judgment calls, depending on the question (see references/tiers.md). Use it to sort, route and pre-filter; verify any decision that changes something.
- Decision models on oMLX's `/v1/decisions` (a probability per option): d3-flash matched or beat this tier at ~4× the speed but isn't wired into `decide.py` yet; Clef lost. Evidence: references/tiers.md, derivations 9 and 15.
- The grammar guarantees the answer's shape, not its truth: a borderline call is uncertain — sharpen the criterion or escalate.
- Many decisions → loop in the shell; each call is independent and fast.

## Teammate — Pi in its own tmux pane

For a multi-turn conversation the user can watch (and type into), run Pi
interactively in a pane beside this one instead of one-shot `pi -p`:

```bash
T=${CLAUDE_PLUGIN_ROOT}/skills/local-inference/scripts/pi_team.sh
P=$($T spawn code "$PWD")           # tier, dir, optional name; prints the pane id (alias pi-code)
$T ask $P "<task>" </dev/null       # types the task, waits, prints the answer + model + tools used
$T ask $P "<follow-up>" </dev/null  # same session — it remembers the earlier turns
$T close $P                         # kill the pane and delete its session files
```

- Answers come from Pi's session JSONL, not the screen; one task at a time.
  `SendMessage`/`ListAgents` don't reach it — this script is the channel.
- Interactive Pi loads AGENTS.md and skills, so turns cost more than one-shots.
- Spawn it in the dir (or worktree) it should change: `write-boundary` limits
  edit/write to it. **Bash isn't bounded** — `permission-gate` stops only
  `rm -rf`, `sudo` and `chmod 777` — so for edits that need bash use § Gated edit.
  Close the pane when done.

## Which to use — Pi or Claude Code on oMLX

**Default to Pi** (`pi -p`, `decide.py`, `pi_team.sh`): the same edit, the same
diff, fewer friction points, answers that can't be lost, no telemetry. **Use the
Claude Code teammate** only when other Claude sessions must message it natively
(`ListAgents`/`SendMessage`), and launch it only through `scripts/claude_team.sh`,
which carries the fixes that made it safe. Evidence, friction log and the parity
table: [references/pi-vs-claude.md](references/pi-vs-claude.md) — **add a dated
row after any test of either setup, and update Parity after any config change.**

## Pi extensions

`assets/pi-extensions/` — `statusline.ts`, `write-boundary.ts` (edit/write only
under the launch dir), `permission-gate.ts`, `see.ts` (the `see` tier as a tool).
Install into Pi's agent dir, and after a plugin update `--check`, install, then
`/reload` open Pi sessions:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/local-inference/scripts/install_pi_extensions.sh [--check]
```

## Writing the brief

The local model starts cold and small. The brief must be self-contained:
- Exact files or globs to look at — don't make it explore
- The exact output format (e.g. "one line per file: `path: finding`", or JSON)
- For edits: the exact transformation, one example before/after, and what not to touch
- Keep the input well under the tier's context; split big jobs into several runs

- **Refuse** what you can't verify: root causes, security, design, multi-step
  reasoning, anything whose failure is silent. If the user insists, verify after.
- **Narrative isn't a brief:** over ~2K tokens with no operation verb and under
  two paths, rewrite it as paths + operation + output (one long log to
  summarize is fine — the verb is the signal).
- Summaries keep source URLs inline; fit claims ("X maps onto Y") are hedged
  unless verified; a finding's scope is checked before it is generalized.

## Verify — always

- Read-only answers: spot-check claims against the files (file paths and line numbers exist, quotes match).
- Edits: `git diff` and review every hunk; run the project's build/lint/tests. Revert with `git checkout -- <files>` rather than patching bad output by hand.
- Sums and comparisons: **never trust the model's arithmetic**. Use `jq`, `awk`, `bc`, or bash to compute. The local model has been known to pass wrong totals as correct.
- Classification: if the answer changes behavior (routing, filtering, deletion), verify the label against the criterion. `decide.py` constrains the shape but not the truth.
- Tell the user the work came from the local model and what you checked.
- Control flow in closures: when reviewing edits that move logic into
  closures (`withLock`, `forEach`, `map`), check that returns and guards still
  exit the right scope — a once-per-process guard inside a closure runs every
  iteration.

## Gated edit — Pi with bash under sandbox

When Pi should carry an edit to green itself — edit, run the project's checks,
fix, commit — give it bash only inside `scripts/pi_sandboxed.sh`: one worktree
branch, no other writes, no network but localhost:8000, nothing started outside.
Rerun `pi_sandboxed.sh self-test` (`--live`: the real Pi) when it, macOS or Pi
change. The recipe: **prepare** the worktree outside (deps,
warm build) → **spawn** with `--write <build dir>` → **brief** with the exact
check/build/test commands and "commit only on your branch; never merge, push or
release" → **review** every hunk and run the full gate yourself → **merge**.
App builds go through `sandbox_build_broker.sh`, outside. Details: [references/gated-edit.md](references/gated-edit.md).
