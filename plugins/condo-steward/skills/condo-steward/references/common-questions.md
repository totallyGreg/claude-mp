# Common questions — and where the answer comes from

Once a community's statements, config, and governing documents are on hand, these should be answerable in one turn. Each row names the data needed, the script or reference that produces the answer, and whether a professional must confirm before the board acts. Use it as a checklist for what "ready" means, and as the first place to look when a new question arrives.

Legend — **Data**: S = monthly statement (PDF/JSON via `parse_statement.py`), B = bank export (`parse_transactions.py`), C = `community.toml`, G = governing documents (declaration/bylaws — user must supply), R = reserve study / SIRS, L = Florida references. **Confirm**: who must sign off before action; "—" means informational.

## Money on hand

| Question | Data | How | Confirm |
|---|---|---|---|
| How much cash do we have, and how much of it can pay bills? | S | Report KPIs: operating vs reserve cash; `financial-accounting.md` on fund restriction | — |
| How many months of expenses can we cover? | S, C | `months_operating_cash` = (operating cash − current liabilities) ÷ monthly expense budget; thresholds in C | — |
| Do our bank accounts reconcile? Any outstanding items? | S | Report "Where is our money" table; reconciliation `difference`, outstanding checks/deposits | CPA if difference ≠ 0 persists |
| Why are there so many transfers in the bank export? | B | `parse_transactions.py` summary `transfer_count`; sweep explanation in `financial-accounting.md` | — |
| Is our cash fully FDIC-insured? | S, B | Balances per bank vs $250k; ICS/sweep placement pages in the statement | bank |
| Does our fidelity/crime coverage exceed the most cash we hold? | S + policy | Compare total cash to bond limit; §718.111(11)(h) | insurance agent |

## Budget and spending

| Question | Data | How | Confirm |
|---|---|---|---|
| Are we on budget this month / year-to-date? | S | Report "Are we on budget"; totals and variance sign convention | — |
| Which lines are running over, and will they run out? | S | `watch_lines`; % of annual used vs % of year elapsed | — |
| What did we pay, to whom, this month? | S | Check register in statement JSON (`check_register.checks`) | — |
| How much does a vendor cost us per year? | S×12 or B | Sum check register by payee across months, or `parse_transactions.py` by description | — |
| Does a contract need competitive bids? | S, C | Contract value vs 5% (condo) / 10% (HOA) of total annual budget incl. reserves; `ch718` §718.3026 | attorney if borderline |
| What does the year-end financial report have to be (cash/compiled/reviewed/audited)? | S | Total annual revenue vs $150k/$300k/$500k tiers; `ch718` §718.111(13) | CPA |
| Can we amend the budget mid-year? | G, L | Bylaws procedure; 14-day notice rules | attorney |

## Reserves

| Question | Data | How | Confirm |
|---|---|---|---|
| Are we contributing to reserves as budgeted? | S | Reserve budget comparison, YTD actual vs budget | — |
| What is each reserve component's balance? Why is one negative? | S | Component table; pooled vs straight-line explanation in `fac-61b` and `financial-accounting.md` | CPA |
| Are we funded to the reserve study / SIRS? | S, R | Percent funded = fund balance ÷ fully-funded balance from R; contribution vs recommended | reserve specialist |
| Can we waive or reduce reserves this year? | L, building height, R | `sirs-milestone-inspections.md`: SIRS items cannot be waived (3+ stories, budgets after 12/31/2024); others by majority of total voting interests | attorney |
| Can we spend reserve money on X? | S, R, L | Purpose match; owner vote rules; SIRS prohibition | attorney |
| When are our milestone inspection and SIRS due? | building age, C | `sirs-milestone-inspections.md` schedule (30 years / 10-year cycle) | engineer, local building dept |

## Owners and collections

| Question | Data | How | Confirm |
|---|---|---|---|
| How much is owed to us and how old is it? | S | Aging totals; delinquency ratio vs annual assessments | — |
| How many accounts are delinquent / at attorney? | S | `ar_aging.status_counts` (no names) | — |
| When can we lien / foreclose, and what notice is required? | L | `ch718` §718.116: 45-day notice of intent to lien, then 45-day notice of intent to foreclose | attorney (always) |
| What interest and late fees can we charge? | G, L | Declaration rate (max 18%); late fee ≤ greater of $25 or 5% | attorney |
| Can we suspend a delinquent owner's voting or amenity rights? | S, L | 90+ days and > $1,000; §718.303(4)–(5) | attorney |
| Can we fine for this violation, and how? | G, L | $100/day, $1,000 max; 14-day notice; independent committee; §718.303 | attorney |
| How much have owners prepaid? | S | `prepaid.total` / GL prepaid assessments liability | — |

## Governance and records

| Question | Data | How | Confirm |
|---|---|---|---|
| How much notice does this meeting need? | L, G | 48 hours posted (board); 14 days mailed + posted (budget, special assessment, rules on unit use); annual/election 60/40/14 | attorney if contested |
| What must be on the records website, and do we need one? | C, L | 25+ units (condo) / 100+ parcels (HOA); list in `ch718` §718.111(12) | — |
| How fast must we answer a records request? | L | 10 working days; exclusions list | attorney if denying |
| Which board members need the education certificate? | L | Within 90 days of election; annual CE | — |
| Can a director serve another term? | L, G | 8-consecutive-year limit and exceptions | attorney |
| Can we vote electronically / hold meetings by video? | L, G | §718.128 resolution + owner consent; remote participation allowed | attorney to draft resolution |
| Does our declaration allow this (rental restriction, pets, assessments basis)? | G | **Only if the user supplies the document** — otherwise say so | attorney |

## Platforms and operations

| Question | Data | How | Confirm |
|---|---|---|---|
| What do we need from the manager before they leave? | — | `tools-and-platforms.md` handover checklist | attorney reviews termination terms |
| What must any accounting platform do for us? | — | `tools-and-platforms.md` requirements list | — |
| Which of our files should not be in the shared drive? | folder | `scan_sensitive.py`; `data-handling.md` tiers | — |
| What deadlines are coming up this year? | C, L | Budget meeting, annual meeting, year-end report (90/120 days), insurance appraisal (36 months), inspection cycles | — |

## Questions this plugin cannot answer (say so plainly)

- Anything requiring the **governing documents** the user has not shared.
- Whether a specific repair is **structurally necessary** — engineer.
- Whether the **manager's accounting is correct** beyond internal consistency checks — CPA.
- **Tax** consequences (1120-H vs 1120, interest income, reserve investments) — CPA.
- Anything where the answer depends on the **current statute text** and the reference file's "as of" date has passed a legislative session — fetch and verify.
