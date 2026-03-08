# AI Security Risk Assessment Report

**Generated:** 2026-03-08 19:40:02
**Framework:** CoSAI Risk Map (Coalition for Secure AI)
**Total Risks Identified:** 26

---

## Executive Summary

This report identifies **26 security risks** in the assessed AI system 
based on the CoSAI Risk Map framework. Risk distribution:

- **Critical:** 10 risks requiring immediate attention
- **High:** 6 risks requiring prompt remediation
- **Medium:** 10 risks requiring planned mitigation
- **Low:** 0 risks requiring monitoring

⚠️ **URGENT**: Critical severity risks identified. Immediate action required.

---

## Risk Summary

### Risks by Category

- **risksSupplyChainAndDevelopment**: 6 risks
- **risksDeploymentAndInfrastructure**: 6 risks
- **risksRuntimeDataSecurity**: 5 risks
- **risksRuntimeOutputSecurity**: 5 risks
- **risksRuntimeInputSecurity**: 4 risks

### Risks by Lifecycle Stage

- **runtime**: 12 risks
- **model-training**: 6 risks
- **deployment**: 4 risks
- **evaluation**: 4 risks
- **data-preparation**: 3 risks
- **maintenance**: 3 risks
- **development**: 2 risks
- **planning**: 1 risks


## Identified Risks

### Critical Severity (10 risks)

#### [DP] Data Poisoning

**Category:** risksSupplyChainAndDevelopment
**Applicable Personas:** personaModelProvider, personaDataProvider, personaModelServing, personaAgenticProvider, personaApplicationDeveloper, personaEndUser, personaModelCreator
**Lifecycle Stages:** data-preparation, model-training, maintenance
**Confidence:** low

**Description:**
Altering data sources used to train the model. In terms of impact, Data Poisoning is comparable to modifying the logic of an application to change its behavior.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlTrainingDataSanitization
- controlSecureByDefaultMLTooling
- controlModelAndDataIntegrityManagement
- ...and 2 more

---

#### [MST] Model Source Tampering

**Category:** risksSupplyChainAndDevelopment
**Applicable Personas:** personaModelProvider, personaPlatformProvider, personaModelServing, personaApplicationDeveloper, personaEndUser, personaModelCreator
**Lifecycle Stages:** development, model-training, deployment
**Confidence:** low

**Description:**
Tampering with the model's code or data. Model Source Tampering is similar to tampering with traditional software code, and can create vulnerabilities or unintended behavior.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlIsolatedConfidentialComputing
- controlModelAndDataAccessControls
- controlModelAndDataExecutionIntegrity
- ...and 3 more

---

#### [MXF] Model Exfiltration

**Category:** risksDeploymentAndInfrastructure
**Applicable Personas:** personaModelProvider, personaModelServing, personaModelCreator, personaModelConsumer
**Lifecycle Stages:** deployment, runtime, model-training, evaluation, maintenance
**Confidence:** low

**Description:**
Theft of a model. Similar to stealing code, this threat has both intellectual property and security implications.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlIsolatedConfidentialComputing
- controlModelAndDataInventoryManagement
- controlModelAndDataAccessControls
- ...and 2 more

---

#### [MDT] Model Deployment Tampering

**Category:** risksDeploymentAndInfrastructure
**Applicable Personas:** personaPlatformProvider, personaModelServing, personaApplicationDeveloper, personaEndUser, personaModelCreator, personaModelConsumer
**Lifecycle Stages:** deployment, runtime
**Confidence:** low

**Description:**
Unauthorized changes to model deployment components. Model Deployment Tampering can result in changes to model behavior.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlIsolatedConfidentialComputing
- controlModelAndDataExecutionIntegrity
- controlOrchestratorAndRouteIntegrity
- ...and 1 more

---

#### [MRE] Model Reverse Engineering

**Category:** risksDeploymentAndInfrastructure
**Applicable Personas:** personaModelProvider, personaDataProvider, personaModelConsumer
**Lifecycle Stages:** runtime
**Confidence:** low

**Description:**
Recreating a model by analyzing its inputs, outputs, and behaviors. A reverse engineer model can be used to create imitation products or adversarial attacks.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlApplicationAccessManagement

---

#### [IIC] Insecure Integrated Component

**Category:** risksDeploymentAndInfrastructure
**Applicable Personas:** personaPlatformProvider, personaModelServing, personaAgenticProvider, personaApplicationDeveloper, personaEndUser, personaModelConsumer
**Lifecycle Stages:** development, deployment, runtime
**Confidence:** low

**Description:**
Software vulnerabilities that can be leveraged to compromise AI models. Insecure Integrated Component can lead to privacy and security concerns, as well as potential ethical and legal challenges.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlAgentPluginPermissions
- controlModelAndDataExecutionIntegrity
- controlUserPoliciesAndEducation

---

#### [PIJ] Prompt Injection

**Category:** risksRuntimeInputSecurity
**Applicable Personas:** personaModelServing, personaApplicationDeveloper, personaEndUser, personaModelCreator, personaModelConsumer
**Lifecycle Stages:** runtime
**Confidence:** low

**Description:**
Tricking a model to run unintended commands. In terms of impact, Prompt Injection can change a model's behavior.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlInputValidationAndSanitization
- controlAdversarialTrainingAndTesting
- controlOutputValidationAndSanitization

---

#### [MEV] Model Evasion

**Category:** risksRuntimeInputSecurity
**Applicable Personas:** personaModelServing, personaAgenticProvider, personaApplicationDeveloper, personaEndUser, personaModelCreator, personaModelConsumer
**Lifecycle Stages:** evaluation, runtime
**Confidence:** low

**Description:**
Changes to a prompt input to cause the model to produce incorrect inferences. Model Evasion can lead to reputational, legal, security, and privacy risks.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlAdversarialTrainingAndTesting

---

#### [IMO] Insecure Model Output

**Category:** risksRuntimeOutputSecurity
**Applicable Personas:** personaAgenticProvider, personaApplicationDeveloper, personaEndUser, personaModelConsumer
**Lifecycle Stages:** runtime
**Confidence:** low

**Description:**
Unvalidated model output passed to the end user. Insecure Model Output poses risks to organizational reputation, security, and user safety.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlOutputValidationAndSanitization
- controlAdversarialTrainingAndTesting

---

#### [RA] Rogue Actions

**Category:** risksRuntimeOutputSecurity
**Applicable Personas:** personaPlatformProvider, personaModelServing, personaAgenticProvider, personaApplicationDeveloper, personaEndUser, personaModelConsumer
**Lifecycle Stages:** runtime
**Confidence:** low

**Description:**
Unintentional model-based actions executed via extensions. Rogue Actions can create a cascading, risk to organizational reputation, user trust, security, and safety.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlAgentPluginPermissions
- controlAgentPluginUserControl
- controlOutputValidationAndSanitization
- ...and 1 more

---

### High Severity (6 risks)

#### [UTD] Unauthorized Training Data

**Category:** risksSupplyChainAndDevelopment
**Applicable Personas:** personaModelProvider, personaDataProvider, personaModelCreator
**Lifecycle Stages:** planning, data-preparation, model-training
**Confidence:** low

**Description:**
Using unauthorized data for model training. Using a model trained with Unauthorized Training Data might lead to legal or ethical challenges.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlTrainingDataSanitization
- controlTrainingDataManagement

---

#### [EDH] Excessive Data Handling

**Category:** risksSupplyChainAndDevelopment
**Applicable Personas:** personaModelProvider, personaDataProvider, personaModelCreator
**Lifecycle Stages:** data-preparation, model-training, evaluation
**Confidence:** low

**Description:**
Using data for model training and development that exceeds authorized or legal boundaries for collection, retention, or processing. This may lead to policy and legal challenges.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlTrainingDataManagement
- controlUserTransparencyAndControls

---

#### [EDH-I] Excessive Data Handling During Inference

**Category:** risksRuntimeDataSecurity
**Applicable Personas:** personaPlatformProvider, personaModelServing, personaApplicationDeveloper, personaEndUser, personaModelCreator
**Lifecycle Stages:** runtime, maintenance
**Confidence:** low

**Description:**
Unauthorized collection, retention, processing, or sharing of user data during model inference. This can lead to privacy violations and legal challenges.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlUserDataManagement
- controlUserTransparencyAndControls

---

#### [DMS] Denial of ML Service

**Category:** risksRuntimeInputSecurity
**Applicable Personas:** personaPlatformProvider, personaModelServing, personaApplicationDeveloper, personaEndUser, personaModelConsumer
**Lifecycle Stages:** runtime
**Confidence:** low

**Description:**
Overloading ML systems with resource-intensive queries. Like traditional DoS attacks, Denial of ML Service can reduce availability of or entirely disrupt a service.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlApplicationAccessManagement

---

#### [SDD] Sensitive Data Disclosure

**Category:** risksRuntimeDataSecurity
**Applicable Personas:** personaModelProvider, personaDataProvider, personaApplicationDeveloper, personaEndUser, personaModelCreator, personaModelConsumer
**Lifecycle Stages:** model-training, evaluation, runtime
**Confidence:** low

**Description:**
Disclosure of sensitive data by the model. Sensitive Data Disclosure poses a threat to user privacy, organizational reputation, and intellectual property.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlModelPrivacyEnhancingTechnologies
- controlRuntimePrivacyEnhancingTechnologies
- controlUserDataManagement
- ...and 7 more

---

#### [ISD] Inferred Sensitive Data

**Category:** risksRuntimeDataSecurity
**Applicable Personas:** personaModelServing, personaApplicationDeveloper, personaEndUser, personaModelCreator, personaModelConsumer
**Lifecycle Stages:** runtime
**Confidence:** low

**Description:**
Model inferring personal information not contained in training data or inputs. Inferred Sensitive Data may be considered a data privacy incident.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlTrainingDataManagement
- controlOutputValidationAndSanitization
- controlAdversarialTrainingAndTesting

---

### Medium Severity (10 risks)

#### [ASSC] Accelerator and System Side-channels

**Category:** risksDeploymentAndInfrastructure
**Applicable Personas:** personaPlatformProvider, personaModelServing, personaApplicationDeveloper, personaEndUser, personaModelCreator, personaModelConsumer
**Lifecycle Stages:** 
**Confidence:** low

**Description:**
Cross-tenant leakage via hardware side-channels in CPUs, GPUs, TPUs, memory systems, and interconnects. These vulnerabilities exploit timing, cache, speculative execution, and memory access patterns to compromise data confidentiality and infer sensitive information in shared computing environments.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlSecureByDefaultMLTooling
- controlModelAndDataAccessControls
- controlIsolatedConfidentialComputing

---

#### [EDW] Economic Denial of Wallet

**Category:** risksRuntimeInputSecurity
**Applicable Personas:** personaPlatformProvider, personaModelServing, personaApplicationDeveloper, personaEndUser, personaModelConsumer
**Lifecycle Stages:** 
**Confidence:** low

**Description:**
Cost abuse via token inflation, long context, or tool loops that spike spend. Economic Denial of Wallet can lead to unexpected financial losses and service disruption through resource exhaustion attacks.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlApplicationAccessManagement

---

#### [FLP] Federated/Distributed Training Privacy

**Category:** risksSupplyChainAndDevelopment
**Applicable Personas:** personaModelProvider, personaDataProvider, personaApplicationDeveloper, personaEndUser, personaModelCreator
**Lifecycle Stages:** 
**Confidence:** low

**Description:**
Gradient leakage and inversion attacks from untrusted clients in federated learning. Federated/Distributed Training Privacy risks can expose sensitive training data and compromise participant privacy.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlModelPrivacyEnhancingTechnologies
- controlRuntimePrivacyEnhancingTechnologies
- controlModelAndDataIntegrityManagement
- ...and 1 more

---

#### [ADI] Adapter/PEFT Injection

**Category:** risksDeploymentAndInfrastructure
**Applicable Personas:** personaPlatformProvider, personaModelServing, personaApplicationDeveloper, personaEndUser, personaModelCreator, personaModelConsumer
**Lifecycle Stages:** 
**Confidence:** low

**Description:**
Trojaned adapters merged at runtime to bypass safety or exfiltrate data. Adapter/PEFT Injection can compromise model behavior and enable unauthorized access to sensitive information or system resources.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlModelAndDataExecutionIntegrity
- controlModelAndDataIntegrityManagement
- controlModelAndDataAccessControls
- ...and 1 more

---

#### [ORH] Orchestrator/Route Hijack

**Category:** risksRuntimeOutputSecurity
**Applicable Personas:** personaModelServing, personaApplicationDeveloper, personaEndUser, personaModelCreator, personaModelConsumer
**Lifecycle Stages:** 
**Confidence:** low

**Description:**
Silent model or route swaps via configuration tampering or prompt-based routing abuse. Orchestrator/Route Hijack can redirect requests to malicious models or compromise routing integrity in AI systems.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlIsolatedConfidentialComputing
- controlModelAndDataIntegrityManagement
- controlModelAndDataAccessControls
- ...and 2 more

---

#### [EBM] Evaluation/Benchmark Manipulation

**Category:** risksRuntimeDataSecurity
**Applicable Personas:** personaModelProvider, personaModelServing, personaApplicationDeveloper, personaEndUser, personaModelCreator
**Lifecycle Stages:** 
**Confidence:** low

**Description:**
Poisoned or leaked evaluation sets misleading safety and robustness signals. Evaluation/Benchmark Manipulation can compromise model assessment accuracy and lead to deployment of unsafe or unreliable AI systems.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlModelAndDataIntegrityManagement

---

#### [COV] Covert Channels in Model Outputs

**Category:** risksRuntimeOutputSecurity
**Applicable Personas:** personaModelServing, personaAgenticProvider, personaApplicationDeveloper, personaEndUser, personaModelCreator, personaModelConsumer
**Lifecycle Stages:** 
**Confidence:** low

**Description:**
Hidden information transmission through model outputs or behavior patterns. Covert Channels in Model Outputs can enable unauthorized data exfiltration and steganographic communication bypassing security controls.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlOutputValidationAndSanitization
- controlModelAndDataIntegrityManagement

---

#### [MLD] Malicious Loader/Deserialization

**Category:** risksSupplyChainAndDevelopment
**Applicable Personas:** personaPlatformProvider, personaModelServing, personaApplicationDeveloper, personaEndUser, personaModelCreator, personaModelConsumer
**Lifecycle Stages:** 
**Confidence:** low

**Description:**
Unsafe loaders for models and tokenizers that can cause remote code execution or integrity compromise. Malicious Loader/Deserialization poses significant security risks including system compromise and data breaches.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlInputValidationAndSanitization
- controlModelAndDataAccessControls
- controlModelAndDataExecutionIntegrity
- ...and 2 more

---

#### [PCP] Prompt/Response Cache Poisoning

**Category:** risksRuntimeDataSecurity
**Applicable Personas:** personaModelServing, personaApplicationDeveloper, personaEndUser, personaModelCreator, personaModelConsumer
**Lifecycle Stages:** 
**Confidence:** low

**Description:**
Cross-user contamination via shared LLM caches lacking isolation and validation. Prompt/Response Cache Poisoning can lead to information leakage, misinformation propagation, and unauthorized access to cached content.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlModelAndDataAccessControls
- controlModelAndDataIntegrityManagement
- controlInputValidationAndSanitization
- ...and 2 more

---

#### [RVP] Retrieval/Vector Store Poisoning

**Category:** risksRuntimeOutputSecurity
**Applicable Personas:** personaPlatformProvider, personaModelServing, personaAgenticProvider, personaApplicationDeveloper, personaEndUser, personaModelCreator, personaModelConsumer
**Lifecycle Stages:** 
**Confidence:** low

**Description:**
Poisoning retrieval corpora or vector indices to steer RAG outputs. Retrieval/Vector Store Poisoning can compromise the integrity of knowledge retrieval systems and lead to misinformation or malicious content injection.


**Assessment Rationale:**
Risk may be applicable - requires manual review based on system architecture

**Recommended Controls:**
- controlTrainingDataSanitization
- controlModelAndDataIntegrityManagement
- controlInputValidationAndSanitization
- ...and 2 more

---

## Recommended Next Steps

1. **Review Critical and High Severity Risks**: Prioritize mitigation efforts
2. **Validate Risk Applicability**: Confirm each risk applies to your specific system
3. **Implement Controls**: Apply recommended controls from the CoSAI framework
4. **Establish Monitoring**: Set up detection and response for runtime risks
5. **Schedule Reassessment**: Conduct regular security assessments as system evolves

## References

- [CoSAI Risk Map Framework](https://github.com/cosai-oasis/secure-ai-tooling)
- [MITRE ATLAS](https://atlas.mitre.org/)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
