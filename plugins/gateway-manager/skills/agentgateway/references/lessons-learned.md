# Lessons Learned: agentgateway

Critical gotchas and insights for agentgateway on Kubernetes.

## Installation Architecture

### Separate Registry

agentgateway components are installed from their own OCI registry:

| Component | Registry | Purpose |
|-----------|----------|---------|
| agentgateway-crds | `cr.agentgateway.dev/charts` | agentgateway CRDs |
| agentgateway | `cr.agentgateway.dev/charts` | agentgateway controller |

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

## OrbStack-Specific Configuration

### Accessing Host Services from Kubernetes

From within OrbStack's Kubernetes cluster:
- **Wrong**: `host.orbstack.internal` (not resolvable from K8s)
- **Correct**: `host.internal` (resolves to `0.250.250.254`)

### Service Exposure

All standard Kubernetes service types work out-of-the-box in OrbStack. No `kubectl port-forward` needed for basic access.

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `backends required DNS resolution which failed` | Backend hostname not resolvable | Use `host.internal` for OrbStack |
| `processing failed: failed to parse request: EOF` | GET request to LLM endpoint | LLM backends expect POST with JSON body |
| `model 'X' not found` | Wrong model in backend config | Update AgentgatewayBackend with correct model |

## Local vs Cloud Deployment

Auth strategies and networking differ between local development and cloud deployments:

| Concern | Local (OrbStack) | Cloud (GKE/EKS/AKS) |
|---------|-------------------|---------------------|
| Host access | `host.internal` (resolves to `0.250.250.254`) | Service DNS or external endpoints |
| GCP auth | Mounted ADC file + CronJob token refresh | Workload Identity (automatic) |
| AWS auth | Mounted credentials file or env vars | IAM Roles for Service Accounts (IRSA) |
| Azure auth | API key in Secret | Managed Identity or API key |
| Egress | Direct outbound HTTPS | May need VPC/firewall rules for `*.googleapis.com`, `*.openai.azure.com` |
| TLS | Optional (HTTP on port 8080) | Recommended (terminate at gateway or ingress) |
| Authentication | Optional for local dev | Required — unauthenticated gateways expose API credits |

## Best Practices

1. **Use `kubectl create secret`** instead of YAML `stringData` for API keys
2. **Scope RBAC** for token refresh CronJobs to specific `resourceNames`
3. **Check model availability** on the backend before configuring
4. **Target HTTPRoute or Gateway** for traffic policies, not backends
5. **Use `host.internal`** for OrbStack host access

## v2.3.0 Migration Notes

Starting with agentgateway v2.3.0:
- agentgateway installs to **`agentgateway-system`** namespace (not `kgateway-system`)
- agentgateway control plane migrates to `agentgateway/agentgateway` repo
- agentgateway is now a **Linux Foundation** project

See `references/helm-lifecycle.md` for detailed migration steps.
