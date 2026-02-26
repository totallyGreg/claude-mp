---
title: Rename gateway-proxy to gateway-manager and split into kgateway + agentgateway skills
type: refactor
status: active
date: 2026-02-25
origin: docs/brainstorms/2026-02-25-litellm-gateway-skill-brainstorm.md
---

# Rename gateway-proxy to gateway-manager and split into kgateway + agentgateway skills

## Overview

Rename the `gateway-proxy` plugin to `gateway-manager` and split the single `gateway-proxy` skill into two separate skills (`kgateway` and `agentgateway`) to align with the upstream project divergence at v2.3.0. This sets the stage for the multi-gateway plugin architecture where each gateway type has its own skill and the `gateway-manager` agent routes between them.

## Problem Statement / Motivation

1. **Upstream divergence**: Starting with v2.3.0, kgateway and agentgateway are splitting into separate projects with separate repos, registries, and namespaces (`kgateway-system` vs `agentgateway-system`). The single skill conflates two diverging concerns.

2. **Multi-gateway plugin evolution**: Issue #60 proposes adding a LiteLLM skill. The plugin name `gateway-proxy` doesn't reflect a multi-skill architecture. `gateway-manager` better describes the plugin's role as a router across gateway types.

3. **Knowledge separation**: The current skill mixes Kubernetes Gateway API concepts (kgateway) with AI/LLM routing concepts (agentgateway). Separating them improves accuracy when the agent loads skill context.

(see brainstorm: `docs/brainstorms/2026-02-25-litellm-gateway-skill-brainstorm.md` — open question about renaming plugin)

## Proposed Solution

### New Directory Structure

```
plugins/gateway-manager/                    # RENAMED from gateway-proxy
├── .claude-plugin/
│   └── plugin.json                         # name: "gateway-manager", version: 3.0.0
├── agents/
│   └── gateway-manager.md                  # UPDATE: route to kgateway OR agentgateway skill
├── commands/                               # UNCHANGED location (cross-cutting commands)
│   ├── gw-backend.md                       # UPDATE: reference agentgateway skill
│   ├── gw-debug.md                         # UPDATE: reference both skills contextually
│   ├── gw-eval.md                          # UPDATE: reference both skills
│   ├── gw-logs.md                          # UPDATE: reference both skills
│   ├── gw-route.md                         # UPDATE: reference kgateway skill
│   ├── gw-status.md                        # UPDATE: reference both skills
│   ├── gw-upgrade.md                       # UPDATE: reference both skills
│   └── gw-versions.md                      # UPDATE: reference both skills
└── skills/
    ├── kgateway/                           # NEW skill
    │   ├── SKILL.md
    │   ├── IMPROVEMENT_PLAN.md
    │   └── references/
    │       ├── gateway-api-patterns.md     # NEW: Gateway, HTTPRoute, GatewayClass patterns
    │       ├── helm-lifecycle.md           # SPLIT: kgateway-specific install/upgrade
    │       └── lessons-learned.md          # SPLIT: kgateway-relevant gotchas
    └── agentgateway/                       # NEW skill
        ├── SKILL.md
        ├── IMPROVEMENT_PLAN.md
        └── references/
            ├── provider-backends.md        # MOVED from gateway-proxy
            ├── resource-patterns.md        # MOVED: agentgateway CRDs only
            ├── mcp-routing.md              # MOVED from gateway-proxy
            ├── external-processing.md      # MOVED from gateway-proxy
            ├── helm-lifecycle.md           # SPLIT: agentgateway-specific install/upgrade
            └── lessons-learned.md          # SPLIT: agentgateway-relevant gotchas
```

### Content Split Strategy (Natural Upstream Split)

| Current Reference | Destination | Rationale |
|---|---|---|
| `provider-backends.md` | `agentgateway/references/` | All 7 LLM providers use `AgentgatewayBackend` CRD |
| `resource-patterns.md` | `agentgateway/references/` | AgentgatewayBackend, AgentgatewayPolicy, AgentgatewayParameters |
| `mcp-routing.md` | `agentgateway/references/` | MCP is an agentgateway feature |
| `external-processing.md` | `agentgateway/references/` | ExtProc runs through agentgateway proxy |
| `helm-lifecycle.md` | Split into both | Each skill gets its own component's Helm chart lifecycle |
| `lessons-learned.md` | Split by relevance | OrbStack networking → both; CRD confusion → agentgateway; Helm ordering → both |

**New reference**: `kgateway/references/gateway-api-patterns.md` — Gateway, HTTPRoute, GatewayClass, Backend CRD (`gateway.kgateway.dev/v1alpha1`). Content extracted from current SKILL.md sections on HTTPRoute and Gateway API.

### Command Routing

Commands stay at plugin level. Each command's "Reference the gateway-proxy skill" line updates to reference the appropriate skill(s):

| Command | Primary Skill | Notes |
|---|---|---|
| `/gw-backend` | agentgateway | Generates `AgentgatewayBackend` YAML |
| `/gw-route` | kgateway | Generates HTTPRoute (Gateway API resource) |
| `/gw-status` | Both | Shows all gateway resources across namespaces |
| `/gw-logs` | Both | Tails kgateway or agentgateway controller logs |
| `/gw-debug` | Both | Full diagnostic across both components |
| `/gw-versions` | Both | Compares installed vs latest for both Helm charts |
| `/gw-upgrade` | Both | Guides Helm upgrades (CRDs → kgateway → agentgateway order) |
| `/gw-eval` | Both | Evaluates config against both skill references |

### Agent Updates

The `gateway-manager.md` agent updates:

1. **Skill routing**: Load `kgateway/SKILL.md` or `agentgateway/SKILL.md` (or both) based on user's request context
2. **Reference paths**: All 7 `${CLAUDE_PLUGIN_ROOT}/skills/gateway-proxy/` paths updated to point to correct skill
3. **Trigger phrase disambiguation**: Agent identifies which project the user is working with and loads appropriate skill
4. **Cross-skill workflows**: For tasks like "set up AI gateway" that need both (Gateway + AgentgatewayBackend), agent loads both skills

### Version Strategy

- **Plugin version**: Bump to `3.0.0` (major — breaking path change + skill restructuring)
- **kgateway skill**: Starts at `1.0.0` (new skill, inherits gateway-proxy lineage)
- **agentgateway skill**: Starts at `1.0.0` (new skill, inherits gateway-proxy lineage)
- **IMPROVEMENT_PLAN.md**: Each skill starts fresh at 1.0.0 with a note referencing `gateway-proxy v2.0.0` as predecessor

## Technical Considerations

### Filesystem Rename Impact (18 files affected)

**Functional files (must update — breaks functionality if missed):**
1. `plugin.json` — `"name"` field
2. `SKILL.md` (×2) — frontmatter `name:` and trigger description
3. `gateway-manager.md` (agent) — 7 `${CLAUDE_PLUGIN_ROOT}/skills/gateway-proxy/` paths
4. `gw-backend.md`, `gw-eval.md`, `gw-route.md` — "Reference the gateway-proxy skill"
5. `gw-upgrade.md`, `gw-versions.md` — references to `references/helm-lifecycle.md`
6. `marketplace.json` — `"name"`, `"source"`, `"skills"` fields
7. `IMPROVEMENT_PLAN.md` (×2) — title and label query URL

**Documentation files (cosmetic — won't break functionality):**
8. `README.md` — 3 mentions in plugin table, directory tree, commands section
9. `docs/lessons/plugin-integration-and-architecture.md` — 3 mentions
10. `docs/lessons/skill-to-plugin-migration.md` — 1 mention
11. `plugins/marketplace-manager/.../plugin_marketplace_guide.md` — 1 mention

**Ephemeral docs (leave as historical record):**
12. `docs/plans/2026-02-03-gateway-proxy-plugin.md` — original plan
13. `docs/plans/2026-02-25-feat-gateway-proxy-v2-agent-lifecycle-plan.md` — v2 plan

### GitHub Label Migration

| Current Label | Action | New Label |
|---|---|---|
| `plugin:gateway-proxy` | Rename | `plugin:gateway-manager` |
| `skill:gateway-proxy` | Delete after creating new ones | — |
| — | Create | `skill:kgateway` |
| — | Create | `skill:agentgateway` |

### GitHub Issue Updates

| Issue | Action |
|---|---|
| #60 (LiteLLM skill) | Update title/body: `gateway-proxy` → `gateway-manager`, update file paths to `plugins/gateway-manager/skills/litellm/` |
| #34 (failover/priority groups) | Update title: `gateway-proxy` → `agentgateway`, change label to `skill:agentgateway` (failover is an agentgateway feature) |
| #58 (closed — v2.0.0) | Leave as historical record |

### Multi-Skill Version Sync

Per institutional learning (`docs/solutions/logic-errors/multi-skill-plugin-version-sync.md`): the version sync script uses "highest version" logic for multi-skill plugins. With kgateway and agentgateway both starting at 1.0.0, this should work correctly. Monitor for drift as skills evolve independently.

## Acceptance Criteria

- [ ] Directory renamed: `plugins/gateway-proxy/` → `plugins/gateway-manager/`
- [ ] `skills/kgateway/` created with SKILL.md, IMPROVEMENT_PLAN.md, and 3 references
- [ ] `skills/agentgateway/` created with SKILL.md, IMPROVEMENT_PLAN.md, and 6 references
- [ ] `plugin.json` name updated to `gateway-manager`, version `3.0.0`
- [ ] `marketplace.json` updated: name, source path, skills array (2 skills)
- [ ] Agent `gateway-manager.md` paths updated to reference both new skills
- [ ] All 8 commands updated with correct skill references
- [ ] GitHub labels created: `plugin:gateway-manager`, `skill:kgateway`, `skill:agentgateway`
- [ ] Old labels renamed/removed: `plugin:gateway-proxy`, `skill:gateway-proxy`
- [ ] Issue #60 updated to reflect `gateway-manager` plugin name and paths
- [ ] Issue #34 updated with `skill:agentgateway` label
- [ ] `README.md` updated with new plugin name and structure
- [ ] Lessons docs updated (cosmetic references)
- [ ] Skillsmith eval score >= 80 for both kgateway and agentgateway skills
- [ ] No regressions: all 8 commands load correct context
- [ ] `old skills/gateway-proxy/` directory removed (content migrated)

## Success Metrics

- Both skills pass skillsmith evaluation with score >= 80
- Agent correctly routes to kgateway skill for Gateway API topics
- Agent correctly routes to agentgateway skill for AI/MCP routing topics
- Agent loads both skills for cross-cutting workflows (e.g., "set up AI gateway")
- Issue #60 LiteLLM plan is actionable with updated paths

## Dependencies & Risks

**Dependencies:**
- Must complete before issue #60 (LiteLLM skill) implementation begins
- Should align with upstream v2.3.0 namespace changes in reference content

**Risks:**
- **Content accuracy during split**: Incorrectly assigning content to wrong skill degrades guidance. Mitigate by reviewing each reference file line-by-line during split.
- **Agent routing quality**: Agent may struggle with ambiguous requests post-split. Mitigate with clear trigger phrases and fallback "load both" behavior.
- **Helm lifecycle split complexity**: `helm-lifecycle.md` covers both components in a single install sequence (CRDs → kgateway → agentgateway). Splitting requires each skill to reference the other for the full sequence. Mitigate by keeping the install sequence overview in both, with component-specific detail in each.

## Sources & References

- **Origin brainstorm:** [docs/brainstorms/2026-02-25-litellm-gateway-skill-brainstorm.md](docs/brainstorms/2026-02-25-litellm-gateway-skill-brainstorm.md) — raised rename question; LiteLLM skill as catalyst for multi-gateway architecture
- **Upstream divergence**: kgateway v2.3.0 splits agentgateway to separate repo (`agentgateway/agentgateway`)
- **Version sync lesson**: `docs/solutions/logic-errors/multi-skill-plugin-version-sync.md` — use "highest version" for multi-skill plugins
- **Migration template**: `docs/plans/skillsmith-plugin-migration.md` — major version bump for path changes
- Related issues: #60 (LiteLLM skill), #34 (failover docs), #58 (v2.0.0 agent — closed)
- Related plans: `docs/plans/2026-02-25-feat-litellm-gateway-skill-plan.md`, `docs/plans/2026-02-25-feat-gateway-proxy-v2-agent-lifecycle-plan.md`
