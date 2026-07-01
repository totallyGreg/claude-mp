---
name: handoff
description: This skill should be used when the user or another agent asks to "create a handoff", "write a handoff payload", "generate a handoff for another agent", "build a context handoff", "configure a tmux relay", "hand off this work", "hand off to another claude", "relay this to another agent", "send context to a teammate", "transfer this to another pane", "pass this to <agent-name>", "/handoff", or otherwise wants to transfer structured work context from this Claude session to another Claude — whether a teammate spawned via SendMessage, a Claude process running in a separate tmux pane, or via clipboard for human-mediated handoff. Do NOT use for tmux pane management generally (use terminal-guru) or for end-of-session file-based recap intended for a future fresh Claude session unrelated to any live recipient (that is a different problem domain).
metadata:
  version: "0.2.0"
compatibility: bash 4+; tmux 3.0+ for tmux transport; pbcopy/xclip/wl-copy for clipboard transport
license: MIT
---

# Handoff

Transfer structured work context from this Claude session to another Claude — a teammate, a separate Claude running in a tmux pane, or to clipboard/file for human-mediated handoff. The skill picks the right transport based on who the recipient is.

## Decision: Transport Selection

The recipient determines the transport. Pick **before** building the payload — the payload schema is the same, but the delivery mechanism differs.

| Recipient | Transport | How |
|---|---|---|
| Teammate in current orchestration (spawned via `TeamCreate` or `Agent`) | **SendMessage tool** (native) | Call `SendMessage({to: "<name>", message: <payload>})` directly. Do NOT invoke the script. |
| Claude running in a separate tmux pane | **`tmux:` transport** | Invoke `scripts/handoff --to tmux:<address>` (pipe payload on stdin) |
| Human to paste into another session | **clipboard** | `scripts/handoff --to clipboard` |
| Audit trail or async pickup | **file** | `scripts/handoff --to file:<path>` |

**SendMessage is always preferred when available** — no filesystem, no shell injection surface, no tmux Enter-character risk; receiver gets the message as their next conversation turn.

## Building the Payload

Every handoff uses the same Markdown schema. Four sections are required; everything else goes into a single free-form "Additional context" section. The receiver should be able to pick up productively without re-asking "what's going on."

| Section | Required | Content |
|---|---|---|
| Goal | yes | One sentence: what the receiver is being asked to do |
| Current state | yes | 5–15 bullets: what's done, in flight, blocked |
| Decisions made | yes | Chosen approach + rejected alternatives (one-line rationale each) |
| Next steps | yes | Ordered list: what to do first, second, third |
| Additional context | optional | Quick-start commands, artifact references, open questions, receiver-specific notes — only include what's genuinely useful |

Full per-section guidance, examples, and anti-patterns live in `references/payload-schema.md`. Load that reference when building a non-trivial payload or when the receiver is a specialized agent.

## Invoking the Script

The script reads payload from stdin and dispatches to the requested transport.

```bash
# Clipboard
echo "$PAYLOAD" | scripts/handoff --to clipboard

# File (chmod 600 enforced)
echo "$PAYLOAD" | scripts/handoff --to file:/tmp/handoff-myrun.md

# Tmux: persistent pane_id (preferred — survives pane moves)
echo "$PAYLOAD" | scripts/handoff --to tmux:%6 --from "archivist"

# Tmux: explicit positional pane address (fragile if panes move)
echo "$PAYLOAD" | scripts/handoff --to tmux:my-session:1.0 --from "archivist"

# Tmux: pick the first claude-running pane
echo "$PAYLOAD" | scripts/handoff --to tmux:auto --from "attache"
```

For `tmux:`, `--filter claude` is applied by default — see `references/tmux-targeting.md` for the security rationale and the pane-discovery algorithm. Pass `--filter '.*'` to disable filtering when the receiver is known and the risk is accepted.

**Disambiguating multiple claude panes:** when several panes run `claude`, `--filter claude` matches all of them and the script picks the first. Use `--filter-address <regex>` to pin by session address. Example: `--filter claude --filter-address "airs/project"` targets the `claude` pane in the `airs/project` session. Combined filters AND together. Run `tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index}\t#{pane_current_command}'` to see all addresses before targeting.

## When NOT to Invoke the Script

- **Recipient is a teammate.** Use the SendMessage tool directly. The script does not handle SendMessage — that is the orchestration layer, not the IPC layer.
- **Recipient is the same Claude session.** No handoff needed; continue the work.
- **End-of-session recap to a hypothetical future Claude.** That is a different problem (session-to-session context preservation, not live agent handoff). The genre is covered by tools like `claude-handoff` (REMvisual).

## Tmux Transport: What to Know

The script writes the payload to a chmod-600 temp file and delivers a one-line pointer message to the target pane via `tmux send-keys`. The pointer says:

```
[handoff from <sender>] Read /tmp/handoff-<pid>-<ts>.md and acknowledge in conversation.
```

The receiver Claude reads the file with its own Read tool. **The payload itself never travels through tmux send-keys** — only the pointer does. This avoids buffer limits, line-break corruption, and shell escaping issues with multi-line payloads.

Critical detail: the script makes **two** tmux send-keys calls — one for the literal message, one for the Enter key. Without the explicit Enter, the message sits at the receiver's prompt forever waiting on manual input. See `references/tmux-targeting.md` for the failure mode this prevents.

## Examples

**Agent hand-off mid-orchestration** (preferred path):
```
SendMessage({
  to: "archivist",
  message: "<payload as plain text>"
})
```

**Cross-tmux hand-off** between two claude processes:
```bash
cat <<'EOF' | scripts/handoff --to tmux:auto --from "lead-claude"
# Goal
Continue the v2.0 design conversation for the archivist plugin.

# Current state
- Plan written and approved (see Additional context)
- Issue #175 created with full design + open questions
- ...
EOF
```

**Human-mediated handoff** (no live receiver):
```bash
echo "$PAYLOAD" | scripts/handoff --to clipboard
# User pastes into a new Claude session
```

## References

- `references/payload-schema.md` — full per-section guidance, examples, and anti-patterns
- `references/tmux-targeting.md` — pane discovery algorithm, `--filter` semantics, security model, two-call Enter delivery
- `scripts/handoff --help` — current script interface (single source of truth)
