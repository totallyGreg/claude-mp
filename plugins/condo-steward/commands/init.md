---
description: Create community.toml for this association project — name, size, where statements live, and review thresholds
disable-model-invocation: true
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/scripts/*), Bash(ls:*), Read, Glob, AskUserQuestion
---

## Procedure

Arguments: `$ARGUMENTS`

1. If `community.toml` already exists in the working directory, show it and ask whether to overwrite (`--force`) or stop.
2. Gather, asking only for what you cannot infer from the folder:
   - legal name of the association (a statement PDF's cover page has it — parse one if handy);
   - number of units/parcels;
   - type: condominium / hoa / cooperative;
   - state (default FL);
   - fiscal year start month (default 1);
   - folder holding monthly statements (look for PDFs named by month);
   - where to write reports (default `reports`).
   Thresholds keep their defaults unless the user has opinions (2–6 months operating cash, 5% delinquency, 10% variance).
3. Run:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/scripts/init_config.py \
  --name "<name>" --units <n> --type <type> --state <ST> \
  --fiscal-year-start <m> --statements-dir "<dir>" --reports-dir "<dir>"
```

4. Remind the user that `community.toml` is theirs and private — add it to `.gitignore` if the project is shared — and offer `/condo-steward:report`.
