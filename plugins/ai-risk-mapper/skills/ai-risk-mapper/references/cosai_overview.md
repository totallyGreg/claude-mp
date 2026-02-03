# CoSAI Risk Map Framework Overview

## What is CoSAI?

The Coalition for Secure AI (CoSAI) Risk Map is a comprehensive framework for identifying, analyzing, and mitigating security risks in Artificial Intelligence systems. Created as an OASIS Open Project, it addresses the critical gap where conventional software security approaches fall short for AI deployments.

## Key Industry Challenges Addressed

1. **Shared Terminology**: Establishes common language for AI threats across organizations
2. **System-Wide Visibility**: Provides comprehensive coverage across entire AI systems, not just models
3. **Ecosystem Focus**: Shifts attention beyond isolated model risks to encompass the broader AI ecosystem

## Framework Structure

The Risk Map organizes AI development into **four primary lifecycle domains**:

### 1. Data
- Data Sources
- Data Filtering and Processing
- Training Data
- Data Storage

### 2. Infrastructure
- Model Frameworks and Code
- Model Storage
- Model Serving
- Training and Tuning Infrastructure

### 3. Model
- The Model (weights and parameters)
- Model Evaluation
- Training and Tuning processes

### 4. Application
- Application layer
- Application I/O Handling
- Agent components (User Query, System Instructions, I/O Handling, Reasoning Core)
- Orchestration (I/O Handling, External Tools, Model Memory, RAG Content)

## Core Framework Components

### Components (19 total)
Fundamental building blocks of AI systems organized into Infrastructure, Model, and Application categories. Components form a directed acyclic graph showing data flow and dependencies.

### Risks (25+ identified)
Catalog of potential security threats including:
- Data Poisoning (DP)
- Model Exfiltration (MXF)
- Prompt Injection (PIJ)
- Sensitive Data Disclosure (SDD)
- Model Evasion (MEV)
- And 20+ additional risks

### Controls (30+ available)
Security measures addressing identified risks across six categories:
- Data Controls
- Infrastructure Controls
- Model Controls
- Application Controls
- Assurance Controls
- Governance Controls

### Personas (2 defined)
- **Model Creator**: Organizations that train and tune foundation models or customize models for domain-specific tasks
- **Model Consumer**: Organizations that build AI applications using models without creating/tuning models themselves

## File Formats

The framework provides dual formats for accessibility and automation:
- **Human-readable**: YAML files (.yaml) for learning and assessment
- **Machine-readable**: JSON schemas (.schema.json) for validation and tooling

## Framework Mappings

CoSAI provides cross-references to established security standards:
- **MITRE ATLAS**: Adversarial Threat Landscape for AI Systems
- **NIST AI RMF**: AI Risk Management Framework
- **STRIDE**: Microsoft's threat modeling approach
- **OWASP Top 10 for LLM**: Web application security for language models

These mappings enable organizations to align CoSAI guidance with existing compliance requirements.

## Usage Patterns

1. **Learning**: Review YAML files to understand the AI security risk landscape
2. **Assessing**: Apply the framework during security evaluations of AI projects
3. **Building**: Use JSON schemas to customize the framework for organizational needs
4. **Validating**: Leverage schemas to validate AI system security configurations

## Key Insight

The framework emphasizes that attacking model weights carries risks equivalent to code-level attacks in traditional software. It treats AI security holistically, recognizing that vulnerabilities can exist at any point from data ingestion through application deployment.

## License

Apache 2.0 - enabling community adoption and customization

## Repository

https://github.com/cosai-oasis/secure-ai-tooling
