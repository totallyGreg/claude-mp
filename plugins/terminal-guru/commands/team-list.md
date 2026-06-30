---
name: team-list
description: List active teammates in the current session's team — names, agent types, agent IDs, and how to address them via SendMessage.
allowed-tools: Bash, Read
---

Show all currently-active teammates in this session's team. Source of truth is the team config file at `~/.claude/teams/session-<id>/config.json` (where `<id>` is the first 8 chars of the session ID).

## Step 1: Verify the experimental flag

If `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is not set to `1`, no team is set up — report that and stop. See `/team-spawn` for the flag setup.

```bash
echo "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-<unset>}"
```

## Step 2: Locate the team config

The team config is named `session-<first-8-of-session-id>`. Find the most recently modified one (the current session's):

```bash
ls -td ~/.claude/teams/session-* 2>/dev/null | head -1
```

If nothing is returned: no team is set up yet. Either no teammates have been spawned, or the flag isn't taking effect. Report this and suggest `/team-spawn`.

## Step 3: Read and present the members

Read `config.json` from the team directory. The `members` array contains each teammate's `name`, `agent_id`, and `agent_type`. Present as a table:

```markdown
| Name | Agent Type | Agent ID |
|------|-----------|----------|
| ...  | ...       | ...      |
```

If the team config has a `tmux_pane_id` field per member (split-pane mode), include a **Pane** column with the `%N` ID.

## Step 4: Surface addressing reminders

After the table, print:

```markdown
**Address a teammate**: `SendMessage({to: "<name>", message: "..."})`
**Shut down**: `SendMessage({to: "<name>", message: {type: "shutdown_request"}})`
**Spawn another**: `/team-spawn <type> <name> <prompt>`
```

If any teammate row in `config.json` looks stale (e.g., its tmux pane is gone), flag it — idle teammates hide from the agent panel after 30 seconds but their config row persists. Use `tmux list-panes -a -F '#{pane_id}'` to verify pane existence if split-pane mode is in use.
