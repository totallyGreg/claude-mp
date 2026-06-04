---
name: Tmux Targeting & Security
description: How the handoff script discovers tmux panes, what --filter claude does, why the two-call Enter delivery matters, and the security model for cross-pane delivery.
load_when: Sending a handoff via tmux transport; debugging a delivery that didn't reach the receiver; understanding why --filter is mandatory by default.
---

# Tmux Targeting & Security

The `tmux:` transport delivers a one-line pointer message to a specific tmux pane. The receiver Claude reads the payload file (chmod 600) referenced in the pointer.

This skill ships its own pane discovery — **no dependency on terminal-guru or any external tmux helper**. Only `tmux` itself is required.

## Target syntax

| Target | Behavior |
|---|---|
| `tmux:auto` | Pick the first pane that passes `--filter`. Warns if multiple match. |
| `tmux:my-session` | Session name → resolves to the session's lowest-index pane. Warns if multiple panes. |
| `tmux:my-session:1.0` | Explicit `session:window.pane` address. Used as-is. Must still pass `--filter`. |

## Pane discovery algorithm

1. `tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index}\t#{pane_current_command}'` builds the full pane list (tab-delimited address + current command).
2. If a filter is set, `grep -E` narrows to panes whose current command matches.
3. Resolution per target type (see table above).
4. The chosen pane address is used for `tmux send-keys -t <pane>`.

If no panes match after filtering, the script exits with a clear error before any delivery.

## The `--filter claude` default

**For any `tmux:` target, the script applies `--filter claude` by default.** This is a security default, not a convenience. Two reasons:

1. **Avoid delivering to shell prompts.** If you send `Read /tmp/handoff-xxx.md and acknowledge.` to a pane running `bash`, the shell tries to execute `Read` as a command — it fails noisily, but a more cleverly crafted pointer could be turned into a shell injection vector. Restricting delivery to panes running `claude` (or another agent process you trust) eliminates the class.
2. **Avoid wrong-target delivery.** Without a filter, `tmux:auto` would pick the first pane in tmux's enumeration order — which is rarely the agent pane you meant. Explicit filtering forces a deliberate selection.

Override only when you know the receiver and accept the risk:

```bash
scripts/handoff --to tmux:my-shell:0.0 --no-filter
# or
scripts/handoff --to tmux:auto --filter 'claude|node'
```

## Two-call delivery: the Enter character matters

The script makes **two** `tmux send-keys` calls per delivery:

```bash
tmux send-keys -t "$pane" -l "[handoff from agent] Read /tmp/handoff-12345-1717520000.md and acknowledge."
tmux send-keys -t "$pane" Enter
```

The `-l` flag on the first call means "send literally" — every character of the message is delivered as-is, with no interpretation of key names. This is correct for the message body.

The second call has **no** `-l` — so `Enter` is interpreted as the Return key.

**Why this matters:** a common failure mode of naive tmux relay implementations is to send the message without the explicit Enter. The text arrives in the receiver pane and sits at the prompt, waiting for the user to manually press Return. The handoff appears delivered (it shows in the pane) but the receiver never sees it as input — the agent just hangs.

If you write your own tmux relay code, **always make the second call**.

## Security model

The transport's threat model assumes:
- Sender and receiver are **the same user** on the same machine (typical dev workflow).
- An attacker with shell access to that user account can read anything anyway — handoff isn't a defense against local compromise.
- The risks worth mitigating are **accidental** exposure (other-user readable temp files on shared systems, leaking payload content to unintended panes, shell-injection via crafted paths).

Specific mitigations the script applies:

| Risk | Mitigation |
|---|---|
| Other users on the system reading the temp file | `chmod 600` immediately on creation; `umask 077` during write |
| Stale temp files accumulating | Sweep old `handoff-*.md` files (>1 day) on each invocation |
| Shell injection via crafted file path | Path validation: `^[/a-zA-Z0-9._-]+$`, reject otherwise |
| Payload content captured by pane sniffers (`tmux capture-pane` from a third pane) | Only the pointer (file path) appears in pane output; payload stays in chmod-600 file |
| Wrong pane receives the pointer and executes it as a command | Mandatory `--filter claude` by default |

What the script does **not** defend against:
- Compromise of the user account (out of scope)
- Receiver pane being a Claude instance owned by a different user (single-user assumption)
- Network-attached tmux sessions where the wire is untrusted (the script does no encryption — file lives in local `/tmp`)

## Debugging a delivery that didn't arrive

If the receiver pane doesn't react:

1. **Confirm the pointer appeared in the pane.** Run `tmux capture-pane -p -t <target>` from another shell and look for the `[handoff from ...]` line.
2. **If the pointer appeared but the receiver didn't act:** the Enter key probably didn't fire. Check the script invocation made two `tmux send-keys` calls.
3. **If the pointer didn't appear:** the target resolution failed silently or the filter excluded the pane. Re-run with `--from debug` and verify the script's stdout shows the resolved pane address.
4. **Confirm the temp file exists and is readable** by the receiver: `ls -la /tmp/handoff-*.md`. Mode should be `-rw-------` (600).

## Related

- `payload-schema.md` — what goes in the payload file the pointer references
- `scripts/handoff --help` — current CLI interface
