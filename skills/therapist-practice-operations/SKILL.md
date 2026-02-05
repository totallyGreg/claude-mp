---
name: therapist-practice-operations
description: This skill should be used when the user asks to "help me with taxes", "organize my expenses", "plan estimated tax payments", "renew my license", "track my continuing education hours", "what are my compliance deadlines", "set up tax tracking", "compare licensing requirements", or mentions managing sole proprietor business operations, taxes, and licensing for mental health therapists.
version: 0.1.0
---

# Therapist Practice Operations Skill

This skill guides mental health therapists operating as sole proprietors through tax preparation, license renewal, compliance tracking, and business record organization. It addresses the unique financial and regulatory landscape for independent practitioners.

## Purpose

Solo therapists face complex, state-specific requirements for business taxes, continuing education, and professional licensing—often without accounting or legal guidance. This skill provides:

- **Interactive tax planning**: Helps determine quarterly estimated payments, deduction tracking strategies, and QBI eligibility
- **License renewal workflows**: State-specific timelines, CE hour requirements, documentation checklists
- **Compliance calendar**: Deadline tracking for federal, state, and professional board requirements
- **Record organization**: Expense categorization and documentation frameworks to support tax filing

## When to Use This Skill

This skill triggers when users ask about:
- **Tax strategy**: "What should my quarterly estimated tax payments be?" or "How do I track deductions?"
- **License renewal**: "My license expires soon—what do I need to do?" or "What are Florida's CE requirements?"
- **Compliance**: "What are my filing deadlines?" or "What do I need to keep documented?"
- **Multi-state operations**: "How do licensing requirements differ between states?"

## How to Use This Skill

### Workflow 1: Annual Tax Planning (January/February)

When a therapist wants to plan their year ahead:

1. **Gather baseline**: Ask for estimated annual income and expenses
2. **Calculate estimated taxes**: Use formulas in `references/tax-formulas.md`
3. **Determine QBI eligibility**: Check if they qualify for qualified business income deduction
4. **Create payment schedule**: Generate quarterly payment calendar with due dates
5. **Set deduction categories**: Use `references/expense-categories.md` to establish what to track
6. **Output**: Provide personalized quarterly payment schedule and deduction tracker template

### Workflow 2: License Renewal (3-6 months before expiration)

When renewal deadline approaches:

1. **Identify state and license type**: Confirm which state(s) and credential type (LMHC, LCSW, etc.)
2. **Pull state requirements**: Reference `references/state-requirements.md` for deadline, CE hours, forms
3. **Create renewal checklist**: Build timeline with application deadline, CE completion date, required documents
4. **Track CE credits**: Help organize which CE courses count toward requirements
5. **Output**: Personalized renewal checklist with deadlines and documentation requirements

### Workflow 3: Quarterly Expense Review & Tax Adjustment

When therapist wants to check progress against quarterly estimates:

1. **Gather expense summary**: Income and expense totals for the quarter
2. **Compare to estimates**: Calculate actual vs. estimated liability
3. **Adjust future payments**: Recalculate remaining quarterly payments if needed
4. **Review deductions**: Identify any missed deduction categories
5. **Output**: Updated payment schedule and deduction summary

### Workflow 4: Multi-State Comparison

When therapist considering opening practice in another state:

1. **Identify both states**: Get current and prospective state(s)
2. **Create comparison table**: Pull requirements from `references/state-requirements.md`
3. **Highlight differences**: License types, CE hours, renewal timeline, fees, tax implications
4. **Output**: Side-by-side comparison document with action items

## Key Tax Concepts for Therapists

### Self-Employment Tax

Sole proprietors pay both employer and employee portions of Social Security and Medicare taxes (~15.3% of net profit). This differs from W2 employees.

**Formula:** Net profit × 0.9235 × 0.153 = Self-employment tax liability

### Estimated Quarterly Tax Payments

Instead of withholding from each paycheck (like W2 employees), sole proprietors make quarterly payments:
- **Due dates**: April 15 (Q1), June 15 (Q2), Sept 15 (Q3), Jan 15 (Q4)
- **Amount**: Roughly 25% of estimated annual income tax + self-employment tax

Underestimating can result in penalties; see `references/tax-formulas.md` for safe harbor rules.

### Qualified Business Income (QBI) Deduction

Eligible therapists may deduct up to 20% of business income (Section 199A deduction). However, income limitations apply, and therapists are likely in a "specified service trade or business" (SSTB) which has restrictions.

**⚠️ Important:** The QBI deduction is scheduled to expire on December 31, 2025 unless Congress extends it. Verify current tax law status when planning your 2026+ taxes and consult with your CPA about any changes.

**Check eligibility**: See `references/qbi-eligibility.md`

### Deductible Business Expenses

Common deductions for therapist practices:
- Office supplies and equipment
- Continuing education courses
- Professional association dues
- Malpractice insurance
- Office rent/home office depreciation
- Technology and software

See `references/expense-categories.md` for comprehensive list with documentation requirements.

## Multi-State Considerations

Therapists practicing in multiple states face:
- **Multiple licenses**: Each state requires separate license with separate CE and renewal fees
- **Income apportionment**: May owe state income taxes in multiple states
- **Reciprocity**: Some states offer license reciprocity; others require separate exams
- **Requirements variation**: CE hours, renewal timeline, scope of practice differ significantly

See `references/state-requirements.md` for Washington and Florida comparison, and how to research other states.

## Record Organization Framework

Maintain these categories year-round:

1. **Income records**: Client payments, insurance reimbursements, other therapy-related revenue
2. **Expense documentation**: Receipts, invoices, statements for all deductible items
3. **Tax documents**: Quarterly payment confirmations, 1099s from payers, estimated tax worksheets
4. **License/CE records**: Certificate of attendance, course transcripts, CE hour logs
5. **Professional documents**: Malpractice insurance policy, professional association memberships, contracts

See `references/record-organization.md` for file structure and retention requirements.

## Common Mistakes to Avoid

### Mistake 1: Underestimating Quarterly Taxes

Sole proprietors forget self-employment tax in their quarterly estimates, then face large tax bills in April.

**Solution:** Use safe harbor rules in `references/tax-formulas.md` to calculate conservatively.

### Mistake 2: Missing Renewal Deadlines

License renewal dates sneak up, and some states have long application processing times. Missing deadlines can result in practice interruption.

**Solution:** Set three calendar reminders (6 months, 3 months, 1 month before expiration) and start the process early.

### Mistake 3: Mixing Personal and Business Expenses

Claiming personal items as business deductions creates audit risk and isn't deductible.

**Solution:** Use separate business account and categorize transactions immediately. See `references/expense-categories.md` for clear deduction guidelines.

### Mistake 4: Not Tracking Multi-State Requirements

When licensed in multiple states, it's easy to miss requirements in the state where you practice less frequently.

**Solution:** Create state-specific checklists and calendars. Review `references/state-requirements.md` for each state annually.

## Additional Resources

### Reference Files

For detailed information, consult:
- **`references/tax-formulas.md`** - Self-employment tax, estimated payment, QBI calculations with worked examples
- **`references/qbi-eligibility.md`** - Detailed QBI deduction analysis and limitation rules for therapists
- **`references/expense-categories.md`** - Comprehensive deduction guide with documentation requirements per category
- **`references/state-requirements.md`** - Licensing, CE, renewal timelines for Washington, Florida, and research framework for other states
- **`references/record-organization.md`** - File structure, retention periods, documentation best practices

### Examples

Working templates in `examples/`:
- **`quarterly-payment-schedule.csv`** - Sample quarterly estimated tax payment calendar
- **`license-renewal-checklist.md`** - License renewal template for multi-state use
- **`expense-tracker.csv`** - Deduction tracking spreadsheet with categories
- **`state-comparison-template.md`** - Template for comparing two states' requirements

### Scripts

Utilities in `scripts/`:
- **`calculate_quarterly_payments.py`** - Calculate quarterly estimated tax payments based on income projection
- **`ce-hour-tracker.py`** - Organize and validate CE credits toward license renewal requirements

## Important Disclaimer

This skill provides general educational information about therapist business operations and is not legal or tax advice. Therapists should:
- Consult a CPA or tax professional for personalized tax advice
- Verify current state licensing requirements with official state boards
- Review current tax law changes (requirements shift annually)
- Consult an attorney for business structure and liability questions

State requirements and tax law change frequently. Always verify current requirements with official sources.
