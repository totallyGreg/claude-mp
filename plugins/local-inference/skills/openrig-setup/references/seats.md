# OpenRig seats in detail

Checked against OpenRig 0.5.17 (2026-10-02), from the daemon source and live
boots.

## Terminal or native Pi (`openrig:new --pi`)

| | `terminal` (default) | `native` (`runtime: pi`) |
|---|---|---|
| How | A shell seat whose `send_text` runs `pi --append-system-prompt <brief>` | OpenRig's runner drives `pi --mode rpc`; `model: omlx/<tier>` |
| OpenRig sees | A shell | Pi's state (`working`/`idle`), session file, exact resume, restore, handover |
| Pi config | Your `~/.pi/agent`: models, extensions (write-boundary, permission-gate) | A per-seat agent dir, `~/.openrig/state/pi/<seat>/agent`; **no extensions** |
| Brief | `coder-brief.md` via `--append-system-prompt` | Slim AgentSpec `agents/pi-coder` merges it into `AGENTS.md` in the worktree |

Native needs your `models.json` in the seat's agent dir — OpenRig has no
resource for it, so the scaffold symlinks it and `openrig:check` fails without
it (after `rig destroy` or a state wipe, re-run the `ln -s` it prints). The
runner forwards only PATH/HOME/… and API keys for openrouter, zai and kimi; an
`apiKey: "!command"` (like the omlx provider's) still works. Answers stream
into the pane. Library AgentSpecs (e.g. `implementer`) send a heavy role and
start OpenRig's SDLC orientation — too much for a local model; the slim agent
avoids the role. Native also writes an untracked `AGENTS.md` into the worktree;
don't commit it. Prefer native when restore/handover matters; terminal when
you want Pi's extensions.

## What a Claude seat writes into its cwd

On every boot of a `claude-code` seat, OpenRig writes into its `cwd`:
- managed blocks in `CLAUDE.md` (culture, `openrig-start`, onboarding);
- `.claude/plugins/` and `.claude/skills/` (openrig-core), `.mcp.json`;
- into `.claude/settings.local.json`: `acceptEdits`, exa/context7, activity
  hooks, and a **`statusLine` that prints nothing** (it only records context
  usage) — rewritten each boot, other keys kept;
- `.openrig/` (the collector and hook scripts).

Any Claude session you start in that directory inherits all of it: a blank
status bar, OpenRig's hooks reporting your session as rig activity, and its
blocks in your instructions. Hence the lead lives in the rig folder.
`openrig:check` warns when a Claude seat's cwd is the repo root. To clean a
directory a seat used to run in, remove those files and the `statusLine`,
`hooks`, `enabledMcpjsonServers` and `permissions.defaultMode` keys (a Codex
seat leaves `.codex/` and `.agents/`).

**One instructions file (AGENTS.md).** Keep project instructions in
`AGENTS.md` and `ln -s AGENTS.md CLAUDE.md` — Claude Code and Pi then read one
file. With the lead in the rig folder, OpenRig's blocks go to the rig folder's
own `CLAUDE.md`, not yours. (`managed_blocks: {claude-code: CLAUDE.local.md}`
is the only other target; OpenRig can't write AGENTS.md for Claude seats, but
its `writeFileSync` does follow a symlink.) In a repo you don't own, add
`CLAUDE.md` to `.git/info/exclude`.

**Codex leftovers.** A Codex starter (e.g. `first-project`) projects
`.codex/plugins/` and `.agents/skills/` into its cwd even when Codex never
launches; with no Codex seats they're unused and safe to delete.
