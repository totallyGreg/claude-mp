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
- `id` (enum): One of 25 valid risk codes:
  - ASSC, ADI, COV, DMS, DP, EBM, EDH, EDW, FLP, IIC, IMO, ISD, MDT, MEV, MLD, MRE, MST, MXF, ORH, PCP, PIJ, RA, RVP, SDD, UTD, EDH-I
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
- `mappings` (object): Cross-references to security frameworks (keys must match framework IDs)
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
- `personas` (array): Target audience (ModelCreator, ModelConsumer)
- `components` (array or enum): Component IDs affected, or "all"/"none"
- `risks` (array or enum): Risk IDs addressed, or "all"

**Optional Fields:**
- `id` (enum): One of 30 predefined control identifiers
- `mappings` (object): Framework cross-references (framework IDs as keys, arrays of framework-specific identifiers as values)
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

### Edges Structure

The `edges` object requires at least one of:
- `to` (array): Component IDs this connects to
- `from` (array): Component IDs that feed into this

## Personas Schema (personas.schema.json)

### Structure

Defines two personas with:
- `id` (string): Unique identifier
- `title` (string): Persona name
- `description` (text): Role and responsibilities

### Defined Personas

1. **Model Creator**: Organizations that train/tune foundation models or customize for domain-specific tasks
2. **Model Consumer**: Organizations that build AI applications using models without creating/tuning them

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
