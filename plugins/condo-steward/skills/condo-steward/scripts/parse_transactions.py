#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl>=3.1"]
# ///
"""
Normalize a bank or portal transaction export (CSV or XLSX) into masked JSON.

Bank activity exports are transaction-level: useful for checking a reconciliation,
seeing sweep behaviour, or totalling spend by payee — but they carry no fund split
or budget, so the monthly statement PDF remains the source for the report.

Every account-like number (8+ digits) in any field is masked to its last four
digits before anything is written. There is no flag to disable this.

Usage:
    uv run parse_transactions.py <export.csv|export.xlsx> [--sheet NAME] [-o out.json]

Column detection is by header name (case-insensitive, first match wins):
    date         : date, posted, transaction date
    description  : description, memo, details, payee, transaction
    amount       : amount, debitcredit, debit/credit          (signed)
                   or separate debit + credit columns          (unsigned)
    balance      : balance, running balance
    account      : accountnickname, account name, account, accountid
    type         : type, transaction type, transaction
    status       : status
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_statement import mask_account_numbers  # noqa: E402

COLUMN_HINTS = {
    "date": ["transaction date", "posted", "post date", "date"],
    "description": ["description", "memo", "details", "payee"],
    "amount": ["debitcredit", "debit/credit", "amount"],
    "debit": ["debit", "withdrawal"],
    "credit": ["credit", "deposit"],
    "balance": ["running balance", "balance"],
    "account": ["accountnickname", "account name", "account nickname", "account", "accountid"],
    "type": ["transaction type", "type", "transaction"],
    "status": ["status"],
}
DATE_FORMATS = ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y", "%d-%b-%Y", "%b %d, %Y")


def read_rows(path: Path, sheet: str | None) -> list[dict]:
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        import warnings

        import openpyxl

        warnings.filterwarnings("ignore", module="openpyxl")
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb[sheet] if sheet else wb.active
        it = ws.iter_rows(values_only=True)
        header = [str(h).strip() if h is not None else "" for h in next(it)]
        return [dict(zip(header, r)) for r in it if any(v is not None for v in r)]
    sys.exit(f"unsupported input: {path.suffix} (use .csv or .xlsx)")


def detect_columns(header: list[str]) -> dict[str, str]:
    low = {h.lower().strip(): h for h in header}
    found: dict[str, str] = {}
    for role, hints in COLUMN_HINTS.items():
        for hint in hints:
            match = next((orig for k, orig in low.items() if k == hint or hint in k), None)
            if match and match not in found.values():
                found[role] = match
                break
    if "amount" not in found and not ("debit" in found and "credit" in found):
        sys.exit(f"could not find an amount column in header: {header}")
    if "date" not in found:
        sys.exit(f"could not find a date column in header: {header}")
    return found


def to_number(v) -> float | None:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("$", "").replace(",", "")
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        return -float(s) if neg else float(s)
    except ValueError:
        return None


def to_date(v) -> str | None:
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.date().isoformat()
    s = str(v).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def normalize(rows: list[dict], cols: dict[str, str]) -> list[dict]:
    out = []
    for r in rows:
        if "amount" in cols:
            amount = to_number(r.get(cols["amount"]))
        else:
            debit = to_number(r.get(cols["debit"])) or 0.0
            credit = to_number(r.get(cols["credit"])) or 0.0
            amount = credit - abs(debit)
        d = to_date(r.get(cols["date"]))
        if d is None or amount is None:
            continue
        tx = {
            "date": d,
            "amount": round(amount, 2),
            "type": _clean(r.get(cols["type"])) if "type" in cols else None,
            "description": _clean(r.get(cols["description"])) if "description" in cols else None,
            "status": _clean(r.get(cols["status"])) if "status" in cols else None,
            "balance": to_number(r.get(cols["balance"])) if "balance" in cols else None,
            "account": _clean(r.get(cols["account"])) if "account" in cols else None,
        }
        out.append(tx)
    out.sort(key=lambda t: t["date"])
    return out


def _clean(v) -> str | None:
    if v is None:
        return None
    return mask_account_numbers(re.sub(r"\s+", " ", str(v)).strip()) or None


def summarize(txs: list[dict]) -> dict:
    inflow = round(sum(t["amount"] for t in txs if t["amount"] > 0), 2)
    outflow = round(sum(t["amount"] for t in txs if t["amount"] < 0), 2)
    by_type: dict[str, dict] = defaultdict(lambda: {"count": 0, "total": 0.0})
    for t in txs:
        key = re.sub(r"\s*#?\s*\d+$", "", t["type"] or "unspecified").strip() or "unspecified"
        by_type[key]["count"] += 1
        by_type[key]["total"] = round(by_type[key]["total"] + t["amount"], 2)
    by_month: dict[str, dict] = defaultdict(lambda: {"in": 0.0, "out": 0.0, "count": 0})
    for t in txs:
        m = by_month[t["date"][:7]]
        m["count"] += 1
        m["in" if t["amount"] > 0 else "out"] = round(m["in" if t["amount"] > 0 else "out"] + t["amount"], 2)
    transfers = [t for t in txs if re.search(r"transfer|sweep", (t["type"] or "") + " " + (t["description"] or ""), re.I)]
    return {
        "date_range": {"start": txs[0]["date"], "end": txs[-1]["date"]} if txs else None,
        "transaction_count": len(txs),
        "inflow": inflow,
        "outflow": outflow,
        "net": round(inflow + outflow, 2),
        "first_balance": txs[0]["balance"] if txs else None,
        "last_balance": txs[-1]["balance"] if txs else None,
        "accounts": dict(Counter(t["account"] or "unspecified" for t in txs)),
        "by_type": dict(sorted(by_type.items())),
        "by_month": dict(sorted(by_month.items())),
        "transfer_count": len(transfers),
        "transfer_net": round(sum(t["amount"] for t in transfers), 2),
        "pending_count": sum(1 for t in txs if (t["status"] or "").lower() not in ("", "cleared", "posted")),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("export", type=Path)
    ap.add_argument("--sheet", help="worksheet name for xlsx (default: active sheet)")
    ap.add_argument("-o", "--output", type=Path)
    args = ap.parse_args()
    if not args.export.exists():
        sys.exit(f"not found: {args.export}")

    rows = read_rows(args.export, args.sheet)
    if not rows:
        sys.exit("no rows")
    cols = detect_columns(list(rows[0].keys()))
    txs = normalize(rows, cols)
    result = {
        "source": {"file": args.export.name, "columns": cols},
        "summary": summarize(txs),
        "transactions": txs,
    }
    text = mask_account_numbers(json.dumps(result, indent=2))
    if args.output:
        args.output.write_text(text)
        print(f"wrote {args.output}  ({len(txs)} transactions, {result['summary']['date_range']})")
    else:
        print(text)


if __name__ == "__main__":
    main()
