# Gateway API Patterns

Kubernetes Gateway API resource patterns for kgateway.

## Backend CRD Systems

Two separate backend systems exist — using the wrong one causes routes that don't resolve.

| CRD | API Group | Gateway Class | Purpose |
|-----|-----------|--------------|---------|
| `AgentgatewayBackend` | `agentgateway.dev/v1alpha1` | `agentgateway` | AI/MCP backends with native protocol translation |
| `Backend` | `gateway.kgateway.dev/v1alpha1` | `kgateway` | Generic backends (AWS Lambda, Static, DFP) with aiExtension sidecar |

**Rule**: Match CRD type to your Gateway's `gatewayClassName`.
- `gatewayClassName: agentgateway` → use `AgentgatewayBackend`
- `gatewayClassName: kgateway` → use `Backend`

**Common mistake**: Some older docs and helper scripts use the `Backend` CRD pattern. If your gateway uses `agentgateway` class, `Backend` resources will create resources that routes can't find.

To check which CRD system your gateway uses:

```bash
kubectl get gateway -n kgateway-system -o jsonpath='{.items[*].spec.gatewayClassName}'
```

## Gateway Resource

Creates the data plane proxy deployment with a LoadBalancer service:

```yaml
kind: Gateway
apiVersion: gateway.networking.k8s.io/v1
metadata:
  name: ai-gateway              # Must NOT be "agentgateway" (conflicts with controller)
  namespace: kgateway-system
  labels:
    app: agentgateway
spec:
  gatewayClassName: agentgateway
  infrastructure:
    parametersRef:
      name: agentgateway-params
      group: agentgateway.dev
      kind: AgentgatewayParameters
  listeners:
  - protocol: HTTP
    port: 8080
    name: http
    allowedRoutes:
      namespaces:
        from: All
```

## HTTPRoute for AI Backend

Routes with path prefix stripping:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: ollama-route
  namespace: kgateway-system
  labels:
    app: agentgateway
    backend: ollama-backend
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
          replacePrefixMatch: /           # Critical: strip the prefix
    backendRefs:
    - name: ollama-backend
      namespace: kgateway-system
      group: agentgateway.dev
      kind: AgentgatewayBackend
```

## HTTPRoute for MCP Backend

MCP routes don't need path rewriting:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: mcp-route
  namespace: kgateway-system
  labels:
    app: agentgateway
    backend: mcp-backend
spec:
  parentRefs:
  - name: ai-gateway
    namespace: kgateway-system
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /mcp
    backendRefs:
    - name: mcp-backend
      namespace: kgateway-system
      group: agentgateway.dev
      kind: AgentgatewayBackend
```

## Parent Gateway References

HTTPRoutes must reference the Gateway by name in `parentRefs`:

```yaml
parentRefs:
- name: ai-gateway    # Must match Gateway metadata.name
  namespace: kgateway-system
```

## Path Prefix Handling

When routing to backends for LLM providers, the path prefix must be stripped:

```yaml
filters:
- type: URLRewrite
  urlRewrite:
    path:
      type: ReplacePrefixMatch
      replacePrefixMatch: /     # Strip prefix
```

Without this, requests like `/ollama/v1/chat/completions` are sent to the backend as-is, causing 404 errors.

## Unified Route Creation Pattern

Dynamic route creation based on configured backends:

```bash
# Get list of configured backends
backends=$(kubectl get agentgatewaybackend -n kgateway-system -o jsonpath='{.items[*].metadata.name}')

# Create routes for each backend
for backend in ${backends}; do
  route_name="${backend%-backend}-route"
  path_prefix="/${backend%-backend}"

  # Determine if AI or MCP backend
  backend_type=$(kubectl get agentgatewaybackend "${backend}" -n kgateway-system -o jsonpath='{.spec}')

  if echo "${backend_type}" | grep -q '"mcp"'; then
    # MCP backend - no path rewriting
    # Create MCP route...
  else
    # AI backend - needs path rewriting
    # Create AI route with URLRewrite filter...
  fi
done
```
