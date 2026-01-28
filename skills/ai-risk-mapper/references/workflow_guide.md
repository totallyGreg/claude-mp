# AI Risk Mapper - Detailed Workflow Guide

Reference for advanced procedures, customization, and detailed orchestrator workflow patterns.

## Orchestrator Workflow Pattern

The orchestrator (`scripts/orchestrate_risk_assessment.py`) handles three key phases:

### Phase 1: Schema Availability

Ensures CoSAI framework data is available:

1. **Try Network Fetch** - Attempt to download latest schemas
   ```bash
   uv run scripts/fetch_cosai_schemas.py
   ```
   - Downloads 5 YAML data files + 5 JSON schema files
   - Caches to `~/.cosai-cache/`
   - Options: `--force` (re-download), `--cache-dir PATH` (custom location)

2. **Network Failure** - If fetch fails (SSL, connectivity):
   - Orchestrator automatically falls back to bundled schemas
   - No user intervention required
   - Workflow continues with cached framework data

3. **Offline Mode** - Start with bundled schemas:
   ```bash
   uv run scripts/orchestrate_risk_assessment.py --target <path> --offline
   ```

### Phase 2: Risk Analysis

Analyzes target for applicable risks using CoSAI framework:

```bash
uv run scripts/analyze_risks.py \
  --target /path/to/codebase \
  --persona ModelConsumer \
  --lifecycle Application \
  --severity-filter Critical \
  --output json > analysis_results.json
```

**Key Parameters:**
- `--target PATH` - File, directory, or system description (required)
- `--persona` - ModelCreator or ModelConsumer (optional filter)
- `--lifecycle` - Data, Infrastructure, Model, or Application (optional filter)
- `--severity-filter` - Critical, High, Medium, Low (optional filter)
- `--output` - text, json, yaml (default: text)

**Analysis Process:**
1. Loads CoSAI risk catalog (25+ risks) from cache/network
2. Analyzes target for risk indicators
3. Assigns severity based on impact and likelihood
4. Maps risks to relevant controls
5. Outputs structured assessment

**Output Structure:**
```json
[
  {
    "risk_id": "[PIJ] Prompt Injection",
    "severity": "Critical",
    "confidence": "high",
    "applicable_personas": ["ModelConsumer"],
    "applicable_lifecycle": ["Application"],
    "rationale": "...",
    "relevant_controls": ["controlInputValidation", "..."]
  }
]
```

### Phase 3: Report Generation

Creates comprehensive assessment reports:

```bash
uv run scripts/generate_report.py \
  --analysis analysis_results.json \
  --output ai_security_assessment.md \
  --format markdown \
  --executive-summary \
  --include-controls
```

**Key Parameters:**
- `--analysis FILE` - JSON from Phase 2 (required)
- `--output FILE` - Output report path (required)
- `--format` - markdown, html, or json (default: markdown)
- `--executive-summary` - Include executive summary
- `--include-controls` - Add control recommendations
- `--include-examples` - Add risk examples and case studies

**Report Contents:**
- Executive summary with risk distribution
- Risk statistics by category and lifecycle stage
- Detailed risk descriptions grouped by severity
- Recommended controls and implementation guidance
- Compliance mappings (MITRE ATLAS, NIST, OWASP, STRIDE)

## Detailed Workflow for Manual Customization

Use this when you need fine-grained control over analysis parameters or when automation is unavailable.

### Step 1: Gather System Information

Use the **System Profile Form** from `references/FORMS.md`:

1. **Basic Information**
   - System name and type (e.g., "Customer Support AI Chatbot")
   - Organization, assessment date, assessor name

2. **Persona Identification** (see `references/personas_guide.md`)
   - **ModelCreator**: Train/tune models, secure training infrastructure
   - **ModelConsumer**: Deploy pre-trained models in applications
   - Both: If organization does both

3. **Lifecycle Coverage** (see `references/cosai_overview.md`)
   - Which stages apply: Data, Infrastructure, Model, Application
   - Example: RAG system covers Infrastructure + Application

4. **AI Components Inventory**
   - Data sources and processing pipelines
   - Model storage and serving infrastructure
   - Application layer and orchestration

**Example Profile:**
```yaml
system_profile:
  basic_info:
    system_name: "RAG-powered Documentation Assistant"
    system_type: "LLM application with vector search"
    organization: "Tech Company"
    date: "2026-01-28"
  personas:
    primary_persona: "ModelConsumer"
  lifecycle_stages:
    - Infrastructure
    - Application
  ai_components:
    model_serving: ["OpenAI API"]
    application_layer: ["Web interface", "Vector database"]
    orchestration: ["RAG pipeline", "Tool calling"]
```

### Step 2: Review Risk Applicability

**Validate Risk Findings:**
1. Review each identified risk for accuracy
2. Remove false positives based on system architecture
3. Add manually identified risks not caught by automation

**Adjust Severity Ratings:**
- Consider organizational context and asset criticality
- Factor in existing controls and mitigations
- Assess likelihood based on threat model

**Document Evidence** (from `references/FORMS.md`):
- Record evidence, assumptions, and rationale
- Link to specific code locations or architecture diagrams
- Use Risk Documentation Form

### Step 3: Identify and Plan Controls

Map risks to controls for implementation:

**Control Categories** (from `references/FORMS.md`):

- **Data Controls** (Data lifecycle)
  - Training Data Sanitization
  - Data Provenance Tracking
  - Privacy-Enhancing Techniques

- **Infrastructure Controls** (Infrastructure lifecycle)
  - Model Integrity Management
  - Access Controls
  - Vulnerability Management
  - Supply Chain Verification

- **Model Controls** (Model lifecycle)
  - Adversarial Training
  - Model Evaluation
  - Red Teaming
  - Robustness Testing

- **Application Controls** (Application lifecycle)
  - Input Validation and Sanitization
  - Output Filtering
  - Prompt Guardrails
  - Agent Permissions

- **Assurance Controls** (All stages)
  - Security Monitoring
  - Incident Response
  - Logging and Audit

- **Governance Controls** (Organization-wide)
  - Risk Management
  - Security Training
  - Compliance Management

**Prioritize for Implementation:**
1. **Critical/High severity** → Implement immediately
2. **Medium severity** → Plan for upcoming sprints
3. **Low severity** → Include in backlog

**Track Implementation** (from `references/FORMS.md`):
```yaml
control_implementation:
  control_info:
    control_id: "controlInputValidationAndSanitization"
    control_title: "Input Validation and Sanitization"
  implementation:
    status: "In Progress"
    priority: "Critical"
    owner: "Security Team"
    target_date: "2024-02-15"
```

## Advanced Customization Patterns

### Custom Risk Analysis

Extend or customize risk detection:

1. **Add Organization-Specific Risks**
   - Follow CoSAI risk schema from `references/schemas_reference.md`
   - Assign custom risk IDs and categories
   - Map to relevant controls

2. **Adjust Severity Criteria**
   - Modify `analyze_risks.py` severity inference logic
   - Consider organization-specific impact factors
   - Integrate with existing risk frameworks

3. **Integrate with CI/CD**
   - Run analysis on every deployment
   - Block deployments with critical risks
   - Track risk trends over time

### Automated Monitoring

Set up continuous risk assessment:

```bash
# Schedule periodic assessments
cron: 0 0 * * 0 uv run scripts/analyze_risks.py --target /app --output weekly_scan.json

# Alert on new critical risks
uv run scripts/analyze_risks.py \
  --target /app \
  --severity-filter Critical \
  --output json | notify_team.sh
```

### Integration with Security Tools

Combine ai-risk-mapper with:
- **SAST tools** - Augment code analysis with AI-specific checks
- **Dependency scanners** - Flag ML library vulnerabilities
- **Penetration testing** - Guide AI security testing
- **SIEM** - Feed risk data into monitoring

## Understanding the Framework

### CoSAI Concepts

For comprehensive framework knowledge, see `references/cosai_overview.md`:

**Key Concepts:**
1. **Components** - Building blocks of AI systems (e.g., Data Sources, The Model, Application)
2. **Risks** - Security threats (e.g., Data Poisoning, Prompt Injection, Model Exfiltration)
3. **Controls** - Mitigations (e.g., Input Validation, Adversarial Training, Access Controls)
4. **Personas** - Roles (Model Creator, Model Consumer)

**Four Lifecycle Domains:**
- **Data**: Training data collection, validation, storage
- **Infrastructure**: Model storage, serving, dependencies
- **Model**: Development, training, evaluation
- **Application**: Deployment, inference, user interfaces

### Personas and Responsibilities

See `references/personas_guide.md` for detailed definitions:

**Model Creator** Responsibilities:
- Train and tune models
- Secure training data and infrastructure
- Implement model-level controls
- Provide security documentation to consumers

**Model Consumer** Responsibilities:
- Deploy models in applications
- Secure application layer and user inputs
- Implement runtime controls
- Monitor model behavior

### Schema Structure

See `references/schemas_reference.md` for complete data structures:

- **risks.schema.json** - 25+ risk definitions with categories, impacts, mappings
- **controls.schema.json** - 30+ controls with implementation guidance
- **components.schema.json** - 19 AI system components with dependencies
- **personas.schema.json** - Role definitions and responsibilities

## Compliance Mapping

CoSAI integrates with established security frameworks:

**MITRE ATLAS** - Adversarial Threat Landscape for AI Systems
- Maps AI-specific attack techniques
- Links risks to ATT&CK-style tactics
- Provides attack scenario examples

**NIST AI RMF** - AI Risk Management Framework
- Aligns with NIST governance model
- Maps to RMF functions (Govern, Map, Measure, Manage)
- Supports compliance documentation

**OWASP Top 10 for LLM** - LLM Application Security
- Cross-references LLM-specific vulnerabilities
- Provides web application security context
- Links to OWASP testing methodologies

**STRIDE** - Threat Modeling
- Maps to STRIDE categories (Spoofing, Tampering, Repudiation, etc.)
- Supports Microsoft threat modeling processes
- Enables threat model documentation

**Use mappings for:**
- Demonstrating compliance with multiple frameworks
- Communicating risks to different stakeholders
- Integrating with existing security programs
- Meeting audit and certification requirements

## Verification and Testing

After implementing controls:

1. **Verify installation** - Confirm control is active
2. **Test effectiveness** - Validate risk mitigation
3. **Document results** - Record verification evidence
4. **Monitor ongoing** - Ensure sustained effectiveness

## Implementation Phases

**Phase 1: Critical Risk Mitigation** (Immediate)
- Address risks with "Critical" severity
- Implement must-have controls
- Verify effectiveness

**Phase 2: High Risk Remediation** (Short-term, 1-3 months)
- Tackle "High" severity risks
- Deploy recommended controls
- Establish monitoring

**Phase 3: Medium Risk Planning** (Mid-term, 3-6 months)
- Plan mitigation for "Medium" risks
- Design control implementations
- Schedule deployments

**Phase 4: Continuous Monitoring** (Ongoing)
- Monitor for new risks
- Update risk assessments as system evolves
- Track control effectiveness

**Reassessment Triggers:**
- Major architecture changes
- New AI components or models
- Security incidents
- Regulatory updates
- Quarterly or bi-annual schedule
