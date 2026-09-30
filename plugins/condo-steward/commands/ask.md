---
description: Record a board or owner question in the community's private ledger, answer it, and promote generalizable answers back toward the skill
argument-hint: <question> | answer <id> | list | promote <id>
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/scripts/*), Read, Glob, AskUserQuestion
---

Follow the **ask** workflow in `${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/references/workflows.md`, running scripts from `${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/`.

Arguments: `$ARGUMENTS`
