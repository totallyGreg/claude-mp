---
name: ai-risk-mapper
description: This skill should be used when identifying, analyzing, and mitigating security risks in Artificial Intelligence systems using the CoSAI (Coalition for Secure AI) Risk Map framework. Use when assessing AI system security, conducting risk analysis for LLM applications, ML pipelines, model training/serving infrastructure, or generating compliance reports aligned with MITRE ATLAS, NIST AI RMF, OWASP Top 10 for LLM, and STRIDE frameworks. Applicable to both Model Creator and Model Consumer personas across Data, Infrastructure, Model, and Application lifecycle stages.
metadata:
  version: "1.0.0"
  author: J. Greg Williams
compatibility: Requires python3 and uv for script execution
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

**Handling Errors:**
- Network/SSL failures → Automatic fallback to bundled schemas
- Analysis failures → Check error output and follow manual workflow below
- Missing target → Ask user to specify target path or description

---

## Overview

Conduct comprehensive security risk assessments for AI systems using the CoSAI Risk Map framework. This skill automates the identification of 25+ AI-specific security risks, recommends mitigation controls, and generates compliance-ready reports aligned with industry standards.

## When to Use This Skill

**Trigger this skill when:**
- Assessing security risks in LLM-based applications, chatbots, or AI agents
- Evaluating ML model training pipelines for security vulnerabilities
- Analyzing AI inference/deployment infrastructure for threats
- Generating AI security compliance reports for NIST, MITRE ATLAS, or OWASP frameworks
- Planning security controls for AI system development or deployment
- Conducting security reviews of RAG pipelines, vector databases, or orchestration layers
- Documenting AI security posture for audits or certifications

**Risk categories covered:**
- Data Poisoning, Model Exfiltration, Prompt Injection, Sensitive Data Disclosure
- Model Evasion, Supply Chain Risks, Adversarial Inputs, and 20+ additional threats

## Workflow Decision Tree

Start here to determine the appropriate workflow:

```
Are you performing a new risk assessment?
├─ YES → Go to "Complete Risk Assessment Workflow"
├─ NO →
    ├─ Need to understand CoSAI framework? → Go to "Learning the Framework"
    ├─ Implementing specific controls? → Go to "Control Implementation"
    └─ Generating reports from existing analysis? → Go to "Report Generation Only"
```

## Manual Workflow (For Customization)

If you need fine-grained control or the orchestrator fails, follow this step-by-step workflow:

**Note:** The automated orchestrator above handles all these steps automatically for standard assessments.

### Step 1: Prepare the Environment

**Fetch CoSAI schemas** (required for first-time use or framework updates):

```bash
uv run scripts/fetch_cosai_schemas.py
```

The script automatically handles dependencies (PyYAML for parsing CoSAI YAML schema files).

This downloads and caches:
- 5 YAML data files (risks, controls, components, personas, self-assessment)
- 5 JSON schema files for validation
- Stored in `~/.cosai-cache/` by default

**Options:**
- `--force` - Re-download even if cache exists
- `--cache-dir PATH` - Use custom cache location

**Verification:** Check cache statistics in output summary

### Step 2: Gather System Information

**Use the System Profile Form** from `references/FORMS.md` to collect:

1. **Basic Information:**
   - System name and type (e.g., "Customer Support AI Chatbot")
   - Organization and assessment date
   - Assessor name

2. **Persona Identification:**
   - Primary persona: ModelCreator or ModelConsumer
   - See `references/personas_guide.md` for detailed persona definitions:
     - **ModelCreator**: Organizations that train/tune models
     - **ModelConsumer**: Organizations that deploy pre-trained models in applications

3. **Lifecycle Coverage:**
   - Which stages apply: Data, Infrastructure, Model, Application
   - See `references/cosai_overview.md` for lifecycle stage descriptions

4. **AI Components Inventory:**
   - Data sources and processing pipelines
   - Model storage and serving infrastructure
   - Application layer and orchestration components

**Example:**
```yaml
system_profile:
  basic_info:
    system_name: "RAG-powered Documentation Assistant"
    system_type: "LLM application with vector search"
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

### Step 3: Analyze Risks

**Run automated risk analysis:**

```bash
uv run scripts/analyze_risks.py \
  --target /path/to/codebase \
  --persona ModelConsumer \
  --output json > analysis_results.json
```

**Required parameters:**
- `--target PATH` - Path to codebase, architecture doc, or system description

**Optional parameters:**
- `--persona` - Filter by ModelCreator or ModelConsumer
- `--lifecycle` - Filter by stage: Data, Infrastructure, Model, Application
- `--output` - Format: text, json, yaml (default: text)
- `--severity-filter` - Show only: Critical, High, Medium, or Low risks
- `--cache-dir` - Custom CoSAI cache location

**Analysis process:**
1. Loads CoSAI risk catalog (25+ risks) from cache
2. Analyzes target for risk indicators and applicability
3. Assigns severity levels based on impact and likelihood
4. Maps risks to relevant controls
5. Outputs structured risk assessments

**Output includes for each risk:**
- Risk ID and title (e.g., [PIJ] Prompt Injection)
- Severity level (Critical, High, Medium, Low)
- Applicable personas and lifecycle stages
- Confidence level (high, medium, low)
- Rationale for why risk applies
- Recommended controls (CoSAI control IDs)

### Step 4: Review and Refine

**Manual review steps:**

1. **Validate Risk Applicability:**
   - Review each identified risk for accuracy
   - Remove false positives based on system architecture
   - Add manually identified risks not caught by automation

2. **Adjust Severity Ratings:**
   - Consider organizational context and asset criticality
   - Factor in existing controls and mitigations
   - Assess likelihood based on threat model

3. **Document Evidence:**
   - Use Risk Documentation Form from `references/FORMS.md`
   - Record evidence, assumptions, and rationale
   - Link to specific code locations or architecture diagrams

**For detailed risk information:**
- See `references/schemas_reference.md` for complete risk schema
- Each risk includes examples, tour content, and framework mappings

### Step 5: Identify Controls

**Map risks to controls** using the analysis output:

Each identified risk includes `relevant_controls` listing applicable CoSAI control IDs.

**Control categories:**
- **Data Controls**: Training data sanitization, data provenance, PII protection
- **Infrastructure Controls**: Model storage security, access controls, supply chain verification
- **Model Controls**: Adversarial training, model evaluation, robustness testing
- **Application Controls**: Input validation, output filtering, prompt engineering, agent permissions
- **Assurance Controls**: Monitoring, logging, vulnerability management
- **Governance Controls**: Risk management, compliance, incident response

**Prioritize controls:**
1. **Critical/High severity risks** - Implement immediately
2. **Medium severity risks** - Plan for upcoming sprints
3. **Low severity risks** - Include in backlog for monitoring

**Track implementation:**
- Use Control Implementation Form from `references/FORMS.md`
- Document status, owner, target dates
- Verify effectiveness after deployment

### Step 6: Generate Report

**Create comprehensive assessment report:**

```bash
uv run scripts/generate_report.py \
  --analysis analysis_results.json \
  --output ai_security_assessment.md \
  --format markdown \
  --executive-summary \
  --include-controls
```

**Required parameters:**
- `--analysis FILE` - Input JSON from Step 3
- `--output FILE` - Output report path

**Optional parameters:**
- `--format` - markdown, html, or json (default: markdown)
- `--executive-summary` - Include executive summary section
- `--include-controls` - Add detailed control recommendations
- `--include-examples` - Add risk examples and case studies

**Report contents:**
- Executive summary with risk distribution
- Risk summary statistics by category and lifecycle
- Detailed risk descriptions grouped by severity
- Recommended controls and implementation guidance
- Compliance mappings (MITRE ATLAS, NIST, OWASP, STRIDE)
- Next steps and remediation roadmap

**Template customization:**
- Base template: `assets/report_template.md`
- Customize for organization-specific formatting
- Add branding, compliance requirements, or additional sections

### Step 7: Implement and Monitor

**Implementation phases:**

1. **Phase 1: Critical Risk Mitigation** (Immediate)
   - Address risks with "Critical" severity
   - Implement must-have controls
   - Verify effectiveness

2. **Phase 2: High Risk Remediation** (Short-term)
   - Tackle "High" severity risks
   - Deploy recommended controls
   - Establish monitoring

3. **Phase 3: Medium Risk Planning** (Mid-term)
   - Plan mitigation for "Medium" risks
   - Design control implementations
   - Schedule deployments

4. **Phase 4: Continuous Monitoring** (Ongoing)
   - Monitor for new risks
   - Update risk assessments as system evolves
   - Track control effectiveness

**Reassessment triggers:**
- Major architecture changes
- New AI components or models
- Security incidents
- Regulatory updates
- Quarterly or bi-annual schedule

## Learning the Framework

### Understanding CoSAI

For comprehensive framework knowledge:

**Start with:** `references/cosai_overview.md`
- Framework structure and methodology
- Four lifecycle domains (Data, Infrastructure, Model, Application)
- 19 AI system components
- 25+ security risks
- 30+ mitigation controls
- Persona model (Creator vs Consumer)

**Key concepts:**
1. **Components** - Building blocks of AI systems (e.g., Data Sources, The Model, Application)
2. **Risks** - Security threats (e.g., Data Poisoning, Prompt Injection, Model Exfiltration)
3. **Controls** - Mitigations (e.g., Input Validation, Adversarial Training, Access Controls)
4. **Personas** - Roles (Model Creator, Model Consumer)

### Personas and Responsibilities

**Read:** `references/personas_guide.md`

**Model Creator responsibilities:**
- Train and tune models
- Secure training data and infrastructure
- Implement model-level controls
- Provide security documentation to consumers

**Model Consumer responsibilities:**
- Deploy models in applications
- Secure application layer and user inputs
- Implement runtime controls
- Monitor model behavior

**Hybrid organizations:**
- Apply both persona controls appropriately
- Coordinate between model development and application teams
- Maintain clear responsibility boundaries

### Schema Structure

**Read:** `references/schemas_reference.md`

Understand the data structures for:
- **risks.schema.json** - 25+ risk definitions with categories, impacts, mappings
- **controls.schema.json** - 30+ controls with implementation guidance
- **components.schema.json** - 19 AI system components with dependencies
- **personas.schema.json** - Role definitions and responsibilities

**Use cases:**
- Validating custom risk data
- Extending framework for organization
- Building tooling integrations
- Automating compliance checks

## Control Implementation

### Planning Control Deployment

**For each identified risk:**

1. **Review recommended controls** from analysis output
2. **Select applicable controls** based on:
   - Organizational capabilities
   - Resource availability
   - Risk tolerance
   - Compliance requirements

3. **Use Control Implementation Form** from `references/FORMS.md`:
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

### Control Categories and Selection

**Data Controls** (for Data lifecycle stage):
- Training Data Sanitization - Detect and remove poisoned data
- Data Provenance Tracking - Verify data source integrity
- Privacy-Enhancing Techniques - Protect PII in training data

**Infrastructure Controls** (for Infrastructure stage):
- Model Integrity Management - Cryptographic signing and verification
- Access Controls - Least-privilege for model and data access
- Vulnerability Management - Secure dependencies and frameworks

**Model Controls** (for Model stage):
- Adversarial Training - Improve robustness against attacks
- Model Evaluation - Comprehensive security testing
- Red Teaming - Simulate attacks to find vulnerabilities

**Application Controls** (for Application stage):
- Input Validation and Sanitization - Block malicious inputs
- Output Filtering - Prevent sensitive data leakage
- Prompt Guardrails - Mitigate prompt injection
- Agent Permissions - Scope tool access and data exposure

**Assurance Controls** (all stages):
- Security Monitoring - Detect anomalies and attacks
- Incident Response - Handle security events
- Logging and Audit - Maintain security audit trails

**Governance Controls** (organization-wide):
- Risk Management - Document and track AI security risks
- Security Training - Educate teams on AI security
- Compliance Management - Meet regulatory requirements

### Verification and Testing

After implementing controls:

1. **Verify installation** - Confirm control is active
2. **Test effectiveness** - Validate risk mitigation
3. **Document results** - Record verification evidence
4. **Monitor ongoing** - Ensure sustained effectiveness

## Report Generation Only

Generate reports from existing analysis results without re-running assessment:

```bash
uv run scripts/generate_report.py \
  --analysis previous_analysis.json \
  --output updated_report.html \
  --format html \
  --executive-summary \
  --include-controls
```

**Use cases:**
- Different report formats for different audiences
- Updated reports with new context or findings
- Compliance-specific reports filtering by framework

## Self-Assessment

Conduct structured self-assessment using CoSAI questionnaire:

**Reference:** `references/FORMS.md` - Self-Assessment Questionnaire

**Process:**
1. Review questions across all security domains
2. Answer: Yes, No, Partial, or N/A
3. Provide evidence and notes for each answer
4. Calculate compliance percentage
5. Identify gaps and improvement areas

**Assessment domains:**
- Data Security
- Infrastructure Security
- Model Security
- Application Security
- Governance and Compliance

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

## Advanced Usage

### Custom Risk Analysis

Extend or customize risk analysis:

1. **Add organization-specific risks:**
   - Follow CoSAI risk schema from `references/schemas_reference.md`
   - Assign custom risk IDs and categories
   - Map to relevant controls

2. **Adjust severity criteria:**
   - Modify `analyze_risks.py` severity inference logic
   - Consider organization-specific impact factors
   - Integrate with existing risk frameworks

3. **Integrate with CI/CD:**
   - Run analysis on every deployment
   - Block deployments with critical risks
   - Track risk trends over time

### Automated Monitoring

Set up continuous risk monitoring:

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
- **Penetration testing** - Guide AI security testing efforts
- **Security Information and Event Management (SIEM)** - Feed risk data into monitoring

## Resources

### Scripts

**`scripts/fetch_cosai_schemas.py`** - Download and cache CoSAI framework data
- Fetches latest YAML and JSON schemas from GitHub
- Caches locally for offline use
- Validates JSON schema integrity
- Generates manifest file

**`scripts/analyze_risks.py`** - Automated risk identification and assessment
- Analyzes codebases, configs, or descriptions
- Filters by persona, lifecycle, and severity
- Outputs structured risk assessments
- Maps risks to controls

**`scripts/generate_report.py`** - Create comprehensive assessment reports
- Multiple output formats (Markdown, HTML, JSON)
- Customizable templates
- Executive summaries and detailed findings
- Compliance mapping sections

### References

**`references/cosai_overview.md`** - Framework introduction and methodology (load for framework understanding)

**`references/personas_guide.md`** - Model Creator vs Model Consumer responsibilities (load when determining persona or control ownership)

**`references/schemas_reference.md`** - JSON schema structures and validation rules (load when validating data or extending framework)

**`references/FORMS.md`** - Structured data collection templates (load when gathering system info or documenting risks)

### Assets

**`assets/report_template.md`** - Markdown report template with placeholders for customization

---

**Framework Source:** https://github.com/cosai-oasis/secure-ai-tooling
**License:** Apache 2.0
**Version:** CoSAI Risk Map (latest from repository)
