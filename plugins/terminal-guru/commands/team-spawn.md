---
name: team-spawn
description: Spawn a persistent teammate agent — forcing function that always passes the name field so the teammate is addressable via SendMessage instead of becoming an ephemeral one-shot subagent.
argument-hint: <subagent-type> <name> <prompt...>
allowed-tools: Agent, Bash, Read
---

Spawn a **persistent teammate** by calling the `Agent` tool with all three required fields: `subagent_type`, `name`, and `prompt`. The `name` field is the ONLY thing that distinguishes a persistent teammate from a one-shot ephemeral subagent — without it, `SendMessage` cannot reach the spawned agent.

## Step 0: Parse arguments

`$ARGUMENTS` is structured as `<subagent-type> <name> <prompt...>`:

- **TYPE** = first whitespace-separated token
- **NAME** = second whitespace-separated token
- **PROMPT** = everything after the second token (preserve newlines)

If TYPE or NAME is missing, ask the user before proceeding. Do not guess values. If PROMPT is empty, ask the user for the spawn brief — teammates don't inherit the lead's conversation history, so a substantive prompt is mandatory.

## Step 1: Verify the experimental flag

Agent teams are gated behind `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Without it, no team is set up at session start and the Agent tool spawns a one-shot subagent regardless of the `name` field.

```bash
echo "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-<unset>}"
```

If the value is not `1`, tell the user:

> Agent teams require `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Add this to `~/.claude/settings.json`:
> ```json
> { "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
> ```
> Then restart the session. Without the flag, this command will spawn a one-shot subagent that is not addressable by name.

Ask whether to proceed anyway (one-shot) or abort. Do not silently degrade.

## Step 2: Verify the agent type

Confirm TYPE matches one of the agent types currently available to the `Agent` tool — the harness surfaces these in a system-reminder near the top of the conversation. Look for `<plugin>:<name>` entries (e.g., `archivist:archivist`, `foundry:skill-observer`) or bare names (e.g., `general-purpose`, `Explore`).

If TYPE is not in the list, present the available types and ask the user to pick one. Do not call the Agent tool with an unknown type — it will fail after-the-fact and the user will think the spawn worked.

## Step 3: Spawn

Call the `Agent` tool with exactly these three fields:

- `subagent_type`: TYPE
- `name`: NAME
- `prompt`: PROMPT

Do not pass `team_name` — that field is accepted but ignored as of Claude Code v2.1.178.

If the user has a tmux split-pane teammate mode active (`teammateMode: "auto"` or `"tmux"` in settings), the spawn creates a new tmux pane. Capture the new pane's `%N` ID for the next step.

## Step 4: Report

Present:

```markdown
**Spawned**: <NAME> (type: <TYPE>)
**Agent ID**: <id returned by Agent tool>
**Pane**: <%N if split-pane, otherwise "in-process (agent panel, ↑/↓ + Enter)">

**Address it**:
- Message: `SendMessage({to: "<NAME>", message: "..."})`
- Shut down: `SendMessage({to: "<NAME>", message: {type: "shutdown_request"}})`
- List active teammates: `/team-list`
```

If a new tmux pane was created and the user is using the pane-labeling pattern (`tmux set -p -t %N @label NAME`), offer to set the label so the pane border shows the teammate name.
