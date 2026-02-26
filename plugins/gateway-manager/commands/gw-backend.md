Generate an AgentgatewayBackend YAML template for the specified provider.
$ARGUMENTS

Supported providers: ollama, openai, anthropic, gemini, vertexai, azureopenai, bedrock

If no provider specified, list the available providers and their requirements.

## Simple Providers

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
- Create the secret first, then the backend

Secret creation (preferred — avoids keys in YAML output):
```bash
kubectl create secret generic <provider>-api-key \
  --from-literal=api-key="${<PROVIDER>_API_KEY}" \
  -n kgateway-system --dry-run=client -o yaml | kubectl apply -f -
```

Backend YAML:
```yaml
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

## Cloud Providers

For **vertexai**, **azureopenai**, **bedrock**:
- These providers require additional auth configuration beyond a simple API key
- Generate the basic backend YAML below
- For full setup including token refresh (Vertex AI) or IAM credentials (Bedrock), use the gateway-manager agent: "set up Vertex AI routing" or "add Azure OpenAI backend"

For **vertexai**:
```yaml
# NOTE: Vertex AI requires GCP access token refresh every 60 minutes.
# Use the gateway-manager agent for complete setup with CronJob-based token refresh.
# Create token secret first:
#   TOKEN=$(gcloud auth application-default print-access-token)
#   kubectl create secret generic vertexai-bearer-token \
#     --from-literal=Authorization="Bearer ${TOKEN}" -n kgateway-system
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: vertexai-backend
  namespace: kgateway-system
spec:
  ai:
    provider:
      vertexai:
        model: "claude-sonnet-4-20250514"
        projectId: "<your-gcp-project>"
        region: "us-east5"
  policies:
    auth:
      secretRef:
        name: vertexai-bearer-token
```

For **azureopenai**:
```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: azureopenai-backend
  namespace: kgateway-system
spec:
  ai:
    provider:
      azureopenai:
        model: "gpt-4o"
        deploymentName: "<your-deployment>"
        apiVersion: "2024-10-21"
      host: "<your-resource>.openai.azure.com"
      port: 443
  policies:
    auth:
      secretRef:
        name: azureopenai-api-key
```

For **bedrock**:
```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: bedrock-backend
  namespace: kgateway-system
spec:
  ai:
    provider:
      bedrock:
        model: "anthropic.claude-sonnet-4-20250514-v1:0"
        region: "us-east-1"
  policies:
    auth:
      secretRef:
        name: bedrock-credentials
```

Output the complete YAML that can be applied with `kubectl apply -f`.

Include comments explaining:
- Required environment variables or secrets
- Common model options for the selected provider
- How to test the backend after creation

Reference the agentgateway skill's `references/provider-backends.md` for detailed patterns including token lifecycle, RBAC, and environment-specific auth.
