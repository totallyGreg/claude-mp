# MCP Server Routing

Configuration patterns for Model Context Protocol (MCP) server backends.

## MCP Backend Structure

MCP backends use the `mcp` spec instead of `ai`:

```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: mcp-backend
  namespace: kgateway-system
  labels:
    app: agentgateway
    type: mcp
spec:
  mcp:
    targets:
    - name: "test-everything"
      static:
        host: "localhost"
        port: 3000
        protocol: SSE           # Protocol is INSIDE static block
```

**Critical**: The `protocol` field goes inside `static`, not at the `targets` level.

## Supported Protocols

| Protocol | Description | Use Case |
|----------|-------------|----------|
| `SSE` | Server-Sent Events over HTTP | Streaming responses |
| `http_sse` | HTTP with SSE | Alternative name for SSE |

Future protocols (not yet supported in agentgateway):
- `stdio` - Standard I/O for local tools
- `websocket` - WebSocket connections

## Single MCP Server

Basic single-target configuration:

```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: mcp-backend
  namespace: kgateway-system
spec:
  mcp:
    targets:
    - name: "filesystem-server"
      static:
        host: "${MCP_SERVER_HOST}"
        port: ${MCP_SERVER_PORT}
        protocol: SSE
```

## Multiple MCP Servers

Multiple targets in a single backend:

```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: mcp-backend
  namespace: kgateway-system
spec:
  mcp:
    targets:
    - name: "filesystem"
      static:
        host: "mcp-filesystem.example.com"
        port: 3001
        protocol: SSE
    - name: "database"
      static:
        host: "mcp-database.example.com"
        port: 3002
        protocol: SSE
    - name: "search"
      static:
        host: "mcp-search.example.com"
        port: 3003
        protocol: SSE
```

## MCP HTTPRoute

MCP routes typically don't need path rewriting:

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

## Testing MCP Endpoints

```bash
gateway_address=$(kubectl get svc -n kgateway-system ai-gateway \
  -o jsonpath="{.status.loadBalancer.ingress[0]['hostname','ip']}")

# Test SSE endpoint
curl "http://${gateway_address}:8080/mcp/sse"

# Test with timeout (SSE connections may hang)
curl --max-time 5 "http://${gateway_address}:8080/mcp/sse"
```

## Environment Variables

```bash
MCP_TEST_SERVER_HOST=localhost   # MCP server host
MCP_TEST_SERVER_PORT=3000        # MCP server port
MCP_SERVER_NAME=test-everything  # Target name in backend
```

## Adding MCP Servers Dynamically

To add additional MCP servers to an existing backend:

```bash
# Get current backend config
kubectl get agentgatewaybackend mcp-backend -n kgateway-system -o yaml > mcp-backend.yaml

# Edit to add new target
# Then apply
kubectl apply -f mcp-backend.yaml
```

Or patch directly:

```bash
kubectl patch agentgatewaybackend mcp-backend -n kgateway-system --type=json \
  -p='[{"op": "add", "path": "/spec/mcp/targets/-", "value": {
    "name": "new-server",
    "static": {
      "host": "new-server.example.com",
      "port": 3004,
      "protocol": "SSE"
    }
  }}]'
```

## MCP Server CORS Requirements

If MCP servers need browser access, ensure CORS policy includes MCP-specific headers:

```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayPolicy
metadata:
  name: gateway-cors
spec:
  targetRefs:
  - group: gateway.networking.k8s.io
    kind: Gateway
    name: ai-gateway
  traffic:
    cors:
      allowHeaders:
      - Content-Type
      - Authorization
      - mcp-protocol-version    # MCP-specific header
      - cache-control
```

## Troubleshooting MCP

### MCP Server Not Responding

```bash
# Check if server is reachable from cluster
kubectl run test --rm -it --image=curlimages/curl --restart=Never \
  -- curl -v http://<host>:<port>/sse
```

### SSE Connection Timeout

SSE connections are long-lived. If testing with curl, use `--max-time`:

```bash
curl --max-time 5 "http://gateway:8080/mcp/sse"
```

### Check MCP Backend Status

```bash
kubectl get agentgatewaybackend mcp-backend -n kgateway-system -o yaml
kubectl describe agentgatewaybackend mcp-backend -n kgateway-system
```
