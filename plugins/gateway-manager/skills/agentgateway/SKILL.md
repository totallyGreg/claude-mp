---
name: agentgateway
description: This skill should be used when configuring agentgateway for AI/LLM provider routing, MCP server routing, external processing, and traffic policies. Use when the user asks to "add an LLM provider backend", "configure MCP routing", "set up Ollama backend", "add OpenAI backend", "configure Anthropic", "add Vertex AI backend", "set up rate limiting", "configure CORS", "add external processing", "upgrade agentgateway", or "troubleshoot AI routing". Supports Ollama, OpenAI, Anthropic, Gemini, Vertex AI, Azure OpenAI, and Bedrock backends.
metadata:
  version: 1.0.0
  author: J. Greg Williams
  license: MIT
---

# agentgateway

Expert guidance for agentgateway — the AI/agentic proxy for LLM routing, MCP server routing, and external processing on Kubernetes.

## Overview

agentgateway is a Linux Foundation project that extends Kubernetes Gateway API for AI workloads. It provides:

- **LLM Provider Routing**: Ollama (local), OpenAI, Anthropic, Gemini, Vertex AI (GCP), Azure OpenAI, AWS Bedrock
- **MCP Server Routing**: Model Context Protocol endpoints via HTTP/SSE
- **External Processing**: Delegate request/response handling to gRPC services for custom mutations and routing
- **Traffic Policies**: Rate limiting (requests and tokens), CORS, authentication via AgentgatewayPolicy

**Note**: Starting v2.3.0, agentgateway diverges from kgateway into its own repo (`agentgateway/agentgateway`) and namespace (`agentgateway-system`). See `references/helm-lifecycle.md`.

## Quick Commands

This plugin includes slash commands for gateway operations:

| Command | Purpose |
|---------|---------|
| `/gw-status` | Show all gateway resources status |
| `/gw-logs [count\|controller]` | Tail controller logs for debugging |
| `/gw-debug` | Full diagnostic with events and recommendations |
| `/gw-backend <provider>` | Generate backend YAML (ollama, openai, anthropic, gemini, vertexai, azureopenai, bedrock) |
| `/gw-eval` | Evaluate current config against best practices |
| `/gw-versions` | Compare installed vs latest helm chart versions |
| `/gw-upgrade [component]` | Guide helm chart upgrades with pre/post validation |

The **gateway-manager agent** handles multi-step workflows: "add an Anthropic backend", "set up Vertex AI routing", "upgrade my gateway", "why isn't my route working".

## Architecture

```
                    ┌─────────────────────────────────────┐
                    │         agentgateway proxy          │
                    │      (port 8080 - LoadBalancer)     │
                    └─────────────┬───────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
   /ollama/*              /anthropic/*                 /mcp/*
   /openai/*              /gemini/*
        │                        │                          │
        ▼                        ▼                          ▼
┌───────────────┐       ┌───────────────┐         ┌───────────────┐
│AgentgatewayBackend    │AgentgatewayBackend      │AgentgatewayBackend
│   (AI type)   │       │   (AI type)   │         │  (MCP type)   │
└───────────────┘       └───────────────┘         └───────────────┘
```

## Key Resources

### AgentgatewayParameters
Configures the agentgateway proxy deployment (logging, resources).

### AgentgatewayBackend
Routes to LLM providers or MCP servers. Two types:
- **AI Backend**: `spec.ai.provider` with host/port and provider type
- **MCP Backend**: `spec.mcp.targets` for MCP server endpoints

### AgentgatewayPolicy
Traffic policies targeting Gateway or HTTPRoute:
- Rate limiting (requests and tokens)
- CORS configuration
- Authentication

## Common Patterns

### Local Ollama Backend

```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: ollama-backend
  namespace: kgateway-system
spec:
  ai:
    provider:
      openai:                    # Ollama is OpenAI-compatible
        model: "llama3.2"
      host: "host.internal"      # OrbStack host access
      port: 11434
```

### Cloud Provider Backend (with Secret)

Create the secret first (preferred — avoids keys in output):
```bash
kubectl create secret generic openai-api-key \
  --from-literal=api-key="${OPENAI_API_KEY}" \
  -n kgateway-system --dry-run=client -o yaml | kubectl apply -f -
```

Then create the backend:
```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: openai-backend
  namespace: kgateway-system
spec:
  ai:
    provider:
      openai:
        model: "gpt-4o-mini"
  policies:
    auth:
      secretRef:
        name: openai-api-key
```

## Version Awareness

The agent and `/gw-versions` command check for updates live:
- Fetches latest releases from `agentgateway/agentgateway`
- Compares against installed helm chart versions
- Warns about docs-vs-reality drift (features documented on `main` may not exist in released versions)
- Always inspect installed CRD to verify field availability

## Troubleshooting Quick Reference

| Error | Cause | Solution |
|-------|-------|----------|
| `backends required DNS resolution which failed` | Backend hostname not resolvable | Use `host.internal` for OrbStack |
| `processing failed: failed to parse request: EOF` | GET request to LLM endpoint | LLM backends expect POST with JSON body |
| `model 'X' not found` | Wrong model in backend config | Update AgentgatewayBackend with correct model |

## Debug Commands

```bash
# Check agentgateway controller logs
kubectl -n kgateway-system logs -l app.kubernetes.io/name=agentgateway --tail=50

# Check backends and policies
kubectl get agentgatewaybackend,agentgatewaypolicy -n kgateway-system

# Describe a backend for detail
kubectl describe agentgatewaybackend <name> -n kgateway-system
```

## Reference Files

When you need more detail, load these reference files:

- **`references/provider-backends.md`**: All 7 provider configurations (Ollama, OpenAI, Anthropic, Gemini, Vertex AI, Azure OpenAI, Bedrock), token lifecycle, secret management
- **`references/resource-patterns.md`**: AgentgatewayBackend, AgentgatewayPolicy, AgentgatewayParameters YAML examples
- **`references/mcp-routing.md`**: MCP server backend and routing patterns
- **`references/external-processing.md`**: External Processing (ExtProc) for custom request/response mutations and routing
- **`references/helm-lifecycle.md`**: agentgateway installation, upgrade, rollback, version checking
- **`references/lessons-learned.md`**: API structure gotchas, CORS pitfalls, local vs cloud deployment patterns

## Installation Requirements

- **kgateway v2.2.x+** required for agentgateway support (pre-v2.3.0)
- Registry: `cr.agentgateway.dev` (agentgateway)
- Enable agentgateway in kgateway: `--set controller.enableAgentgateway=true` (pre-v2.3.0)
- See `references/helm-lifecycle.md` for complete installation sequence
