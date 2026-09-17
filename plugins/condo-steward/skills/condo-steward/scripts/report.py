#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pdfplumber>=0.11"]
# ///
"""
Build a self-contained HTML report from one or more monthly financial statements.

Answers the questions boards and owners ask most: How much cash do we have and
in which fund? Are we on budget? Are reserves funded as planned? Who owes us and
what do we owe? Do the bank accounts reconcile? With several months, adds trends.

Usage:
    uv run report.py <statement.pdf|.json> [more ...] [--config community.toml] [-o report.html]
    uv run report.py --dir <folder-of-statements> [--config community.toml] [-o report.html]

Inputs may be statement PDFs (parsed on the fly via parse_statement.py) or JSON
already produced by it. Months are ordered by period end; the latest is the
focus month. Output defaults to ./reports/<entity-slug>-<period>.html.

The report contains only aggregate figures. Owner-level receivable detail is never
rendered even if present in the JSON.
"""

from __future__ import annotations

import argparse
import html
import importlib
import json
import re
import sys
import tomllib
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import parse_statement  # noqa: E402

DEFAULT_THRESHOLDS = {
    "operating_cash_months_min": 2.0,
    "operating_cash_months_max": 6.0,
    "delinquency_ratio_warn": 0.05,   # receivables / annual assessments
    "budget_variance_warn": 0.10,     # |YTD variance| / YTD budget
    "budget_variance_min_dollars": 500.0,  # ignore small-dollar lines in the watch list
    "variance_sign": -1,              # -1: negative variance = unfavorable (most packages); 1: flipped
}


# --------------------------------------------------------------------------- loading


def load_config(path: Path | None) -> dict:
    candidates = [path] if path else [Path("community.toml"), Path(".community.toml")]
    for c in candidates:
        if c and c.exists():
            cfg = tomllib.loads(c.read_text())
            cfg.setdefault("thresholds", {})
            cfg["thresholds"] = {**DEFAULT_THRESHOLDS, **cfg["thresholds"]}
            return cfg
    return {"community": {}, "thresholds": dict(DEFAULT_THRESHOLDS)}


def load_statement(path: Path, profile: str) -> dict:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text())
    else:
        mod = importlib.import_module(f"profiles.{profile.replace('-', '_')}")
        data = mod.parse(parse_statement.load_lines(path))
        data["source"] = {"file": path.name, "profile": profile}
    # Normalize the profile contract: absent sections become empty, never None.
    data.setdefault("budget", {})
    data["budget"] = data["budget"] or {}
    for key in ("reconciliations",):
        data[key] = data.get(key) or []
    for key in ("ar_aging", "ap_aging", "prepaid", "check_register"):
        data[key] = data.get(key) or {}
    bs = data.get("balance_sheet") or {}
    bs.setdefault("accounts", [])
    bs.setdefault("totals", {})
    data["balance_sheet"] = bs
    return json.loads(parse_statement.mask_account_numbers(json.dumps(data)))


# --------------------------------------------------------------------------- metrics


def _acct_sum(bs: dict, column: str, category_match: str, side: str | None = None) -> float:
    return round(sum(
        a[column] for a in bs["accounts"]
        if re.search(category_match, a["category"] or "", re.I) and (side is None or a["side"] == side)
    ), 2)


def _find_line(budget: dict, pattern: str) -> dict | None:
    for ln in budget.get("lines", []):
        if re.search(pattern, ln["name"], re.I):
            return ln
    return None


def metrics(stmt: dict, cfg: dict) -> dict:
    bs = stmt["balance_sheet"]
    op = stmt["budget"].get("operating", {"lines": [], "totals": {}})
    rs = stmt["budget"].get("reserve", {"lines": [], "totals": {}})
    t = cfg["thresholds"]

    cash_accounts = [a for a in bs["accounts"] if a["side"] == "assets" and re.search(r"^cash", a["category"] or "", re.I)]
    cash_op = round(sum(a["operating"] for a in cash_accounts), 2)
    cash_res = round(sum(a["reserve"] for a in cash_accounts), 2)
    receivables = _acct_sum(bs, "total", r"receivable", "assets")
    prepaid_assess = round(sum(a["total"] for a in bs["accounts"] if re.search(r"prepaid assess", a["name"], re.I)), 2)
    current_liabilities = _acct_sum(bs, "total", r"^current liab", "liabilities_equity")
    # Prepaid assessments are owed as service, not cash — exclude from the liquidity calculation.
    cash_claims = round(current_liabilities - prepaid_assess, 2)
    if not cash_accounts:
        print(f"warn: no cash accounts recognised in {stmt.get('source', {}).get('file')} "
              f"(categories: {sorted({a['category'] for a in bs['accounts'] if a['category']})})", file=sys.stderr)
    loans = [a for a in bs["accounts"] if a["side"] == "liabilities_equity"
             and re.search(r"loan|note|mortgage|line of credit", a["name"], re.I)]
    reserve_components = [a for a in bs["accounts"] if a["side"] == "liabilities_equity"
                          and re.search(r"^reserve", a["category"] or "", re.I)]

    exp_tot = op["totals"].get("Total Expense", {})
    inc_tot = op["totals"].get("Total Income", {})
    net_tot = op["totals"].get("Net Income", {})
    annual_expense = exp_tot.get("annual_budget") or 0.0
    monthly_expense = annual_expense / 12 if annual_expense else None
    # Regular assessments only: exclude special assessments, fees, interest, fines.
    assess_lines = [ln for ln in op.get("lines", []) if ln.get("section") != "expense"
                    and re.search(r"assessment", ln["name"], re.I)
                    and not re.search(r"special|late|fee|interest|fine", ln["name"], re.I)]
    annual_assessments = round(sum(ln["annual_budget"] for ln in assess_lines), 2) or inc_tot.get("annual_budget", 0.0)

    months_cash = round((cash_op - cash_claims) / monthly_expense, 1) if monthly_expense else None
    delinquency_ratio = round(receivables / annual_assessments, 4) if annual_assessments else None

    res_inc = rs["totals"].get("Total Income", {})
    res_exp = rs["totals"].get("Total Expense", {})
    contrib_line = _find_line(rs, r"funding|contribution|assessment")

    # Budget lines materially over budget YTD (expense) or under (income)
    sign = t["variance_sign"]
    watch = []
    for ln in op.get("lines", []):
        unfavorable = ln["ytd_variance"] * sign > 0
        if ln["ytd_budget"] and unfavorable and abs(ln["ytd_variance"]) >= t["budget_variance_min_dollars"] \
                and abs(ln["ytd_variance"]) / abs(ln["ytd_budget"]) >= t["budget_variance_warn"]:
            watch.append(ln)
    watch.sort(key=lambda l: -abs(l["ytd_variance"]))

    recons = stmt["reconciliations"]
    recon_issues = [r for r in recons if r.get("difference") is not None and abs(r["difference"]) > 0.005]
    recon_unknown = [r for r in recons if r.get("difference") is None]
    recon_missing = [a for a in cash_accounts if a["number"] not in {r["gl_account"] for r in recons}]

    return {
        "period_end": stmt["period_end"],
        "cash_operating": cash_op,
        "cash_reserve": cash_res,
        "receivables": receivables,
        "current_liabilities": current_liabilities,
        "cash_accounts": cash_accounts,
        "prepaid_assessments": round(prepaid_assess, 2),
        "loans": loans,
        "loan_total": round(sum(a["total"] for a in loans), 2),
        "monthly_expense_budget": monthly_expense,
        "months_operating_cash": months_cash,
        "annual_assessments": annual_assessments,
        "delinquency_ratio": delinquency_ratio,
        "income": inc_tot, "expense": exp_tot, "net": net_tot,
        "reserve_income": res_inc, "reserve_expense": res_exp,
        "reserve_contribution": contrib_line,
        "reserve_fund_balance": bs["totals"].get("Total Reserves", {}).get("reserve"),
        "reserve_components": reserve_components,
        "watch_lines": watch[:8],
        "ar": stmt.get("ar_aging") or {},
        "ap": stmt.get("ap_aging") or {},
        "reconciliations": stmt["reconciliations"],
        "recon_issues": recon_issues,
        "recon_unknown": recon_unknown,
        "recon_missing": recon_missing,
        "check_total": (stmt.get("check_register") or {}).get("total"),
        "check_count": len((stmt.get("check_register") or {}).get("checks", [])),
    }


def flags(m: dict, cfg: dict) -> list[dict]:
    """Rule-based observations. Each carries a severity and, where relevant, who to ask."""
    t = cfg["thresholds"]
    sign = t["variance_sign"]
    is_condo = cfg.get("community", {}).get("type", "condominium") != "hoa"
    out = []

    def add(sev, text, ask=None):
        out.append({"severity": sev, "text": text, "ask": ask})

    if not m["cash_accounts"]:
        add("high", "No cash accounts were recognised on the balance sheet — the figures below are not "
                    "trustworthy. The statement layout may need a new parser profile.", "manager / maintainer")

    mc = m["months_operating_cash"]
    if mc is not None:
        if mc < t["operating_cash_months_min"]:
            add("high", f"Operating cash net of payables covers {mc} months of budgeted expenses "
                        f"(target ≥ {t['operating_cash_months_min']}). Cash is tight.", "CPA / manager")
        elif mc > t["operating_cash_months_max"]:
            add("info", f"Operating cash net of payables covers {mc} months of budgeted expenses "
                        f"(above {t['operating_cash_months_max']}). Consider whether surplus should fund "
                        f"reserves, reduce debt, or be held deliberately.", "CPA")
    if m["delinquency_ratio"] is not None and m["delinquency_ratio"] >= t["delinquency_ratio_warn"]:
        add("medium", f"Receivables are {m['delinquency_ratio']:.1%} of annual assessments "
                      f"(${m['receivables']:,.0f}). Review the collection policy and statutory notice steps.",
            "association attorney")
    ar = m["ar"].get("totals") or {}
    if ar.get("days_90"):
        add("medium", f"${ar['days_90']:,.0f} of receivables is 90+ days past due.", "association attorney")
    if m["recon_issues"]:
        names = ", ".join(r["account_name"] for r in m["recon_issues"])
        add("high", f"Bank reconciliation difference on: {names}. Ask the manager to explain before approving.",
            "CPA")
    if m["recon_unknown"]:
        names = ", ".join(r["account_name"] for r in m["recon_unknown"])
        add("medium", f"Reconciliation found but no 'GL vs. balance difference' line could be read for: {names}. "
                      f"Do not assume these tie.", "manager")
    if m["recon_missing"]:
        names = ", ".join(f"{a['number']} {a['name']}" for a in m["recon_missing"])
        add("medium", f"No reconciliation report in the package for: {names}. Every cash account should have one.",
            "manager")
    ytd_var = m["expense"].get("ytd_variance")
    ytd_bud = m["expense"].get("ytd_budget")
    if ytd_var is not None and ytd_bud and ytd_var * sign > 0 and abs(ytd_var) / ytd_bud >= t["budget_variance_warn"]:
        add("medium", f"Total operating expenses are ${abs(ytd_var):,.0f} over budget year-to-date "
                      f"({abs(ytd_var) / ytd_bud:.1%}).")
    net_ytd = m["net"].get("ytd_actual")
    if net_ytd is not None and net_ytd < 0:
        add("medium", f"Operating fund is running a year-to-date deficit of ${-net_ytd:,.0f}.")
    contrib = m["reserve_contribution"]
    if contrib and contrib["ytd_actual"] + 0.01 < contrib["ytd_budget"]:
        add("high", f"Reserve contributions are behind budget: ${contrib['ytd_actual']:,.0f} of "
                    f"${contrib['ytd_budget']:,.0f} year-to-date."
                    + (" Statutory reserve funding may be affected." if is_condo
                       else " Check whether these reserves are statutory or board-elected."),
            "association attorney / reserve specialist")
    neg = [a for a in m["reserve_components"] if a["reserve"] < 0]
    if neg:
        add("info", "Some reserve component balances are negative (" +
            ", ".join(a["name"] for a in neg) + "). Ask how components are presented — "
            "pooled vs. straight-line — and whether the schedule matches the reserve study.", "CPA")
    if m["cash_reserve"] is not None and m["reserve_fund_balance"] is not None \
            and abs(m["cash_reserve"] - m["reserve_fund_balance"]) > 1.0:
        add("medium", f"Reserve cash (${m['cash_reserve']:,.0f}) differs from the reserve fund balance "
                      f"(${m['reserve_fund_balance']:,.0f}). Reserve money may be commingled or owed between funds.",
            "CPA")
    if m["loan_total"]:
        add("info", f"Outstanding loans: ${m['loan_total']:,.0f}.")
    if not out:
        add("info", "No rule-based flags this month.")
    return out


# --------------------------------------------------------------------------- html


def money(v, blank="—") -> str:
    if v is None:
        return blank
    s = f"${abs(v):,.2f}"
    return f"({s})" if v < 0 else s


def pct(v) -> str:
    return "—" if v is None else f"{v:.1%}"


def esc(s) -> str:
    return html.escape(parse_statement.mask_account_numbers(str(s if s is not None else "")))


def variance_cell(v, sign: int = -1) -> str:
    """Show the package's own variance figure; colour by favourability per variance_sign."""
    v = v or 0
    cls = "neg" if v * sign > 0 else "pos" if v else ""
    return f'<td class="num {cls}">{money(v)}</td>'


def sparkline(values: list[float], width=160, height=36) -> str:
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    pts = []
    for i, v in enumerate(values):
        if v is None:
            continue
        x = i * (width - 4) / (len(values) - 1) + 2
        y = height - 2 - (v - lo) / span * (height - 4)
        pts.append(f"{x:.1f},{y:.1f}")
    return (f'<svg class="spark" viewBox="0 0 {width} {height}" width="{width}" height="{height}">'
            f'<polyline fill="none" stroke="currentColor" stroke-width="1.5" points="{" ".join(pts)}"/></svg>')


def render(months: list[tuple[dict, dict]], cfg: dict, generated: date) -> str:
    stmt, m = months[-1]
    entity = cfg.get("community", {}).get("name") or stmt.get("entity") or "Community Association"
    units = cfg.get("community", {}).get("units")
    sign = cfg["thresholds"]["variance_sign"]
    fl = flags(m, cfg)
    sev_order = {"high": 0, "medium": 1, "info": 2}
    fl.sort(key=lambda f: sev_order[f["severity"]])

    def kpi(label, value, sub=""):
        return f'<div class="kpi"><div class="label">{esc(label)}</div><div class="value">{value}</div><div class="sub">{sub}</div></div>'

    parts = [f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(entity)} — Financial Report {esc(m['period_end'])}</title>
<style>
:root{{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#6b6a66;--card:#fff;--line:#e4e1da;--pos:#1f7a4d;--neg:#b3261e;--warn:#9a6b00;--accent:#2f5d8a}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#161615;--fg:#ecebe6;--muted:#a3a19a;--card:#1f1f1d;--line:#33332f;--pos:#5fc48f;--neg:#ff7b72;--warn:#e0b04b;--accent:#8ab4e8}}}}
:root[data-theme=dark]{{--bg:#161615;--fg:#ecebe6;--muted:#a3a19a;--card:#1f1f1d;--line:#33332f;--pos:#5fc48f;--neg:#ff7b72;--warn:#e0b04b;--accent:#8ab4e8}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
main{{max-width:1040px;margin:0 auto;padding:24px 16px 64px}}h1{{font-size:1.6rem;margin:0 0 4px}}h2{{font-size:1.15rem;margin:36px 0 12px;border-bottom:1px solid var(--line);padding-bottom:6px}}
.meta{{color:var(--muted);font-size:.9rem}}.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-top:20px}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}}.kpi .label{{font-size:.8rem;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}}
.kpi .value{{font-size:1.45rem;font-weight:600;margin:4px 0}}.kpi .sub{{font-size:.85rem;color:var(--muted)}}
table{{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:.92rem}}
th,td{{padding:8px 10px;text-align:left;border-top:1px solid var(--line)}}th{{background:transparent;color:var(--muted);font-weight:600;font-size:.8rem;text-transform:uppercase;letter-spacing:.04em;border-top:none}}
td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}.pos{{color:var(--pos)}}.neg{{color:var(--neg)}}
.flag{{display:flex;gap:10px;align-items:flex-start;background:var(--card);border:1px solid var(--line);border-left:4px solid var(--line);border-radius:8px;padding:10px 12px;margin-bottom:8px}}
.flag.high{{border-left-color:var(--neg)}}.flag.medium{{border-left-color:var(--warn)}}.flag.info{{border-left-color:var(--accent)}}
.flag .sev{{font-size:.72rem;font-weight:700;text-transform:uppercase;min-width:58px;padding-top:3px}}.flag .ask{{color:var(--muted);font-size:.85rem}}
.q{{color:var(--muted);font-size:.9rem;margin:-6px 0 10px}}.spark{{color:var(--accent);vertical-align:middle}}
.note{{background:var(--card);border:1px dashed var(--line);border-radius:8px;padding:12px 14px;font-size:.88rem;color:var(--muted);margin-top:36px}}
@media (max-width:640px){{table{{display:block;overflow-x:auto}}}}
</style></head><body><main>
<h1>{esc(entity)}</h1>
<div class="meta">Financial report for the period ending <strong>{esc(m['period_end'])}</strong>
{f"· {esc(units)} units" if units else ""} · generated {generated.isoformat()} from {esc(stmt.get('source', {}).get('file', '?'))}
{f"· {len(months)} months on file" if len(months) > 1 else ""}</div>
"""]

    # --- KPIs
    parts.append('<div class="kpis">')
    parts.append(kpi("Operating cash", money(m["cash_operating"]),
                     f"{m['months_operating_cash']} months of expenses, net of payables" if m["months_operating_cash"] is not None else ""))
    parts.append(kpi("Reserve cash", money(m["cash_reserve"]),
                     f"fund balance {money(m['reserve_fund_balance'])}" if m["reserve_fund_balance"] is not None else ""))
    parts.append(kpi("Owed to us", money(m["receivables"]),
                     f"{pct(m['delinquency_ratio'])} of annual assessments" if m["delinquency_ratio"] is not None else ""))
    parts.append(kpi("We owe", money(m["current_liabilities"]),
                     f"incl. {money(m['prepaid_assessments'])} prepaid by owners" if m["prepaid_assessments"] else ""))
    parts.append(kpi("YTD operating result", money(m["net"].get("ytd_actual")),
                     f"budget {money(m['net'].get('ytd_budget'))}"))
    parts.append(kpi("Loans outstanding", money(m["loan_total"]) if m["loan_total"] else "None"))
    parts.append("</div>")

    # --- Flags
    parts.append("<h2>What needs attention</h2>")
    for f in fl:
        ask = f'<div class="ask">Consider asking: {esc(f["ask"])}</div>' if f["ask"] else ""
        parts.append(f'<div class="flag {f["severity"]}"><div class="sev">{f["severity"]}</div><div>{esc(f["text"])}{ask}</div></div>')

    # --- Cash
    parts.append("<h2>Where is our money?</h2><p class=\"q\">Cash by account and fund. Operating pays the bills; reserves are restricted for major repairs and replacements.</p>")
    parts.append("<table><tr><th>Account</th><th>Fund</th><th class=num>Balance</th><th>Reconciled</th><th class=num>Outstanding items</th></tr>")
    recon_by = {r["gl_account"]: r for r in m["reconciliations"]}
    for a in m["cash_accounts"]:
        fund = "Reserve" if a["reserve"] else "Operating"
        r = recon_by.get(a["number"])
        if not r:
            ok = '<span class="neg">no reconciliation</span>'
        elif r.get("difference") is None:
            ok = '<span class="neg">? difference not read</span>'
        elif abs(r["difference"]) < 0.005:
            ok = "✔ ties"
        else:
            ok = f'<span class="neg">✘ off {money(r["difference"])}</span>'
        outstanding = "—" if not r else f'{money(r.get("outstanding_checks"))} chk / {money(r.get("outstanding_deposits"))} dep'
        parts.append(f"<tr><td>{esc(a['number'])} · {esc(a['name'])}</td><td>{fund}</td><td class=num>{money(a['total'])}</td><td>{ok}</td><td class=num>{outstanding}</td></tr>")
    parts.append(f"<tr><th>Total cash</th><th></th><th class=num>{money(m['cash_operating'] + m['cash_reserve'])}</th><th></th><th></th></tr></table>")

    # --- Budget
    e, i, n = m["expense"], m["income"], m["net"]
    conv = "Negative" if sign == -1 else "Positive"
    parts.append(f"<h2>Are we on budget?</h2><p class=\"q\">Operating fund. {conv} variance = unfavorable (spent more, or collected less, than planned); unfavorable shown in red.</p>")
    parts.append("<table><tr><th></th><th class=num>Month actual</th><th class=num>Month budget</th><th class=num>Variance</th><th class=num>YTD actual</th><th class=num>YTD budget</th><th class=num>Variance</th><th class=num>Annual budget</th></tr>")
    for label, row in (("Income", i), ("Expense", e), ("Net", n)):
        if row:
            parts.append(f"<tr><td>{label}</td><td class=num>{money(row.get('month_actual'))}</td><td class=num>{money(row.get('month_budget'))}</td>{variance_cell(row.get('month_variance'), sign)}"
                         f"<td class=num>{money(row.get('ytd_actual'))}</td><td class=num>{money(row.get('ytd_budget'))}</td>{variance_cell(row.get('ytd_variance'), sign)}<td class=num>{money(row.get('annual_budget'))}</td></tr>")
    parts.append("</table>")
    if m["watch_lines"]:
        parts.append("<h3 style=\"font-size:1rem;margin-top:18px\">Lines running over budget year-to-date</h3>")
        parts.append("<table><tr><th>Line</th><th class=num>YTD actual</th><th class=num>YTD budget</th><th class=num>Variance</th><th class=num>% of annual used</th></tr>")
        for ln in m["watch_lines"]:
            used = ln["ytd_actual"] / ln["annual_budget"] if ln["annual_budget"] else None
            parts.append(f"<tr><td>{esc(ln['number'])} · {esc(ln['name'])}</td><td class=num>{money(ln['ytd_actual'])}</td><td class=num>{money(ln['ytd_budget'])}</td>{variance_cell(ln['ytd_variance'], sign)}<td class=num>{pct(used)}</td></tr>")
        parts.append("</table>")

    # --- Reserves
    ri, re_ = m["reserve_income"], m["reserve_expense"]
    parts.append("<h2>Are reserves being funded?</h2><p class=\"q\">Contributions should track the adopted budget; spending should match planned projects.</p>")
    if ri or re_:
        parts.append("<table><tr><th></th><th class=num>Month actual</th><th class=num>Month budget</th><th class=num>YTD actual</th><th class=num>YTD budget</th><th class=num>Variance</th><th class=num>Annual budget</th></tr>")
        for label, row in (("Contributions & interest", ri), ("Reserve spending", re_)):
            if row:
                parts.append(f"<tr><td>{label}</td><td class=num>{money(row.get('month_actual'))}</td><td class=num>{money(row.get('month_budget'))}</td><td class=num>{money(row.get('ytd_actual'))}</td><td class=num>{money(row.get('ytd_budget'))}</td>{variance_cell(row.get('ytd_variance'), sign)}<td class=num>{money(row.get('annual_budget'))}</td></tr>")
        parts.append("</table>")
    if m["reserve_components"]:
        parts.append("<table style=\"margin-top:12px\"><tr><th>Reserve component</th><th class=num>Balance</th></tr>")
        for a in m["reserve_components"]:
            cls = "neg" if a["reserve"] < 0 else ""
            parts.append(f"<tr><td>{esc(a['number'])} · {esc(a['name'])}</td><td class=\"num {cls}\">{money(a['reserve'])}</td></tr>")
        parts.append(f"<tr><th>Total reserve fund</th><th class=num>{money(m['reserve_fund_balance'])}</th></tr></table>")

    # --- Receivables / payables
    ar, ap = m["ar"], m["ap"]
    parts.append("<h2>Who owes us, and what do we owe?</h2>")
    parts.append("<table><tr><th></th><th class=num>Current</th><th class=num>30 days</th><th class=num>60 days</th><th class=num>90+ days</th><th class=num>Total</th><th>Detail</th></tr>")
    if ar.get("totals"):
        t_ = ar["totals"]
        sc = ", ".join(f"{v} {esc(k)}" for k, v in (ar.get("status_counts") or {}).items())
        parts.append(f"<tr><td>Owner receivables</td><td class=num>{money(t_['current'])}</td><td class=num>{money(t_['days_30'])}</td><td class=num>{money(t_['days_60'])}</td><td class=num>{money(t_['days_90'])}</td><td class=num>{money(t_['total'])}</td><td>{ar.get('account_count', 0)} accounts ({sc})</td></tr>")
    if ap.get("totals"):
        t_ = ap["totals"]
        parts.append(f"<tr><td>Vendor payables</td><td class=num>{money(t_['current'])}</td><td class=num>{money(t_['days_30'])}</td><td class=num>{money(t_['days_60'])}</td><td class=num>{money(t_['days_90'])}</td><td class=num>{money(t_['total'])}</td><td>{ap.get('invoice_count', 0)} open invoices</td></tr>")
    parts.append("</table>")
    if m["check_total"] is not None:
        parts.append(f"<p class=\"meta\" style=\"margin-top:8px\">{m['check_count']} disbursements totaling {money(m['check_total'])} this month (see the check register in the statement).</p>")
    for a in m["loans"]:
        parts.append(f"<p class=\"meta\">Loan · {esc(a['name'])}: {money(a['total'])} outstanding.</p>")

    # --- Trend
    if len(months) > 1:
        parts.append("<h2>Trend</h2><p class=\"q\">Month-end balances across the statements on file.</p>")
        series = [
            ("Operating cash", "cash_operating"), ("Reserve cash", "cash_reserve"),
            ("Receivables", "receivables"), ("Current liabilities", "current_liabilities"),
            ("Loans", "loan_total"),
        ]
        parts.append("<table><tr><th>Measure</th>" + "".join(f"<th class=num>{esc(mm['period_end'][:7])}</th>" for _, mm in months) + "<th></th></tr>")
        for label, key in series:
            vals = [mm[key] for _, mm in months]
            parts.append(f"<tr><td>{label}</td>" + "".join(f"<td class=num>{money(v)}</td>" for v in vals) + f"<td>{sparkline(vals)}</td></tr>")
        ytd = [mm["net"].get("ytd_actual") for _, mm in months]
        parts.append("<tr><td>YTD operating result</td>" + "".join(f"<td class=num>{money(v)}</td>" for v in ytd) + f"<td>{sparkline(ytd)}</td></tr>")
        parts.append("</table>")

    parts.append("""<div class="note"><strong>About this report.</strong> Figures are read directly from the management company's
unaudited statement; nothing is estimated. Flags are rule-based prompts for discussion, not conclusions.
Decisions about reserves, collections, borrowing, insurance, or structural repairs should be confirmed with the
association's attorney, CPA, reserve specialist, or engineer as appropriate.</div>
</main></body></html>""")
    return "\n".join(parts)


# --------------------------------------------------------------------------- cli


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "association"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("statements", nargs="*", type=Path, help="statement PDFs or parsed JSON files")
    ap.add_argument("--dir", type=Path, help="folder of statements (*.pdf, *.json)")
    ap.add_argument("--config", type=Path, help="community.toml (default: ./community.toml if present)")
    ap.add_argument("--profile", help="statement layout profile (default: community.toml profile, else fund-ledger)")
    ap.add_argument("-o", "--output", type=Path)
    args = ap.parse_args()

    paths = list(args.statements)
    if args.dir:
        paths += sorted(p for p in args.dir.iterdir() if p.suffix.lower() in (".pdf", ".json", ".txt"))
    if not paths:
        sys.exit("no statements given (pass files or --dir)")

    cfg = load_config(args.config)
    profile = args.profile or cfg.get("community", {}).get("profile") or "fund-ledger"
    loaded = []
    for p in paths:
        stmt = load_statement(p, profile)
        if not stmt.get("balance_sheet") or not stmt.get("period_end"):
            print(f"skip {p.name}: no balance sheet/period found", file=sys.stderr)
            continue
        loaded.append((stmt, metrics(stmt, cfg)))
    if not loaded:
        sys.exit("nothing parsable")
    loaded.sort(key=lambda sm: sm[1]["period_end"])
    # de-dupe by period, keeping the last file seen
    by_period = {mm["period_end"]: (s, mm) for s, mm in loaded}
    months = [by_period[k] for k in sorted(by_period)]

    stmt, m = months[-1]
    entity = cfg.get("community", {}).get("name") or stmt.get("entity") or "association"
    out = args.output or Path(cfg.get("community", {}).get("reports_dir", "reports")) / f"{slug(entity)}-{m['period_end'][:7]}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(months, cfg, date.today()))
    print(f"wrote {out}  ({len(months)} month(s), latest {m['period_end']})")


if __name__ == "__main__":
    main()
