# Workflows

Step-by-step procedures for the user-facing tasks. Paths are relative to this skill's root; in Claude Code the `commands/` files invoke these as `/condo-steward:<name>` and prefix paths with `${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/`. Any other agent can follow them directly.

## init

Create community.toml for this association project — name, size, where statements live, and review thresholds.

### Procedure

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
uv run scripts/init_config.py \
  --name "<name>" --units <n> --type <type> --state <ST> \
  --fiscal-year-start <m> --statements-dir "<dir>" --reports-dir "<dir>"
```

4. Remind the user that `community.toml` is theirs and private — add it to `.gitignore` if the project is shared — and offer `/condo-steward:report`.

## report `[file|folder]`

Parse the latest financial statement(s) and generate a local HTML report answering the key questions a board or owner has.

### Procedure

1. Resolve the input. If the user gave a path, use it. Otherwise read `community.toml` in the working directory for `statements_dir`; if neither exists, ask for the folder (and offer `/condo-steward:init`).
2. Run the report from the project root (community.toml and relative paths resolve against the working directory):

```bash
uv run scripts/report.py --dir "<folder>"
# or: uv run scripts/report.py "<file.pdf>"
```

   The script prints the output path (default `reports/<slug>-<YYYY-MM>.html`). If it reports "no balance sheet/period found" for a file, the layout may need a new profile — see `references/statement-profiles.md`.

3. Open the report for the user (`open <path>` on macOS, `xdg-open` on Linux; otherwise just give the path) and, in chat, list the **What needs attention** flags in one or two lines each, with the professional to involve where the report names one.
4. Offer the natural next step: a targeted question about a flagged line, or `/condo-steward:trend` if only one month was on file and more exist.

Do not paste the HTML into chat. Do not include owner names in any summary.

## trend `[folder]`

Compare several months of financial statements — cash, receivables, reserves, and results over time.

### Procedure

1. Resolve the folder as in `/condo-steward:report`. Confirm it holds at least two statements (`ls`); if only one, say so and run a single-month report instead.
2. Run:

```bash
uv run scripts/report.py --dir "<folder>"
```

   With more than one month the report gains a **Trend** section (month-end balances with sparklines). The latest month is the focus for KPIs and flags.

3. Open the report and summarize in chat: direction of operating cash, reserve cash, receivables, and YTD result — three or four sentences, with figures and periods. Point out any month where a reconciliation did not tie.
4. If the user wants a specific line over time (e.g., utilities), parse each statement to JSON with `parse_statement.py` and tabulate that line's `month_actual` by period — no script changes needed.

## statute `<topic>`

Look up what Florida law says on a community-association topic (reserves, records, meetings, elections, assessments, fines, SIRS) with the professional to confirm it.

### Procedure

1. Determine the association type: `community.toml → type` if present (condominium → Ch. 718, hoa → Ch. 720, cooperative → treat as 718). If unknown, ask — the answer differs.
2. Read the relevant section of the matching file under `references/florida/`:
   - governance, records, budgets, assessments, fines, meetings, elections → `ch718-condominiums.md` or `ch720-hoa.md`
   - structural reserves, inspections, 3+ story buildings → `sirs-milestone-inspections.md`
   - reserve math, year-end report contents → `fac-61b-financial-reporting.md`
3. Answer in this order:
   - the operative rule, with section number and the concrete thresholds (days, dollars, vote fraction);
   - how it applies to this community if numbers or facts are at hand (revenue tier, delinquency, building height);
   - what the community's own declaration/bylaws might change — say plainly if you have not seen them;
   - which professional must confirm before acting, and why (per `references/professional-escalation.md`).
4. Close with the "as of" date from the reference file and the official link (<https://www.leg.state.fl.us/statutes/>). If the topic is one the Legislature changed recently (reserves, SIRS, records website, board education, fines), say so explicitly and offer to fetch the current text.

Keep it to the question asked. Do not draft notices, liens, or fine letters — offer to outline the required contents for the attorney instead.

## scan `[folder-or-file]`

Scan a folder (e.g. a shared drive) for files exposing full bank or account numbers before syncing or committing.

### Procedure

1. Resolve the path (argument, else `community.toml → statements_dir`, else ask).
2. Run:

```bash
uv run scripts/scan_sensitive.py "<path>"
```

3. Report each flagged file in one line with the masked samples the script printed — never re-print a full number even if the user pastes one. Distinguish the usual sources:
   - bank **exports** (CSV/XLSX): expect full account IDs → recommend `parse_transactions.py` and sharing the masked JSON, moving the raw export out of the shared folder;
   - statement **PDFs**: usually owner account numbers and invoice numbers on aging pages → Personal tier; keep in a board-only folder;
   - generated reports/JSON from this plugin: should be clean — if not, that is a bug; say so.
4. Point to `references/data-handling.md` for the tiering rules if the user asks what should live where.

## ask `<question> | answer <id> | list | promote <id>`

Record a board or owner question in the community's private ledger, answer it, and promote generalizable answers back toward the skill.

### Procedure

The ledger lives in the community project (`questions/ledger.jsonl`, or `questions_file` in `community.toml`). It is private; nothing is written into the plugin.

1. **New question** (`/condo-steward:ask <question>`): first try to answer it — check `references/common-questions.md`, the statements, and the Florida references. Then record it regardless of outcome so the board keeps a memory:

   ```bash
   uv run scripts/questions.py add "<question>" [--by <role>] [--tag <topic>]
   ```

   If you answered it, immediately record the answer (step 2). If not, leave it open and say what would be needed (a document, a professional, more data).

2. **Answer** (`/condo-steward:ask answer <id>`): record the answer with its sources (statement period, reference file and section, statute link). If the *question* would apply to any community, give its community-neutral form with `--general` — that is what makes it promotable:

   ```bash
   uv run …/questions.py answer <id> "<answer>" --source "<source>" [--source …] [--general "<neutral question>"]
   ```

3. **List** (`/condo-steward:ask list`): `questions.py list --open` (default) or `--generalizable` to see promotion candidates. Render the markdown table the script prints.

4. **Promote** (`/condo-steward:ask promote <id>`): `questions.py promote <id> --target common-questions|florida|friction`. The script only **prints** a candidate. Review it with the user, strip anything community-specific, and then either place it in the plugin repo yourself (if the user maintains the plugin) or hand it to `/foundry:ss-wtf` as a friction report. After placing, `questions.py mark <id> --promoted-to "<file#anchor>"`.

Account numbers are masked on the way into the ledger; owner names are not — do not put them in questions or answers.
