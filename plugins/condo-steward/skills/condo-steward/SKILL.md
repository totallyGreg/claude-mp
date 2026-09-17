---
name: condo-steward
description: This skill should be used when users ask to "read our financial statement", "explain the balance sheet", "generate a financial report", "are we on budget", "how are our reserves", "who owes the association", "what does Florida statute say about", "can the board", "do we need an audit", "reserve waiver", "SIRS", "milestone inspection", "records request", "special assessment", "fine an owner", "lien", "meeting notice", "which software should we use", "switch to self-management", "PayHOA", or otherwise need help understanding, reporting on, or governing a condominium, HOA, or cooperative. Parses management statements and bank exports (masking account numbers), builds a local HTML report, and explains Florida Ch. 718/720 and FAC 61B — naming which professional (attorney, CPA, reserve specialist, engineer) must confirm anything with legal or financial consequence. Do NOT use for personal finance, commercial underwriting, or drafting legal instruments.
metadata:
  version: "0.1.0"
compatibility: Python 3.11+ via uv (PEP 723 scripts); PDF statements parsed with pdfplumber
license: MIT
---

# Condo Steward

Help owners and board members understand and run their community association well. The skill holds **no community-specific data**: everything about a particular association lives in that project's `community.toml` and its own documents. Legal references are Florida-first (Chapters 718 and 720, FAC 61B) and structured so other states can be added under `references/<state>/`.

## Core rules

1. **Answer first, then escalate.** Explain the statute or the number plainly, then say which professional must confirm anything that creates a legal right, changes the books, or touches structural safety. Read `references/professional-escalation.md` for the who/when/how.
2. **Never guess at governing documents.** The declaration and bylaws can be stricter than statute. If the user has not shared them, say so and point to the article they should check.
3. **Cite and link the law.** Every legal statement carries the section number **and** the official link (Online Sunshine / flrules.org — URL patterns at the top of each Florida reference), plus the reference file's "as of" date. Florida amends 718/720 every session; if a session has passed since that date, say so and offer to fetch the current text.
4. **Privacy — enforced in code.** Every script masks 8+ digit numbers to last-four in all output, with no override; owner names/units are dropped unless `--include-names` and never rendered. Full account numbers belong in the treasurer's password manager, not in files or chat. Shared-drive rules are in `references/data-handling.md`; `scan_sensitive.py` checks a folder before it is synced or committed. Test fixtures are synthetic.
5. **Numbers come from the statement, not from memory.** Use the scripts to extract; quote figures with the period they belong to.

## Workflow: financial statement questions

1. Locate the statement(s) — usually PDFs in the community's statements folder (see `community.toml → statements_dir`; if no config exists, offer `/condo-steward:init`).
2. Parse: `uv run ${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/scripts/parse_statement.py <pdf> -o <json>` (JSON to a scratch or reports location, never into the plugin).
3. For a full picture, render: `uv run ${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/scripts/report.py --dir <statements_dir>` → HTML in `reports_dir`. Open it for the user and summarize the "What needs attention" flags in chat.
4. For a targeted question ("why is water over budget?"), read the JSON and answer from it; consult `references/financial-accounting.md` for how to interpret the line.
5. If the parser misses a section, check `references/statement-profiles.md` — the statement may need a new profile.
6. Bank CSV/XLSX exports are transaction-level (no funds, no budget): use `parse_transactions.py` to verify a reconciliation, examine sweep activity, or total spend by payee — not as a substitute for the statement. Prefer inputs in this order: manager's GL/statement export (XLSX/CSV, if the portal offers one) → statement PDF → bank activity export.

## Workflow: statute and governance questions

1. Identify the community type (condominium → Ch. 718; HOA → Ch. 720; cooperative → Ch. 719, treat like 718). `community.toml → type` if present, else ask.
2. Read the matching reference file section (table below). Quote the section number and the operative rule (days of notice, dollar thresholds, vote required).
3. Relate it to the community's numbers when relevant (e.g., total revenue → year-end report tier; delinquency → 45-day notices).
4. Name the professional and the specific reason, per `references/professional-escalation.md`.

## Workflow: capturing questions (the learning loop)

Every community asks things the skill cannot yet answer. Record them in the community's private ledger (`questions.py add`), record answers with sources when found (`questions.py answer … --general "<neutral form>"` when the question is not community-specific), and periodically `questions.py promote <id>` — it prints a sanitized candidate for `references/common-questions.md`, a Florida reference, or a friction report; a human places it. See `commands/ask.md`.

## Scripts

| Script | Purpose | Invocation |
|---|---|---|
| `scripts/parse_statement.py` | PDF or fixed-width text → JSON (balance sheet by fund, budget vs actual, aging totals, reconciliations, check register) | `uv run …/parse_statement.py statement.pdf [-o out.json] [--include-names] [--profile fund-ledger]` |
| `scripts/report.py` | One or many statements → self-contained HTML report with KPIs, flags, cash/budget/reserve/receivable sections, trend when >1 month | `uv run …/report.py --dir <folder> [--config community.toml] [-o report.html]` |
| `scripts/parse_transactions.py` | Bank/portal CSV or XLSX export → masked, normalized transactions with totals by type and month | `uv run …/parse_transactions.py export.xlsx [-o out.json]` |
| `scripts/scan_sensitive.py` | Find files exposing unmasked account-like numbers (exit 1 if any) | `uv run …/scan_sensitive.py <folder>` |
| `scripts/questions.py` | Private question ledger (JSONL): add, answer, list, promote (prints only), mark |  `uv run …/questions.py add "…"` |
| `scripts/init_config.py` | Write the per-community `community.toml` | `uv run …/init_config.py --name "…" --units N [options]` |
| `tests/test_parse.py` | Smoke tests on the synthetic fixture | `uv run …/tests/test_parse.py` |

All scripts use PEP 723 inline metadata; `uv run` resolves dependencies. Profiles for other statement layouts go in `scripts/profiles/`.

## References (read as needed, not all at once)

| File | Read when |
|---|---|
| `references/common-questions.md` | First stop for any question: maps the ~45 questions boards ask to data, script/reference, and who must confirm |
| `references/financial-accounting.md` | Any question about a statement line, fund accounting, ratios, red flags |
| `references/professional-escalation.md` | Before giving advice with legal, tax, or structural consequence |
| `references/florida/ch718-condominiums.md` | Condominium governance, records, budgets, reserves, assessments, fines, meetings, elections |
| `references/florida/sirs-milestone-inspections.md` | Buildings 3+ stories: SIRS, milestone inspections, reserve waiver limits |
| `references/florida/fac-61b-financial-reporting.md` | Reserve calculation methods, year-end report contents, budget disclosures |
| `references/florida/ch720-hoa.md` | Homeowners' associations (parcels, not units) |
| `references/tools-and-platforms.md` | Choosing or switching management/accounting platforms, banking programs, e-voting, records sites; manager → self-management checklist |
| `references/data-handling.md` | What may live in a shared drive; secret / personal / community tiers; leak response |
| `references/statement-profiles.md` | Parser misses a section; supporting a new management package |

## Commands

The user-facing workflows are thin command files in `commands/` — `init`, `report`, `trend`, `statute`, `scan`, `ask` — invoked as `/condo-steward:<name>`. Each points at a script in this skill's `scripts/` via `${CLAUDE_PLUGIN_ROOT}`; the procedures, references, and tests all live here.

## Adding another state

Create `references/<state>/` with the same file roles (association statute summary, reserve/financial rules, structural-safety rules if any) and add a row to the table above. Keep the same "Currency" header and official-source link convention.
