# Statement profiles — adding support for another management package

`scripts/parse_statement.py` turns a PDF into a list of `Line` objects, each holding tokens with horizontal positions. A **profile** in `scripts/profiles/` turns those lines into the JSON the report needs. Ship one profile per distinct layout.

## Contract

```python
def parse(lines: list[Line], include_names: bool = False) -> dict
```

Return this shape (keys may be `None` when a section is absent; the report degrades gracefully):

```jsonc
{
  "entity": "…Association, Inc.",
  "period_end": "YYYY-MM-DD",
  "balance_sheet": {
    "period_end": "…",
    "accounts": [{"number": "1003", "name": "…", "side": "assets|liabilities_equity",
                  "category": "Cash-Operating", "operating": 0.0, "reserve": 0.0, "total": 0.0}],
    "totals": {"Total Reserves": {"operating": …, "reserve": …, "total": …}, "Net Income": {…}}
  },
  "budget": {
    "operating": {"month": {"start","end"}, "ytd": {"start","end"},
                  "lines": [{"number","name","section":"income|expense","group",
                             "month_actual","month_budget","month_variance",
                             "ytd_actual","ytd_budget","ytd_variance","annual_budget"}],
                  "totals": {"Total Income": {...}, "Total Expense": {...}, "Net Income": {...}}},
    "reserve": { same shape }
  },
  "ar_aging": {"totals": {"current","days_30","days_60","days_90","total"},
               "account_count": 0, "status_counts": {}, "accounts": [{"total_due","status"}]},
  "ap_aging": {"totals": {"total","current","days_30","days_60","days_90"}, "invoice_count": 0},
  "prepaid": {"total": 0.0},
  "check_register": {"checks": [{"gl_account","check","date","payee","amount"}], "total": 0.0},
  "reconciliations": [{"bank","account_name","gl_account","statement_date","statement_balance",
                       "gl_balance","outstanding_checks","outstanding_deposits","difference"}]
}
```

What the report relies on most: balance-sheet `category` strings starting with `Cash` (to split operating vs reserve cash), `Receivable`, `Current Liab`, `Reserve`; budget `totals` named `Total Income`, `Total Expense`, `Net Income`; a line whose name contains `assessment` (annual assessments); reconciliation `difference`.

## Writing a profile

1. Extract text once to see the layout: `uv run parse_statement.py statement.pdf` with a throwaway profile that just prints `ln.text`, or `pdftotext -layout` if you have poppler.
2. Identify **section titles** and map them to the keys above (`SECTION_TITLES` in `fund_ledger.py` is the pattern).
3. For multi-column reports (balance sheet by fund), read the header tokens' `x1` (right edge) and assign each money token to the nearest column — right-aligned numbers make this reliable. `_assign_columns` shows the idiom.
4. For fixed-column reports (budget comparison), read the header row for column right edges and assign by nearest edge so blank cells do not shift values; fall back to the last N money tokens when no header is found (`_assign_budget`).
5. Build a **synthetic fixture** in `tests/fixtures/` with a fictional association and round numbers. Never commit a real statement or real owner data. Text fixtures work because `load_lines()` treats character offsets as x-positions.
6. Add assertions to `tests/test_parse.py` (or a sibling file) and run `uv run tests/test_parse.py`.
7. Register the profile name in `SKILL.md` and, if it should be the default for a community, set `profile = "<name>"` under `[community]` in that community's `community.toml` (`report.py` reads it; `--profile` overrides).

## Privacy rules for every profile

- Owner names, unit numbers, email addresses: only emitted when `include_names=True`, and the report never renders them. Owner account numbers are masked even then (`mask_account_numbers(..., min_digits=5)`).
- Every 8+ digit run in any output is masked by the callers; profiles need not repeat it but must not undo it. 8-digit check/invoice numbers get masked as collateral — acceptable.
- Vendor names in the check register are business records and are kept.
- Never write extracted data anywhere except where the user directs (`-o`).
