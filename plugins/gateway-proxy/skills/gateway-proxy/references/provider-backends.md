# Provider Backend Configurations

Provider-specific AgentgatewayBackend configurations for each LLM provider.

## Ollama (Local)

Ollama is OpenAI-compatible and runs locally. No API key required.

```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: ollama-backend
  namespace: kgateway-system
  labels:
    app: agentgateway
    provider: ollama
spec:
  ai:
    provider:
      openai:                        # Ollama uses OpenAI-compatible API
        model: "llama3.2"            # Must match model pulled in Ollama
      host: "host.internal"          # OrbStack internal DNS for host access
      port: 11434
```

### Environment Variables

```bash
OLLAMA_HOST=host.internal    # Default for OrbStack
OLLAMA_PORT=11434            # Default Ollama port
OLLAMA_MODEL=llama3.2        # Model to use
```

### Verify Ollama Connectivity

```bash
# From within cluster
kubectl run test --rm -it --image=curlimages/curl --restart=Never \
  -- curl http://host.internal:11434/api/tags

# From host (OrbStack)
curl http://localhost:11434/api/tags
```

### Common Ollama Models

- `llama3.2` - Meta's Llama 3.2
- `mistral` - Mistral 7B
- `codellama` - Code Llama
- `phi3` - Microsoft Phi-3
- `gemma2` - Google Gemma 2

## OpenAI

Requires `OPENAI_API_KEY` environment variable.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: openai-api-key
  namespace: kgateway-system
  labels:
    app: agentgateway
    provider: openai
type: Opaque
stringData:
  api-key: "${OPENAI_API_KEY}"
---
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: openai-backend
  namespace: kgateway-system
  labels:
    app: agentgateway
    provider: openai
spec:
  ai:
    provider:
      openai:
        model: "gpt-4o-mini"
  policies:
    auth:
      secretRef:
        name: openai-api-key
```

### Environment Variables

```bash
OPENAI_API_KEY=sk-...        # Required
OPENAI_MODEL=gpt-4o-mini     # Default model
```

### Common OpenAI Models

- `gpt-4o` - GPT-4 Omni
- `gpt-4o-mini` - GPT-4 Omni Mini (cost-effective)
- `gpt-4-turbo` - GPT-4 Turbo
- `gpt-3.5-turbo` - GPT-3.5 Turbo

## Anthropic

Requires `ANTHROPIC_API_KEY` environment variable.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: anthropic-api-key
  namespace: kgateway-system
  labels:
    app: agentgateway
    provider: anthropic
type: Opaque
stringData:
  api-key: "${ANTHROPIC_API_KEY}"
---
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: anthropic-backend
  namespace: kgateway-system
  labels:
    app: agentgateway
    provider: anthropic
spec:
  ai:
    provider:
      anthropic:
        model: "claude-sonnet-4-20250514"
  policies:
    auth:
      secretRef:
        name: anthropic-api-key
```

### Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-...           # Required
ANTHROPIC_MODEL=claude-sonnet-4-20250514  # Default model
```

### Common Anthropic Models

- `claude-sonnet-4-20250514` - Claude Sonnet 4
- `claude-opus-4-20250514` - Claude Opus 4
- `claude-3-5-sonnet-20241022` - Claude 3.5 Sonnet
- `claude-3-haiku-20240307` - Claude 3 Haiku (fast)

## Google Gemini

Requires `GEMINI_API_KEY` environment variable.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: gemini-api-key
  namespace: kgateway-system
  labels:
    app: agentgateway
    provider: gemini
type: Opaque
stringData:
  api-key: "${GEMINI_API_KEY}"
---
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: gemini-backend
  namespace: kgateway-system
  labels:
    app: agentgateway
    provider: gemini
spec:
  ai:
    provider:
      gemini:
        model: "gemini-2.0-flash"
  policies:
    auth:
      secretRef:
        name: gemini-api-key
```

### Environment Variables

```bash
GEMINI_API_KEY=...           # Required
GEMINI_MODEL=gemini-2.0-flash  # Default model
```

### Common Gemini Models

- `gemini-2.0-flash` - Gemini 2.0 Flash
- `gemini-2.0-pro` - Gemini 2.0 Pro
- `gemini-1.5-flash` - Gemini 1.5 Flash
- `gemini-1.5-pro` - Gemini 1.5 Pro

## Testing Backends

### Test Ollama

```bash
gateway_address=$(kubectl get svc -n kgateway-system ai-gateway \
  -o jsonpath="{.status.loadBalancer.ingress[0]['hostname','ip']}")

# Test models endpoint
curl "http://${gateway_address}:8080/ollama/v1/models"

# Test chat completions
curl -X POST "http://${gateway_address}:8080/ollama/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2", "messages": [{"role": "user", "content": "Hello"}]}'
```

### Test OpenAI

```bash
curl "http://${gateway_address}:8080/openai/v1/models"
```

### Test Anthropic

```bash
curl -X POST "http://${gateway_address}:8080/anthropic/v1/messages" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 50,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Test Gemini

```bash
curl "http://${gateway_address}:8080/gemini/v1/models"
```

## Vertex AI (GCP)

Routes to Anthropic or Google models hosted on Google Cloud Vertex AI. Requires GCP access tokens which expire every 60 minutes.

**Warning**: The `gcp` auth type appears in agentgateway docs on `main` but may NOT exist in released CRDs. Always inspect the installed CRD to verify. Use `secretRef` with Bearer token as the reliable auth method.

### Create Secret (use kubectl, not YAML stringData)

```bash
# Generate a GCP access token and create the secret
TOKEN=$(gcloud auth application-default print-access-token)
kubectl create secret generic vertexai-bearer-token \
  --from-literal=Authorization="Bearer ${TOKEN}" \
  -n kgateway-system --dry-run=client -o yaml | kubectl apply -f -
```

### Backend Configuration

```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: vertexai-backend
  namespace: kgateway-system
  labels:
    app: agentgateway
    provider: vertexai
spec:
  ai:
    provider:
      vertexai:
        model: "claude-sonnet-4-20250514"
        projectId: "my-gcp-project"
        region: "us-east5"
  policies:
    auth:
      secretRef:
        name: vertexai-bearer-token
```

### Token Refresh CronJob

GCP access tokens expire after 60 minutes. Use a CronJob to refresh every 45 minutes.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: gcp-token-refresher
  namespace: kgateway-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: gcp-token-refresher
  namespace: kgateway-system
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "update", "patch"]
  resourceNames: ["vertexai-bearer-token"]  # Scoped to specific secret only
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: gcp-token-refresher
  namespace: kgateway-system
subjects:
- kind: ServiceAccount
  name: gcp-token-refresher
roleRef:
  kind: Role
  name: gcp-token-refresher
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: gcp-token-refresh
  namespace: kgateway-system
spec:
  schedule: "*/45 * * * *"
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: gcp-token-refresher
          restartPolicy: OnFailure
          containers:
          - name: refresh
            image: google/cloud-sdk:slim
            command: ["sh", "-c"]
            args:
            - |
              TOKEN=$(gcloud auth application-default print-access-token)
              kubectl create secret generic vertexai-bearer-token \
                --from-literal=Authorization="Bearer ${TOKEN}" \
                -n kgateway-system --dry-run=client -o yaml | kubectl apply -f -
              # Annotate with refresh timestamp for monitoring
              kubectl annotate secret vertexai-bearer-token \
                -n kgateway-system \
                last-refreshed="$(date -u +%Y-%m-%dT%H:%M:%SZ)" --overwrite
            volumeMounts:
            - name: gcloud-config
              mountPath: /root/.config/gcloud
              readOnly: true
          volumes:
          - name: gcloud-config
            secret:
              secretName: gcloud-adc-credentials
```

### Manual Token Refresh

```bash
# Debug: manually refresh the token
TOKEN=$(gcloud auth application-default print-access-token)
kubectl create secret generic vertexai-bearer-token \
  --from-literal=Authorization="Bearer ${TOKEN}" \
  -n kgateway-system --dry-run=client -o yaml | kubectl apply -f -

# Check last refresh time
kubectl get secret vertexai-bearer-token -n kgateway-system \
  -o jsonpath='{.metadata.annotations.last-refreshed}'
```

### Model Name Formats

| Context | Format | Example |
|---------|--------|---------|
| Vertex AI rawPredict | Hyphenated | `claude-sonnet-4-20250514` |
| Vertex AI with version | `@` suffix | `claude-sonnet-4@20250514` |
| agentgateway config | Hyphenated | `claude-sonnet-4-20250514` |

### Local vs Cloud Auth

| Environment | Auth Method |
|-------------|-------------|
| Local (OrbStack) | Mounted ADC credentials + CronJob refresh |
| GKE | Workload Identity (automatic, no CronJob needed) |
| Other cloud | Service account key file mounted as Secret |

## Azure OpenAI

Routes to Azure-hosted OpenAI models. Uses Azure API keys.

### Create Secret

```bash
kubectl create secret generic azureopenai-api-key \
  --from-literal=api-key="${AZURE_OPENAI_API_KEY}" \
  -n kgateway-system --dry-run=client -o yaml | kubectl apply -f -
```

### Backend Configuration

```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: azureopenai-backend
  namespace: kgateway-system
  labels:
    app: agentgateway
    provider: azureopenai
spec:
  ai:
    provider:
      azureopenai:
        model: "gpt-4o"
        deploymentName: "my-gpt4o-deployment"
        apiVersion: "2024-10-21"
      host: "my-resource.openai.azure.com"
      port: 443
  policies:
    auth:
      secretRef:
        name: azureopenai-api-key
```

### Common Azure OpenAI Models

- `gpt-4o` - GPT-4 Omni
- `gpt-4o-mini` - GPT-4 Omni Mini
- `gpt-4-turbo` - GPT-4 Turbo

## AWS Bedrock

Routes to AWS Bedrock-hosted models. Uses AWS IAM credentials.

### Create Secret

```bash
kubectl create secret generic bedrock-credentials \
  --from-literal=aws-access-key-id="${AWS_ACCESS_KEY_ID}" \
  --from-literal=aws-secret-access-key="${AWS_SECRET_ACCESS_KEY}" \
  -n kgateway-system --dry-run=client -o yaml | kubectl apply -f -
```

### Backend Configuration

```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: bedrock-backend
  namespace: kgateway-system
  labels:
    app: agentgateway
    provider: bedrock
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

### Common Bedrock Model IDs

- `anthropic.claude-sonnet-4-20250514-v1:0` - Claude Sonnet 4
- `anthropic.claude-3-5-sonnet-20241022-v2:0` - Claude 3.5 Sonnet v2
- `anthropic.claude-3-haiku-20240307-v1:0` - Claude 3 Haiku
- `amazon.titan-text-premier-v1:0` - Amazon Titan Text

### Local vs Cloud Auth

| Environment | Auth Method |
|-------------|-------------|
| Local (OrbStack) | Mounted credentials file or env vars in Secret |
| EKS | IAM Roles for Service Accounts (IRSA) — no static credentials needed |

## Testing Backends

### Test Ollama

```bash
gateway_address=$(kubectl get svc -n kgateway-system ai-gateway \
  -o jsonpath="{.status.loadBalancer.ingress[0]['hostname','ip']}")

# Test models endpoint
curl "http://${gateway_address}:8080/ollama/v1/models"

# Test chat completions
curl -X POST "http://${gateway_address}:8080/ollama/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2", "messages": [{"role": "user", "content": "Hello"}]}'
```

### Test OpenAI

```bash
curl "http://${gateway_address}:8080/openai/v1/models"
```

### Test Anthropic

```bash
curl -X POST "http://${gateway_address}:8080/anthropic/v1/messages" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 50,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Test Gemini

```bash
curl "http://${gateway_address}:8080/gemini/v1/models"
```

## Provider API Structure Differences

| Provider | Type Key | Endpoint | Auth Header | Model Field |
|----------|----------|----------|-------------|-------------|
| Ollama | `openai` | `/v1/chat/completions` | None | `model` |
| OpenAI | `openai` | `/v1/chat/completions` | `Authorization: Bearer` | `model` |
| Anthropic | `anthropic` | `/v1/messages` | `x-api-key` | `model` |
| Gemini | `gemini` | `/v1beta/models/:model:generateContent` | API key param | In URL |
| Vertex AI | `vertexai` | Vertex AI rawPredict | `Authorization: Bearer` (GCP token) | In config |
| Azure OpenAI | `azureopenai` | Azure endpoint | `api-key` header | In config |
| AWS Bedrock | `bedrock` | Bedrock regional endpoint | AWS SigV4 | In config |

The agentgateway proxy normalizes these differences — all backends accept the same path prefix routes.

## Secret Lifecycle

### Creating Secrets Securely

Prefer `kubectl create secret` over YAML `stringData` to avoid keys appearing in conversation output or shell history:

```bash
# Preferred: key never appears in YAML
kubectl create secret generic <provider>-api-key \
  --from-literal=api-key="${API_KEY}" \
  -n kgateway-system --dry-run=client -o yaml | kubectl apply -f -

# Avoid: key visible in YAML output
# stringData:
#   api-key: "${API_KEY}"
```

### Rotation Pattern

To rotate a key without downtime:
1. Create new secret with updated key: `kubectl create secret generic <name> --from-literal=... --dry-run=client -o yaml | kubectl apply -f -`
2. The backend picks up the new secret value automatically
3. Verify the new key works by testing the backend endpoint

### Production Recommendations

For production deployments, use External Secrets Operator with your cloud's secret manager instead of raw Kubernetes Secrets:
- **GCP**: Google Secret Manager
- **AWS**: AWS Secrets Manager
- **Azure**: Azure Key Vault
