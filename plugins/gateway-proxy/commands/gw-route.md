Generate an HTTPRoute YAML template for routing to a backend.
$ARGUMENTS

The argument should be the route name (e.g., "ollama", "openai", "mcp").

Generate an HTTPRoute that:
1. Attaches to the ai-gateway Gateway
2. Matches the path prefix /<name>
3. Includes URLRewrite filter to strip the prefix (for AI backends)
4. References the corresponding AgentgatewayBackend

For AI backends (ollama, openai, anthropic, gemini):
- Include URLRewrite with `ReplacePrefixMatch: /`

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: <name>-route
  namespace: kgateway-system
spec:
  parentRefs:
  - name: ai-gateway
    namespace: kgateway-system
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /<name>
    filters:
    - type: URLRewrite
      urlRewrite:
        path:
          type: ReplacePrefixMatch
          replacePrefixMatch: /
    backendRefs:
    - name: <name>-backend
      group: agentgateway.dev
      kind: AgentgatewayBackend
```

For MCP backends:
- No URL rewriting needed (remove the filters section)

Output the complete YAML ready for `kubectl apply`.

Include a test command to verify the route works after creation:
```bash
# Test the route (replace with actual endpoint)
curl -X POST http://<gateway-ip>/<name>/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "<model>", "messages": [{"role": "user", "content": "Hello"}]}'
```

Reference the gateway-proxy skill for detailed patterns.
