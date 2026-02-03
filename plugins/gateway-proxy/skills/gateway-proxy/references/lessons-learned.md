# Lessons Learned: Configuring kgateway with agentgateway

Critical gotchas and insights discovered while implementing agentgateway on Kubernetes with kgateway.

## Installation Architecture

### Separate Registries

kgateway and agentgateway components are installed from **different OCI registries**:

| Component | Registry | Purpose |
|-----------|----------|---------|
| kgateway-crds | `cr.kgateway.dev/kgateway-dev/charts` | kgateway Custom Resource Definitions |
| kgateway | `cr.kgateway.dev/kgateway-dev/charts` | kgateway controller (Envoy-based) |
| agentgateway-crds | `cr.agentgateway.dev/charts` | agentgateway CRDs |
| agentgateway | `cr.agentgateway.dev/charts` | agentgateway controller |

### Version Requirements

- **kgateway v2.2.x or later is required** for agentgateway support
- Version format uses dots: `v2.2.0-rc.2` (not `v2.2.0-rc1`)

### Enable Flag

When installing kgateway with helm, enable agentgateway support:

```bash
helm upgrade -i kgateway oci://cr.kgateway.dev/kgateway-dev/charts/kgateway \
  --set controller.enableAgentgateway=true
```

This sets `KGW_ENABLE_AGENTGATEWAY=true` in the controller pod.

## Naming Conventions

### Gateway vs Controller Naming Conflict

**Critical**: The Gateway resource name creates a deployment with the same name. If you name your Gateway `agentgateway`, it will conflict with the agentgateway controller deployment.

**Solution**: Name your Gateway differently from the controller:
- Controller deployment: `agentgateway` (created by helm)
- Gateway resource: `ai-gateway` (or any other unique name)
- Data plane deployment: `ai-gateway` (created by Gateway controller)

### Deployment Selector Immutability

Kubernetes deployment selectors are immutable. If a deployment exists with different labels than what the controller wants to create, you'll get:

```
spec.selector: Invalid value: ... field is immutable
```

**Solution**: Delete the existing deployment before recreating the Gateway:

```bash
kubectl -n kgateway-system delete deployment <gateway-name>
```

## API Structure

### API Version

- API Group: `agentgateway.dev/v1alpha1`
- CRDs: `AgentgatewayBackend`, `AgentgatewayPolicy`, `AgentgatewayParameters`

### AgentgatewayBackend for LLM Providers

For AI/LLM backends, the structure is:

```yaml
spec:
  ai:
    provider:
      host: "<hostname>"           # Sibling to provider type
      port: <port>                 # Sibling to provider type
      openai:                      # Provider type (openai, anthropic, gemini)
        model: "<model-name>"
```

**Key insight**: `host` and `port` are at the same level as the provider type (`openai`), not inside it.

### AgentgatewayBackend for MCP Servers

For MCP (Model Context Protocol) backends:

```yaml
spec:
  mcp:
    targets:
    - static:
        host: "<hostname>"
        port: <port>
        protocol: sse             # Protocol goes INSIDE static, not at targets level
```

### AgentgatewayPolicy Targets

The `traffic` field in AgentgatewayPolicy can only target:
- `Gateway`
- `XListenerSet`
- `HTTPRoute`

It **cannot** target `AgentgatewayBackend` directly.

### CORS Configuration

CORS `allowOrigins` uses simple strings, not objects:

```yaml
# Correct
allowOrigins:
- "*"

# Wrong - will fail
allowOrigins:
- type: Exact
  value: "*"
```

The `maxAge` field is an integer (seconds), not a duration string:

```yaml
# Correct
maxAge: 86400

# Wrong
maxAge: "86400s"
```

## HTTPRoute Configuration

### Path Prefix Handling

When routing to AgentgatewayBackend for LLM providers, the path prefix must be stripped:

```yaml
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
        replacePrefixMatch: /     # Strip /ollama prefix
  backendRefs:
  - name: ollama-backend
    group: agentgateway.dev
    kind: AgentgatewayBackend
```

Without this, requests like `/ollama/v1/chat/completions` are sent to the backend as-is, causing 404 errors.

### Parent Gateway References

HTTPRoutes must reference the Gateway by name in `parentRefs`:

```yaml
parentRefs:
- name: ai-gateway    # Must match Gateway metadata.name
  namespace: kgateway-system
```

## OrbStack-Specific Configuration

### Accessing Host Services from Kubernetes

From within OrbStack's Kubernetes cluster:
- **Wrong**: `host.orbstack.internal` (not resolvable from K8s)
- **Correct**: `host.internal` (resolves to `0.250.250.254`)

```bash
# Test from within cluster
kubectl run test --rm -it --image=busybox -- nslookup host.internal
# Returns: 0.250.250.254
```

### Disable Rosetta (Apple Silicon)

On Apple Silicon Macs, kgateway requires Rosetta to be **disabled** in OrbStack to avoid assertion failures in the proxy.

### Service Exposure

All standard Kubernetes service types work out-of-the-box in OrbStack:

- **LoadBalancer & Ingress**: Exposed on `localhost` and `*.k8s.orb.local`
- **NodePort**: Accessible directly on `localhost:<NodePort>`
- **ClusterIP**: Directly routable from Mac
- **Pod IPs**: Directly accessible from Mac

No `kubectl port-forward` needed for basic access.

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `spec.selector: Invalid value... field is immutable` | Deployment exists with different labels | Delete existing deployment |
| `backends required DNS resolution which failed` | Backend hostname not resolvable | Use `host.internal` for OrbStack |
| `route not found` | HTTPRoute not attached to Gateway | Check parentRefs in HTTPRoute |
| `processing failed: failed to parse request: EOF` | GET request to LLM endpoint | LLM backends expect POST with JSON body |
| `model 'X' not found` | Wrong model in backend config | Update AgentgatewayBackend with correct model |

## Best Practices

1. **Always use different names** for Gateway resources and controller deployments
2. **Delete deployments** before recreating Gateways if you encounter selector conflicts
3. **Use `host.internal`** for OrbStack host access
4. **Strip path prefixes** in routes to LLM backends
5. **Check model availability** on the backend before configuring
6. **Use URL rewriting** with `ReplacePrefixMatch` for clean API paths
7. **Target HTTPRoute or Gateway** for traffic policies, not backends
