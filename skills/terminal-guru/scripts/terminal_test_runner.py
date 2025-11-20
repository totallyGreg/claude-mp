#!/usr/bin/env python3
"""
Terminal Test Runner - Main orchestrator for terminal testing workflow.

This module:
1. Creates isolated test environments
2. Executes test suites
3. Aggregates test outputs
4. Coordinates with output analyzer
5. Handles iterative test cycles

All test logic is in Python to avoid shell-testing-shell circular dependency.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from environment_builder import EnvironmentBuilder
from tests.base import save_results, load_results


class TerminalTestRunner:
    """Main orchestrator for terminal testing workflow."""

    def __init__(self, user_config_path: Optional[str] = None, test_name: str = "test"):
        """
        Initialize test runner.

        Args:
            user_config_path: Path to user's config (default: $HOME)
            test_name: Identifier for this test run
        """
        self.test_name = test_name
        self.user_config_path = user_config_path
        self.env_builder = EnvironmentBuilder()
        self.zdotdir: Optional[str] = None
        self.env_path: Optional[Path] = None
        self.shell_binary = "/bin/zsh"  # Default, can be configured

    def create_environment(self) -> str:
        """
        Create isolated ZDOTDIR and return path.

        Returns:
            Path to created ZDOTDIR
        """
        print(f"Creating isolated test environment: {self.test_name}")
        self.zdotdir = self.env_builder.create_environment(
            self.test_name,
            self.user_config_path
        )

        # Get parent environment path
        self.env_path = Path(self.zdotdir).parent

        print(f"Environment created at: {self.env_path}")
        print(f"ZDOTDIR: {self.zdotdir}")

        return self.zdotdir

    def run_all_tests(self) -> Dict:
        """
        Execute all test suites and return aggregated results.

        Returns:
            Aggregated test results dictionary
        """
        if not self.zdotdir:
            raise RuntimeError("Environment not created. Call create_environment() first.")

        print("\nRunning comprehensive test suite...")

        results = {
            'test_name': self.test_name,
            'timestamp': datetime.now().isoformat(),
            'zdotdir': self.zdotdir,
            'suites': {}
        }

        # Run test suites in order
        suites = ['display', 'performance', 'compatibility']

        for suite_name in suites:
            print(f"\nRunning {suite_name} tests...")
            suite_results = self.run_test_suite(suite_name)
            results['suites'][suite_name] = suite_results

        # Save aggregate results
        results_file = self.env_path / "results" / "all_results.json"
        save_results(results, results_file)

        print(f"\nResults saved to: {results_file}")

        return results

    def run_test_suite(self, suite_name: str) -> Dict:
        """
        Execute specific test suite.

        Args:
            suite_name: Name of suite to run (display, performance, compatibility)

        Returns:
            Test suite results dictionary
        """
        # Import test suite dynamically
        suite_module = self._import_test_suite(suite_name)

        if suite_module:
            # Run the test suite
            suite = suite_module.create_suite(self.shell_binary, self.zdotdir)
            suite.run_tests()
            results = suite.to_dict()

            # Save suite-specific results
            results_file = self.env_path / "results" / f"{suite_name}_results.json"
            save_results(results, results_file)

            return results
        else:
            # Return placeholder for unimplemented suites
            return {
                'suite': suite_name,
                'status': 'not_implemented',
                'message': f'{suite_name} test suite not yet implemented'
            }

    def _import_test_suite(self, suite_name: str):
        """
        Dynamically import test suite module.

        Args:
            suite_name: Name of suite to import

        Returns:
            Test suite module or None if not found
        """
        try:
            if suite_name == 'display':
                from tests import display_tests
                return display_tests
            elif suite_name == 'performance':
                from tests import performance_tests
                return performance_tests
            elif suite_name == 'compatibility':
                from tests import plugin_tests
                return plugin_tests
        except ImportError as e:
            print(f"Warning: Could not import {suite_name} tests: {e}")
            return None

    def analyze_results(self, results: Dict) -> Dict:
        """
        Analyze test results and generate recommendations.

        Args:
            results: Test results dictionary

        Returns:
            Analysis with recommendations
        """
        try:
            from analysis.output_analyzer import OutputAnalyzer
            analyzer = OutputAnalyzer(results)
            return analyzer.analyze()
        except ImportError:
            return {
                'status': 'not_implemented',
                'message': 'Output analyzer not yet implemented'
            }

    def compare_runs(self, baseline_path: str, current_path: str) -> Dict:
        """
        Compare two test runs.

        Args:
            baseline_path: Path to baseline results JSON
            current_path: Path to current results JSON

        Returns:
            Comparison results
        """
        baseline = load_results(Path(baseline_path))
        current = load_results(Path(current_path))

        comparison = {
            'baseline': baseline_path,
            'current': current_path,
            'improvements': [],
            'regressions': [],
            'unchanged': []
        }

        # Compare each suite
        for suite_name in baseline.get('suites', {}).keys():
            if suite_name in current.get('suites', {}):
                baseline_suite = baseline['suites'][suite_name]
                current_suite = current['suites'][suite_name]

                baseline_status = baseline_suite.get('summary', {}).get('overall_status')
                current_status = current_suite.get('summary', {}).get('overall_status')

                if baseline_status == 'fail' and current_status == 'pass':
                    comparison['improvements'].append({
                        'suite': suite_name,
                        'change': 'fixed'
                    })
                elif baseline_status == 'pass' and current_status == 'fail':
                    comparison['regressions'].append({
                        'suite': suite_name,
                        'change': 'broke'
                    })
                else:
                    comparison['unchanged'].append(suite_name)

        return comparison

    def cleanup(self, preserve: bool = False) -> None:
        """
        Clean up test environment.

        Args:
            preserve: If True, keep the environment for inspection
        """
        if not preserve and self.env_path:
            print(f"\nCleaning up test environment: {self.env_path}")
            self.env_builder.cleanup_environment(str(self.env_path))
        elif preserve:
            print(f"\nPreserving test environment at: {self.env_path}")


def main():
    """Command-line interface for test runner."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Run terminal tests in isolated environment'
    )
    parser.add_argument(
        '--name',
        default='test',
        help='Name for this test run (default: test)'
    )
    parser.add_argument(
        '--source',
        help='Source config directory (default: $HOME)'
    )
    parser.add_argument(
        '--shell',
        default='/bin/zsh',
        help='Shell binary to test (default: /bin/zsh)'
    )
    parser.add_argument(
        '--suite',
        choices=['display', 'performance', 'compatibility', 'all'],
        default='all',
        help='Test suite to run (default: all)'
    )
    parser.add_argument(
        '--preserve',
        action='store_true',
        help='Preserve test environment after completion'
    )
    parser.add_argument(
        '--compare',
        nargs=2,
        metavar=('BASELINE', 'CURRENT'),
        help='Compare two test result files'
    )

    args = parser.parse_args()

    # Handle comparison mode
    if args.compare:
        runner = TerminalTestRunner()
        comparison = runner.compare_runs(args.compare[0], args.compare[1])
        print("\nTest Comparison:")
        print(json.dumps(comparison, indent=2))
        return

    # Create runner
    runner = TerminalTestRunner(args.source, args.name)
    runner.shell_binary = args.shell

    try:
        # Create environment
        runner.create_environment()

        # Run tests
        if args.suite == 'all':
            results = runner.run_all_tests()
        else:
            results = {
                'test_name': args.name,
                'timestamp': datetime.now().isoformat(),
                'suites': {
                    args.suite: runner.run_test_suite(args.suite)
                }
            }

        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        for suite_name, suite_results in results.get('suites', {}).items():
            summary = suite_results.get('summary', {})
            print(f"\n{suite_name.upper()}:")
            print(f"  Total: {summary.get('total_tests', 'N/A')}")
            print(f"  Passed: {summary.get('passed', 'N/A')}")
            print(f"  Failed: {summary.get('failed', 'N/A')}")
            print(f"  Status: {summary.get('overall_status', 'N/A')}")

    finally:
        # Cleanup
        runner.cleanup(preserve=args.preserve)


if __name__ == '__main__':
    main()
