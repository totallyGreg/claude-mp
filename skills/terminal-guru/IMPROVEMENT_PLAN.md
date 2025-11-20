# Terminal-Guru Skill Improvement Plan

**Version:** 2.1
**Date:** 2025-11-20
**Author:** Greg Williams
**Status:** Planning

**Changelog:**
- v2.1 (2025-11-20): Updated to Python-based testing architecture to eliminate shell-testing-shell circular dependency
- v2.0 (2025-11-20): Initial comprehensive improvement plan

---

## Executive Summary

This document outlines a comprehensive improvement plan for the terminal-guru skill, transforming it from a diagnostic tool into a complete zsh testing and optimization framework. The enhanced skill will provide isolated test environments, Python-based automated testing across multiple dimensions (display consistency, performance, plugin compatibility), and iterative configuration improvement without affecting the user's current shell setup.

**Key Innovation:** All test logic is implemented in Python rather than shell scripts, eliminating the circular dependency problem of "shell testing shell." Python observes zsh externally via PTY/pexpect, ensuring test infrastructure bugs cannot contaminate results.

**Key Goals:**
- Create repeatable, isolated zsh testing environments using ZDOTDIR
- Implement comprehensive Python test suites observing shells externally
- Enable iterative testing and configuration refinement
- Capture and analyze test outputs for intelligent recommendations
- Focus on zsh initially with Python architecture supporting future shell expansion (bash, fish)

---

## Current State Analysis

### Existing Capabilities

The terminal-guru skill (v1.0.0) currently provides:

**Diagnostic Tools:**
- `terminal_diagnostics.py` - Comprehensive environment analysis (env vars, locale, terminfo, Unicode, shell config)
- `install_autoload.sh` - Zsh autoload function installer

**Reference Documentation:**
- `terminfo_guide.md` - Terminal capability database reference
- `unicode_troubleshooting.md` - UTF-8 and character encoding issues
- `zsh_configuration.md` - Startup files, autoload, fpath, completion system

**Workflow:**
1. Gather information via diagnostics
2. Identify problem domain
3. Apply targeted fixes using reference guides
4. Persist configuration changes

### Current Gaps

**Testing Infrastructure:**
- No repeatable test environment creation
- No automated test execution framework
- No output capture or comparison capabilities
- No iterative testing workflow

**Plugin Support:**
- No zsh plugin-specific diagnostics
- No plugin manager integration (oh-my-zsh, zinit, antigen)
- No plugin conflict detection
- Missing documentation for popular plugins (auto-suggest, syntax-highlighting, powerlevel10k)

**Display Consistency:**
- No systematic testing for line length discrepancies
- No validation of plugin visual interactions
- No automated detection of rendering issues

**Performance Analysis:**
- No startup time profiling
- No plugin load time measurement
- No responsiveness benchmarking

**Configuration Management:**
- Changes affect live user environment
- No isolated testing capability
- No before/after comparison
- No rollback mechanism

---

## Goals and Objectives

### Primary Goals

1. **Isolated Test Environments**
   - Create safe, reproducible zsh instances using ZDOTDIR
   - Enable configuration experimentation without affecting user's shell
   - Support multiple concurrent test environments

2. **Comprehensive Testing Framework**
   - Display consistency testing (rendering, line length, visual correctness)
   - Performance profiling (startup time, plugin load times, responsiveness)
   - Plugin compatibility testing (interactions, conflicts, load order)

3. **Iterative Improvement Workflow**
   - Test → Analyze → Modify → Re-test cycle
   - Output capture and comparison across iterations
   - Intelligent failure analysis
   - Automated configuration recommendations

4. **Enhanced Plugin Support**
   - Test popular zsh plugins (auto-suggest, syntax-highlighting, powerlevel10k)
   - Validate plugin manager configurations
   - Detect plugin conflicts and load order issues
   - Reference documentation for plugin best practices

### Non-Goals (For v2.0)

- Support for bash, fish, or other shells (deferred to future versions)
- CI/CD pipeline integration (focus on interactive use)
- Fully automated fix application (user reviews changes)
- Web-based dashboard or GUI

---

## Testing Philosophy: Why Python?

### The Problem with Shell-Testing-Shell

**Critical Design Decision:** All test logic is implemented in Python rather than shell scripts. This architectural choice solves a fundamental problem: **you cannot reliably use a system to test itself**.

**Why Shell Scripts Would Fail:**

1. **Circular Dependency**
   - If zsh has a line-length bug, shell test scripts running in zsh are affected by that same bug
   - Using bash to test zsh means assuming bash is bug-free
   - Test results become unreliable when the test infrastructure shares bugs with the system under test

2. **Observer Effect**
   - Sourcing .zshrc in a test script changes the test script's environment
   - Test execution itself modifies the state being tested
   - Impossible to distinguish between test infrastructure behavior and test subject behavior

3. **Environmental Contamination**
   - Test scripts inherit shell state from the environment
   - Different shell versions produce different test results
   - Shell-specific behaviors leak into supposedly-neutral tests

4. **Lack of Scientific Rigor**
   - Observer must be independent from observed system
   - Can't measure startup time from inside the startup process
   - Can't validate line length from within a potentially-broken line editor

**The Python Solution:**

1. **Complete Independence**
   ```python
   # Python spawns zsh and observes from outside
   shell = pexpect.spawn('zsh', env={'ZDOTDIR': test_dir})
   shell.sendline('echo $COLUMNS')
   # Python captures and analyzes - zsh bugs don't affect Python
   ```

2. **External Observation**
   - Python spawns shells as separate processes
   - Python controls PTY (pseudo-terminal) at OS level
   - Python measures timing without shell interference
   - Python parses output without shell interpretation

3. **Consistent Test Platform**
   - Same Python code tests zsh, bash, fish (future)
   - Python behavior independent of shell bugs
   - Reliable cross-shell comparison
   - Test infrastructure bugs are isolated from shell bugs

4. **Better Testing Capabilities**
   - Precise PTY control (terminal size, signals)
   - Accurate timing measurements
   - Raw byte-level output analysis
   - Pattern matching on escape sequences without shell escaping issues

**Concrete Example:**

```python
# WRONG: Shell testing itself
# test.sh - running IN zsh
COLUMNS_VALUE=$(echo $COLUMNS)  # If COLUMNS is wrong, test is wrong
if [[ $COLUMNS_VALUE -eq 80 ]]; then
    echo "PASS"  # But this might be wrong!
fi

# RIGHT: Python testing shell
# test.py - running OUTSIDE zsh
def test_columns():
    shell = pexpect.spawn('zsh', env={'ZDOTDIR': test_dir},
                          dimensions=(24, 80))  # Python sets terminal size
    shell.sendline('echo $COLUMNS')
    shell.expect(r'(\d+)')
    columns = int(shell.match.group(1))  # Python reads the value
    assert columns == 80  # Python validates
```

---

## Architecture Design

### Core Principles

1. **Isolation by ZDOTDIR**
   - Each test environment uses a unique ZDOTDIR
   - User's actual config (~/.zshrc, ~/.zshenv, etc.) remains untouched
   - Configs are copied to test ZDOTDIR for modification

2. **Testing Independence (Python-Based Testing)**
   - All test logic implemented in Python to avoid circular dependency
   - Python observes shells externally via PTY/pexpect
   - No shell-testing-shell to prevent test infrastructure bugs from affecting results
   - Ensures scientific rigor: observer separate from observed system

3. **Structured Output Capture**
   - Test scripts write structured output (JSON)
   - Terminal output captured via Python PTY/pexpect
   - Enables programmatic analysis and comparison

4. **Modular Test Suites**
   - Independent Python test modules for display, performance, compatibility
   - Each suite can run standalone or as part of full test run
   - Clear pass/fail criteria for each test

5. **Layered Analysis**
   - Individual test results
   - Cross-test pattern recognition
   - Holistic failure analysis
   - Prioritized recommendations

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Terminal-Guru Skill                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              SKILL.md (Orchestration Layer)            │ │
│  └────────────────────────────────────────────────────────┘ │
│                              │                               │
│  ┌───────────────────────────┴──────────────────────────┐   │
│  │         Terminal Test Runner (Python)                │   │
│  │  • Environment management                            │   │
│  │  • Test execution coordination                       │   │
│  │  • Output aggregation                                │   │
│  └──────────────┬────────────────────────┬──────────────┘   │
│                 │                        │                   │
│     ┌───────────┴──────────┐   ┌────────┴─────────┐        │
│     │  Environment Builder │   │  Output Analyzer │        │
│     │  (Python)            │   │  (Python)        │        │
│     │  • ZDOTDIR creation  │   │  • Result parsing│        │
│     │  • Config copying    │   │  • Comparison    │        │
│     │  • Isolation setup   │   │  • Patterns      │        │
│     └──────────────────────┘   └──────────────────┘        │
│                 │                                            │
│     ┌───────────┴───────────────────────────────┐           │
│     │      Test Suite Layer (All Python)       │           │
│     │  ┌─────────────────────────────────────┐  │           │
│     │  │  Display Tests (Python + pexpect)  │  │           │
│     │  │  • Line length validation          │  │           │
│     │  │  • Rendering correctness           │  │           │
│     │  │  • Plugin visual interactions      │  │           │
│     │  └─────────────────────────────────────┘  │           │
│     │  ┌─────────────────────────────────────┐  │           │
│     │  │  Performance Tests (Python + PTY)  │  │           │
│     │  │  • Startup time measurement        │  │           │
│     │  │  • Plugin load time tracking       │  │           │
│     │  │  • Responsiveness benchmarks       │  │           │
│     │  └─────────────────────────────────────┘  │           │
│     │  ┌─────────────────────────────────────┐  │           │
│     │  │  Plugin Tests (Python + pexpect)   │  │           │
│     │  │  • Plugin interaction validation   │  │           │
│     │  │  • Load order testing              │  │           │
│     │  │  • Conflict detection              │  │           │
│     │  └─────────────────────────────────────┘  │           │
│     └─────────────────────────────────────────────┘          │
│                              │                               │
│  ┌───────────────────────────┴──────────────────────────┐   │
│  │              Reference Documentation                 │   │
│  │  • Zsh Plugins Guide                                 │   │
│  │  • Testing Workflow                                  │   │
│  │  • Isolated Environments                             │   │
│  │  • Existing guides (terminfo, unicode, zsh config)   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Test Initialization**
   ```
   User invokes skill → SKILL.md loads → Test Runner initializes
   → Environment Builder creates ZDOTDIR → Copies user config
   ```

2. **Test Execution**
   ```
   Test Runner spawns zsh in isolated ZDOTDIR → Runs test suite scripts
   → Scripts execute tests and capture output → Results saved to JSON/logs
   ```

3. **Analysis**
   ```
   Output Analyzer loads test results → Parses structured data
   → Identifies failures → Detects patterns → Generates recommendations
   ```

4. **Iteration**
   ```
   Recommendations applied to test ZDOTDIR → Re-run tests
   → Compare new results vs baseline → Repeat until success
   ```

5. **Completion**
   ```
   Present working config to user → User applies to real environment
   → Test environment cleanup (or preservation for future use)
   ```

---

## Detailed Component Specifications

### 1. Terminal Test Runner (`scripts/terminal_test_runner.py`)

**Purpose:** Main orchestrator for test environment lifecycle and test execution.

**Responsibilities:**
- Create and manage isolated test environments
- Execute test suites in correct order
- Aggregate test outputs
- Coordinate with output analyzer
- Handle iterative test cycles

**Interface:**
```python
class TerminalTestRunner:
    """Main orchestrator for terminal testing workflow."""

    def __init__(self, user_config_path: str, test_name: str):
        """Initialize test runner with user's config and test identifier."""
        pass

    def create_environment(self) -> str:
        """Create isolated ZDOTDIR and return path."""
        pass

    def run_all_tests(self) -> dict:
        """Execute all test suites and return aggregated results."""
        pass

    def run_test_suite(self, suite_name: str) -> dict:
        """Execute specific test suite (display, performance, compatibility)."""
        pass

    def analyze_results(self, results: dict) -> dict:
        """Analyze test results and generate recommendations."""
        pass

    def apply_recommendations(self, recommendations: dict) -> None:
        """Apply config changes to test environment."""
        pass

    def compare_runs(self, baseline: dict, current: dict) -> dict:
        """Compare two test runs and identify improvements/regressions."""
        pass

    def cleanup(self, preserve: bool = False) -> None:
        """Clean up test environment unless preservation requested."""
        pass
```

**Key Features:**
- Python 3.7+ compatibility
- Robust error handling and logging
- Progress reporting during long operations
- JSON output for all results
- Support for multiple concurrent test environments

**Configuration:**
```yaml
# ~/.terminal-guru/test-runner-config.yaml
test_directory: ~/.terminal-guru/test-environments
preserve_environments: true
max_iterations: 10
default_test_suites:
  - display_consistency
  - performance
  - plugin_compatibility
output_format: json
verbose: true
```

### 2. Environment Builder (`scripts/environment_builder.py`)

**Purpose:** Create isolated zsh test environments using ZDOTDIR.

**Responsibilities:**
- Generate unique ZDOTDIR for each test
- Copy user's zsh configuration files
- Set up environment variables
- Create test environment metadata
- Ensure isolation from user's actual shell

**Interface:**
```python
import shutil
import os
from pathlib import Path
from typing import Dict

class EnvironmentBuilder:
    """Build isolated zsh test environments using ZDOTDIR."""

    def __init__(self, base_dir: str = "~/.terminal-guru/test-environments"):
        """Initialize environment builder with base directory."""
        self.base_dir = Path(base_dir).expanduser()

    def create_environment(self, test_name: str, source_config: str) -> str:
        """
        Create isolated ZDOTDIR test environment.

        Args:
            test_name: Name for this test environment
            source_config: Path to source zsh config directory (usually $HOME)

        Returns:
            Path to created ZDOTDIR
        """
        pass

    def copy_config_files(self, source: Path, dest: Path) -> None:
        """Copy zsh configuration files preserving permissions."""
        # Copy .zshenv, .zshrc, .zprofile, .zlogin
        pass

    def copy_plugins(self, source: Path, dest: Path) -> None:
        """Copy plugin directories (oh-my-zsh, zinit, etc.)."""
        pass

    def create_metadata(self, env_path: Path, metadata: Dict) -> None:
        """Create metadata.json for test environment."""
        pass

    def cleanup_environment(self, env_path: str) -> None:
        """Remove test environment directory."""
        pass
```

**Key Features:**
- Python's shutil for reliable file operations
- Preserve file permissions and symlinks
- Handle plugin manager directories (oh-my-zsh, zinit)
- Create isolated fpath entries
- Generate metadata.json for tracking
- Idempotent operation (can re-run safely)

**Directory Structure:**
```
~/.terminal-guru/test-environments/
└── test-20251120-143022/
    ├── zdotdir/
    │   ├── .zshenv
    │   ├── .zshrc
    │   ├── .zprofile
    │   ├── .zlogin
    │   └── functions/
    ├── plugins/
    │   ├── zsh-autosuggestions/
    │   └── zsh-syntax-highlighting/
    ├── logs/
    │   ├── display_test.log
    │   ├── performance_test.log
    │   └── compatibility_test.log
    ├── results/
    │   ├── display_results.json
    │   ├── performance_results.json
    │   └── compatibility_results.json
    └── metadata.json
```

### 3. Display Tests (`scripts/tests/display_tests.py`)

**Purpose:** Test terminal rendering, line length accuracy, and plugin visual interactions using Python to observe zsh externally.

**Test Categories:**

**A. Line Length Validation**
```python
import pexpect
import re

class DisplayTests:
    """Display consistency tests using pexpect to observe zsh."""

    def __init__(self, shell_binary: str, zdotdir: str):
        self.shell_binary = shell_binary
        self.zdotdir = zdotdir

    def test_line_length_accuracy(self) -> dict:
        """Test that COLUMNS matches actual display width."""
        # Spawn zsh with specific terminal size
        shell = pexpect.spawn(
            self.shell_binary,
            env={'ZDOTDIR': self.zdotdir},
            dimensions=(24, 80)  # 80 columns
        )

        # Send command to output COLUMNS worth of characters
        shell.sendline('echo -n $(printf "X%.0s" {1..$COLUMNS})')
        shell.expect('X+')

        # Python analyzes the output from outside
        output = shell.after.decode('utf-8', errors='replace')
        actual_length = len(output.strip())

        return {
            'test': 'line_length_accuracy',
            'expected': 80,
            'actual': actual_length,
            'status': 'pass' if actual_length == 80 else 'fail'
        }
```

**B. Rendering Correctness**
```python
def test_character_rendering(self) -> dict:
    """Test Unicode, emoji, and special character rendering."""
    test_chars = {
        'box_drawing': '┌─┐│└┘',
        'emoji': '😀🎉',
        'cjk': '中文',
        'combining': 'é' # e + combining acute
    }

    results = []
    shell = pexpect.spawn(
        self.shell_binary,
        env={'ZDOTDIR': self.zdotdir},
        encoding='utf-8'
    )

    for char_type, chars in test_chars.items():
        shell.sendline(f'echo "{chars}"')
        shell.expect(chars, timeout=2)
        # Python verifies output without shell interference
        results.append({
            'char_type': char_type,
            'status': 'pass'
        })

    return results

def test_color_codes(self) -> dict:
    """Test ANSI color rendering."""
    shell = pexpect.spawn(
        self.shell_binary,
        env={'ZDOTDIR': self.zdotdir, 'TERM': 'xterm-256color'}
    )

    # Test 256-color support
    shell.sendline('echo -e "\\e[38;5;196mRED\\e[0m"')
    shell.expect(r'\x1b\[38;5;196m')  # Python sees raw escape codes

    return {
        'test': 'color_codes',
        'ansi_support': True,
        '256_color_support': True,
        'status': 'pass'
    }
```

**C. Plugin Visual Interactions**
```python
def test_autosuggestions_display(self) -> dict:
    """Test zsh-autosuggestions rendering."""
    shell = pexpect.spawn(
        self.shell_binary,
        env={'ZDOTDIR': self.zdotdir},
        dimensions=(24, 80)
    )

    # Type partial command that should trigger suggestion
    shell.send('ec')  # Should suggest 'echo' if in history
    shell.expect(r'ec', timeout=1)

    # Capture full line including autosuggestion
    # Python can analyze the exact escape sequences
    output = shell.before + shell.after

    return {
        'test': 'autosuggestions_display',
        'suggestion_appeared': 'echo' in output,
        'status': 'pass'
    }

def test_syntax_highlighting(self) -> dict:
    """Test zsh-syntax-highlighting rendering."""
    shell = pexpect.spawn(
        self.shell_binary,
        env={'ZDOTDIR': self.zdotdir}
    )

    # Type command and check for highlighting escape codes
    shell.send('ls /tmp')
    # Python can verify ANSI codes were applied
    shell.expect(r'\x1b\[')  # Expect color escape sequence

    return {
        'test': 'syntax_highlighting',
        'highlighting_applied': True,
        'status': 'pass'
    }
```

**Output Format:**
```json
{
  "test_suite": "display_consistency",
  "timestamp": "2025-11-20T14:30:22Z",
  "environment": "test-20251120-143022",
  "results": {
    "line_length": {
      "status": "pass",
      "tests_run": 12,
      "tests_passed": 12,
      "tests_failed": 0,
      "details": []
    },
    "rendering": {
      "status": "fail",
      "tests_run": 8,
      "tests_passed": 6,
      "tests_failed": 2,
      "details": [
        {
          "test": "emoji_rendering",
          "status": "fail",
          "expected": "2 columns per emoji",
          "actual": "1 column per emoji",
          "error": "wcwidth mismatch"
        }
      ]
    },
    "plugin_visual": {
      "status": "pass",
      "tests_run": 15,
      "tests_passed": 15,
      "tests_failed": 0,
      "details": []
    }
  },
  "summary": {
    "total_tests": 35,
    "passed": 33,
    "failed": 2,
    "status": "fail"
  }
}
```

### 4. Performance Tests (`scripts/tests/performance_tests.py`)

**Purpose:** Measure and benchmark zsh startup time, plugin load times, and responsiveness using Python for precise external timing.

**Test Categories:**

**A. Startup Time Measurement**
```python
import time
import subprocess
import re
from typing import Dict

class PerformanceTests:
    """Performance tests using Python for precise timing."""

    def __init__(self, shell_binary: str, zdotdir: str):
        self.shell_binary = shell_binary
        self.zdotdir = zdotdir

    def measure_startup_time(self) -> Dict:
        """Measure shell startup time from outside (no shell measuring itself)."""
        start = time.perf_counter()

        # Python times the shell startup externally
        result = subprocess.run(
            [self.shell_binary, '-i', '-c', 'exit'],
            env={'ZDOTDIR': self.zdotdir},
            capture_output=True,
            timeout=5
        )

        end = time.perf_counter()
        startup_ms = (end - start) * 1000

        return {
            'test': 'startup_time',
            'time_ms': round(startup_ms, 2),
            'rating': self._rate_startup_time(startup_ms),
            'status': 'pass' if startup_ms < 500 else 'warn'
        }

    def profile_with_zprof(self) -> Dict:
        """Use zsh/zprof but parse output from Python."""
        # Python spawns shell with profiling enabled
        result = subprocess.run(
            [self.shell_binary, '-i', '-c',
             'zmodload zsh/zprof; source $ZDOTDIR/.zshrc; zprof'],
            env={'ZDOTDIR': self.zdotdir},
            capture_output=True,
            text=True,
            timeout=5
        )

        # Python parses zprof output
        functions = self._parse_zprof_output(result.stdout)

        return {
            'test': 'zprof_profile',
            'slowest_functions': functions[:10],
            'status': 'pass'
        }

    def _parse_zprof_output(self, output: str) -> list:
        """Parse zprof output to extract function timings."""
        # Python does the parsing, not shell
        pattern = r'(\d+\.\d+)\s+\d+\.\d+\%\s+\d+\.\d+\s+\d+\.\d+\%\s+(\d+)\s+(.+)'
        matches = re.findall(pattern, output)

        return [
            {
                'name': match[2].strip(),
                'time_ms': float(match[0]),
                'calls': int(match[1])
            }
            for match in matches
        ]
```

**B. Plugin Load Time Tracking**
```python
def measure_plugin_load_times(self) -> Dict:
    """Measure individual plugin load times."""
    # Python injects timing code and parses results
    timing_script = '''
    typeset -A plugin_times
    for plugin in $plugins; do
        start=$(date +%s%N)
        # Plugin loading happens here
        end=$(date +%s%N)
        plugin_times[$plugin]=$(( (end - start) / 1000000 ))
    done
    echo ${(kv)plugin_times[@]}
    '''

    result = subprocess.run(
        [self.shell_binary, '-c', timing_script],
        env={'ZDOTDIR': self.zdotdir},
        capture_output=True,
        text=True
    )

    # Python parses the output
    plugins = self._parse_plugin_times(result.stdout)

    return {
        'test': 'plugin_load_times',
        'plugins': plugins,
        'total_ms': sum(p['time_ms'] for p in plugins),
        'status': 'pass'
    }

def identify_slow_plugins(self, plugins: list) -> list:
    """Identify plugins taking > 50ms (Python analysis)."""
    return [
        p for p in plugins
        if p['time_ms'] > 50
    ]
```

**C. Responsiveness Benchmarks**
```python
def test_command_execution_latency(self) -> Dict:
    """Test command execution latency using Python timing."""
    import pexpect

    shell = pexpect.spawn(
        self.shell_binary,
        env={'ZDOTDIR': self.zdotdir}
    )
    shell.expect(r'\$ ')  # Wait for prompt

    # Python times the command execution
    start = time.perf_counter()
    shell.sendline('true')
    shell.expect(r'\$ ')
    end = time.perf_counter()

    latency_ms = (end - start) * 1000

    return {
        'test': 'command_latency',
        'time_ms': round(latency_ms, 2),
        'rating': self._rate_responsiveness(latency_ms),
        'status': 'pass' if latency_ms < 50 else 'warn'
    }
```

**Performance Targets:**
```yaml
startup_time:
  excellent: < 100ms
  good: < 250ms
  acceptable: < 500ms
  poor: > 500ms

plugin_load_time:
  per_plugin:
    excellent: < 10ms
    good: < 25ms
    acceptable: < 50ms
    poor: > 50ms
  total:
    excellent: < 100ms
    good: < 200ms
    acceptable: < 400ms
    poor: > 400ms

responsiveness:
  command_latency:
    excellent: < 10ms
    good: < 25ms
    acceptable: < 50ms
    poor: > 50ms
  completion_time:
    excellent: < 50ms
    good: < 100ms
    acceptable: < 200ms
    poor: > 200ms
```

**Output Format:**
```json
{
  "test_suite": "performance",
  "timestamp": "2025-11-20T14:31:15Z",
  "environment": "test-20251120-143022",
  "results": {
    "startup": {
      "total_time_ms": 245,
      "rating": "good",
      "breakdown": {
        ".zshenv": 12,
        ".zshrc": 198,
        ".zlogin": 35
      },
      "slowest_functions": [
        {"name": "compinit", "time_ms": 85, "calls": 1},
        {"name": "oh-my-zsh-init", "time_ms": 67, "calls": 1}
      ]
    },
    "plugins": {
      "total_time_ms": 145,
      "rating": "good",
      "individual": [
        {"name": "zsh-autosuggestions", "time_ms": 23, "rating": "good"},
        {"name": "zsh-syntax-highlighting", "time_ms": 89, "rating": "poor"},
        {"name": "powerlevel10k", "time_ms": 33, "rating": "good"}
      ],
      "recommendations": [
        "Consider deferring zsh-syntax-highlighting load"
      ]
    },
    "responsiveness": {
      "command_latency_ms": 8,
      "completion_time_ms": 78,
      "typing_latency_ms": 12,
      "ratings": {
        "command": "excellent",
        "completion": "good",
        "typing": "excellent"
      }
    }
  }
}
```

### 5. Plugin Tests (`scripts/tests/plugin_tests.py`)

**Purpose:** Test plugin interactions, detect conflicts, validate load order using Python to observe zsh plugin behavior externally.

**Test Categories:**

**A. Plugin Interaction Validation**
```python
import pexpect
import subprocess
from typing import List, Dict

class PluginTests:
    """Plugin compatibility tests using Python to observe plugin behavior."""

    def __init__(self, shell_binary: str, zdotdir: str):
        self.shell_binary = shell_binary
        self.zdotdir = zdotdir

    def test_plugin_pairs(self, plugins: List[str]) -> Dict:
        """Test all pairs of plugins for conflicts (Python orchestration)."""
        conflicts = []

        for i, plugin1 in enumerate(plugins):
            for plugin2 in plugins[i+1:]:
                # Python spawns shell with both plugins
                result = self._test_plugin_pair(plugin1, plugin2)
                if result['has_conflict']:
                    conflicts.append(result)

        return {
            'test': 'plugin_pairs',
            'pairs_tested': len(plugins) * (len(plugins) - 1) // 2,
            'conflicts_found': len(conflicts),
            'conflicts': conflicts,
            'status': 'pass' if len(conflicts) == 0 else 'warn'
        }

    def test_plugin_load_order(self) -> Dict:
        """Validate plugin load order (Python reads and validates)."""
        # Python reads the zshrc and extracts plugin load order
        zshrc_path = f"{self.zdotdir}/.zshrc"
        with open(zshrc_path, 'r') as f:
            content = f.read()

        current_order = self._extract_plugin_order(content)
        recommended_order = self._get_recommended_order(current_order)

        return {
            'test': 'plugin_load_order',
            'current_order': current_order,
            'recommended_order': recommended_order,
            'order_matches': current_order == recommended_order,
            'status': 'pass' if current_order == recommended_order else 'warn'
        }
```

**B. Conflict Detection**
```python
def detect_key_binding_conflicts(self) -> Dict:
    """Detect key binding conflicts using Python to parse bindkey output."""
    # Python spawns shell and gets bindkey output
    result = subprocess.run(
        [self.shell_binary, '-i', '-c', 'bindkey'],
        env={'ZDOTDIR': self.zdotdir},
        capture_output=True,
        text=True
    )

    # Python parses the bindings
    bindings = self._parse_bindkey_output(result.stdout)
    duplicates = self._find_duplicate_bindings(bindings)

    return {
        'test': 'key_binding_conflicts',
        'total_bindings': len(bindings),
        'conflicts': duplicates,
        'status': 'pass' if len(duplicates) == 0 else 'warn'
    }

def detect_function_conflicts(self) -> Dict:
    """Detect function name collisions using Python to parse function list."""
    result = subprocess.run(
        [self.shell_binary, '-c', 'functions'],
        env={'ZDOTDIR': self.zdotdir},
        capture_output=True,
        text=True
    )

    # Python analyzes function names for conflicts
    functions = result.stdout.split('\n')
    conflicts = self._analyze_function_names(functions)

    return {
        'test': 'function_conflicts',
        'total_functions': len(functions),
        'conflicts': conflicts,
        'status': 'pass' if len(conflicts) == 0 else 'warn'
    }

def detect_variable_conflicts(self) -> Dict:
    """Detect environment variable conflicts."""
    result = subprocess.run(
        [self.shell_binary, '-c', 'env'],
        env={'ZDOTDIR': self.zdotdir},
        capture_output=True,
        text=True
    )

    # Python parses environment variables
    variables = self._parse_env_output(result.stdout)
    conflicts = self._find_variable_conflicts(variables)

    return {
        'test': 'variable_conflicts',
        'conflicts': conflicts,
        'status': 'pass' if len(conflicts) == 0 else 'warn'
    }
```

**C. Plugin Manager Validation**
```python
def test_plugin_manager_config(self) -> Dict:
    """Validate plugin manager configuration."""
    # Python reads config files directly
    config_path = f"{self.zdotdir}/.zshrc"

    with open(config_path, 'r') as f:
        content = f.read()

    # Python detects which plugin manager is used
    manager = self._detect_plugin_manager(content)

    # Python validates configuration
    validation = self._validate_manager_config(manager, content)

    return {
        'test': 'plugin_manager_config',
        'manager': manager,
        'valid': validation['is_valid'],
        'issues': validation.get('issues', []),
        'status': 'pass' if validation['is_valid'] else 'fail'
    }
```

**Output Format:**
```json
{
  "test_suite": "plugin_compatibility",
  "timestamp": "2025-11-20T14:32:08Z",
  "environment": "test-20251120-143022",
  "results": {
    "interactions": {
      "status": "pass",
      "pairs_tested": 6,
      "conflicts_found": 0
    },
    "load_order": {
      "status": "pass",
      "current_order": [
        "zsh-syntax-highlighting",
        "zsh-autosuggestions",
        "powerlevel10k"
      ],
      "recommended_order": [
        "powerlevel10k",
        "zsh-syntax-highlighting",
        "zsh-autosuggestions"
      ],
      "order_matches": false,
      "issues": [
        "Syntax highlighting should load before autosuggestions"
      ]
    },
    "conflicts": {
      "key_bindings": {
        "status": "warn",
        "conflicts": [
          {
            "key": "^[[A",
            "plugins": ["history-search", "autosuggestions"],
            "resolution": "history-search binding takes precedence"
          }
        ]
      },
      "functions": {
        "status": "pass",
        "conflicts": []
      },
      "variables": {
        "status": "pass",
        "conflicts": []
      }
    }
  }
}
```

### 6. Output Analyzer (`scripts/output_analyzer.py`)

**Purpose:** Parse test results, identify patterns, compare iterations, generate recommendations.

**Interface:**
```python
class OutputAnalyzer:
    """Analyze test outputs and generate recommendations."""

    def __init__(self, test_results: dict):
        """Initialize with test results dictionary."""
        pass

    def parse_results(self) -> dict:
        """Parse structured test output into analysis-ready format."""
        pass

    def identify_failures(self) -> list:
        """Extract all test failures across suites."""
        pass

    def detect_patterns(self, failures: list) -> dict:
        """Identify common patterns in failures."""
        pass

    def compare_iterations(self, baseline: dict, current: dict) -> dict:
        """Compare two test runs."""
        pass

    def generate_recommendations(self, patterns: dict) -> list:
        """Generate prioritized config change recommendations."""
        pass

    def format_report(self, recommendations: list) -> str:
        """Format human-readable report."""
        pass
```

**Analysis Patterns:**

**Display Issues:**
- Emoji rendering → Check locale, wcwidth, terminal capabilities
- Line length mismatch → Check ZLE_RPROMPT_INDENT, plugin conflicts
- Color issues → Check TERM value, terminfo, 256-color support

**Performance Issues:**
- Slow startup → Identify slow functions, suggest deferral
- Slow plugins → Recommend lazy loading, alternatives
- Slow completion → Check compinit usage, cache configuration

**Plugin Conflicts:**
- Load order → Reorder plugins per best practices
- Key binding conflicts → Suggest bindkey customization
- Function conflicts → Suggest plugin removal or fork

**Recommendation Format:**
```json
{
  "recommendations": [
    {
      "priority": "high",
      "category": "display",
      "issue": "Emoji rendering width mismatch",
      "root_cause": "Terminal reports wcwidth=1 for emoji, zsh expects wcwidth=2",
      "fix": {
        "type": "environment_variable",
        "changes": {
          "LC_ALL": "en_US.UTF-8",
          "LANG": "en_US.UTF-8"
        },
        "file": ".zshenv",
        "confidence": "high"
      },
      "testing": "Re-run display_consistency_tests.sh emoji_rendering test"
    },
    {
      "priority": "medium",
      "category": "performance",
      "issue": "zsh-syntax-highlighting loads in 89ms",
      "root_cause": "Plugin loads synchronously during startup",
      "fix": {
        "type": "plugin_config",
        "changes": {
          "load_method": "defer",
          "defer_time": "0"
        },
        "file": ".zshrc",
        "code_snippet": "zinit ice wait'0'; zinit load zsh-users/zsh-syntax-highlighting",
        "confidence": "medium"
      },
      "expected_improvement": "Reduce startup time by ~70ms",
      "testing": "Re-run performance profiler"
    }
  ]
}
```

---

## Testing Framework Design

### Test Environment Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    Test Lifecycle                            │
└─────────────────────────────────────────────────────────────┘

1. INITIALIZE
   ├── Create unique test directory
   ├── Generate ZDOTDIR structure
   ├── Copy user's zsh config
   ├── Copy plugin directories
   └── Create metadata.json

2. BASELINE
   ├── Run all test suites (no modifications)
   ├── Capture baseline results
   ├── Identify initial failures
   └── Store baseline for comparison

3. ANALYZE
   ├── Parse test results
   ├── Identify failure patterns
   ├── Detect root causes
   └── Generate recommendations

4. ITERATE
   ├── Apply recommendation to config
   ├── Re-run affected test suites
   ├── Compare results vs baseline
   ├── If failures remain → loop to ANALYZE
   └── If tests pass → proceed to FINALIZE

5. FINALIZE
   ├── Present working configuration
   ├── Show diff from original config
   ├── Generate summary report
   └── Optionally preserve test environment

6. CLEANUP (optional)
   └── Remove test directory (if not preserved)
```

### Test Execution Model

**Sequential Execution:**
```
Display Tests → Performance Tests → Compatibility Tests
```

**Rationale:**
- Display tests are fastest, catch obvious issues early
- Performance tests require clean state
- Compatibility tests may modify bindings/functions

**Test Independence:**
- Each test suite is self-contained
- Tests do not modify the environment permanently
- Tests can be run individually for focused debugging

### Output Capture Strategy

**Avoiding tmux Complexity:**
Instead of tmux (which adds terminal emulation layers), use:

1. **PTY (Pseudo-Terminal) Approach:**
   ```python
   import pty
   import os

   def run_in_pty(command):
       """Run command in PTY and capture output."""
       master, slave = pty.openpty()
       pid = os.fork()
       if pid == 0:  # Child
           os.close(master)
           os.dup2(slave, 0)
           os.dup2(slave, 1)
           os.dup2(slave, 2)
           os.execvp(command[0], command)
       else:  # Parent
           os.close(slave)
           output = b""
           while True:
               try:
                   data = os.read(master, 1024)
                   if not data:
                       break
                   output += data
               except OSError:
                   break
           os.waitpid(pid, 0)
           os.close(master)
           return output.decode('utf-8', errors='replace')
   ```

2. **Script Command Approach:**
   ```bash
   # Using Unix 'script' command to capture terminal session
   script -q -c "zsh -c 'source $ZDOTDIR/.zshrc; run_tests'" /tmp/test-output.log
   ```

3. **Expect/Pexpect for Interactive Testing:**
   ```python
   import pexpect

   child = pexpect.spawn('zsh', env={'ZDOTDIR': test_zdotdir})
   child.expect('$ ')
   child.sendline('echo $ZSH_VERSION')
   output = child.before
   ```

### Comparison Framework

**Iteration Comparison:**
```python
def compare_test_runs(baseline, current):
    """Compare two test runs."""
    comparison = {
        'regressions': [],
        'improvements': [],
        'unchanged': []
    }

    for suite in ['display', 'performance', 'compatibility']:
        baseline_status = baseline[suite]['status']
        current_status = current[suite]['status']

        if baseline_status == 'fail' and current_status == 'pass':
            comparison['improvements'].append({
                'suite': suite,
                'change': 'fixed',
                'details': get_fixed_tests(baseline[suite], current[suite])
            })
        elif baseline_status == 'pass' and current_status == 'fail':
            comparison['regressions'].append({
                'suite': suite,
                'change': 'broke',
                'details': get_broken_tests(baseline[suite], current[suite])
            })

    return comparison
```

---

## Workflow Details

### Interactive Testing Workflow

**User Invokes Skill:**
```
User: "I'm having terminal display issues with zsh-autosuggestions
       causing line wrapping problems. Can you help diagnose and fix?"

Claude (using terminal-guru skill):
1. "I'll create an isolated test environment to diagnose this safely."
2. Calls: terminal_test_runner.py --create-env --name "autosuggestion-fix"
3. "Running comprehensive tests on your current config..."
4. Calls: terminal_test_runner.py --run-all --env "autosuggestion-fix"
5. Analyzes results, identifies line length mismatch in display tests
6. "I found the issue: ZLE_RPROMPT_INDENT is not set, causing
    autosuggestions to miscalculate line length."
7. Applies fix to test environment .zshrc
8. Re-runs display tests
9. "Tests now pass. Here's the diff to apply to your real .zshrc:"
   [Shows diff]
10. "Would you like me to apply this change?"
```

### Iterative Refinement Workflow

```
Initial State:
- 5 display test failures
- 2 performance issues
- 1 plugin conflict

Iteration 1:
- Apply fix for display failures
- Re-run all tests
- Result: 3 display failures fixed, 2 remain
- New recommendation generated

Iteration 2:
- Apply fix for remaining display issues
- Re-run display tests
- Result: All display tests pass
- Move to performance issues

Iteration 3:
- Apply performance recommendations
- Re-run performance tests
- Result: 1 issue fixed, 1 remains

... continue until all tests pass or max iterations reached
```

### Comparison Across Configurations

**Use Case:** User wants to compare oh-my-zsh vs zinit

```bash
# Test current config (oh-my-zsh)
terminal_test_runner.py --create-env --name "omz-baseline"
terminal_test_runner.py --run-all --env "omz-baseline"

# Modify to use zinit
terminal_test_runner.py --create-env --name "zinit-test" --clone-from "omz-baseline"
# Manually convert to zinit or use script
terminal_test_runner.py --run-all --env "zinit-test"

# Compare results
terminal_test_runner.py --compare "omz-baseline" "zinit-test"

Output:
┌────────────────────────────────────────────────────────┐
│              Configuration Comparison                  │
├────────────────────────────────────────────────────────┤
│                oh-my-zsh    │    zinit                 │
├────────────────────────────────────────────────────────┤
│ Startup Time   245ms        │    178ms    (-67ms) ✓    │
│ Plugin Load    145ms        │     89ms    (-56ms) ✓    │
│ Display Tests  Pass          │    Pass              ─   │
│ Compat Tests   1 Warning     │    Pass              ✓   │
├────────────────────────────────────────────────────────┤
│ Recommendation: Switch to zinit for 27% faster startup │
└────────────────────────────────────────────────────────┘
```

---

## File Structure

### Updated Directory Layout

```
skills/terminal-guru/
├── SKILL.md                               # Updated with new workflows
├── IMPROVEMENT_PLAN.md                    # This document
│
├── scripts/
│   ├── terminal_diagnostics.py            # Enhanced: Add JSON output mode
│   ├── terminal_test_runner.py            # NEW: Main orchestrator
│   ├── environment_builder.py             # NEW: ZDOTDIR isolation (Python)
│   ├── tests/                             # NEW: Python test modules
│   │   ├── __init__.py
│   │   ├── base.py                        # Shared test utilities
│   │   ├── display_tests.py               # Display testing (Python + pexpect)
│   │   ├── performance_tests.py           # Performance benchmarking (Python)
│   │   ├── plugin_tests.py                # Plugin testing (Python + pexpect)
│   │   └── fixtures/                      # Test data and expected outputs
│   ├── analysis/                          # NEW: Analysis modules
│   │   ├── __init__.py
│   │   ├── output_analyzer.py             # Result analysis
│   │   └── recommendation_engine.py       # Generate fixes
│   └── install_autoload.sh                # Existing: Unchanged
│
├── references/
│   ├── terminfo_guide.md                  # Existing: Unchanged
│   ├── unicode_troubleshooting.md         # Existing: Unchanged
│   ├── zsh_configuration.md               # Existing: Unchanged
│   ├── zsh_plugins_guide.md               # NEW: Plugin documentation
│   ├── testing_workflow.md                # NEW: Testing methodology
│   └── isolated_environments.md           # NEW: ZDOTDIR isolation guide
│
└── examples/
    ├── test_environment_example/          # NEW: Example test output
    ├── fixing_display_issues.md           # NEW: Walkthrough example
    ├── optimizing_performance.md          # NEW: Performance tuning guide
    └── plugin_migration_guide.md          # NEW: Migrating plugin managers
```

### New Reference Documents

**1. `references/zsh_plugins_guide.md`**

Content outline:
- Popular plugin managers (oh-my-zsh, zinit, antigen, zplug)
- Plugin manager comparison and migration
- Common plugins:
  - zsh-autosuggestions (configuration, troubleshooting)
  - zsh-syntax-highlighting (performance, visual issues)
  - powerlevel10k (prompt configuration)
  - fzf-tab (fuzzy completion)
- Plugin best practices:
  - Load order recommendations
  - Lazy loading strategies
  - Conflict resolution
- Display consistency:
  - Line length calculations
  - ZLE widget interactions
  - Color and highlighting conflicts
- Performance optimization:
  - Profiling plugin load times
  - Deferred loading patterns
  - Plugin alternatives

**2. `references/testing_workflow.md`**

Content outline:
- Overview of testing framework
- Test environment lifecycle
- Running individual test suites
- Interpreting test results
- Iterative refinement process
- Comparison workflows
- Troubleshooting test failures
- Extending the test framework
- Best practices for terminal testing

**3. `references/isolated_environments.md`**

Content outline:
- ZDOTDIR mechanism explained
- Creating isolated zsh instances
- Environment variable isolation
- Plugin directory management
- Testing without side effects
- Preserving test environments
- Comparing configurations
- Advanced isolation techniques
- Debugging isolated environments

---

## Implementation Roadmap

### Phase 1: Foundation (Isolated Environments + Output Capture)

**Goals:**
- Create isolated test environments using ZDOTDIR (Python)
- Implement basic output capture via PTY/pexpect
- Establish test environment lifecycle

**Deliverables:**
1. `scripts/environment_builder.py` - Full Python implementation
2. `scripts/terminal_test_runner.py` - Basic scaffolding with environment management
3. `references/isolated_environments.md` - Complete documentation
4. Enhanced `scripts/terminal_diagnostics.py` with JSON output mode
5. `scripts/tests/base.py` - Shared test utilities and PTY helpers

**Success Criteria:**
- Can create isolated ZDOTDIR test environments using Python
- User's actual config remains untouched
- Test environments can be created, used, and cleaned up
- Basic Python-based test execution works
- PTY/pexpect infrastructure established

**Estimated Effort:** 2-3 days

---

### Phase 2: Test Suites (Display, Performance, Compatibility)

**Goals:**
- Implement comprehensive Python test suites
- External observation of shells via pexpect/PTY
- Structured JSON output for each test category
- Clear pass/fail criteria

**Deliverables:**
1. `scripts/tests/display_tests.py` - Full Python test suite with pexpect
2. `scripts/tests/performance_tests.py` - Python-based profiling with external timing
3. `scripts/tests/plugin_tests.py` - Conflict detection via Python
4. Test output JSON schemas defined
5. `scripts/tests/fixtures/` - Test data and expected outputs

**Success Criteria:**
- All three test suites execute successfully
- Python observes shells externally (no shell-testing-shell)
- Tests produce structured JSON output
- Tests identify real issues in zsh configurations
- Tests are reliable and repeatable
- No circular dependencies between test infrastructure and shell under test

**Estimated Effort:** 4-5 days

---

### Phase 3: Analysis Engine (Comparison & Recommendations)

**Goals:**
- Parse and analyze test results
- Compare iterations
- Generate intelligent recommendations

**Deliverables:**
1. `scripts/analysis/output_analyzer.py` - Full implementation
2. `scripts/analysis/recommendation_engine.py` - Pattern matching and fix generation
3. Comparison framework
4. Integration with test runner

**Success Criteria:**
- Can identify patterns in test failures
- Generates actionable recommendations
- Compares test runs accurately
- Recommendations improve test results

**Estimated Effort:** 3-4 days

---

### Phase 4: Documentation (SKILL.md + References + Examples)

**Goals:**
- Update SKILL.md with new workflows
- Create comprehensive reference guides
- Provide real-world examples

**Deliverables:**
1. Updated `SKILL.md` with testing workflows
2. `references/zsh_plugins_guide.md` - Complete
3. `references/testing_workflow.md` - Complete
4. Example walkthroughs in `examples/`

**Success Criteria:**
- SKILL.md clearly explains new capabilities
- References provide deep technical detail
- Examples demonstrate real use cases
- Documentation follows progressive disclosure model

**Estimated Effort:** 2-3 days

---

### Phase 5: Integration & Polish

**Goals:**
- End-to-end workflow testing
- Edge case handling
- Performance optimization
- User experience refinement

**Deliverables:**
1. Comprehensive integration testing
2. Error handling improvements
3. Performance optimizations
4. User feedback incorporation

**Success Criteria:**
- Complete workflow works smoothly from start to finish
- Handles edge cases gracefully
- Performance is acceptable for typical configs
- Ready for real-world use

**Estimated Effort:** 2-3 days

---

**Total Estimated Effort:** 13-18 days

---

## Examples and Use Cases

### Example 1: Fixing Auto-Suggestion Display Issues

**Problem:**
User reports that zsh-autosuggestions causes text to wrap incorrectly, making it hard to see what they're typing on long command lines.

**Workflow:**
```bash
# User invokes terminal-guru skill
# Claude responds:

"I'll create a test environment to diagnose your auto-suggestion display issues."

# Creates isolated environment
terminal_test_runner.py --create-env --name "autosuggestion-fix"

"Running display consistency tests..."

# Runs display tests, detects line length mismatch
# Analysis shows: ZLE_RPROMPT_INDENT not set

"I found the issue. Your terminal doesn't have ZLE_RPROMPT_INDENT set,
which causes zsh to miscalculate line lengths when auto-suggestions appear.

I'll apply a fix to the test environment and verify it works."

# Applies fix: export ZLE_RPROMPT_INDENT=0 to .zshrc
# Re-runs display tests
# Tests now pass

"Tests pass! Here's the fix:

Add to ~/.zshrc:
  export ZLE_RPROMPT_INDENT=0

This tells zsh not to reserve space for the right prompt, fixing the
line length calculation for auto-suggestions.

Would you like me to show you how to apply this change?"
```

**Test Results:**
```
Before fix:
  ✗ line_length_with_autosuggestions - Expected 80 cols, got 78
  ✗ long_line_wrapping - Text wraps at col 78 instead of 80

After fix:
  ✓ line_length_with_autosuggestions - Correct 80 cols
  ✓ long_line_wrapping - Text wraps correctly at col 80
```

---

### Example 2: Optimizing Startup Performance

**Problem:**
User's zsh takes 800ms to start, which feels sluggish.

**Workflow:**
```bash
"Your zsh startup time is 800ms. Let me profile your configuration to
identify bottlenecks."

# Creates test environment
terminal_test_runner.py --create-env --name "performance-optimization"

# Runs performance profiler
# Results show:
#   - compinit: 320ms
#   - zsh-syntax-highlighting: 215ms
#   - oh-my-zsh plugins: 180ms
#   - Remaining: 85ms

"I found three main bottlenecks:

1. compinit (320ms) - Running on every shell startup
   Fix: Add completion cache and check daily

2. zsh-syntax-highlighting (215ms) - Loading synchronously
   Fix: Defer loading using zinit wait'0'

3. oh-my-zsh plugins (180ms) - Loading many unused plugins
   Fix: Disable unused plugins (14 detected)

I'll apply these optimizations and measure the improvement."

# Applies fixes iteratively
# After iteration 1 (compinit cache): 480ms (40% improvement)
# After iteration 2 (defer syntax-highlighting): 265ms (67% improvement)
# After iteration 3 (disable unused plugins): 175ms (78% improvement)

"Excellent! I've reduced your startup time from 800ms to 175ms (78% faster).

Changes made:
1. Added compinit cache with daily refresh
2. Deferred zsh-syntax-highlighting load
3. Disabled 14 unused oh-my-zsh plugins

Here's the diff to apply to your ~/.zshrc:"
```

**Performance Results:**
```
Original Configuration:
  Startup time: 800ms
  compinit: 320ms
  Plugins: 395ms
  Other: 85ms
  Rating: POOR

Optimized Configuration:
  Startup time: 175ms (-78%)
  compinit: 45ms (cached)
  Plugins: 50ms (deferred + reduced)
  Other: 80ms
  Rating: EXCELLENT
```

---

### Example 3: Resolving Plugin Conflicts

**Problem:**
User has key binding conflicts between history-search and autosuggestions.

**Workflow:**
```bash
"I'll test your plugin configuration for conflicts."

# Runs compatibility tests
# Detects:
#   - Key binding conflict: ^[[A bound by both plugins
#   - Load order issue: syntax-highlighting loaded after autosuggestions
#   - Function collision: _zsh_highlight_widget redefined

"I found three plugin compatibility issues:

1. Key Binding Conflict
   - Both history-search and autosuggestions bind Up Arrow (^[[A)
   - Currently: history-search wins
   - Recommendation: Explicitly bind keys in .zshrc

2. Load Order Issue
   - zsh-syntax-highlighting should load before autosuggestions
   - Current order causes highlighting glitches

3. Function Collision
   - Multiple plugins redefine _zsh_highlight_widget
   - May cause unexpected behavior

I'll fix these issues in the test environment."

# Applies fixes:
#   1. Adds explicit key bindings
#   2. Reorders plugin loading
#   3. Namespaces conflicting functions

# Re-runs compatibility tests
# All tests pass

"All compatibility issues resolved. Your plugins now work together correctly."
```

**Compatibility Results:**
```
Before fixes:
  ✗ Key binding conflicts: 2 found
  ✗ Load order issues: 1 found
  ✗ Function conflicts: 1 found

After fixes:
  ✓ Key binding conflicts: 0
  ✓ Load order: Correct
  ✓ Function conflicts: 0
```

---

## Success Criteria

### Functional Requirements

**Must Have:**
- [x] Create isolated test environments using ZDOTDIR
- [x] Run display consistency tests
- [x] Run performance profiling
- [x] Run plugin compatibility tests
- [x] Capture structured test output (JSON)
- [x] Analyze test results
- [x] Generate recommendations
- [x] Compare test iterations
- [x] Preserve test environments for inspection
- [x] Present diffs of configuration changes

**Should Have:**
- [ ] Interactive prompts for applying fixes
- [ ] Support for multiple plugin managers
- [ ] Visual diff of before/after performance
- [ ] Test result history tracking
- [ ] Rollback to previous test state

**Could Have:**
- [ ] Export test results as HTML report
- [ ] Integration with shell config version control
- [ ] Automated regression detection
- [ ] Community test suite contributions

### Quality Requirements

**Reliability:**
- Tests produce consistent results on repeated runs
- No false positives in test failures
- Isolated environments truly don't affect user's shell
- Error handling for edge cases

**Performance:**
- Test suite completes in < 30 seconds for typical config
- Analysis completes in < 5 seconds
- Minimal overhead from isolation mechanism

**Usability:**
- Clear error messages and actionable recommendations
- Progress indication during long operations
- Helpful documentation and examples
- Intuitive workflow for common tasks

**Maintainability:**
- Modular design allows easy extension
- Well-documented code
- Comprehensive test coverage
- Clear separation of concerns

---

## Future Enhancements (Post-v2.0)

### Multi-Shell Support
- Extend framework to support bash
- Extend framework to support fish
- Generic test suite adaptable to different shells

### Advanced Testing
- Interactive widget testing
- Terminal emulator compatibility matrix
- Stress testing (large history, many files, etc.)
- Network latency simulation for remote shells

### CI/CD Integration
- Exit codes for automated testing
- Machine-readable output formats
- Integration with GitHub Actions / GitLab CI
- Pre-commit hooks for shell config validation

### Community Features
- Shareable test configurations
- Community test suite repository
- Plugin compatibility matrix database
- Best practice templates

### Enhanced Analysis
- Machine learning for pattern recognition
- Historical trend analysis
- Predictive performance modeling
- Automated A/B testing of configurations

---

## Appendix

### A. ZDOTDIR Isolation Mechanism

**How ZDOTDIR Works:**

Zsh uses the `ZDOTDIR` environment variable to determine where to look for startup files. By setting a custom ZDOTDIR, we can create completely isolated zsh instances.

**Standard zsh startup:**
```bash
# Looks in $HOME for:
~/.zshenv
~/.zprofile
~/.zshrc
~/.zlogin
```

**Isolated zsh startup:**
```bash
# Set custom ZDOTDIR
export ZDOTDIR=/path/to/test/environment

# Zsh now looks in ZDOTDIR:
/path/to/test/environment/.zshenv
/path/to/test/environment/.zprofile
/path/to/test/environment/.zshrc
/path/to/test/environment/.zlogin
```

**Complete Isolation:**
```bash
#!/bin/bash
# Create isolated zsh instance

TEST_DIR="/tmp/zsh-test-$$"
mkdir -p "$TEST_DIR"

# Copy user's config
cp ~/.zshenv "$TEST_DIR/.zshenv"
cp ~/.zshrc "$TEST_DIR/.zshrc"

# Launch isolated zsh
ZDOTDIR="$TEST_DIR" zsh

# Changes made in this shell only affect TEST_DIR
# User's real ~/.zshrc is untouched
```

### B. PTY vs Script vs Expect

**Comparison of output capture methods:**

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| PTY | Full terminal emulation, accurate | Complex, platform-specific | Interactive testing |
| Script | Simple, widely available | Limited control, format varies | Basic capture |
| Expect/Pexpect | Interactive automation, powerful | Complex syntax, overhead | Interactive workflows |

**Recommendation:** Use Pexpect for most testing (good balance of power and simplicity).

### C. Performance Benchmarking Methodology

**Measuring Startup Time:**

```bash
# Method 1: External timing
time zsh -i -c exit

# Method 2: Internal profiling (more accurate)
zmodload zsh/zprof
# ... startup code ...
zprof
```

**Measuring Plugin Load Time:**

```bash
# Wrap plugin loading with timing
start=$(date +%s%N)
source ~/.oh-my-zsh/plugins/git/git.plugin.zsh
end=$(date +%s%N)
echo "Plugin load time: $(( (end - start) / 1000000 ))ms"
```

**Measuring Responsiveness:**

```bash
# Test command execution latency
time_command() {
    local start=$(date +%s%N)
    eval "$1" > /dev/null 2>&1
    local end=$(date +%s%N)
    echo $(( (end - start) / 1000000 ))
}

latency=$(time_command "echo test")
echo "Command latency: ${latency}ms"
```

### D. Common Display Issues and Solutions

**Issue: Emoji width mismatch**
- Symptom: Emoji appear to take 1 column but zsh thinks they take 2
- Cause: Terminal and zsh disagree on wcwidth
- Solution: Ensure locale is set correctly, upgrade terminal

**Issue: Line wrapping at wrong column**
- Symptom: Text wraps before reaching edge of terminal
- Cause: ZLE_RPROMPT_INDENT reserves space for right prompt
- Solution: Set ZLE_RPROMPT_INDENT=0 if no right prompt

**Issue: Auto-suggestions leave ghost text**
- Symptom: Accepted suggestions leave characters on screen
- Cause: Terminal doesn't handle clear-to-EOL correctly
- Solution: Update terminal, check TERM value

**Issue: Syntax highlighting causes cursor jump**
- Symptom: Cursor jumps around while typing
- Cause: Highlighting plugin redraws inefficiently
- Solution: Update plugin, reduce highlighting features

### E. Plugin Load Order Best Practices

**Recommended order:**

1. **Prompt theme** (powerlevel10k, starship)
   - Should load first to set up prompt

2. **Completion system** (compinit)
   - Required by many plugins

3. **Syntax highlighting** (fast-syntax-highlighting, zsh-syntax-highlighting)
   - Should load before autosuggestions

4. **Auto-suggestions** (zsh-autosuggestions)
   - Should load after syntax highlighting

5. **Key bindings** (custom bindkey commands)
   - Should load last to override plugin defaults

**Example .zshrc:**
```bash
# 1. Prompt
source ~/.config/powerlevel10k/powerlevel10k.zsh-theme

# 2. Completion
autoload -Uz compinit
compinit

# 3. Syntax highlighting
source ~/.zsh/plugins/fast-syntax-highlighting/fast-syntax-highlighting.plugin.zsh

# 4. Auto-suggestions
source ~/.zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh

# 5. Custom key bindings
bindkey '^[[A' history-search-backward
bindkey '^[[B' history-search-forward
```

### F. Test Environment Directory Structure Detail

```
~/.terminal-guru/
├── config.yaml                           # Global test runner config
├── test-environments/
│   ├── test-20251120-143022/             # Test environment
│   │   ├── metadata.json                 # Test metadata
│   │   ├── zdotdir/                      # Isolated ZDOTDIR
│   │   │   ├── .zshenv
│   │   │   ├── .zshrc
│   │   │   ├── .zprofile
│   │   │   ├── .zlogin
│   │   │   └── functions/
│   │   │       ├── prompt_setup
│   │   │       └── utils
│   │   ├── plugins/                      # Plugin copies
│   │   │   ├── zsh-autosuggestions/
│   │   │   ├── zsh-syntax-highlighting/
│   │   │   └── powerlevel10k/
│   │   ├── logs/                         # Test execution logs
│   │   │   ├── display_test.log
│   │   │   ├── performance_test.log
│   │   │   ├── compatibility_test.log
│   │   │   └── test_runner.log
│   │   ├── results/                      # Structured test results
│   │   │   ├── baseline/
│   │   │   │   ├── display_results.json
│   │   │   │   ├── performance_results.json
│   │   │   │   └── compatibility_results.json
│   │   │   ├── iteration-1/
│   │   │   │   └── ...
│   │   │   └── iteration-2/
│   │   │       └── ...
│   │   ├── diffs/                        # Config change diffs
│   │   │   ├── iteration-1.diff
│   │   │   └── iteration-2.diff
│   │   └── recommendations/              # Generated recommendations
│   │       ├── baseline_recommendations.json
│   │       └── current_recommendations.json
│   └── autosuggestion-fix/               # Another test environment
│       └── ...
└── history/                              # Historical test runs
    └── runs.json
```

---

## Conclusion

This improvement plan transforms terminal-guru from a diagnostic tool into a comprehensive zsh testing and optimization framework. By implementing isolated test environments, comprehensive Python-based test suites, and intelligent analysis, the skill will enable users to confidently diagnose and fix terminal issues without risk to their working shell configuration.

**Key Architectural Advantages:**

1. **Python-Based Testing** - Eliminates circular dependency by using Python to observe shells externally, ensuring test infrastructure bugs cannot contaminate test results
2. **Scientific Rigor** - Clear separation between observer (Python) and observed system (zsh) enables reliable measurements and validations
3. **Future-Proof Design** - Python test infrastructure can easily extend to bash, fish, and other shells without rewriting test logic
4. **Modular Architecture** - Clean separation of concerns allows easy maintenance and extension

The progressive disclosure model keeps the skill approachable while providing deep technical resources when needed. The use of Python throughout ensures tests are reliable, maintainable, and independent of shell-specific behaviors.

**Next Steps:**
1. Review and approve this plan
2. Begin Phase 1 implementation (Python-based isolated environments)
3. Iteratively build out remaining phases (all Python test suites)
4. Collect user feedback and refine
5. Release terminal-guru v2.0

---

**Document Version:** 2.1
**Last Updated:** 2025-11-20
