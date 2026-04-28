---
title: "feat: Foundry — consolidate skillsmith + marketplace-manager + agentsmith into a single plugin"
type: feat
status: active
date: 2026-04-27
deepened: 2026-04-27
---

# feat: Foundry — consolidate skillsmith + marketplace-manager + agentsmith into a single plugin

## Overview

Create a **foundry** plugin that consolidates three tightly coupled plugin lifecycle tools — skillsmith (skill quality), marketplace-manager (distribution/versioning), and a new agentsmith capability (agent quality) — into a single plugin. The three skills retain their identities, command namespaces (`ss-*`, `mp-*`, `as-*`), and individual SKILL.md versions, but ship as one installable unit that covers the full evaluate-improve-publish lifecycle for plugin development.

This supersedes `docs/plans/2026-04-22-001-feat-agentsmith-evaluation-improvement-pipeline-plan.md`, which planned agentsmith as a standalone plugin.

---

## Problem Frame

Three tools share a tight lifecycle — every skill/agent improvement ends with version bumping and marketplace syncing. Keeping them as separate plugins creates friction:

- Users must install and manage three plugins for what is functionally one workflow
- Cross-plugin invocation (`ss-improve` Step 6 invokes `marketplace-manager`) adds indirection
- The agentsmith capability (GitHub #163) would add a fourth plugin to this same workflow

The prior analysis in `docs/lessons/plugin-integration-and-architecture.md` recommended keeping them separate for concern separation. This plan overrides that decision based on a user-validated insight: **these tools serve the same person (the plugin developer) during the same workflow (build → evaluate → improve → publish)**, and the friction of three separate installs outweighs the theoretical benefits of separation.

Related issues:
- **#163** — Agentsmith: agent evaluation, improvement, and self-evolution pipeline
- **#152** — Plugin validation gap: structural checks miss agent content quality
- **#153** — Skillsmith workflow gaps: source path, version cascade, self-improvement
- **#160** — Archivist agent-native audit: one-off → repeatable

---

## Requirements Trace

- R1. Consolidate skillsmith, marketplace-manager, and agentsmith into a single `foundry` plugin
- R2. Preserve all existing functionality: 12 commands (`ss-*`, `mp-*`), 1 agent (`skill-observer`), 2 hooks, all scripts
- R3. Add agentsmith evaluation engine with 3 quality dimensions (Trigger Effectiveness, System Prompt Quality, Coherence)
- R4. Add `/as-evaluate` and `/as-improve` commands that orchestrate the improvement loop
- R5. Add PostToolUse hook for agent auto-evaluation on edit
- R6. Handle both flat (`agents/name.md`) and directory-based (`agents/name/AGENT.md`) agent file patterns
- R7. Agentsmith delegates: skill evaluation → skillsmith, version cascade → marketplace-manager, structural validation → marketplace-manager's pre-commit hook
- R8. Update marketplace.json (replace 2 entries with 1), WORKFLOW.md, and CLAUDE.md path references
- R9. Update `docs/lessons/plugin-integration-and-architecture.md` to reflect the revised decision

---

## Scope Boundaries

- Full consolidation of skillsmith + marketplace-manager + agentsmith Phase 1-2 (evaluation engine + improvement loop)
- All existing functionality preserved with no behavioral changes
- Path references updated throughout the repo

### Deferred to Follow-Up Work

- Agentsmith Phase 3 (workflow-to-command graduation): separate iteration once evaluation pipeline is proven
- Agentsmith Phase 4 (agent-native audit automation): depends on evaluation script maturity
- Agent-observer (session transcript analysis for agents): future, parallel to skill-observer
- Mise en place framework: generic agent composition/discoverability pattern

---

## Context & Research

### Relevant Code and Patterns

- `plugins/skillsmith/` — skill quality framework (v6.9.0): 1 skill, 7 commands, 1 agent, 2 hooks, 5 Python scripts
- `plugins/marketplace-manager/` — distribution framework (v4.0.0): 1 skill, 5 commands, 0 agents, 0 hooks, 4 Python scripts
- `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py` — evaluation engine architecture (3,169 lines)
- `plugins/skillsmith/commands/ss-improve.md` — improvement loop with source-path resolution
- `plugins/skillsmith/hooks/hooks.json` — hook configuration pattern (2 PostToolUse hooks)
- `plugin-dev:agent-development` — upstream agent spec (`system-prompt-design.md`, `triggering-examples.md`)
- Agent files across repo: archivist (flat), omnifocus-agent (flat), gateway-manager (flat), terminal-guru (flat), skill-observer (directory-based)

### Institutional Learnings

- **Orchestrate, don't replicate** (memory: `feedback_agentsmith_delegation_principle.md`): Agentsmith defers to upstream tools. Structural validation → marketplace-manager's pre-commit hook. Skill evaluation → skillsmith. Version cascade → marketplace-manager.
- **Context-aware evaluation** (`docs/lessons/evaluate-skill-false-positives.md`): Parse YAML frontmatter separately from body; skip code blocks during heuristic checks.
- **Multi-skill version sync** (`docs/solutions/logic-errors/multi-skill-plugin-version-sync.md`): The old `sync_marketplace_versions.py` was fixed to use `max(versions, key=_parse_semver)`, but the current `sync.py` (v4.0.0 rewrite) did not carry forward this logic — it skips multi-skill plugins as "ambiguous". Foundry with 3 skills requires fixing `sync.py` to implement highest-version-wins (addressed in U2).
- **Not all changes improve quality** (`docs/lessons/improvement-plan-metrics-tracking.md`): Baseline regression detection is essential. Store per-agent baselines in `.agentsmith-baselines.json`.
- **`$CLAUDE_PLUGIN_ROOT` paths are relative to plugin root**: Command files reference `${CLAUDE_PLUGIN_ROOT}/skills/<name>/scripts/...`. Moving commands into foundry preserves these paths unchanged because the `skills/` subdirectory structure stays the same.

---

## Key Technical Decisions

- **Plugin name: `foundry`**: Where plugin components are forged and refined. Encompasses the full lifecycle from quality evaluation through improvement to marketplace distribution.

- **Three skills, one plugin**: `skillsmith`, `marketplace-manager`, and `agentsmith` each retain their SKILL.md identity, command namespace, and individual SKILL.md version. The `plugin.json` carries a single package version (semver, per Anthropic spec). **Note:** the current `sync.py` skips multi-skill plugins (returns "ambiguous") — it must be updated to use highest-version-wins logic before foundry can rely on automated version sync. This is addressed in U2.

- **Plugin.json starts at v1.0.0**: Foundry is a new plugin identity. Individual SKILL.md versions carry forward (skillsmith v6.9.0, marketplace-manager v4.0.0, agentsmith v1.0.0) as informational metadata. The `plugin.json` version starts fresh at `1.0.0`.

- **Command namespaces preserved**: `ss-*` (7 commands), `mp-*` (5 commands), `as-*` (2 commands) — no renaming. Users' muscle memory is undisturbed.

- **3 agentsmith evaluation dimensions** (carried from prior plan):

  | Dimension | Weight | What It Measures |
  |-----------|--------|------------------|
  | Trigger Effectiveness | 35% | Example coverage (explicit, proactive, implicit), `<commentary>` presence, negative triggers, phrasing variety |
  | System Prompt Quality | 35% | Role specificity, concrete responsibilities, step-by-step process, quality standards, output format, edge cases, 500-3,000 word sweet spot |
  | Coherence | 30% | Description-body alignment, tool scope fitness, terminology consistency |

- **Repo-level scripts remain vendorable**: `marketplace-manager/scripts/repo/validate.py` and `sync.py` are designed to be copied into external repos. They must remain self-contained with no external dependencies, even inside the merged plugin.

- **Migration strategy**: Copy files (not git mv) to preserve clean history, then delete old directories in a separate commit. This keeps the consolidation reviewable.

---

## Open Questions

### Resolved During Planning

- **What about existing users of skillsmith/marketplace-manager?** — This is a personal marketplace. The user is the only consumer. Migration is a marketplace.json update.
- **Does `$CLAUDE_PLUGIN_ROOT` break?** — No. Commands reference `${CLAUDE_PLUGIN_ROOT}/skills/<skill-name>/scripts/...`. The `skills/` subdirectory structure is identical in the new plugin, so all paths resolve correctly.
- **How does multi-skill versioning work?** — `sync.py` already handles this: it selects `max(versions)` across all skills when a plugin has multiple. Foundry with 3 skills works out of the box.
- **Should existing hooks merge?** — Yes. Single `hooks.json` with 3 PostToolUse hooks: on-skill-edit, on-script-edit (from skillsmith), on-agent-edit (new for agentsmith).

### Deferred to Implementation

- Exact agentsmith scoring thresholds and sub-metric weights (calibrate against existing agents)
- Whether `--update-readme` should add agent quality scores alongside skill metrics (likely yes, format TBD)
- Hook fast-path heuristic details for agent detection (needs to handle both flat and directory patterns)

---

## Output Structure

```
plugins/foundry/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── skillsmith/              ← migrated from plugins/skillsmith/skills/skillsmith/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── evaluate_skill.py
│   │   │   └── utils.py
│   │   ├── references/
│   │   └── tests/
│   ├── marketplace-manager/     ← migrated from plugins/marketplace-manager/skills/marketplace-manager/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── repo/
│   │   │   │   ├── validate.py
│   │   │   │   └── sync.py
│   │   │   ├── setup.py
│   │   │   └── scaffold.py
│   │   └── references/
│   └── agentsmith/              ← new
│       ├── SKILL.md
│       ├── scripts/
│       │   ├── evaluate_agent.py
│       │   └── utils.py
│       ├── references/
│       │   └── agent-quality-rubric.md
│       └── tests/
│           └── test_evaluate_agent.py
├── commands/
│   ├── ss-evaluate.md           ← migrated (7 ss-* commands)
│   ├── ss-improve.md
│   ├── ss-init.md
│   ├── ss-observe.md
│   ├── ss-package.md
│   ├── ss-research.md
│   ├── ss-validate.md
│   ├── mp-add.md                ← migrated (5 mp-* commands)
│   ├── mp-list.md
│   ├── mp-status.md
│   ├── mp-sync.md
│   ├── mp-validate.md
│   ├── as-evaluate.md           ← new
│   └── as-improve.md            ← new
├── agents/
│   └── skill-observer/          ← migrated from plugins/skillsmith/agents/skill-observer/
│       ├── AGENT.md
│       └── scripts/
├── hooks/
│   ├── hooks.json               ← merged (3 PostToolUse hooks)
│   └── scripts/
│       ├── on-skill-edit.sh     ← migrated
│       ├── on-script-edit.sh    ← migrated
│       └── on-agent-edit.sh     ← new
├── README.md
└── LICENSE
```

---

## Implementation Units

- U1. **Create foundry plugin and migrate skillsmith**

**Goal:** Create the foundry plugin scaffold and copy all skillsmith content into it. Verify the migrated commands, hooks, and scripts work from the new location.

**Requirements:** R1, R2

**Dependencies:** None

**Files:**
- Create: `plugins/foundry/.claude-plugin/plugin.json`
- Create: `plugins/foundry/README.md`
- Create: `plugins/foundry/LICENSE`
- Copy: `plugins/skillsmith/skills/skillsmith/` → `plugins/foundry/skills/skillsmith/`
- Copy: `plugins/skillsmith/commands/*.md` → `plugins/foundry/commands/`
- Copy: `plugins/skillsmith/agents/skill-observer/` → `plugins/foundry/agents/skill-observer/`
- Copy: `plugins/skillsmith/hooks/` → `plugins/foundry/hooks/`

**Approach:**
- `plugin.json` uses name `foundry`, version `1.0.0`, description covers full scope
- Copy files (preserve originals until U7 cleanup) so both old and new work during migration
- README.md starts with `## Skill: skillsmith` section carrying forward the existing version history
- Verify `evaluate_skill.py` runs correctly from the new path: `uv run plugins/foundry/skills/skillsmith/scripts/evaluate_skill.py`
- Verify hook scripts work from new `$CLAUDE_PLUGIN_ROOT`

**Patterns to follow:**
- `plugins/skillsmith/.claude-plugin/plugin.json` — manifest format
- `plugins/skillsmith/README.md` — per-skill section format

**Test scenarios:**
- Happy path: `uv run plugins/foundry/skills/skillsmith/scripts/evaluate_skill.py plugins/foundry/skills/skillsmith` → produces valid scores
- Happy path: hook scripts reference `${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/` and resolve correctly
- Happy path: all 7 `ss-*` command files have correct `${CLAUDE_PLUGIN_ROOT}` paths
- Edge case: `utils.py` imports work from the new location (relative imports)

**Verification:**
- `evaluate_skill.py` runs on skillsmith's own SKILL.md from the new path
- All command files present with unchanged content (except any absolute path refs, if any)
- Hook scripts executable and correctly referencing foundry paths

---

- U2. **Migrate marketplace-manager into foundry and fix multi-skill sync**

**Goal:** Copy marketplace-manager content into the foundry plugin and fix `sync.py` to support multi-skill plugins (currently skips them as "ambiguous"). Without this fix, foundry's 3 skills would be silently skipped by version sync.

**Requirements:** R1, R2

**Dependencies:** U1

**Files:**
- Copy: `plugins/marketplace-manager/skills/marketplace-manager/` → `plugins/foundry/skills/marketplace-manager/`
- Copy: `plugins/marketplace-manager/commands/*.md` → `plugins/foundry/commands/`
- Modify: `plugins/foundry/skills/marketplace-manager/scripts/repo/sync.py` (add highest-version-wins logic for multi-skill plugins)
- Modify: `plugins/foundry/README.md` (add `## Skill: marketplace-manager` section)

**Approach:**
- Copy skill directory including `scripts/repo/` (vendorable scripts) — directory structure unchanged
- Copy all 5 `mp-*` commands
- **Fix `sync.py` multi-skill handling**: The current `resolve_version()` returns `(None, "multi-skill (ambiguous)")` for plugins with >1 skill directory (lines 109-110). Apply the highest-version-wins logic from the old `sync_marketplace_versions.py` fix: scan all `skills/*/SKILL.md` files, extract versions, select `max(versions, key=_parse_semver)`. The `_parse_semver` helper already exists in the lesson doc. For multi-skill plugins without plugin.json, this becomes the authoritative version. For multi-skill plugins WITH plugin.json (foundry's case), plugin.json takes priority — but the sync should still report if any skill version exceeds plugin.json's version.
- `setup.py` uses `Path(__file__).parent / "repo"` for repo-level script paths, which resolves correctly regardless of parent plugin name
- README.md gets a `## Skill: marketplace-manager` section carrying forward the version history

**Patterns to follow:**
- `docs/solutions/logic-errors/multi-skill-plugin-version-sync.md` — the original fix pattern to port to `sync.py`
- `plugins/marketplace-manager/skills/marketplace-manager/scripts/setup.py` — relative path resolution pattern

**Test scenarios:**
- Happy path: `uv run plugins/foundry/skills/marketplace-manager/scripts/repo/validate.py .claude-plugin/marketplace.json` → validates successfully
- Happy path: `sync.py` on foundry (3 skills) → correctly reads plugin.json version, does not skip as "ambiguous"
- Happy path: `sync.py --dry-run` on a multi-skill plugin without plugin.json → selects highest skill version
- Happy path: all 5 `mp-*` commands present with correct `${CLAUDE_PLUGIN_ROOT}` paths
- Edge case: `setup.py install-scripts` still copies repo-level scripts correctly (relative path resolution)
- Edge case: multi-skill plugin where one skill has no version → skips that skill, uses versions from others

**Verification:**
- `validate.py` and `sync.py` run against the repo's `marketplace.json` from the new path
- `sync.py` no longer skips multi-skill plugins — foundry entry syncs correctly
- All marketplace-manager commands present and referencing correct skill directory

---

- U3. **Create agentsmith evaluation engine**

**Goal:** Implement `evaluate_agent.py` with 3 quality dimensions derived from upstream `plugin-dev:agent-development` guidance. Agent quality evaluation is agentsmith's unique value — structural validation is enforced at commit time by marketplace-manager's pre-commit hook.

**Requirements:** R3, R6

**Dependencies:** U1 (uses skillsmith's evaluate_skill.py as architectural template)

**Files:**
- Create: `plugins/foundry/skills/agentsmith/scripts/evaluate_agent.py`
- Create: `plugins/foundry/skills/agentsmith/scripts/utils.py`
- Create: `plugins/foundry/skills/agentsmith/references/agent-quality-rubric.md`
- Test: `plugins/foundry/skills/agentsmith/tests/test_evaluate_agent.py`

**Approach:**
- Mirror `evaluate_skill.py` architecture: argparse CLI, dimension scoring functions, weighted overall score, multiple output formats
- PEP 723 inline metadata (`pyyaml>=6.0.1`)
- Agent file parser handles both flat and directory-based patterns; frontmatter parsed separately from body to avoid false positives (learned from skillsmith)
- 3 quality dimensions:
  - **Trigger Effectiveness (35%)**: example count and variety (explicit, proactive, implicit), `<commentary>` presence, negative triggers, phrasing variety, description specificity
  - **System Prompt Quality (35%)**: role specificity, concrete responsibilities, step-by-step process, quality standards, output format, edge cases, 500-3,000 word sweet spot
  - **Coherence (30%)**: description-body alignment, tool scope fitness, terminology consistency
- CLI flags: `--explain` (coaching), `--format json` (machine output), `--export-table-row` (README updates), `--quick` (hook use — one-line score summary)
- `utils.py`: `find_agent_file()` (handles both patterns), `load_baselines()`, `save_baselines()`
- Baseline storage: `.agentsmith-baselines.json` in plugin source directory

**Patterns to follow:**
- `plugins/foundry/skills/skillsmith/scripts/evaluate_skill.py` — CLI architecture, scoring model, output formatting
- `plugins/foundry/skills/skillsmith/scripts/utils.py` — shared utility pattern

**Test scenarios:**
- Happy path: evaluate archivist agent (flat) → scores for all 3 dimensions with weighted overall
- Happy path: evaluate skill-observer agent (directory) → correctly finds and parses AGENT.md
- Happy path: `--explain` → per-dimension coaching with sub-metric detail
- Happy path: `--format json` → valid JSON with dimension scores and overall
- Happy path: `--quick` → one-line score summary, completes in under 2 seconds
- Edge case: agent with zero `<example>` blocks → Trigger Effectiveness scores low with coaching
- Edge case: agent with no `tools` array → Coherence scores tool alignment based on whether system prompt scope justifies full access
- Edge case: agent with multi-line YAML block scalar description (`|`) → parses correctly
- Error path: non-agent file → clear error, not stack trace
- Error path: nonexistent path → exit code 1 with message
- Error path: malformed YAML frontmatter → clear parse error
- Integration: baseline file created on first eval; subsequent evals compare and flag regressions

**Verification:**
- Running against all 5 existing agents produces differentiated scores
- `--quick` completes in under 2 seconds
- Baseline file created and populated after first run

---

- U4. **Calibrate agentsmith scoring against existing agents**

**Goal:** Run the evaluation engine against all 5 existing agents to verify scores differentiate meaningfully and adjust thresholds.

**Requirements:** R3

**Dependencies:** U3

**Files:**
- Modify: `plugins/foundry/skills/agentsmith/scripts/evaluate_agent.py` (threshold adjustments)
- Modify: `plugins/foundry/skills/agentsmith/references/agent-quality-rubric.md` (document calibration results)
- Modify: agent files with known structural issues (e.g., gateway-manager missing `model` field)

**Approach:**
- Fix known structural compliance issues first (gateway-manager `model` field)
- Evaluate all 5 agents and manually rank them by quality (human judgment)
- Verify scoring produces the same ordinal ranking; accept whatever point spread emerges naturally
- Adjust weights and thresholds if scores produce counterintuitive rankings
- Document calibration results and final thresholds in the rubric reference
- Save calibration baselines for all 5 agents

**Patterns to follow:**
- `docs/lessons/skills-evaluation-summary.md` — evaluation-at-scale pattern

**Test scenarios:**
- Happy path: 5 agents produce scores matching the manually-determined quality ranking
- Happy path: agents with comprehensive descriptions + system prompts outscore minimal ones
- Edge case: two agents score identically overall → per-dimension scores still differentiate
- Integration: scores stable across repeated runs (deterministic scoring)

**Verification:**
- Calibration results documented in `agent-quality-rubric.md` with scores for all 5 agents
- Scoring ordinal ranking matches human judgment
- Dimension weights finalized

---

- U5. **Create agentsmith commands, SKILL.md, and hook**

**Goal:** Create the `/as-evaluate` and `/as-improve` commands, the agentsmith SKILL.md, and the PostToolUse hook for agent auto-evaluation.

**Requirements:** R4, R5, R7

**Dependencies:** U3, U4

**Files:**
- Create: `plugins/foundry/skills/agentsmith/SKILL.md`
- Create: `plugins/foundry/commands/as-evaluate.md`
- Create: `plugins/foundry/commands/as-improve.md`
- Create: `plugins/foundry/hooks/scripts/on-agent-edit.sh`
- Modify: `plugins/foundry/hooks/hooks.json` (add agent edit hook)
- Modify: `plugins/foundry/README.md` (add `## Skill: agentsmith` section)

**Approach:**
- `/as-evaluate` wraps `evaluate_agent.py` invocation with argument handling
- `/as-improve` orchestrates the full improvement loop:
  - Step 0: Verify target is agent; redirect skills → skillsmith, hooks/commands → plugin-dev
  - Step 0a: Source-path resolution (installed cache → source repo via marketplace.json)
  - Step 1: Run `evaluate_agent.py --explain`, report top-3 quality gaps
  - Step 1b: If plugin has skills, run skillsmith evaluate on each (intra-plugin call now)
  - Step 2: Apply improvements; reference `plugin-dev:agent-development` for guidance
  - Step 3: Re-evaluate; compare against baseline; block if regression
  - Step 4: Update README with `--export-table-row`
  - Step 5: Version bump — PATCH/MINOR/MAJOR in `plugin.json`
  - Step 6: Sync marketplace — invoke `sync.py` directly at `${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/repo/sync.py` (now a sibling skill, not a separate plugin invocation)
- Hook: PostToolUse on Write|Edit, bash fast-path filters for `/agents/` + `.md`, runs `evaluate_agent.py --quick`
- SKILL.md triggers on: "evaluate my agent", "improve agent quality", "agent metrics", "check agent description", "agent isn't triggering"
- Update `ss-improve`: (1) redirect agent targets → agentsmith (intra-plugin redirect), (2) rewrite Step 6 from "invoke marketplace-manager" (natural language plugin reference that won't resolve after consolidation) to direct `sync.py` invocation via `${CLAUDE_PLUGIN_ROOT}` path

**Patterns to follow:**
- `plugins/foundry/commands/ss-improve.md` — improvement loop structure
- `plugins/foundry/hooks/scripts/on-skill-edit.sh` — PostToolUse hook pattern

**Test scenarios:**
- Happy path: `/as-evaluate` on archivist → displays 3 quality dimension scores with overall
- Happy path: `/as-improve` on source-repo agent → completes all 6 steps, version bumped, marketplace synced
- Happy path: `/as-improve` on agent whose plugin has skills → skillsmith eval runs on each skill
- Happy path: edit agent `.md` → hook fires, displays score summary
- Happy path: edit non-agent file → hook exits in milliseconds (bash filter, no Python)
- Edge case: installed-cache path → remaps to source repo
- Edge case: no source mapping → aborts with guidance
- Edge case: regression detected in Step 3 → blocks version bump, reports which dimensions dropped
- Edge case: edit installed-cache agent → hook skips
- Error path: `/as-improve` target is SKILL.md → redirects to skillsmith with message
- Error path: `/as-evaluate` on non-agent file → clear error
- Error path: `evaluate_agent.py` fails in hook → exits cleanly, doesn't block edit
- Integration: version cascade → plugin.json bumped AND marketplace.json synced
- Integration: `ss-improve` on an agent file → redirects to agentsmith

**Verification:**
- Full `/as-improve` loop completes and leaves repo in clean state
- Hook fires on agent edits and completes in under 2 seconds
- Non-agent file edits add negligible latency
- Bidirectional redirects work (ss-improve ↔ as-improve)

---

- U6. **Update marketplace.json, cross-references, and cleanup**

**Goal:** Replace the two old marketplace entries with a single foundry entry, update all path references across the repo, update the architecture lesson, and remove the old plugin directories.

**Requirements:** R8, R9

**Dependencies:** U1, U2, U5

**Files:**
- Modify: `.claude-plugin/marketplace.json` (remove `skillsmith` + `marketplace-manager` entries, add `foundry` entry)
- Modify: `WORKFLOW.md` (update all `plugins/skillsmith/` and `plugins/marketplace-manager/` paths to `plugins/foundry/`; also fix stale `sync_marketplace_versions.py` references → `sync.py`)
- Modify: `.claude/CLAUDE.md` (update `evaluate_skill.py` path)
- Modify: `plugins/omnifocus-manager/CONTRIBUTING.md` (update `evaluate_skill.py` path reference)
- Modify: `plugins/foundry/skills/skillsmith/references/integration_guide.md` (update to reflect intra-plugin coordination)
- Modify: `docs/lessons/plugin-integration-and-architecture.md` (add addendum: consolidation decision revisited)
- Delete: `plugins/skillsmith/` (entire directory)
- Delete: `plugins/marketplace-manager/` (entire directory)
- Modify: `docs/plans/2026-04-22-001-feat-agentsmith-evaluation-improvement-pipeline-plan.md` (set `status: superseded`)

**Approach:**
- marketplace.json: single entry `{ "name": "foundry", "source": "./plugins/foundry", "version": "1.0.0" }`
- Run `validate.py` against updated marketplace.json to confirm validity
- Run `sync.py` to confirm version sync works with 3 skills
- **Repo-wide path sweep**: `rg "plugins/skillsmith|plugins/marketplace-manager"` across entire repo (not just WORKFLOW.md and CLAUDE.md) to catch references in other plugins' docs (e.g., `plugins/omnifocus-manager/CONTRIBUTING.md`). Also fix `sync_marketplace_versions.py` → `sync.py` (stale script name predating the v4.0.0 rewrite)
- Architecture lesson: add dated addendum explaining the consolidation rationale — don't delete the original analysis, as the reasoning was sound; the override is based on user-validated workflow friction
- Delete old directories only after all references are updated and validated

**Patterns to follow:**
- `.claude-plugin/marketplace.json` — existing entry format
- `WORKFLOW.md` — existing path reference patterns

**Test scenarios:**
- Happy path: `validate.py` passes on updated marketplace.json with no errors
- Happy path: `sync.py --dry-run` correctly identifies foundry's 3 skills and syncs from plugin.json
- Happy path: no remaining references to `plugins/skillsmith/` or `plugins/marketplace-manager/` anywhere in repo (outside docs/plans/ and docs/lessons/)
- Happy path: no remaining references to `sync_marketplace_versions.py` in WORKFLOW.md
- Integration: full end-to-end — install foundry from marketplace.json, run `ss-evaluate`, `mp-validate`, `as-evaluate`

**Verification:**
- `rg "plugins/skillsmith|plugins/marketplace-manager" --glob '!docs/plans/*' --glob '!docs/lessons/*' --glob '!docs/solutions/*'` returns zero matches
- `validate.py` and `sync.py` pass cleanly
- Old directories removed
- Architecture lesson updated with addendum

---

## System-Wide Impact

- **Interaction graph:** `/as-improve` orchestrates: skillsmith (sibling skill evaluation), `plugin-dev:agent-development` (improvement guidance reference), marketplace-manager's `sync.py` (sibling version sync). PostToolUse hooks (3 total) fire on Write|Edit events. `/ss-improve` updated to redirect agent targets to agentsmith (intra-plugin). Structural validation remains at commit time via marketplace-manager's pre-commit hook.
- **Error propagation:** If any delegated tool fails, `/as-improve` reports which step failed and aborts. Hook failures exit silently (never block editing). Migration failures during U6 are caught by `validate.py`.
- **State lifecycle risks:** Source-path resolution is highest risk — incorrect remapping writes to wrong locations. Marketplace.json transition from 2 entries to 1 must be atomic. Baseline file (`.agentsmith-baselines.json`) stored per-plugin in source directory.
- **API surface parity:** After foundry ships, `ss-improve` redirects agents → agentsmith (intra-plugin). `as-improve` redirects skills → skillsmith (intra-plugin). Bidirectional routing.
- **Unchanged invariants:** Upstream `plugin-dev:plugin-validator` and `plugin-dev:agent-development` are referenced, not modified. The pre-commit hook in marketplace repos continues to use vendored `validate.py` and `sync.py` — those scripts are self-contained and unaffected by where they live in the source tree.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Multi-skill version sync confusion with 3 skills | U2 fixes `sync.py` to add highest-version-wins logic (currently skips multi-skill plugins); verified in U2 test scenarios |
| Stale references to old plugin paths | `rg` sweep in U6 verification; `validate.py` catches marketplace.json issues |
| Agent evaluation dimensions don't differentiate | U4 calibration step against 5 real agents; adjust weights before shipping |
| Hook performance stacking (3 hooks on every Write/Edit) | Bash fast-path filters exit in milliseconds for non-matching files |
| Breaking existing skillsmith/marketplace-manager installs | Personal marketplace — single consumer, clean cut-over |
| False positives in system prompt analysis | Parse frontmatter separately from body; skip code blocks (learned from skillsmith) |

---

## Documentation / Operational Notes

- Update `docs/lessons/plugin-integration-and-architecture.md` with addendum explaining consolidation rationale
- Mark prior agentsmith plan as superseded
- Plugin-level README.md carries forward version history from both skillsmith and marketplace-manager READMEs
- Update memory file `marketplace-manager.md` to reflect foundry consolidation

---

## Sources & References

- **Prior plan (superseded):** `docs/plans/2026-04-22-001-feat-agentsmith-evaluation-improvement-pipeline-plan.md`
- Related issues: #163 (agentsmith), #152 (validation gap), #153 (skillsmith workflow gaps), #160 (agent-native audit)
- Related code: `plugins/skillsmith/` (source), `plugins/marketplace-manager/` (source), `plugin-dev:agent-development` (upstream spec)
- Institutional learnings: `docs/lessons/plugin-integration-and-architecture.md`, `docs/lessons/evaluate-skill-false-positives.md`, `docs/solutions/logic-errors/multi-skill-plugin-version-sync.md`
- Memory: `feedback_agentsmith_delegation_principle.md` (orchestrate, don't replicate)
