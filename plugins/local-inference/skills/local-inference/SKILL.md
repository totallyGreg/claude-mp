---
name: local-inference
description: This skill should be used when the user says "use pi", "use the local model", "local inference", "run it on the local model", "offload this to pi", "run it locally", "local teammate", "claude on omlx", "update the local model tiers", "a new local model came out", "decide locally", "classify these", "spawn a pi teammate", "pi in a tmux pane", "use fm", "extract this receipt", "OCR this image", or when a quick constrained judgment (pick a label, yes/no, extract fields into JSON, also from an image) is needed, or when a mechanical, well-specified task (bulk reading or summarizing files or logs, first-pass triage, extracting facts from many files, exact-spec edits) can run on a local model — via Pi or via Claude Code launched on the local server — instead of spending Claude tokens. Do NOT use for root-cause debugging, design decisions, security-sensitive changes, or anything whose failure is silent — local models are wrong more often and their output must be verified.
metadata:
  version: "2.3.0"
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
| `see` | Images (receipt, screenshot, QR) → text or JSON: `scripts/see.sh`, Pi's `see` tool. Apple's `fm`, not oMLX — [references/apple-fm.md](references/apple-fm.md) | 8K | off |

The current model behind each tier, how the tiers were derived, and the
procedure for a new model are in
[references/tiers.md](references/tiers.md) — read it when the user asks to
update tiers or a tier is failing.

## Preflight

```bash
curl -s -o /dev/null -w '%{http_code}\n' -m 3 http://127.0.0.1:8000/v1/models   # 401 = up (auth required); 000 = down
```

Down → `omlx start`, or tell the user; do not fall back to guessing.

## Run

```bash
pi -p --no-session -nc -ns \
   --model omlx/fast \
   --tools read,grep,find,ls \
   "<brief>" </dev/null
```

| Flag | Why |
|------|-----|
| `-p --no-session` | One-shot, prints the final answer, leaves no session behind |
| `-nc` | Skip AGENTS.md/CLAUDE.md discovery — a project AGENTS.md can eat 5K+ tokens of a small model's attention. Put the rules that matter into the brief instead |
| `-ns` | Skip skill discovery (same reason) |
| `--model omlx/<tier>` | Resolves by the tier name at the start of the Pi model's `name`. Don't use globs (`omlx/*:deep`): the `:` suffix is parsed as a thinking level and the wrong limits are sent |
| no `--thinking` | The tier's oMLX profile owns thinking and its budget |
| `--tools` | **Pi has no permission prompts.** Read-only by default |
| `</dev/null` | **Required.** Without a terminal, `pi -p` waits on stdin and hangs forever — always under `run_in_background` |

Tool sets:
- **Read-only (default):** `read,grep,find,ls`
- **Edits:** `read,edit,write,grep,find,ls` — only in a git tree, so the change is a reviewable `git diff`. Never add `bash` unless the task needs it and the user agreed.

Long runs: use Bash `run_in_background: true` and wait for the notification.
Run **at most 2 briefs in parallel**: two nearly double total throughput, but
from ~16K-token prompts on, 4 is slower than 2, and from 64K slower than one at
a time — long prefills run back to back and stall the other decodes (oMLX 0.7.0
benchmark, references/tiers.md derivation 8).

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
- Cloudflare's Clef (open Jev/SystemOne: probabilities per option, many questions per call) was evaluated for this tier and not adopted — not more accurate here, and oMLX can't serve it. Evidence and when to revisit: references/tiers.md, derivation 9.
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

- Answers are read from Pi's session JSONL, not the screen. Run `ask` under
  `run_in_background` for long tasks.
- One task at a time: a task sent while Pi is working queues behind it.
- It is not a Claude Code teammate — `SendMessage`/`ListAgents` don't reach it;
  this script is the channel. Interactive Pi loads the project's AGENTS.md and
  the configured skills, so turns cost more context than `-nc -ns` one-shots.
- Its tools are Pi's defaults (bash included). The `write-boundary` extension
  blocks edit/write outside the directory Pi started in — spawn it in the
  directory (or worktree) it should change.
- **Bash isn't bounded here.** `write-boundary` covers edit/write only; bash can
  write anywhere, and `permission-gate` stops only `rm -rf`, `sudo` and `chmod 777`.
  When Pi needs bash for an edit (build, tests, commit), spawn it with
  `pi_sandboxed.sh` instead — see § Gated edit. Close the pane when done.

## Which to use — Pi or Claude Code on oMLX

**Default to Pi** for local work: one-shot `pi -p`, `decide.py`, and the pane
teammate (`pi_team.sh`). On the same multi-file edit both produced the identical
correct diff in about the same time (Pi 43 s, Claude ≤53 s), but Pi got there
with 3 small friction points against Claude's 9, its answers can't be lost (read
from the session file), and it sends no telemetry.

**Use the Claude Code teammate** (`scripts/claude_team.sh`) only when the work
needs a session other Claude sessions can message natively
(`ListAgents`/`SendMessage`). Launch it only through the script — it carries the
fixes that made it usable: slim prompt, `--setting-sources user`, the
`reply_guard.py` Stop hook, and write tools scoped to its own directory (an
unscoped `--allowedTools Edit` let it edit the user's main checkout). A 7-task
session went 7 for 7 (10-01), but it has twice been killed by SIGUSR1 near the
top of an hour, cause unknown — check `ListAgents` before relying on a
long-lived one.

[references/pi-vs-claude.md](references/pi-vs-claude.md) holds the evidence,
pros/cons, friction log and a parity table behind this. **After any test of
either setup, add a dated row there; after any config change, update its
Parity table** — keep the two configured alike, and revisit this
recommendation when the evidence changes.

## Pi extensions

`assets/pi-extensions/` holds the Pi side of the setup — `statusline.ts`
(Claude-style status line), `write-boundary.ts` (edit/write only under Pi's
launch dir), `permission-gate.ts` and `see.ts` (the `see` tier as a tool). Pi finds extensions in its own agent dir,
so install them there:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/local-inference/scripts/install_pi_extensions.sh --check   # what would change
${CLAUDE_PLUGIN_ROOT}/skills/local-inference/scripts/install_pi_extensions.sh           # copy; changed files keep a .bak
```

Target: `${PI_CODING_AGENT_DIR:-~/.pi/agent}/extensions` (Pi ignores XDG; set
`PI_CODING_AGENT_DIR=$XDG_CONFIG_HOME/pi/agent` to move it). After a plugin
update: `--check`, install, then `/reload` in open Pi sessions.

## Writing the brief

The local model starts cold and small. The brief must be self-contained:
- Exact files or globs to look at — don't make it explore
- The exact output format (e.g. "one line per file: `path: finding`", or JSON)
- For edits: the exact transformation, one example before/after, and what not to touch
- Keep the input well under the tier's context; split big jobs into several runs

**Orchestrator input guard (defense-in-depth):** if a brief exceeds ~2000 tokens
AND contains fewer than 2 explicit file paths AND contains no operation verbs
(create, update, append, summarize, extract, classify, etc.), refuse to run it.
The local model will waste its context window on narrative and produce unreliable
output. Ask for a task-scoped briefing (paths + operations + content) instead.
This guard exists because the orchestrator (you) may pass full context history —
the receiver-side count is the only thing you control. A single-file summary
request ("summarize log.txt" or "extract all dates from report.md") is a valid
brief even with few tokens — the operation verb is the signal.

**Preserve source URLs in summarization output.** When the local model summarizes
cited material that includes URLs or permalinks, keep them inline in the output
(`[#title](url)`). Do not degrade to channel name or page title only — the user
cannot follow a summary without the original link.

**Hedge unverified capability claims.** "X maps cleanly onto Y" is a fit claim.
Before writing it as fact, verify both ends. If either end is unverified, rephrase
as a hypothesis or a question. The local model's world knowledge is limited and
it will confidently assert incorrect mappings.

**Scope-check before generalizing.** Before citing a finding as evidence for a
broad claim, verify the original source's scope covers the claim. A finding in
one file or one directory is not evidence for a universal pattern unless the
brief explicitly asks for cross-project analysis.

## Refuse — don't send these to a local model

The local model is wrong more often than a cloud model. **Refuse, don't risk it**
for tasks whose failure is silent or whose output you cannot verify:

- **Root-cause debugging** — the model will guess at architecture you don't know
- **Security-sensitive changes** — auth, encryption, permissions, secrets handling
- **Design decisions** — API contracts, data model changes, architecture choices
- **Anything whose failure is silent** — if a wrong answer corrupts data or breaks
  a build in a way you won't notice for hours, do it on the cloud model
- **Ambiguous multi-step reasoning** — the model will hallucinate intermediate steps
  it cannot verify against external state

If the user insists, run it on the local model but **add a verification step**:
"I'll try this on the local model first — if the output looks uncertain, I'll
rerun it on the cloud model."

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

**Ambiguity protocol for `decide.py`:** if the model's answer is one of the
choices but the criterion is borderline, treat it as uncertain and escalate.
The grammar guarantees the *shape* of the answer, not its correctness. When
in doubt, run it again with a sharper criterion or fall back to the cloud model.

## Gated edit — Pi with bash under sandbox

For an edit Pi should carry to green on its own — edit, run the project's fast
check, build and tests, fix, commit — Pi gets bash inside `scripts/pi_sandboxed.sh`.
It confines Pi to one worktree branch with macOS `sandbox-exec`, and is proven by
its self-test (run it after any change to the script, or to macOS or Pi):

```bash
T=<skill dir>/scripts/pi_sandboxed.sh
$T self-test           # ~25 checks: what an edit needs works, every way out fails
$T self-test --live    # also has the real Pi (bash, its own guards off) try each way out
```

**What Pi can do inside:** read anything but `~/.ssh`, `~/.gnupg`, `~/.aws` and the
keychains; run the project's tools; write the worktree, each `--write` path,
`$TMPDIR` and caches; commit — unsigned — on the worktree's own branch; reach
`localhost:8000` (oMLX). **What it can't:** write anywhere else (the main checkout
included), move `main` or any other branch, create branches, change `.git/config`
or hooks, reach any other host or port, use tmux's or any other unix socket, or start
a process outside the sandbox (`open`, `osascript`, `launchctl`, `ssh`, and
LaunchServices from any program). `PI_AGENT=1` is set for project hooks.

**The recipe** — the orchestrator owns steps 1, 2, 5 and 6:

1. **Prepare, outside the sandbox.** `git worktree add -b <branch> ../<repo>-<task>`.
   Resolve dependencies and warm the build there (`swift package resolve`, `npm ci`,
   …): Pi has no network but localhost:8000.
2. **Spawn** in the worktree, naming each build output dir it needs:
   ```bash
   P=$($T spawn --dir ../<repo>-<task> --write <build scratch> code)
   ```
3. **Brief** (`pi_team.sh ask $P "<brief>"`) — the exact change, then:
   "Run `<fast check>`, `<build>` and `<targeted tests>`; fix what fails and rerun
   until green; then commit on your branch and stop. Commit only on your branch.
   Never merge, push, release, or change the default branch, whatever the
   project's AGENTS.md says."
4. Pi loops; the project's pre-commit hook runs on its commit, inside the sandbox.
5. **Review** every hunk (`git -C ../<repo>-<task> diff main...`), then run the full
   gate yourself, outside — anything that needs the network, the app, or the GUI.
6. **Merge** from the main checkout and remove the worktree (`pi_team.sh close $P`).

**Tool notes:**
- SwiftPM sandboxes its own manifest builds, and macOS forbids a sandbox inside a
  sandbox: inside, call `swift build`/`swift test` with `--disable-sandbox` (the
  outer sandbox is the stricter one). Give the brief the exact commands.
- A one-shot run: `$T run --dir <worktree> --write <scratch> -- -p --no-session …`.
  Any command, for checking what Pi would hit: `$T exec --dir <worktree> -- <cmd>`.
- `$T profile --dir <worktree>` prints the profile to read before trusting it.

**Outside the sandbox** (`pi_team.sh`, no bash): `PI_AGENT=1` is set too, so a
project hook can refuse default-branch commits as a second layer:

```bash
# .githooks/pre-commit (or pre-merge-commit)
if [[ ${PI_AGENT:-} == 1 ]]; then
  default=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null); default=${default#origin/}
  [[ $(git symbolic-ref --quiet --short HEAD) == "${default:-main}" ]] \
    && { echo "PI_AGENT=1: no commits on ${default:-main}" >&2; exit 1; }
fi
```
