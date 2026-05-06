---
last_verified: 2026-05-06
sources:
  - type: github
    repo: "cosai-oasis/secure-ai-tooling"
    paths: ["risk-map/yaml/risks.yaml", "risk-map/yaml/controls.yaml"]
    description: "CoSAI risk IDs, control IDs, and framework mappings used in examples"
---

# Usage Examples

## Automated Assessment

User: "Analyze security risks in my AI chatbot codebase"

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/orchestrate_risk_assessment.py \
  --target ./chatbot-src \
  --output-dir ./risk-output
```

Output:
```
✓ Fetched CoSAI schemas
✓ Identified 14 applicable risks
✓ Generated report: ai_security_assessment.md
```

## Interactive Threat Modeling

User: "What risks apply to prompt injection attacks?"

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_risk_search.py "injection" --offline
```

Output shows PIJ, ADI, RVP risks with descriptions, controls, and framework mappings.

## Gap Analysis

User: "What controls am I missing for Data Poisoning risk?"

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_gap_analysis.py DP --implemented controlTrainingDataSanitization --offline
```

Output:
```
Gap Analysis: [DP] Data Poisoning
Coverage: 20% (1 of 5 controls)

Missing Controls:
  ✗ Model and Data Integrity Management
  ✗ Model and Data Access Controls
  ✗ Secure-by-Default ML Tooling
  ✗ Model and Data Inventory Management
```

## Compliance Mapping

User: "Map prompt injection to MITRE ATLAS"

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_framework_map.py PIJ --framework mitre-atlas --offline
```

Output:
```
Risk: [PIJ] Prompt Injection
MITRE-ATLAS Mappings:
  - AML.T0051
```

## Custom Filtered Analysis

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/analyze_risks.py \
  --target /path/to/codebase \
  --persona ApplicationDeveloper \
  --lifecycle Application \
  --severity-filter Critical \
  --output json > analysis.json
```

**Filter options:**
- `--persona ModelProvider|DataProvider|PlatformProvider|ModelServing|AgenticProvider|ApplicationDeveloper|Governance|EndUser`
- `--lifecycle Data|Infrastructure|Model|Application`
- `--severity-filter Critical|High|Medium|Low`
- `--output text|json|yaml`
- `--offline` for bundled schemas

## Custom Report Generation

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/generate_report.py \
  --analysis analysis.json \
  --output ai_security_assessment.md \
  --format markdown \
  --executive-summary \
  --include-controls
```
