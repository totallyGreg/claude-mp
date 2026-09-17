#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pdfplumber>=0.11", "openpyxl>=3.1"]
# ///
"""
Scan a folder (e.g. a shared drive) for files that expose full account numbers.

Reports, per file, how many unmasked account-like numbers (8+ consecutive digits,
not part of a dollar amount or date) appear, with a masked sample so the reader can
recognise the source without re-exposing it. Exit code 1 if anything is found, so
it can gate a sync or a commit.

Usage:
    uv run scan_sensitive.py <folder-or-file> [--min-digits 8] [--ignore-ext pdf] [--json]

Scans .csv .txt .md .json .toml .html .xlsx .pdf. Statement PDFs almost always
trip the scanner on owner account numbers and invoice numbers in the aging pages
(Personal tier, see references/data-handling.md); use --ignore-ext pdf to focus on
exports and generated files. Owner names are not detected — they are not
machine-recognisable — so this is a floor, not a guarantee.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_statement import ACCOUNT_NUMBER_RE, looks_like_account  # noqa: E402  (same rules as the masker)

TEXT_EXT = {".csv", ".txt", ".md", ".json", ".toml", ".html", ".htm", ".yaml", ".yml"}
SCAN_EXT = TEXT_EXT | {".xlsx", ".pdf"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv"}


def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in TEXT_EXT:
        return path.read_text(errors="replace")
    if ext == ".xlsx":
        import warnings

        import openpyxl

        warnings.filterwarnings("ignore", module="openpyxl")
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        return "\n".join(
            " ".join("" if v is None else str(v) for v in row)
            for ws in wb.worksheets for row in ws.iter_rows(values_only=True)
        )
    if ext == ".pdf":
        import logging

        import pdfplumber

        logging.getLogger("pdfminer").setLevel(logging.ERROR)
        with pdfplumber.open(path) as pdf:
            return "\n".join((p.extract_text() or "") for p in pdf.pages)
    return ""


def find_numbers(text: str, min_digits: int) -> list[str]:
    return [m.group() for m in ACCOUNT_NUMBER_RE.finditer(text) if looks_like_account(m.group(), min_digits)]


def mask(n: str) -> str:
    digits = re.sub(r"\D", "", n)
    return "*" * (len(digits) - 4) + digits[-4:]


def scan(root: Path, min_digits: int, ignore_ext: set[str]) -> list[dict]:
    exts = SCAN_EXT - ignore_ext
    files = [root] if root.is_file() else [
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in exts and not (set(p.parts) & SKIP_DIRS)
    ]
    findings = []
    for f in sorted(files):
        try:
            hits = find_numbers(extract_text(f), min_digits)
        except Exception as e:  # unreadable file is a finding in itself
            findings.append({"file": str(f), "error": str(e)})
            continue
        if hits:
            distinct = sorted(set(hits), key=hits.index)
            findings.append({"file": str(f), "count": len(hits), "distinct": len(distinct),
                             "samples": [mask(n) for n in distinct[:5]]})
    return findings


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", type=Path)
    ap.add_argument("--min-digits", type=int, default=8)
    ap.add_argument("--ignore-ext", action="append", default=[], help="extension to skip, e.g. pdf (repeatable)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if not args.path.exists():
        sys.exit(f"not found: {args.path}")

    findings = scan(args.path, args.min_digits, {"." + e.lstrip(".").lower() for e in args.ignore_ext})
    if args.json:
        print(json.dumps(findings, indent=2))
    elif not findings:
        print("clean: no unmasked account-like numbers found")
    else:
        for f in findings:
            if "error" in f:
                print(f"?  {f['file']}: {f['error']}")
            else:
                print(f"!  {f['file']}: {f['count']} occurrences, {f['distinct']} distinct — e.g. {', '.join(f['samples'])}")
        print(f"\n{len(findings)} file(s) need attention. Mask, move to private storage, or delete.")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
