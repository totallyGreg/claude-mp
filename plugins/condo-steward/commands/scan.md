---
description: Scan a folder (e.g. a shared drive) for files exposing full bank or account numbers before syncing or committing
argument-hint: [folder-or-file]
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/scripts/*), Bash(ls:*), Read, AskUserQuestion
---

Follow the **scan** workflow in `${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/references/workflows.md`, running scripts from `${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/`.

Arguments: `$ARGUMENTS`
