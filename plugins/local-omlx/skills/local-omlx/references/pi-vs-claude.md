# Pi vs Claude Code on oMLX — running comparison

Two ways to put a local oMLX model to work: **Pi** (`pi`, driven one-shot or
in a tmux pane via `scripts/pi_team.sh`) and **Claude Code on oMLX**
(`omlx launch claude --cross-session`, a real peer reachable by
`SendMessage`). Goal: find which is fastest with the least friction, and keep
both configured alike so the comparison is fair.

**Keeping this current:** every test of either setup adds a dated row to
§ Evidence or § Friction log, and any configuration change updates § Parity.
Don't summarize away old rows — the history is how a trend shows.

## Verdict so far (2026-09-30)

Close on results, apart on friction. On the same multi-file edit both
produced the identical correct diff in about the same time (Pi 43 s, Claude
≤53 s). Pi got there with no setup beyond `pi_team.sh`; Claude needed the slim
flags, the reply guard (fired on every edit/answer turn so far but one), and
— after it edited the user's main checkout from a worktree — write
permissions scoped to its own directory. Claude's advantages: native teammate
messaging, and a real write boundary once scoped. Pi's: fewer moving parts,
replies that can't be lost, no telemetry — and, since `write-boundary.ts`, a
write boundary for its edit/write tools too.
**Recommendation: Pi by default; the Claude teammate only when native
cross-session messaging is needed** (recorded in SKILL.md § Which to use).
Long-session result (10-01): a fresh slim teammate with the fixed guard went
7 for 7 — correct, delivered, inside its worktree, 171 s total. Remaining
Claude risks: an unexplained SIGUSR1 kill near the top of an hour (twice),
and a context compaction in run 1 that made it forget its directory (the
write scope held).

## Evidence

Same machine (M5 Pro, 64 GB), same model unless noted
(`Qwen3.6-35B-A3B-oQ4e-mtp:code`), read-only tasks on AudiobookOCD.

| Date | Setup | Task | Time | Correct | Result delivered | Notes |
|---|---|---|---|---|---|---|
| 09-30 | Pi pane | `gate` dependencies from mise.toml | 58 s | yes | yes (session file) | first turn loads AGENTS.md |
| 09-30 | Pi pane | follow-up: what runs in parallel | 27 s | mostly | yes | over-claimed `app:canary` |
| 09-30 | Pi pane (`pi_team.sh`) | `docs` description verbatim | 12 s | yes | yes | |
| 09-30 | Claude, default | `app:test` dependency + description | ~2.5 min | yes | **no** — answered in own pane | 52K-token prompt, re-read in full each request |
| 09-30 | Claude, default | asked to reply via SendMessage | ~1.8 min | — | **no** — auto mode blocked it | classifier unreachable via oMLX |
| 09-30 | Claude, default + `--allowedTools SendMessage` | same task | — | — | **no** — session exited mid-task | cause not found; pane vanished |
| 09-30 | Claude, slim | `app:canary` description verbatim | ~10 s | yes | **yes** (SendMessage) | prompt 6–10K tokens |
| 09-30 | Claude, slim | find "what next" docstring (Grep) | — | — | **no** — never processed | arrived mid-turn while it ran an unrequested backlog review (project SessionStart hook) |
| 09-30 | Claude, slim + `--setting-sources user` | same | ~10 s | yes | **no** — answered in own pane | reply discipline, not permissions |
| 09-30 | Claude, slim + reply guard + tier mapping | `app:canary` description verbatim | ~20 s | yes | **yes** — after the guard blocked one stop | tried ToolSearch first (not in its tool list) |
| 09-30 | Claude, slim + reply guard + tier mapping | find "what next" docstring | ~10 s | yes | **yes** — unprompted | ~7K tokens, 4–5 s per request |
| 09-30 | Pi pane (`pi_team.sh`), own worktree | **edit:** rename `stage_steps`→`parse_stage_steps`, 5 sites / 3 files | 43 s | **exact** — compiles, check-loop passes | yes | 8 tool calls (grep, 3 read, 3 edit, grep) |
| 09-30 | Claude + `--allowedTools Edit` (unscoped), own worktree | same edit | ~43 s | edits right, **wrong tree** | yes (guard fired once) | used absolute paths into the user's main checkout from the start; edited `main` — reverted by the lead |
| 09-30 | Claude + `Edit(//<worktree>/**)` + cwd in brief | same edit | ≤53 s | **exact** — diff identical to Pi's | yes (guard fired once) | 12 tool calls, all inside the worktree |
| 09-30 | same | boundary test: edit a file outside its dir | — | — | yes | blocked (classifier unreachable), file unchanged |
| 09-30 | Claude long run 1 (7 tasks planned, one session, Edit scoped) | tasks 1–3 read, 4 rename | 16/22/16 s, task 4 **301 s** | 4 of 4 | 4 of 4 (guard on 1 and 4) | context **compacted mid task 4**; afterwards it aimed Bash/Write/4× Edit at the user's main checkout — all blocked by the scope/tool list — then edited its worktree correctly. Task 5 arrived mid-turn and was dropped: the guard skipped because it had already fired that turn (fixed: once per task). Then idle until **killed by SIGUSR1 at 07:00:06** |
| 10-01 | Claude long run 2 (fresh session, fixed guard) | 7 tasks: 3 read, rename ×2, recall from memory, summarize a script | 17/14/17/47/9/47/20 s — **171 s total** | **7 of 7** (both renames exact, compile + check-loop pass) | **7 of 7** (guard once, task 1) | no compaction, no tool call aimed outside its worktree; prompt grew 13K→16.5K tokens over the session |
| 09-30 | Pi + `write-boundary.ts` | write inside (relative) / outside (absolute) / `../` escape / same dir via `/tmp` spelling | — | allowed / **blocked** / **blocked** / allowed | yes | outside file unchanged; real-path comparison handles /tmp→/private/tmp |

Claude "slim" = `scripts/claude_team.sh` (brief in `scripts/claude_teammate_brief.txt`):
`--system-prompt <brief> --tools Read,Grep,Glob,ToolSearch,SendMessage --allowedTools SendMessage --strict-mcp-config --disable-slash-commands --setting-sources user`
(the last flag was added after the hook row below).

## Pros and cons

| | Pi | Claude Code on oMLX |
|---|---|---|
| Speed (simple task) | 12–60 s | default ~2 min; slim ~10 s |
| Prompt overhead | ~7K tokens first turn (instructions + AGENTS.md) | default 52–62K; slim 6–10K |
| Native teammate (`ListAgents`/`SendMessage`) | no — `pi_team.sh` is the channel | **yes** |
| Result reliably reaches the lead | **yes** — read from session JSONL | with `reply_guard.py`: 2 of 2 (without: 1 of 4) |
| Permission model | no prompts; `permission-gate` blocks rm -rf/sudo/chmod 777 | auto mode's classifier is server-side → every non-read-only action blocked unless `--allowedTools` |
| Off-task risk | low (Pi has no session hooks) | project SessionStart hook hijacked a turn; needs `--setting-sources user` |
| Stability | no crashes seen | 7-task session clean (10-01); two SIGUSR1 kills near the top of an hour (20:00:02, 07:00:06), cause unknown; survived 09:00 on 10-01, so not every hour |
| Write boundary | `write-boundary.ts`: edit/write only under the launch dir (real-path check); bash not covered | scoped allow rule `Edit(//<dir>/**)`; outside it the unreachable classifier blocks the write; no Bash tool given |
| Path discipline | used relative paths in its worktree | guessed the user's main checkout from context; fixed by putting the working dir in the brief |
| Telemetry | none | `--cross-session` requires Claude Code telemetry and feature flags on |
| Cost display | $0 | shows a fake $ estimate for the unknown model |
| Tool set | read, bash, edit, write, grep, find, ls | full Claude Code tools (trimmed to read-only + messaging in slim) |
| Watching it work | tmux pane, live | tmux pane, live |

## Friction log

- **09-30 Pi:** `pi -p` hangs without a terminal — needs `</dev/null`. Fixed in the skill.
- **09-30 Pi:** `--model omlx/*:deep` sends the wrong limits (`:` read as a thinking level). Use `omlx/<tier>`.
- **09-30 Pi:** `pi_team.sh` first version hung on an empty glob (`cat` with no files reads stdin). Fixed.
- **09-30 Claude:** `omlx launch claude --model X` alone used Qwen3.8 — oMLX's `claude_code.opus_model` setting fills the opus tier, and opus is the default tier. Pass `--opus/--sonnet/--haiku` (or fix the settings — § Parity).
- **09-30 Claude:** auto mode classifier gives no verdict through oMLX → SendMessage, edits, writes blocked.
- **09-30 Claude:** project `.claude/settings.json` SessionStart hook ("backlog review due") steered the teammate off task; a task queued mid-turn was never processed.
- **09-30 Claude:** the local model doesn't reliably end with SendMessage, even when told to. Fixed with `reply_guard.py`, a Stop hook that blocks ending a turn until it has replied.
- **09-30 Claude:** with `--tools` restricting the set, ToolSearch doesn't exist and SendMessage is loaded directly; the brief told it to use ToolSearch and it wasted two calls. Removed from the brief and guard.
- **09-30 Claude — incident:** with `--allowedTools Edit` (unscoped) and launched in a worktree, the teammate used absolute paths into the user's main checkout and edited three files on `main`. The pre-approval removed the outside-the-working-dir check. The lead reverted the three files (the user's `INBOX.md` change untouched). Fixed: `claude_team.sh` scopes write tools to `Edit(//<dir>/**)` and states the working directory in the brief; a boundary test confirmed an outside edit is blocked.
- **09-30/10-01 Claude:** `reply_guard.py` blocked only once per *turn* (stop_hook_active), so a task queued mid-turn after a block went unanswered. Fixed: once per *task* (it looks for its own earlier block after the task).
- **09-30/10-01 Claude:** a context compaction mid-task dropped the working directory from the model's memory; it reverted to the user's main checkout paths. The scoped `Edit` rule and missing Bash/Write blocked every attempt. Why it compacted at a ~16K-token context is unexplained.
- **09-30/10-01 Claude:** teammate killed by SIGUSR1 at 20:00:02 and 07:00:06, idle the second time. No cron/launchd job or Claude/Homebrew update found at those times. Open.
- **10-01 Claude:** `omlx launch claude` runs Claude Code 2.1.270 from `~/.local/share/claude`, while `claude` on PATH is Homebrew's 2.1.284 — the teammate is two versions behind the lead.
- **09-30 Claude:** after mapping opus→`:deep`, launching without a tier starts the teammate on deep (the user's default Claude tier is opus). `claude_team.sh` passes `--model sonnet`.
- **09-30 Claude:** each request re-read the whole prompt (`reused 0` in oMLX's log) — no prefix-cache reuse between turns. Not yet checked for Pi.

## Parity — configure both alike

| Aspect | Pi | Claude Code on oMLX | Aligned? |
|---|---|---|---|
| Tiers | fast/code/deep by name (`~/.pi/agent/models.json`) | haiku→`:fast`, sonnet→`:code`, opus→`:deep` in oMLX's `claude_code` settings; starts on sonnet, `/model` switches | yes (09-30) |
| Default model | `:code` | `:code` (via launch flags) | yes |
| Instructions | Pi prompt + AGENTS.md/CLAUDE.md auto-loaded | slim: short teammate brief; user CLAUDE.md | **no** — decide one brief and give it to both |
| Skills | personal (terminal-guru, chronicle, skillsmith) + project swift-dev | disabled (`--disable-slash-commands`) | **no** |
| Tools | read, bash, edit, write, grep, find, ls | slim: Read, Grep, Glob (+ messaging) | **no** — Claude is read-only |
| Safety | `write-boundary.ts` + permission-gate (rm -rf, sudo, chmod 777) | user hooks (bash-firewall) + scoped allowlist | yes for edit/write (09-30); Pi's bash can still write anywhere, Claude's teammate has no Bash |
| Session hooks | none | user hooks only (`--setting-sources user`) | yes, after the fix |
| Status line | `statusline.ts` mirroring Claude's | user's statusline | yes |
| Teammate channel | `pi_team.sh` spawn/ask/close | `claude_team.sh` spawn, then `ListAgents`/`SendMessage`; close the pane by hand | different by nature |
| Reply guarantee | structural (session file) | `reply_guard.py` Stop hook | yes (09-30) — different mechanism, same effect |

## Next tests

1. ~~Stop hook~~ and ~~tier mapping~~ — done 09-30.
2. ~~Longer Claude session~~ — done 10-01: 7/7 in run 2. Still open: the top-of-hour SIGUSR1 kill.
3. ~~Same edit task on both~~ — done 09-30: identical diffs, Pi 43 s, Claude ≤53 s.
3a. ~~Pi write boundary~~ — done 09-30 (`~/.pi/agent/extensions/write-boundary.ts`).
4. Prefix-cache reuse for Pi turns (oMLX log `reused N`) vs Claude's `reused 0`.
5. Give both the same instruction set (decide: AGENTS.md vs a short brief) and the same skills.
