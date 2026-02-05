#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
CE Hour Tracker for Therapist License Renewal.

Organize and validate continuing education credits toward license renewal requirements.
Supports state-specific requirements and provides progress tracking.

Usage:
    uv run scripts/ce-hour-tracker.py --state washington --total-required 20 \
        --add "Grief Counseling|2024-03-15|6|Elective" \
        --add "Ethics in Therapy|2024-05-20|3|Ethics" \
        --add "Cultural Competency|2024-06-10|2|Diversity"

    uv run scripts/ce-hour-tracker.py --state florida --total-required 20 \
        --add "Advanced Trauma Work|2024-02-15|8|Elective" \
        --ethics-required 3 --validate
"""

import argparse
import sys
from datetime import datetime


# State-specific requirements
STATE_REQUIREMENTS = {
    'washington': {
        'renewal_period_years': 2,
        'total_hours': 20,
        'ethics_hours': 3,
        'diversity_hours': 2,
        'domestic_violence_hours': 2,
    },
    'florida': {
        'renewal_period_years': 2,
        'total_hours': 20,
        'ethics_hours': 3,
        'diversity_hours': 0,  # Flexible
        'domestic_violence_hours': 0,  # Flexible
    },
}

# Topic categories for tracking
TOPIC_CATEGORIES = {
    'Ethics': ['ethics', 'ethical', 'professional responsibility'],
    'Diversity': ['diversity', 'cultural', 'multicultural', 'lgbtq', 'trauma-informed'],
    'Domestic Violence': ['domestic violence', 'intimate partner violence', 'trauma'],
    'Elective': [],
}


class CETracker:
    """Track continuing education hours toward license renewal."""

    def __init__(self, state: str, total_required: int, ethics_required: int = 0,
                 diversity_required: int = 0, dv_required: int = 0):
        """
        Initialize CE tracker.

        Args:
            state: State abbreviation (washington, florida, etc.)
            total_required: Total CE hours required for renewal
            ethics_required: Required ethics hours (state-specific)
            diversity_required: Required diversity hours (state-specific)
            dv_required: Required domestic violence hours (state-specific)
        """
        self.state = state.lower()
        self.total_required = total_required
        self.ethics_required = ethics_required
        self.diversity_required = diversity_required
        self.dv_required = dv_required
        self.courses = []

    def add_course(self, title: str, date: str, hours: float, topic: str) -> None:
        """
        Add a CE course.

        Args:
            title: Course name
            date: Completion date (YYYY-MM-DD format)
            hours: Credit hours earned
            topic: Topic category (Ethics, Diversity, Domestic Violence, Elective)
        """
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Invalid date format: {date}. Use YYYY-MM-DD")

        if hours <= 0:
            raise ValueError(f"Hours must be positive. Got: {hours}")

        course = {
            'title': title,
            'date': date,
            'date_obj': date_obj,
            'hours': float(hours),
            'topic': topic,
        }
        self.courses.append(course)

    def categorize_course(self, course: dict) -> str:
        """
        Categorize a course by topic (helper for better categorization).

        Args:
            course: Course dict with 'topic' key

        Returns:
            Standardized topic category
        """
        topic_lower = course['topic'].lower()

        for category, keywords in TOPIC_CATEGORIES.items():
            if category == 'Elective':
                continue
            for keyword in keywords:
                if keyword in topic_lower:
                    return category

        return 'Elective'

    def get_summary(self) -> dict:
        """
        Calculate CE progress summary.

        Returns:
            Dictionary with totals by category and progress metrics
        """
        summary = {
            'total_hours': 0,
            'ethics_hours': 0,
            'diversity_hours': 0,
            'dv_hours': 0,
            'elective_hours': 0,
            'courses_count': len(self.courses),
        }

        for course in self.courses:
            category = self.categorize_course(course)
            summary['total_hours'] += course['hours']

            if category == 'Ethics':
                summary['ethics_hours'] += course['hours']
            elif category == 'Diversity':
                summary['diversity_hours'] += course['hours']
            elif category == 'Domestic Violence':
                summary['dv_hours'] += course['hours']
            else:
                summary['elective_hours'] += course['hours']

        return summary

    def validate(self) -> dict:
        """
        Validate CE progress against state requirements.

        Returns:
            Dictionary with validation results (met/not met for each requirement)
        """
        summary = self.get_summary()

        return {
            'total_met': summary['total_hours'] >= self.total_required,
            'ethics_met': summary['ethics_hours'] >= self.ethics_required,
            'diversity_met': summary['diversity_hours'] >= self.diversity_required,
            'dv_met': summary['dv_hours'] >= self.dv_required,
            'summary': summary,
        }

    def print_summary(self) -> None:
        """Print CE progress summary."""
        summary = self.get_summary()
        validation = self.validate()

        print("\n" + "="*70)
        print(f"CE HOUR TRACKER - {self.state.upper()}")
        print("="*70)

        print(f"\nCourses Completed: {summary['courses_count']}")
        print(f"\nHours by Category:")
        print(f"  Total Hours:          {summary['total_hours']:.1f} / {self.total_required} "
              f"{'✓' if validation['total_met'] else '✗'}")
        print(f"  Ethics Hours:         {summary['ethics_hours']:.1f} / {self.ethics_required} "
              f"{'✓' if validation['ethics_met'] else '✗'}")

        if self.diversity_required > 0:
            print(f"  Diversity Hours:      {summary['diversity_hours']:.1f} / "
                  f"{self.diversity_required} {'✓' if validation['diversity_met'] else '✗'}")

        if self.dv_required > 0:
            print(f"  Domestic Violence:    {summary['dv_hours']:.1f} / "
                  f"{self.dv_required} {'✓' if validation['dv_met'] else '✗'}")

        if self.total_required > 0:
            progress = (summary['total_hours'] / self.total_required) * 100
            print(f"  Elective Hours:       {summary['elective_hours']:.1f}")
            print(f"\nProgress: {progress:.0f}% complete ({summary['total_hours']:.1f}/{self.total_required} hours)")

        print(f"\nCourses:")
        if not self.courses:
            print("  (No courses added)")
        else:
            sorted_courses = sorted(self.courses, key=lambda x: x['date_obj'])
            for i, course in enumerate(sorted_courses, 1):
                category = self.categorize_course(course)
                print(f"  {i}. {course['title']}")
                print(f"     Date: {course['date']} | Hours: {course['hours']} | "
                      f"Category: {category}")

        print(f"\nValidation Status:")
        all_requirements_met = all([
            validation['total_met'],
            validation['ethics_met'] if self.ethics_required > 0 else True,
            validation['diversity_met'] if self.diversity_required > 0 else True,
            validation['dv_met'] if self.dv_required > 0 else True,
        ])

        if all_requirements_met:
            print("  ✓ All requirements met for renewal!")
        else:
            print("  ✗ Some requirements not yet met:")
            if not validation['total_met']:
                needed = self.total_required - summary['total_hours']
                print(f"    - Need {needed:.1f} more total hours")
            if self.ethics_required > 0 and not validation['ethics_met']:
                needed = self.ethics_required - summary['ethics_hours']
                print(f"    - Need {needed:.1f} more ethics hours")
            if self.diversity_required > 0 and not validation['diversity_met']:
                needed = self.diversity_required - summary['diversity_hours']
                print(f"    - Need {needed:.1f} more diversity hours")
            if self.dv_required > 0 and not validation['dv_met']:
                needed = self.dv_required - summary['dv_hours']
                print(f"    - Need {needed:.1f} more domestic violence hours")

        print("\n" + "="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Track CE hours toward therapist license renewal',
        epilog='Use --state to automatically load state-specific requirements'
    )

    parser.add_argument(
        '--state',
        type=str,
        choices=list(STATE_REQUIREMENTS.keys()),
        help='State for license renewal (loads state-specific requirements)'
    )

    parser.add_argument(
        '--total-required',
        type=int,
        default=20,
        help='Total CE hours required for renewal (default: 20)'
    )

    parser.add_argument(
        '--ethics-required',
        type=int,
        default=0,
        help='Required ethics hours (use --state to auto-fill)'
    )

    parser.add_argument(
        '--diversity-required',
        type=int,
        default=0,
        help='Required diversity hours (use --state to auto-fill)'
    )

    parser.add_argument(
        '--dv-required',
        type=int,
        default=0,
        help='Required domestic violence hours (use --state to auto-fill)'
    )

    parser.add_argument(
        '--add',
        action='append',
        dest='courses',
        help='Add a course: "Title|YYYY-MM-DD|hours|Topic" (can use multiple times)'
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Show validation summary'
    )

    args = parser.parse_args()

    # Load state-specific requirements if state provided
    if args.state:
        state_reqs = STATE_REQUIREMENTS[args.state]
        total_required = args.total_required
        ethics_required = state_reqs['ethics_hours']
        diversity_required = state_reqs['diversity_hours']
        dv_required = state_reqs['domestic_violence_hours']
    else:
        total_required = args.total_required
        ethics_required = args.ethics_required
        diversity_required = args.diversity_required
        dv_required = args.dv_required

    # Create tracker
    state_name = args.state or 'custom'
    tracker = CETracker(
        state=state_name,
        total_required=total_required,
        ethics_required=ethics_required,
        diversity_required=diversity_required,
        dv_required=dv_required,
    )

    # Add courses
    if args.courses:
        for course_str in args.courses:
            try:
                parts = course_str.split('|')
                if len(parts) != 4:
                    print(f"Error: Course format should be 'Title|YYYY-MM-DD|hours|Topic'",
                          file=sys.stderr)
                    print(f"Got: {course_str}", file=sys.stderr)
                    sys.exit(1)

                title, date, hours_str, topic = parts
                hours = float(hours_str)
                tracker.add_course(title.strip(), date.strip(), hours, topic.strip())
            except ValueError as e:
                print(f"Error adding course: {e}", file=sys.stderr)
                sys.exit(1)

    # Show summary
    tracker.print_summary()

    # Validate if requested
    if args.validate:
        validation = tracker.validate()
        all_met = all([
            validation['total_met'],
            validation['ethics_met'],
            validation['diversity_met'],
            validation['dv_met'],
        ])
        sys.exit(0 if all_met else 1)


if __name__ == '__main__':
    main()
