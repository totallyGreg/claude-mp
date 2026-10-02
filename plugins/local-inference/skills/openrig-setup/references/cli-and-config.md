# OpenRig CLI and config reference

Source: openrig.dev/docs (documented against 0.5.14; commands below checked
against the installed 0.5.17 `--help`, 2026-10-01). Help text says "node" where
the docs say "seat". `rig <cmd> --help` is authoritative; `--json` on most
commands is for agents.

## Architecture in one paragraph

A local daemon (Hono HTTP + SQLite, default `127.0.0.1:7433`) holds all state.
The `rig` CLI, `rig tui` and the MCP server are clients of it. Every seat runs
in a tmux session — tmux is the transport, SQLite is the truth; if they
disagree, the database wins. Seat address `{pod}-{member}@{rig}` (for `rig send`,
`capture`, `transcript`); logical id `pod.member` (for `rig launch`, `remove`,
`bind --node`).

## Vocabulary

fleet (all rigs) · rig (a team, one `rig.yaml`) · pod (bounded context group) ·
seat (named position; survives its session) · session (the harness process now
in a seat) · snapshot (restore point) · queue item / qitem (owned work unit) ·
handoff (transactional transfer) · workflow · chatroom · context pack ·
watchdog (scheduler surviving restarts) · stream (append-only intake) ·
work tree (project → mission → slice, each with SPEC.md) · agent image
(captured resumable seat state).

## Install and health

| Command | What |
|---|---|
| `npm install -g @openrig/cli` | install |
| `rig setup --dry-run` / `rig setup` | plan / apply: installs or checks harnesses and cmux. `rig setup --policy` records a permission policy |
| `rig preflight` | can this machine run OpenRig (node, tmux, writable home, port). No daemon needed |
| `rig doctor` | install health; `--spec ./rig.yaml` compares a spec to the running rig of the same name. No daemon needed |
| `rig daemon start\|stop\|status\|logs --follow` | daemon control |
| `rig start --last` | after reboot: daemon + kernel + last-running rigs |
| `rig crash-cart` | daemon down: read-only recovery verdict as JSON |
| `rig workspace doctor` | 8-check workspace readiness (root, missions, allowlist, daemon alignment, …). Read-only |
| `rig workspace validate [root]` | frontmatter gap report for a work tree |
| `rig destroy --state\|--all --backup --yes --confirm destroy-openrig-state` | last resort only |

## Specs and lifecycle

| Command | What |
|---|---|
| `rig specs ls` / `preview <name>` / `show <name>` | library; `show` prints the spec's path |
| `rig specs add <path>` / `remove` / `rename` / `sync` | user library |
| `rig up <name\|./rig.yaml\|x.rigbundle>` | boot or restore; `--plan` validates and previews only; `--cwd <path>` overrides every member's cwd for this run; `--fresh <seats…>` |
| `rig down <rig> --snapshot` | stop, snapshot first (snapshot failure doesn't block teardown) |
| `rig create <name>` | one-seat rig with no spec |
| `rig grow <rig> <seat> --pod <pod>` / `--new-pod <pod> --runtime claude-code` | add seats live (runtime defaults to claude-code) |
| `rig launch <rig> <pod.member>` | relaunch one seat |
| `rig discover [--draft]` → `rig adopt <spec> --bind <logicalId=session>` | bring existing tmux sessions under a rig |
| `rig archive <rig>` / `unarchive` | hide a rig, keep its data |
| `rig ps` (`--nodes`, `-A`, `--filter status=stopped`, `--json`) | fleet / seats. Stopped rigs are hidden by default |
| `rig status` | daemon + rig status |
| `rig restore-check [--rig <id>]` | exit 0 restorable, 1 not, 2 unknown |
| `rig snapshot list` / `rig restore <snapshotId> --rig <id>` | explicit restore |
| `rig policy list` / `apply <name> --spec <path>` / `current --spec <path>` | record permission posture: locked, standard, open, yolo, none. Recorded only — Claude Code's own permission settings enforce |
| `rig mode effective` / `set … --confirm` | human-led vs delegated posture |
| `rig tui` | the operator UI |

## Seats and messaging

`rig send <addr> "text" --verify [--wait-for-idle 30]` · `rig send --pod <pod>` ·
`rig capture <addr> --lines 50` · `rig transcript <addr> --tail 100 --grep x` ·
`rig chatroom send|wait` · `rig whoami` · `rig seat status|clean|stop|launch|set-model <addr>` ·
`rig handover <seat> --reason "…" --dry-run`.

## Diagnosing a stuck seat (record before pane)

`rig parked --rig R` → `rig heartbeat --rig R` → `rig health --rig R` →
`rig health explain <id>` → only then `rig capture` / `tmux attach` →
`rig launch R pod.member`. Empty health output is not proof of health.
Restores report per seat (resumed, rebuilt, fresh, awaiting decision, failed);
mixed results are normal.

## Config

`rig config [--with-source] [--json]` · `rig config get <key> [--show-source]` ·
`rig config set <key> <value>` · `rig config reset [key]` ·
`rig config init-workspace [--root <path>] [--dry-run]` (additive scaffold).

Resolution: CLI flag → env var → config file → default. `default` means derived
on this machine — never copy a default path into docs as a constant. Changing
startup-time roots (files allowlist, progress scan roots) needs a daemon restart.

Keys that matter for setup:

| Key | Default |
|---|---|
| `daemon.host` / `daemon.port` | 127.0.0.1 / 7433 |
| `workspace.root` | ~/.openrig/workspace (derived) — projects, missions, specs roots hang off it |
| `workspace.projects_root`, `slices_root`, `specs_root`, `steering_path`, `catalog_path` | under workspace.root |
| `topology.root`, `skills.root`, `context.root`, `db.path` | derived |
| `files.allowlist` | derived; daemon restart to change |
| `snapshots.periodic.enabled` / `interval_seconds` / `retention_keep` | true / 300 / 10 |
| `health.context_pressure.warning_percent` / `critical_percent` | 95 / 99 |
| `policies.claude_compaction.enabled` / `threshold_percent` | false / 80 |
| `queue.pickup_stall_threshold_minutes` | 3 |
| `recovery.auto_drive_provider_prompts` | false |
| `runtime.codex.hooks_enabled` | true (irrelevant without Codex) |
| `ui.timezone` | America/Los_Angeles |

Other files: `~/.openrig/hosts.yaml` (remote hosts, `rig host add`),
`$OPENRIG_HOME` (state home). Skill loadout per working dir:
`rig skill loadout --runtime claude-code [--apply]`, `rig skill audit`.

## Work tree

`rig scope mission create <name> --intent "…"`,
`rig scope slice create <mission> <name> --intent "…"`: creates SPEC.md,
slice.yaml, PROGRESS.md, PROOF.md, proof/ with stable dot-IDs under
`workspace.slices_root`. `rig scope audit` is advisory. `rig proof add` files
evidence. `rig queue create --destination <addr> --body-file f --mission m --slice s`,
`claim`, `update --state done --closure-reason …`, `handoff --to <addr>`.
