---
title: "feat(gateway-proxy): Add gateway-manager agent, lifecycle commands, and cloud provider support"
type: feat
status: implementation-complete
date: 2026-02-25
issue: "#58"
origin: "~/.claude/plans/ticklish-popping-hedgehog.md (10 issues discovered using agentgateway as Vertex AI proxy)"
---

# feat(gateway-proxy): Gateway Manager Agent, Lifecycle Commands, Cloud Providers (v2.0.0)

## Enhancement Summary

**Deepened on:** 2026-02-25
**Review agents used:** agent-native-reviewer, architecture-strategist, security-sentinel, code-simplicity-reviewer, pattern-recognition-specialist, agent-native-architecture skill, create-agent-skills skill, learnings-researcher
**Research agents used:** Helm upgrade best practices, K8s Gateway API patterns, agentgateway features (v0.10-v0.12)

### Key Improvements from Research

1. **Split `provider-backends.md`** into simple + cloud provider reference files (architecture review)
2. **Add A2A protocol documentation** — new `references/a2a-routing.md` (agentgateway research: A2A support not in plan at all)
3. **Update MCP routing** — StreamableHTTP, stateful routing, target policies, MCP auth (agentgateway v0.11-v0.12 features)
4. **v2.3.0-beta namespace split** — agentgateway moves to `agentgateway-system` namespace (breaking change)
5. **Secret handling security** — use `kubectl create secret` over YAML `stringData` to avoid keys in agent output (security review)
6. **CronJob RBAC must use `resourceNames`** — scope to specific secret, not all secrets in namespace (security review)
7. **Add "Remove/Decommission" workflow** to agent — CRUD completeness gap (agent-native review)
8. **Reframe agent workflows as outcomes**, not step-by-step procedures (agent-native-architecture skill)
9. **Agent color collision** — change from `cyan` (used by terminal-guru) to `green` (pattern review)
10. **Conditional reference loading** in agent — load per workflow, not all 7 at startup (architecture review)

### Simplicity Review Tension (Decision Required)

The simplicity reviewer argues the agent is a YAGNI violation — the enhanced skill + commands address all 10 gaps without an agent. The agent-native and architecture reviewers see it as the correct Stage 3 evolution. **This is a scope decision for the user**: ship skill+commands only (v1.2.0) or include the agent (v2.0.0).

### New Discoveries from Research

- **14 documentation gaps** found in existing skill (agentgateway v0.11-v0.12 features)
- **Helm upgrade safety pattern**: always use `--atomic --wait --cleanup-on-fail` + backup values before upgrading
- **v2.3.0-beta**: `enableAgentgateway` flag removed from kgateway; separate namespace required
- **New auth mechanisms**: Basic auth, API key auth, HTTP ExtAuthz, mTLS (v0.11.0+)
- **CEL 2.0 breaking changes**: function name renames, 5-500x performance improvement
- **agentgateway governance change**: now a Linux Foundation project (kgateway is CNCF sandbox)

### Security Findings (Priority Order)

| Severity | Finding | Mitigation |
|----------|---------|------------|
| Critical | Secret values visible in agent YAML output via `${VAR}` expansion | Use `kubectl create secret --from-literal` instead of YAML `stringData` |
| High | CronJob RBAC allows access to ALL namespace secrets | Scope Role to specific `resourceNames` |
| High | Agent boundary enforcement is prompt-only | Add explicit confirmation-matching rules + mandatory `--dry-run=client` |
| High | No rotation guidance for static API keys | Add Secret Lifecycle section with rotation cadence |
| Medium | CORS `allowOrigins: ["*"]` in templates | Add warning comment; flag in `/gw-eval` |
| Medium | No gateway-level authentication | Document auth options; flag unauthenticated gateways in eval |
| Medium | Helm upgrade without state backup | Add `helm get values` backup step before upgrade |

## Overview

Enhance the gateway-proxy plugin from a static skill+commands plugin (Stage 2) into an intelligent gateway management system (Stage 3) with an autonomous agent, lifecycle operations, and cloud provider support. This addresses all 10 gaps identified during the Vertex AI proxy investigation.

**Issue**: [#58](https://github.com/totallyGreg/claude-mp/issues/58)
**Version**: 1.1.0 → 2.0.0 (MAJOR — new agent, new commands, significant skill expansion)

## Upstream Architecture: kgateway / agentgateway Split

**Critical context** discovered during planning: kgateway and agentgateway are **diverging into separate projects** starting with v2.3.0.

From the [kgateway README](https://github.com/kgateway-dev/kgateway):
> Starting with version 2.3.0, the control plane for agentgateway has been migrated to the [agentgateway](https://github.com/agentgateway/agentgateway) repo, enabling a singular focus for kgateway to be a stable, robust, and battle-tested API Gateway powered by Envoy.

| Project | Repo | Purpose | Data Plane |
|---------|------|---------|------------|
| **kgateway** | `kgateway-dev/kgateway` | K8s Gateway API control plane for Envoy | Envoy |
| **agentgateway** | `agentgateway/agentgateway` | AI/agentic proxy for MCP, A2A, LLM routing | Rust-native |

**Current state (v2.2.x)**: Both are released from `kgateway-dev/kgateway`. The agentgateway CRDs and helm charts ship alongside kgateway.

**Future state (v2.3.0+)**: agentgateway control plane moves to `agentgateway/agentgateway`. kgateway provides the K8s control plane, agentgateway is the data plane.

### Implications for Plugin Design

This split means the plugin should be structured to accommodate both projects diverging:

1. **Version checking** must query both repos: `kgateway-dev/kgateway` (latest: v2.2.1) and `agentgateway/agentgateway` (latest: v0.12.0, but K8s integration still via kgateway for now)
2. **Skill split consideration**: A future `agentgateway` skill focused on standalone/non-K8s deployments may make sense as the projects diverge. For v2.0.0, keep one skill since the K8s CRDs are still coupled.
3. **Agent must be version-aware**: The agent should detect installed version and adapt behavior — v2.2.x patterns vs v2.3.0+ patterns may differ.

## Design Decisions

Carried forward from brainstorming session:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Agent + enhanced single skill + new commands | Cohesive; skill = knowledge, agent = orchestration, commands = quick actions |
| Agent autonomy | Present-and-confirm | Generate YAML → show to user → apply on approval. Safety over speed. |
| Version data | Live GitHub fetch | No curated matrix to maintain; `gh api` against both repos |
| Skill structure | Single skill for now, designed for future split | Keep one skill while K8s CRDs are coupled; split when agentgateway fully separates |
| Plugin scope | kgateway/agentgateway on K8s | Standalone agentgateway and other products (Kong, Apigee) as separate skills later |
| GitHub repos | `kgateway-dev/kgateway` + `agentgateway/agentgateway` | Both repos for version/release data; kgateway for K8s-specific, agentgateway for standalone |

## Target Directory Structure

```
plugins/gateway-proxy/
├── .claude-plugin/
│   └── plugin.json                         # v2.0.0
├── agents/
│   └── gateway-manager.md                  # NEW — autonomous agent
├── commands/
│   ├── gw-status.md                        # existing (unchanged)
│   ├── gw-debug.md                         # existing (unchanged)
│   ├── gw-route.md                         # existing (unchanged)
│   ├── gw-backend.md                       # MODIFIED — add cloud providers
│   ├── gw-logs.md                          # existing (unchanged)
│   ├── gw-versions.md                      # NEW — version comparison
│   ├── gw-upgrade.md                       # NEW — helm upgrade guidance
│   └── gw-eval.md                          # NEW — config evaluation
├── skills/gateway-proxy/
│   ├── SKILL.md                            # MODIFIED — agent ref, cloud providers, version awareness
│   ├── IMPROVEMENT_PLAN.md                 # MODIFIED — v2.0.0 entry
│   └── references/
│       ├── provider-backends.md            # MODIFIED — add Vertex AI, Azure OpenAI, Bedrock
│       ├── resource-patterns.md            # MODIFIED — CRD disambiguation
│       ├── lessons-learned.md              # MODIFIED — cloud auth, local vs cloud
│       ├── mcp-routing.md                  # existing (unchanged)
│       ├── external-processing.md          # existing (unchanged)
│       └── helm-lifecycle.md               # NEW — upgrade, rollback, version checking
```

## Implementation Phases

### Phase 1: Agent Foundation

Create the `gateway-manager` agent as the core orchestration layer. This is the highest-value addition — it enables all the "translate intent into config" workflows.

#### Task 1.1: Create `agents/gateway-manager.md`

**File**: `plugins/gateway-proxy/agents/gateway-manager.md`

**Frontmatter** (follow pkm-manager and terminal-guru conventions):

```yaml
---
name: gateway-manager
description: |
  Use this agent when managing kgateway and agentgateway resources on Kubernetes:
  "add an Anthropic backend", "set up Vertex AI routing", "check gateway versions",
  "upgrade agentgateway", "evaluate my gateway config", "why isn't my route working",
  "add rate limiting", "configure CORS", "set up MCP routing".

  <example>
  Context: User wants to add a new LLM provider
  user: "Add an Anthropic backend to my gateway"
  assistant: "I'll use the gateway-manager agent to generate the backend, secret, and route YAML."
  <commentary>
  Configuration workflow: detect current state → generate YAML → present for approval → apply.
  </commentary>
  </example>

  <example>
  Context: User wants to check for updates
  user: "Am I on the latest agentgateway version?"
  assistant: "I'll use the gateway-manager agent to compare installed vs latest versions."
  <commentary>
  Version check workflow: read installed chart versions → fetch GitHub releases → compare → report.
  </commentary>
  </example>

  <example>
  Context: User wants complex cloud provider setup
  user: "Set up routing to Claude on Vertex AI"
  assistant: "I'll use the gateway-manager agent to generate all required resources including auth."
  <commentary>
  Cloud provider workflow: generate backend + route + token secret + optional CronJob → present all YAML → apply on approval.
  </commentary>
  </example>

  <example>
  Context: User wants to diagnose an issue
  user: "My ollama route is returning 404s"
  assistant: "I'll use the gateway-manager agent to diagnose the routing issue."
  <commentary>
  Diagnostic workflow: check route attachment → verify path rewriting → inspect backend → check logs → report findings.
  </commentary>
  </example>

  <example>
  Context: User wants to upgrade helm charts
  user: "Upgrade my gateway to the latest version"
  assistant: "I'll use the gateway-manager agent to plan the upgrade."
  <commentary>
  Upgrade workflow: check installed versions → fetch latest → generate upgrade commands → present for approval → guide execution.
  </commentary>
  </example>

tools: ["Read", "Bash", "Grep", "Glob", "WebFetch"]
color: cyan
---
```

**Body structure** (system prompt):

```markdown
# Gateway Manager Agent

You are an expert Kubernetes gateway operator specializing in kgateway and
agentgateway. You orchestrate configuration, upgrades, and diagnostics for
AI/LLM routing infrastructure.

## Domain Knowledge

Load the gateway-proxy skill for domain knowledge:
- Core skill: `${CLAUDE_PLUGIN_ROOT}/skills/gateway-proxy/SKILL.md`
- Provider backends: `${CLAUDE_PLUGIN_ROOT}/skills/gateway-proxy/references/provider-backends.md`
- Resource patterns: `${CLAUDE_PLUGIN_ROOT}/skills/gateway-proxy/references/resource-patterns.md`
- Helm lifecycle: `${CLAUDE_PLUGIN_ROOT}/skills/gateway-proxy/references/helm-lifecycle.md`
- Lessons learned: `${CLAUDE_PLUGIN_ROOT}/skills/gateway-proxy/references/lessons-learned.md`
- MCP routing: `${CLAUDE_PLUGIN_ROOT}/skills/gateway-proxy/references/mcp-routing.md`
- External processing: `${CLAUDE_PLUGIN_ROOT}/skills/gateway-proxy/references/external-processing.md`

## Core Workflows

### 1. Evaluate (Current State Assessment)
- Run `kubectl get gateway,agentgatewaybackend,httproute,agentgatewaypolicy -n kgateway-system`
- Check installed helm chart versions
- Compare against best practices from skill references
- Report: healthy resources, misconfigurations, missing routes, orphaned resources

### 2. Configure (Generate Resources)
- Determine provider type from user request
- Load provider-specific patterns from references/provider-backends.md
- Generate complete YAML (Secret + Backend + HTTPRoute)
- **Always present YAML to user for approval before applying**
- Apply with `kubectl apply -f -` only after explicit user confirmation

### 3. Upgrade (Version Management)
- Check installed versions: `helm list -n kgateway-system`
- Fetch latest releases from GitHub:
  - `gh api repos/kgateway-dev/kgateway/releases/latest`
  - `gh api repos/agentgateway/agentgateway/releases/latest`
- Compare and report differences
- Generate helm upgrade commands
- **Present commands for user to execute** (never auto-upgrade)

### 4. Diagnose (Troubleshooting)
- Read controller logs for errors
- Check resource status and events
- Cross-reference with known issues from lessons-learned.md
- Provide specific remediation steps

### 5. Translate (Intent → Config)
- User describes what they want in natural language
- Agent maps to required resources
- Generates complete multi-resource YAML
- Handles dependencies (e.g., Secret before Backend)

## Bounded Autonomy

### Always safe (do without asking):
- Read operations: kubectl get, describe, logs
- GitHub API reads: release info, changelog
- YAML generation (displayed, not applied)

### Requires user confirmation:
- kubectl apply (any resource creation/modification)
- kubectl delete (any resource deletion)
- helm upgrade (any chart upgrade)
- Any destructive operation

## Version Checking

When checking versions, use `gh api` for GitHub releases:

```bash
# kgateway latest
gh api repos/kgateway-dev/kgateway/releases/latest --jq '.tag_name'

# agentgateway latest
gh api repos/agentgateway/agentgateway/releases/latest --jq '.tag_name'

# Installed versions
helm list -n kgateway-system -o json | jq '.[] | {name: .name, version: .app_version, chart: .chart}'
```

For release notes and new features:

```bash
# Recent releases with notes
gh api repos/kgateway-dev/kgateway/releases --jq '.[:3] | .[] | {tag: .tag_name, date: .published_at, body: .body}'
gh api repos/agentgateway/agentgateway/releases --jq '.[:3] | .[] | {tag: .tag_name, date: .published_at, body: .body}'
```

## CRD System Awareness

Two backend CRD systems exist — never confuse them:

| CRD | API Group | Gateway Class | When to Use |
|-----|-----------|--------------|-------------|
| `AgentgatewayBackend` | `agentgateway.dev/v1alpha1` | `agentgateway` | AI/MCP backends (current setup) |
| `Backend` | `gateway.kgateway.dev/v1alpha1` | `kgateway` | Generic backends (Lambda, static, DFP) |

The user's ai-gateway uses `gatewayClassName: agentgateway`, so always use `AgentgatewayBackend`.

## Output Format

When presenting YAML for approval:

1. Show the complete YAML in a fenced code block
2. Explain what each resource does
3. Highlight any prerequisites (env vars, secrets)
4. Ask: "Apply this configuration? (yes/no)"
5. Only proceed with `kubectl apply` after explicit "yes"
```

**Acceptance criteria**:
- [ ] Agent triggers on gateway management phrases
- [ ] Agent loads skill references for domain knowledge
- [ ] Agent uses present-and-confirm for all mutations
- [ ] Agent can fetch versions from GitHub via `gh api`
- [ ] 5+ example blocks in description for reliable triggering

---

### Phase 2: Lifecycle Commands

Add three new slash commands for common lifecycle operations. These are quick-access commands that don't require the full agent.

#### Task 2.1: Create `/gw-versions` command

**File**: `plugins/gateway-proxy/commands/gw-versions.md`

**Behavior**: Compare installed helm chart versions against latest GitHub releases.

```markdown
Compare installed kgateway and agentgateway helm chart versions against the latest GitHub releases.

Run the following commands to gather version information:

1. Installed versions:
\```bash
helm list -n kgateway-system -o json 2>/dev/null | jq -r '.[] | "\(.name)\t\(.chart)\t\(.app_version)"' || echo "No helm releases found in kgateway-system"
\```

2. Latest kgateway release:
\```bash
gh api repos/kgateway-dev/kgateway/releases/latest --jq '{tag: .tag_name, date: .published_at, url: .html_url}' 2>/dev/null || echo "Could not fetch kgateway releases"
\```

3. Latest agentgateway release:
\```bash
gh api repos/agentgateway/agentgateway/releases/latest --jq '{tag: .tag_name, date: .published_at, url: .html_url}' 2>/dev/null || echo "Could not fetch agentgateway releases"
\```

4. Gateway API CRD version:
\```bash
kubectl get crd gateways.gateway.networking.k8s.io -o jsonpath='{.metadata.labels.gateway\.networking\.k8s\.io/bundle-version}' 2>/dev/null || echo "Gateway API CRDs not found"
\```

Present results in a comparison table:

| Component | Installed | Latest | Status |
|-----------|-----------|--------|--------|
| kgateway-crds | ... | ... | ✅ Current / ⚠️ Update available |
| kgateway | ... | ... | ✅ Current / ⚠️ Update available |
| agentgateway-crds | ... | ... | ✅ Current / ⚠️ Update available |
| agentgateway | ... | ... | ✅ Current / ⚠️ Update available |
| Gateway API CRDs | ... | ... | ✅ Current / ⚠️ Update available |

If updates are available, show what's new by fetching release notes:
\```bash
gh api repos/<repo>/releases/latest --jq '.body' | head -30
\```

Suggest running `/gw-upgrade` if updates are available.
```

#### Task 2.2: Create `/gw-upgrade` command

**File**: `plugins/gateway-proxy/commands/gw-upgrade.md`

**Behavior**: Guide through helm chart upgrades with pre/post validation.

```markdown
Guide a helm chart upgrade for kgateway and/or agentgateway.
$ARGUMENTS

If no arguments, check all components. If a component name is given (kgateway, agentgateway), upgrade only that.

## Pre-upgrade Checks

1. Current state:
\```bash
kubectl get gateway,agentgatewaybackend,httproute,agentgatewaypolicy -n kgateway-system
helm list -n kgateway-system
\```

2. Latest versions:
\```bash
gh api repos/kgateway-dev/kgateway/releases/latest --jq '.tag_name'
gh api repos/agentgateway/agentgateway/releases/latest --jq '.tag_name'
\```

3. Breaking changes check:
\```bash
gh api repos/<repo>/releases/latest --jq '.body'
\```

## Upgrade Commands

Present the upgrade commands in correct order (CRDs first, then controllers).
Reference the gateway-proxy skill's `references/helm-lifecycle.md` for patterns.

Upgrade order:
1. Gateway API CRDs (if needed)
2. kgateway-crds
3. kgateway controller
4. agentgateway-crds
5. agentgateway controller

## Post-upgrade Validation

After upgrade, run:
\```bash
kubectl get gateway,agentgatewaybackend,httproute -n kgateway-system
kubectl get pods -n kgateway-system
\```

Verify all resources show healthy status. Check logs for errors:
\```bash
kubectl -n kgateway-system logs -l app.kubernetes.io/name=kgateway --tail=20
kubectl -n kgateway-system logs -l app.kubernetes.io/name=agentgateway --tail=20
\```

Present all commands for user approval before executing anything.
```

#### Task 2.3: Create `/gw-eval` command

**File**: `plugins/gateway-proxy/commands/gw-eval.md`

**Behavior**: Evaluate current gateway configuration against best practices.

```markdown
Evaluate the current kgateway/agentgateway configuration for issues and best practices.

Run the following diagnostic checks:

1. Resource inventory:
\```bash
kubectl get gateway,agentgatewaybackend,httproute,agentgatewaypolicy -n kgateway-system -o wide
\```

2. Version check:
\```bash
helm list -n kgateway-system -o json 2>/dev/null
\```

3. Route-to-backend mapping:
\```bash
kubectl get httproute -n kgateway-system -o json | jq '.items[] | {name: .metadata.name, backends: [.spec.rules[].backendRefs[]?.name]}'
\```

4. Backends without routes:
\```bash
# Get all backend names
kubectl get agentgatewaybackend -n kgateway-system -o jsonpath='{.items[*].metadata.name}'
# Compare against route backendRefs to find orphans
\```

5. Gateway health:
\```bash
kubectl get gateway -n kgateway-system -o json | jq '.items[] | {name: .metadata.name, programmed: .status.conditions[] | select(.type=="Programmed") | .status}'
\```

6. Pod status:
\```bash
kubectl get pods -n kgateway-system -l 'app.kubernetes.io/name in (kgateway,agentgateway)' -o wide
\```

Reference the gateway-proxy skill for best practices.

## Evaluation Report

Present findings in these categories:

### Health Status
- Gateway programmed and accepting traffic?
- All controller pods running?
- All backends accepted?

### Configuration Quality
- Every backend has a corresponding HTTPRoute?
- AI routes include URLRewrite with ReplacePrefixMatch?
- Policies attached and accepted?
- Gateway name doesn't conflict with controller name?

### Version Status
- Installed version vs latest release
- Any RC versions in production?

### Recommendations
- List specific fixes with YAML snippets
- Prioritize: errors > warnings > improvements
```

---

### Phase 3: Skill Enhancement — Cloud Providers

Address Issues 1-6 from the origin document. This is the largest content addition.

#### Task 3.1: Add cloud providers to `references/provider-backends.md`

**File**: `plugins/gateway-proxy/skills/gateway-proxy/references/provider-backends.md`

Add three new sections after the existing Gemini section:

**Vertex AI (GCP)** section covering:
- Provider type: `vertexai` with `model`, `projectId`, `region` fields
- Auth: `secretRef` with Bearer token (GCP access tokens expire in 60 min)
- Token refresh CronJob pattern (mount ADC, refresh every 45 min, update secret)
- RBAC for CronJob ServiceAccount to update secrets
- Protocol translation: OpenAI → Vertex AI Anthropic (`rawPredict` endpoint)
- Model name format differences (hyphens vs `@` version suffix)
- Local vs cloud auth (ADC file vs metadata server / Workload Identity)
- Warning: `gcp` auth type exists in docs but NOT in released CRDs (as of v2.2.1)

**Azure OpenAI** section covering:
- Provider type: `azureopenai` with deployment name, API version
- Auth: `secretRef` with Azure API key
- Endpoint format: `<resource>.openai.azure.com`

**AWS Bedrock** section covering:
- Provider type: `bedrock` with region, model ID
- Auth: AWS IAM credentials
- Local: mounted credentials file

Also add:
- **Provider API Comparison Table**: Update existing table with all 7 providers
- **Model Name Mapping Table**: Format differences per provider

#### Task 3.2: Add token lifecycle patterns

Add to `references/provider-backends.md` or a new section in `references/lessons-learned.md`:

- CronJob YAML for GCP token refresh (ServiceAccount, Role, RoleBinding, CronJob)
- Secret structure for Bearer token auth
- Monitoring/alerting for token refresh failures
- Manual token refresh command for debugging

#### Task 3.3: Document protocol translation

Add to `references/provider-backends.md`:

- How agentgateway translates between provider formats
- OpenAI → Anthropic Messages API differences
- OpenAI → Vertex AI rawPredict routing
- Model name mapping behavior

---

### Phase 4: Skill Enhancement — CRD & Version Awareness

Address Issues 7-9 from the origin document.

#### Task 4.1: Add CRD disambiguation to `references/resource-patterns.md`

Add a new section at the top of the file:

```markdown
## Backend CRD Systems

Two separate backend systems exist — using the wrong one causes routes that don't resolve.

| CRD | API Group | Gateway Class | Purpose |
|-----|-----------|--------------|---------|
| `AgentgatewayBackend` | `agentgateway.dev/v1alpha1` | `agentgateway` | AI/MCP backends with native protocol translation |
| `Backend` | `gateway.kgateway.dev/v1alpha1` | `kgateway` | Generic backends (AWS Lambda, Static, DFP) with aiExtension sidecar |

**Rule**: Match CRD type to your Gateway's `gatewayClassName`.
- `gatewayClassName: agentgateway` → use `AgentgatewayBackend`
- `gatewayClassName: kgateway` → use `Backend`

**Common mistake**: The `kgateway` zsh function and some older docs use the `Backend` CRD pattern. If your gateway uses `agentgateway` class, these will create resources that routes can't find.
```

#### Task 4.2: Create `references/helm-lifecycle.md`

**File**: `plugins/gateway-proxy/skills/gateway-proxy/references/helm-lifecycle.md`

Content covering:
- Installation sequence (Gateway API CRDs → kgateway-crds → kgateway → agentgateway-crds → agentgateway)
- Version checking commands (helm list, gh api for releases)
- Upgrade procedure (CRDs first, then controllers, preserve order)
- Rollback procedure (helm rollback, CRD pinning)
- CRD refresh patterns (when to re-apply CRDs)
- Version-specific feature availability warnings
- GitHub repos: `kgateway-dev/kgateway`, `agentgateway/agentgateway`
- Docs-vs-reality drift: always inspect installed CRD to know what's available
  ```bash
  kubectl get crd agentgatewaybackends.agentgateway.dev -o json | jq '.spec.versions[0].schema.openAPIV3Schema.properties.spec'
  ```

#### Task 4.3: Add version awareness to SKILL.md

Add a brief section to SKILL.md:

```markdown
## Version Awareness

The agent and `/gw-versions` command can check for updates live:
- Fetches latest releases from GitHub
- Compares against installed helm chart versions
- Warns about docs-vs-reality drift (features documented on `main` may not exist in released versions)
- Always inspect installed CRD to verify field availability
```

---

### Phase 5: Skill Enhancement — Environment Patterns

Address Issue 10 from the origin document.

#### Task 5.1: Add environment patterns to `references/lessons-learned.md`

Add a section covering local vs cloud deployment differences:

| Concern | Local (OrbStack) | Cloud (GKE/EKS/AKS) |
|---------|-------------------|---------------------|
| Host access | `host.internal` | Service DNS |
| GCP auth | Mounted ADC + CronJob | Workload Identity / metadata server |
| AWS auth | Mounted credentials | IAM roles for service accounts |
| Azure auth | API key in secret | Managed Identity |
| Egress | Direct outbound | VPC/firewall rules |
| Metadata server | Not available | Available |

---

### Phase 6: Update Existing Components

#### Task 6.1: Enhance `/gw-backend` command

**File**: `plugins/gateway-proxy/commands/gw-backend.md`

Add `vertexai`, `azureopenai`, `bedrock` to the supported providers list. For each, include the appropriate YAML template referencing the expanded `provider-backends.md`.

#### Task 6.2: Update SKILL.md

**File**: `plugins/gateway-proxy/skills/gateway-proxy/SKILL.md`

Changes:
- Add agent reference in Quick Commands table
- Add cloud providers to the Overview LLM Providers list
- Add Version Awareness section
- Add reference to `references/helm-lifecycle.md` in Reference Files section
- Update description/trigger phrases in frontmatter to include agent-related triggers

#### Task 6.3: Update `plugin.json`

**File**: `plugins/gateway-proxy/.claude-plugin/plugin.json`

- Bump version to `2.0.0`
- Update description to mention agent, lifecycle, and cloud providers
- Add new keywords: `agent`, `lifecycle`, `vertex-ai`, `helm`

#### Task 6.4: Update IMPROVEMENT_PLAN.md

**File**: `plugins/gateway-proxy/skills/gateway-proxy/IMPROVEMENT_PLAN.md`

- Add v2.0.0 row to Version History with eval scores
- Add #58 to Active Work (remove after completion)

---

### Phase 7: Validation & Release

#### Task 7.1: Run skillsmith evaluation

```bash
uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py \
  plugins/gateway-proxy/skills/gateway-proxy --quick --strict
```

Target: Overall score ≥ 85.

#### Task 7.2: Sync marketplace

```bash
uv run plugins/marketplace-manager/skills/marketplace-manager/scripts/sync_marketplace_versions.py
```

#### Task 7.3: Two-commit release

1. **Commit 1 — Implementation**: All file changes
   ```
   feat(gateway-proxy): Add gateway-manager agent, lifecycle commands, cloud providers (#58)
   ```

2. **Commit 2 — Release**: Version bumps, IMPROVEMENT_PLAN update, marketplace sync
   ```
   chore: Release gateway-proxy v2.0.0

   Closes #58
   ```

## Acceptance Criteria

- [ ] `gateway-manager` agent triggers on gateway management phrases (5+ examples)
- [ ] Agent generates complete YAML and presents for approval before applying
- [ ] Agent fetches latest versions from GitHub via `gh api`
- [ ] `/gw-versions` shows installed vs latest for all helm charts
- [ ] `/gw-upgrade` generates upgrade commands in correct order
- [ ] `/gw-eval` identifies stale versions, orphaned resources, missing best practices
- [ ] Vertex AI provider documented with token refresh CronJob pattern
- [ ] Azure OpenAI and AWS Bedrock providers documented
- [ ] Backend vs AgentgatewayBackend CRD disambiguation documented
- [ ] `references/helm-lifecycle.md` covers upgrade, rollback, version checking
- [ ] Local vs cloud environment patterns documented
- [ ] `/gw-backend` supports cloud providers
- [ ] Skillsmith eval score ≥ 85 overall
- [ ] marketplace.json synced

## Edge Cases & Risks

| Risk | Mitigation |
|------|------------|
| GitHub API rate limiting during version checks | Use `gh api` (authenticated); fall back gracefully with error message |
| GitHub repo names may change | Document repos in helm-lifecycle.md; agent can adapt if fetch fails |
| Vertex AI token refresh CronJob failure | Document monitoring patterns; agent should warn about silent failures |
| CRD fields differ between versions | Agent should inspect installed CRD before generating YAML |
| Agent generates invalid YAML for newer/older versions | Agent should `kubectl apply --dry-run=client` before presenting to user |
| Existing issue #34 (failover/priority groups) | Separate concern; can be addressed independently |
| No cluster / kubectl unavailable | Agent should detect and report clearly, not produce cryptic errors |
| No Gateway resource exists when adding backend | Agent should detect prerequisite and offer to create Gateway as part of flow |
| Namespace hardcoded to kgateway-system | Agent should detect actual namespace from `helm list` or ask if ambiguous |
| RC vs stable version ambiguity | `/gw-versions` shows both stable and pre-release latest; let user decide |

## SpecFlow Analysis: Key Gaps Addressed

The SpecFlow analysis identified gaps that are incorporated into the plan:

### Prerequisite Detection
The agent's system prompt (Phase 1) includes a prerequisite detection sequence at the start of any configuration flow: check kubectl connectivity → check namespace → check installed CRDs → check Gateway resource → check installed versions. If prerequisites are missing, the agent offers to create them.

### Present-and-Confirm Mechanics
The agent handles: approval ("yes", "apply it"), rejection (ask what to change, modify, re-present), partial approval ("apply the backend but not the route"), and follow-up questions before approving. Multi-resource YAML is grouped by concern with explanations between blocks, single approval for the batch.

### `/gw-eval` Specific Checks
Minimum check list with severity levels:
- **Critical**: Routes pointing to non-existent backends, Gateway not programmed, controller pods not ready
- **Warning**: Backends with no routes (orphaned), stale versions, RC versions in use, secrets referenced but not found
- **Info**: CORS policy missing, no rate limiting configured, debug logging enabled

### `/gw-backend` Boundary for Cloud Providers
Simple providers (ollama, openai, anthropic, gemini) handled by the command directly. Complex providers (vertexai, azureopenai, bedrock) generate backend YAML with a warning comment noting additional auth setup is needed, and suggest using the gateway-manager agent for full setup.

### `/gw-upgrade` Execution Model
Present upgrade commands as a numbered sequence. Ask "Shall I run these?" with a single confirmation. Upgrade order is enforced: CRDs first, then controllers. Include rollback commands in the output.

### Environment Detection
Agent attempts auto-detection via `kubectl cluster-info` to determine OrbStack vs cloud. Falls back to asking if ambiguous. Adjusts host references and auth patterns accordingly.

## Dependencies

- `gh` CLI installed and authenticated (for GitHub API calls)
- `kubectl` configured with cluster access
- `helm` installed (for version checking and upgrades)
- Existing gateway-proxy plugin v1.1.0 as foundation

## Sources & References

### Origin
- **Investigation document**: `~/.claude/plans/ticklish-popping-hedgehog.md` — 10 issues discovered using agentgateway as Vertex AI proxy
- **Issue**: [#58](https://github.com/totallyGreg/claude-mp/issues/58)

### Internal References
- Agent conventions: `plugins/pkm-plugin/agents/pkm-manager.md`, `plugins/terminal-guru/agents/terminal-guru.md`
- Plugin structure: `docs/lessons/skill-to-plugin-migration.md` (Stage 2 → Stage 3 evolution)
- Live data fetch pattern: `plugins/ai-risk-mapper/skills/ai-risk-mapper/scripts/fetch_cosai_schemas.py`
- Original plugin plan: `docs/plans/2026-02-03-gateway-proxy-plugin.md`
- Release workflow: `WORKFLOW.md`

### External References
- kgateway repo: `github.com/kgateway-dev/kgateway` — K8s control plane + Envoy data plane
- agentgateway repo: `github.com/agentgateway/agentgateway` — Rust AI/agentic data plane (standalone + K8s via kgateway)
- **Note**: Starting v2.3.0, agentgateway control plane migrates from kgateway to agentgateway repo
- Gateway API spec: `gateway-api.sigs.k8s.io`
- agentgateway docs (standalone): `agentgateway.dev/docs`
- agentgateway docs (K8s): `kgateway.dev/docs/agentgateway`
