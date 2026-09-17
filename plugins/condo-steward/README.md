# condo-steward

Help owners and board members understand and run a condominium, HOA, or cooperative. Reads the management company's monthly financial statement, builds a local HTML report that answers the questions people actually ask, and explains Florida community-association law — while being clear about when an attorney, CPA, reserve specialist, or engineer has to be the one to decide.

The plugin contains **no data about any particular community**. Everything specific lives in your project's `community.toml` and your own documents.

## Commands

Thin command files in `commands/` expose the scripts; the single `condo-steward` skill holds the scripts, references, and tests.

| Command | What it does |
|---|---|
| `/condo-steward:init` | Create `community.toml` (name, units, type, statements folder, review thresholds) |
| `/condo-steward:report [file\|folder]` | Parse the latest statement(s) → `reports/<slug>-<YYYY-MM>.html` and summarize the flags |
| `/condo-steward:trend [folder]` | Same report across every month on file, with a trend section |
| `/condo-steward:statute <topic>` | What Florida Ch. 718 / 720 / FAC 61B say, applied to your numbers, with who must confirm |
| `/condo-steward:ask <question>` | Record a question in the community's private ledger; answer, list, and promote generalizable answers back to the skill |
| `/condo-steward:scan [folder]` | Find files exposing full account numbers before they hit a shared drive or repo |

## What the report answers

Where is our money (by fund, reconciled?) · Are we on budget (month, YTD, lines running over) · Are reserves funded (contributions vs plan, component balances) · Who owes us / what do we owe (aging, loans) · Trend · **What needs attention** — rule-based flags with the professional to ask.

## Scripts (PEP 723, run with `uv`)

```bash
S=skills/condo-steward/scripts
uv run $S/parse_statement.py statement.pdf -o statement.json     # PDF → JSON
uv run $S/report.py --dir Financials/Statements                  # PDFs/JSON → HTML
uv run $S/parse_transactions.py bank-export.xlsx -o tx.json         # CSV/XLSX → masked transactions
uv run $S/scan_sensitive.py "Shared Drive/Financials"                # exit 1 if full account numbers found
uv run $S/questions.py add "Do we need an audit this year?"         # private question ledger
uv run $S/init_config.py --name "…Association, Inc." --units 24  # community.toml
uv run skills/condo-steward/tests/test_parse.py                  # smoke tests (synthetic fixture)
```

The parser is **profile-based**. `fund-ledger` handles the common layout (balance sheet by fund → budget comparison → aging → check register → reconciliations). Other management packages: add a module under `scripts/profiles/` per `references/statement-profiles.md`.

## Privacy

- Every script masks 8+ digit numbers (bank, ACH, owner account IDs) to their last four in all output — there is no flag to turn this off. Reports show account name + last four.
- Owner names and units are dropped unless `--include-names` is passed, and are never rendered in the report.
- `scan_sensitive.py` checks a folder for unmasked numbers; `references/data-handling.md` says what belongs in a shared drive, a board-only folder, or the treasurer's password manager.
- Test fixtures are synthetic. Do not commit real statements, bank exports, or `community.toml` to a shared repository.

## Input formats

| Source | Has | Use for |
|---|---|---|
| Monthly statement **PDF** (manager) | balance sheet by fund, budget vs actual, aging, reconciliations, check register | the report — richest structured source today |
| Manager GL/statement **XLSX/CSV** export | same, without PDF parsing risk | preferred if the portal offers it — add a profile |
| Bank activity **CSV/XLSX** | transactions only, full account numbers | verifying a reconciliation, sweep behaviour, spend by payee |

## The learning loop

Questions a community asks are recorded in its own `questions/ledger.jsonl` (private, JSONL). When an answer would help any community, `questions.py promote` prints a sanitized candidate row/bullet/friction report — a person reviews it and places it in `references/common-questions.md`, a Florida reference, or files it via foundry. The skill never reads the ledger; the community never loses its institutional memory.

## Law coverage

Every legal answer cites the section and links the official text (Online Sunshine / flrules.org). Florida first: Chapter 718 (condominiums), Chapter 720 (HOAs), FAC 61B (budgets, reserves, financial reporting), and the post-2022 structural framework (milestone inspections, SIRS). Each reference carries an "as of" date and the official source to verify against — the Legislature changes these every year. Add other states under `references/<state>/`.

## Requirements

- [uv](https://docs.astral.sh/uv/) (Python 3.11+ resolved automatically)
- Statements as text-based PDFs (scanned images need OCR first)
