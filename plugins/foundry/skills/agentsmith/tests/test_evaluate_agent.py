#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pyyaml>=6.0.1",
# ]
# ///
"""Tests for evaluate_agent.py scoring logic."""

import json
import sys
import tempfile
import textwrap
import unittest
from io import StringIO
from pathlib import Path

# Add scripts directory to path so we can import the module
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / 'scripts'
sys.path.insert(0, str(SCRIPTS_DIR))

from evaluate_agent import (
    extract_examples,
    parse_agent_file,
    score_trigger_effectiveness,
    score_system_prompt_quality,
    score_coherence,
    calculate_overall_score,
    evaluate_agent,
    print_quick_output,
    strip_code_blocks,
)
from utils import find_agent_file


# ============================================================================
# Sample agent content for testing
# ============================================================================

SAMPLE_AGENT_FULL = textwrap.dedent("""\
    ---
    name: test-agent
    description: |
      Use this agent when testing evaluation logic.

      <example>
      Context: User wants to test something
      user: "Run the evaluation tests"
      assistant: "I'll use the test-agent to run the evaluation suite."
      <commentary>
      Standard test invocation. Routes to the test runner.
      </commentary>
      </example>

      <example>
      Context: User reports a failing test
      user: "My tests are broken, help me diagnose"
      assistant: "I'll use the test-agent to analyze the test failures."
      <commentary>
      Diagnostic workflow — agent checks test output and identifies root cause.
      </commentary>
      </example>

      <example>
      Context: User wants proactive test monitoring
      user: "Watch for test regressions after my refactor"
      assistant: "I'll use the test-agent to monitor test results."
      <commentary>
      Proactive trigger — agent monitors after user completes a refactor.
      </commentary>
      </example>

      Do NOT use this agent for production deployments or manual testing.

    tools: ["Read", "Bash", "Grep"]
    model: inherit
    color: green
    ---

    # Test Agent

    You are a test orchestration agent that manages automated test suites. You analyze test failures, identify root causes, and suggest fixes.

    ## Responsibilities

    - Run test suites via Bash
    - Parse test output for failures
    - Identify root causes of failures
    - Suggest specific fixes
    - Track test health over time

    ## Workflow

    1. **Discover tests**: Read test configuration files
    2. **Run suite**: Execute tests via `uv run pytest`
    3. **Parse output**: Extract failures and errors
    4. **Diagnose**: Analyze stack traces with Grep
    5. **Report**: Present findings with fix suggestions

    ## Quality Standards

    - MUST run all tests before reporting
    - ALWAYS include stack traces in reports
    - NEVER modify production code without approval

    ## Output Format

    ```markdown
    ## Test Report

    | Suite | Pass | Fail | Skip |
    |-------|------|------|------|
    | ...   | ...  | ...  | ...  |

    ### Failures
    - Test name: reason
    ```

    ## Edge Cases

    - If test directory is not found, report the error
    - If tests fail to compile, check for syntax errors first
    - If no tests are found, suggest creating test files
    """)

SAMPLE_AGENT_MINIMAL = textwrap.dedent("""\
    ---
    name: minimal-agent
    description: A minimal agent.
    model: inherit
    ---

    Help the user.
    """)

SAMPLE_AGENT_NO_FRONTMATTER = "# No Frontmatter\n\nJust a body."

SAMPLE_AGENT_MALFORMED_YAML = textwrap.dedent("""\
    ---
    name: broken
    description: [invalid yaml
    ---

    Body text.
    """)


class TestYAMLParsing(unittest.TestCase):
    """Test YAML frontmatter parsing."""

    def _write_agent(self, content: str) -> Path:
        """Write content to a temp agent file and return path."""
        tmpdir = tempfile.mkdtemp()
        agent_path = Path(tmpdir) / 'test-agent.md'
        agent_path.write_text(content)
        return agent_path

    def test_valid_frontmatter(self):
        path = self._write_agent(SAMPLE_AGENT_FULL)
        parsed = parse_agent_file(path)
        self.assertEqual(parsed['name'], 'test-agent')
        self.assertEqual(parsed['pattern'], 'flat')
        self.assertIn('description', parsed['frontmatter'])
        self.assertIn('Test Agent', parsed['body'])

    def test_missing_frontmatter(self):
        path = self._write_agent(SAMPLE_AGENT_NO_FRONTMATTER)
        with self.assertRaises(ValueError):
            parse_agent_file(path)

    def test_malformed_yaml(self):
        path = self._write_agent(SAMPLE_AGENT_MALFORMED_YAML)
        with self.assertRaises(ValueError):
            parse_agent_file(path)

    def test_minimal_frontmatter(self):
        path = self._write_agent(SAMPLE_AGENT_MINIMAL)
        parsed = parse_agent_file(path)
        self.assertEqual(parsed['name'], 'minimal-agent')


class TestAgentFileDetection(unittest.TestCase):
    """Test agent file detection (flat vs directory patterns)."""

    def test_flat_pattern_direct_file(self):
        tmpdir = tempfile.mkdtemp()
        agent_path = Path(tmpdir) / 'my-agent.md'
        agent_path.write_text(SAMPLE_AGENT_FULL)
        result = find_agent_file(str(agent_path))
        self.assertEqual(result, agent_path.resolve())

    def test_directory_pattern_agent_md(self):
        tmpdir = tempfile.mkdtemp()
        agent_dir = Path(tmpdir) / 'my-agent'
        agent_dir.mkdir()
        agent_md = agent_dir / 'AGENT.md'
        agent_md.write_text(SAMPLE_AGENT_FULL)
        result = find_agent_file(str(agent_dir))
        self.assertEqual(result, agent_md.resolve())

    def test_flat_pattern_from_directory(self):
        tmpdir = tempfile.mkdtemp()
        agents_dir = Path(tmpdir) / 'agents'
        agents_dir.mkdir()
        # Create the flat .md file
        flat_md = agents_dir / 'my-agent.md'
        flat_md.write_text(SAMPLE_AGENT_FULL)
        # Create a directory with the same name
        agent_dir = agents_dir / 'my-agent'
        agent_dir.mkdir()
        result = find_agent_file(str(agent_dir))
        self.assertEqual(result, flat_md.resolve())

    def test_nonexistent_raises(self):
        with self.assertRaises(FileNotFoundError):
            find_agent_file('/nonexistent/path/agent.md')


class TestExampleExtraction(unittest.TestCase):
    """Test extraction of <example> blocks."""

    def test_extract_multiple_examples(self):
        parsed = parse_agent_file(
            self._write_agent(SAMPLE_AGENT_FULL)
        )
        examples = extract_examples(parsed['frontmatter']['description'])
        self.assertEqual(len(examples), 3)

    def test_example_has_user_and_assistant(self):
        parsed = parse_agent_file(
            self._write_agent(SAMPLE_AGENT_FULL)
        )
        examples = extract_examples(parsed['frontmatter']['description'])
        for ex in examples:
            self.assertIn('user', ex)
            self.assertIn('assistant', ex)

    def test_example_has_commentary(self):
        parsed = parse_agent_file(
            self._write_agent(SAMPLE_AGENT_FULL)
        )
        examples = extract_examples(parsed['frontmatter']['description'])
        for ex in examples:
            self.assertIn('commentary', ex)

    def test_no_examples(self):
        examples = extract_examples("A plain description with no examples.")
        self.assertEqual(len(examples), 0)

    def _write_agent(self, content: str) -> Path:
        tmpdir = tempfile.mkdtemp()
        agent_path = Path(tmpdir) / 'test-agent.md'
        agent_path.write_text(content)
        return agent_path


class TestScoringProducesResults(unittest.TestCase):
    """Test that scoring produces non-zero results for sample agents."""

    def setUp(self):
        tmpdir = tempfile.mkdtemp()
        self.agent_path = Path(tmpdir) / 'test-agent.md'
        self.agent_path.write_text(SAMPLE_AGENT_FULL)

    def test_full_agent_produces_nonzero_scores(self):
        result = evaluate_agent(self.agent_path)
        m = result['metrics']
        self.assertGreater(m['trigger_effectiveness']['score'], 0)
        self.assertGreater(m['system_prompt_quality']['score'], 0)
        self.assertGreater(m['coherence']['score'], 0)
        self.assertGreater(m['overall_score'], 0)

    def test_minimal_agent_produces_low_scores(self):
        tmpdir = tempfile.mkdtemp()
        path = Path(tmpdir) / 'minimal.md'
        path.write_text(SAMPLE_AGENT_MINIMAL)
        result = evaluate_agent(path)
        m = result['metrics']
        # Minimal agent should score lower than full agent
        self.assertLess(m['overall_score'], 50)

    def test_overall_score_is_weighted(self):
        result = evaluate_agent(self.agent_path)
        m = result['metrics']
        # Recalculate and verify
        expected = calculate_overall_score(
            m['trigger_effectiveness'],
            m['system_prompt_quality'],
            m['coherence'],
        )
        self.assertEqual(m['overall_score'], expected)


class TestTriggerEffectiveness(unittest.TestCase):
    """Test trigger effectiveness scoring sub-metrics."""

    def test_negative_trigger_detected(self):
        fm = {
            'description': (
                'Use this agent for X.\n'
                'Do NOT use this agent for Y.\n'
                '<example>\nuser: "test"\nassistant: "ok"\n</example>'
            )
        }
        examples = extract_examples(fm['description'])
        result = score_trigger_effectiveness(fm, examples)
        self.assertTrue(
            result['sub_metrics']['negative_triggers']['present']
        )

    def test_no_negative_trigger(self):
        fm = {
            'description': (
                'Use this agent for X.\n'
                '<example>\nuser: "test"\nassistant: "ok"\n</example>'
            )
        }
        examples = extract_examples(fm['description'])
        result = score_trigger_effectiveness(fm, examples)
        self.assertFalse(
            result['sub_metrics']['negative_triggers']['present']
        )


class TestSystemPromptQuality(unittest.TestCase):
    """Test system prompt quality scoring."""

    def test_well_structured_body_scores_high(self):
        body = textwrap.dedent("""\
            # Test Agent

            You are an expert test orchestration agent that manages automated testing.

            ## Responsibilities

            - Run test suites
            - Parse output
            - Identify failures
            - Suggest fixes
            - Track history

            ## Workflow

            1. **Discover** tests
            2. **Run** suite
            3. **Parse** output
            4. **Diagnose** failures
            5. **Report** findings

            ## Quality Standards

            - MUST run all tests
            - ALWAYS report clearly
            - NEVER skip errors

            ## Output Format

            ```markdown
            ## Report
            | Status | Count |
            |--------|-------|
            ```

            ## Edge Cases

            - If tests not found, report error
            - If compilation fails, check syntax
            """)
        result = score_system_prompt_quality(body)
        self.assertGreater(result['score'], 60)

    def test_minimal_body_scores_low(self):
        body = "Help the user."
        result = score_system_prompt_quality(body)
        self.assertLess(result['score'], 30)

    def test_length_sweet_spot(self):
        # 500-3000 words should get full length score
        body = "word " * 1000
        result = score_system_prompt_quality(body)
        self.assertEqual(
            result['sub_metrics']['length_sweet_spot']['score'], 15
        )

    def test_too_short(self):
        body = "word " * 50
        result = score_system_prompt_quality(body)
        self.assertEqual(
            result['sub_metrics']['length_sweet_spot']['score'], 0
        )


class TestCoherence(unittest.TestCase):
    """Test coherence scoring."""

    def test_aligned_agent_scores_well(self):
        fm = {
            'description': (
                'Use for testing.\n'
                '<example>\nuser: "Run tests"\nassistant: "Running test suite"\n'
                '<commentary>Runs tests</commentary>\n</example>'
            ),
            'tools': ['Read', 'Bash'],
        }
        body = (
            "# Test Agent\n\n"
            "You run tests using Bash and Read tool.\n\n"
            "## Running Tests\n\n"
            "Use Bash to execute the test suite.\n"
        )
        examples = extract_examples(fm['description'])
        result = score_coherence(fm, body, examples)
        self.assertGreater(result['score'], 30)

    def test_no_tools_declared(self):
        fm = {'description': 'A description.'}
        body = "Some body text."
        examples = []
        result = score_coherence(fm, body, examples)
        # Should still produce a score
        self.assertGreaterEqual(result['score'], 0)


class TestQuickOutput(unittest.TestCase):
    """Test --quick output format."""

    def test_quick_output_format(self):
        result = {
            'agent': 'test-agent',
            'metrics': {
                'trigger_effectiveness': {'score': 75},
                'system_prompt_quality': {'score': 80},
                'coherence': {'score': 70},
                'overall_score': 75,
            },
        }
        captured = StringIO()
        sys.stdout = captured
        print_quick_output(result)
        sys.stdout = sys.__stdout__
        output = captured.getvalue()
        self.assertIn('[agentsmith]', output)
        self.assertIn('Quick eval', output)
        self.assertIn('Overall 75/100', output)
        self.assertIn('Trig:75', output)
        self.assertIn('Prompt:80', output)
        self.assertIn('Coher:70', output)


class TestJSONOutput(unittest.TestCase):
    """Test --format json output is valid JSON."""

    def test_evaluate_produces_valid_json(self):
        tmpdir = tempfile.mkdtemp()
        path = Path(tmpdir) / 'test-agent.md'
        path.write_text(SAMPLE_AGENT_FULL)
        result = evaluate_agent(path)
        # Should be JSON-serializable
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        self.assertIn('agent', parsed)
        self.assertIn('metrics', parsed)
        self.assertIn('overall_score', parsed['metrics'])

    def test_json_has_required_fields(self):
        tmpdir = tempfile.mkdtemp()
        path = Path(tmpdir) / 'test-agent.md'
        path.write_text(SAMPLE_AGENT_FULL)
        result = evaluate_agent(path)
        self.assertIn('agent', result)
        self.assertIn('path', result)
        self.assertIn('pattern', result)
        self.assertIn('metrics', result)
        m = result['metrics']
        self.assertIn('trigger_effectiveness', m)
        self.assertIn('system_prompt_quality', m)
        self.assertIn('coherence', m)
        self.assertIn('overall_score', m)


class TestStripCodeBlocks(unittest.TestCase):
    """Test code block stripping utility."""

    def test_strips_fenced_blocks(self):
        text = "Before\n```python\ncode here\n```\nAfter"
        result = strip_code_blocks(text)
        self.assertNotIn('code here', result)
        self.assertIn('Before', result)
        self.assertIn('After', result)

    def test_preserves_non_code(self):
        text = "No code blocks here, just text."
        result = strip_code_blocks(text)
        self.assertEqual(result, text)


if __name__ == '__main__':
    unittest.main()
