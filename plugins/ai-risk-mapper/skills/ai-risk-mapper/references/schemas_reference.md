---
last_verified: 2026-05-06
sources:
  - type: github
    repo: "cosai-oasis/secure-ai-tooling"
    paths: ["risk-map/schemas/"]
    description: "CoSAI JSON schema definitions for validation and automation"
---

# CoSAI Schema Reference

This document describes the JSON schema structures used in the CoSAI Risk Map framework for validation and automation.

## Risks Schema (risks.schema.json)

### Root-Level Fields

**Required:**
- `title` (string): Name of the risks definition
- `description` (text): Overview content
- `risks` (array): Collection of risk objects

### Risk Object Structure

**Required Fields:**
- `id` (enum): One of 28 valid risk codes (camelCase format):
  - riskDataPoisoning, riskUnauthorizedTrainingData, riskModelSourceTampering, riskExcessiveDataHandling, riskExcessiveDataHandlingDuringInference, riskModelExfiltration, riskModelDeploymentTampering, riskDenialOfMLService, riskModelReverseEngineering, riskInsecureIntegratedComponent, riskPromptInjection, riskModelEvasion, riskSensitiveDataDisclosure, riskInferredSensitiveData, riskInsecureModelOutput, riskRogueActions, riskAcceleratorAndSystemSideChannels, riskEconomicDenialOfWallet, riskFederatedDistributedTrainingPrivacy, riskAdapterPEFTInjection, riskToolRegistryTampering, riskOrchestratorRouteHijacking, riskEvaluationBenchmarkManipulation, riskCovertChannelsInModelOutputs, riskMaliciousLoaderDeserialization, riskToolSourceProvenance, riskPromptResponseCachePoisoning, riskRetrievalVectorStorePoisoning
- `title` (string): Risk name
- `shortDescription` (text): Brief overview
- `longDescription` (text): Detailed explanation
- `category` (enum): Risk classification from five options:
  - risksSupplyChainAndDevelopment
  - risksDeploymentAndInfrastructure
  - risksRuntimeInputSecurity
  - risksRuntimeDataSecurity
  - risksRuntimeOutputSecurity
- `personas` (array): References to persona IDs
- `controls` (array): References to control IDs

**Optional Fields:**
- `tourContent` (object): Narrative structure with properties:
  - `introduced` (text)
  - `exposed` (text)
  - `mitigated` (text)
- `examples` (text): Real-world cases
- `relevantQuestions` (array of strings): Assessment questions
- `mappings` (object): Cross-references to security frameworks. `mitre-atlas`, `iso-22989`, and `eu-ai-act` use per-framework strict patterns via `$ref` to `frameworks.schema.json`; `stride`, `nist-ai-rmf`, and `owasp-top10-llm` use a loose catch-all. Keys must match framework IDs.
- `externalReferences` (object): External URL references via `$ref` to `external-references.schema.json`
- `lifecycleStage` (array or enum): Stage identifiers, or "all"/"none"
- `impactType` (array or enum): Impact category identifiers, or "all"/"none"
- `actorAccess` (array or enum): Access level identifiers, or "all"/"none"

## Controls Schema (controls.schema.json)

### Root-Level Fields

**Required:**
- `title` (string)
- `description` (text)
- `categories` (array)
- `controls` (array)

### Control Object Structure

**Required Fields:**
- `title` (string): Control name
- `description` (text): Detailed explanation
- `category` (enum): One of six options:
  - controlsData
  - controlsInfrastructure
  - controlsModel
  - controlsApplication
  - controlsAssurance
  - controlsGovernance
- `personas` (array): Target audience (8 active personas: personaModelProvider, personaDataProvider, personaPlatformProvider, personaModelServing, personaAgenticProvider, personaApplicationDeveloper, personaGovernance, personaEndUser)
- `components` (array or enum): Component IDs affected, or "all"/"none"
- `risks` (array or enum): Risk IDs addressed, or "all"

**Optional Fields:**
- `id` (enum): One of 30 predefined control identifiers
- `mappings` (object): Framework cross-references. `mitre-atlas`, `iso-22989`, and `eu-ai-act` use per-framework strict patterns; others use loose catch-all.
- `externalReferences` (object): External URL references via `$ref` to `external-references.schema.json`
- `lifecycleStage` (array or enum): Stage identifiers, or "all"/"none"
- `impactType` (array or enum): Impact category identifiers, or "all"/"none"
- `actorAccess` (array or enum): Access level identifiers, or "all"/"none"

## Components Schema (components.schema.json)

### Root-Level Fields

**Required:**
- `title` (string)
- `description` (text)
- `categories` (array)
- `components` (array)

**Optional:**
- `subcategory` (array)

### Component Object Structure

**Required Fields:**
- `id` (enum): One of 25 predefined component identifiers
- `title` (string): Component name
- `category` (enum): One of three values:
  - componentsInfrastructure
  - componentsModel
  - componentsApplication
- `edges` (object): Connection definitions (must contain at least one of "to" or "from")

**Optional Fields:**
- `description` (text): Component explanation
- `subcategory` (enum): One of four values:
  - componentsModelTraining
  - componentsData
  - (two additional values)
- `mappings` (object): Cross-references to external security frameworks (same per-framework strict/loose pattern as risks and controls)
- `externalReferences` (object): External URL references via `$ref` to `external-references.schema.json`

### Edges Structure

The `edges` object requires at least one of:
- `to` (array): Component IDs this connects to
- `from` (array): Component IDs that feed into this

## Personas Schema (personas.schema.json)

### Structure

Defines personas with:
- `id` (string): Unique identifier
- `title` (string): Persona name
- `description` (text): Role and responsibilities
- `responsibilities` (array): Specific responsibilities for this persona
- `mappings` (object): ISO 22989 and other framework mappings
- `identificationQuestions` (array): Questions to identify this persona
- `externalReferences` (object): External URL references
- `deprecated` (boolean): Whether this persona is deprecated

### Defined Personas (10: 8 active + 2 deprecated)

1. **Model Provider** (`personaModelProvider`): Model training and serving
2. **Data Provider** (`personaDataProvider`): Data quality and provenance
3. **AI Platform Provider** (`personaPlatformProvider`): Infrastructure and APIs
4. **AI Model Serving** (`personaModelServing`): Model serving endpoints
5. **Agentic Platform Providers** (`personaAgenticProvider`): Agentic frameworks
6. **Application Developer** (`personaApplicationDeveloper`): AI-powered apps
7. **AI System Governance** (`personaGovernance`): Compliance and controls
8. **AI System Users** (`personaEndUser`): End users
9. ~~Model Creator~~ (`personaModelCreator`): _deprecated_
10. ~~Model Consumer~~ (`personaModelConsumer`): _deprecated_

## Lifecycle Stage Schema (lifecycle-stage.schema.json)

- `order` (integer): Sequential order in the lifecycle, constrained to range 1–8

## Riskmap Meta-Schema (riskmap.schema.json)

Shared definitions used across schemas:
- `prose` (array): Flexible text content (strings or nested arrays)
- `prose-strict` (array): Validated prose content — strings or nested string arrays, all non-empty (`minLength: 1`)

## Validation Rules

### Cross-References
All ID references (personas, controls, components, frameworks, lifecycle stages, impact types) must match defined entities in corresponding schema files.

### Enumerated Values
Use special values for flexible categorization:
- `"all"`: Applies to all items in the category
- `"none"`: Explicitly applies to no items

### Bidirectional Validation
The framework enforces consistency:
- If Control A lists Risk B, Risk B should list Control A
- If Component X connects to Component Y, the relationship should be documented bidirectionally

## Schema URLs

Full schemas available at:
- https://github.com/cosai-oasis/secure-ai-tooling/tree/main/risk-map/schemas
