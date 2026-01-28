---
name: ai-risk-mapper
description: This skill should be used when identifying, analyzing, and mitigating security risks in Artificial Intelligence systems using the CoSAI (Coalition for Secure AI) Risk Map framework. Use when assessing AI system security, conducting risk analysis for LLM applications, ML pipelines, model training/serving infrastructure, or generating compliance reports aligned with MITRE ATLAS, NIST AI RMF, OWASP Top 10 for LLM, and STRIDE frameworks. Applicable to both Model Creator and Model Consumer personas across Data, Infrastructure, Model, and Application lifecycle stages.
metadata:
  version: "2.0.0"
  author: J. Greg Williams
compatibility: Requires python3 and uv for script execution
license: Apache 2.0
---

# AI Risk Mapper

## When Invoked

When this skill is triggered by requests like:
- "Analyze the security risks in [file/directory/system]"
- "Assess AI security for [target]"
- "Generate a CoSAI risk assessment"

**Immediately execute the automated workflow:**

```bash
uv run scripts/orchestrate_risk_assessment.py \
  --target <user_specified_target> \
  --output-dir ./risk-assessment-output
```

The orchestrator automatically:
1. Fetches/caches CoSAI schemas (or uses offline fallback on network failure)
2. Analyzes target for applicable risks
3. Generates comprehensive assessment report
4. Presents findings to user

See `references/workflow_guide.md` for orchestrator workflow details.

## Error Handling & Fallback

**Network/SSL Failures:**
If schema fetching fails (SSL errors, connectivity issues):
- Orchestrator automatically switches to bundled offline schemas
- Workflow continues without user intervention
- Assessment completes with cached framework data

Example:
```bash
# Orchestrator handles this automatically, but if manual recovery needed:
uv run scripts/orchestrate_risk_assessment.py --target <path> --offline
```

**Analysis Failures:**
If risk analysis encounters errors:
1. Check error output for details (missing target, parsing errors, etc.)
2. Verify target path exists and is accessible
3. Ask user to specify target (file path, directory, or system description)
4. For customization needs, see "Manual Workflow" section below

**Handling Missing Target:**
- Error: `Target not found`
- Ask user: "Please specify a file, directory path, or brief system description to analyze"
- Example targets: `/path/to/codebase`, `./architecture.md`, `"RAG pipeline description"`

## Manual Workflow (For Customization)

Use this when you need fine-grained control or the orchestrator doesn't meet specific needs.

### Step 1: Ensure Schemas Available

Try fetching fresh schemas:
```bash
uv run scripts/fetch_cosai_schemas.py
```

If network fails, use bundled offline mode:
```bash
uv run scripts/orchestrate_risk_assessment.py --offline
```

### Step 2: Analyze Specific Risks

For custom analysis with filters:

```bash
uv run scripts/analyze_risks.py \
  --target /path/to/codebase \
  --persona ModelConsumer \
  --lifecycle Application \
  --severity-filter Critical \
  --output json > analysis.json
```

**Useful filter combinations:**
- `--persona ModelCreator` - For systems building/training models
- `--persona ModelConsumer` - For systems deploying models
- `--lifecycle Data` - Focus on training data risks
- `--lifecycle Application` - Focus on deployment/inference risks
- `--severity-filter Critical` - Show only critical risks
- `--output yaml` - YAML format for parsing

### Step 3: Generate Custom Reports

```bash
uv run scripts/generate_report.py \
  --analysis analysis.json \
  --output ai_security_assessment.md \
  --format markdown \
  --executive-summary \
  --include-controls
```

For detailed workflow guidance including system profiling, risk review, control planning, and monitoring setup, see `references/workflow_guide.md`.

## Framework Reference Pointers

When users need to understand CoSAI concepts, point to existing documentation:

**Framework Fundamentals** (`references/cosai_overview.md`)
- Framework structure and methodology
- Four lifecycle domains (Data, Infrastructure, Model, Application)
- 19 AI system components with dependencies
- 25+ security risks and categories

**Persona Definitions** (`references/personas_guide.md`)
- Model Creator responsibilities (training, infrastructure, model security)
- Model Consumer responsibilities (deployment, application, runtime)
- Hybrid organization guidance

**Risk & Schema Structures** (`references/schemas_reference.md`)
- Complete risk definitions with examples
- Control schemas and implementation guidance
- Component dependencies and relationships
- Validation rules and mappings

**Data Collection** (`references/FORMS.md`)
- System Profile Form for gathering system information
- Risk Documentation Form for recording findings
- Control Implementation Form for tracking deployment
- Self-Assessment Questionnaire for structured evaluation

## Usage Examples

### Example 1: Automated Assessment (Happy Path)

User: "Analyze security risks in my AI chatbot codebase"

```bash
uv run scripts/orchestrate_risk_assessment.py \
  --target ./chatbot-src \
  --output-dir ./risk-output
```

Output:
```
✓ Fetched CoSAI schemas
✓ Identified 14 applicable risks
✓ Generated report: ai_security_assessment.md
```

Report includes risks like Prompt Injection, Model Exfiltration, Sensitive Data Disclosure with severity levels and recommended controls.

### Example 2: SSL Failure with Automatic Fallback

User: "Assess security for this RAG pipeline architecture"

Network/SSL error occurs (corporate proxy, firewall):

```
⚠️  Schema fetch failed: SSL error
✓ Using bundled schemas (offline mode)
✓ Identified 12 applicable risks
✓ Generated report
```

Workflow completes successfully with bundled offline schemas. No user intervention required.

### Example 3: Manual Workflow for Fine-Grained Control

User: "I need to analyze only Application-layer risks for a Model Consumer"

```bash
# Step 1: Ensure schemas available
uv run scripts/fetch_cosai_schemas.py

# Step 2: Custom filtered analysis
uv run scripts/analyze_risks.py \
  --target ./my-app \
  --persona ModelConsumer \
  --lifecycle Application \
  --severity-filter Critical \
  --output json > findings.json

# Step 3: Generate custom report
uv run scripts/generate_report.py \
  --analysis findings.json \
  --output focused_assessment.md \
  --include-controls
```

Result: Focused assessment showing only Application-layer risks relevant to Model Consumer, with recommended controls for each.

## Resources

**Automation Scripts** (auto-executed by orchestrator):
- `scripts/orchestrate_risk_assessment.py` - Workflow orchestrator with automatic schema fallback
- `scripts/fetch_cosai_schemas.py` - CoSAI schema downloader with offline fallback
- `scripts/analyze_risks.py` - Risk identification and filtering engine
- `scripts/generate_report.py` - Multi-format report generator

**Bundled Assets**:
- `assets/cosai-schemas/` - Offline CoSAI schema cache (used as fallback)
- `assets/report_template.md` - Report template for customization

**Reference Documentation**:
- `references/cosai_overview.md` - Framework methodology and structure
- `references/personas_guide.md` - Role and responsibility definitions
- `references/schemas_reference.md` - Data structure specifications
- `references/FORMS.md` - Data collection and documentation templates
- `references/workflow_guide.md` - Detailed workflow procedures and customization patterns

**External Framework**: https://github.com/cosai-oasis/secure-ai-tooling
