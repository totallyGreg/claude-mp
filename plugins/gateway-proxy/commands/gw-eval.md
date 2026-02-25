Evaluate the current kgateway/agentgateway configuration for issues and best practices.

Run the following diagnostic checks:

1. Resource inventory:
```bash
kubectl get gateway,agentgatewaybackend,httproute,agentgatewaypolicy -n kgateway-system -o wide
```

2. Version check:
```bash
helm list -n kgateway-system -o json 2>/dev/null | jq '.[] | {name: .name, chart: .chart, app_version: .app_version}'
```

3. Route-to-backend mapping:
```bash
kubectl get httproute -n kgateway-system -o json | jq '.items[] | {name: .metadata.name, backends: [.spec.rules[].backendRefs[]?.name]}'
```

4. Backends without routes (orphan check):
```bash
# Get all backend names and route backend refs, compare
echo "--- Backends ---"
kubectl get agentgatewaybackend -n kgateway-system -o jsonpath='{.items[*].metadata.name}'
echo ""
echo "--- Route backendRefs ---"
kubectl get httproute -n kgateway-system -o json | jq -r '[.items[].spec.rules[].backendRefs[]?.name] | unique | .[]'
```

5. Gateway health:
```bash
kubectl get gateway -n kgateway-system -o json | jq '.items[] | {name: .metadata.name, programmed: .status.conditions[] | select(.type=="Programmed") | .status}'
```

6. Pod status:
```bash
kubectl get pods -n kgateway-system -l 'app.kubernetes.io/name in (kgateway,agentgateway)' -o wide
```

7. GCP token freshness (if Vertex AI configured):
```bash
kubectl get secret vertexai-bearer-token -n kgateway-system -o jsonpath='{.metadata.annotations.last-refreshed}' 2>/dev/null
```

Reference the gateway-proxy skill for best practices.

## Evaluation Report

Present findings organized by severity:

### Critical
- Routes pointing to non-existent backends
- Gateway not programmed (Programmed condition != True)
- Controller pods not running or in CrashLoopBackOff

### Warning
- Backends with no corresponding HTTPRoute (orphaned)
- Stale versions (installed != latest stable release)
- RC/beta versions in use
- Secrets referenced by backends but not found
- GCP token last refresh > 60 minutes ago
- CORS policy using `allowOrigins: ["*"]`

### Info
- No rate limiting policy configured
- No authentication policy on Gateway
- Debug logging enabled (AgentgatewayParameters level: debug)
- Gateway name matches controller deployment name (potential conflict)

### Recommendations
- List specific fixes with YAML snippets where applicable
- Prioritize: critical > warning > info
- For proactive remediation, suggest using the gateway-manager agent
