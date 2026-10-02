---
name: openrig-setup
description: This skill should be used when the user asks to "set up openrig", "install openrig", "configure openrig for this project", "check my openrig setup", "is openrig set up correctly", "create a rig for this repo", "scaffold a rig", "switch rigs", "rename a rig", "write a rig.yaml", "convert a codex rig to claude", "openrig doctor", "why won't my rig start", or mentions rig.yaml, agent.yaml, `rig up`, `rig setup`, `mise run openrig:*`, or the OpenRig daemon in a setup or configuration context. Covers install, the daemon, config keys, rig shapes (Claude lead + Pi coder, Pi alone), naming, starting and switching rigs, RigSpec/AgentSpec authoring, Claude-Code-only rigs (no Codex), and a read-only audit. Do NOT use for operating a running rig day to day (queue triage, handover, recovery) — use the openrig-skills skills OpenRig projects into its seats.
metadata:
  version: "1.3.0"
compatibility: macOS or Linux; OpenRig CLI 0.5.x (checked on 0.5.17); Node 22 or 24; tmux; Claude Code; mise and uv for the tasks; Pi + oMLX for Pi seats
license: MIT
---

# openrig-setup

Install OpenRig, give a project a rig that boots, and prove it with a read-only
audit. This setup uses **Claude Code and Pi only** — there is no Codex.

OpenRig in one line: a local daemon (HTTP + SQLite, `127.0.0.1:7433`) owns all
state; `rig` (CLI), `rig tui` and its MCP server are clients; each seat is a
session in tmux — tmux is the transport, the database is the truth. Commands
and config are in [references/cli-and-config.md](references/cli-and-config.md),
and the `rig.yaml`/`agent.yaml` schemas are in [references/specs.md](references/specs.md).

## The tools: mise tasks

The skill ships three mise file tasks in `mise-tasks/openrig/`. Install them
once (and again after a plugin update) into the global mise tasks dir, so they
work in every project:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/openrig-setup/scripts/install_mise_tasks.sh --check   # what would change
${CLAUDE_PLUGIN_ROOT}/skills/openrig-setup/scripts/install_mise_tasks.sh
```

| Task | Does |
|------|------|
| `mise run openrig:check [project]` | Read-only audit, exit 1 on any FAIL. Checks prereqs, `rig doctor`, the daemon, `rig workspace doctor`, every `rig.yaml` (version, Codex seats, `agent_ref` and `cwd` resolution, terminal seats launch a command, native pi seats have `models.json`, `rig up --plan`) and duplicate rig names |
| `mise run openrig:new <claude-pi\|pi-solo> [project] --prefix P --tier code --pi terminal\|native` | Scaffold a rig: spec + briefs in `openrig-specs/<P>-<shape>/`, a worktree at `.worktrees/<P>-<shape>` on `experiment/<P>-<shape>-<date>`, then `rig up --plan`. `--dry-run` first |
| `mise run openrig:convert <starter> <dest> <name>` | Copy a library starter (`rig specs ls`) as a Claude-only spec |

The project defaults to where `mise run` was invoked. Without mise, run the
files in `mise-tasks/openrig/` directly.

## 1. Audit first — always

`mise run openrig:check` before changing anything, and fix FAILs in the order
printed. If OpenRig isn't installed:

```bash
npm install -g @openrig/cli            # or Homebrew; Node 22 on Apple silicon
rig setup --dry-run && rig setup        # ignore its Codex lines
rig preflight && rig doctor             # "cmux not found" is fine — optional
rig daemon start                        # after reboot: rig start --last
```

Start the daemon from a directory that will outlive it (`cd ~ && rig daemon
start`). It keeps its cwd and runs `pi --version` there; if that directory is
deleted, Node programs fail and preflight blocks every pi seat with
"Runtime "pi" not available".

## 2. Pick a shape

| Shape | Seats | Use when |
|-------|-------|----------|
| `claude-pi` | `dev-lead` (Claude Code) → `dev-coder` (Pi) | Design, judgment and review from Claude; typing from a local model |
| `pi-solo` | `dev-coder` (Pi) | Well-specified tasks, cheap and private; you hand it tasks directly |

Don't build two-Pi orchestrator + coder rigs. The split pays off only when the
orchestrator is stronger than the coder, or the second seat is independent; two
copies of one local model add messaging, two contexts and oMLX contention, and
"review" shares the coder's blind spots. A second Pi earns a seat only with a
different job — e.g. a read-only reviewer on `omlx/deep`
(`--tools read,grep,find,ls`). Idle seats cost nothing on oMLX.

### Terminal or native Pi (`--pi`)

`terminal` (default): a shell seat whose `send_text` launches
`pi --append-system-prompt <brief>`; Pi keeps your `~/.pi/agent` config and
extensions, but OpenRig only sees a shell. `native` (`runtime: pi`): OpenRig's
runner drives Pi and tracks its state, session, restore and handover; Pi gets a
per-seat agent dir with no extensions, so the scaffold links your
`models.json` into it. Prefer native when restore/handover matters. Details,
env and key limits: [references/seats.md](references/seats.md).

## 3. Name it

Rig `<project-prefix>-<shape>` (e.g. `qs-claude-pi`), seats by role (`lead`,
`coder`), runtime and tier in the `label`. Ids: lowercase, no dots. Addresses
are `{pod}-{member}@{rig}` and the briefs hardcode them, so **renaming a rig
means new briefs** — scaffold a new rig rather than editing `name:`. Rig names
must be unique among stopped rigs too, or `rig up <name>` is ambiguous; archive
old ones with `rig archive <rigId>` (reversible: `rig unarchive`).

## 4. Start, switch, retire

There is no "project's rig" setting (`rig project` is a task classifier). A rig
belongs to a project through where its spec lives and its seats' `cwd`.

```bash
mise run openrig:new claude-pi --prefix qs --dry-run && mise run openrig:new claude-pi --prefix qs
rig up openrig-specs/qs-claude-pi/rig.yaml      # first boot; later: rig up qs-claude-pi
rig ps --nodes --rig qs-claude-pi
rig doctor --spec openrig-specs/qs-claude-pi/rig.yaml

rig down qs-claude-pi --snapshot && rig up qs-pi-solo   # switch
rig down old --snapshot && rig archive <rigId>           # retire (rig ps --json --filter status=stopped for ids)
```

Two rigs can run at once (separate worktrees), but they share oMLX; past two
concurrent Pi requests each one slows down. Reusing one spec across projects
doesn't work: library specs can't use relative `cwd`, and `rig up --cwd`
overrides *every* seat's cwd, collapsing the coder's worktree into the lead's
directory. Scaffold one spec per project instead.

## 5. What the scaffold gets right — and hand-written specs got wrong

- **`cwd` resolves against the spec's directory**, not where `rig up` runs. In
  `openrig-specs/<rig>/rig.yaml`, `"."` is the rig folder and `"../.."` the repo root.
- **The Claude lead runs in the rig folder (`cwd: "."`), never where you
  work.** OpenRig takes over its cwd (§6). The scaffold gives it the repo via
  `.claude/settings.local.json` → `permissions.additionalDirectories`, and
  Claude Code still loads the repo's CLAUDE.md/AGENTS.md from the parent folders.
- **A terminal seat is a shell.** Its `send_text` is typed in as a command, so
  it must launch the agent; prose runs as a shell command. For Pi:
  `pi --model omlx/code --append-system-prompt <abs brief> "<kick>"` —
  `--append-system-prompt` takes a file and keeps the brief in the system
  prompt for the whole session. Escape `'` as `''` inside a YAML single-quoted value.
- **Briefs use absolute paths** — the coder's worktree doesn't contain an
  untracked or ignored `openrig-specs/`.
- **The coder gets its own worktree** (`.worktrees/` is added to
  `.git/info/exclude`), so it can't touch the main checkout; the lead reviews
  with `git -C <worktree> diff`.

## 6. What a Claude seat writes into its cwd

On every boot OpenRig writes into a Claude seat's cwd: managed blocks in
`CLAUDE.md`, `.claude/` plugins, skills and settings (including a `statusLine`
that prints nothing, plus activity hooks), `.mcp.json` and `.openrig/`. Any
session you start there inherits it — hence the lead lives in the rig folder.
Keep one instructions file: project rules in `AGENTS.md`, `ln -s AGENTS.md
CLAUDE.md`. Cleanup steps and the `managed_blocks` options:
[references/seats.md](references/seats.md).

## 7. Permissions

`permission_policy: builtin:standard` is recorded only (`launch_posture:
floor`); Claude Code's own settings decide. Expect the lead to ask before every
`rig` command until you allow them — answer "don't ask again" in its pane, or
add to the rig folder's `.claude/settings.local.json` `permissions.allow`:
`Bash(rig whoami:*)`, `Bash(rig send:*)`, `Bash(rig capture:*)`,
`Bash(rig context:*)`, `Bash(git -C:*)`. Pi has no permission prompts — its
worktree is its boundary.

## 8. Configure

```bash
rig config --with-source               # every key + which layer won
rig config set <key> <value>           # rig config reset <key> to undo
```

Precedence: flag → env → config file → default (`default` paths are derived
per machine). After editing config, `rig workspace doctor` reports
`daemon_reload_needed`: there is no `rig daemon restart` in 0.5.17 —
`rig daemon stop && rig daemon start`. Long Claude seats: consider a pod
`continuity_policy` or `policies.claude_compaction.enabled`.

## Next steps once the loop works

- Hand tasks through the queue instead of bare `rig send`
  (`rig queue create --destination dev-coder@<rig> --body-file …`): owned,
  stateful, visible to `rig parked` / `rig heartbeat`.
- `rig down --snapshot` whenever you switch; periodic snapshots are on (300 s).

## Verify

Done only when: `mise run openrig:check` exits 0; `rig up … --plan` says
`Status: planned`; after `rig up`, `rig ps --nodes` shows every seat running and
`rig capture <coder>` shows Pi on the right tier and branch; `rig doctor --spec`
passes `spec_live_conformance`. Report each with its output — not `rig ps`
alone.
