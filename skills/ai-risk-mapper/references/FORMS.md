# AI Risk Mapper Forms

This document contains structured forms for collecting information during AI security risk assessments.

## System Profile Form

```yaml
system_profile:
  basic_info:
    system_name: ""
    system_type: ""  # e.g., "LLM-based chatbot", "Computer vision pipeline", "ML training platform"
    organization: ""
    assessment_date: ""
    assessor_name: ""

  personas:
    primary_persona: ""  # ModelCreator or ModelConsumer
    secondary_persona: ""  # Optional: if organization has both roles

  lifecycle_stages:
    - Data
    - Infrastructure
    - Model
    - Application

  ai_components:
    data_sources: []
    data_processing: []
    training_infrastructure: []
    model_storage: []
    model_serving: []
    application_layer: []
    orchestration: []

  architecture:
    description: ""
    diagram_path: ""  # Optional: path to architecture diagram
```

## Risk Assessment Checklist

```yaml
risk_assessment:
  target:
    type: ""  # codebase, architecture_doc, system_description
    path: ""
    description: ""

  scope:
    include_lifecycle_stages: []
    exclude_lifecycle_stages: []
    persona_filter: ""
    severity_threshold: ""  # minimum severity to report

  analysis_options:
    automated_scanning: true
    manual_review: true
    code_analysis: true
    dependency_scanning: true
    configuration_review: true
```

## Risk Documentation Form

```yaml
risk_entry:
  identification:
    risk_id: ""  # CoSAI risk ID (e.g., DP, PIJ, MEV)
    custom_id: ""  # Optional: organization-specific ID
    title: ""

  assessment:
    severity: ""  # Critical, High, Medium, Low
    likelihood: ""  # High, Medium, Low
    impact: ""  # High, Medium, Low
    confidence: ""  # High, Medium, Low

  context:
    applicable_personas: []
    lifecycle_stages: []
    affected_components: []
    attack_vectors: []

  details:
    description: ""
    rationale: ""
    evidence: ""
    assumptions: []

  controls:
    recommended_controls: []
    existing_controls: []
    control_gaps: []
```

## Control Implementation Form

```yaml
control_implementation:
  control_info:
    control_id: ""  # CoSAI control ID
    control_title: ""
    category: ""  # Data, Infrastructure, Model, Application, Assurance, Governance

  implementation:
    status: ""  # Not Started, In Progress, Implemented, Verified
    priority: ""  # Critical, High, Medium, Low
    owner: ""
    target_date: ""
    actual_date: ""

  details:
    implementation_notes: ""
    configuration: ""
    verification_method: ""
    verification_date: ""

  effectiveness:
    risks_mitigated: []
    residual_risks: []
    monitoring_required: true
    monitoring_method: ""
```

## Self-Assessment Questionnaire

Use this structured questionnaire to evaluate your AI system's security posture:

```yaml
self_assessment:
  metadata:
    assessment_id: ""
    system_name: ""
    date: ""
    assessor: ""

  data_security:
    - question: "Are all data sources validated for integrity and provenance?"
      answer: ""  # Yes, No, Partial, N/A
      evidence: ""
      notes: ""

    - question: "Is training data sanitized to detect and remove poisoned data?"
      answer: ""
      evidence: ""
      notes: ""

  infrastructure_security:
    - question: "Are model artifacts cryptographically signed and integrity-verified?"
      answer: ""
      evidence: ""
      notes: ""

  application_security:
    - question: "Are all user inputs validated and sanitized before model processing?"
      answer: ""
      evidence: ""
      notes: ""
```

For complete self-assessment questions, see the CoSAI `self-assessment.yaml` schema.
