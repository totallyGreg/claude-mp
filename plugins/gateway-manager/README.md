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

## Changelog

| Version | Changes |
|---------|---------|
| 3.0.0 | Current release |
| 1.0.0 | Initial plugin with kgateway and agentgateway skills |

## Skill: agentgateway

### Current Metrics

**Score: 91/100** (Good) — 2026-03-22

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 89 | 80 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.0.0 | 2026-02-25 | [#61](https://github.com/totallyGreg/claude-mp/issues/61) | Split from gateway-proxy v2.0.0; agentgateway-focused skill | 98 | 88 | 80 | 100 | - | 91 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)


## Skill: kgateway

### Current Metrics

**Score: 91/100** (Good) — 2026-03-22

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 98 | 90 | 80 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.0.0 | 2026-02-25 | [#61](https://github.com/totallyGreg/claude-mp/issues/61) | Split from gateway-proxy v2.0.0; kgateway-focused skill | 98 | 90 | 80 | 100 | - | 91 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

