---
title: "feat: Add LiteLLM skill to gateway-proxy plugin"
type: feat
status: active
date: 2026-02-25
origin: docs/brainstorms/2026-02-25-litellm-gateway-skill-brainstorm.md
labels: plugin:gateway-proxy
---

# feat: Add LiteLLM Skill to Gateway-Proxy Plugin

## Overview

Add a new `skills/litellm/` skill to the gateway-proxy plugin, evolving it into a multi-gateway plugin. The gateway-manager agent will route to the appropriate skill (kgateway or LiteLLM) based on explicit user context. The LiteLLM skill covers lifecycle management (install, upgrade, remove) and configuration (models, providers, routing) across all deployment methods (Docker, Kubernetes, pip).

This is the first step toward a multi-gateway architecture where each gateway type has its own skill and the agent acts as a router (see brainstorm: `docs/brainstorms/2026-02-25-litellm-gateway-skill-brainstorm.md`).

## Problem Statement / Motivation

The gateway-proxy plugin currently only supports kgateway/agentgateway — a Kubernetes-native Gateway API solution. LiteLLM is a widely-used alternative that:

- Runs anywhere (Docker, K8s, bare metal) — no Kubernetes required
- Provides a unified OpenAI-compatible API across 100+ LLM providers
- Includes built-in cost tracking, budget limits, and key management
- Offers config-driven model routing with fallbacks and load balancing

Users working with LiteLLM need the same agent-guided experience for setup, configuration, and troubleshooting that kgateway users already have.

## Proposed Solution

### Plugin Structure Changes

```
plugins/gateway-proxy/
├── .claude-plugin/
│   └── plugin.json                  # UPDATE: bump version, update description
├── agents/
│   └── gateway-manager.md           # UPDATE: add LiteLLM routing logic
├── commands/
│   ├── gw-*.md                      # EXISTING: kgateway commands (unchanged)
│   ├── ll-status.md                 # NEW: health check & model status
│   ├── ll-models.md                 # NEW: list/add/remove model configs
│   ├── ll-config.md                 # NEW: generate/validate config.yaml
│   ├── ll-upgrade.md                # NEW: version check & upgrade guide
│   ├── ll-debug.md                  # NEW: full diagnostic (logs + config + health)
│   └── ll-logs.md                   # NEW: tail LiteLLM logs
└── skills/
    ├── gateway-proxy/               # EXISTING (unchanged)
    │   ├── SKILL.md
    │   ├── IMPROVEMENT_PLAN.md
    │   └── references/
    └── litellm/                     # NEW
        ├── SKILL.md
        ├── IMPROVEMENT_PLAN.md
        └── references/
            ├── deployment-patterns.md    # Docker, K8s (Helm), pip lifecycle
            ├── model-configuration.md    # config.yaml patterns, aliases, fallbacks
            ├── provider-setup.md         # Per-provider auth & config
            └── lessons-learned.md        # Gotchas, troubleshooting
```

### Agent Routing Design

The gateway-manager agent routes to the correct skill based on **explicit keyword matching**:

| User Says | Skill Loaded | Rationale |
|-----------|-------------|-----------|
| "LiteLLM", "litellm", "lite llm" | `skills/litellm/` | Explicit product name |
| "kgateway", "agentgateway", "gateway-proxy" | `skills/gateway-proxy/` | Explicit product name |
| "add an OpenAI backend" (ambiguous) | Ask user | Could be either gateway |
| "which gateway should I use?" | Both skills | Comparison scenario |

**Decision tree in agent prompt:**
1. Check for explicit gateway name in user request
2. If found → load that skill's references
3. If ambiguous → ask "Are you using kgateway/agentgateway or LiteLLM?"
4. If comparison → load both skills, present recommendation matrix

### Deployment Detection (Per-Session)

When the LiteLLM skill is loaded, the agent detects the deployment method:

```
1. Check kubectl: kubectl get deploy -A -l app.kubernetes.io/name=litellm
2. Check Docker: docker ps --filter "ancestor=ghcr.io/berriai/litellm" --format "{{.Names}}"
3. Check pip: pip show litellm 2>/dev/null
4. If multiple found → ask user which deployment to manage
5. If none found → assume new installation, ask preferred method
```

## Technical Considerations

### LiteLLM SKILL.md Content Areas

**Core knowledge (in SKILL.md):**
- What LiteLLM is and when to use it vs kgateway
- Quick commands table (linking to `ll-*` commands)
- Config.yaml structure overview
- Reference file index (progressive disclosure)

**Reference: deployment-patterns.md**
- Docker: `docker-compose.yaml` template, volume mounts, env vars
- Kubernetes: Helm chart values, ConfigMap for config.yaml, Service/Deployment manifests
- pip: `pip install 'litellm[proxy]'`, systemd service template, startup command
- Upgrade procedures per method (with rollback)
- Removal/cleanup procedures per method

**Reference: model-configuration.md**
- `config.yaml` schema: `model_list`, `litellm_settings`, `router_settings`
- Model aliases and custom naming
- Fallback chains and retry configuration
- Wildcard routing (proxy all models from a provider)
- Load balancing strategies (simple-shuffle, least-busy, latency-based)
- Redis dependency for advanced routing

**Reference: provider-setup.md**
- OpenAI, Anthropic, Azure OpenAI, AWS Bedrock, Vertex AI, Ollama, HuggingFace
- Auth patterns per provider (API keys, service accounts, IAM roles)
- Environment variable vs config.yaml credential placement
- Secret management best practices per deployment method

**Reference: lessons-learned.md**
- Common config.yaml mistakes
- Version-specific breaking changes
- Performance tuning (workers, concurrency)
- Database backend considerations (PostgreSQL for key management)
- Redis setup for routing features

### Agent Updates (gateway-manager.md)

Key changes to the agent:
1. **Description**: Add LiteLLM trigger phrases alongside existing kgateway triggers
2. **Initial assessment**: Add LiteLLM detection commands to silent startup check
3. **Reference loading**: New section for LiteLLM workflow-based reference loading
4. **Disambiguation**: New section for handling ambiguous requests
5. **Comparison workflow**: Knowledge of when to recommend LiteLLM vs kgateway

### Marketplace Integration

Update `marketplace.json` to declare the new skill:
```json
{
  "skills": [
    "./skills/gateway-proxy",
    "./skills/litellm"
  ]
}
```

**Version sync**: Follow the multi-skill version sync pattern — plugin version = highest skill version. Run sync script after version changes (see learnings: `docs/solutions/logic-errors/multi-skill-plugin-version-sync.md`).

## Acceptance Criteria

### Skill Structure
- [ ] `skills/litellm/SKILL.md` exists with proper frontmatter, trigger phrases, and progressive disclosure
- [ ] `skills/litellm/IMPROVEMENT_PLAN.md` exists with version history table
- [ ] All 4 reference files created with accurate LiteLLM documentation
- [ ] Skillsmith evaluation score recorded in IMPROVEMENT_PLAN.md

### Agent Routing
- [ ] Gateway-manager agent recognizes "LiteLLM" and loads litellm skill references
- [ ] Ambiguous requests trigger a clarifying question (not a guess)
- [ ] Comparison requests load both skills and present recommendation

### Commands (6 new `ll-*` commands)
- [ ] `/ll-status` — checks LiteLLM health endpoint, lists active models, shows version
- [ ] `/ll-models` — lists configured models from config.yaml, supports add/remove
- [ ] `/ll-config` — generates/validates config.yaml, presents for approval before applying
- [ ] `/ll-upgrade` — checks current vs latest version, generates upgrade commands per deployment method
- [ ] `/ll-debug` — full diagnostic: status + logs + config validation + provider connectivity
- [ ] `/ll-logs [count]` — tails LiteLLM logs (auto-detects Docker/K8s/systemd)

### Lifecycle Coverage
- [ ] Install workflow for Docker, K8s, and pip — each produces a working LiteLLM deployment
- [ ] Upgrade workflow with version comparison, changelog reference, and rollback instructions
- [ ] Remove workflow with dependency-aware cleanup per deployment method

### Configuration Coverage
- [ ] Add/modify/remove model configurations via config.yaml
- [ ] Provider auth setup for at least: OpenAI, Anthropic, Azure OpenAI, Ollama
- [ ] Routing strategy configuration (with Redis dependency awareness)

### Integration
- [ ] Marketplace.json updated with `./skills/litellm`
- [ ] Plugin version synced correctly
- [ ] Existing kgateway skill and commands unaffected (no regressions)

## Success Metrics

- Skillsmith evaluation score >= 80 overall
- All `ll-*` commands produce correct output for each deployment method
- Agent correctly routes to litellm skill on LiteLLM-related queries
- No regressions in existing `gw-*` commands or gateway-proxy skill

## Dependencies & Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| LiteLLM config.yaml schema accuracy | Skill gives wrong config advice | Research LiteLLM docs during implementation; test against actual LiteLLM instance |
| Agent routing ambiguity | Wrong skill loaded for user | Explicit keyword matching + clarifying question for ambiguous requests |
| Multi-skill version sync | Stale marketplace.json | Follow three-layer defense (sync script + pre-commit hook + process) |
| LiteLLM rapid release cadence | Skill content becomes stale | Focus on stable config patterns; version-specific content in lessons-learned.md |
| Scope creep (database, Redis, virtual keys) | Delayed delivery | MVP focuses on core lifecycle + config; advanced features in follow-up issue |

## Implementation Phases

### Phase 1: Skill Foundation
1. Create `skills/litellm/SKILL.md` with frontmatter and core knowledge
2. Create `skills/litellm/IMPROVEMENT_PLAN.md`
3. Create `references/deployment-patterns.md` (Docker, K8s, pip lifecycle)
4. Create `references/model-configuration.md` (config.yaml patterns)
5. Create `references/provider-setup.md` (provider auth)
6. Create `references/lessons-learned.md` (gotchas)

### Phase 2: Commands
7. Create `commands/ll-status.md`
8. Create `commands/ll-models.md`
9. Create `commands/ll-config.md`
10. Create `commands/ll-upgrade.md`
11. Create `commands/ll-debug.md`
12. Create `commands/ll-logs.md`

### Phase 3: Agent & Integration
13. Update `agents/gateway-manager.md` with LiteLLM routing, triggers, and reference loading
14. Update marketplace.json with `./skills/litellm`
15. Update plugin.json version and description (multi-gateway scope)

### Phase 4: Validation
16. Run skillsmith evaluation: `uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py plugins/gateway-proxy/skills/litellm`
17. Record eval score in IMPROVEMENT_PLAN.md
18. Run marketplace version sync
19. Verify existing kgateway skill/commands unaffected

## Sources & References

### Origin

- **Brainstorm document:** [docs/brainstorms/2026-02-25-litellm-gateway-skill-brainstorm.md](docs/brainstorms/2026-02-25-litellm-gateway-skill-brainstorm.md) — Key decisions: same-plugin multi-skill architecture, explicit user-driven routing, full deployment coverage, `ll-*` command prefix

### Internal References

- Multi-skill plugin pattern: `plugins/pkm-plugin/`, `plugins/terminal-guru/`
- Gateway-proxy skill: `plugins/gateway-proxy/skills/gateway-proxy/SKILL.md`
- Gateway-manager agent: `plugins/gateway-proxy/agents/gateway-manager.md`
- Version sync learning: `docs/solutions/logic-errors/multi-skill-plugin-version-sync.md`
- Plugin architecture: `docs/lessons/plugin-integration-and-architecture.md`
- Skill migration stages: `docs/lessons/skill-to-plugin-migration.md`

### External References

- LiteLLM Documentation: https://docs.litellm.ai/
- LiteLLM Proxy Config: https://docs.litellm.ai/docs/proxy/configs
- LiteLLM Docker Deployment: https://docs.litellm.ai/docs/proxy/docker_quick_start
- LiteLLM GitHub: https://github.com/BerriAI/litellm
