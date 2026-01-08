#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pyyaml>=6.0.1",
# ]
# ///
"""
CoSAI Risk Analyzer

Analyzes AI systems to identify applicable security risks from the CoSAI Risk Map framework.
Can analyze codebases, architecture descriptions, or system configurations.

Usage:
    uv run scripts/analyze_risks.py --target <path_or_description> [options]

Options:
    --target PATH         Path to codebase, config file, or system description
    --persona PERSONA     Your role: ModelCreator or ModelConsumer (default: both)
    --lifecycle STAGE     Filter by lifecycle stage (Data, Infrastructure, Model, Application)
    --output FORMAT       Output format: text, json, yaml (default: text)
    --cache-dir PATH      CoSAI cache directory (default: ~/.cosai-cache)
    --severity-filter     Filter by risk severity: critical, high, medium, low
"""

import argparse
import json
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict


@dataclass
class RiskAssessment:
    """Represents an identified risk"""
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


class RiskAnalyzer:
    """Analyzes AI systems for CoSAI risks"""

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the analyzer.

        Args:
            cache_dir: CoSAI cache directory
        """
        self.cache_dir = cache_dir or Path.home() / ".cosai-cache"
        self.risks_data = None
        self.controls_data = None
        self.components_data = None

    def load_schemas(self) -> bool:
        """
        Load CoSAI schemas from cache.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load risks
            risks_file = self.cache_dir / "yaml" / "risks.yaml"
            if not risks_file.exists():
                print(f"✗ Risks file not found: {risks_file}", file=sys.stderr)
                print("  Run fetch_cosai_schemas.py first to download schemas", file=sys.stderr)
                return False

            with open(risks_file) as f:
                self.risks_data = yaml.safe_load(f)

            # Load controls
            controls_file = self.cache_dir / "yaml" / "controls.yaml"
            with open(controls_file) as f:
                self.controls_data = yaml.safe_load(f)

            # Load components
            components_file = self.cache_dir / "yaml" / "components.yaml"
            with open(components_file) as f:
                self.components_data = yaml.safe_load(f)

            print(f"✓ Loaded {len(self.risks_data['risks'])} risks from cache")
            print(f"✓ Loaded {len(self.controls_data['controls'])} controls from cache")
            print(f"✓ Loaded {len(self.components_data['components'])} components from cache")
            return True

        except Exception as e:
            print(f"✗ Error loading schemas: {e}", file=sys.stderr)
            return False

    def analyze_target(
        self,
        target: str,
        persona_filter: Optional[str] = None,
        lifecycle_filter: Optional[str] = None,
        severity_filter: Optional[str] = None
    ) -> List[RiskAssessment]:
        """
        Analyze a target for applicable risks.

        Args:
            target: Path or description to analyze
            persona_filter: Filter by persona (ModelCreator, ModelConsumer)
            lifecycle_filter: Filter by lifecycle stage
            severity_filter: Filter by severity level

        Returns:
            List of identified risks
        """
        assessments = []
        target_path = Path(target)

        # Determine if target is a file/directory or description
        is_file_target = target_path.exists()

        print(f"\n🔍 Analyzing target: {target}")
        print(f"   Target type: {'File/Directory' if is_file_target else 'Description'}")

        # Analyze each risk for applicability
        for risk in self.risks_data['risks']:
            # Apply filters
            if persona_filter and persona_filter not in risk.get('personas', []):
                continue

            lifecycle_stages = risk.get('lifecycleStage', [])
            if lifecycle_filter and lifecycle_filter not in lifecycle_stages:
                continue

            # Determine applicability (this is simplified - real analysis would be more sophisticated)
            applicable, confidence, rationale = self._assess_risk_applicability(
                risk, target, is_file_target
            )

            if applicable:
                # Infer severity from category and impact
                severity = self._infer_severity(risk)

                if severity_filter and severity.lower() != severity_filter.lower():
                    continue

                assessment = RiskAssessment(
                    risk_id=risk['id'],
                    title=risk['title'],
                    category=risk['category'],
                    severity=severity,
                    applicable_personas=risk.get('personas', []),
                    lifecycle_stages=lifecycle_stages if isinstance(lifecycle_stages, list) else [lifecycle_stages],
                    short_description=risk['shortDescription'],
                    long_description=risk['longDescription'],
                    impact_types=risk.get('impactType', []),
                    relevant_controls=risk.get('controls', []),
                    confidence=confidence,
                    rationale=rationale
                )
                assessments.append(assessment)

        return assessments

    def _assess_risk_applicability(
        self, risk: Dict, target: str, is_file_target: bool
    ) -> tuple[bool, str, str]:
        """
        Assess if a risk is applicable to the target.

        Args:
            risk: Risk definition
            target: Target to analyze
            is_file_target: Whether target is a file/directory

        Returns:
            Tuple of (applicable, confidence, rationale)
        """
        # This is a simplified implementation
        # A production version would use more sophisticated analysis including:
        # - Static code analysis
        # - Dependency scanning
        # - Configuration parsing
        # - LLM-based semantic analysis

        risk_id = risk['id']
        target_lower = target.lower()

        # Simple heuristics for demonstration
        indicators = {
            'DP': ['training', 'dataset', 'data_loader', 'augmentation'],  # Data Poisoning
            'PIJ': ['prompt', 'chat', 'agent', 'llm', 'conversation'],  # Prompt Injection
            'MEV': ['inference', 'predict', 'classify', 'model.eval'],  # Model Evasion
            'MXF': ['model.save', 'checkpoint', 'export', 'serialize'],  # Model Exfiltration
            'SDD': ['pii', 'personal', 'sensitive', 'privacy'],  # Sensitive Data Disclosure
        }

        if risk_id in indicators:
            for indicator in indicators[risk_id]:
                if indicator in target_lower:
                    return (
                        True,
                        "medium",
                        f"Detected {indicator!r} keyword suggesting {risk['title']} risk"
                    )

        # Default: assume all risks are potentially applicable (conservative approach)
        return (
            True,
            "low",
            "Risk may be applicable - requires manual review based on system architecture"
        )

    def _infer_severity(self, risk: Dict) -> str:
        """
        Infer severity level from risk characteristics.

        Args:
            risk: Risk definition

        Returns:
            Severity level: Critical, High, Medium, or Low
        """
        # This is simplified - real severity would consider:
        # - Impact type (safety, privacy, integrity)
        # - Likelihood based on attack surface
        # - Asset criticality
        # - Regulatory implications

        impact_types = risk.get('impactType', [])

        # High severity impacts
        if 'safety' in impact_types or 'integrity' in impact_types:
            return "Critical"

        # Medium-high severity
        if 'privacy' in impact_types or 'availability' in impact_types:
            return "High"

        # Default to medium
        return "Medium"

    def format_output(self, assessments: List[RiskAssessment], format: str) -> str:
        """
        Format assessment results.

        Args:
            assessments: List of risk assessments
            format: Output format (text, json, yaml)

        Returns:
            Formatted output string
        """
        if format == "json":
            return json.dumps(
                [asdict(a) for a in assessments],
                indent=2
            )
        elif format == "yaml":
            return yaml.dump(
                [asdict(a) for a in assessments],
                default_flow_style=False
            )
        else:  # text
            output = []
            output.append("\n" + "="*80)
            output.append(f"CoSAI Risk Assessment Results - {len(assessments)} risks identified")
            output.append("="*80)

            # Group by severity
            by_severity = {}
            for assessment in assessments:
                severity = assessment.severity
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(assessment)

            for severity in ['Critical', 'High', 'Medium', 'Low']:
                if severity not in by_severity:
                    continue

                output.append(f"\n{'='*80}")
                output.append(f"{severity.upper()} SEVERITY RISKS ({len(by_severity[severity])})")
                output.append(f"{'='*80}")

                for assessment in by_severity[severity]:
                    output.append(f"\n[{assessment.risk_id}] {assessment.title}")
                    output.append(f"  Category:    {assessment.category}")
                    output.append(f"  Personas:    {', '.join(assessment.applicable_personas)}")
                    output.append(f"  Lifecycle:   {', '.join(assessment.lifecycle_stages)}")
                    output.append(f"  Confidence:  {assessment.confidence}")
                    output.append(f"  Description: {assessment.short_description}")
                    output.append(f"  Rationale:   {assessment.rationale}")
                    output.append(f"  Controls:    {', '.join(assessment.relevant_controls[:5])}")
                    if len(assessment.relevant_controls) > 5:
                        output.append(f"               ...and {len(assessment.relevant_controls) - 5} more")

            output.append("\n" + "="*80)
            return "\n".join(output)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Analyze AI systems for CoSAI security risks"
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Path to codebase, config, or system description"
    )
    parser.add_argument(
        "--persona",
        choices=["ModelCreator", "ModelConsumer"],
        help="Filter by persona"
    )
    parser.add_argument(
        "--lifecycle",
        choices=["Data", "Infrastructure", "Model", "Application"],
        help="Filter by lifecycle stage"
    )
    parser.add_argument(
        "--output",
        choices=["text", "json", "yaml"],
        default="text",
        help="Output format"
    )
    parser.add_argument(
        "--severity-filter",
        choices=["Critical", "High", "Medium", "Low"],
        help="Filter by severity level"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        help="CoSAI cache directory (default: ~/.cosai-cache)"
    )

    args = parser.parse_args()

    analyzer = RiskAnalyzer(cache_dir=args.cache_dir)

    if not analyzer.load_schemas():
        sys.exit(1)

    assessments = analyzer.analyze_target(
        args.target,
        persona_filter=args.persona,
        lifecycle_filter=args.lifecycle,
        severity_filter=args.severity_filter
    )

    output = analyzer.format_output(assessments, args.output)
    print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
