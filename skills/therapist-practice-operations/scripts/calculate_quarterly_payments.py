#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
Calculate quarterly estimated tax payments for therapist sole proprietors.

This script helps determine quarterly tax payment amounts based on income projections,
using IRS safe harbor rules to avoid penalties.

Usage:
    uv run scripts/calculate_quarterly_payments.py --income 80000 --expenses 15000
    uv run scripts/calculate_quarterly_payments.py --income 100000 --expenses 20000 --prior-year 18000
"""

import argparse
import sys


def calculate_self_employment_tax(net_profit: float) -> float:
    """
    Calculate self-employment tax (Social Security + Medicare).

    Args:
        net_profit: Net business income after deductions

    Returns:
        Self-employment tax liability
    """
    # Apply adjustment factor (92.35% of net profit subject to SE tax)
    adjusted_profit = net_profit * 0.9235
    # Apply SE tax rate (15.3%: 12.4% SS + 2.9% Medicare)
    se_tax = adjusted_profit * 0.153
    return se_tax


def estimate_income_tax(net_profit: float, se_tax: float, standard_deduction: float = 14600) -> float:
    """
    Rough estimate of federal income tax (simplified for 2026).

    Note: This is a simplified estimate. Use actual tax brackets and consult a CPA
    for accurate calculation.

    Args:
        net_profit: Net business income
        se_tax: Self-employment tax calculated
        standard_deduction: Standard deduction for tax year (single filer default)

    Returns:
        Estimated federal income tax
    """
    # Deductible portion of SE tax
    se_tax_deduction = se_tax * 0.5

    # Adjusted gross income
    agi = net_profit - se_tax_deduction

    # Taxable income (simplified; doesn't account for all deductions)
    taxable_income = max(0, agi - standard_deduction)

    # Very simplified tax calculation (2026 approximate brackets for single filer)
    # This is NOT accurate; use actual tax software or CPA
    if taxable_income <= 11600:
        income_tax = taxable_income * 0.10
    elif taxable_income <= 47150:
        income_tax = 1160 + (taxable_income - 11600) * 0.12
    elif taxable_income <= 100525:
        income_tax = 5426 + (taxable_income - 47150) * 0.22
    else:
        income_tax = 17168.50 + (taxable_income - 100525) * 0.24

    return income_tax


def calculate_quarterly_payments(
    estimated_income: float,
    estimated_expenses: float,
    prior_year_tax: float | None = None,
    safe_harbor_percentage: float = 1.0
) -> dict:
    """
    Calculate quarterly estimated tax payment amounts using safe harbor rules.

    Safe harbor: Avoid penalties if total quarterly payments equal at least:
    - 100% of prior year tax liability, OR
    - 90% of current year estimated tax liability

    For high earners (>$150k): 110% of prior year required

    Args:
        estimated_income: Projected annual therapy income
        estimated_expenses: Projected annual business expenses
        prior_year_tax: Actual total tax from previous year (for safe harbor)
        safe_harbor_percentage: 1.0 for under $150k AGI, 1.1 for over $150k

    Returns:
        Dictionary with payment amounts and analysis
    """
    # Calculate net profit
    net_profit = estimated_income - estimated_expenses

    # Calculate taxes
    se_tax = calculate_self_employment_tax(net_profit)
    income_tax = estimate_income_tax(net_profit, se_tax)
    total_tax = se_tax + income_tax

    # Determine safe harbor amounts
    safe_harbor_prior = prior_year_tax * safe_harbor_percentage if prior_year_tax else None
    safe_harbor_current = total_tax * 0.90

    # Quarterly payment (equal distribution)
    quarterly_payment = total_tax / 4

    # Safe harbor check
    if safe_harbor_prior and safe_harbor_current:
        safe_harbor_amount = max(safe_harbor_prior, safe_harbor_current)
        total_safe_harbor = safe_harbor_amount
    elif safe_harbor_prior:
        safe_harbor_amount = safe_harbor_prior
        total_safe_harbor = safe_harbor_amount
    else:
        safe_harbor_amount = safe_harbor_current
        total_safe_harbor = safe_harbor_amount

    quarterly_safe_harbor = total_safe_harbor / 4

    return {
        'estimated_income': estimated_income,
        'estimated_expenses': estimated_expenses,
        'net_profit': net_profit,
        'self_employment_tax': se_tax,
        'income_tax': income_tax,
        'total_tax': total_tax,
        'quarterly_payment_equal': quarterly_payment,
        'safe_harbor_amount': safe_harbor_amount,
        'safe_harbor_quarterly': quarterly_safe_harbor,
        'q1_due': 'April 15',
        'q2_due': 'June 15',
        'q3_due': 'September 15',
        'q4_due': 'January 15 (next year)',
    }


def print_results(results: dict) -> None:
    """Print quarterly payment calculation results."""

    print("\n" + "="*60)
    print("QUARTERLY ESTIMATED TAX PAYMENT CALCULATION")
    print("="*60)

    print(f"\nIncome & Expense Projection:")
    print(f"  Estimated Annual Income:    ${results['estimated_income']:,.2f}")
    print(f"  Estimated Annual Expenses:  ${results['estimated_expenses']:,.2f}")
    print(f"  Net Business Profit:        ${results['net_profit']:,.2f}")

    print(f"\nTax Liability Calculation:")
    print(f"  Self-Employment Tax:        ${results['self_employment_tax']:,.2f}")
    print(f"  Estimated Income Tax:       ${results['income_tax']:,.2f}")
    print(f"  Total Tax Liability:        ${results['total_tax']:,.2f}")

    print(f"\nQuarterly Payment Amounts:")
    print(f"  Equal Distribution Method:  ${results['quarterly_payment_equal']:,.2f} per quarter")
    print(f"  Safe Harbor Amount:         ${results['safe_harbor_amount']:,.2f} total")
    print(f"  Safe Harbor per Quarter:    ${results['safe_harbor_quarterly']:,.2f} per quarter")

    print(f"\nPayment Due Dates:")
    print(f"  Q1 (Jan-Mar):  {results['q1_due']}")
    print(f"  Q2 (Apr-May):  {results['q2_due']}")
    print(f"  Q3 (Jun-Aug):  {results['q3_due']}")
    print(f"  Q4 (Sep-Dec):  {results['q4_due']}")

    print(f"\nSuggested Quarterly Payments:")
    quarterly = results['safe_harbor_quarterly']
    print(f"  Q1 Payment (due April 15):     ${quarterly:,.2f}")
    print(f"  Q2 Payment (due June 15):      ${quarterly:,.2f}")
    print(f"  Q3 Payment (due Sept 15):      ${quarterly:,.2f}")
    print(f"  Q4 Payment (due Jan 15):       ${quarterly:,.2f}")
    print(f"  Total Annual Payments:         ${quarterly * 4:,.2f}")

    print(f"\nIMPORTANT NOTES:")
    print(f"  * This is a simplified estimate. Use actual tax software or consult a CPA.")
    print(f"  * Adjust payments mid-year if actual income differs from projection.")
    print(f"  * Keep payment confirmations for your tax records.")
    print(f"  * Safe harbor rules help avoid penalties (see references/tax-formulas.md).")
    print("\n" + "="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Calculate quarterly estimated tax payments for therapists',
        epilog='Example: python calculate_quarterly_payments.py --income 85000 --expenses 12000'
    )

    parser.add_argument(
        '--income',
        type=float,
        required=True,
        help='Estimated annual therapy income'
    )
    parser.add_argument(
        '--expenses',
        type=float,
        required=True,
        help='Estimated annual business expenses'
    )
    parser.add_argument(
        '--prior-year',
        type=float,
        help='Prior year total tax liability (for safe harbor calculation)'
    )
    parser.add_argument(
        '--high-earner',
        action='store_true',
        help='Use 110% safe harbor (for income over $150k AGI)'
    )

    args = parser.parse_args()

    # Validate inputs
    if args.income <= 0:
        print("Error: Income must be positive", file=sys.stderr)
        sys.exit(1)
    if args.expenses < 0:
        print("Error: Expenses cannot be negative", file=sys.stderr)
        sys.exit(1)

    safe_harbor = 1.1 if args.high_earner else 1.0

    results = calculate_quarterly_payments(
        estimated_income=args.income,
        estimated_expenses=args.expenses,
        prior_year_tax=args.prior_year if args.prior_year else None,
        safe_harbor_percentage=safe_harbor
    )

    print_results(results)


if __name__ == '__main__':
    main()
