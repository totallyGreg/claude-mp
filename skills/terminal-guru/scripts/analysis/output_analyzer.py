"""
Output Analyzer - Parse test results and generate recommendations.

This module analyzes test results, identifies patterns, compares iterations,
and generates actionable recommendations for configuration improvements.
"""

from typing import Dict, List, Any


class OutputAnalyzer:
    """Analyze test outputs and generate recommendations."""

    def __init__(self, test_results: Dict):
        """
        Initialize with test results dictionary.

        Args:
            test_results: Test results from terminal_test_runner
        """
        self.test_results = test_results

    def analyze(self) -> Dict:
        """
        Analyze test results and generate recommendations.

        Returns:
            Analysis dictionary with recommendations
        """
        analysis = {
            'test_name': self.test_results.get('test_name', 'unknown'),
            'timestamp': self.test_results.get('timestamp'),
            'failures': self.identify_failures(),
            'warnings': self.identify_warnings(),
            'recommendations': []
        }

        # Generate recommendations based on failures
        analysis['recommendations'] = self.generate_recommendations(
            analysis['failures'],
            analysis['warnings']
        )

        return analysis

    def identify_failures(self) -> List[Dict]:
        """Extract all test failures across suites."""
        failures = []

        for suite_name, suite_results in self.test_results.get('suites', {}).items():
            for result in suite_results.get('results', []):
                if result.get('status') == 'fail':
                    failures.append({
                        'suite': suite_name,
                        'test': result.get('test'),
                        'details': result
                    })

        return failures

    def identify_warnings(self) -> List[Dict]:
        """Extract all test warnings across suites."""
        warnings = []

        for suite_name, suite_results in self.test_results.get('suites', {}).items():
            for result in suite_results.get('results', []):
                if result.get('status') == 'warn':
                    warnings.append({
                        'suite': suite_name,
                        'test': result.get('test'),
                        'details': result
                    })

        return warnings

    def generate_recommendations(self, failures: List[Dict], warnings: List[Dict]) -> List[Dict]:
        """
        Generate prioritized config change recommendations.

        Args:
            failures: List of failed tests
            warnings: List of warned tests

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        # Analyze failures and generate recommendations
        for failure in failures:
            test_name = failure['test']

            if test_name == 'unicode_rendering':
                recommendations.append({
                    'priority': 'high',
                    'category': 'display',
                    'issue': 'Unicode rendering failed',
                    'fix': {
                        'type': 'environment_variable',
                        'changes': {
                            'LANG': 'en_US.UTF-8',
                            'LC_ALL': 'en_US.UTF-8'
                        },
                        'file': '.zshenv',
                        'confidence': 'high'
                    }
                })

        # Analyze warnings and generate recommendations
        for warning in warnings:
            test_name = warning['test']

            if test_name == 'startup_time':
                details = warning['details']
                if details.get('time_ms', 0) > 500:
                    recommendations.append({
                        'priority': 'medium',
                        'category': 'performance',
                        'issue': f'Slow startup time: {details.get("time_ms")}ms',
                        'fix': {
                            'type': 'profile',
                            'suggestion': 'Use zsh/zprof to identify slow functions',
                            'confidence': 'medium'
                        }
                    })

        return recommendations
