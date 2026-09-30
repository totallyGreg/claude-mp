#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Write a community.toml for the current association project.

Everything specific to one community (name, size, where statements live,
review thresholds) belongs here — never in the plugin. Keep this file out of
public repositories; it is yours, not the tool's.

Usage:
    uv run init_config.py --name "Example Condominium Association, Inc." --units 24 \
        [--statements-dir Financials/Statements] [--reports-dir reports] \
        [--fiscal-year-start 1] [--state FL] [--type condominium|hoa|cooperative] \
        [--cash-months-min 2] [--cash-months-max 6] [--delinquency-warn 0.05] \
        [--variance-warn 0.10] [-o community.toml] [--force]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def toml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="legal name of the association")
    ap.add_argument("--units", type=int, required=True)
    ap.add_argument("--type", default="condominium", choices=["condominium", "hoa", "cooperative"])
    ap.add_argument("--state", default="FL")
    ap.add_argument("--fiscal-year-start", type=int, default=1, help="month number (1 = January)")
    ap.add_argument("--statements-dir", default="Financials/Statements")
    ap.add_argument("--reports-dir", default="reports")
    ap.add_argument("--cash-months-min", type=float, default=2.0)
    ap.add_argument("--cash-months-max", type=float, default=6.0)
    ap.add_argument("--delinquency-warn", type=float, default=0.05)
    ap.add_argument("--variance-warn", type=float, default=0.10)
    ap.add_argument("-o", "--output", type=Path, default=Path("community.toml"))
    ap.add_argument("--force", action="store_true", help="overwrite an existing file")
    a = ap.parse_args()

    if a.output.exists() and not a.force:
        sys.exit(f"{a.output} exists; use --force to overwrite")

    body = f"""# Community configuration for condo-steward. Private to this association — do not publish.

[community]
name = {toml_str(a.name)}
units = {a.units}
type = {toml_str(a.type)}
state = {toml_str(a.state)}
fiscal_year_start_month = {a.fiscal_year_start}
statements_dir = {toml_str(a.statements_dir)}
reports_dir = {toml_str(a.reports_dir)}

# Review thresholds used by the report's "what needs attention" rules.
[thresholds]
operating_cash_months_min = {a.cash_months_min}   # flag if operating cash (net of payables) covers fewer months of budget
operating_cash_months_max = {a.cash_months_max}   # flag if it covers more (possible idle surplus)
delinquency_ratio_warn = {a.delinquency_warn}     # receivables / annual assessments
budget_variance_warn = {a.variance_warn}          # |YTD variance| / YTD budget, per line and in total
budget_variance_min_dollars = 500.0               # ignore smaller lines in the over-budget list
variance_sign = -1                                # -1 if the package shows unfavorable variances as negative; 1 if flipped

# Optional: notes about specific GL accounts, shown nowhere yet but useful to future readers.
# [accounts."NNNN"]
# note = "e.g. sweep account paired with operating checking; the two act as one pool."

# Optional: statement layout profile if not the default (see references/statement-profiles.md).
# profile = "fund-ledger"
"""
    a.output.write_text(body)
    print(f"wrote {a.output}")
    gi = Path(".gitignore")
    if gi.exists() and "community.toml" not in gi.read_text():
        print("hint: add community.toml to .gitignore if this project is version-controlled and shared")


if __name__ == "__main__":
    main()
