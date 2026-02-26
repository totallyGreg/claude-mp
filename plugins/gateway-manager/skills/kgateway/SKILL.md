---
name: kgateway
description: This skill should be used when configuring kgateway (Kubernetes Gateway API implementation) for HTTP routing, Gateway resources, HTTPRoutes, and GatewayClass configuration. Use when the user asks to "create a Gateway resource", "configure HTTPRoute", "set up path-based routing", "check kgateway installation", "install kgateway", "upgrade kgateway helm chart", or "troubleshoot route attachment". Covers Gateway API standards, kgateway Backend CRD, and Envoy-based control plane on Kubernetes.
metadata:
  version: 1.0.0
  author: J. Greg Williams
  license: MIT
---

# kgateway

Expert guidance for kgateway — the Kubernetes Gateway API implementation powered by Envoy.

## Overview

kgateway is a CNCF sandbox project that implements the Kubernetes Gateway API. It provides:

- **Gateway API compliance**: Gateway, HTTPRoute, GatewayClass resources
- **Envoy-based data plane**: Production-grade proxy
- **Backend CRD**: `Backend` (`gateway.kgateway.dev/v1alpha1`) for generic backends (AWS Lambda, Static, DFP)
- **agentgateway integration**: Enable AI/MCP routing via `--set controller.enableAgentgateway=true`

**Note**: Starting v2.3.0, kgateway and agentgateway diverge into separate projects. kgateway focuses on Envoy-based Gateway API; agentgateway moves to its own repo and namespace. See `references/helm-lifecycle.md`.

## Quick Commands

This plugin includes slash commands for gateway operations:

| Command | Purpose |
|---------|---------|
| `/gw-status` | Show all gateway resources status |
| `/gw-logs [count\|controller]` | Tail controller logs for debugging |
| `/gw-debug` | Full diagnostic with events and recommendations |
| `/gw-route <name>` | Generate HTTPRoute YAML with path rewriting |
| `/gw-versions` | Compare installed vs latest helm chart versions |
| `/gw-upgrade [component]` | Guide helm chart upgrades with pre/post validation |

The **gateway-manager agent** handles multi-step workflows involving both kgateway and agentgateway.

## Key Resources

### Gateway

Creates the data plane proxy deployment with a LoadBalancer service:

```yaml
kind: Gateway
apiVersion: gateway.networking.k8s.io/v1
metadata:
  name: ai-gateway              # Must NOT conflict with controller deployment names
  namespace: kgateway-system
spec:
  gatewayClassName: agentgateway # or "kgateway" for generic backends
  listeners:
  - protocol: HTTP
    port: 8080
    name: http
    allowedRoutes:
      namespaces:
        from: All
```

### HTTPRoute

Gateway API routes with path-based matching and URL rewriting:

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

### Backend CRD (kgateway-native)

For generic backends using kgateway's own CRD:

```yaml
apiVersion: gateway.kgateway.dev/v1alpha1
kind: Backend
metadata:
  name: my-backend
  namespace: kgateway-system
spec:
  type: Static
  # Backend-specific configuration
```

### GatewayClass

Two GatewayClasses are available — match your CRD to the class:

| GatewayClass | Backend CRD | API Group | Purpose |
|---|---|---|---|
| `kgateway` | `Backend` | `gateway.kgateway.dev/v1alpha1` | Generic backends |
| `agentgateway` | `AgentgatewayBackend` | `agentgateway.dev/v1alpha1` | AI/MCP backends |

## Installation

```bash
# 1. Gateway API CRDs (upstream)
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.1/standard-install.yaml

# 2. kgateway CRDs
helm upgrade -i kgateway-crds oci://cr.kgateway.dev/kgateway-dev/charts/kgateway-crds \
  --version v2.2.1 --namespace kgateway-system --create-namespace

# 3. kgateway controller (with agentgateway enabled)
helm upgrade -i kgateway oci://cr.kgateway.dev/kgateway-dev/charts/kgateway \
  --version v2.2.1 --namespace kgateway-system \
  --set controller.enableAgentgateway=true
```

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `spec.selector: Invalid value... field is immutable` | Deployment exists with different labels | Delete existing deployment first |
| `route not found` | HTTPRoute not attached to Gateway | Check parentRefs in HTTPRoute |
| 404 errors on backend | Path prefix not stripped | Add URLRewrite filter with `ReplacePrefixMatch: /` |

## Debug Commands

```bash
# Check controller logs
kubectl -n kgateway-system logs -l app.kubernetes.io/name=kgateway --tail=50

# Check gateway and routes
kubectl get gateway,httproute -n kgateway-system

# Verify GatewayClass
kubectl get gatewayclass
```

## Reference Files

When you need more detail, load these reference files:

- **`references/gateway-api-patterns.md`**: Gateway, HTTPRoute, GatewayClass patterns, Backend CRD disambiguation
- **`references/helm-lifecycle.md`**: kgateway installation, upgrade, rollback, version checking
- **`references/lessons-learned.md`**: Naming conflicts, OrbStack networking, deployment selector issues
