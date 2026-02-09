"""
Base test utilities for terminal testing.

Provides shared infrastructure for display, performance, and plugin tests.
All test logic is implemented in Python to avoid shell-testing-shell circular dependency.
"""

import subprocess
import time
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class TestResult:
    """Represents a single test result."""

    def __init__(self, test_name: str, status: str, details: Optional[Dict] = None):
        """
        Initialize test result.

        Args:
            test_name: Name of the test
            status: 'pass', 'fail', or 'warn'
            details: Optional detailed information about the test
        """
        self.test_name = test_name
        self.status = status
        self.details = details or {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'test': self.test_name,
            'status': self.status,
            'timestamp': self.timestamp,
            **self.details
        }


class TestSuite:
    """Base class for test suites."""

    def __init__(self, shell_binary: str, zdotdir: str, suite_name: str):
        """
        Initialize test suite.

        Args:
            shell_binary: Path to shell binary (e.g., /bin/zsh)
            zdotdir: Path to isolated ZDOTDIR for testing
            suite_name: Name of this test suite
        """
        self.shell_binary = shell_binary
        self.zdotdir = zdotdir
        self.suite_name = suite_name
        self.results: List[TestResult] = []

    def run_shell_command(self, command: str, env: Optional[Dict] = None,
                         timeout: int = 5) -> Tuple[str, str, int]:
        """
        Run a shell command and return output.

        Args:
            command: Shell command to execute
            env: Optional environment variables
            timeout: Command timeout in seconds

        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        test_env = {'ZDOTDIR': self.zdotdir}
        if env:
            test_env.update(env)

        try:
            result = subprocess.run(
                [self.shell_binary, '-c', command],
                env=test_env,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return '', f'Command timed out after {timeout}s', -1

    def add_result(self, result: TestResult) -> None:
        """Add a test result to this suite."""
        self.results.append(result)

    def get_summary(self) -> Dict:
        """Get summary of test results."""
        passed = sum(1 for r in self.results if r.status == 'pass')
        failed = sum(1 for r in self.results if r.status == 'fail')
        warned = sum(1 for r in self.results if r.status == 'warn')

        return {
            'suite': self.suite_name,
            'total_tests': len(self.results),
            'passed': passed,
            'failed': failed,
            'warned': warned,
            'overall_status': 'fail' if failed > 0 else ('warn' if warned > 0 else 'pass')
        }

    def to_dict(self) -> Dict:
        """Convert all results to dictionary for JSON serialization."""
        return {
            'suite': self.suite_name,
            'timestamp': time.time(),
            'results': [r.to_dict() for r in self.results],
            'summary': self.get_summary()
        }


class PTYHelper:
    """Helper for pseudo-terminal operations."""

    @staticmethod
    def spawn_shell(shell_binary: str, zdotdir: str, env: Optional[Dict] = None) -> subprocess.Popen:
        """
        Spawn a shell in a controlled environment.

        Args:
            shell_binary: Path to shell binary
            zdotdir: Path to isolated ZDOTDIR
            env: Optional additional environment variables

        Returns:
            Popen object for the spawned shell
        """
        test_env = {'ZDOTDIR': zdotdir}
        if env:
            test_env.update(env)

        # Note: This basic implementation uses subprocess.Popen
        # For interactive testing, pexpect should be used (added as dependency)
        return subprocess.Popen(
            [shell_binary, '-i'],
            env=test_env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    @staticmethod
    def measure_timing(func) -> Tuple[float, any]:
        """
        Measure execution time of a function.

        Args:
            func: Function to measure

        Returns:
            Tuple of (elapsed_ms, function_result)
        """
        start = time.perf_counter()
        result = func()
        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000
        return elapsed_ms, result


def save_results(results: Dict, output_path: Path) -> None:
    """
    Save test results to JSON file.

    Args:
        results: Results dictionary
        output_path: Path to save JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)


def load_results(input_path: Path) -> Dict:
    """
    Load test results from JSON file.

    Args:
        input_path: Path to JSON file

    Returns:
        Results dictionary
    """
    with open(input_path, 'r') as f:
        return json.load(f)
