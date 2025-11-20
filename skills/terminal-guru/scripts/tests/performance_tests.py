"""
Performance tests - Python-based shell performance measurement.

Measures and benchmarks zsh startup time, plugin load times, and responsiveness
using Python for precise external timing (no shell measuring itself).
"""

import time
import subprocess
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.base import TestSuite, TestResult


class PerformanceTests(TestSuite):
    """Performance test suite using Python for precise timing."""

    def __init__(self, shell_binary: str, zdotdir: str):
        super().__init__(shell_binary, zdotdir, 'performance')

    def run_tests(self) -> None:
        """Run all performance tests."""
        self.test_startup_time()
        self.test_command_execution()
        self.test_zprof_available()

    def test_startup_time(self) -> None:
        """Measure shell startup time from outside (Python timing)."""
        # Python times the shell startup externally
        start = time.perf_counter()

        try:
            result = subprocess.run(
                [self.shell_binary, '-i', '-c', 'exit'],
                env={'ZDOTDIR': self.zdotdir},
                capture_output=True,
                timeout=10
            )
            end = time.perf_counter()
            startup_ms = (end - start) * 1000

            # Determine rating
            if startup_ms < 100:
                rating = 'excellent'
            elif startup_ms < 250:
                rating = 'good'
            elif startup_ms < 500:
                rating = 'acceptable'
            else:
                rating = 'poor'

            status = 'pass' if startup_ms < 500 else 'warn'

            test_result = TestResult(
                'startup_time',
                status,
                {
                    'time_ms': round(startup_ms, 2),
                    'rating': rating,
                    'message': f'Startup time: {startup_ms:.2f}ms ({rating})'
                }
            )
        except subprocess.TimeoutExpired:
            test_result = TestResult(
                'startup_time',
                'fail',
                {
                    'error': 'Startup timed out after 10s',
                    'message': 'Shell startup is extremely slow'
                }
            )

        self.add_result(test_result)

    def test_command_execution(self) -> None:
        """Test basic command execution latency."""
        # Time a simple command execution
        start = time.perf_counter()

        stdout, stderr, returncode = self.run_shell_command('true')

        end = time.perf_counter()
        latency_ms = (end - start) * 1000

        # Determine rating
        if latency_ms < 50:
            rating = 'good'
            status = 'pass'
        elif latency_ms < 100:
            rating = 'acceptable'
            status = 'pass'
        else:
            rating = 'slow'
            status = 'warn'

        result = TestResult(
            'command_execution',
            status,
            {
                'latency_ms': round(latency_ms, 2),
                'rating': rating,
                'message': f'Command execution: {latency_ms:.2f}ms ({rating})'
            }
        )

        self.add_result(result)

    def test_zprof_available(self) -> None:
        """Check if zsh/zprof module is available for profiling."""
        stdout, stderr, returncode = self.run_shell_command(
            'zmodload zsh/zprof 2>&1 && echo "available"'
        )

        if 'available' in stdout:
            result = TestResult(
                'zprof_available',
                'pass',
                {
                    'message': 'zsh/zprof module available for profiling'
                }
            )
        else:
            result = TestResult(
                'zprof_available',
                'warn',
                {
                    'message': 'zsh/zprof not available - advanced profiling limited'
                }
            )

        self.add_result(result)


def create_suite(shell_binary: str, zdotdir: str) -> PerformanceTests:
    """Factory function to create performance test suite."""
    return PerformanceTests(shell_binary, zdotdir)
