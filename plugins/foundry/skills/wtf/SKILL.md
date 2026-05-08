---
name: wtf
description: >-
  This skill should be used PROACTIVELY to "create a friction report",
  "check for broken tooling", or "run a friction check" when you hit confusing
  errors, bad docs, missing prereqs, broken tools, misleading skills, flaky tests,
  auth/MCP failures, or any "this should've been easier" moment. Also trigger when
  the user says "file an issue", "report this friction", "log this feedback", "wtf",
  or "this should be easier".
  Do NOT use for fixing the friction itself (use skillsmith or agentsmith instead).
metadata:
  author: J. Greg Williams
  version: "1.0.0"
compatibility: claude-code
license: MIT
---

# WTF — Work the Foundry

File friction reports so the foundry's improve workflows can fix real pain.

## When to File

- You hit unexpected friction during a task (confusing errors, missing docs, broken tools)
- A skill file is incomplete, wrong, or misleading
- A workflow required unnecessary trial-and-error to figure out
- You have a concrete suggestion for improving DX

## How to File

Identify the friction source from your current context, then run:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/wtf/scripts/submit-issue.sh \
  --type <type> \
  --name "<plugin:name>" \
  --category <category> \
  --description "<one-line summary of the friction>" \
  --project "<working directory>" \
  --session "<session id>"
```

### Arguments

| Arg | Values | Required |
|-----|--------|----------|
| `--type` | `skill`, `agent`, `tool`, `workflow` | No (defaults to `unknown`) |
| `--name` | Plugin-qualified name, e.g. `foundry:skillsmith`, `archivist:archivist` | No |
| `--category` | `bad-docs`, `broken-tool`, `misleading-skill`, `missing-prereq`, `auth-failure`, `flaky`, `other` | No (defaults to `other`) |
| `--description` | One-line friction summary | **Yes** |
| `--project` | Current working directory path | No |
| `--session` | Current session ID | No |

### Identifying the Source

You always know what you're doing. Use your current context:
- If a skill is loaded, use its `plugin:skill` name
- If an agent was spawned, use its `plugin:subagent_type`
- If a raw tool failed, use `tool` type with the tool name
- If a workflow broke, use `workflow` type with a descriptive name

## After Filing

**Continue your current task immediately.** Friction reporting is a side-effect — never interrupt the user's work to report friction. File the report and move on.

### Example

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/wtf/scripts/submit-issue.sh \
  --type skill --name "archivist:archivist" --category misleading-skill \
  --description "Health check reported 0 orphans but vault has 12 unlinked notes"
```

## Where Reports Go

Reports are stored in `.local/agent-issues/reports/` (gitignored, never committed). They are consumed by `/ss-improve` and `/as-improve` as advisory context when improving the reported skill or agent.
