# AI Risk Mapper - Comprehensive Capability Evaluation

**Date**: 2026-01-28
**Evaluator**: Claude Code
**Scope**: Current capabilities vs. CoSAI source of truth requirements

## Executive Summary

The ai-risk-mapper skill (v2.0.0) provides foundational AI security risk assessment capabilities with automated workflow orchestration and offline resilience. However, it has **critical synchronization gaps** with the CoSAI source repository and lacks **semantic intelligence** for accurate risk detection. This evaluation identifies gaps and opportunities for improvement.

---

## 1. Current Capability Assessment

### ✅ Strengths

| Capability | Status | Details |
|-----------|--------|---------|
| **Automated Workflows** | ✓ Complete | Orchestrator handles 3-phase workflow (schema fetch → analysis → reporting) |
| **Offline Resilience** | ✓ Complete | Bundled schemas with SSL fallback; works without network |
| **Multi-Format Output** | ✓ Complete | JSON, YAML, Markdown, HTML report generation |
| **Persona Filtering** | ✓ Complete | ModelCreator/ModelConsumer persona-based analysis |
| **Lifecycle Filtering** | ✓ Complete | Data/Infrastructure/Model/Application stage filtering |
| **Framework Mapping** | ✓ Partial | References MITRE ATLAS, NIST, OWASP, STRIDE |
| **Documentation** | ✓ Good | Comprehensive SKILL.md, workflow_guide.md, reference docs |
| **Error Handling** | ✓ Good | Network failure fallback, validation, helpful error messages |

### ⚠️ Critical Gaps

| Gap | Severity | Impact | Details |
|-----|----------|--------|---------|
| **Schema Sync** | HIGH | Offline validity | Missing v2.0.0 frameworks.schema.json + metadata schemas |
| **YAML Data Sync** | HIGH | Content accuracy | Missing frameworks.yaml + persona updates (Jan 28, 2026) |
| **Keyword-Based Detection** | HIGH | Accuracy | Uses pattern matching; misses semantic risks |
| **Branch Awareness** | MEDIUM | Currency | Fetch script targets main only; unaware of develop branch |
| **Graph Validation** | MEDIUM | Confidence | No use of CoSAI's edge validation or graph generation |
| **Test Coverage** | MEDIUM | Reliability | Zero automated tests for Python scripts |
| **Visualization** | MEDIUM | Usability | No risk dashboard or visual representation |
| **Troubleshooting** | LOW | UX | Missing detailed error recovery guides |

### ⚠️ Observable Issues from CoSAI Sync

**CoSAI Repository Current State** (as of 2026-01-28):
- main: `00e6dc4` (commit: "Merge pull request #128")
- develop: 7 commits ahead of main
- Recent updates: Persona expansion (7 personas), Framework v1.0 definitions, Schema enhancements

**AI-Risk-Mapper Bundle Status**:
```
Bundled Schemas (5):
  ✓ risks.schema.json        (v1.0)
  ✓ controls.schema.json     (v1.0)
  ✓ components.schema.json   (v1.0)
  ✓ personas.schema.json     (? - likely v1.0)
  ✓ self-assessment.schema.json (v1.0)

  ✗ frameworks.schema.json   (MISSING - added Jan 28, 2026)
  ✗ actor-access.schema.json (MISSING)
  ✗ impact-type.schema.json  (MISSING)
  ✗ lifecycle-stage.schema.json (MISSING)
  ✗ mermaid-styles.schema.json (MISSING)

Bundled YAML Data:
  ✗ frameworks.yaml          (MISSING)
  ✗ Updated personas.yaml    (likely outdated)
```

**Risk**: Offline mode increasingly diverges from source of truth with each CoSAI release.

---

## 2. CoSAI Source Repository Alignment

### 2.1 Two-Stage Release Cycle

CoSAI uses a governance model where changes flow:
```
feature branch → develop (Stage 1: Technical Review)
             → main (Stage 2: Community Review)
```

**Implication for ai-risk-mapper**:
- Content updates (YAML data) released bi-weekly to main
- Infrastructure updates (scripts, schemas) happen continuously
- Develop branch has pending features awaiting community review
- **Current skill only syncs with main; misses develop-stage innovations**

### 2.2 Available Validation Infrastructure

CoSAI provides pre-commit hook system with powerful validation:

| Hook | Purpose | Relevance |
|------|---------|-----------|
| **validate_riskmap.py** | Edge validation + graph generation | Could replace/enhance analyze_risks.py |
| **validate_control_risk_references.py** | Bidirectional mapping validation | Could verify control suggestions |
| **validate_framework_references.py** | Framework applicability constraints | Could improve persona/framework mapping |
| **yaml_to_markdown.py** | Generate cross-reference tables | Could support reporting |
| **ComponentGraph** | Component dependency graphs | Could visualize system architecture |
| **ControlGraph** | Control-to-component mapping | Could guide control selection |
| **RiskGraph** | Risk-to-control relationships | Could show mitigation chains |

**Opportunity**: Instead of reimplementing analysis, wrap/adapt CoSAI's validation scripts.

### 2.3 Framework Definitions (NEW - Jan 28, 2026)

CoSAI just added `frameworks.yaml` with:
- Framework versioning (MITRE ATLAS v3.0, NIST AI RMF v1.0, etc.)
- Framework applicability constraints
- Framework-to-entity mappings

**Risk**: AI-risk-mapper cannot leverage framework versions for compliance tracking.

---

## 3. Semantic Risk Detection Gap

### Current Approach (Keyword-Based)

`analyze_risks.py` uses pattern matching:
```python
# Pseudocode
if "password" in file_content or "secret" in file_content:
    risks.append("Sensitive Data Disclosure")
```

**Limitations**:
- False positives (e.g., "secret" in variable names, comments)
- False negatives (semantic risks not caught by keywords)
- Cannot detect business logic vulnerabilities
- No context understanding (safe vs unsafe patterns)

### CoSAI's Risk Catalog (25+ Risks)

Examples of semantic risks keyword matching struggles with:
- **Model Inversion Attack**: Requires understanding model training methodology
- **Prompt Injection**: Context-aware payload detection needed
- **Supply Chain Compromise**: Requires dependency analysis understanding
- **Alignment Issues**: Requires semantic output analysis

**Opportunity**: Enhance with semantic analysis (Claude API integration) while maintaining offline capability.

---

## 4. GitHub Issues Status

### Open Issues Tagged with skill:ai-risk-mapper

| Issue | Status | Relevance |
|-------|--------|-----------|
| **#20** | OPEN | Phase 3: Enhanced automation & visualization (v2.1.0+) |

**Issue #20 Requirements**:
1. Semantic analysis enhancement (HIGH PRIORITY)
2. Visualization & tracking dashboard (MEDIUM)
3. Test coverage & troubleshooting (MEDIUM)

**Completion Status**: 0% - Just created 2026-01-28

---

## 5. Script Utility Assessment

### Available Scripts

| Script | Purpose | Maturity | Testing |
|--------|---------|----------|---------|
| `orchestrate_risk_assessment.py` | Workflow coordination | v2.0 | None |
| `fetch_cosai_schemas.py` | Schema downloading | v2.0 | None |
| `analyze_risks.py` | Risk detection | v1.0 | None |
| `generate_report.py` | Report generation | v1.0 | None |

**CoSAI Equivalent Scripts** (Not currently used):
| Script | Purpose | Gap |
|--------|---------|-----|
| `validate_riskmap.py` | Graph validation + generation | Not utilized |
| `validate_control_risk_references.py` | Mapping validation | Not utilized |
| `validate_framework_references.py` | Framework constraints | Not utilized |
| `yaml_to_markdown.py` | Reference table generation | Not utilized |

**Recommendation**: Create wrapper commands to leverage CoSAI utilities.

---

## 6. Branch Awareness

### Current Behavior

**fetch_cosai_schemas.py**:
```python
# Current: Hardcoded main branch
url = f"https://raw.githubusercontent.com/cosai-oasis/secure-ai-tooling/main/risk-map/yaml/{filename}.yaml"
```

**Limitations**:
- Cannot fetch develop branch innovations
- No version tracking or branch selection
- No warning when develop has updates
- Users cannot opt-in to pre-release features

### CoSAI Branch States

| Branch | Status | Use Case |
|--------|--------|----------|
| main | Release-ready | Production usage (bi-weekly updates) |
| develop | Pre-release (7 commits ahead) | Early access to features pending community review |

**Recommendation**: Add `--branch` flag to fetch script; make main default, allow develop override.

---

## 7. Missing Capabilities Analysis

### Immediate Needs (v2.0 → v2.1)

1. **Semantic Risk Detection**
   - Status: Not implemented
   - Complexity: High
   - Impact: Critical (accuracy improvement)
   - Implementation: LLM-based analysis engine

2. **Framework Version Tracking**
   - Status: Not implemented
   - Complexity: Medium
   - Impact: High (compliance tracking)
   - Implementation: Extract framework versions from schemas

3. **Schema Bundle Updates**
   - Status: Not implemented
   - Complexity: Low
   - Impact: Medium (offline validity)
   - Implementation: Add missing schemas to offline bundle

4. **Branch Selection**
   - Status: Not implemented
   - Complexity: Low
   - Impact: Medium (feature access)
   - Implementation: Add --branch flag to fetch script

### Medium-Term Needs (v2.1 → v2.2)

5. **Risk Visualization**
   - Status: Planned (Issue #20)
   - Complexity: High
   - Impact: Medium (usability)

6. **Control Tracking**
   - Status: Planned (Issue #20)
   - Complexity: High
   - Impact: Medium (remediation management)

7. **Test Coverage**
   - Status: Planned (Issue #20)
   - Complexity: Medium
   - Impact: Medium (reliability)

---

## 8. Recommended Slash Commands

To make useful CoSAI scripts accessible and improve workflow, consider these slash commands:

### Analysis Commands

| Command | Purpose | Underlying Script |
|---------|---------|-------------------|
| `/assess` | Run full risk assessment | orchestrate_risk_assessment.py |
| `/analyze-risks` | Filtered risk analysis | analyze_risks.py |
| `/semantic-analyze` | (v2.1) LLM-based analysis | enhanced analyze_risks.py |

### Utilities

| Command | Purpose | Underlying Script |
|---------|---------|-------------------|
| `/fetch-schemas` | Download latest schemas | fetch_cosai_schemas.py |
| `/validate-risks` | Validate risk mappings | validate_riskmap.py (CoSAI) |
| `/generate-report` | Create assessment report | generate_report.py |

### Visualization (v2.1+)

| Command | Purpose | Underlying Script |
|---------|---------|-------------------|
| `/visualize-risks` | Show risk dashboard | New visualization module |
| `/track-controls` | Show control progress | New tracking module |
| `/risk-graph` | Show risk-control graph | validate_riskmap.py (CoSAI) |

### Reference & Learning

| Command | Purpose | Reference |
|---------|---------|-----------|
| `/cosai-concepts` | Explain CoSAI framework | references/cosai_overview.md |
| `/persona-guide` | Show persona definitions | references/personas_guide.md |
| `/risk-reference` | Show risk catalog | references/schemas_reference.md |

---

## 9. Conclusion

### Summary of Findings

**Maturity Level**: v2.0.0 is a **solid foundation** but has **critical gaps**:

1. ✅ Automation & orchestration working well
2. ✅ Documentation comprehensive
3. ❌ Accuracy limited by keyword-based detection
4. ❌ Out of sync with CoSAI schema/data updates
5. ❌ Missing visualization & tracking capabilities
6. ❌ No test coverage for reliability

### Priority Improvements

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| P0 | Update bundled schemas (frameworks.yaml) | 2h | High |
| P0 | Add branch awareness to fetch script | 4h | Medium |
| P1 | Implement semantic risk detection | 20h | Critical |
| P1 | Add test coverage for scripts | 16h | High |
| P2 | Visualization dashboard | 24h | Medium |
| P2 | Control tracking module | 20h | Medium |

### Recommended Path Forward

1. **Immediate** (v2.0.1): Schema bundle update + branch awareness
2. **Short-term** (v2.1.0): Semantic analysis engine (issue #20)
3. **Medium-term** (v2.2.0): Visualization & tracking (issue #20)
4. **Ongoing**: Test coverage + documentation

---

## Appendix: Configuration Recommendations

### For fetch_cosai_schemas.py Enhancement

```python
# Proposed additions:
parser.add_argument('--branch', default='main',
                   choices=['main', 'develop'],
                   help='GitHub branch to fetch from')
parser.add_argument('--include-frameworks', action='store_true',
                   help='Include frameworks.yaml and schemas')
parser.add_argument('--version-check', action='store_true',
                   help='Check for updates from develop branch')
```

### For Semantic Analysis Integration

```python
# Proposed enhancement to analyze_risks.py:
parser.add_argument('--semantic', action='store_true',
                   help='Use LLM-based semantic analysis')
parser.add_argument('--semantic-model', default='claude-3-haiku',
                   help='Model for semantic analysis')
parser.add_argument('--confidence-threshold', type=float, default=0.7,
                   help='Minimum confidence for risk identification')
```

### For Test Coverage

```python
# pyproject.toml additions needed:
[tool.pytest.ini_options]
testpaths = ["tests"]
minversion = "7.0"

[tool.coverage.run]
source = ["scripts"]
omit = ["*/__pycache__/*", "*/test_*.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

---

## Appendix: Reference Links

**CoSAI Source Repository**:
- GitHub: https://github.com/cosai-oasis/secure-ai-tooling
- Main branch: https://github.com/cosai-oasis/secure-ai-tooling/tree/main
- Develop branch: https://github.com/cosai-oasis/secure-ai-tooling/tree/develop

**AI-Risk-Mapper Skill**:
- Location: `/skills/ai-risk-mapper/`
- GitHub Issues: https://github.com/totallyGreg/claude-mp/issues?label=skill:ai-risk-mapper
- Open Issues: Issue #20 (Phase 3 - v2.1.0+)

**Related Documentation**:
- Project Workflow: `/WORKFLOW.md`
- Improvement Plan: `/skills/ai-risk-mapper/IMPROVEMENT_PLAN.md`
- Lessons Learned: `/docs/lessons/`
