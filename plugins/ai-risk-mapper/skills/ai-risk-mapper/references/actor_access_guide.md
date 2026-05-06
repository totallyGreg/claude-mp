---
last_verified: 2026-05-06
sources:
  - type: github
    repo: "cosai-oasis/secure-ai-tooling"
    paths: ["risk-map/yaml/actor-access.yaml"]
    description: "CoSAI threat actor access level taxonomy — traditional and AI-specific access patterns"
---

# Threat Actor Access Levels

The CoSAI Risk Map classifies threat actor access into 9 levels across two categories. Each risk in the framework specifies which access levels can exploit it, enabling threat modeling scoped to realistic attacker capabilities.

## Traditional Access Levels

| ID | Title | Description |
|----|-------|-------------|
| `external` | External Access | Remote attackers with no direct system access (e.g., attacks via public interfaces) |
| `api` | API Access | Attackers with access to public or authenticated API endpoints |
| `user` | User Access | Standard authenticated users with normal application privileges |
| `privileged` | Privileged Access | Administrators, operators, or power users with elevated permissions |
| `physical` | Physical Access | Attackers with physical access to hardware, facilities, or devices |

## AI-Specific Access Levels

| ID | Title | Description |
|----|-------|-------------|
| `agent` | Agent Access | AI agents or autonomous systems with tool/plugin execution capabilities |
| `supply-chain` | Supply Chain Position | Actors in the software, data, or model supply chain (data providers, model vendors) |
| `infrastructure-provider` | Infrastructure Provider | Cloud or infrastructure providers with access to underlying systems (hypervisor, storage) |
| `service-provider` | Service Provider | Third-party service providers with access to systems or data (ML platforms, annotation services) |

## Usage in Risk Assessment

Every risk in `risks.yaml` has an `actorAccess` field listing which access levels can exploit it. This enables:

- **Threat modeling by attacker profile** — "What can an external attacker do to our system?"
- **Agentic risk scoping** — "What risks arise specifically from AI agent access?"
- **Supply chain risk filtering** — "What risks come from our model/data providers?"

### Query Examples

```bash
# List all access levels with risk counts
uv run scripts/cli_actor_access.py --list

# Show risks exploitable by AI agents
uv run scripts/cli_actor_access.py agent

# Show supply chain risks
uv run scripts/cli_actor_access.py supply-chain --offline
```

### Programmatic Access

```python
from core_analyzer import RiskAnalyzer

analyzer = RiskAnalyzer(offline=True)

# Get risks exploitable at agent access level
agent_risks = analyzer.get_risks_by_actor_access("agent")
for risk in agent_risks:
    print(f"{risk.id}: {risk.title}")
    print(f"  Also exploitable via: {', '.join(risk.actor_access)}")
```

## Operationalization

Actor access levels support the 4-phase operationalization model described by the CoSAI project:

1. **Phase 1 — Discovery**: Identify which access levels exist in your architecture (do you have agents? supply chain dependencies? API endpoints?)
2. **Phase 2 — Risk Assessment**: Filter risks by the access levels present in your system
3. **Phase 3 — Control Selection**: Prioritize controls that mitigate risks at your most exposed access levels
4. **Phase 4 — Compliance**: Map actor access patterns to framework requirements (NIST AI RMF, MITRE ATLAS)

Organizations building agentic AI systems should pay particular attention to the `agent`, `api`, and `supply-chain` access levels, as these represent the highest-growth threat surface in modern AI deployments.
