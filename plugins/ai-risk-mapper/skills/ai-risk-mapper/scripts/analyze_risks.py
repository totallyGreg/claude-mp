#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pyyaml>=6.0.1",
# ]
# ///
"""
CoSAI Risk Analyzer

Analyzes AI systems to identify applicable security risks from the CoSAI Risk Map framework.
Thin wrapper around core_analyzer providing CLI access and assessment context.

Usage:
    uv run scripts/analyze_risks.py --target <path_or_description> [options]

Options:
    --target PATH         Path to codebase, config file, or system description
    --persona PERSONA     Your role: ModelCreator or ModelConsumer (default: both)
    --lifecycle STAGE     Filter by lifecycle stage (Data, Infrastructure, Model, Application)
    --output FORMAT       Output format: text, json, yaml (default: text)
    --cache-dir PATH      CoSAI cache directory (default: ~/.cosai-cache)
    --offline             Use bundled schemas (offline mode)
    --severity-filter     Filter by risk severity: Critical, High, Medium, Low
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# Import core analyzer - handles all schema loading
from core_analyzer import RiskAnalyzer as CoreAnalyzer


@dataclass
class RiskAssessment:
    """Represents an identified risk with assessment context."""

    risk_id: str
    title: str
    category: str
    severity: str
    applicable_personas: List[str]
    lifecycle_stages: List[str]
    short_description: str
    long_description: str
    impact_types: List[str]
    relevant_controls: List[str]
    confidence: str  # high, medium, low
    rationale: str


# Keyword indicators for applicability heuristics
RISK_INDICATORS = {
    "DP": ["training", "dataset", "data_loader", "augmentation"],
    "PIJ": ["prompt", "chat", "agent", "llm", "conversation"],
    "MEV": ["inference", "predict", "classify", "model.eval"],
    "MXF": ["model.save", "checkpoint", "export", "serialize"],
    "SDD": ["pii", "personal", "sensitive", "privacy"],
}


class TargetAnalyzer:
    """Analyzes targets for CoSAI risks using core analyzer."""

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        offline: bool = False,
    ):
        """
        Initialize the analyzer.

        Args:
            cache_dir: CoSAI cache directory (overrides default)
            offline: Use bundled schemas
        """
        # Determine yaml_dir based on arguments
        yaml_dir = None
        if cache_dir:
            yaml_dir = cache_dir / "yaml"

        try:
            self.core = CoreAnalyzer(yaml_dir=yaml_dir, offline=offline)
            stats = self.core.get_statistics()
            print(f"✓ Loaded {stats['total_risks']} risks from cache")
            print(f"✓ Loaded {stats['total_controls']} controls from cache")
            print(f"✓ Loaded {stats['total_components']} components from cache")
        except FileNotFoundError as e:
            print(f"✗ {e}", file=sys.stderr)
            raise

    def analyze_target(
        self,
        target: str,
        persona_filter: Optional[str] = None,
        lifecycle_filter: Optional[str] = None,
        severity_filter: Optional[str] = None,
    ) -> List[RiskAssessment]:
        """
        Analyze a target for applicable risks.

        Args:
            target: Path or description to analyze
            persona_filter: Filter by persona (personaModelCreator, personaModelConsumer)
            lifecycle_filter: Filter by lifecycle stage
            severity_filter: Filter by severity level

        Returns:
            List of identified risks with assessment context
        """
        assessments = []
        target_path = Path(target)
        is_file_target = target_path.exists()

        print(f"\n🔍 Analyzing target: {target}")
        print(f"   Target type: {'File/Directory' if is_file_target else 'Description'}")

        # Map simple persona names to full IDs
        persona_id = None
        if persona_filter:
            persona_id = f"persona{persona_filter}"

        for risk in self.core.get_all_risks():
            # Apply persona filter
            if persona_id and persona_id not in risk.personas:
                continue

            # Apply lifecycle filter
            if lifecycle_filter and lifecycle_filter not in risk.lifecycle_stages:
                continue

            # Assess applicability
            applicable, confidence, rationale = self._assess_applicability(
                risk.id, risk.title, target, is_file_target
            )

            if applicable:
                severity = self._infer_severity(risk.impact_types)

                if severity_filter and severity.lower() != severity_filter.lower():
                    continue

                assessment = RiskAssessment(
                    risk_id=risk.id,
                    title=risk.title,
                    category=risk.category,
                    severity=severity,
                    applicable_personas=risk.personas,
                    lifecycle_stages=risk.lifecycle_stages,
                    short_description=risk.short_description,
                    long_description=risk.long_description,
                    impact_types=risk.impact_types,
                    relevant_controls=risk.controls,
                    confidence=confidence,
                    rationale=rationale,
                )
                assessments.append(assessment)

        return assessments

    def _assess_applicability(
        self, risk_id: str, risk_title: str, target: str, is_file_target: bool
    ) -> tuple:
        """Assess if a risk applies to the target using keyword heuristics."""
        target_lower = target.lower()

        if risk_id in RISK_INDICATORS:
            for indicator in RISK_INDICATORS[risk_id]:
                if indicator in target_lower:
                    return (
                        True,
                        "medium",
                        f"Detected '{indicator}' keyword suggesting {risk_title} risk",
                    )

        # Conservative: assume all risks potentially applicable
        return (
            True,
            "low",
            "Risk may be applicable - requires manual review based on system architecture",
        )

    def _infer_severity(self, impact_types: List[str]) -> str:
        """Infer severity from impact types."""
        if "safety" in impact_types or "integrity" in impact_types:
            return "Critical"
        if "privacy" in impact_types or "availability" in impact_types:
            return "High"
        return "Medium"


def format_output(assessments: List[RiskAssessment], output_format: str) -> str:
    """Format assessment results for output."""
    if output_format == "json":
        return json.dumps([asdict(a) for a in assessments], indent=2)

    if output_format == "yaml":
        return yaml.dump([asdict(a) for a in assessments], default_flow_style=False)

    # Text format
    lines = [
        "",
        "=" * 80,
        f"CoSAI Risk Assessment Results - {len(assessments)} risks identified",
        "=" * 80,
    ]

    # Group by severity
    by_severity: Dict[str, List[RiskAssessment]] = {}
    for assessment in assessments:
        by_severity.setdefault(assessment.severity, []).append(assessment)

    for severity in ["Critical", "High", "Medium", "Low"]:
        if severity not in by_severity:
            continue

        lines.extend([
            "",
            "=" * 80,
            f"{severity.upper()} SEVERITY RISKS ({len(by_severity[severity])})",
            "=" * 80,
        ])

        for a in by_severity[severity]:
            lines.extend([
                "",
                f"[{a.risk_id}] {a.title}",
                f"  Category:    {a.category}",
                f"  Personas:    {', '.join(a.applicable_personas)}",
                f"  Lifecycle:   {', '.join(a.lifecycle_stages)}",
                f"  Confidence:  {a.confidence}",
                f"  Description: {a.short_description}",
                f"  Rationale:   {a.rationale}",
                f"  Controls:    {', '.join(a.relevant_controls[:5])}",
            ])
            if len(a.relevant_controls) > 5:
                lines.append(f"               ...and {len(a.relevant_controls) - 5} more")

    lines.append("")
    lines.append("=" * 80)
    return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze AI systems for CoSAI security risks"
    )
    parser.add_argument(
        "--target", required=True, help="Path to codebase, config, or system description"
    )
    parser.add_argument(
        "--persona",
        choices=["ModelCreator", "ModelConsumer"],
        help="Filter by persona",
    )
    parser.add_argument(
        "--lifecycle",
        choices=["Data", "Infrastructure", "Model", "Application"],
        help="Filter by lifecycle stage",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json", "yaml"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--severity-filter",
        choices=["Critical", "High", "Medium", "Low"],
        help="Filter by severity level",
    )
    parser.add_argument(
        "--cache-dir", type=Path, help="CoSAI cache directory (default: ~/.cosai-cache)"
    )
    parser.add_argument(
        "--offline", action="store_true", help="Use bundled schemas (offline mode)"
    )

    args = parser.parse_args()

    try:
        analyzer = TargetAnalyzer(cache_dir=args.cache_dir, offline=args.offline)
    except FileNotFoundError:
        sys.exit(1)

    assessments = analyzer.analyze_target(
        args.target,
        persona_filter=args.persona,
        lifecycle_filter=args.lifecycle,
        severity_filter=args.severity_filter,
    )

    print(format_output(assessments, args.output))
    sys.exit(0)


if __name__ == "__main__":
    main()
