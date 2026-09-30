#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pdfplumber>=0.11"]
# ///
"""
Parse a community-association monthly financial statement into structured JSON.

Extracts the sections most management-company packages share: balance sheet
(by fund column), budget comparison (operating and reserve), receivable and
payable aging totals, bank reconciliations, and the check register.

Usage:
    uv run parse_statement.py <statement.pdf|statement.txt> [--profile fund-ledger]
                              [--include-names] [-o out.json]

Input may be a PDF or a pre-extracted fixed-width text file (e.g. `pdftotext -layout`
output or the synthetic test fixture). Owner names in the receivable aging are
omitted unless --include-names is given; aggregate totals are always produced.

Profiles live in profiles/<name>.py and expose `parse(lines) -> dict`. Add a new
profile when a management package lays its reports out differently.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

MONEY_RE = re.compile(r"-?\(?\$-?[\d,]+\.\d{2}\)?")
# Runs of digits, optionally in groups of 3+ separated by a single space or dash
# (card/account style "1234 5678 9012"). Dates (2026-03-31), dollar amounts, and
# 4-digit GL codes never match; total digit count is checked in the callback.
ACCOUNT_NUMBER_RE = re.compile(r"(?<![\d.$,])\d{3,}(?:[ -]\d{3,})*(?!\d)(?!\.\d)")
MASK_MIN_DIGITS = 8


def mask_account_numbers(text: str, min_digits: int = MASK_MIN_DIGITS) -> str:
    """Replace any run of `min_digits`+ digits (bank/ACH/owner account ids) with a last-4 mask.

    Applied to every free-text field the scripts emit. Dollar amounts, dates, and
    4-digit GL codes are untouched; 8+ digit check or invoice numbers are masked too,
    which is accepted collateral. Full account numbers belong in the treasurer's
    password manager, never in generated files.
    """
    def repl(m: re.Match) -> str:
        return "****" + re.sub(r"\D", "", m.group())[-4:] if looks_like_account(m.group(), min_digits) else m.group()

    return ACCOUNT_NUMBER_RE.sub(repl, text)


def looks_like_account(candidate: str, min_digits: int = MASK_MIN_DIGITS) -> bool:
    """A single digit run of min_digits+, or 3+ separated groups (card/IBAN style).
    Two adjacent columns like 'GL 1003  check 300328' are not treated as one number."""
    groups = re.split(r"[ -]", candidate)
    digits = sum(len(g) for g in groups)
    return digits >= min_digits and (len(groups) == 1 or len(groups) >= 3)


@dataclass
class Token:
    text: str
    x0: float
    x1: float


@dataclass
class Line:
    tokens: list[Token]

    @property
    def text(self) -> str:
        return " ".join(t.text for t in self.tokens)

    def money(self) -> list[tuple[float, Token]]:
        """All money values on the line as (amount, token), left to right."""
        out = []
        for t in self.tokens:
            for m in MONEY_RE.finditer(t.text):
                out.append((parse_money(m.group()), t))
        return out


def parse_money(s: str) -> float:
    neg = s.startswith("-") or s.startswith("(") or "$-" in s
    v = float(re.sub(r"[^\d.]", "", s))
    return -v if neg else v


def lines_from_pdf(path: Path) -> list[Line]:
    import logging

    import pdfplumber

    logging.getLogger("pdfminer").setLevel(logging.ERROR)  # silence stream-decompression chatter
    lines: list[Line] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(x_tolerance=1.5, y_tolerance=2, keep_blank_chars=False)
            rows: dict[int, list[Token]] = {}
            for w in words:
                key = round(w["top"] / 3)  # bucket by vertical position
                rows.setdefault(key, []).append(Token(w["text"], w["x0"], w["x1"]))
            for key in sorted(rows):
                toks = sorted(rows[key], key=lambda t: t.x0)
                lines.append(Line(_merge_split_money(toks)))
    return lines


def _merge_split_money(tokens: list[Token]) -> list[Token]:
    """pdfplumber occasionally splits '$1,234.56' from a leading '(' or '-'; rejoin."""
    out: list[Token] = []
    for t in tokens:
        if out and out[-1].text in ("(", "-") and t.text.startswith("$"):
            prev = out.pop()
            out.append(Token(prev.text + t.text, prev.x0, t.x1))
        else:
            out.append(t)
    return out


def lines_from_text(path: Path) -> list[Line]:
    """Fixed-width text: token x positions are character columns."""
    lines: list[Line] = []
    for raw in path.read_text().splitlines():
        toks = [Token(m.group(), m.start(), m.end()) for m in re.finditer(r"\S+", raw)]
        if toks:
            lines.append(Line(toks))
    return lines


def load_lines(path: Path) -> list[Line]:
    if path.suffix.lower() == ".pdf":
        return lines_from_pdf(path)
    if path.suffix.lower() == ".txt":
        return lines_from_text(path)
    sys.exit(f"unsupported input: {path.name} (use .pdf or fixed-width .txt)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("statement", type=Path)
    ap.add_argument("--profile", default="fund-ledger", help="statement layout profile (default: fund-ledger)")
    ap.add_argument("--include-names", action="store_true", help="keep owner names/units in receivable detail")
    ap.add_argument("-o", "--output", type=Path, help="write JSON here instead of stdout")
    args = ap.parse_args()

    if not args.statement.exists():
        sys.exit(f"not found: {args.statement}")

    profile = importlib.import_module(f"profiles.{args.profile.replace('-', '_')}")
    lines = load_lines(args.statement)
    result = profile.parse(lines, include_names=args.include_names)
    result["source"] = {"file": args.statement.name, "profile": args.profile}

    text = mask_account_numbers(json.dumps(result, indent=2))
    if args.output:
        args.output.write_text(text)
        print(f"wrote {args.output}")
    else:
        print(text)


if __name__ == "__main__":
    main()
