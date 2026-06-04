---
description: Hand off the current work context to another Claude — teammate (SendMessage), separate tmux pane, clipboard, or file
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/*), Bash(tmux:*), Bash(pbcopy), Bash(xclip:*), Bash(wl-copy), Read, AskUserQuestion, SendMessage
---

<!--
/handoff - Transfer current work context to another Claude with a structured payload.
Usage:
  /handoff                              → auto-select transport (teammate if available, else clipboard)
  /handoff to:teammate <name>           → SendMessage to a teammate
  /handoff to:tmux                      → pick first claude-running pane
  /handoff to:tmux <session>            → specific session (lowest pane)
  /handoff to:tmux <session:window.pane> → explicit address
  /handoff to:clipboard                 → pbcopy / xclip
  /handoff to:file <path>               → write to path (chmod 600)

Free-text after the transport is treated as the handoff intent (Goal section).
-->

## Procedure

You are being asked to hand off the current session's work to another Claude. The handoff transport is encoded in the user's arguments above; if no transport is named, auto-select one.

### Step 1: Pick the transport

| User specified | Action |
|---|---|
| `to:teammate <name>` | Use the SendMessage tool — see Step 4a below. Do NOT invoke the script. |
| `to:tmux ...` | Use the script's `tmux:` mode — Step 4b. |
| `to:clipboard` | Use the script's `clipboard` mode — Step 4c. |
| `to:file <path>` | Use the script's `file:<path>` mode — Step 4c. |
| nothing specified | Auto-select: if active teammates exist in this team, ask which one (AskUserQuestion); else default to `clipboard` and inform the user. |

### Step 2: Load the payload schema

Read `${CLAUDE_PLUGIN_ROOT}/skills/handoff/references/payload-schema.md` for the 8-section structure. The schema is the same regardless of transport.

### Step 3: Build the payload

From the current conversation, construct a Markdown payload with the 8 sections per the schema. Required sections: Goal, Current state, Decisions made, Next steps. Optional sections: include only if genuinely populated — do not write empty stubs.

If the user gave free-text after the transport (e.g., `/handoff to:tmux continue the v2 design conversation`), use it as the Goal sentence verbatim or as direct input to the Goal.

Confirm the payload looks complete before delivery. For non-trivial handoffs, show the payload to the user first and ask for approval.

### Step 4a: Deliver via SendMessage (teammate)

Call the SendMessage tool:

```
SendMessage({
  to: "<teammate-name>",
  summary: "Handoff: <one-line goal>",
  message: "<full payload as plain text>"
})
```

The teammate receives it as their next conversation turn. Confirm to the user that the handoff was sent.

### Step 4b: Deliver via tmux

Read `${CLAUDE_PLUGIN_ROOT}/skills/handoff/references/tmux-targeting.md` if the user's target was unusual (no-filter override, multi-pane session, etc.) — otherwise the defaults are safe.

Invoke the script with the payload piped on stdin:

```bash
cat <<'PAYLOAD' | ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/handoff --to tmux:<target> --from "<this-session-identifier>"
<full payload>
PAYLOAD
```

`--filter claude` is applied automatically. Report the script's stdout (which includes `handoff: sent to <pane> (payload at <file>)`) so the user sees both the destination and the temp file path.

### Step 4c: Deliver via clipboard or file

```bash
echo "<payload>" | ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/handoff --to clipboard
# or
echo "<payload>" | ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/handoff --to file:/path/to/handoff.md
```

Report success and (for clipboard) tell the user the payload is ready to paste. For file, report the path and the `chmod 600` enforcement.

### Step 5: Confirm and stop

Tell the user the handoff is delivered. Do not continue the underlying work — the receiver picks it up. If the user wants to keep working in this session afterward, that's a separate request.
