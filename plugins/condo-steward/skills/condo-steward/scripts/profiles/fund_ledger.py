# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Profile: fund-ledger

Layout used by several association-management accounting packages: a cover page,
then a Balance Sheet with Operating / Reserve / Total columns, Budget Comparison
reports (one per fund) with Month and Year-to-Date actual/budget/variance plus
Annual Budget, an Aged Accounts Receivable, a Prepaid report, an Accounts Payable
Aging, a Check Register, one Reconciliation Report per bank account, and General
Ledger detail.

Section boundaries are detected by report titles. Account lines are
"NNNN - Name" followed by money columns.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from datetime import datetime

# parse_statement adds scripts/ to sys.path before importing profiles.
from parse_statement import Line, mask_account_numbers, parse_money

# Lines that are never balance-sheet categories: page footers, dates, report boilerplate.
NOT_A_CATEGORY = re.compile(r"^(page\b|\d{1,2}/\d{1,2}/\d{4}$|balance sheet|unaudited|prepared by|as of\b)", re.I)

ACCOUNT_RE = re.compile(r"^(\d{4}) - (.+?)(?=\s-?\(?\$)")
DATE_RE = re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b")
SECTION_TITLES = {
    "Balance Sheet": "balance_sheet",
    "Budget Comparison Report - Operating": "budget_operating",
    "Budget Comparison Report - Reserve": "budget_reserve",
    "Aged Account Receivable": "ar_aging",
    "Aged Accounts Receivable": "ar_aging",
    "Prepaid Report": "prepaid",
    "Accounts Payable Aging Report": "ap_aging",
    "Check Register Report": "check_register",
    "Reconciliation Report": "reconciliation",
    "General Ledger Report": "general_ledger",
}


def _to_iso(s: str) -> str:
    return datetime.strptime(s, "%m/%d/%Y").date().isoformat()


def split_sections(lines: list[Line]) -> list[tuple[str, list[Line]]]:
    sections: list[tuple[str, list[Line]]] = []
    current = ("preamble", [])
    for ln in lines:
        title = SECTION_TITLES.get(ln.text.strip())
        if title:
            sections.append(current)
            current = (title, [])
        else:
            current[1].append(ln)
    sections.append(current)
    return [s for s in sections if s[1]]


# --------------------------------------------------------------------------- balance sheet


def parse_balance_sheet(chunks: list[list[Line]]) -> dict:
    """Balance sheet may span pages; each page repeats the column header."""
    accounts: list[dict] = []
    specials: dict[str, dict] = {}
    period_end = None
    category = None
    side = None
    cols: list[tuple[str, float]] = []  # (name, right-edge x)

    for lines in chunks:
        for ln in lines:
            text = ln.text.strip()
            if period_end is None and DATE_RE.fullmatch(text):
                period_end = _to_iso(text)
                continue
            heads = [t for t in ln.tokens if t.text in ("Operating", "Reserve", "Total")]
            if len(heads) >= 2 and not ln.money():
                cols = [(t.text.lower(), t.x1) for t in heads]
                if text.startswith("Liabilities"):
                    side = "liabilities_equity"
                elif side is None:
                    side = "assets"
                continue
            if text == "Assets":
                side = "assets"
                continue
            if text.startswith("Liabilities & Equity"):
                side = "liabilities_equity"
                continue

            money = ln.money()
            if not money:
                if text and not text.startswith("Total") and "Association" not in text \
                        and not NOT_A_CATEGORY.match(text):
                    category = text
                continue

            values = _assign_columns(money, cols)
            m = ACCOUNT_RE.match(text)
            if m:
                accounts.append({
                    "number": m.group(1),
                    "name": m.group(2).strip(),
                    "side": side,
                    "category": category,
                    **values,
                })
            else:
                label = re.sub(r"\s-?\(?\$.*$", "", text).strip()
                if label in ("Retained Earnings", "Net Income", "Assets Total",
                             "Liabilities and Equity Total") or label.startswith("Total "):
                    specials[label] = values

    return {"period_end": period_end, "accounts": accounts, "totals": specials}


def _assign_columns(money, cols) -> dict:
    """Right-aligned values: match each amount to the nearest column right edge."""
    out = {"operating": 0.0, "reserve": 0.0, "total": 0.0}
    if not cols:
        names = ["operating", "reserve", "total"][-len(money):]
        for (amt, _), n in zip(money, names):
            out[n] = amt
        return out
    for amt, tok in money:
        name = min(cols, key=lambda c: abs(c[1] - tok.x1))[0]
        out[name] = amt
    if out["total"] == 0.0 and (out["operating"] or out["reserve"]):
        out["total"] = round(out["operating"] + out["reserve"], 2)
    return out


BUDGET_FIELDS = ["month_actual", "month_budget", "month_variance",
                 "ytd_actual", "ytd_budget", "ytd_variance", "annual_budget"]


def _budget_columns(ln: Line) -> list[float] | None:
    """Right edges of the 7 budget columns from the header row
    'Actual Budget Variance Actual Budget Variance Annual Budget'."""
    heads = [t for t in ln.tokens if t.text in ("Actual", "Budget", "Variance")]
    if len(heads) < 7:
        return None
    return [t.x1 for t in heads[:7]]  # the 7th 'Budget' is the right edge of 'Annual Budget'


def _assign_budget(money, cols: list[float] | None) -> dict | None:
    if cols and len(money) < 7:
        vals = {}
        for amt, tok in money:
            idx = min(range(7), key=lambda i: abs(cols[i] - tok.x1))
            vals[BUDGET_FIELDS[idx]] = amt
        return {f: vals.get(f, 0.0) for f in BUDGET_FIELDS}
    if len(money) >= 7:
        return dict(zip(BUDGET_FIELDS, [a for a, _ in money[-7:]]))
    return None


# --------------------------------------------------------------------------- budget comparison


def parse_budget(lines: list[Line]) -> dict:
    periods = []
    rows: list[dict] = []
    totals: dict[str, dict] = {}
    group = None
    section = None
    cols = None
    for ln in lines:
        text = ln.text.strip()
        hdr = _budget_columns(ln)
        if hdr:
            cols = hdr
            continue
        dates = DATE_RE.findall(text)
        if len(dates) == 4 and not ln.money():  # "Month range   YTD range" header row
            periods = [(_to_iso(dates[0]), _to_iso(dates[1])), (_to_iso(dates[2]), _to_iso(dates[3]))]
            continue
        if len(dates) == 2 and not ln.money() and not periods:  # report title line
            periods = [(_to_iso(dates[0]), _to_iso(dates[1]))]
            continue
        money = ln.money()
        if not money:
            if text in ("Income", "Expense"):
                section = text.lower()
            elif text and not text.startswith(("Actual", "Total")) and "Association" not in text \
                    and "Inc." not in text:
                group = text
            continue
        fields = _assign_budget(money, cols)
        if fields is None:
            print(f"warn: budget line with {len(money)} values and no column header, skipped: {text[:60]}",
                  file=sys.stderr)
            continue
        m = ACCOUNT_RE.match(text)
        if m:
            rows.append({"number": m.group(1), "name": m.group(2).strip(),
                         "section": section, "group": group, **fields})
        else:
            label = re.sub(r"\s-?\(?\$.*$", "", text).strip()
            totals[label] = fields
    month = periods[0] if periods else (None, None)
    ytd = periods[1] if len(periods) > 1 else (None, None)
    return {"month": {"start": month[0], "end": month[1]},
            "ytd": {"start": ytd[0], "end": ytd[1]},
            "lines": rows, "totals": totals}


# --------------------------------------------------------------------------- aging reports


def parse_ar_aging(lines: list[Line], include_names: bool) -> dict:
    accounts: list[dict] = []
    totals = None
    for ln in lines:
        text = ln.text.strip()
        money = ln.money()
        if text.startswith("Totals:") and len(money) >= 5:
            totals = dict(zip(["current", "days_30", "days_60", "days_90", "total"],
                              [a for a, _ in money[-5:]]))
            continue
        if re.match(r"^\d{6,}\s", text) and money:
            amount, tok = money[-1]
            trailing = text[text.rfind(tok.text) + len(tok.text):].strip()
            entry = {"total_due": amount, "status": trailing or None}
            if include_names:
                acct, rest = text.split(None, 1)
                entry["account"] = mask_account_numbers(acct, min_digits=5)
                entry["detail"] = rest[: rest.find(tok.text)].strip()
            accounts.append(entry)
    return {
        "totals": totals,
        "account_count": len(accounts),
        "status_counts": dict(Counter(a["status"] or "unspecified" for a in accounts)),
        "accounts": accounts,
    }


def parse_ap_aging(lines: list[Line]) -> dict:
    totals = None
    invoices = 0
    for ln in lines:
        text = ln.text.strip()
        money = ln.money()
        if text.startswith("Totals:") and len(money) >= 5:
            totals = dict(zip(["total", "current", "days_30", "days_60", "days_90"],
                              [a for a, _ in money[-5:]]))
        elif re.search(r"\bTotal:", text) and money:
            invoices += 1
    return {"totals": totals, "invoice_count": invoices}


def parse_prepaid(lines: list[Line]) -> dict:
    for ln in lines:
        if ln.text.strip().startswith("Totals:") and ln.money():
            return {"total": ln.money()[-1][0]}
    return {"total": None}


# --------------------------------------------------------------------------- register & reconciliation

CHECK_RE = re.compile(r"^(\d{4})\s+(\S+)\s+(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s+(-?\(?\$[\d,]+\.\d{2}\)?)$")


def parse_check_register(lines: list[Line]) -> dict:
    checks = []
    total = None
    for ln in lines:
        text = ln.text.strip()
        m = CHECK_RE.match(text)
        if m:
            checks.append({"gl_account": m.group(1), "check": m.group(2),
                           "date": _to_iso(m.group(3)), "payee": m.group(4),
                           "amount": parse_money(m.group(5))})
        elif text.startswith("Total:") and ln.money():
            total = ln.money()[-1][0]
    return {"checks": checks, "total": total}


RECON_FIELDS = {
    "Statement Balance:": "statement_balance",
    "GL Balance:": "gl_balance",
    "Last Statement Balance:": "last_statement_balance",
    "Outstanding Checks:": "outstanding_checks",
    "Outstanding Deposits:": "outstanding_deposits",
    "Calculated Balance:": "calculated_balance",
    "GL vs. Balance Difference:": "difference",
}


def parse_reconciliation(lines: list[Line]) -> dict | None:
    rec: dict = {}
    for ln in lines:
        text = ln.text.strip()
        if "Statement Balance:" in text and "Last" not in text:
            head = text.split("Statement Balance:")[0].strip()
            m = re.match(r"^(.*?) - (.+)-(\d{4})$", head)
            if m:
                rec.update(bank=m.group(1), account_name=m.group(2), gl_account=m.group(3))
        m = re.search(r"Statement Date:\s*(\d{1,2}/\d{1,2}/\d{4})", text)
        if m:
            rec["statement_date"] = _to_iso(m.group(1))
        for label, key in RECON_FIELDS.items():
            if label in text and not (label == "Statement Balance:" and "Last Statement Balance:" in text):
                tail = text.split(label, 1)[1]
                mm = re.search(r"-?\(?\$[\d,]+\.\d{2}\)?", tail)
                if mm:
                    rec[key] = parse_money(mm.group())
    if "gl_account" not in rec:
        return None
    rec.setdefault("difference", None)  # None = not found on the page; never assume it ties
    return rec


# --------------------------------------------------------------------------- entry point


def parse(lines: list[Line], include_names: bool = False) -> dict:
    sections = split_sections(lines)
    entity = None
    for name, body in sections:
        if name == "preamble" and body:
            texts = [l.text.strip() for l in body[:6]]
            for i, t in enumerate(texts):
                if t and "Statements" not in t and "Prepared" not in t \
                        and not re.fullmatch(r"[A-Z][a-z]+ \d{4}", t):
                    entity = t
                    if t.endswith(",") and i + 1 < len(texts):  # "…Association," / "Inc." wrapped
                        entity = f"{t} {texts[i + 1]}"
                    break
            break

    balance_chunks = [b for n, b in sections if n == "balance_sheet"]
    result = {
        "entity": entity,
        "balance_sheet": parse_balance_sheet(balance_chunks) if balance_chunks else None,
        "budget": {},
        "ar_aging": None,
        "ap_aging": None,
        "prepaid": None,
        "check_register": None,
        "reconciliations": [],
    }
    seen_recon = set()
    for name, body in sections:
        if name == "budget_operating":
            result["budget"]["operating"] = _merge_budget(result["budget"].get("operating"), parse_budget(body))
        elif name == "budget_reserve":
            result["budget"]["reserve"] = _merge_budget(result["budget"].get("reserve"), parse_budget(body))
        elif name == "ar_aging" and result["ar_aging"] is None:
            result["ar_aging"] = parse_ar_aging(body, include_names)
        elif name == "ap_aging" and result["ap_aging"] is None:
            result["ap_aging"] = parse_ap_aging(body)
        elif name == "prepaid":
            result["prepaid"] = parse_prepaid(body)
        elif name == "check_register" and result["check_register"] is None:
            result["check_register"] = parse_check_register(body)
        elif name == "reconciliation":
            rec = parse_reconciliation(body)
            if rec and rec["gl_account"] not in seen_recon:
                seen_recon.add(rec["gl_account"])
                result["reconciliations"].append(rec)

    bs = result["balance_sheet"]
    result["period_end"] = (bs or {}).get("period_end") or (
        result["budget"].get("operating", {}).get("month", {}).get("end"))
    return result


def _merge_budget(existing: dict | None, new: dict) -> dict:
    """Budget reports paginate; later pages carry more lines and the totals."""
    if not existing:
        return new
    existing["lines"].extend(new["lines"])
    existing["totals"].update(new["totals"])
    for k in ("month", "ytd"):
        if not existing[k]["end"] and new[k]["end"]:
            existing[k] = new[k]
    return existing
