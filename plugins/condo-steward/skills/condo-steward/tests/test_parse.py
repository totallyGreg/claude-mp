#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pdfplumber>=0.11"]
# ///
"""
Smoke tests for parse_statement.py and report.py against the synthetic fixture.

    uv run tests/test_parse.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import parse_statement  # noqa: E402
import parse_transactions  # noqa: E402
import report  # noqa: E402
import scan_sensitive  # noqa: E402
from profiles import fund_ledger  # noqa: E402

FIXTURE = HERE / "fixtures" / "sample-statement.txt"
BANK_FIXTURE = HERE / "fixtures" / "sample-bank-export.csv"


def check(cond: bool, msg: str, failures: list[str]) -> None:
    if not cond:
        failures.append(msg)


def main() -> int:
    failures: list[str] = []
    stmt = fund_ledger.parse(parse_statement.load_lines(FIXTURE))
    stmt["source"] = {"file": FIXTURE.name, "profile": "fund-ledger"}

    check(stmt["entity"] == "Example Condominium Association, Inc.", "entity", failures)
    check(stmt["period_end"] == "2026-03-31", "period_end", failures)
    bs = stmt["balance_sheet"]
    by = {a["number"]: a for a in bs["accounts"]}
    check(by["1010"]["operating"] == 41250.10 and by["1010"]["reserve"] == 0.0, "operating column", failures)
    check(by["1110"]["reserve"] == 120500.55 and by["1110"]["operating"] == 0.0, "reserve column", failures)
    check(bs["totals"]["Net Income"]["total"] == 5000.0, "net income total", failures)
    op = stmt["budget"]["operating"]
    check(op["ytd"] == {"start": "2026-01-01", "end": "2026-03-31"}, "ytd period", failures)
    check(op["totals"]["Total Expense"]["annual_budget"] == 240000.0, "annual expense budget", failures)
    check(len(op["lines"]) == 6, "operating lines", failures)
    check(stmt["ar_aging"]["totals"]["days_90"] == 8000.0, "ar 90-day bucket", failures)
    check(stmt["ar_aging"]["status_counts"] == {"Statement": 1, "At Attorney": 1}, "ar statuses", failures)
    check("detail" not in stmt["ar_aging"]["accounts"][0], "names omitted by default", failures)
    check(stmt["ap_aging"]["totals"]["total"] == 7300.0, "ap total", failures)
    check(stmt["check_register"]["total"] == 5900.0 and len(stmt["check_register"]["checks"]) == 3, "checks", failures)
    recs = {r["gl_account"]: r for r in stmt["reconciliations"]}
    check(recs["1010"]["statement_balance"] == 41250.10, "statement balance not clobbered by 'last'", failures)
    check(recs["1110"]["difference"] == 100.0, "recon difference", failures)

    cfg = report.load_config(None)
    m = report.metrics(stmt, cfg)
    check(m["cash_operating"] == 71250.10, "cash_operating", failures)
    check(m["cash_reserve"] == 120500.55, "cash_reserve", failures)
    check(m["months_operating_cash"] == 3.2, f"months of cash {m['months_operating_cash']}", failures)  # excludes prepaid assessments
    check(m["loan_total"] == 40000.0, "loan total", failures)
    check(m["delinquency_ratio"] == 0.035, "delinquency ratio", failures)
    fl = report.flags(m, cfg)
    check(any("reconciliation" in f["text"].lower() for f in fl), "recon flag raised", failures)
    check(any("90+" in f["text"] for f in fl), "90-day flag raised", failures)

    html = report.render([(stmt, m)], cfg, date(2026, 4, 1))
    check("Unit 101 Owner" not in html and "Example Way" not in html, "no owner detail in html", failures)
    check("$71,250.10" in html and "$120,500.55" in html, "kpis rendered", failures)
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "r.html"
        out.write_text(html)
        check(out.stat().st_size > 5000, "html written", failures)

    # masking
    mask = parse_statement.mask_account_numbers
    check(mask("Acct No. 987654321055-D and $1,234,567.89 and 7/31/2026 and 1003")
          == "Acct No. ****1055-D and $1,234,567.89 and 7/31/2026 and 1003", "mask keeps money/dates/GL codes", failures)
    check(mask("to Acct 123456789012.") == "to Acct ****9012.", "mask before sentence period", failures)
    check(mask("card 1234 5678 9012 and 1234-5678-9012") == "card ****9012 and ****9012", "mask grouped digits", failures)
    check(mask('{"date": "2026-03-31", "check": "100285"}') == '{"date": "2026-03-31", "check": "100285"}',
          "mask leaves ISO dates and 6-digit check numbers", failures)
    check(mask("Check # 20012345") == "Check # ****2345", "8-digit check numbers are masked (documented)", failures)

    # robustness: footer line must not become a category; missing recon difference is unknown, not "ties"
    text = FIXTURE.read_text().replace("Cash-Operating\n", "Cash-Operating\nPage 1 of 3\n", 1)
    text = text.replace("GL vs. Balance Difference:  $0.00", "")
    tmp = HERE / "fixtures" / "_probe.txt"
    tmp.write_text(text)
    try:
        probe = fund_ledger.parse(parse_statement.load_lines(tmp))
        probe["source"] = {"file": "probe", "profile": "fund-ledger"}
        probe = report.load_statement(tmp, "fund-ledger")  # exercise normalisation too
    finally:
        tmp.unlink()
    check(probe["balance_sheet"]["accounts"][0]["category"] == "Cash-Operating", "page footer ignored as category", failures)
    probe_rec = {r["gl_account"]: r for r in probe["reconciliations"]}
    check(probe_rec["1010"]["difference"] is None, "missing difference is None", failures)
    pm = report.metrics(probe, cfg)
    check(len(pm["recon_unknown"]) == 1, "unknown recon surfaced", failures)
    check(any("Do not assume these tie" in f["text"] for f in report.flags(pm, cfg)), "unknown recon flagged", failures)
    check("? difference not read" in report.render([(probe, pm)], cfg, date(2026, 4, 1)), "unknown recon rendered", failures)

    # null sections from a sparse profile must not crash
    with tempfile.TemporaryDirectory() as td:
        sparse = Path(td) / "sparse.json"
        sparse.write_text(json.dumps({"entity": "X", "period_end": "2026-01-31",
                                      "balance_sheet": {"accounts": [], "totals": {}},
                                      "budget": None, "reconciliations": None, "ar_aging": None,
                                      "ap_aging": None, "prepaid": None, "check_register": None,
                                      "source": {"file": "sparse.json", "profile": "test"}}))
        sp = report.load_statement(sparse, "fund-ledger")
        spm = report.metrics(sp, cfg)
        spf = report.flags(spm, cfg)
        check(any("No cash accounts" in f["text"] for f in spf), "no-cash flag", failures)
        check(len(report.render([(sp, spm)], cfg, date(2026, 2, 1))) > 1000, "sparse renders", failures)

    # transaction export
    rows = parse_transactions.read_rows(BANK_FIXTURE, None)
    cols = parse_transactions.detect_columns(list(rows[0].keys()))
    txs = parse_transactions.normalize(rows, cols)
    check(cols["amount"] == "DebitCredit" and cols["date"] == "Date", f"column detection {cols}", failures)
    check([t["amount"] for t in txs] == [-1000.0, 2200.0, -1200.0, 1200.0], "amounts sorted by date", failures)
    summ = parse_transactions.summarize(txs)
    check(summ["inflow"] == 3400.0 and summ["outflow"] == -2200.0 and summ["transfer_count"] == 1, "summary", failures)
    check(summ["pending_count"] == 1, "pending count", failures)
    dumped = parse_statement.mask_account_numbers(json.dumps({"summary": summ, "transactions": txs}))
    check("123456789012" not in dumped and "987654321098" not in dumped and "****9055" in dumped, "export masked", failures)
    check(not scan_sensitive.find_numbers(dumped, 8), "scanner finds nothing in masked output", failures)
    check(scan_sensitive.find_numbers(BANK_FIXTURE.read_text(), 8), "scanner finds raw export", failures)

    if failures:
        print("FAIL:\n  " + "\n  ".join(failures))
        return 1
    print(f"ok — {len(bs['accounts'])} accounts, {len(op['lines'])} budget lines, {len(fl)} flags")
    return 0


if __name__ == "__main__":
    sys.exit(main())
