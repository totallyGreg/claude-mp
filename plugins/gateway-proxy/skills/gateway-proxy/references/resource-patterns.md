# Resource Patterns

Complete YAML examples for all agentgateway resource types.

## AgentgatewayParameters

Configures the agentgateway proxy deployment:

```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayParameters
metadata:
  name: agentgateway-params
  namespace: kgateway-system
spec:
  logging:
    level: info        # debug, info, warn, error
    format: text       # text or json
  resources:
    requests:
      memory: "128Mi"
      cpu: "100m"
    limits:
      memory: "256Mi"
      cpu: "500m"
```

## Gateway

Creates the agentgateway data plane with LoadBalancer service:

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

## AgentgatewayPolicy - Rate Limiting

Request-based rate limiting on Gateway:

```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayPolicy
metadata:
  name: gateway-rate-limit
  namespace: kgateway-system
  labels:
    app: agentgateway
spec:
  targetRefs:
  - group: gateway.networking.k8s.io
    kind: Gateway
    name: ai-gateway
  traffic:
    rateLimit:
      local:
      - requests: 100
        unit: Minutes           # Seconds, Minutes, Hours
        burst: 20
```

## AgentgatewayPolicy - Token Rate Limiting

Token-based rate limiting on HTTPRoutes:

```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayPolicy
metadata:
  name: ai-token-rate-limit
  namespace: kgateway-system
  labels:
    app: agentgateway
spec:
  targetSelectors:
  - group: gateway.networking.k8s.io
    kind: HTTPRoute
    matchLabels:
      app: agentgateway
  traffic:
    rateLimit:
      local:
      - tokens: 50000
        unit: Minutes
        burst: 10000
```

## AgentgatewayPolicy - CORS

CORS configuration for browser access:

```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayPolicy
metadata:
  name: gateway-cors
  namespace: kgateway-system
  labels:
    app: agentgateway
spec:
  targetRefs:
  - group: gateway.networking.k8s.io
    kind: Gateway
    name: ai-gateway
  traffic:
    cors:
      allowOrigins:
      - "*"                      # Simple strings, NOT objects
      allowMethods:
      - GET
      - POST
      - PUT
      - DELETE
      - OPTIONS
      allowHeaders:
      - Content-Type
      - Authorization
      - X-Requested-With
      - Accept
      - Origin
      - mcp-protocol-version
      - cache-control
      exposeHeaders:
      - Content-Length
      - Content-Type
      maxAge: 86400              # Integer seconds, NOT duration string
      allowCredentials: false
```

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

## Installation Sequence

Complete installation in order:

```bash
# 1. Gateway API CRDs
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.1/standard-install.yaml

# 2. kgateway CRDs
helm upgrade -i kgateway-crds oci://cr.kgateway.dev/kgateway-dev/charts/kgateway-crds \
  --version v2.2.0-rc.2 --namespace kgateway-system --create-namespace

# 3. kgateway controller with agentgateway enabled
helm upgrade -i kgateway oci://cr.kgateway.dev/kgateway-dev/charts/kgateway \
  --version v2.2.0-rc.2 --namespace kgateway-system \
  --set controller.enableAgentgateway=true

# 4. agentgateway CRDs
helm upgrade -i agentgateway-crds oci://cr.agentgateway.dev/charts/agentgateway-crds \
  --version v2.2.0-rc.2 --namespace kgateway-system

# 5. agentgateway controller
helm upgrade -i agentgateway oci://cr.agentgateway.dev/charts/agentgateway \
  --version v2.2.0-rc.2 --namespace kgateway-system
```

## Cleanup Patterns

### Remove Specific Backend

```bash
backend_name="openai-backend"

# Delete backend
kubectl delete agentgatewaybackend "${backend_name}" -n kgateway-system

# Delete associated secret (if exists)
secret_name="${backend_name%-backend}-api-key"
kubectl delete secret "${secret_name}" -n kgateway-system 2>/dev/null

# Delete route
kubectl delete httproute "${backend_name%-backend}-route" -n kgateway-system
```

### Full Cleanup

```bash
# Delete routes and policies by label
kubectl delete httproute -n kgateway-system -l app=agentgateway
kubectl delete agentgatewaypolicy -n kgateway-system -l app=agentgateway

# Delete backends
kubectl delete agentgatewaybackend -n kgateway-system -l app=agentgateway

# Delete gateway
kubectl delete gateway ai-gateway -n kgateway-system

# Delete parameters
kubectl delete agentgatewayparameters agentgateway-params -n kgateway-system
```
