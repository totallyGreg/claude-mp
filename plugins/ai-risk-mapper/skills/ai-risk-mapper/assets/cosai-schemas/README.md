# Bundled CoSAI Schemas

Offline copy of CoSAI Risk Map data from the upstream repository.

## Source

- **Repository:** https://github.com/cosai-oasis/secure-ai-tooling
- **Upstream commit:** `820d3d2c6bb1`
- **Sync date:** 2026-03-05

## File Inventory

### YAML Data Files (9)

| File | Description |
|------|-------------|
| `components.yaml` | AI system components with subcategories and edges |
| `controls.yaml` | Security controls with persona/component/risk mappings |
| `frameworks.yaml` | Compliance framework definitions (MITRE ATLAS, NIST, OWASP, STRIDE, ISO 22989) |
| `personas.yaml` | 8 active + 2 deprecated personas with ISO 22989 alignment |
| `risks.yaml` | Risk definitions with categories, personas, controls, lifecycle stages |
| `self-assessment.yaml` | Assessment questions and criteria |
| `actor-access.yaml` | Actor access level enum definitions |
| `impact-type.yaml` | Impact type enum definitions |
| `lifecycle-stage.yaml` | Lifecycle stage enum definitions |

### JSON Schema Files (11)

| File | Description |
|------|-------------|
| `components.schema.json` | Components validation schema |
| `controls.schema.json` | Controls validation schema |
| `frameworks.schema.json` | Frameworks validation schema |
| `personas.schema.json` | Personas validation schema |
| `risks.schema.json` | Risks validation schema |
| `self-assessment.schema.json` | Self-assessment validation schema |
| `actor-access.schema.json` | Actor access enum schema |
| `impact-type.schema.json` | Impact type enum schema |
| `lifecycle-stage.schema.json` | Lifecycle stage enum schema |
| `mermaid-styles.schema.json` | Mermaid diagram styles schema |
| `riskmap.schema.json` | Root risk map schema |
