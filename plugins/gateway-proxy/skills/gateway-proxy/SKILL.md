---
name: gateway-proxy
description: Expert guidance for configuring kgateway and agentgateway for AI/LLM routing, MCP server routing, and API gateway patterns. Use when setting up gateway proxies for Ollama, OpenAI, Anthropic, Gemini backends, configuring HTTPRoutes, troubleshooting Gateway API issues, or working with OrbStack Kubernetes networking.
metadata:
  version: 1.1.0
  author: J. Greg Williams
  license: MIT
---

# Gateway Proxy

Expert guidance for configuring Kubernetes Gateway API with agentgateway for AI workloads.

## Overview

This skill covers kgateway (Kubernetes Gateway API implementation) and agentgateway (AI-specific extension) for routing to:

- **LLM Providers**: Ollama (local), OpenAI, Anthropic, Gemini
- **MCP Servers**: Model Context Protocol endpoints via HTTP/SSE
- **Unified API Gateway**: Single entry point with path-based routing
- **External Processing**: Delegate request/response handling to gRPC services for custom mutations and routing

## Quick Commands

This plugin includes slash commands for common gateway operations:

| Command | Purpose |
|---------|---------|
| `/gw-status` | Show all gateway resources status |
| `/gw-logs [count\|controller]` | Tail controller logs for debugging |
| `/gw-debug` | Full diagnostic with events and recommendations |
| `/gw-backend <provider>` | Generate backend YAML (ollama, openai, anthropic, gemini) |
| `/gw-route <name>` | Generate HTTPRoute YAML with path rewriting |

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

### HTTPRoute
Gateway API routes with path-based matching and URL rewriting.

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

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: openai-api-key
  namespace: kgateway-system
stringData:
  api-key: "${OPENAI_API_KEY}"
---
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

### HTTPRoute with Path Rewriting

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: ollama-route
  namespace: kgateway-system
spec:
  parentRefs:
  - name: ai-gateway
    namespace: kgateway-system
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /ollama
    filters:
    - type: URLRewrite
      urlRewrite:
        path:
          type: ReplacePrefixMatch
          replacePrefixMatch: /        # Strip prefix!
    backendRefs:
    - name: ollama-backend
      group: agentgateway.dev
      kind: AgentgatewayBackend
```

## Troubleshooting Quick Reference

| Error | Cause | Solution |
|-------|-------|----------|
| `spec.selector: Invalid value... field is immutable` | Deployment exists with different labels | Delete existing deployment first |
| `backends required DNS resolution which failed` | Backend hostname not resolvable | Use `host.internal` for OrbStack |
| `route not found` | HTTPRoute not attached to Gateway | Check parentRefs in HTTPRoute |
| `processing failed: failed to parse request: EOF` | GET request to LLM endpoint | LLM backends expect POST with JSON body |
| 404 errors on backend | Path prefix not stripped | Add URLRewrite filter with `ReplacePrefixMatch: /` |

## Debug Commands

```bash
# Check controller logs
kubectl -n kgateway-system logs -l app.kubernetes.io/name=kgateway --tail=50
kubectl -n kgateway-system logs -l app.kubernetes.io/name=agentgateway --tail=50

# Check gateway and backends
kubectl get gateway,agentgatewaybackend,httproute -n kgateway-system

# Check policies
kubectl get agentgatewaypolicy -n kgateway-system
```

## Reference Files

When you need more detail, load these reference files:

- **`references/lessons-learned.md`**: Critical gotchas, naming conflicts, OrbStack networking
- **`references/resource-patterns.md`**: Complete YAML examples for all resource types
- **`references/provider-backends.md`**: Provider-specific backend configurations (Ollama, OpenAI, Anthropic, Gemini)
- **`references/mcp-routing.md`**: MCP server backend and routing patterns
- **`references/external-processing.md`**: External Processing (ExtProc) for custom request/response mutations and routing

## Installation Requirements

- **kgateway v2.2.x+** required for agentgateway support
- Separate registries: `cr.kgateway.dev` (kgateway) and `cr.agentgateway.dev` (agentgateway)
- Enable agentgateway in kgateway: `--set controller.enableAgentgateway=true`
