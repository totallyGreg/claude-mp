---
last_verified: 2026-04-28
sources:
  - type: github
    repo: "cosai-oasis/secure-ai-tooling"
    paths: ["risk-map/"]
    description: "CoSAI Risk Map — risk IDs, persona IDs, framework mappings from upstream YAML"
---

# Interactive Exploration Guide

This guide covers interactive exploration of the CoSAI Risk Map framework using CLI commands and the core analyzer API. Use these tools for ad-hoc queries, threat modeling sessions, and compliance mapping.

## Quick Reference

### Entity IDs

**Risks (26 total):**
| ID | Title | Category |
|----|-------|----------|
| `DP` | Data Poisoning | Supply Chain & Development |
| `UTD` | Unauthorized Training Data | Supply Chain & Development |
| `MST` | Model Source Tampering | Supply Chain & Development |
| `EDH` | Excessive Data Handling | Supply Chain & Development |
| `EDH-I` | Excessive Data Handling During Inference | Runtime Data Security |
| `MXF` | Model Exfiltration | Model Security |
| `MDT` | Model Deployment Tampering | Model Security |
| `DMS` | Denial of ML Service | Infrastructure |
| `MRE` | Model Reverse Engineering | Model Security |
| `IIC` | Insecure Integrated Component | Application Security |
| `PIJ` | Prompt Injection | Application Security |
| `MEV` | Model Evasion | Model Security |
| `SDD` | Sensitive Data Disclosure | Data Security |
| `ISD` | Inferred Sensitive Data | Privacy |
| `IMO` | Insecure Model Output | Application Security |
| `RA` | Rogue Actions | Application Security |
| `ASSC` | Accelerator and System Side-channels | Deployment & Infrastructure |
| `EDW` | Economic Denial of Wallet | Infrastructure |
| `FLP` | Federated/Distributed Training Privacy | Privacy |
| `ADI` | Adapter/PEFT Injection | Supply Chain & Development |
| `ORH` | Orchestrator/Route Hijack | Application Security |
| `EBM` | Evaluation/Benchmark Manipulation | Assurance |
| `COV` | Covert Channels in Model Outputs | Data Security |
| `MLD` | Malicious Loader/Deserialization | Supply Chain & Development |
| `PCP` | Prompt/Response Cache Poisoning | Application Security |
| `RVP` | Retrieval/Vector Store Poisoning | Application Security |

**Personas (10: 8 active + 2 deprecated):**
| ID | Title | Status |
|----|-------|--------|
| `personaModelProvider` | Model Provider | Active |
| `personaDataProvider` | Data Provider | Active |
| `personaPlatformProvider` | AI Platform Provider | Active |
| `personaModelServing` | AI Model Serving | Active |
| `personaAgenticProvider` | Agentic Platform and Framework Providers | Active |
| `personaApplicationDeveloper` | Application Developer | Active |
| `personaGovernance` | AI System Governance | Active |
| `personaEndUser` | AI System Users | Active |
| `personaModelCreator` | Model Creator (Legacy) | Deprecated |
| `personaModelConsumer` | Model Consumer (Legacy) | Deprecated |

**Framework Mappings:**
- `mitre-atlas` - MITRE ATLAS attack framework
- `nist-ai-rmf` - NIST AI Risk Management Framework
- `stride` - STRIDE threat modeling
- `owasp-top10-llm` - OWASP Top 10 for LLM Applications
- `iso-22989` - ISO/IEC 22989 AI concepts and terminology

## Slash Commands

### `/risk-search <query>`

Search risks by keyword across title and descriptions.

```bash
uv run scripts/cli_risk_search.py "data poisoning"
```

**Output:**
```
Found 2 matching risks:

[DP] Data Poisoning
  Category: risksSupplyChainAndDevelopment
  Personas: personaModelProvider, personaDataProvider
  Description: Altering data sources used to train the model...

[RVP] Retrieval/Vector Store Poisoning
  Category: risksApplicationSecurity
  ...
```

**Use cases:**
- Finding all risks related to a threat type
- Exploring risks by technology (e.g., "LLM", "inference")
- Identifying risks by attack vector

### `/control-search <query>`

Search controls by keyword.

```bash
uv run scripts/cli_control_search.py "training"
```

**Output:**
```
Found 3 matching controls:

[controlTrainingDataSanitization] Training Data Sanitization
  Category: controlsData
  Risks mitigated: DP, UTD, ADI
  ...
```

**Use cases:**
- Finding controls for specific areas
- Exploring implementation options

### `/controls-for-risk <risk-id>`

Get all controls that mitigate a specific risk.

```bash
uv run scripts/cli_controls_for_risk.py DP
```

**Output:**
```
Risk: [DP] Data Poisoning

5 controls mitigate this risk:

1. [controlTrainingDataSanitization] Training Data Sanitization
   Description: Implement processes to validate and sanitize training data...
   Components: componentTrainingData, componentDataPipeline

2. [controlSecureByDefaultMLTooling] Secure-by-Default ML Tooling
   ...
```

**Use cases:**
- Building control recommendations for identified risks
- Creating security requirements

### `/persona-profile <persona-id>`

Get complete risk profile for a persona.

```bash
uv run scripts/cli_persona_profile.py personaModelProvider
```

**Output:**
```
Persona: Model Provider
Description: Organizations that train and serve AI models...

Responsibilities:
  - Model architecture design and training
  - Model evaluation and validation
  - Model documentation and cards

Relevant Risks: 18
  Supply Chain & Development: DP, UTD, MST, EDH, ADI, MLD
  Model Security: MXF, MDT, MRE, MEV
  ...

Relevant Controls: 24
  ...
```

**Use cases:**
- Understanding role-specific responsibilities
- Scoping assessments by persona
- Training and awareness

### `/gap-analysis <risk-id> --implemented <control-ids>`

Assess control coverage for a specific risk.

```bash
uv run scripts/cli_gap_analysis.py DP --implemented controlTrainingDataSanitization controlModelAndDataIntegrityManagement
```

**Output:**
```
Gap Analysis: [DP] Data Poisoning

Coverage: 40% (2 of 5 applicable controls implemented)

Implemented Controls:
  - [controlTrainingDataSanitization] Training Data Sanitization
  - [controlModelAndDataIntegrityManagement] Model and Data Integrity Management

Missing Controls:
  - [controlSecureByDefaultMLTooling] Secure-by-Default ML Tooling
  - [controlModelAndDataAccessControls] Model and Data Access Controls
  - [controlModelAndDataInventoryManagement] Model and Data Inventory Management

Recommendations:
  Priority 1: Implement access controls for training data
  Priority 2: Add secure ML tooling for development
  ...
```

**Use cases:**
- Measuring security posture
- Prioritizing control implementation
- Compliance gap assessment

### `/framework-map <risk-id> [--framework <name>]`

Get framework mappings for a risk.

```bash
uv run scripts/cli_framework_map.py PIJ --framework mitre-atlas
```

**Output:**
```
Risk: [PIJ] Prompt Injection

MITRE ATLAS Mappings:
  - AML.T0051 - LLM Prompt Injection
  - AML.T0054 - LLM Jailbreak

All Framework Mappings:
  mitre-atlas: AML.T0051, AML.T0054
  nist-ai-rmf: GOVERN-1.1, MAP-1.5
  stride: Tampering, Information Disclosure
  owasp-top10-llm: LLM01 - Prompt Injection
```

**Use cases:**
- Compliance mapping
- Threat intelligence correlation
- Security control validation

## Query Patterns

### Threat Modeling

```python
from core_analyzer import RiskAnalyzer

analyzer = RiskAnalyzer(offline=True)

# 1. Identify risks for your persona
risks = analyzer.get_risks_by_persona("personaApplicationDeveloper")

# 2. Filter by lifecycle stage
app_risks = analyzer.get_risks_by_lifecycle_stage("Application")

# 3. Get controls for each risk
for risk in app_risks:
    controls = analyzer.get_controls_for_risk(risk.id)
    print(f"{risk.title}: {len(controls)} controls")
```

### Gap Analysis Workflow

```python
# 1. Define implemented controls
implemented = [
    "controlInputValidationAndSanitization",
    "controlOutputValidationAndSanitization",
    "controlApplicationAccessManagement"
]

# 2. Assess each relevant risk
for risk in analyzer.get_risks_by_persona("personaApplicationDeveloper"):
    gap = analyzer.assess_risk_gap(risk.id, implemented)
    print(f"{risk.id}: {gap['coverage_percentage']}% coverage")
```

### Compliance Mapping

```python
# Map all risks to OWASP LLM Top 10
for risk in analyzer.get_all_risks():
    owasp = analyzer.get_framework_mappings(risk.id, "owasp-top10-llm")
    if owasp:
        print(f"{risk.id}: {', '.join(owasp)}")
```

### Component-Based Analysis

```python
# Find risks affecting training data components
risks = analyzer.get_risks_by_component("componentTrainingData")
print(f"Training data risks: {len(risks)}")
for risk in risks:
    print(f"  - {risk.title}")
```

## Best Practices

### 1. Start with Persona Scoping
Identify your persona first to focus on relevant risks and controls. With 8 active personas, you can get more targeted results than the legacy 2-persona model.

### 2. Use Layered Filtering
Combine multiple filters for targeted analysis:
- Persona + Lifecycle Stage
- Category + Impact Type
- Component + Control Category

### 3. Document Gap Analysis Results
Export gap analysis results for tracking:
```bash
uv run scripts/cli_gap_analysis.py PIJ --implemented controlInputValidationAndSanitization
```

### 4. Cross-Reference Frameworks
Use framework mappings to correlate with existing security programs:
- MITRE ATLAS for threat intelligence
- NIST AI RMF for governance
- OWASP LLM for application security
- ISO 22989 for persona alignment

### 5. Iterate on Control Coverage
Re-run gap analysis as controls are implemented to track progress toward target coverage.

## API Reference

The `core_analyzer.RiskAnalyzer` class provides 30+ methods:

### Risk Methods
| Method | Description |
|--------|-------------|
| `find_risk(id)` | Get risk by ID |
| `get_all_risks()` | Get all risks |
| `search_risks(keyword)` | Search by keyword |
| `get_risks_by_persona(id)` | Filter by persona |
| `get_risks_by_lifecycle_stage(stage)` | Filter by lifecycle |
| `get_risks_by_impact_type(type)` | Filter by impact |
| `get_risks_by_category(cat)` | Filter by category |
| `get_risks_by_component(id)` | Reverse lookup from component |

### Control Methods
| Method | Description |
|--------|-------------|
| `find_control(id)` | Get control by ID |
| `get_all_controls()` | Get all controls |
| `search_controls(keyword)` | Search by keyword |
| `get_controls_for_risk(id)` | Get controls for a risk |
| `get_controls_by_persona(id)` | Filter by persona |
| `get_controls_by_component(id)` | Filter by component |
| `get_controls_by_category(cat)` | Filter by category |

### Analysis Methods
| Method | Description |
|--------|-------------|
| `assess_risk_gap(id, controls)` | Gap analysis |
| `get_persona_risk_profile(id)` | Full persona profile |
| `search_all(keyword)` | Search across all entities |

### Framework Methods
| Method | Description |
|--------|-------------|
| `get_framework_mappings(risk_id, framework)` | Get specific mappings |
| `get_control_framework_mappings(id, framework)` | Control mappings |
| `get_all_framework_mappings(risk_id)` | All mappings for risk |

### Export Methods
| Method | Description |
|--------|-------------|
| `export_risk_as_dict(id)` | Export risk as dict |
| `export_control_as_dict(id)` | Export control as dict |
| `export_all_risks_as_json()` | Export all risks |
| `export_all_controls_as_json()` | Export all controls |

### Utility Methods
| Method | Description |
|--------|-------------|
| `get_statistics()` | Entity counts |
| `get_risk_ids()` | All risk IDs |
| `get_control_ids()` | All control IDs |
| `get_component_ids()` | All component IDs |
| `get_persona_ids()` | All persona IDs |

## Offline Mode

All CLI commands support offline mode using bundled schemas:

```bash
# Explicit offline mode
uv run scripts/cli_risk_search.py "injection" --offline

# Automatic fallback if cache not available
```

The bundled schemas are located at `assets/cosai-schemas/yaml/` and are used automatically when:
1. `--offline` flag is provided
2. Cache directory (`~/.cosai-cache/yaml/`) doesn't exist
