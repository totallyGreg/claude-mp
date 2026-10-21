# local-inference

Delegate work from Claude Code to models running on your Mac, by task tier rather than by model or tool. The current stack is the [oMLX](https://github.com/jundot/omlx) server plus two agents that share its tiers:

- **Pi** (`pi`) — one-shot briefs (`pi -p`), or a teammate in its own tmux pane driven by `pi_team.sh`.
- **Claude Code on oMLX** — `omlx launch claude --cross-session`, a real teammate reachable with `ListAgents`/`SendMessage`, launched slim by `claude_team.sh`.

Claude Code on Anthropic's models stays the orchestrator: it writes the brief, runs the local agent, and verifies the result.

**openrig-setup** puts those agents into a long-lived [OpenRig](https://openrig.dev) rig — a Claude Code lead with a Pi coder (`claude-pi`) or Pi alone (`pi-solo`) — scaffolded by `openrig:new` and audited read-only by `openrig:check`.

<!-- BEGIN AUTOGEN:overview (managed by skillsmith --update-components; edits overwritten) -->
## What's inside

Delegate work to local models on Apple silicon (task tiers, Pi and Claude Code teammates on oMLX, Apple's on-device fm), and set up and audit Claude-Code-only OpenRig rigs.

**At a glance:** 2 skills

## Install

```
/plugin marketplace add totallyGreg/claude-mp
/plugin install local-inference@totally-tools
```
<!-- END AUTOGEN:overview -->

## Tiers

Tiers are defined by task; the model behind each changes as better ones arrive. Each except `see` is an oMLX profile exposed as a model (`<model>:<tier>`).

| Tier | For | Pi | Claude Code on oMLX |
|------|-----|----|---------------------|
| `fast` | mechanical reading, extraction, exact-spec edits | `omlx/fast` | haiku |
| `code` | agentic loops, multi-file edits | `omlx/code` | sonnet |
| `deep` | one hard question | `omlx/deep` | opus |
| `decide` | one grammar-constrained answer (label, yes/no, JSON) | `scripts/decide.py` | — |
| `see` | image → text or JSON (receipt, screenshot, QR); Apple's on-device `fm` | `fm respond` | — |

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
| `skills/local-inference/scripts/see.sh` | The `see` tier: image → JSON/text/payload with Apple's `fm` (OCR + schema, plain vision, barcode; `--with-text` returns what OCR read) |
| `skills/local-inference/scripts/pi_team.sh` | Pi teammate in a tmux pane: `spawn`, `ask`, `close` |
| `skills/local-inference/scripts/pi_sandboxed.sh` | Pi with bash confined to one worktree branch (`sandbox-exec`): `run`, `spawn` (drive with `pi_team.sh`), `exec`, `profile`, `self-test` |
| `skills/local-inference/scripts/sandbox_build_broker.sh` | Builds a sandboxed agent asks for, run outside it (Xcode needs LaunchServices): named builds only, a snapshot only the broker writes, refused when the tree changes build files (per-ecosystem presets, auto-detected) or macro code |
| `skills/local-inference/scripts/agent_sandbox_selftest.sh` | Proves each sandbox and broker rule both ways; `--live` has the real Pi try every escape |
| `skills/local-inference/scripts/agent_sandbox.sh` | The harness-agnostic sandbox: any agent or command, one worktree branch, secrets dropped from its environment |
| `skills/local-inference/scripts/claude_team.sh` | Claude Code on oMLX as a teammate: slim prompt, scoped write tools, reply guard |
| `skills/local-inference/scripts/reply_guard.py` | Stop hook: the teammate can't end a turn without replying |
| `skills/local-inference/scripts/install_pi_extensions.sh` | Copies the Pi extensions into Pi's agent dir; `--check` shows what would change |
| `skills/local-inference/scripts/bench_decode.py`, `bench_parallel.py`, `kv_probe.py`, `eval_decide.py`, `eval_clef.py` | Speed (single request, and N concurrent at a given prompt size), one long request per KV-compression setting (TTFT, decode, peak memory, recall), and decision-accuracy measurements for new models (`eval_decide.py … fm` measures Apple's on-device model); `eval_clef.py` for Clef/Jev-style decision models |
| `skills/local-inference/assets/pi-extensions/statusline.ts` | Claude-style status line for Pi |
| `skills/local-inference/assets/pi-extensions/write-boundary.ts` | Pi's edit/write only under its launch directory |
| `skills/local-inference/assets/pi-extensions/permission-gate.ts` | Asks before recursive deletes, sudo, or chmod 777 |
| `skills/local-inference/assets/pi-extensions/see.ts` | `see` tool: gives Pi's text-only tiers eyes through `see.sh` (installed next to it) |
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
4. For rigs: install the `openrig:*` mise tasks into the global mise tasks dir, then follow `skills/openrig-setup/SKILL.md`:
   ```bash
   skills/openrig-setup/scripts/install_mise_tasks.sh
   ```
   Re-run after plugin updates (`--check` first).

## Skill: local-inference

### Current Metrics

**Score: 97/100** (Excellent) — 2026-10-15

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 98 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 2.4.0 | 2026-10-21 | [#230](https://github.com/totallyGreg/claude-mp/issues/230) | oMLX 0.7.1 re-baseline (tiers.md derivation 11): no single-request gain over 0.7.0 on this Mac; parallel requests add ~no throughput with MTP on (prefills queue, MTP batches ≤ 2), so SKILL.md now says one at a time instead of "at most 2". New `scripts/bench_parallel.py`. Affine4/Affine8 KV compression on `deep` tested and rejected (derivation 12, new `scripts/kv_probe.py`). | 98 | 90 | 100 | 100 | 100 | 97 |
| 2.3.0 | 2026-10-15 | [#213](https://github.com/totallyGreg/claude-mp/issues/213) | Pi can be given bash for a gated edit: `pi_sandboxed.sh` rewritten (2.6.0's couldn't start Pi) to confine it to one worktree branch — no other writes, no network but the model port, no unix sockets, LaunchServices or AppleEvents — `sandbox_build_broker.sh` runs app builds outside on request (named builds, a broker-only snapshot, build files refused by ecosystem preset), `agent_sandbox.sh` is the harness-agnostic layer under Pi's launcher, and `agent_sandbox_selftest.sh` proves each rule both ways, `--live` with the real Pi. New `references/gated-edit.md` holds the recipe; SKILL.md back under 2K tokens (sections 12 → 9). Includes 2.2.0's guardrails (Refuse, input guard, `decide.py` caps). +v2.2.0 | 98 | 90 | 100 | 100 | 100 | 97 |
| 2.1.0 | 2026-10-13 | [#210](https://github.com/totallyGreg/claude-mp/issues/210) | Apple `fm` (macOS 27 on-device model) as the backend of a new `see` tier (image → text/JSON); new `references/apple-fm.md`: OCR + schema for text in images, plain `--image` for charts, Apple's schema dialect (enum works, JSON Schema rejected), 8K shared context, dash-leading input trap, `fm serve` streams by default. Receipt → JSON verified here. `scripts/see.sh` + Pi `see` tool ([#212](https://github.com/totallyGreg/claude-mp/issues/212)). | 98 | 90 | 100 | 100 | 100 | 97 |
| 2.0.0 | 2026-10-02 | [#198](https://github.com/totallyGreg/claude-mp/issues/198) | Renamed `local-omlx` → `local-inference`; product-neutral description and intro (tiers stay, the stack underneath changes); TurboQuant KV 8-bit on `deep` tested and rejected; 0.7.0 memory-guard ceiling recorded. Description 80 → 100. +v2.0.1 | 93 | 90 | 100 | 100 | 100 | 96 |
| 1.1.0 | 2026-10-01 | - | Pi extensions moved into `assets/pi-extensions/`; `install_pi_extensions.sh` copies them into Pi's agent dir (`${PI_CODING_AGENT_DIR:-~/.pi/agent}`) instead of Pi loading them from the marketplace clone. Score 94 (no change). +v1.1.1 | 93 | 90 | 100 | 100 | 80 | 94 |
| 1.0.0 | 2026-10-01 | [#196](https://github.com/totallyGreg/claude-mp/issues/196) | Initial release, moved from a personal skill: fast/code/deep/decide tiers on oMLX profiles; Pi one-shots and pane teammate (`pi_team.sh`); Claude Code on oMLX as a cross-session teammate (`claude_team.sh` + `reply_guard.py`, write tools scoped to its directory); `decide.py`, `bench_decode.py`, `eval_decide.py`; Pi vs Claude comparison and tier derivation references. | 93 | 90 | 100 | 100 | 80 | 94 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

## Skill: openrig-setup

### Current Metrics

**Score: 95/100** (Excellent) — 2026-10-02

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 93 | 86 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.3.0 | 2026-10-02 | - | `openrig:new --pi native` runs the coder on OpenRig's native `pi` runtime; terminal vs native tradeoffs. +v1.3.1 (`openrig:new` merges the lead's settings) +v1.3.2 (names a reused worktree's real branch; RTK allow rules) +v1.3.3 (lifecycle lessons; scaffold hygiene) | 93 | 86 | 100 | 100 | 100 | 95 |
| 1.2.0 | 2026-10-02 | - | The `claude-pi` lead runs in the rig folder, so OpenRig's per-boot rewrites stay out of the repo root; `openrig:check` warns on a Claude seat whose cwd is the repo. | 93 | 87 | 100 | 100 | 100 | 96 |
| 1.1.0 | 2026-10-01 | - | Scripts become mise file tasks (`openrig:check`, `openrig:convert`, new `openrig:new` scaffold) installed by `install_mise_tasks.sh`; rig shapes, naming, start/switch/retire. | 93 | 87 | 100 | 100 | 100 | 96 |
| 1.0.0 | 2026-10-01 | - | Initial release: install, configure and audit OpenRig with Claude Code only; read-only audit and a library-starter converter. | 98 | 90 | 100 | 100 | 100 | 97 |

Scores for 1.0.0–1.2.0 were measured on 2026-10-02 against each release's commit.

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

## Changelog

| Version | Date | Summary |
|---------|------|---------|
| 2.8.0 | 2026-10-21 | `local-inference` 2.4.0 ([#230](https://github.com/totallyGreg/claude-mp/issues/230)): oMLX 0.7.1 re-baseline (tiers.md derivation 11). Single requests are no faster than on 0.7.0 (cool, on battery: 35B 2,743 prefill / 104.7 decode tok/s, 27B 381 / 32.4; warm and charging, 9–30% lower). Parallel requests add almost no throughput with MTP on: four ~2K prompts give +12% in total, ~16K prompts give none, and time to first token grows with each request, because prefills queue and Lightning MTP batches at most two sequences. SKILL.md now says one at a time (was "at most 2", from a post measured on an M5 Ultra). New `scripts/bench_parallel.py` measures N concurrent requests. oMLX 0.7.1's Affine4/Affine8 KV compression tested on `deep` and rejected (derivation 12): on a 40.9K-token request it saved 2.4–3.4 GB of peak memory but slowed time to first token by 12–22% and decode by 16–22% (only 15 of 64 layers keep a KV cache in Qwen3.8), and it doesn't keep the 35B loaded during a long `deep` request. Recall of a fact at the start of the context held at every setting. New `scripts/kv_probe.py`. |
| 2.7.0 | 2026-10-15 | `local-inference` 2.3.0 ([#213](https://github.com/totallyGreg/claude-mp/issues/213)): Pi can be given bash for a gated edit. `scripts/pi_sandboxed.sh` (rewritten; 2.6.0's version couldn't start Pi) confines it with `sandbox-exec` to one worktree branch: it writes only the worktree, `--write` paths, `$TMPDIR` and caches; commits unsigned on its own branch only (never main, other branches, `.git/config` or hooks); reaches only localhost:8000; can't read `~/.ssh`/keychains; can't use unix sockets (tmux) or LaunchServices/AppleEvents, so nothing it runs can start a process outside. `scripts/sandbox_build_broker.sh` runs the builds Pi can't (xcodebuild needs LaunchServices, which also launches apps outside) on request, from a snapshot, refusing build-file and macro edits by ecosystem preset; `scripts/agent_sandbox.sh` is the harness-agnostic sandbox (secrets dropped from its environment) under `pi_sandboxed.sh`; `scripts/agent_sandbox_selftest.sh` proves each rule both ways (48 checks, 53 with `--live`; `--live` has the real Pi try every escape with its own guards off). Found by testing: an NSWorkspace launch escaped a profile that blocked only `open`; SwiftPM needs `--disable-sandbox` inside. The recipe is SKILL.md § Gated edit plus new `references/gated-edit.md`; SKILL.md restructured back under 2K tokens (skillsmith 93 → 97). `pi_team.sh` sets `PI_AGENT=1` in the pane's command (2.6.0 typed it to the model). 2.6.0 (2026-10-15): epistemic guardrails, Refuse section, `decide.py` choice cap and required `--system`, `see.sh` refusal routing. |
| 2.5.0 | 2026-10-13 | `local-inference` 2.1.0 ([#210](https://github.com/totallyGreg/claude-mp/issues/210)): new `see` tier (image → text or JSON) backed by Apple's `fm` CLI (macOS 27) — new `references/apple-fm.md` from tests on this Mac and Nikhil Vemu's macOS 27 `fm` write-up: which "eye" to use (OCR + schema for text, plain `--image` for charts), the schema dialect, 8K context, input traps, `fm serve` gotchas. Finder droplet / Folder Action wrappers live in terminal-guru. `eval_decide.py` takes `fm` as a model: on 62 backlog items it was 3× faster than `decide` but less accurate (type 38 vs 45, area 44 vs 54), so it does not replace `decide` (tiers.md derivation 10). New `scripts/see.sh` and Pi `see` tool ([#212](https://github.com/totallyGreg/claude-mp/issues/212)): an `omlx/code` agent read receipts and a QR code exactly through it, but its own sum checks were wrong in 2 of 3 runs — verify sums with code (references/apple-fm.md, pi-vs-claude.md). |
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
