# CoSAI Personas Guide

The CoSAI Risk Map framework defines ten personas (8 active, 2 deprecated) aligned with ISO/IEC 22989 AI actor terminology. These personas identify who is impacted by risks and who is responsible for enacting controls across the AI ecosystem.

## Active Personas

### Model Provider (`personaModelProvider`)

**ISO 22989 mapping:** AI Producer

**Definition:** Actors that develop, train, evaluate, and tune AI/ML models (foundation models, specialized models, or domain-adapted models). Includes those developing models from scratch or significantly modifying existing models for distribution.

**Responsibilities:**
- Model architecture design and training
- Model evaluation and validation
- Model documentation and cards
- Model versioning and updates

**Examples:** Research labs developing foundation models, companies fine-tuning open-source models, organizations training domain-specific models.

### Data Provider (`personaDataProvider`)

**ISO 22989 mapping:** AI Partner (data supplier)

**Definition:** Actors that supply training data, evaluation datasets, or inference data to model providers or application developers. Includes data aggregators, data marketplaces, and those licensing datasets.

**Responsibilities:**
- Data quality assurance
- Data provenance tracking
- Data licensing and compliance
- Data privacy protections

**Examples:** Data aggregation companies, dataset curators, data marketplace operators.

### AI Platform Provider (`personaPlatformProvider`)

**ISO 22989 mapping:** AI Partner (infrastructure provider)

**Definition:** Actors that provide infrastructure, compute resources, APIs, and platform services for AI model hosting, training, or inference. Includes cloud providers, MLOps platforms, and model API services.

**Responsibilities:**
- Infrastructure security and availability
- API security and rate limiting
- Compute resource allocation
- Model hosting and serving

**Examples:** Cloud providers (AWS, Azure, GCP), MLOps platforms, model API services.

### AI Model Serving (`personaModelServing`)

**Definition:** The entity responsible for provisioning, managing, and securing the runtime environment that serves AI/ML model predictions at scale. Covers all model types and focuses on secure execution of predictions.

**Responsibilities:**
- Manage and secure model serving API endpoints
- Perform runtime input validation and sanitization
- Execute models within isolated or confidential computing environments
- Enforce granular model and data access controls
- Verify model and data integrity at load-time and runtime
- Secure orchestration and routing of serving requests
- Monitor, validate, and sanitize model outputs
- Implement runtime privacy-enhancing technologies

**Examples:** Model inference infrastructure teams, serving platform operators.

### Agentic Platform and Framework Providers (`personaAgenticProvider`)

**ISO 22989 mapping:** AI Partner (tooling provider)

**Definition:** Actors that provide development environments, software frameworks, and orchestration runtimes for agentic reasoning, planning, and tool execution.

**Responsibilities:**
- Framework security and sandboxing
- Tool execution safety controls
- State management security
- API integration security
- Cognitive architecture safety guardrails

**Identification questions:**
- Is your system responsible for deciding which tool an AI model should use next?
- Does your platform manage the state or history of a multi-turn agentic workflow?
- Are you providing the glue that connects an LLM to an API?
- Are you maintaining a library or SDK that abstracts the complexity of LLM tool-calling?
- Does your software define the cognitive architecture (loops, reasoning steps) for an AI system?

**Examples:** LangChain, Semantic Kernel, Vertex AI Agent Builder, OpenAI Assistants API.

### Application Developer (`personaApplicationDeveloper`)

**ISO 22989 mapping:** AI Consumer (application builder)

**Definition:** Actors that integrate AI models (via APIs or embedded models) into applications, products, or services. They may consume models without modifying them, or perform light customization (prompt engineering, RAG, etc.).

**Responsibilities:**
- Application-level security controls
- Input validation and sanitization
- Output filtering and monitoring
- User access controls

**Examples:** SaaS companies adding AI features, enterprises deploying chatbots, product teams integrating LLMs.

### AI System Governance (`personaGovernance`)

**Definition:** Actors responsible for defining security control objectives, measuring implementations, and enforcing compliance for AI systems across the lifecycle. Includes AI risk officers, compliance teams, and governance boards.

**Responsibilities:**
- Security control objectives definition
- Implementation measurement and monitoring
- Compliance enforcement
- Risk assessment and management
- Incident response coordination

**Examples:** AI risk officers, compliance teams, governance boards, internal audit teams.

### AI System Users (`personaEndUser`)

**ISO 22989 mapping:** AI Consumer (end user)

**Definition:** Actors that use AI-powered applications or services without developing or deploying the AI components themselves.

**Responsibilities:**
- Appropriate use of AI systems
- Reporting issues or anomalies
- Following usage policies
- Data minimization (user inputs)

**Examples:** Business users of AI tools, consumers of AI-powered products.

## Deprecated Personas

### ~~Model Creator~~ (`personaModelCreator`) -- DEPRECATED

Superseded by **Model Provider** for training/tuning activities, or **Application Developer** for integration activities.

### ~~Model Consumer~~ (`personaModelConsumer`) -- DEPRECATED

Superseded by **Application Developer** for application building, or **AI System Users** for end-user activities.

## Determining Your Persona

Organizations may map to multiple personas. Use these questions:

1. **Do you train or fine-tune models?** → Model Provider
2. **Do you supply datasets to model builders?** → Data Provider
3. **Do you provide compute/hosting infrastructure?** → AI Platform Provider
4. **Do you manage model serving endpoints?** → AI Model Serving
5. **Do you build agentic frameworks or tools?** → Agentic Platform Provider
6. **Do you integrate models into applications?** → Application Developer
7. **Do you define security policies and compliance?** → Governance
8. **Do you use AI-powered applications?** → End User

Most organizations hold 2-3 personas simultaneously. Apply controls from each applicable persona.

## Control Assignment by Persona

Controls in `controls.yaml` specify applicable personas:

```yaml
personas:
  - personaModelProvider
  - personaApplicationDeveloper
```

**Implementation guidance:**
- If a control lists only your persona, you are fully responsible
- If a control lists multiple personas, coordinate with counterparts
- If a control lists a different persona, ensure your supply chain partners address it

## References

For complete persona definitions, see:
- `yaml/personas.yaml` in the CoSAI repository
- Persona-specific control assignments in `yaml/controls.yaml`
- ISO/IEC 22989:2022 for AI actor terminology
