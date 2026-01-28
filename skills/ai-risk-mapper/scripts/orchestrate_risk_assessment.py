#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml>=6.0.1"]
# ///
"""
Risk Assessment Orchestrator

Automatically executes the complete CoSAI risk assessment workflow when invoked.
Handles schema fetching, risk analysis, and report generation with graceful fallback.

Usage (invoked by Claude when ai-risk-mapper skill triggers):
    uv run scripts/orchestrate_risk_assessment.py --target <path> [options]

Options:
    --target PATH           Target to analyze (file, directory, or description)
    --persona PERSONA       ModelCreator or ModelConsumer (default: both)
    --output-dir PATH       Output directory (default: ./risk-assessment-output)
    --skip-schemas          Skip schema fetching (use cached)
    --offline               Offline mode with bundled schemas
    --format FORMAT         Report format: markdown, html, json (default: markdown)
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Optional


class RiskAssessmentOrchestrator:
    """Orchestrates complete risk assessment workflow"""

    def __init__(self, target: Path, output_dir: Path, offline: bool = False):
        self.target = target
        self.output_dir = output_dir
        self.offline = offline
        self.cache_dir = Path.home() / ".cosai-cache"

    def run(self) -> bool:
        """Execute complete workflow with error handling"""

        print("🔍 AI Risk Assessment Workflow")
        print(f"Target: {self.target}")
        print("-" * 60)

        # Step 1: Ensure schemas are available
        if not self.offline:
            if not self._fetch_schemas():
                print("\n⚠️  Schema fetch failed. Attempting offline mode...")
                self.offline = True

        if self.offline:
            if not self._use_bundled_schemas():
                print("\n❌ Offline mode failed. Cannot proceed.")
                return False

        # Step 2: Analyze risks
        print("\n📊 Step 2: Analyzing Risks...")
        analysis_file = self._analyze_risks()
        if not analysis_file:
            print("❌ Risk analysis failed")
            return False

        # Step 3: Generate report
        print("\n📝 Step 3: Generating Report...")
        report_file = self._generate_report(analysis_file)
        if not report_file:
            print("❌ Report generation failed")
            return False

        # Success summary
        print("\n✅ Assessment Complete!")
        print(f"   Analysis: {analysis_file}")
        print(f"   Report:   {report_file}")
        return True

    def _fetch_schemas(self) -> bool:
        """Fetch CoSAI schemas with error handling"""
        print("\n📥 Step 1: Fetching Schemas...")
        try:
            # Import the fetcher from the local script
            sys.path.insert(0, str(Path(__file__).parent))
            from fetch_cosai_schemas import CoSAIFetcher

            fetcher = CoSAIFetcher(cache_dir=self.cache_dir, force=False)
            return fetcher.run()
        except Exception as e:
            print(f"⚠️  Schema fetch error: {e}")
            return False

    def _use_bundled_schemas(self) -> bool:
        """Use pre-bundled schemas as fallback"""
        print("📦 Using bundled schemas (offline mode)")
        bundled_dir = Path(__file__).parent.parent / "assets" / "cosai-schemas"
        if not bundled_dir.exists():
            print(f"❌ Bundled schemas not found at: {bundled_dir}")
            return False

        # Copy bundled schemas to cache
        try:
            shutil.copytree(bundled_dir, self.cache_dir, dirs_exist_ok=True)
            print(f"✓ Bundled schemas ready (offline mode)")
            return True
        except Exception as e:
            print(f"❌ Failed to setup bundled schemas: {e}")
            return False

    def _analyze_risks(self) -> Optional[Path]:
        """Run risk analysis"""
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from analyze_risks import RiskAnalyzer

            analyzer = RiskAnalyzer(cache_dir=self.cache_dir)

            if not analyzer.load_schemas():
                return None

            # Perform analysis
            risks = analyzer.analyze_target(str(self.target))

            # Save results
            self.output_dir.mkdir(parents=True, exist_ok=True)
            analysis_file = self.output_dir / "risk_analysis.json"

            with open(analysis_file, 'w') as f:
                json.dump([risk.__dict__ for risk in risks], f, indent=2)

            print(f"✓ Identified {len(risks)} applicable risks")
            return analysis_file

        except Exception as e:
            print(f"❌ Analysis error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _generate_report(self, analysis_file: Path) -> Optional[Path]:
        """Generate assessment report"""
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from generate_report import ReportGenerator

            generator = ReportGenerator()
            analysis_data = generator.load_analysis(analysis_file)

            report_file = self.output_dir / "ai_security_assessment.md"
            report_content = generator.generate_markdown(
                analysis_data,
                include_controls=True,
                include_examples=False,
                executive_summary=True
            )

            with open(report_file, 'w') as f:
                f.write(report_content)

            print(f"✓ Generated report: {report_file.name}")
            return report_file

        except Exception as e:
            print(f"❌ Report generation error: {e}")
            import traceback
            traceback.print_exc()
            return None


def main():
    parser = argparse.ArgumentParser(
        description="Orchestrate complete CoSAI risk assessment workflow"
    )
    parser.add_argument("--target", required=True, help="Target to analyze")
    parser.add_argument("--output-dir", default="./risk-assessment-output",
                        help="Output directory for results")
    parser.add_argument("--offline", action="store_true",
                        help="Use bundled schemas (offline mode)")
    parser.add_argument("--skip-schemas", action="store_true",
                        help="Skip schema fetching (use cached)")
    parser.add_argument("--persona", default="both",
                        help="Persona to analyze: ModelCreator, ModelConsumer, or both")
    parser.add_argument("--format", default="markdown",
                        help="Report format: markdown, html, json")

    args = parser.parse_args()

    # Validate target
    target_path = Path(args.target)
    if not target_path.exists() and not isinstance(args.target, str):
        print(f"❌ Target not found: {args.target}")
        print("ℹ️  Please specify valid file, directory, or system description")
        sys.exit(1)

    orchestrator = RiskAssessmentOrchestrator(
        target=target_path,
        output_dir=Path(args.output_dir),
        offline=args.offline
    )

    success = orchestrator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
