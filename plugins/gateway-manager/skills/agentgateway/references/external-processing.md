# External Processing (ExtProc)

External Processing allows agentgateway to delegate request/response handling to an external gRPC service for custom mutations, routing decisions, and content inspection.

## Overview

External Processing (ExtProc) is based on the **Envoy external processor protocol** (`envoy.service.ext_proc.v3`). It enables:

- **Request mutation**: Modify headers, body, or trailers before forwarding upstream
- **Response mutation**: Modify headers, body, or trailers before returning to client
- **Immediate responses**: Short-circuit requests with custom responses
- **Dynamic routing**: Make routing decisions based on request content (e.g., model selection)
- **Content inspection**: Analyze LLM prompts/responses for guardrails

## Agentgateway vs Envoy Differences

The External Processing gRPC service was designed for Envoy and includes Envoy-specific fields. Agentgateway aims for API compatibility but has implementation differences.

### Key Differences

| Aspect | Envoy Behavior | Agentgateway Behavior |
|--------|----------------|----------------------|
| **Headers/Body** | Configurable processing modes | Always sent, body in streaming mode |
| **attributes** | Sent based on configuration | Never sent in requests |
| **metadata_context** | Sent based on configuration | Never sent in requests |
| **protocol_config** | Sent in first request | Never sent in requests |
| **dynamic_metadata** | Propagated to downstream | Ignored in responses |
| **mode_override** | Allows changing processing mode | Ignored in responses |
| **override_message_timeout** | Extends timeout per-message | Ignored in responses |
| **clear_route_cache** | Triggers route recomputation | Ignored (no route cache) |
| **CONTINUE_AND_REPLACE** | Body mutation status | Ignored in responses |

### Implications for ExtProc Services

Your ExtProc service **must**:
- Handle both headers and body messages (they're always sent)
- Process body in streaming mode (chunks arrive as they're received)

Your ExtProc service **cannot rely on**:
- Receiving attributes or metadata_context from the gateway
- Sending dynamic_metadata back to downstream filters
- Changing processing mode mid-request

## How It Works

ExtProc uses bidirectional gRPC streaming:

```
┌─────────┐     1. Request Headers      ┌─────────────┐
│ Client  │ ─────────────────────────▶  │             │
└─────────┘                             │             │
     │        2. Request Body (stream)  │   ExtProc   │
     │      ─────────────────────────▶  │   Service   │
     │                                  │             │
     │        3. Mutations/Decisions    │             │
     │      ◀─────────────────────────  │             │
     ▼                                  └─────────────┘
┌─────────┐
│Upstream │
└─────────┘
```

1. Gateway sends request headers to ExtProc service
2. Gateway streams request body chunks (always, in streaming mode)
3. ExtProc returns mutations (add/remove headers, modify body)
4. Gateway applies mutations and forwards to upstream
5. Process repeats for response path

## Configuration

External processing can be applied at two levels:
- **Route level**: Applied to specific routes
- **Gateway level**: Applied to all routes on the gateway

**Precedence**: If ExtProc is configured at both levels, the **route-level policy takes precedence**.

### Route-Level ExtProc Policy

Apply ExtProc to specific routes:

```yaml
# agentgateway.yaml
binds:
- name: ai-gateway
  listeners:
  - port: 8080
    routes:
    - name: llm-route
      backends:
      - host: llm-backend.example.com
        port: 443
      policies:
        extProc:
          backend: /extproc-service
          failureMode: failClosed
```

### Gateway-Level ExtProc Policy

Apply ExtProc to all routes on the gateway:

```yaml
# agentgateway.yaml
binds:
- name: ai-gateway
  policies:
    extProc:
      backend: /extproc-service
      failureMode: failClosed
  listeners:
  - port: 8080
    routes:
    - name: llm-route
      backends:
      - host: llm-backend.example.com
        port: 443
```

### Combined Route and Gateway Policies

When both are configured, route-level takes precedence:

```yaml
binds:
- name: ai-gateway
  policies:
    extProc:
      backend: /default-extproc        # Applied to routes without their own policy
      failureMode: failClosed
  listeners:
  - port: 8080
    routes:
    - name: inference-route
      policies:
        extProc:
          backend: /inference-extproc  # This takes precedence for this route
          failureMode: failOpen
      backends:
      - host: inference.example.com
        port: 443
    - name: chat-route
      # No route-level extProc, uses gateway-level /default-extproc
      backends:
      - host: chat.example.com
        port: 443
```

### Backend Reference Options

ExtProc targets can be specified in multiple ways:

```yaml
# Option 1: Backend reference (recommended)
extProc:
  backend: /my-extproc-service   # References a defined backend

# Option 2: Direct host
extProc:
  host: extproc.example.com
  port: 50051

# Option 3: Kubernetes service
extProc:
  service:
    name:
      namespace: default
      hostname: extproc-svc
    port: 50051
```

### Complete Example

```yaml
backends:
- name: extproc-service
  static:
    host: extproc.default.svc.cluster.local
    port: 50051

binds:
- name: ai-gateway
  listeners:
  - port: 8080
    routes:
    - name: inference-route
      backends:
      - host: llm-provider.example.com
        port: 443
      policies:
        extProc:
          backend: /extproc-service
          failureMode: failOpen
```

## Failure Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `failClosed` | Block requests if ExtProc fails (default) | Security-critical processing |
| `failOpen` | Allow requests through if ExtProc fails | Non-critical enhancements |

### FailOpen Behavior

When `failOpen` is set and the ExtProc service fails:
- Request path: Original body is buffered and forwarded unchanged
- Response path: Original response is returned unchanged
- Request continues without ExtProc mutations

### FailClosed Behavior

When `failClosed` is set and ExtProc service fails:
- Returns HTTP 500 error to client
- Error message: `ext_proc failed: <reason>`

## Inference Routing

A specialized ExtProc pattern for LLM model/endpoint selection based on request content.

### How It Works

1. ExtProc service analyzes request body (e.g., model field, prompt content)
2. Returns routing decision via `x-gateway-destination-endpoint` header
3. Gateway routes to the specified endpoint

### Response Headers

| Header | Purpose |
|--------|---------|
| `x-gateway-destination-endpoint` | Target endpoint address (IP:port) |
| `x-gateway-model-name` | Selected model name |

### Example ExtProc Response

```protobuf
HeaderMutation {
  set_headers: [
    { key: "x-gateway-destination-endpoint", value: "10.0.0.5:8080" },
    { key: "x-gateway-model-name", value: "llama3.2" }
  ]
}
```

## Implementing an ExtProc Service

### Protocol Definition

The service must implement the `ExternalProcessor` gRPC service:

```protobuf
service ExternalProcessor {
  rpc Process(stream ProcessingRequest) returns (stream ProcessingResponse) {}
}
```

### Message Types

**ProcessingRequest** (from gateway):
- `request_headers` / `response_headers` - HTTP headers (always sent)
- `request_body` / `response_body` - Body chunks (always sent, streaming)
- `request_trailers` / `response_trailers` - HTTP trailers

**Note**: `attributes`, `metadata_context`, and `protocol_config` are NOT sent by agentgateway.

**ProcessingResponse** (from service):
- `HeadersResponse` - Header mutations
- `BodyResponse` - Body mutations
- `TrailersResponse` - Trailer mutations
- `ImmediateResponse` - Short-circuit with custom response

**Note**: `dynamic_metadata`, `mode_override`, and `override_message_timeout` are ignored by agentgateway.

### Header Mutation Example

```go
// Go example using envoy ext_proc types
response := &extproc.ProcessingResponse{
    Response: &extproc.ProcessingResponse_RequestHeaders{
        RequestHeaders: &extproc.HeadersResponse{
            Response: &extproc.CommonResponse{
                HeaderMutation: &extproc.HeaderMutation{
                    SetHeaders: []*core.HeaderValueOption{
                        {
                            Header: &core.HeaderValue{
                                Key:   "x-custom-header",
                                Value: "custom-value",
                            },
                        },
                    },
                    RemoveHeaders: []string{"x-remove-me"},
                },
            },
        },
    },
}
```

### Body Streaming Handler

Since agentgateway always streams body, your service must handle multiple body chunks:

```go
func (s *Server) Process(stream extproc.ExternalProcessor_ProcessServer) error {
    var requestBody bytes.Buffer

    for {
        req, err := stream.Recv()
        if err == io.EOF {
            return nil
        }
        if err != nil {
            return err
        }

        switch r := req.Request.(type) {
        case *extproc.ProcessingRequest_RequestHeaders:
            // Headers always arrive first
            stream.Send(requestHeaderResponse())

        case *extproc.ProcessingRequest_RequestBody:
            // Accumulate body chunks
            requestBody.Write(r.RequestBody.Body)

            if r.RequestBody.EndOfStream {
                // Full body received, make routing decision
                stream.Send(requestBodyResponse(&requestBody))
            }

        case *extproc.ProcessingRequest_ResponseHeaders:
            stream.Send(responseHeaderResponse())

        case *extproc.ProcessingRequest_ResponseBody:
            stream.Send(responseBodyResponse())
        }
    }
}
```

### Immediate Response Example

Short-circuit a request without forwarding to upstream:

```go
response := &extproc.ProcessingResponse{
    Response: &extproc.ProcessingResponse_ImmediateResponse{
        ImmediateResponse: &extproc.ImmediateResponse{
            Status: &envoy_type.HttpStatus{Code: 403},
            Body:   "Access denied",
            Headers: &extproc.HeaderMutation{
                SetHeaders: []*core.HeaderValueOption{
                    {Header: &core.HeaderValue{Key: "content-type", Value: "text/plain"}},
                },
            },
        },
    },
}
```

## Testing ExtProc

### Verify ExtProc Service

```bash
# Check if ExtProc service is responding
grpcurl -plaintext extproc.default.svc.cluster.local:50051 list

# Should show:
# envoy.service.ext_proc.v3.ExternalProcessor
```

### Test Request Flow

```bash
# Send request through gateway
curl -v http://gateway:8080/inference \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2", "prompt": "Hello"}'

# Check for ExtProc-added headers in response
```

### Debug Logging

Enable debug logging to see ExtProc interactions:

```yaml
# In AgentgatewayParameters or config
logging:
  level: debug
```

Look for log entries:
- `connecting to <extproc-address>` - ExtProc connection
- `ext_proc failed` - ExtProc errors

## Troubleshooting

### ExtProc Service Unavailable

**Symptom**: HTTP 500 with `ext_proc failed: connection refused`

**Solutions**:
1. Check ExtProc service is running: `kubectl get pods -l app=extproc`
2. Verify port and address match configuration
3. Check network policies allow gRPC traffic
4. Consider using `failOpen` for non-critical processing

### Timeout Issues

**Symptom**: Slow responses or timeouts

**Solutions**:
```yaml
policies:
  timeout:
    backendRequestTimeout: 30s   # Increase timeout for ExtProc
```

### Body Handling Issues

**Symptom**: ExtProc receiving unexpected body chunks

Agentgateway always sends body in streaming mode. Your service must:
- Handle multiple `RequestBody` messages
- Check `end_of_stream` to know when body is complete
- Buffer body chunks if you need the full body for decisions

### Service Designed for Envoy Not Working

**Symptom**: ExtProc service works with Envoy but not agentgateway

Check if your service relies on:
- `attributes` or `metadata_context` in requests (not sent)
- `dynamic_metadata` propagation (ignored)
- Non-streaming body modes (not supported)

## Use Cases

| Use Case | Description |
|----------|-------------|
| **Prompt Guard** | Inspect prompts for PII, injection attacks |
| **Model Routing** | Select models based on request content |
| **Token Counting** | Track token usage before/after inference |
| **Response Filtering** | Remove sensitive content from responses |
| **A/B Testing** | Route percentage of traffic to different models |
| **Custom Auth** | Complex authorization logic beyond JWT/API keys |

## Reference Implementation

The Gateway API Inference Extension project provides a reference body-based router (BBR) implementation:

- [gateway-api-inference-extension](https://github.com/kubernetes-sigs/gateway-api-inference-extension)
- Demonstrates model routing based on request body analysis
- Uses `x-gateway-model-name` and `x-gateway-destination-endpoint` headers
