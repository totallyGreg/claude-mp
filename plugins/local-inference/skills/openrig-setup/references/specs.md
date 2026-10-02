# OpenRig spec formats

Source: openrig.dev/specs/{rigspec,agentspec,agent-startup-guide,edge-types}
(checked 2026-10-01 against CLI 0.5.17). Format versions: RigSpec "0.2",
AgentSpec "1.0", RigBundle schema 2.

## RigSpec — `rig.yaml`

```yaml
version: "0.2"            # required, exactly "0.2"
name: my-rig              # required; used in session names, snapshots, library lookup
summary: >                # optional
  What this team is for.
culture_file: CULTURE.md  # optional safe relative path: rig-wide norms
docs: []                  # optional supporting docs that travel with the rig
permission_policy: builtin:standard  # recorded posture (rig policy apply); absent = "floor". Also per member
workspace:                # optional (not in the docs; from the 0.5.17 validator)
  workspace_root: /path/to/hub        # required
  repos:                              # required; relative paths resolve against workspace_root
    - {name: app, path: app, kind: project}   # kind: user|project|knowledge|lab|delivery
  default_repo: app                   # optional, must match a repo name
  knowledge_root: /path/to/notes      # optional
startup: {files: [], actions: []}   # rig layer, applies to every member
services: {kind: compose, ...}      # optional; compose is the only kind
pods:                     # required, non-empty
  - id: dev               # no dots
    label: Development
    continuity_policy:    # optional
      enabled: true
      sync_triggers: [pre_compaction, pre_shutdown]
      artifacts: {session_log: true, restore_brief: true}
      restore_protocol: {peer_driven: true, verify_via_quiz: false}
    members:
      - id: impl          # no dots; seat address dev-impl@my-rig, logical id dev.impl
        agent_ref: "local:agents/impl"   # local:<relative to rig.yaml> or path:<absolute>
        profile: default
        runtime: claude-code             # claude-code | codex | terminal
        cwd: "."                         # session start dir, relative to THIS FILE's dir (or absolute)
        label: "Implementation Lead"
        model: <model-id>                # optional; omit to use the harness default
        restore_policy: resume_if_possible   # | relaunch_fresh | checkpoint_only
      - id: server                       # terminal node: exact triple, all three
        runtime: terminal
        agent_ref: "builtin:terminal"
        profile: none
    edges:                               # pod-local: unqualified ids
      - {kind: delegates_to, from: impl, to: qa}
edges:                                   # cross-pod: pod.member ids
  - {kind: can_observe, from: rev.r1, to: dev.impl}
```

Edge kinds: `delegates_to` (orchestrator → worker), `can_observe`,
`collaborates_with` (peers), `escalates_to` (worker → orchestrator).

Allowed keys (anything else is rejected) — rig: version, name, summary,
culture_file, permission_policy, managed_blocks, docs, startup, services,
workspace, pods, edges. Pod: id, label, summary, continuity_policy, startup,
members, edges. Member: id, label, agent_ref, profile, runtime,
codex_config_profile, model, role, permission_policy, cwd, restore_policy,
compaction_strategy, mechanic, startup, session_source, starter_ref.

Validator rules that bite: version must be "0.2"; no dots in pod/member ids;
`agent_ref` must be `local:` or `path:` (except the terminal triple);
startup actions need `idempotent`, and non-idempotent actions can't apply on
`restore`.

Built-in library specs live under the installed CLI
(`rig specs show <name>` prints the path) and use `local:../../../agents/...`
refs. Those break when the yaml is copied elsewhere — rewrite them to `path:`
(`scripts/claude_only_spec.py` does this).

## AgentSpec — `agent.yaml`

```yaml
name: my-agent
version: "1.0"            # informational
defaults: {}              # runtime, model, lifecycle when the member doesn't override
imports:
  - ref: "local:../shared"     # `ref`, not the old `source`
resources:                # the pool: what exists
  skills: []              # dirs with SKILL.md, delivered by skill_install
  guidance: []            # markdown merged into CLAUDE.md / AGENTS.md as managed content
  subagents: []
  hooks: []
  runtime_resources: []   # harness config files (claude settings, mcp)
profiles:                 # a MAP, not an array; each selects from resources
  default:
    uses:
      skills: [openrig-user, shared:some-skill]   # qualified when imported
      guidance: [role]
      subagents: []
      hooks: []
      runtime_resources: [shared:claude-default-settings]
    lifecycle:
      restore_policy: resume_if_possible
startup: {files: [], actions: []}
```

Lifecycle: `execution_mode: interactive_resident` (only accepted value);
`compaction_strategy: harness_native | pod_continuity`. No secrets, no session
IDs, no topology (cwd, edges, pods belong in the RigSpec).

The built-in AgentSpecs are runtime-neutral: their profiles list both Claude and
Codex runtime resources, so a seat only needs `runtime:` changed in the RigSpec.

## Startup content

Layers merge additively, in order: agent → profile → rig → culture_file → pod →
member → operator overlays. Most rigs need only role guidance (agent), a culture
file (rig) and the odd member overlay.

```yaml
files:
  - path: guidance/role.md
    delivery_hint: guidance_merge   # merged into CLAUDE.md before boot — reliable
    required: true
    applies_on: [fresh_start]       # fresh_start | restore — split fresh-only from restore content
  - path: skills/openrig-user
    delivery_hint: skill_install    # projected before boot — reliable
    required: true
actions:
  - type: send_text                 # typed after the harness is ready — reliable
    value: "Load openrig-user and verify your environment."
    phase: after_ready
    idempotent: true
```

Reliability: guidance_merge, skill_install, send_text are supported. Hook and
runtime-resource projection and MCP install are experimental. System
dependencies are never installed — describe the desired state in guidance and
have the agent check it.

Skill vs guidance: reusable procedure → skill. Role, team, project or
environment facts → guidance / startup.
