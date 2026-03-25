# agentgateway

agentgateway is a Linux Foundation project that extends the Kubernetes Gateway API for AI/agentic workloads, acting as a proxy for LLM provider routing, MCP server routing, and external processing. Use this skill when configuring LLM backends (Ollama, OpenAI, Anthropic, Gemini, Vertex AI, Azure OpenAI, Bedrock), setting up MCP server routing, applying traffic policies, or troubleshooting AI routing on Kubernetes. It is distinct from a generic ingress controller in that it understands AI-specific concerns like token-based rate limiting, provider auth secrets, and MCP protocol endpoints.

## Capabilities

- Configure LLM provider backends for Ollama, OpenAI, Anthropic, Gemini, Vertex AI, Azure OpenAI, and AWS Bedrock
- Route Model Context Protocol (MCP) server endpoints via HTTP/SSE using AgentgatewayBackend
- Apply traffic policies (rate limiting by requests and tokens, CORS, authentication) via AgentgatewayPolicy
- Delegate request/response handling to gRPC external processing services for custom mutations and routing
- Diagnose and debug AI routing failures using controller logs, CRD inspection, and gateway resource status
- Guide helm chart installation, upgrades, and rollbacks across agentgateway versions including the v2.3.0 repo split

## Current Metrics

**Score: 91/100** (Good) — 2026-03-22

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 89 | 80 | 100 | 100 |

## Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.0.0 | 2026-02-25 | [#61](https://github.com/totallyGreg/claude-mp/issues/61) | Split from gateway-proxy v2.0.0; agentgateway-focused skill | 98 | 88 | 80 | 100 | - | 91 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

## Active Work

- None.

## Known Issues

- None.

## Archive

- Git history: `git log --grep="agentgateway"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:enhancement+is:closed

---

*Run `uv run scripts/evaluate_skill.py <path> --update-readme` to refresh metrics.*
