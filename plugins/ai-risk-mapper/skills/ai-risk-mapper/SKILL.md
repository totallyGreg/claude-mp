---
name: ai-risk-mapper
description: This skill should be used when identifying, analyzing, and mitigating security risks in Artificial Intelligence systems using the CoSAI (Coalition for Secure AI) Risk Map framework. Use when assessing AI system security, conducting risk analysis for LLM applications, ML pipelines, model training/serving infrastructure, or generating compliance reports aligned with MITRE ATLAS, NIST AI RMF, OWASP Top 10 for LLM, and STRIDE frameworks. Supports both automated assessments and interactive exploration with 30+ query methods.
metadata:
  version: "4.0.1"
  author: J. Greg Williams
compatibility: Requires python3 and uv for script execution
license: Apache 2.0
---

# AI Risk Mapper

## When Invoked

### Automated Assessment

For requests like "Analyze security risks in [target]" or "Generate a CoSAI risk assessment":

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/orchestrate_risk_assessment.py \
  --target <user_specified_target> \
  --output-dir ./risk-assessment-output
```

The orchestrator automatically:
1. Fetches/caches CoSAI schemas (or uses offline fallback)
2. Analyzes target for applicable risks
3. Generates comprehensive assessment report
4. Presents findings to user

### Interactive Exploration

For ad-hoc queries, threat modeling, or compliance mapping:

| Purpose | Script |
|---------|--------|
| Search risks by keyword | `uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_risk_search.py "injection"` |
| Search controls by keyword | `uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_control_search.py "training"` |
| Get controls for a risk | `uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_controls_for_risk.py DP` |
| Get persona risk profile | `uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_persona_profile.py personaModelCreator` |
| Assess control coverage | `uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_gap_analysis.py DP --implemented controlTrainingDataSanitization` |
| Get framework mappings | `uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_framework_map.py PIJ --framework mitre-atlas` |

All scripts support `--offline` flag for bundled schema usage.

See `references/exploration_guide.md` for complete API reference, query patterns, and entity IDs.

## Error Handling & Fallback

**Network/SSL Failures:**
- Orchestrator automatically switches to bundled offline schemas
- Workflow continues without user intervention

**Manual offline mode:**
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/orchestrate_risk_assessment.py --target <path> --offline
```

**Missing Target:**
- Ask user: "Please specify a file, directory path, or brief system description to analyze"
- Example targets: `/path/to/codebase`, `./architecture.md`, `"RAG pipeline description"`

## Manual Workflow (For Customization)

### Step 1: Ensure Schemas Available

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/fetch_cosai_schemas.py
```

### Step 2: Custom Filtered Analysis

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/analyze_risks.py \
  --target /path/to/codebase \
  --persona ModelConsumer \
  --lifecycle Application \
  --severity-filter Critical \
  --output json > analysis.json
```

**Filter options:**
- `--persona ModelCreator|ModelConsumer`
- `--lifecycle Data|Infrastructure|Model|Application`
- `--severity-filter Critical|High|Medium|Low`
- `--output text|json|yaml`
- `--offline` for bundled schemas

### Step 3: Generate Custom Reports

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/generate_report.py \
  --analysis analysis.json \
  --output ai_security_assessment.md \
  --format markdown \
  --executive-summary \
  --include-controls
```

## Framework Reference Pointers

| Topic | Reference |
|-------|-----------|
| Framework fundamentals | `references/cosai_overview.md` |
| Persona definitions | `references/personas_guide.md` |
| Risk & schema structures | `references/schemas_reference.md` |
| Data collection forms | `references/forms.md` |
| Workflow procedures | `references/workflow_guide.md` |
| Interactive exploration | `references/exploration_guide.md` |

## Usage Examples

### Example 1: Automated Assessment

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

### Example 2: Interactive Threat Modeling

User: "What risks apply to prompt injection attacks?"

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_risk_search.py "injection" --offline
```

Output shows PIJ, ADI, RVP risks with descriptions, controls, and framework mappings.

### Example 3: Gap Analysis

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

### Example 4: Compliance Mapping

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

## Resources

**Automation Scripts:** (via `${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/`)
- `orchestrate_risk_assessment.py` - Workflow orchestrator
- `fetch_cosai_schemas.py` - Schema downloader
- `analyze_risks.py` - Risk identification engine
- `generate_report.py` - Report generator
- `core_analyzer.py` - Core query API (30+ methods)

**Interactive CLI:** (via `${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/`)
- `cli_risk_search.py` - Search risks
- `cli_control_search.py` - Search controls
- `cli_controls_for_risk.py` - Controls for risk
- `cli_persona_profile.py` - Persona profiles
- `cli_gap_analysis.py` - Gap analysis
- `cli_framework_map.py` - Framework mappings

**Bundled Assets:** (via `${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/`)
- `assets/cosai-schemas/` - Offline schema cache
- `assets/report_template.md` - Report template

**External Framework:** https://github.com/cosai-oasis/secure-ai-tooling
