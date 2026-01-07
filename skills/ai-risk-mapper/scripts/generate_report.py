#!/usr/bin/env python3
"""
CoSAI Risk Assessment Report Generator

Generates comprehensive risk assessment reports from analysis results.
Supports multiple output formats including Markdown, HTML, and JSON.

Usage:
    python3 generate_report.py --analysis FILE --output FILE [options]

Options:
    --analysis FILE       JSON file with risk analysis results
    --output FILE         Output file path
    --format FORMAT       Report format: markdown, html, json (default: markdown)
    --template PATH       Custom template file
    --include-controls    Include detailed control recommendations
    --include-examples    Include risk examples and case studies
    --executive-summary   Include executive summary section
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ReportGenerator:
    """Generates risk assessment reports"""

    def __init__(self):
        """Initialize the generator"""
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def load_analysis(self, analysis_file: Path) -> Dict:
        """
        Load analysis results from JSON file.

        Args:
            analysis_file: Path to analysis JSON file

        Returns:
            Analysis data dictionary
        """
        try:
            with open(analysis_file) as f:
                data = json.load(f)
            print(f"✓ Loaded analysis with {len(data)} risks")
            return data
        except Exception as e:
            print(f"✗ Error loading analysis: {e}", file=sys.stderr)
            sys.exit(1)

    def generate_markdown(
        self,
        analysis: List[Dict],
        include_controls: bool = False,
        include_examples: bool = False,
        executive_summary: bool = False
    ) -> str:
        """
        Generate Markdown report.

        Args:
            analysis: List of risk assessments
            include_controls: Include control recommendations
            include_examples: Include risk examples
            executive_summary: Include executive summary

        Returns:
            Markdown report string
        """
        lines = []

        # Title
        lines.append("# AI Security Risk Assessment Report")
        lines.append("")
        lines.append(f"**Generated:** {self.timestamp}")
        lines.append(f"**Framework:** CoSAI Risk Map (Coalition for Secure AI)")
        lines.append(f"**Total Risks Identified:** {len(analysis)}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Executive Summary
        if executive_summary:
            lines.extend(self._generate_executive_summary(analysis))

        # Risk Summary Statistics
        lines.append("## Risk Summary")
        lines.append("")
        lines.extend(self._generate_summary_stats(analysis))
        lines.append("")

        # Risks by Severity
        lines.append("## Identified Risks")
        lines.append("")

        by_severity = self._group_by_severity(analysis)

        for severity in ['Critical', 'High', 'Medium', 'Low']:
            if severity not in by_severity:
                continue

            risks = by_severity[severity]
            lines.append(f"### {severity} Severity ({len(risks)} risks)")
            lines.append("")

            for risk in risks:
                lines.append(f"#### [{risk['risk_id']}] {risk['title']}")
                lines.append("")
                lines.append(f"**Category:** {risk['category']}")
                lines.append(f"**Applicable Personas:** {', '.join(risk['applicable_personas'])}")
                lines.append(f"**Lifecycle Stages:** {', '.join(risk['lifecycle_stages'])}")
                lines.append(f"**Confidence:** {risk['confidence']}")
                lines.append("")
                lines.append("**Description:**")
                lines.append(f"{risk['short_description']}")
                lines.append("")
                lines.append("**Assessment Rationale:**")
                lines.append(f"{risk['rationale']}")
                lines.append("")

                if include_controls and risk['relevant_controls']:
                    lines.append("**Recommended Controls:**")
                    for control_id in risk['relevant_controls'][:3]:
                        lines.append(f"- {control_id}")
                    if len(risk['relevant_controls']) > 3:
                        lines.append(f"- ...and {len(risk['relevant_controls']) - 3} more")
                    lines.append("")

                lines.append("---")
                lines.append("")

        # Next Steps
        lines.append("## Recommended Next Steps")
        lines.append("")
        lines.append("1. **Review Critical and High Severity Risks**: Prioritize mitigation efforts")
        lines.append("2. **Validate Risk Applicability**: Confirm each risk applies to your specific system")
        lines.append("3. **Implement Controls**: Apply recommended controls from the CoSAI framework")
        lines.append("4. **Establish Monitoring**: Set up detection and response for runtime risks")
        lines.append("5. **Schedule Reassessment**: Conduct regular security assessments as system evolves")
        lines.append("")

        # References
        lines.append("## References")
        lines.append("")
        lines.append("- [CoSAI Risk Map Framework](https://github.com/cosai-oasis/secure-ai-tooling)")
        lines.append("- [MITRE ATLAS](https://atlas.mitre.org/)")
        lines.append("- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)")
        lines.append("- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)")
        lines.append("")

        return "\n".join(lines)

    def generate_html(self, analysis: List[Dict], **kwargs) -> str:
        """
        Generate HTML report.

        Args:
            analysis: List of risk assessments
            **kwargs: Additional options

        Returns:
            HTML report string
        """
        # For now, wrap markdown in basic HTML
        # A production version would use proper HTML templates
        markdown_content = self.generate_markdown(analysis, **kwargs)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Security Risk Assessment Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1, h2, h3, h4 {{ color: #2c3e50; }}
        h1 {{ border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ border-bottom: 2px solid #95a5a6; padding-bottom: 8px; margin-top: 30px; }}
        h3 {{ color: #e74c3c; margin-top: 25px; }}
        h4 {{ color: #34495e; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        hr {{ border: 0; border-top: 1px solid #ddd; margin: 20px 0; }}
        strong {{ color: #2c3e50; }}
        ul {{ padding-left: 25px; }}
        .timestamp {{ color: #7f8c8d; font-style: italic; }}
    </style>
</head>
<body>
<pre>{markdown_content}</pre>
</body>
</html>"""
        return html

    def _generate_executive_summary(self, analysis: List[Dict]) -> List[str]:
        """Generate executive summary section"""
        lines = []
        lines.append("## Executive Summary")
        lines.append("")

        # Count by severity
        by_severity = self._group_by_severity(analysis)
        critical = len(by_severity.get('Critical', []))
        high = len(by_severity.get('High', []))
        medium = len(by_severity.get('Medium', []))
        low = len(by_severity.get('Low', []))

        lines.append(f"This report identifies **{len(analysis)} security risks** in the assessed AI system ")
        lines.append(f"based on the CoSAI Risk Map framework. Risk distribution:")
        lines.append("")
        lines.append(f"- **Critical:** {critical} risks requiring immediate attention")
        lines.append(f"- **High:** {high} risks requiring prompt remediation")
        lines.append(f"- **Medium:** {medium} risks requiring planned mitigation")
        lines.append(f"- **Low:** {low} risks requiring monitoring")
        lines.append("")

        if critical > 0:
            lines.append("⚠️ **URGENT**: Critical severity risks identified. Immediate action required.")
            lines.append("")

        lines.append("---")
        lines.append("")

        return lines

    def _generate_summary_stats(self, analysis: List[Dict]) -> List[str]:
        """Generate summary statistics"""
        lines = []

        # Risks by category
        by_category = {}
        for risk in analysis:
            cat = risk['category']
            by_category[cat] = by_category.get(cat, 0) + 1

        lines.append("### Risks by Category")
        lines.append("")
        for category, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{category}**: {count} risks")
        lines.append("")

        # Risks by lifecycle stage
        by_lifecycle = {}
        for risk in analysis:
            for stage in risk['lifecycle_stages']:
                by_lifecycle[stage] = by_lifecycle.get(stage, 0) + 1

        lines.append("### Risks by Lifecycle Stage")
        lines.append("")
        for stage, count in sorted(by_lifecycle.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{stage}**: {count} risks")
        lines.append("")

        return lines

    def _group_by_severity(self, analysis: List[Dict]) -> Dict[str, List[Dict]]:
        """Group risks by severity"""
        by_severity = {}
        for risk in analysis:
            severity = risk['severity']
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(risk)
        return by_severity

    def generate_report(
        self,
        analysis_file: Path,
        output_file: Path,
        format: str,
        **options
    ) -> bool:
        """
        Generate complete report.

        Args:
            analysis_file: Input analysis JSON
            output_file: Output report file
            format: Output format
            **options: Additional report options

        Returns:
            True if successful
        """
        try:
            # Load analysis
            analysis = self.load_analysis(analysis_file)

            # Generate report
            if format == "markdown":
                content = self.generate_markdown(analysis, **options)
            elif format == "html":
                content = self.generate_html(analysis, **options)
            elif format == "json":
                content = json.dumps(analysis, indent=2)
            else:
                print(f"✗ Unsupported format: {format}", file=sys.stderr)
                return False

            # Write output
            output_file.write_text(content)
            print(f"✓ Report generated: {output_file}")
            print(f"  Format: {format}")
            print(f"  Risks: {len(analysis)}")

            return True

        except Exception as e:
            print(f"✗ Error generating report: {e}", file=sys.stderr)
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate CoSAI risk assessment reports"
    )
    parser.add_argument(
        "--analysis",
        type=Path,
        required=True,
        help="Input analysis JSON file"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output report file"
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "html", "json"],
        default="markdown",
        help="Report format"
    )
    parser.add_argument(
        "--include-controls",
        action="store_true",
        help="Include control recommendations"
    )
    parser.add_argument(
        "--include-examples",
        action="store_true",
        help="Include risk examples"
    )
    parser.add_argument(
        "--executive-summary",
        action="store_true",
        help="Include executive summary"
    )

    args = parser.parse_args()

    generator = ReportGenerator()
    success = generator.generate_report(
        args.analysis,
        args.output,
        args.format,
        include_controls=args.include_controls,
        include_examples=args.include_examples,
        executive_summary=args.executive_summary
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
