# Bundled CoSAI Schemas

Offline copy of CoSAI Risk Map data from the upstream repository.

## Source

- **Repository:** https://github.com/cosai-oasis/secure-ai-tooling
- **Upstream commit:** `e01f684`
- **Sync date:** 2026-05-06

## File Inventory

### YAML Data Files (10)

| File | Description |
|------|-------------|
| `components.yaml` | AI system components with subcategories and edges |
| `controls.yaml` | Security controls with persona/component/risk mappings |
| `frameworks.yaml` | Compliance framework definitions (MITRE ATLAS, NIST, OWASP, STRIDE, ISO 22989) |
| `personas.yaml` | 8 active + 2 deprecated personas with ISO 22989 alignment |
| `risks.yaml` | 28 risk definitions with camelCase IDs, categories, personas, controls, lifecycle stages |
| `self-assessment.yaml` | Assessment questions and criteria |
| `actor-access.yaml` | Actor access level enum definitions |
| `impact-type.yaml` | Impact type enum definitions |
| `lifecycle-stage.yaml` | Lifecycle stage enum definitions |
| `mermaid-styles.yaml` | Mermaid diagram style definitions |

### JSON Schema Files (13)

| File | Description |
|------|-------------|
| `components.schema.json` | Components validation schema (with mappings and externalReferences) |
| `controls.schema.json` | Controls validation schema (with strict mapping patterns) |
| `external-references.schema.json` | External references definition schema |
| `frameworks.schema.json` | Frameworks validation schema |
| `personas.schema.json` | Personas validation schema (with externalReferences) |
| `persona-site-data.schema.json` | Persona site data with sentinel resolution |
| `risks.schema.json` | Risks validation schema (with strict mapping patterns and externalReferences) |
| `self-assessment.schema.json` | Self-assessment validation schema |
| `actor-access.schema.json` | Actor access enum schema |
| `impact-type.schema.json` | Impact type enum schema |
| `lifecycle-stage.schema.json` | Lifecycle stage enum schema (order range 1-8) |
| `mermaid-styles.schema.json` | Mermaid diagram styles schema |
| `riskmap.schema.json` | Root risk map schema (with prose-strict definition) |
