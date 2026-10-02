---
name: openrig-setup
description: This skill should be used when the user asks to "set up openrig", "install openrig", "configure openrig for this project", "check my openrig setup", "is openrig set up correctly", "write a rig.yaml", "create a rig for this repo", "convert a codex rig to claude", "openrig doctor", "why won't my rig start", or mentions rig.yaml, agent.yaml, `rig up`, `rig setup`, or the OpenRig daemon in a setup or configuration context. Covers install, the daemon, config keys, RigSpec/AgentSpec authoring, Claude-Code-only rigs (no Codex), and a read-only audit of a project's setup. Do NOT use for operating a running rig day to day (queue triage, handover, recovery) — use the openrig-skills skills OpenRig projects into its seats.
metadata:
  version: "1.0.0"
compatibility: macOS or Linux; OpenRig CLI 0.5.x (checked on 0.5.17); Node 22 or 24; tmux; Claude Code; uv for the Python script
license: MIT
---

# openrig-setup

Install OpenRig, configure it, and give a project a rig that boots, then
prove the setup with a read-only audit. This setup uses **Claude Code only**:
there is no Codex. Library starters that use Codex seats get converted.

OpenRig in one line: a local daemon (HTTP + SQLite, `127.0.0.1:7433`) owns all
state; `rig` (CLI), `rig tui` and its MCP server are clients; each seat is a
Claude Code session in tmux. tmux is the transport and the database is the
truth. Commands and config are in
[references/cli-and-config.md](references/cli-and-config.md), and the
`rig.yaml`/`agent.yaml` schemas are in [references/specs.md](references/specs.md).

## 1. Audit first — always

```bash
S=${CLAUDE_PLUGIN_ROOT}/skills/openrig-setup/scripts
$S/openrig_check.sh /path/to/project
```

It is read-only and runs these checks:
- prerequisites
- `rig doctor`
- daemon status
- non-default config
- `rig workspace doctor`
- every `rig.yaml` in the project: version, Codex seats, `culture_file` and `agent_ref` resolution, and `rig up --plan`
- all rigs, including stopped ones, with duplicate rig names flagged

Fix FAIL lines in the order printed. Don't change anything before reading the
audit.

## 2. Install (only if the audit says so)

```bash
node --version            # 22 (Apple silicon) or 24
tmux -V
npm install -g @openrig/cli   # or the existing Homebrew install
rig setup --dry-run && rig setup
rig preflight && rig doctor
rig daemon start          # after reboot: rig start --last
```

`rig doctor` warning that cmux is missing is fine: cmux is optional. Skip every
Codex step, and ignore the Codex lines in `rig setup` output.

## 3. Give a project a rig

Pick the smallest shape that fits:

| Need | Do |
|------|-----|
| One seat, no spec | `rig create <name>` |
| A pair or team from a proven starter | convert a library starter (below) |
| A custom topology | write `rig.yaml` from references/specs.md |

**Converting a starter to Claude-only.** `rig specs ls` lists the starters;
`first-project` is an owner plus a checker, `conveyor` is intake → plan →
build → review. Convert one with:

```bash
$S/claude_only_spec.py first-project <project>/.openrig <rig-name> --dry-run
$S/claude_only_spec.py first-project <project>/.openrig <rig-name>
rig up <project>/.openrig/rig.yaml --plan
```

The script makes these changes:
- copies the starter's `rig.yaml` and `CULTURE.md`
- points `cwd` at the enclosing git repo root
- rewrites the starter's relative `local:../../../agents/…` refs to absolute
  `path:` refs, because copying the yaml breaks the relative ones
- sets `runtime: claude-code`
- drops the GPT `model:` lines

The library AgentSpecs work with either runtime, so nothing else changes.

Before booting, check four things in the spec:
1. `name` is unique. `rig up <name>` resolves by name, so leftover rigs with the
   same name make it ambiguous. Archive extras with `rig archive <rigId>`.
2. `cwd` points at the repo. It resolves against the spec's own directory, not
   where you run `rig up`, so `cwd: "."` in `<repo>/.openrig/rig.yaml` starts
   seats in `.openrig/`. The script rewrites it to the repo root; `--cwd`
   overrides it for one run.
3. Pod and member ids contain no dots.
4. A permission posture is recorded: `rig policy apply standard --spec <dir>`.
   Without one, `--plan` warns `launch_posture=floor`. The posture is only
   recorded; Claude Code's own permission settings enforce it.

Then boot and confirm:

```bash
rig up <project>/.openrig/rig.yaml
rig ps --nodes --rig <rig-name>
rig doctor --spec <project>/.openrig/rig.yaml   # spec matches the running rig
rig tui
```

**Pi (or any CLI agent) as a seat.** Use a terminal node: `runtime: terminal`,
`agent_ref: "builtin:terminal"`, `profile: none`, all three. The seat is a plain
shell, so its `send_text` is typed in as a command. Prose would run as a shell
command, so launch the agent with its brief:

```yaml
startup:
  actions:
    - type: send_text
      value: 'pi --model omlx/code "Read <repo>/path/brief.md and do the tasks in it."'
      phase: after_ready
      applies_on: [fresh_start]
      idempotent: true
```

Paths in the brief are relative to the seat's `cwd`. The local-inference
skill covers tiers and Pi flags.

## 4. Configure

```bash
rig config --with-source          # every key + which layer won
rig config get workspace.root --show-source
rig config set <key> <value>      # rig config reset <key> to undo
rig config init-workspace --dry-run
```

The precedence order is flag → env → config file → default. A `default` path is
derived per machine, so don't hardcode it. Changing the files allowlist or the
progress scan roots needs `rig daemon stop && rig daemon start`. The Claude-relevant
keys are `policies.claude_compaction.*` (off by default) and
`health.context_pressure.*`. Claude compacts more aggressively than Codex, so for
long seats consider a pod `continuity_policy` or turning on Claude compaction.

## 5. Startup content: what each seat knows at boot

Put role, project and environment facts into guidance files
(`delivery_hint: guidance_merge`, merged into CLAUDE.md before boot). Put
reusable procedures into skills (`skill_install`). Then use one `send_text`
action, `phase: after_ready`, to tell the seat to load them. Hook, MCP and
runtime-resource projection are experimental, so describe the desired state in
guidance and have the seat verify it. The full layering order is in
references/specs.md.

## Verify

The setup counts as correct only when all of these hold:
- `openrig_check.sh` exits 0
- `rig up … --plan` reports `Status: planned` without errors
- after `rig up`, every seat in `rig ps --nodes` is running
- `rig doctor --spec` passes `spec_live_conformance`

Report each result to the user with its command output. Don't claim the
setup works from `rig ps` alone.
