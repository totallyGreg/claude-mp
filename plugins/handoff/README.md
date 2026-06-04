# Handoff

Hand off work to another Claude — a teammate in the same orchestration, a separate Claude running in a different tmux pane, or via clipboard/file for human-mediated transfer.

The skill produces a structured 8-section Markdown payload (Goal, Current state, Decisions made, Open questions, Next steps, Quick-start commands, Artifact references, Receiver notes) and dispatches it through the right transport based on who the recipient is.

## Why

Three external "handoff skill" implementations exist in the wider community (YKehinde, mattpocock, REMvisual) — but they all solve **session-to-session context preservation** (write a file, paste into a future Claude). None target a **specific running agent** in another tmux pane, and none integrate with the harness's native `SendMessage` channel for in-orchestration handoffs.

This plugin fills that gap. The same payload schema works whether you're:
- Handing off to a teammate inside the current orchestration (SendMessage, no IPC)
- Relaying to a Claude running in another tmux pane (file-drop + pointer message)
- Saving to clipboard for the user to paste manually
- Writing to a file for an audit trail or async pickup

## Usage

### Slash command

```
/handoff                              # auto-select transport
/handoff to:teammate <name>           # SendMessage to a teammate
/handoff to:tmux                      # first claude-running pane
/handoff to:tmux <session>            # specific session, lowest-index pane
/handoff to:tmux <session:window.pane> # explicit address
/handoff to:clipboard                 # pbcopy / xclip / wl-copy
/handoff to:file <path>               # chmod 600 + write
```

Free-text after the transport is used as the Goal section of the payload, e.g.:

```
/handoff to:tmux continue the v2 design conversation for the archivist plugin
```

### Direct script invocation (for agents)

```bash
echo "$PAYLOAD" | scripts/handoff --to tmux:auto --from "lead-claude"
echo "$PAYLOAD" | scripts/handoff --to clipboard
echo "$PAYLOAD" | scripts/handoff --to file:/tmp/handoff-task-X.md
scripts/handoff --help
```

## Transports

| Transport | When | Mechanism |
|---|---|---|
| **SendMessage** | Recipient is a teammate in the current team | Native harness tool — no filesystem, no IPC, receiver gets message as next turn |
| **tmux:** | Recipient is a Claude in a separate tmux pane | chmod-600 temp file + one-line pointer via `tmux send-keys` (with explicit Enter) |
| **clipboard** | Human-mediated paste into another session | `pbcopy` (macOS), `xclip` (X11), or `wl-copy` (Wayland) |
| **file** | Audit trail or async pickup | Write to specified path with `chmod 600` |

SendMessage is preferred when available — no filesystem exposure, no Enter-character risk, no shell-injection surface.

## Security

The tmux transport assumes single-user threat model (sender and receiver are the same user on the same host). Within that model:

- Payload files are written with `chmod 600` and `umask 077`
- Old `handoff-*.md` temp files (>1 day) are swept on each invocation
- File paths in pointer messages are validated (`^[/a-zA-Z0-9._-]+$`)
- `--filter claude` is applied by default for `tmux:` targets — prevents delivering "read this file" instructions to a shell prompt that would try to execute them
- Two-call `tmux send-keys` (literal message + explicit Enter) — fixes the common failure mode where the message arrives but sits at the prompt waiting on manual Return

See `skills/handoff/references/tmux-targeting.md` for the full security model and known non-defenses.

## Composition with terminal-guru

This plugin ships its own minimal tmux pane discovery — **no dependency on `terminal-guru` or any external tmux helper**. Only `tmux` itself is required.

If the standalone `tmux-send` capability planned for `terminal-guru` ever ships, the handoff plugin can optionally delegate pane targeting to it (for richer picker UX) — but that's an optimization, not a requirement.

## Components

- `agents/` — none (skill + command only)
- `skills/handoff/SKILL.md` — when to use, payload overview, transport selection
- `skills/handoff/scripts/handoff` — bash script handling clipboard, file, and tmux transports
- `skills/handoff/references/payload-schema.md` — full 8-section spec with examples
- `skills/handoff/references/tmux-targeting.md` — pane discovery algorithm + security model
- `commands/handoff.md` — `/handoff` slash command

## Skill: handoff

### Current Metrics

**Score: 98/100** (Excellent) — 2026-06-04

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 0.1.0 | 2026-06-04 | - | Initial release. Three transports: SendMessage (via calling agent), tmux send-keys with two-call Enter delivery, clipboard, file. 8-section Markdown payload schema. Standalone tmux pane discovery (no terminal-guru dependency). Security: chmod 600 temp files, mandatory `--filter claude` default, path validation. | 100 | 90 | 100 | 100 | 100 | 98 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

## License

MIT
