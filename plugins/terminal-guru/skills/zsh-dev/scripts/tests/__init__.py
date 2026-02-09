"""
Terminal testing framework - Test suites.

This package contains Python-based test suites that observe shells externally
to avoid the circular dependency problem of shell-testing-shell.
"""

from .base import TestResult, TestSuite, PTYHelper, save_results, load_results

__all__ = ['TestResult', 'TestSuite', 'PTYHelper', 'save_results', 'load_results']
