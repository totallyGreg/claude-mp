# local-inference

Delegate work from Claude Code to models running on your Mac, by task tier rather than by model or tool. The current stack is the [oMLX](https://github.com/jundot/omlx) server plus two agents that share its tiers:

- **Pi** (`pi`) — one-shot briefs (`pi -p`), or a teammate in its own tmux pane driven by `pi_team.sh`.
- **Claude Code on oMLX** — `omlx launch claude --cross-session`, a real teammate reachable with `ListAgents`/`SendMessage`, launched slim by `claude_team.sh`.

Claude Code on Anthropic's models stays the orchestrator: it writes the brief, runs the local agent, and verifies the result.

<!-- BEGIN AUTOGEN:overview (managed by skillsmith --update-components; edits overwritten) -->
## What's inside

Delegate work to local models on Apple silicon (task tiers, Pi and Claude Code teammates on oMLX), and set up and audit Claude-Code-only OpenRig rigs.

**At a glance:** 2 skills

## Install

```
/plugin marketplace add totallyGreg/claude-mp
/plugin install local-inference@totally-tools
```
<!-- END AUTOGEN:overview -->

## Tiers

Tiers are defined by task; the model behind each changes as better ones arrive. Each is an oMLX profile exposed as a model (`<model>:<tier>`).

| Tier | For | Pi | Claude Code on oMLX |
|------|-----|----|---------------------|
| `fast` | mechanical reading, extraction, exact-spec edits | `omlx/fast` | haiku |
| `code` | agentic loops, multi-file edits | `omlx/code` | sonnet |
| `deep` | one hard question | `omlx/deep` | opus |
| `decide` | one grammar-constrained answer (label, yes/no, JSON) | `scripts/decide.py` | — |

`skills/local-inference/references/tiers.md` records the current mapping, how it was measured, and the procedure for adopting a new model.

## Which to use

**Pi by default.** On the same multi-file edit both produced the identical diff in about the same time, but Pi needed far less setup, its answers can't be lost, and it sends no telemetry. **The Claude Code teammate** when another Claude session needs to message it natively. `skills/local-inference/references/pi-vs-claude.md` is the running comparison — evidence, friction log, and a parity table.

<!-- BEGIN AUTOGEN:components (managed by skillsmith --update-components; edits overwritten) -->
## Components

### Skills (2)

| Skill | Description |
|-------|-------|
| `local-inference` | Delegate work to models running on this Mac, picked by task tier, not by model or tool. |
| `openrig-setup` | Install OpenRig, give a project a rig that boots, and prove it with a read-only audit. |
<!-- END AUTOGEN:components -->

## Scripts and Pi extensions

| Path | What |
|------|------|
| `skills/local-inference/scripts/decide.py` | One constrained answer from the `decide` tier |
| `skills/local-inference/scripts/pi_team.sh` | Pi teammate in a tmux pane: `spawn`, `ask`, `close` |
| `skills/local-inference/scripts/claude_team.sh` | Claude Code on oMLX as a teammate: slim prompt, scoped write tools, reply guard |
| `skills/local-inference/scripts/reply_guard.py` | Stop hook: the teammate can't end a turn without replying |
| `skills/local-inference/scripts/install_pi_extensions.sh` | Copies the Pi extensions into Pi's agent dir; `--check` shows what would change |
| `skills/local-inference/scripts/bench_decode.py`, `eval_decide.py` | Speed and decision-accuracy measurements for new models |
| `skills/local-inference/assets/pi-extensions/statusline.ts` | Claude-style status line for Pi |
| `skills/local-inference/assets/pi-extensions/write-boundary.ts` | Pi's edit/write only under its launch directory |
| `skills/local-inference/assets/pi-extensions/permission-gate.ts` | Asks before recursive deletes, sudo, or chmod 777 |
| `skills/openrig-setup/mise-tasks/openrig/{check.sh,new.py,convert.py}` | mise file tasks `openrig:check` (read-only audit), `openrig:new` (scaffold a `claude-pi` or `pi-solo` rig), `openrig:convert` (library starter → Claude-only spec) |
| `skills/openrig-setup/scripts/install_mise_tasks.sh` | Copies the openrig tasks into the global mise tasks dir; `--check` shows what would change |

## Setup

1. oMLX running on `127.0.0.1:8000` with the tier profiles (`references/tiers.md`).
2. `~/.pi/agent/models.json` with the `omlx` provider and the tier entries.
3. Install the Pi extensions into Pi's agent dir (`${PI_CODING_AGENT_DIR:-~/.pi/agent}/extensions`):
   ```bash
   skills/local-inference/scripts/install_pi_extensions.sh
   ```
   Re-run after plugin updates (`--check` first). Pi doesn't read XDG paths; set `PI_CODING_AGENT_DIR` to move its config.

## Skill: local-inference

### Current Metrics

**Score: 96/100** (Excellent) — 2026-10-01

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 93 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 2.0.0 | 2026-10-01 | [#198](https://github.com/totallyGreg/claude-mp/issues/198) | Renamed `local-omlx` → `local-inference`; product-neutral description and intro (tiers stay, the stack underneath changes); TurboQuant KV 8-bit on `deep` tested and rejected; 0.7.0 memory-guard ceiling recorded. Description 80 → 100. | 93 | 90 | 100 | 100 | 100 | 96 |
| 1.1.0 | 2026-10-01 | - | Pi extensions moved into `assets/pi-extensions/`; `install_pi_extensions.sh` copies them into Pi's agent dir (`${PI_CODING_AGENT_DIR:-~/.pi/agent}`) instead of Pi loading them from the marketplace clone. Score 94 (no change). +v1.1.1 | 93 | 90 | 100 | 100 | 80 | 94 |
| 1.0.0 | 2026-10-01 | [#196](https://github.com/totallyGreg/claude-mp/issues/196) | Initial release, moved from a personal skill: fast/code/deep/decide tiers on oMLX profiles; Pi one-shots and pane teammate (`pi_team.sh`); Claude Code on oMLX as a cross-session teammate (`claude_team.sh` + `reply_guard.py`, write tools scoped to its directory); `decide.py`, `bench_decode.py`, `eval_decide.py`; Pi vs Claude comparison and tier derivation references. | 93 | 90 | 100 | 100 | 80 | 94 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

## Changelog

| Version | Date | Summary |
|---------|------|---------|
| 2.4.4 | 2026-10-02 | `local-inference` 2.0.1: Cloudflare's Clef (open Jev/SystemOne decision model) evaluated for `decide` and not adopted — no accuracy gain on 45 BACKLOG items, oMLX can't serve it; evidence and when to revisit in tiers.md derivation 9, re-run with the new `scripts/eval_clef.py`. `decide` guidance: wording moved area accuracy 42 → 37 on the same model, so compare models only on identical wording. |
| 2.4.3 | 2026-10-02 | `openrig-setup` 1.3.3: lifecycle lessons from a full stop/`rig start --last` (never `rig down kernel` — once stopped by hand only `rig up kernel --existing` restores it; the `phase=connections` shutdown timeout is harmless; seats resume but auto mode doesn't) in new `references/lifecycle.md`, plus committing the setup to a branch for worktrees. `openrig:new` writes `openrig-specs/.gitignore` and marks a tracked `AGENTS.md` skip-worktree for native Pi seats. `openrig:check` prints the daemon-restart hint only when the reload check warns. |
| 2.4.2 | 2026-10-02 | `openrig-setup` 1.3.2: `openrig:new` names a reused worktree's actual branch in the briefs (it used today's date, so a regenerated rig's lead saw a branch that didn't exist). Skill: RTK rewrites read-only commands to `rtk …` and so multiplies the lead's permission prompts — allow both spellings; `cd && git` compounds still need a human or auto mode. |
| 2.4.1 | 2026-10-02 | `openrig-setup` 1.3.1: `openrig:new` merges the lead's `.claude/settings.local.json` instead of overwriting it, so regenerating a rig in place (e.g. switching its coder to `--pi native`) keeps the user's allow rules. |
| 2.4.0 | 2026-10-02 | `openrig-setup` 1.3.0: `openrig:new --pi native` runs the coder on OpenRig's native `pi` runtime (state, session, restore and handover tracked) — a slim `agents/pi-coder` AgentSpec carries the brief, and the scaffold links your `models.json` into the seat's per-seat Pi agent dir, which OpenRig can't provision. `openrig:check` fails a native seat without it. Skill: terminal vs native tradeoffs; start the daemon from a stable directory (a deleted cwd makes preflight reject every pi seat); `uses.hooks`/`resources.hooks` were removed from AgentSpec — use `plugins`. |
| 2.3.0 | 2026-10-02 | `openrig-setup` 1.2.0: the `claude-pi` lead now runs in the rig folder (`cwd: "."`) with the repo in `permissions.additionalDirectories` — OpenRig rewrites its cwd's status line (to one that prints nothing), hooks, settings and CLAUDE.md on every boot, which blanked the status bar of the user's own sessions in the repo root. `openrig:check` warns on a Claude seat whose cwd is the repo root; the installer skips iCloud sync-conflict copies. |
| 2.2.0 | 2026-10-01 | `openrig-setup` 1.1.0: scripts become mise file tasks (`openrig:check`, `openrig:convert`, new `openrig:new` scaffold for `claude-pi` / `pi-solo` rigs with worktree + briefs), installed globally by `install_mise_tasks.sh`. Skill adds rig shapes, naming, start/switch/retire, what a Claude seat writes into its cwd, permission allow rules, and keeping one AGENTS.md (CLAUDE.md symlinked to it). The check now fails a terminal seat whose `send_text` is prose instead of a command. |
| 2.1.0 | 2026-10-01 | New `openrig-setup` skill: install, configure and audit OpenRig for a project with Claude Code only (no Codex). `openrig_check.sh` read-only audit; `claude_only_spec.py` converts a library starter (Codex → claude-code, `local:` → `path:` refs, `cwd` → repo root). Distilled from openrig.dev docs by Pi (`omlx/fast`) and checked against the 0.5.17 CLI and validator. |
| 2.0.0 | 2026-10-01 | Renamed from `local-omlx` to `local-inference`: the job stays, the tools under it change ([#198](https://github.com/totallyGreg/claude-mp/issues/198)). Reinstall as `local-inference@totally-tools`. Also records the TurboQuant KV 8-bit test on `deep` (rejected: decode halved, TTFT +23%, memory higher) and the 0.7.0 memory-guard ceiling. |
| 1.1.1 | 2026-10-01 | oMLX 0.7.0 measured on this machine (35B: prefill +93%, decode +29%; Qwen3.8-27B: +51%, +78%); from the r/oMLX 0.7.0 benchmark: at most 2 parallel briefs, TurboQuant KV 8-bit and Splash noted as candidates, decide determinism checked. |
| 1.1.0 | 2026-10-01 | Pi extensions moved from a top-level `pi/` dir (not a plugin component Claude Code recognizes, and it tied Pi to the marketplace clone's path) into the skill's `assets/pi-extensions/`, with `install_pi_extensions.sh` copying them into Pi's own agent dir. |
| 1.0.0 | 2026-10-01 | Initial release: the personal `local-omlx` skill moved into the marketplace, with the Pi extensions that pair with it ([#196](https://github.com/totallyGreg/claude-mp/issues/196)). |

## License

MIT
