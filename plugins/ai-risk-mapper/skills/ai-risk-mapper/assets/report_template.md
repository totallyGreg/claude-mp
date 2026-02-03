# AI Security Risk Assessment Report

**System Name:** {{SYSTEM_NAME}}
**Assessment Date:** {{ASSESSMENT_DATE}}
**Assessor:** {{ASSESSOR_NAME}}
**Framework:** CoSAI Risk Map (Coalition for Secure AI)
**Report Version:** {{REPORT_VERSION}}

---

## Executive Summary

This report documents security risks identified in **{{SYSTEM_NAME}}** using the CoSAI Risk Map framework. The assessment identified **{{TOTAL_RISKS}}** risks requiring attention.

### Risk Distribution

| Severity | Count | Priority |
|----------|-------|----------|
| Critical | {{CRITICAL_COUNT}} | Immediate action required |
| High     | {{HIGH_COUNT}} | Prompt remediation needed |
| Medium   | {{MEDIUM_COUNT}} | Planned mitigation required |
| Low      | {{LOW_COUNT}} | Monitoring recommended |

### Key Findings

{{KEY_FINDINGS}}

---

## System Overview

**System Type:** {{SYSTEM_TYPE}}
**Primary Persona:** {{PRIMARY_PERSONA}}
**Lifecycle Stages:** {{LIFECYCLE_STAGES}}
**AI Components:** {{AI_COMPONENTS}}

### Architecture Summary

{{ARCHITECTURE_DESCRIPTION}}

---

## Risk Assessment Methodology

This assessment follows the CoSAI Risk Map framework, which organizes AI security across four lifecycle domains:

1. **Data** - Data sources, processing, training data, storage
2. **Infrastructure** - Model frameworks, storage, serving infrastructure
3. **Model** - Model weights, evaluation, training processes
4. **Application** - Application layer, I/O handling, agent components

### Assessment Scope

- **Components Analyzed:** {{COMPONENTS_ANALYZED}}
- **Personas Assessed:** {{PERSONAS_ASSESSED}}
- **Lifecycle Coverage:** {{LIFECYCLE_COVERAGE}}

---

## Identified Risks

{{RISK_SECTIONS}}

---

## Control Recommendations

### Immediate Actions (Critical/High Risks)

{{IMMEDIATE_ACTIONS}}

### Planned Mitigations (Medium Risks)

{{PLANNED_MITIGATIONS}}

### Ongoing Monitoring (Low Risks)

{{ONGOING_MONITORING}}

---

## Compliance Mapping

This assessment aligns with the following security frameworks:

### MITRE ATLAS
{{MITRE_ATLAS_MAPPING}}

### NIST AI RMF
{{NIST_MAPPING}}

### OWASP Top 10 for LLM
{{OWASP_MAPPING}}

---

## Implementation Roadmap

### Phase 1: Critical Risk Mitigation (Weeks 1-2)
{{PHASE_1_TASKS}}

### Phase 2: High Risk Remediation (Weeks 3-6)
{{PHASE_2_TASKS}}

### Phase 3: Medium Risk Planning (Weeks 7-12)
{{PHASE_3_TASKS}}

### Phase 4: Continuous Monitoring (Ongoing)
{{PHASE_4_TASKS}}

---

## Appendix A: Risk Details

{{DETAILED_RISK_DESCRIPTIONS}}

---

## Appendix B: Control Catalog

{{CONTROL_CATALOG}}

---

## References

- [CoSAI Risk Map Framework](https://github.com/cosai-oasis/secure-ai-tooling)
- [MITRE ATLAS](https://atlas.mitre.org/)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)

---

**Report Generated:** {{GENERATION_TIMESTAMP}}
**Tool:** ai-risk-mapper skill for Claude Code
**Framework Version:** CoSAI Risk Map {{FRAMEWORK_VERSION}}
