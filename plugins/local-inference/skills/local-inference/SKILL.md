---
name: local-omlx
description: This skill should be used when the user says "use pi", "use the local model", "offload this to pi", "run it locally", "local teammate", "claude on omlx", "update the local model tiers", "a new local model came out", "decide locally", "classify these", "spawn a pi teammate", "pi in a tmux pane", or when a quick constrained judgment (pick a label, yes/no, extract fields into JSON) is needed, or when a mechanical, well-specified task (bulk reading or summarizing files or logs, first-pass triage, extracting facts from many files, repetitive edits with an exact spec) can run on a local oMLX model — via Pi or via Claude Code launched on oMLX — instead of spending Claude tokens. Do NOT use for root-cause debugging, design decisions, security-sensitive changes, or anything whose failure is silent — local models are wrong more often and their output must be verified.
metadata:
  version: "1.1.1"
compatibility: macOS on Apple silicon; oMLX server on 127.0.0.1:8000; pi; tmux 3.5+ for pane teammates; uv for the Python scripts
license: MIT
---

# local-omlx

Two ways to run work on the local oMLX models, both sharing the same tiers:

- **Pi** (`pi`) — a coding agent with an `omlx` provider
  (`~/.pi/agent/models.json`), run one-shot or as a pane teammate.
- **Claude Code on oMLX** — `omlx launch claude`, a real cross-session teammate
  (`scripts/claude_team.sh`; see § Pi vs Claude Code on oMLX).

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
S=${CLAUDE_PLUGIN_ROOT}/skills/local-omlx/scripts/decide.py
$S --choices bug,improvement --system "Classify the backlog item." "<text>"
$S --choices yes,no --system "<the criterion, stated exactly>" "<text>"
$S --schema fields.json "<text to extract from>"      # JSON Schema file
cat item.txt | $S --choices a,b,c --system "..."      # question from stdin
```

- Always give the criterion in `--system`, including what each choice means, and say how to treat the ambiguous case — the measured 93% on 11-way area classification was with a one-line definition per area, and an exact bug/improvement definition gained 2–3 items in 45.
- It was right 69–93% of the time on real judgment calls, depending on the question (see references/tiers.md). Use it to sort, route and pre-filter; verify any decision that changes something.
- Many decisions → loop in the shell; each call is independent and fast.

## Teammate — Pi in its own tmux pane

For a multi-turn conversation the user can watch (and type into), run Pi
interactively in a pane beside this one instead of one-shot `pi -p`:

```bash
T=${CLAUDE_PLUGIN_ROOT}/skills/local-omlx/scripts/pi_team.sh
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
  directory (or worktree) it should change. The bash tool is not covered;
  `permission-gate` only blocks rm -rf / sudo / chmod 777. Close the pane when done.

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
launch dir) and `permission-gate.ts`. Pi finds extensions in its own agent dir,
so install them there:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/local-omlx/scripts/install_pi_extensions.sh --check   # what would change
${CLAUDE_PLUGIN_ROOT}/skills/local-omlx/scripts/install_pi_extensions.sh           # copy; changed files keep a .bak
```

Target is `${PI_CODING_AGENT_DIR:-~/.pi/agent}/extensions` — Pi does not read
XDG paths; to keep Pi's config under `$XDG_CONFIG_HOME`, set
`PI_CODING_AGENT_DIR=$XDG_CONFIG_HOME/pi/agent`. Updates are deliberate: after the
plugin updates, run `--check`, then install, then `/reload` in open Pi sessions.

## Writing the brief

The local model starts cold and small. The brief must be self-contained:
- Exact files or globs to look at — don't make it explore
- The exact output format (e.g. "one line per file: `path: finding`", or JSON)
- For edits: the exact transformation, one example before/after, and what not to touch
- Keep the input well under the tier's context; split big jobs into several runs

## Verify — always

- Read-only answers: spot-check claims against the files (file paths and line numbers exist, quotes match).
- Edits: `git diff` and review every hunk; run the project's build/lint/tests. Revert with `git checkout -- <files>` rather than patching bad output by hand.
- Tell the user the work came from the local model and what you checked.
