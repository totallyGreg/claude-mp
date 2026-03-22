# gateway-manager

Kubernetes Gateway API (kgateway) and AI/LLM routing (agentgateway) management.

## Components

### Agent: gateway-manager
Manages kgateway and agentgateway resources on Kubernetes. Routes between kgateway (infrastructure) and agentgateway (AI routing) based on user intent.

### Skill: kgateway
Kubernetes Gateway API configuration and operations:
- Gateway resources, HTTPRoutes, GatewayClass configuration
- kgateway Backend CRD and Envoy-based control plane
- Helm chart installation, upgrades, and version lifecycle
- Route attachment troubleshooting

### Skill: agentgateway
AI/LLM provider routing and traffic policies:
- Provider backends: Ollama, OpenAI, Anthropic, Gemini, Vertex AI, Azure OpenAI, Bedrock
- MCP server routing and external processing
- Rate limiting, CORS, and traffic policy configuration
- Upgrade workflows and routing diagnostics

### Commands (8)
`/gw-backend`, `/gw-debug`, `/gw-eval`, `/gw-logs`, `/gw-route`, `/gw-status`, `/gw-upgrade`, `/gw-versions`

## Version History

| Version | Changes |
|---------|---------|
| 3.0.0 | Current release |
| 1.0.0 | Initial plugin with kgateway and agentgateway skills |
