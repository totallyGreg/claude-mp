---
description: Parse the latest financial statement(s) and generate a local HTML report answering the key questions a board or owner has
argument-hint: [file|folder]
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/scripts/*), Bash(open:*), Bash(xdg-open:*), Bash(ls:*), Read, Glob, AskUserQuestion
---

Follow the **report** workflow in `${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/references/workflows.md`, running scripts from `${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/`.

Arguments: `$ARGUMENTS`
