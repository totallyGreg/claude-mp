---
name: ai-risk-mapper
description: This skill should be used when identifying, analyzing, and mitigating security risks in Artificial Intelligence systems using the CoSAI (Coalition for Secure AI) Risk Map framework. Use when users ask to "assess AI security risks", "analyze AI system threats", "map risks to controls", "run a risk assessment", "check compliance with MITRE ATLAS", "generate a CoSAI report", or "profile persona risks". Supports LLM applications, ML pipelines, model training/serving infrastructure, and compliance reporting aligned with MITRE ATLAS, NIST AI RMF, OWASP Top 10 for LLM, STRIDE, and ISO 22989 frameworks. Do NOT use for general software security scanning without an AI/ML component (use standard SAST/DAST tools instead).
metadata:
  version: "5.2.0"
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

For ad-hoc queries, threat modeling, or compliance mapping, use the CLI scripts. All support `--offline` flag for bundled schema usage.

| Purpose | Script |
|---------|--------|
| Search risks by keyword | `uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_risk_search.py "injection"` |
| Search controls by keyword | `uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_control_search.py "training"` |
| Get controls for a risk | `uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_controls_for_risk.py DP` |
| Get persona risk profile | `uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_persona_profile.py personaModelProvider` |
| Assess control coverage | `uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_gap_analysis.py DP --implemented controlTrainingDataSanitization` |
| Get framework mappings | `uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_framework_map.py PIJ --framework mitre-atlas` |

See `references/exploration_guide.md` for entity IDs, query patterns, and the core analyzer API.

## Error Handling & Fallback

**Network/SSL Failures:** Orchestrator automatically switches to bundled offline schemas — workflow continues without user intervention.

**Manual offline mode:**
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/orchestrate_risk_assessment.py --target <path> --offline
```

**Missing Target:** Ask user: "Please specify a file, directory path, or brief system description to analyze"

## Reference Pointers

| Topic | Reference |
|-------|-----------|
| Framework fundamentals | `references/cosai_overview.md` |
| Persona definitions | `references/personas_guide.md` |
| Risk & schema structures | `references/schemas_reference.md` |
| Data collection forms | `references/forms.md` |
| Workflow procedures | `references/workflow_guide.md` |
| Interactive exploration | `references/exploration_guide.md` |
| Usage examples | `references/usage_examples.md` |

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
