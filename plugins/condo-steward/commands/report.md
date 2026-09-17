---
description: Parse the latest financial statement(s) and generate a local HTML report answering the key questions a board or owner has
argument-hint: [file|folder]
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/scripts/*), Bash(open:*), Bash(xdg-open:*), Bash(ls:*), Read, Glob, AskUserQuestion
---

## Procedure

Arguments: `$ARGUMENTS`

1. Resolve the input. If the user gave a path, use it. Otherwise read `community.toml` in the working directory for `statements_dir`; if neither exists, ask for the folder (and offer `/condo-steward:init`).
2. Run the report from the project root (community.toml and relative paths resolve against the working directory):

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/scripts/report.py --dir "<folder>"
# or: uv run ${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/scripts/report.py "<file.pdf>"
```

   The script prints the output path (default `reports/<slug>-<YYYY-MM>.html`). If it reports "no balance sheet/period found" for a file, the layout may need a new profile — see `references/statement-profiles.md`.

3. Open the report for the user (`open <path>` on macOS, `xdg-open` on Linux; otherwise just give the path) and, in chat, list the **What needs attention** flags in one or two lines each, with the professional to involve where the report names one.
4. Offer the natural next step: a targeted question about a flagged line, or `/condo-steward:trend` if only one month was on file and more exist.

Do not paste the HTML into chat. Do not include owner names in any summary.
