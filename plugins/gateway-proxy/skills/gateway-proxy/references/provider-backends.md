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

## Provider API Structure Differences

| Provider | Endpoint | Auth Header | Model Field |
|----------|----------|-------------|-------------|
| Ollama | `/v1/chat/completions` | None | `model` |
| OpenAI | `/v1/chat/completions` | `Authorization: Bearer` | `model` |
| Anthropic | `/v1/messages` | `x-api-key` | `model` |
| Gemini | `/v1beta/models/:model:generateContent` | API key param | In URL |

The agentgateway proxy normalizes these differences - all backends accept the same path prefix routes.
