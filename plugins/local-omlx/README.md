# local-omlx

Run work on local [oMLX](https://github.com/jundot/omlx) models from Claude Code, two ways that share the same model tiers:

- **Pi** (`pi`) — one-shot briefs (`pi -p`), or a teammate in its own tmux pane driven by `pi_team.sh`.
- **Claude Code on oMLX** — `omlx launch claude --cross-session`, a real teammate reachable with `ListAgents`/`SendMessage`, launched slim by `claude_team.sh`.

Claude Code on Anthropic's models stays the orchestrator: it writes the brief, runs the local agent, and verifies the result.

<!-- BEGIN AUTOGEN:overview (managed by skillsmith --update-components; edits overwritten) -->
## What's inside

Run work on local oMLX models from Claude Code: Pi one-shots and pane teammates, a decide tier, and Claude Code on oMLX as a cross-session teammate.

**At a glance:** 1 skill

## Install

```
/plugin marketplace add totallyGreg/claude-mp
/plugin install local-omlx@totally-tools
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

`skills/local-omlx/references/tiers.md` records the current mapping, how it was measured, and the procedure for adopting a new model.

## Which to use

**Pi by default.** On the same multi-file edit both produced the identical diff in about the same time, but Pi needed far less setup, its answers can't be lost, and it sends no telemetry. **The Claude Code teammate** when another Claude session needs to message it natively. `skills/local-omlx/references/pi-vs-claude.md` is the running comparison — evidence, friction log, and a parity table.

<!-- BEGIN AUTOGEN:components (managed by skillsmith --update-components; edits overwritten) -->
## Components

### Skills (1)

| Skill | Description |
|-------|-------|
| `local-omlx` | Two ways to run work on the local oMLX models, both sharing the same tiers: |
<!-- END AUTOGEN:components -->

## Scripts and Pi extensions

| Path | What |
|------|------|
| `skills/local-omlx/scripts/decide.py` | One constrained answer from the `decide` tier |
| `skills/local-omlx/scripts/pi_team.sh` | Pi teammate in a tmux pane: `spawn`, `ask`, `close` |
| `skills/local-omlx/scripts/claude_team.sh` | Claude Code on oMLX as a teammate: slim prompt, scoped write tools, reply guard |
| `skills/local-omlx/scripts/reply_guard.py` | Stop hook: the teammate can't end a turn without replying |
| `skills/local-omlx/scripts/bench_decode.py`, `eval_decide.py` | Speed and decision-accuracy measurements for new models |
| `pi/extensions/statusline.ts` | Claude-style status line for Pi |
| `pi/extensions/write-boundary.ts` | Pi's edit/write only under its launch directory |
| `pi/extensions/permission-gate.ts` | Asks before recursive deletes, sudo, or chmod 777 |

## Setup

1. oMLX running on `127.0.0.1:8000` with the tier profiles (`references/tiers.md`).
2. `~/.pi/agent/models.json` with the `omlx` provider and the tier entries.
3. In `~/.pi/agent/settings.json`, load the Pi extensions from the marketplace copy:
   ```json
   "extensions": ["~/.claude/plugins/marketplaces/totally-tools/plugins/local-omlx/pi/extensions"]
   ```

## Skill: local-omlx

### Current Metrics

**Score: 94/100** (Good) — 2026-10-01

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 93 | 90 | 100 | 100 | 80 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.0.0 | 2026-10-01 | [#196](https://github.com/totallyGreg/claude-mp/issues/196) | Initial release, moved from a personal skill: fast/code/deep/decide tiers on oMLX profiles; Pi one-shots and pane teammate (`pi_team.sh`); Claude Code on oMLX as a cross-session teammate (`claude_team.sh` + `reply_guard.py`, write tools scoped to its directory); `decide.py`, `bench_decode.py`, `eval_decide.py`; Pi vs Claude comparison and tier derivation references. | 93 | 90 | 100 | 100 | 80 | 94 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

## Changelog

| Version | Date | Summary |
|---------|------|---------|
| 1.0.0 | 2026-10-01 | Initial release: the personal `local-omlx` skill moved into the marketplace, with the Pi extensions that pair with it ([#196](https://github.com/totallyGreg/claude-mp/issues/196)). |

## License

MIT
