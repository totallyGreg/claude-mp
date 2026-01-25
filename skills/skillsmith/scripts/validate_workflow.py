#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml>=6.0.1"]
# ///
"""
Skillsmith Validation Workflow - Unified entry point for all validation scenarios.

Provides three validation modes:
1. Quick (dev): Fast validation for development iterations
2. Full (comprehensive): Complete evaluation with metrics
3. Release (strict): Pre-release quality gate with all checks

Usage:
    uv run scripts/validate_workflow.py <skill-path> [--mode {quick|full|release}] [--output {text|json}]

Exit codes:
    0 - All validations passed
    1 - Validation errors (blocking)
    2 - Warnings only (standard mode only)
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Literal


class ValidationWorkflow:
    """Unified validation workflow for skills."""

    def __init__(self, skill_path: str):
        self.skill_path = Path(skill_path).resolve()
        if not self.skill_path.exists():
            raise ValueError(f"Skill path does not exist: {skill_path}")

    def run_quick_validation(self) -> dict:
        """Run quick validation (structural checks only)."""
        return self._run_evaluate_skill(flags=["--quick"])

    def run_full_evaluation(self) -> dict:
        """Run comprehensive evaluation with metrics."""
        return self._run_evaluate_skill(flags=[])

    def run_strict_validation(self) -> dict:
        """Run strict validation (errors + warnings blocking)."""
        return self._run_evaluate_skill(flags=["--quick", "--strict"])

    def _run_evaluate_skill(self, flags: list) -> dict:
        """Execute evaluate_skill.py with specified flags."""
        try:
            # Find evaluate_skill.py in the same directory as this script
            script_dir = Path(__file__).parent
            evaluate_script = script_dir / "evaluate_skill.py"

            if not evaluate_script.exists():
                return {
                    "valid": False,
                    "error": f"evaluate_skill.py not found at {evaluate_script}",
                }

            # Build command
            cmd = [sys.executable, str(evaluate_script), str(self.skill_path)] + flags

            # Run the validation
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )

            return {
                "valid": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "flags": flags,
            }
        except subprocess.TimeoutExpired:
            return {
                "valid": False,
                "error": "Validation timed out (>30 seconds)",
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
            }

    def validate(
        self,
        mode: Literal["quick", "full", "release"] = "quick",
        output_format: Literal["text", "json"] = "text",
    ) -> dict:
        """
        Execute validation workflow.

        Args:
            mode: Validation mode (quick|full|release)
            output_format: Output format (text|json)

        Returns:
            Validation result dict
        """
        print(f"\n{'='*60}")
        print(f"Skillsmith Validation Workflow - {mode.upper()} Mode")
        print(f"{'='*60}")
        print(f"Skill: {self.skill_path.name}")
        print(f"Path: {self.skill_path}")
        print()

        # Run appropriate validation
        if mode == "quick":
            result = self.run_quick_validation()
            stage = "Quick Validation"
        elif mode == "full":
            result = self.run_full_evaluation()
            stage = "Full Evaluation"
        elif mode == "release":
            result = self.run_strict_validation()
            stage = "Strict Validation (Release Gate)"
        else:
            raise ValueError(f"Unknown validation mode: {mode}")

        # Format output
        if output_format == "json":
            return self._format_json(result, stage)
        else:
            return self._format_text(result, stage, mode)

    def _format_text(self, result: dict, stage: str, mode: str) -> dict:
        """Format validation result as human-readable text."""
        print(f"Stage: {stage}")
        print(f"Status: {'✅ PASS' if result['valid'] else '❌ FAIL'}")
        print()

        if "error" in result:
            print(f"Error: {result['error']}")
            print()
            return {
                "valid": False,
                "error": result["error"],
                "exit_code": 1,
            }

        # Print validation output
        if result.get("stdout"):
            print(result["stdout"])

        if result.get("stderr"):
            print("Warnings/Errors:", result["stderr"])

        # Determine exit code
        exit_code = 0 if result["valid"] else 1

        print()
        print(f"{'='*60}")
        print(f"Result: {'PASS ✅' if result['valid'] else 'FAIL ❌'}")
        print(f"Exit Code: {exit_code}")
        print(f"{'='*60}\n")

        return {
            "valid": result["valid"],
            "exit_code": exit_code,
            "mode": mode,
            "stage": stage,
        }

    def _format_json(self, result: dict, stage: str) -> dict:
        """Format validation result as JSON."""
        return {
            "valid": result.get("valid", False),
            "stage": stage,
            "exit_code": result.get("exit_code", 1),
            "error": result.get("error"),
            "details": {
                "stdout": result.get("stdout"),
                "stderr": result.get("stderr"),
            },
        }


def main():
    """CLI entry point for validation workflow."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Skillsmith Validation Workflow - Unified validation entry point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick validation (development)
  uv run scripts/validate_workflow.py skills/my-skill --mode quick

  # Full evaluation with metrics
  uv run scripts/validate_workflow.py skills/my-skill --mode full

  # Strict validation (pre-release)
  uv run scripts/validate_workflow.py skills/my-skill --mode release

  # JSON output for scripting
  uv run scripts/validate_workflow.py skills/my-skill --mode quick --output json
        """,
    )

    parser.add_argument(
        "skill_path", help="Path to skill directory to validate"
    )
    parser.add_argument(
        "--mode",
        choices=["quick", "full", "release"],
        default="quick",
        help="Validation mode (default: quick)",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args()

    try:
        validator = ValidationWorkflow(args.skill_path)
        result = validator.validate(
            mode=args.mode, output_format=args.output
        )

        # Exit with appropriate code
        if args.output == "json":
            print(json.dumps(result, indent=2))

        sys.exit(result.get("exit_code", 1 if not result.get("valid") else 0))

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nValidation cancelled by user", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
