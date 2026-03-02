---
date: 2026-02-25
topic: litellm-gateway-skill
---

# LiteLLM Skill for Gateway-Proxy Plugin

## What We're Building

A new `skills/litellm/` skill within the existing `gateway-proxy` plugin that gives the gateway-manager agent knowledge of LiteLLM proxy — lifecycle management (install, upgrade, remove), model/provider configuration, and deployment patterns (Docker, Kubernetes, pip). The agent will route to the appropriate skill (kgateway or LiteLLM) based on explicit user context.

This is the first step toward a **multi-gateway plugin** architecture where each gateway type (kgateway/agentgateway, LiteLLM, and eventually Kong) has its own skill, and the agent acts as a router.

## Why This Approach

- **Same plugin, new skill** — keeps the "gateway" theme unified under one plugin while maintaining separation of concerns
- **Full-featured from the start** — matches the depth and pattern of the existing kgateway skill (SKILL.md + references/ + commands)
- **Agent routing by user context** — user explicitly states which gateway they're working with; no fragile auto-detection
- **Documentation-driven** — no scripts needed; pure reference docs that the agent loads on-demand

## Key Decisions

- **Plugin structure**: New `skills/litellm/` directory alongside `skills/gateway-proxy/` (not a separate plugin, not merged into existing skill)
- **Agent routing**: User specifies gateway explicitly (e.g., "I'm using LiteLLM" or trigger phrases). Agent loads appropriate skill references.
- **Deployment coverage**: All three methods — Docker/Compose, Kubernetes (Helm), pip install
- **Command prefix**: `ll-*` commands (e.g., `ll-status`, `ll-models`, `ll-config`, `ll-upgrade`, `ll-debug`)
- **No auto-detection**: Agent doesn't probe environment to guess gateway type

## Proposed Structure

```
plugins/gateway-proxy/
├── agents/
│   └── gateway-manager.md          # UPDATE: add LiteLLM routing logic
├── skills/
│   ├── gateway-proxy/              # Existing kgateway/agentgateway skill
│   │   ├── SKILL.md
│   │   ├── IMPROVEMENT_PLAN.md
│   │   └── references/
│   └── litellm/                    # NEW
│       ├── SKILL.md                # Core knowledge, triggers, progressive disclosure
│       ├── IMPROVEMENT_PLAN.md
│       └── references/
│           ├── deployment-patterns.md    # Docker, K8s Helm, pip install lifecycle
│           ├── model-configuration.md    # config.yaml patterns, model aliases, fallbacks
│           ├── provider-setup.md         # Per-provider auth (OpenAI, Anthropic, Azure, etc.)
│           └── lessons-learned.md        # Gotchas, troubleshooting
└── commands/
    ├── gw-*                        # Existing kgateway commands
    ├── ll-status.md                # NEW: Check LiteLLM health & running models
    ├── ll-models.md                # NEW: List/add/remove model configs
    ├── ll-config.md                # NEW: Generate/validate config.yaml
    ├── ll-upgrade.md               # NEW: Upgrade LiteLLM (Docker/pip/Helm)
    └── ll-debug.md                 # NEW: Logs, health check, connectivity test
```

## Agent Changes

The gateway-manager agent needs updates to:
1. Recognize LiteLLM trigger phrases ("set up LiteLLM", "add a model to LiteLLM", "LiteLLM config")
2. Load `skills/litellm/SKILL.md` and appropriate references based on workflow
3. Use the same bounded-autonomy pattern (read = safe, mutate = confirm)
4. Understand when to recommend LiteLLM vs kgateway (comparison knowledge)

## LiteLLM Skill Content Areas

### Lifecycle Management
- **Install**: Docker pull, docker-compose setup, pip install, Helm chart
- **Upgrade**: Version checking, image/package updates, migration notes
- **Remove**: Container cleanup, Helm uninstall, pip uninstall

### Configuration Patterns
- **config.yaml**: Model definitions, provider routing, fallbacks, load balancing
- **Model aliases**: Mapping custom names to provider models
- **Virtual keys**: API key management, team budgets, rate limits
- **Callbacks**: Logging, webhooks, custom callbacks

### Provider Setup
- OpenAI, Anthropic, Azure OpenAI, AWS Bedrock, Vertex AI, Ollama, HuggingFace
- Auth patterns per provider (API keys, service accounts, IAM roles)

### Comparison with kgateway
- LiteLLM: Application-layer proxy, config-driven, built-in cost tracking
- kgateway/agentgateway: Kubernetes-native, Gateway API, infrastructure-layer
- When to use each (or both together)

## Open Questions

- Should the plugin name/description change to reflect multi-gateway scope? (e.g., "AI Gateway Manager" instead of "gateway-proxy")
- What LiteLLM version should be targeted? (latest stable)
- Should the skill include database setup for LiteLLM's spend tracking? (PostgreSQL/Redis)
- How deep should the virtual keys / team management content go?

## Implementation Tools

- **plugin-dev:skill-development** — for SKILL.md structure and progressive disclosure
- **plugin-dev:agent-development** — for gateway-manager agent updates
- **plugin-dev:command-development** — for `ll-*` slash commands
- **skillsmith** — for evaluating skill quality before committing

## Next Steps

→ `/workflows:plan` for implementation details
→ Research LiteLLM docs for accurate config.yaml schema and CLI commands
→ Update gateway-manager agent routing logic
