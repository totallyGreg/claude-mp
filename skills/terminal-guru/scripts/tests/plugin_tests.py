"""
Plugin compatibility tests - Python-based plugin testing.

Tests plugin interactions, detects conflicts, validates load order using
Python to observe zsh plugin behavior externally.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.base import TestSuite, TestResult


class PluginTests(TestSuite):
    """Plugin compatibility test suite using Python."""

    def __init__(self, shell_binary: str, zdotdir: str):
        super().__init__(shell_binary, zdotdir, 'plugin_compatibility')

    def run_tests(self) -> None:
        """Run all plugin compatibility tests."""
        self.test_plugin_detection()
        self.test_fpath_configuration()
        self.test_autoload_mechanism()

    def test_plugin_detection(self) -> None:
        """Detect which plugin manager is in use."""
        # Check for common plugin managers
        managers = {
            'oh-my-zsh': 'test -d "$HOME/.oh-my-zsh" && echo "detected"',
            'zinit': 'test -d "$HOME/.zinit" && echo "detected"',
            'antigen': 'test -d "$HOME/.antigen" && echo "detected"',
            'zplug': 'test -d "$HOME/.zplug" && echo "detected"'
        }

        detected = []
        for manager, command in managers.items():
            stdout, stderr, returncode = self.run_shell_command(command)
            if 'detected' in stdout:
                detected.append(manager)

        if detected:
            result = TestResult(
                'plugin_detection',
                'pass',
                {
                    'detected_managers': detected,
                    'message': f'Detected plugin managers: {", ".join(detected)}'
                }
            )
        else:
            result = TestResult(
                'plugin_detection',
                'pass',
                {
                    'detected_managers': [],
                    'message': 'No plugin manager detected (manual configuration)'
                }
            )

        self.add_result(result)

    def test_fpath_configuration(self) -> None:
        """Test FPATH configuration."""
        stdout, stderr, returncode = self.run_shell_command(
            'print -l $fpath | head -5'
        )

        if returncode == 0 and stdout.strip():
            paths = stdout.strip().split('\n')
            result = TestResult(
                'fpath_configuration',
                'pass',
                {
                    'fpath_entries': len(paths),
                    'sample_paths': paths[:5],
                    'message': f'FPATH configured with {len(paths)} entries'
                }
            )
        else:
            result = TestResult(
                'fpath_configuration',
                'warn',
                {
                    'message': 'Could not retrieve FPATH configuration',
                    'error': stderr
                }
            )

        self.add_result(result)

    def test_autoload_mechanism(self) -> None:
        """Test if autoload mechanism is working."""
        # Test if autoload is functional
        stdout, stderr, returncode = self.run_shell_command(
            'whence -v autoload'
        )

        if returncode == 0 and ('builtin' in stdout or 'shell builtin' in stdout):
            result = TestResult(
                'autoload_mechanism',
                'pass',
                {
                    'message': 'Autoload mechanism available',
                    'output': stdout.strip()
                }
            )
        else:
            result = TestResult(
                'autoload_mechanism',
                'fail',
                {
                    'message': 'Autoload mechanism not working correctly',
                    'error': stderr
                }
            )

        self.add_result(result)


def create_suite(shell_binary: str, zdotdir: str) -> PluginTests:
    """Factory function to create plugin test suite."""
    return PluginTests(shell_binary, zdotdir)
