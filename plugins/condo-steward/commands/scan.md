---
description: Scan a folder (e.g. a shared drive) for files exposing full bank or account numbers before syncing or committing
argument-hint: [folder-or-file]
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/scripts/*), Bash(ls:*), Read, AskUserQuestion
---

## Procedure

Arguments: `$ARGUMENTS`

1. Resolve the path (argument, else `community.toml → statements_dir`, else ask).
2. Run:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/scripts/scan_sensitive.py "<path>"
```

3. Report each flagged file in one line with the masked samples the script printed — never re-print a full number even if the user pastes one. Distinguish the usual sources:
   - bank **exports** (CSV/XLSX): expect full account IDs → recommend `parse_transactions.py` and sharing the masked JSON, moving the raw export out of the shared folder;
   - statement **PDFs**: usually owner account numbers and invoice numbers on aging pages → Personal tier; keep in a board-only folder;
   - generated reports/JSON from this plugin: should be clean — if not, that is a bug; say so.
4. Point to `references/data-handling.md` for the tiering rules if the user asks what should live where.
