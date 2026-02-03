Generate an AgentgatewayBackend YAML template for the specified provider.
$ARGUMENTS

Supported providers: ollama, openai, anthropic, gemini

If no provider specified, list the available providers and their requirements.

Based on the provider argument, generate the appropriate YAML:

For **ollama**:
- No API key required
- Uses `host.internal` for OrbStack host access
- OpenAI-compatible API

```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: ollama-backend
  namespace: kgateway-system
spec:
  ai:
    provider:
      openai:
        model: "llama3.2"
      host: "host.internal"
      port: 11434
```

For **openai**, **anthropic**, **gemini**:
- Requires Secret with API key
- Include both Secret and AgentgatewayBackend resources

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: <provider>-api-key
  namespace: kgateway-system
stringData:
  api-key: "${<PROVIDER>_API_KEY}"
---
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: <provider>-backend
  namespace: kgateway-system
spec:
  ai:
    provider:
      <provider>:
        model: "<default-model>"
  policies:
    auth:
      secretRef:
        name: <provider>-api-key
```

Output the complete YAML that can be applied with `kubectl apply -f`.

Include comments explaining:
- Required environment variables
- Common model options
- How to test the backend after creation

Reference the gateway-proxy skill for detailed patterns.
