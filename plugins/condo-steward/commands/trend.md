---
description: Compare several months of financial statements — cash, receivables, reserves, and results over time
argument-hint: [folder]
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/scripts/*), Bash(open:*), Bash(xdg-open:*), Bash(ls:*), Read, Glob, AskUserQuestion
---

## Procedure

Arguments: `$ARGUMENTS`

1. Resolve the folder as in `/condo-steward:report`. Confirm it holds at least two statements (`ls`); if only one, say so and run a single-month report instead.
2. Run:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/scripts/report.py --dir "<folder>"
```

   With more than one month the report gains a **Trend** section (month-end balances with sparklines). The latest month is the focus for KPIs and flags.

3. Open the report and summarize in chat: direction of operating cash, reserve cash, receivables, and YTD result — three or four sentences, with figures and periods. Point out any month where a reconciliation did not tie.
4. If the user wants a specific line over time (e.g., utilities), parse each statement to JSON with `parse_statement.py` and tabulate that line's `month_actual` by period — no script changes needed.
