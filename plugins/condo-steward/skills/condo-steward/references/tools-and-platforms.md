# Tools an association may employ

Software categories a board runs into, what each is for, what to demand of it, and what changes when a community moves between them. Product names are examples of widely used condo/HOA platforms, not endorsements; features change — check current documentation. No banks' individual products, contractors, or people belong in this file.

## 1. Management / accounting platforms

The system of record for the general ledger, owner ledgers, assessments, vendor payments, and (increasingly) the statutory records website.

| Model | Typical products | Notes |
|---|---|---|
| **Self-managed platform** (board runs it) | PayHOA, HOA Life / HOALife, Condo Control, CondoSites+accounting add-ons | Per-unit or flat monthly pricing; owner portal with ACH/card collections; fund accounting of varying depth. The board becomes the bookkeeper unless it hires one. |
| **Manager-operated platform** (a management company runs it, board gets a portal) | Vantaca, CINC Systems, AppFolio Association, Buildium, TOPS [ONE], Caliber | Richer accounting and bank integrations; the manager owns the data unless the contract says otherwise. Monthly statement packages like the one this plugin parses usually come from these. |
| **General accounting + portal** | QuickBooks / Xero with a separate portal or records site | Works for small associations; fund accounting must be enforced by discipline (classes/tracking categories), not by the software. |

### What to require, whichever model

- **Fund accounting**: operating and reserve funds as separate books or enforced classes, with transfers between them recorded as such. If reserves are a line item in one checking account, the software is not doing fund accounting.
- **Budget vs actual** by month and year-to-date, per fund, exportable.
- **Bank feeds and reconciliation** with a printable reconciliation per account (statement balance, GL balance, outstanding items, difference).
- **Owner ledgers** with aging (current/30/60/90), late-fee and interest automation matching the declaration, and statutory notice templates that a person still reviews.
- **Exports** in CSV/XLSX for every report — this is what lets the plugin's parser profiles work without PDF scraping, and what makes leaving the platform possible.
- **Records website** capability for the Florida 25-unit (condo) / 100-parcel (HOA) posting requirement, with owner logins.
- **Electronic voting** support (Florida §718.128: allowed after a board resolution and per-owner consent) and meeting-notice delivery by email with owner consent on file.
- **Vendor 1099 tracking**, insurance-certificate tracking, and a place for the fidelity bond and D&O policy documents.
- **Role-based access** so a treasurer can see everything and an owner sees only their ledger and the official records.

## 2. Association banking and treasury

- **Association-specialty banking**: several banks run programs built for HOAs/condos — lockbox coupon processing, ACH/portal collections, manager sub-accounts, and integrations with the platforms above. Ask about fees for returned payments and card processing, which owners often bear.
- **Sweep / insured cash accounts** (IntraFi ICS, CDARS, or a bank's own sweep): keep operating checking at a target balance and place the rest across insured banks. Expect many daily "sweep transfer" entries in exports; they are not spending.
- **Reserve investing**: Florida 2025 changes permit certain reserve investments with conditions; before moving reserves into CDs or treasuries, the attorney confirms the procedure and the CPA confirms presentation. Keep reserves in accounts titled to the association, not to the manager.
- **Loans / lines of credit** for capital projects are common; the loan account, interest expense, and covenant reporting all need a home in the books.

## 3. Governance and communication tools

- **Records website / portal** (often part of the platform; standalone options exist) — meets the statutory posting duty and cuts records requests.
- **E-voting and meeting tools** — platforms with §718.128-compliant voting, plus ordinary video conferencing for board meetings (Florida permits remote participation; notice and minutes rules still apply).
- **Document storage** — a shared drive is fine for community-tier documents (see `data-handling.md`); official records custody should still be defined by resolution.
- **Payment collection** — portal ACH is cheapest for owners; card fees should be disclosed; lockbox for paper checks.

## 4. Reserve study, inspection, and compliance tools

- Reserve-study firms deliver PDFs and sometimes a spreadsheet of components (useful life, cost, funding plan). Ask for the spreadsheet — it feeds the reserve section of the report and future SIRS updates.
- Milestone inspection and SIRS reports are official records and must be posted; keep the sealed PDF and the owner summary together.

## 5. Moving from a manager to self-management (or between platforms)

Before the manager's last day, obtain — in CSV/XLSX where possible — and check off:

1. Full **general ledger** detail for the current and prior fiscal year, plus trial balance at the cutover date.
2. **Owner ledgers** with balances, aging, payment plans, and any accounts at attorney.
3. **Prepaid assessments** list (a liability the new system must carry).
4. **Vendor list** with W-9s, 1099 year-to-date totals, insurance certificates, and open contracts.
5. **Bank reconciliations** for every account through the cutover month, and the last bank statements.
6. **Reserve schedule**: components, balances, the current reserve study/SIRS, and the funding method (straight-line or pooled).
7. **Official records** inventory: declaration, bylaws, rules, amendments, minutes, election materials, insurance policies, inspection reports, contracts — with the 7-year retention items identified.
8. **Bank authority**: signer changes, online-banking admin transfer, lockbox/ACH re-pointing, and cancellation of the manager's access on a written date.
9. **Insurance**: confirm fidelity/crime coverage names the new custodians of funds (the board) and that D&O covers the added responsibilities.
10. **Statutory calendar**: budget meeting, annual meeting/election, year-end financial report tier and deadline, insurance appraisal (36 months), inspection cycles. A manager was tracking these; someone must now.

What self-management removes: a licensed CAM's handling of notices and collections, a second set of eyes on disbursements, and the manager's fidelity bond. Replace them with **two-signature or dual-approval payments**, a bookkeeper or CPA for monthly close, and an attorney on retainer for collections. Ask the attorney whether any governing-document provision requires a licensed manager.

## 6. Making exports useful to this plugin

When the platform can export the balance sheet, budget comparison, aging, and reconciliations as CSV/XLSX, add a parser profile (see `statement-profiles.md`) that reads those files instead of the PDF. Column-based exports are more reliable than PDF text; prefer them when both exist. Bank activity exports go through `parse_transactions.py`, which masks account numbers on the way in.
