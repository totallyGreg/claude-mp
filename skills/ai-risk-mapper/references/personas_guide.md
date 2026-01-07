# CoSAI Personas Guide

The CoSAI Risk Map framework defines two distinct personas responsible for implementing controls to mitigate AI security risks. Understanding these personas is critical for determining organizational responsibilities and control ownership.

## Model Creator

### Definition
Organizations that train and tune foundation models for Generative AI, or tune acquired models for more domain-specific tasks.

### Responsibilities
- Develop and customize underlying AI models
- Train models on proprietary or curated datasets
- Fine-tune pre-trained models for specific domains
- Optimize model architectures and hyperparameters
- Manage model training infrastructure
- Implement model-level security controls
- Ensure model quality and safety

### Typical Examples
- Research labs developing foundation models (e.g., OpenAI, Anthropic, Google DeepMind)
- Companies fine-tuning open-source models for enterprise use
- Organizations training domain-specific models (medical, financial, legal AI)
- ML engineering teams building custom models from scratch

### Key Controls
Model Creators are primarily responsible for controls in:
- **Data Controls**: Training data sanitization, data provenance, privacy-enhancing techniques
- **Model Controls**: Adversarial training, model evaluation, robustness testing
- **Infrastructure Controls**: Secure training environments, model storage security
- **Governance Controls**: Model documentation, risk assessments, compliance

### Risk Focus
Model Creators must address risks during:
- Data collection and preprocessing
- Model training and tuning
- Model evaluation and validation
- Model storage and versioning
- Model distribution and deployment preparation

## Model Consumer

### Definition
Organizations that build AI applications, features, or products using models, but do not create or tune the models themselves.

### Responsibilities
- Integrate pre-trained models into applications
- Deploy models via APIs or packaged downloads
- Build application logic around model capabilities
- Implement input/output validation
- Monitor model behavior in production
- Manage model updates and versioning
- Implement application-level security controls

### Typical Examples
- SaaS companies adding AI features using OpenAI/Anthropic APIs
- Enterprises deploying chatbots using commercial models
- Product teams integrating LLMs into existing applications
- Mobile app developers using on-device ML models
- Organizations using AI platforms (AWS Bedrock, Azure OpenAI)

### Key Controls
Model Consumers are primarily responsible for controls in:
- **Application Controls**: Input validation, output filtering, prompt engineering, agent permissions
- **Infrastructure Controls**: API security, model serving security, access controls
- **Data Controls**: User data handling, PII protection, data retention
- **Assurance Controls**: Monitoring, logging, incident response

### Risk Focus
Model Consumers must address risks during:
- Model deployment and integration
- Application development
- Runtime operation and monitoring
- User interaction and input handling
- Output processing and delivery

## Shared Responsibilities

Both personas share responsibility for:

### Governance Controls
- **Risk Management**: Both must conduct risk assessments appropriate to their role
- **Compliance**: Both must ensure adherence to regulations (GDPR, HIPAA, etc.)
- **Documentation**: Both must maintain appropriate security documentation
- **Training**: Both must train personnel on AI security best practices

### Assurance Controls
- **Security Testing**: Both should conduct security testing appropriate to their access level
- **Vulnerability Management**: Both must address vulnerabilities in their scope
- **Incident Response**: Both must have incident response capabilities

## Determining Your Persona

Use this decision tree to identify which persona applies to your organization:

**Do you train or fine-tune models?**
- **Yes** → You are a Model Creator
  - Do you also deploy models in applications?
    - **Yes** → You have both personas (see Hybrid Organizations below)
    - **No** → Pure Model Creator

- **No** → You are a Model Consumer
  - Do you only use models via APIs or pre-built packages?
    - **Yes** → Pure Model Consumer

## Hybrid Organizations

Many organizations operate in both roles:
- **Example 1**: Company fine-tunes GPT-4 for internal use (Model Creator) and deploys it in customer-facing chatbot (Model Consumer)
- **Example 2**: Research lab trains custom models (Model Creator) and uses third-party models for evaluation (Model Consumer)

**For hybrid organizations:**
1. Apply Model Creator controls to model development activities
2. Apply Model Consumer controls to application deployment activities
3. Implement all shared Governance and Assurance controls
4. Clearly document which teams own which persona responsibilities

## Control Assignment by Persona

When reviewing CoSAI controls, each control specifies applicable personas:

```yaml
personas:
  - ModelCreator
  - ModelConsumer
  # or both
```

**Implementation guidance:**
- If a control lists only your persona, you are fully responsible
- If a control lists both personas, coordinate with your counterparts
- If a control lists the other persona, ensure your supply chain partners address it

## Persona-Specific Risk Visibility

### Model Creator Risk Visibility
Model Creators have deep visibility into:
- Training data composition and quality
- Model architecture and weights
- Training process and hyperparameters
- Model evaluation metrics
- Known model limitations

Model Creators have limited visibility into:
- How models are deployed by consumers
- Application-level prompt engineering
- Runtime input patterns
- User interaction contexts

### Model Consumer Risk Visibility
Model Consumers have deep visibility into:
- Application architecture and integration
- User input patterns and contexts
- Runtime behavior and performance
- Output usage and impact
- User feedback and incidents

Model Consumers have limited visibility into:
- Training data composition
- Model architecture internals
- Training process details
- Model evaluation procedures
- Upstream supply chain security

## Best Practices

### For Model Creators
1. **Provide Security Documentation**: Supply Model Consumers with security characteristics, limitations, and recommended usage patterns
2. **Implement Model Cards**: Document model capabilities, training data, evaluation results, and known risks
3. **Offer Secure Distribution**: Provide cryptographically signed model artifacts with integrity verification
4. **Support Incident Response**: Establish channels for Model Consumers to report security issues

### For Model Consumers
1. **Evaluate Model Provenance**: Assess the trustworthiness of model sources
2. **Understand Model Limitations**: Review model documentation and security characteristics
3. **Implement Defense in Depth**: Don't rely solely on model-level security
4. **Monitor Runtime Behavior**: Detect anomalies and potential attacks in production
5. **Plan for Model Updates**: Establish processes for updating models when vulnerabilities are discovered

## References

For complete persona definitions, see:
- `yaml/personas.yaml` in the CoSAI repository
- Persona-specific control assignments in `yaml/controls.yaml`
