"""
Display consistency tests - Python-based testing observing zsh externally.

Tests terminal rendering, line length accuracy, and plugin visual interactions
without the circular dependency of shell-testing-shell.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.base import TestSuite, TestResult


class DisplayTests(TestSuite):
    """Display consistency test suite using Python to observe zsh."""

    def __init__(self, shell_binary: str, zdotdir: str):
        super().__init__(shell_binary, zdotdir, 'display_consistency')

    def run_tests(self) -> None:
        """Run all display tests."""
        self.test_columns_variable()
        self.test_unicode_rendering()
        self.test_color_support()

    def test_columns_variable(self) -> None:
        """Test that COLUMNS variable is set correctly."""
        stdout, stderr, returncode = self.run_shell_command('echo $COLUMNS')

        if returncode == 0 and stdout.strip().isdigit():
            columns = int(stdout.strip())
            result = TestResult(
                'columns_variable',
                'pass' if columns > 0 else 'fail',
                {
                    'columns': columns,
                    'expected': '> 0',
                    'message': f'COLUMNS is {columns}'
                }
            )
        else:
            result = TestResult(
                'columns_variable',
                'fail',
                {
                    'error': 'Could not retrieve COLUMNS value',
                    'stderr': stderr
                }
            )

        self.add_result(result)

    def test_unicode_rendering(self) -> None:
        """Test basic Unicode rendering capability."""
        test_string = '你好世界'  # Chinese characters
        stdout, stderr, returncode = self.run_shell_command(f'echo "{test_string}"')

        if returncode == 0 and test_string in stdout:
            result = TestResult(
                'unicode_rendering',
                'pass',
                {
                    'test_string': test_string,
                    'message': 'Unicode characters rendered correctly'
                }
            )
        else:
            result = TestResult(
                'unicode_rendering',
                'fail',
                {
                    'test_string': test_string,
                    'output': stdout,
                    'error': 'Unicode rendering failed'
                }
            )

        self.add_result(result)

    def test_color_support(self) -> None:
        """Test terminal color support."""
        # Test color capability through tput
        stdout, stderr, returncode = self.run_shell_command('tput colors 2>/dev/null')

        if returncode == 0 and stdout.strip().isdigit():
            colors = int(stdout.strip())
            status = 'pass' if colors >= 8 else 'warn'
            result = TestResult(
                'color_support',
                status,
                {
                    'colors': colors,
                    'message': f'Terminal supports {colors} colors'
                }
            )
        else:
            result = TestResult(
                'color_support',
                'warn',
                {
                    'message': 'Could not determine color support',
                    'stderr': stderr
                }
            )

        self.add_result(result)


def create_suite(shell_binary: str, zdotdir: str) -> DisplayTests:
    """Factory function to create display test suite."""
    return DisplayTests(shell_binary, zdotdir)
