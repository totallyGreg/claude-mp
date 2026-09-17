# Community association accounting — how to read the numbers

Community associations are small non-profits that use **fund accounting**: money is tracked in separate funds according to what it is allowed to be used for. Nearly every question a board or owner asks can be answered by knowing which fund a number belongs to and whether it is a balance (a point in time) or a flow (over a period).

## The two funds (sometimes three)

| Fund | What it is for | Typical accounts |
|---|---|---|
| **Operating** | Day-to-day: utilities, insurance, management, maintenance, contracts | Operating checking, sweep/money-market linked to it, receivables, prepaid expenses, payables, accrued expenses, prepaid assessments |
| **Reserve** | Restricted savings for major repair and replacement of components (roof, painting, paving, elevators, and in Florida the SIRS items) | Reserve money market / CDs, one equity line per component or pool |
| **Special assessment / project** (sometimes) | Money collected for one specific project | Project account, project payable |

Operating money can be moved to reserves any time; moving reserve money to operating is restricted (in Florida: owner vote for non-SIRS items, never for SIRS items). A "due to/due from" between funds means one fund is holding the other's cash — a common finding worth asking about.

## The monthly statement package

Management companies send an **unaudited** package each month. Typical contents, in the order the parser expects them:

1. **Balance sheet** (by fund) — what the association owns and owes *on the last day of the month*.
2. **Budget comparison / income statement** — actual vs. budget for the month and year-to-date, per fund.
3. **Aged receivables** — what owners owe, by how many days late.
4. **Prepaid report** — owners who have paid ahead (a liability: the association owes them the service).
5. **Aged payables** — unpaid vendor invoices.
6. **Check register / disbursements** — every payment made.
7. **Bank reconciliations** — proof that each bank balance ties to the ledger.
8. **General ledger detail** — every transaction by account.

The monthly package is not the statutory year-end report (see `florida/ch718-condominiums.md` §718.111(13)); that one is compiled, reviewed, or audited by a CPA once a year.

## Balance sheet — what to look for

- **Cash – operating** vs **cash – reserve**: the first question is always "how much do we have and can we use it?" Reserve cash is not available for bills.
- **Sweep / ICS / money-market accounts** paired with checking: some banks hold checking at a target balance and sweep the rest into an interest-bearing account, often placed across several banks so the total stays FDIC-insured (IntraFi ICS/CDARS). Treat the pair as one pool. The statement will show many "sweep transfer" entries; that is normal, not churn.
- **Assessments receivable**: what owners owe. Compare with the aged receivables report; the totals should match.
- **Prepaid insurance** and **loan costs / accumulated amortization**: amounts paid in advance being expensed over time. Prepaid insurance should fall each month by roughly the annual premium ÷ 12.
- **Prepaid assessments** (liability): owners who paid early. Not income yet.
- **Accounts payable / accrued expenses**: bills received but unpaid, and expenses incurred but not yet billed.
- **Loans**: principal outstanding. Interest shows in the budget comparison, not here.
- **Reserve equity lines**: one per component (roof, painting…) or a pool. The sum should equal reserve cash. A **negative** component means money designated for it was spent on something else or the schedule is presented on an accrual basis that nets a funding target against spending — either way, ask the CPA what it represents and how it will be restored.
- **Retained earnings / net income**: cumulative and current-year operating results. Persistent negative operating retained earnings means the association has been living on reserves or borrowing.

Sanity checks: assets = liabilities + equity in each fund; reserve cash ≈ total reserves; receivables on the balance sheet = aged receivables total; payables = aged payables total; each bank account has a reconciliation with zero difference.

## Budget comparison — what to look for

- **Assessment income** should equal budget every month (it is billed, not collected; collection problems show in receivables, not here).
- **Variance** convention: negative = unfavorable (spent more than planned, or earned less). Confirm the package's convention — some flip the sign.
- **Year-to-date** matters more than the month; seasonality (insurance renewals, chiller season, annual inspections) distorts single months.
- **% of annual budget used** vs **% of year elapsed** flags lines that will run out.
- **Insurance** is often paid up front and amortized; if the package expenses it when paid, mid-year comparisons are misleading.
- **Interest on loans** is an operating expense; **principal** is not — it reduces the loan liability.
- **Reserve fund budget**: contributions (income to the reserve fund) should track budget exactly; spending should correspond to approved projects.

## Key ratios (the report computes these)

| Ratio | Formula | Rule of thumb |
|---|---|---|
| Months of operating cash | (operating cash − current liabilities) ÷ (annual operating expense budget ÷ 12) | 2–6 months is common; below 1 is precarious; well above 6 suggests idle money or an unfunded plan |
| Delinquency ratio | assessments receivable ÷ annual assessments | under 5% healthy; over 10% needs a collection plan; lenders (FHA/Fannie) look at % of units 60+ days late |
| Reserve funding vs. plan | YTD reserve contributions ÷ YTD budgeted contributions | should be 100%; anything less is a waiver or a shortfall |
| Percent funded (reserves) | reserve fund balance ÷ fully-funded balance from the reserve study | 70%+ strong, 30% or less weak — requires the reserve study to compute |
| Expense variance | YTD actual ÷ YTD budget − 1 | ±10% on a line is worth a question; on the total it is worth a budget amendment |

## Cash vs. accrual

Most management packages are on a **modified accrual** basis: assessments are booked when billed, expenses when invoiced. Cash-basis statements show only money moved and will understate what is owed. Ask which basis is used before comparing months.

## Common red flags

- Bank reconciliation difference ≠ 0, or reconciliations missing for any account.
- Large or growing "outstanding deposits" on a reconciliation (money recorded but not in the bank).
- Reserve cash lower than reserve fund balance (reserves partly living in operating cash).
- Assessment income that does not equal budget (billing error or an unrecorded assessment change).
- A vendor paid from reserves without a board-approved project.
- Payables aging into 60/90 days while cash is available (cash-flow or approval problem).
- Management fee or legal line materially over budget with no board discussion.
- Related-party payees (board members, manager affiliates).

## When to bring in a professional

| Situation | Who |
|---|---|
| Choosing pooled vs. straight-line reserves; restating negative components; year-end report; tax filing (Form 1120-H vs 1120) | **CPA** experienced with community associations |
| Collections, liens, foreclosure, fines, contract disputes, records requests, anything involving a vote to waive or borrow | **Association attorney** |
| Reserve study, SIRS, component useful lives | **Reserve specialist** (RS/PRA) |
| Milestone inspection, structural repairs, roof, elevators | **Licensed engineer / architect** |
| Coverage adequacy, appraisal, fidelity bond limits | **Insurance agent** and independent appraiser |
| Loan terms, covenants, sweep/ICS structure | **Bank relationship manager**, with the attorney reviewing documents |

The plugin can prepare questions and organize numbers for these conversations; it cannot replace them.
