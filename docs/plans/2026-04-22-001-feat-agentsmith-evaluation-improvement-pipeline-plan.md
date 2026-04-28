---
title: "feat: Agentsmith — agent evaluation, improvement, and self-evolution pipeline"
type: feat
status: superseded
date: 2026-04-22
superseded_by: docs/plans/2026-04-27-001-feat-foundry-plugin-consolidation-plan.md
---

# feat: Agentsmith — agent evaluation, improvement, and self-evolution pipeline

## Overview

Create an Agentsmith plugin that is the single entry point for agent quality work. Agentsmith **orchestrates** existing tools — delegating skill evaluation to `skillsmith` and version management to `marketplace-manager` — while adding the quality dimensions that none of those tools cover: trigger effectiveness, system prompt quality, and description-body coherence. Structural validation is enforced by marketplace-manager's pre-commit hook at commit time, not at evaluation time.

Agents are always bundled in plugins with commands pointing to scripts embedded in skills. Agentsmith understands this topology and evaluates the full plugin surface when improving an agent.

## Problem Frame

Three existing issues surface this gap from different angles:

- **#152** — Plugin structural validation misses agent content quality entirely
- **#153** — Skillsmith can't self-improve, operates on installed copies, and lacks version cascade — the same problems apply to any agent improvement loop
- **#160** — Archivist agent-native audit scored 71% as a one-off — no repeatable evaluation pipeline exists

The architectural lesson from `docs/lessons/plugin-integration-and-architecture.md` is clear: keep quality tools for different artifact types as separate plugins. But the deeper lesson is: **orchestrate, don't replicate**. Agentsmith delegates structural checks to the upstream tools that own them and focuses on the quality dimensions nobody else covers.

## Requirements Trace

- R1. Evaluate agent `.md` files across quality dimensions with numeric scores (0-100), focusing on dimensions upstream tools don't cover
- R2. Provide an improvement loop that orchestrates evaluation → gap identification → fixes → re-evaluation → version cascade
- R3. Handle both installed-cache paths and source-repo paths, always writing to source
- R4. Support both flat (`agents/name.md`) and directory-based (`agents/name/AGENT.md`) agent file patterns
- R5. Delegate skill evaluation to `skillsmith` when the agent's plugin contains skills
- R6. Delegate version cascade to `marketplace-manager` (plugin.json → marketplace.json)
- R7. Structural validation enforced at commit time by marketplace-manager's pre-commit hook — not reimplemented or delegated at evaluation time
- R8. Provide a PostToolUse hook that auto-evaluates agent files on edit

## Scope Boundaries

- Agent quality evaluation and orchestrated improvement — no reimplementation of upstream validation
- Content-level improvements only — structural refactoring (flat → directory-based) is a manual recommendation, not automated
- Phase 1-2 only in this plan — workflow graduation (Phase 3 from #163) and agent-native audit automation (Phase 4) are deferred

### Deferred to Separate Tasks

- Workflow-to-command graduation: separate iteration once evaluation pipeline is proven
- Agent-native audit automation (formalizing #160's 8-principle rubric): depends on evaluation script maturity
- Agent-observer (session transcript analysis for agents): future, parallel to skill-observer
- Mise en place framework: generic agent composition/discoverability pattern that agentsmith would be the first consumer of

## Context & Research

### Relevant Code and Patterns

- `plugins/skillsmith/` — structural template (plugin layout, commands, hooks, scripts)
- `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py` — evaluation engine architecture (dimensions, CLI flags, README updates)
- `plugins/skillsmith/commands/ss-improve.md` — improvement loop with source-path resolution (Step 0a)
- `plugin-dev:plugin-validator` — upstream agent for structural validation (frontmatter fields, example format, tool declarations)
- `plugin-dev:agent-development` — upstream spec for agent creation (required fields: name, description, model, color; recommended: tools)
- Agent files across repo: `plugins/archivist/agents/archivist.md` (flat), `plugins/omnifocus-manager/agents/omnifocus-agent.md` (flat), `plugins/gateway-manager/agents/gateway-manager.md` (flat), `plugins/terminal-guru/agents/terminal-guru.md` (flat), `plugins/skillsmith/agents/skill-observer/AGENT.md` (directory-based)

### Institutional Learnings

- **Orchestrate, don't replicate** (session feedback 2026-04-22): Tools should defer to upstream specs and existing tools rather than reimplementing their capabilities. Agentsmith calls skillsmith for skill quality, marketplace-manager for version sync. Structural validation is enforced at commit time by marketplace-manager's pre-commit hook — agentsmith doesn't invoke or reimplement it.
- **Separate quality plugins by artifact type** (`docs/lessons/plugin-integration-and-architecture.md`): Do NOT fold into skillsmith. They serve different artifacts and will evolve independently.
- **Context-aware evaluation rules** (`docs/lessons/evaluate-skill-false-positives.md`): Design evaluation rules that parse YAML frontmatter separately from body content and skip code blocks during heuristic checks.
- **Installed vs source path confusion** (`docs/lessons/improvement-plan-metrics-tracking.md`): Source-path resolution must be robust from day one.
- **Not all changes improve quality** (`docs/lessons/improvement-plan-metrics-tracking.md`): Regression detection is essential — store baseline scores and flag regressions.

### Calibration Targets

The 5 existing agents in the repo serve as calibration targets. A well-designed scoring system should produce meaningful differentiation:
- Archivist (8 examples, comprehensive system prompt) — should score high
- Skill-observer (compact, focused, directory-based) — should score high on different dimensions
- Gateway-manager (missing required `model` field — fix for compliance before calibrating quality scores), terminal-guru, omnifocus-agent — should score variably based on their actual quality

## Key Technical Decisions

- **Orchestrator, not standalone engine**: Agentsmith is the tool you call for agent work. It delegates skill evaluation to `skillsmith` and version cascade to `marketplace-manager`. Structural validation (frontmatter fields, name formats) is enforced by marketplace-manager's pre-commit hook at commit time — agentsmith does not reimplement or invoke it. Agentsmith adds the quality dimensions nobody else covers.

- **Agent version = plugin version**: Agent `.md` files have no version field in their frontmatter. When `/as-improve` modifies an agent, it bumps `plugin.json` only — agents are part of the plugin release unit.

- **3 evaluation dimensions** derived from `plugin-dev:agent-development` upstream quality guidance (`system-prompt-design.md`, `triggering-examples.md`, `agent-creation-system-prompt.md`):

  | Dimension | Weight | What It Measures | Derived From |
  |-----------|--------|------------------|-------------|
  | Trigger Effectiveness | 35% | Do examples cover explicit, proactive, and implicit triggers? Do they vary phrasings? Is `<commentary>` present? Are there negative triggers (when NOT to use)? Is description specific enough to avoid over/under-triggering? | `triggering-examples.md` |
  | System Prompt Quality | 35% | Is the role specific (not "help the user")? Are responsibilities concrete? Is there a step-by-step process? Are quality standards measurable? Is output format defined? Are edge cases handled? Is length in the 500-3,000 word sweet spot (per upstream guidance)? | `system-prompt-design.md` |
  | Coherence | 30% | Do description examples match what the system prompt enables? Are there capabilities claimed in examples that the body doesn't cover (or vice versa)? Are tools declared that the prompt never references? Does the prompt reference tools not in the `tools` array? | Cross-referencing description ↔ body ↔ tools |

  **What this consolidates:** Conciseness is a sub-metric within System Prompt Quality (the upstream spec already defines 500-3,000 words as the sweet spot). Tool scope fitness is a sub-metric within Coherence (tool alignment is one facet of description-body consistency). This avoids standalone dimensions that either duplicate upstream structural checks or penalize thoroughness.

  Structural compliance (required frontmatter fields, field formats, name validation) is **not** an agentsmith dimension — that's enforced by marketplace-manager's pre-commit hook at commit time. Agentsmith evaluates quality only.

  Weights are initial and should be calibrated against the 5 existing agents.

- **Agent detection**: For the hook fast-path, check for `agents/` parent directory + `.md` extension in bash (no Python). For `evaluate_agent.py`, parse YAML frontmatter and verify `description` field contains `<example>` blocks (the distinguishing feature of agent `.md` files vs other markdown).

- **Read-only evaluate on any path, write-only improve on source paths**: `/as-evaluate` works on any readable agent path (including installed cache). `/as-improve` requires source repo access and aborts with guidance if path remapping fails.

- **Plugin-wide evaluation**: When `/as-improve` runs on an agent, it also evaluates the agent's sibling skills (via skillsmith) and reports a holistic plugin quality summary. Agents don't exist in isolation — they bundle with commands and skills.

- **Baseline regression detection**: `evaluate_agent.py` stores baseline scores in a `.agentsmith-baselines.json` file in the plugin's source directory. `/as-improve` Step 3 compares post-improvement scores against this baseline and blocks the version bump if overall score regresses.

- **`as-` command prefix**: Following skillsmith's `ss-` convention (e.g., `as-evaluate`, `as-improve`).

## Open Questions

### Resolved During Planning

- **What are the evaluation dimensions?** — 3 quality dimensions derived from upstream `plugin-dev:agent-development` guidance: Trigger Effectiveness, System Prompt Quality, Coherence. Structural compliance enforced at commit time by marketplace-manager's pre-commit hook.
- **How does version bumping work for agents?** — Bump `plugin.json` only. Agents don't carry their own version.
- **Should evaluate work on installed paths?** — Yes, read-only. Improve requires source access.
- **How does agent detection work?** — Hook fast-path: bash check for `agents/` directory + `.md` extension. Python: parse frontmatter, verify `<example>` blocks in description.
- **Where do baseline scores persist?** — `.agentsmith-baselines.json` in the plugin's source directory.
- **Where does structural validation happen?** — At commit time via marketplace-manager's pre-commit hook. Agentsmith does not invoke plugin-dev:plugin-validator at evaluation or improvement time.

### Deferred to Implementation

- Exact scoring thresholds and sub-metric weights within each dimension (calibrate against existing agents during implementation)
- Whether `--update-readme` should add agent quality scores to the plugin README alongside skill metrics (likely yes, format TBD)
- Hook fast-path heuristic details (needs to handle both flat and directory patterns, exit in milliseconds for non-agent files)
- Tool alignment sub-metrics within Coherence: how to handle agents without a `tools` array (omitted = full access per upstream spec — score based on whether system prompt scope justifies full access)

## Output Structure

```
plugins/agentsmith/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── as-evaluate.md
│   └── as-improve.md
├── hooks/
│   ├── hooks.json
│   └── scripts/
│       └── on-agent-edit.sh
├── skills/
│   └── agentsmith/
│       ├── SKILL.md
│       ├── scripts/
│       │   ├── evaluate_agent.py
│       │   └── utils.py
│       └── references/
│           └── agent-quality-rubric.md
├── README.md
└── LICENSE
```

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

```
evaluate_agent.py <agent-path> [--explain] [--format json] [--export-table-row]
  |
  +-- resolve_agent_path(path)
  |     |-- detect flat vs directory pattern
  |     |-- if installed cache: resolve to source via marketplace.json (read-only eval still works)
  |     \-- parse YAML frontmatter + system prompt body + extract <example> blocks
  |
  +-- score_trigger_effectiveness(description, examples)
  |     |-- count examples (minimum 2 per upstream spec)
  |     |-- classify example types: explicit, proactive, implicit, edge-case
  |     |-- check each example has <commentary>
  |     |-- check for negative triggers ("Do NOT use", "when not to use")
  |     |-- check triggering condition specificity (not too generic, not too narrow)
  |     \-- check phrasing variety across examples
  |
  +-- score_system_prompt_quality(body)
  |     |-- role specificity (not "help the user" — concrete domain + expertise)
  |     |-- responsibilities concreteness (measurable, not vague)
  |     |-- process steps (step-by-step, not "analyze the code")
  |     |-- quality standards presence (measurable criteria)
  |     |-- output format definition (structured, not "provide a report")
  |     |-- edge case handling
  |     \-- length in sweet spot (500-3,000 words per upstream; penalty above 10,000)
  |
  +-- score_coherence(description, body, tools)
  |     |-- do examples claim capabilities the body doesn't enable?
  |     |-- does the body describe workflows not represented in examples?
  |     |-- are declared tools referenced in the body?
  |     |-- does the body reference tools not in the tools array?
  |     \-- terminology consistency between description and body
  |
  +-- compute_overall(weights)
  +-- load_baseline(plugin_path)                 ← REGRESSION CHECK
  |     \-- compare against .agentsmith-baselines.json
  \-- output(format, scores, baseline_delta)

  Note: structural validation (frontmatter fields, name formats) is NOT
  part of evaluate_agent.py. It is enforced at commit time by
  marketplace-manager's pre-commit hook.


/as-improve <agent-path>  (slash command — runs in Claude conversation context)
  |
  +-- Step 0: Verify target is agent; redirect non-agents
  +-- Step 0a: Source-path resolution (installed cache → source repo)
  +-- Step 1: Run evaluate_agent.py --explain, report top-3 gaps
  +-- Step 1b: If plugin has skills → run skillsmith eval on each  ← DELEGATE
  +-- Step 2: Apply improvements (reference plugin-dev:agent-development for guidance)
  +-- Step 3: Re-evaluate, compare against baseline, block if regression
  +-- Step 4: Update README (--export-table-row)
  +-- Step 5: Version bump plugin.json
  +-- Step 6: Sync marketplace  ← DELEGATE to marketplace-manager

  Note: no plugin-validator step. Structural compliance is caught by
  the pre-commit hook when changes are committed.
```

## Implementation Units

- [ ] **Unit 1: Plugin scaffold and evaluate_agent.py core**

  **Goal:** Create the agentsmith plugin structure and implement the core evaluation engine with 3 quality dimensions derived from upstream `plugin-dev:agent-development` guidance.

  **Requirements:** R1, R4

  **Dependencies:** None

  **Files:**
  - Create: `plugins/agentsmith/.claude-plugin/plugin.json`
  - Create: `plugins/agentsmith/skills/agentsmith/scripts/evaluate_agent.py`
  - Create: `plugins/agentsmith/skills/agentsmith/scripts/utils.py`
  - Create: `plugins/agentsmith/skills/agentsmith/references/agent-quality-rubric.md`
  - Create: `plugins/agentsmith/README.md`
  - Create: `plugins/agentsmith/LICENSE`
  - Test: `plugins/agentsmith/skills/agentsmith/tests/test_evaluate_agent.py`

  **Approach:**
  - Mirror `evaluate_skill.py`'s architecture: argparse CLI, dimension scoring functions, weighted overall score, multiple output formats
  - PEP 723 inline metadata header (`pyyaml>=6.0.1` dependency)
  - Agent file parser handles both flat and directory-based patterns; frontmatter parsed separately from body to avoid false positives
  - 3 quality dimensions (Trigger Effectiveness, System Prompt Quality, Coherence) derived from upstream `plugin-dev:agent-development` guidance — no structural validation (enforced at commit time by marketplace-manager pre-commit hook)
  - `--explain` provides per-dimension coaching with sub-metric detail; `--format json` for machine output; `--export-table-row` for README updates
  - `--quick` flag for hook use: skips baseline comparison and coaching output, produces one-line score summary only
  - `utils.py` provides: `find_agent_file()` (handles both patterns), `load_baselines()`, `save_baselines()`
  - Baseline storage: `.agentsmith-baselines.json` in plugin source directory, keyed by agent name, stores per-dimension scores and overall

  **Patterns to follow:**
  - `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py` — CLI architecture, output formatting
  - `plugins/skillsmith/skills/skillsmith/scripts/utils.py` — shared utility pattern

  **Test scenarios:**
  - Happy path: evaluate archivist agent (flat) → produces scores for all 3 quality dimensions with overall weighted score
  - Happy path: evaluate skill-observer agent (directory) → correctly finds and parses AGENT.md
  - Happy path: `--explain` → per-dimension coaching with sub-metric detail
  - Happy path: `--format json` → valid JSON with dimension scores and overall
  - Happy path: `--quick` → produces one-line score summary, completes in under 2 seconds
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

- [ ] **Unit 2: Calibrate scoring against existing agents**

  **Goal:** Fix known structural compliance issues in existing agents, then run the evaluation engine against all 5 to verify scores differentiate and adjust thresholds.

  **Requirements:** R1

  **Dependencies:** Unit 1

  **Files:**
  - Modify: agent files that fail structural checks (e.g., gateway-manager missing `model` field)
  - Modify: `plugins/agentsmith/skills/agentsmith/scripts/evaluate_agent.py` (threshold adjustments)
  - Modify: `plugins/agentsmith/skills/agentsmith/references/agent-quality-rubric.md` (document calibration results)

  **Approach:**
  - Fix known structural compliance issues first (gateway-manager `model` field) — these would be caught by pre-commit hook anyway
  - Evaluate all 5 agents and manually rank them by quality (human judgment)
  - Verify scoring produces the same ordinal ranking; accept whatever point spread emerges naturally
  - Adjust weights and thresholds if scores produce counterintuitive rankings
  - Document calibration results and final thresholds in the rubric reference
  - Save calibration baselines for all 5 agents

  **Patterns to follow:**
  - `docs/lessons/skills-evaluation-summary.md` — evaluation-at-scale pattern

  **Test scenarios:**
  - Happy path: 5 agents produce scores matching the manually-determined quality ranking
  - Happy path: agents with comprehensive descriptions + system prompts outscore agents with minimal content
  - Edge case: two agents score identically overall → per-dimension scores still differentiate
  - Integration: scores stable across repeated runs (deterministic scoring)

  **Verification:**
  - Calibration results documented in `agent-quality-rubric.md` with scores for all 5 agents
  - Structural compliance fixes committed (gateway-manager `model` field)
  - Scoring ordinal ranking matches human judgment
  - Dimension weights finalized

- [ ] **Unit 3: `/as-evaluate` and `/as-improve` commands**

  **Goal:** Create slash commands for one-shot evaluation and the full orchestrated improvement loop with delegation to skillsmith and marketplace-manager.

  **Requirements:** R2, R3, R5, R6

  **Dependencies:** Unit 1, Unit 2

  **Files:**
  - Create: `plugins/agentsmith/commands/as-evaluate.md`
  - Create: `plugins/agentsmith/commands/as-improve.md`

  **Approach:**
  - `/as-evaluate` wraps `evaluate_agent.py` invocation with argument handling
  - `/as-improve` orchestrates the full improvement loop:
    - Step 0: Verify target is an agent file; redirect skills → skillsmith, hooks/commands → plugin-dev
    - Step 0a: Source-path resolution (installed cache → source repo via marketplace.json)
    - Step 1: Run `evaluate_agent.py --explain`, report top-3 quality gaps
    - Step 1b: If plugin has skills, run `skillsmith evaluate` on each and report results
    - Step 2: Apply agent improvements; reference `plugin-dev:agent-development` for guidance
    - Step 3: Re-evaluate; compare against baseline; block version bump if overall score regresses
    - Step 4: Update plugin README with `--export-table-row`
    - Step 5: Version bump — PATCH/MINOR/MAJOR in `plugin.json`
    - Step 6: Sync marketplace — delegate to marketplace-manager
    - Note: structural validation is caught by the pre-commit hook when changes are committed

  **Patterns to follow:**
  - `plugins/skillsmith/commands/ss-improve.md` — improvement loop with source-path resolution

  **Test scenarios:**
  - Happy path: `/as-evaluate` on archivist → displays 3 quality dimension scores with overall
  - Happy path: `/as-improve` on source-repo agent → completes all 6 steps, version bumped, marketplace synced
  - Happy path: `/as-improve` on agent whose plugin has skills → skillsmith eval runs on each skill
  - Edge case: installed-cache path → remaps to source repo
  - Edge case: no source mapping → aborts with clear guidance
  - Edge case: regression detected in Step 3 → blocks version bump, reports which dimensions dropped
  - Error path: target is SKILL.md → redirects to skillsmith
  - Error path: nonexistent path → clear error
  - Integration: version cascade → plugin.json bumped AND marketplace.json synced

  **Verification:**
  - Full loop completes and leaves repo in clean state
  - Skillsmith delegation works when plugin has skills
  - Regression detection blocks bad changes

- [ ] **Unit 4: PostToolUse hook for agent auto-evaluation**

  **Goal:** Auto-evaluate agent files on edit, providing immediate quality feedback without blocking the editing workflow.

  **Requirements:** R8

  **Dependencies:** Unit 2 (needs calibrated thresholds)

  **Files:**
  - Create: `plugins/agentsmith/hooks/hooks.json`
  - Create: `plugins/agentsmith/hooks/scripts/on-agent-edit.sh`

  **Approach:**
  - PostToolUse hook matcher: `Write|Edit` events (same broad matcher as skillsmith)
  - Hook script performs fast-path filtering in bash BEFORE invoking Python: check file path contains `/agents/` and file extension is `.md`; exit 0 immediately for non-matching files
  - Skip installed cache paths (`~/.claude/plugins/`)
  - Run `evaluate_agent.py --quick` (agentsmith dimensions only, no plugin-validator delegation)
  - Output one-line score summary to stderr, exit code 2
  - Must complete in under 2 seconds total (bash filter + Python eval)
  - Cumulative with skillsmith's hook: both fire on every Write|Edit, so fast-path exit is critical

  **Patterns to follow:**
  - `plugins/skillsmith/hooks/hooks.json` — hook configuration
  - `plugins/skillsmith/hooks/scripts/on-skill-edit.sh` — PostToolUse pattern with bash fast-path filter

  **Test scenarios:**
  - Happy path: edit an agent `.md` → hook fires, displays score summary
  - Happy path: edit a non-agent file → hook exits in milliseconds (bash filter, no Python)
  - Edge case: edit installed-cache agent → hook skips
  - Error path: `evaluate_agent.py` fails → hook exits cleanly, doesn't block edit

  **Verification:**
  - Hook fires on agent edits and completes in under 2 seconds
  - Non-agent file edits add negligible latency (bash-only exit)

- [ ] **Unit 5: SKILL.md and marketplace registration**

  **Goal:** Write the SKILL.md with proper trigger descriptions, register in marketplace, and update skillsmith's redirect.

  **Requirements:** R1, R2

  **Dependencies:** Units 1-4

  **Files:**
  - Create: `plugins/agentsmith/skills/agentsmith/SKILL.md`
  - Modify: `.claude-plugin/marketplace.json` (add agentsmith entry)
  - Modify: `plugins/agentsmith/README.md` (add initial metrics and v1.0.0 changelog entry)
  - Modify: `plugins/skillsmith/commands/ss-improve.md` (update redirect: agents → agentsmith instead of plugin-dev)

  **Approach:**
  - SKILL.md triggers on: "evaluate my agent", "improve agent quality", "agent metrics", "check agent description", "agent isn't triggering", "validate agent", "as-evaluate", "as-improve"
  - Run `evaluate_skill.py` (skillsmith) on agentsmith's SKILL.md to get baseline metrics — practice what we preach
  - Add agentsmith to `marketplace.json` with `source: "./plugins/agentsmith"`
  - Update skillsmith's `/ss-improve` Step 0 redirect: when target is an agent file, redirect to agentsmith (currently redirects to plugin-dev:agent-development)
  - Record baseline quality scores in README.md with v1.0.0 changelog entry

  **Patterns to follow:**
  - `plugins/skillsmith/skills/skillsmith/SKILL.md` — trigger description pattern
  - `plugins/skillsmith/README.md` — plugin README format

  **Test scenarios:**
  - Happy path: `validate.py` accepts new marketplace entry without errors
  - Happy path: `sync.py` syncs agentsmith version from plugin.json
  - Happy path: `evaluate_skill.py` on agentsmith SKILL.md → scores above 80 overall
  - Happy path: skillsmith strict validation passes on SKILL.md
  - Integration: `/ss-improve` on an agent file → redirects to agentsmith with message
  - Integration: `/as-improve` on a SKILL.md → redirects to skillsmith with message

  **Verification:**
  - `marketplace.json` includes agentsmith with correct source path
  - `validate.py` passes with no errors
  - SKILL.md passes skillsmith strict validation
  - Bidirectional redirects work (ss-improve ↔ as-improve)

## System-Wide Impact

- **Interaction graph:** `/as-improve` orchestrates: `skillsmith` (sibling skill evaluation), `plugin-dev:agent-development` (improvement guidance reference), `marketplace-manager` (version sync). The PostToolUse hook runs `evaluate_agent.py --quick` on file edits. `/ss-improve` updated to redirect agent targets to agentsmith. Structural validation is enforced by marketplace-manager's pre-commit hook at commit time — not invoked during evaluation or improvement.
- **Error propagation:** If any delegated tool fails, `/as-improve` reports which step failed and aborts cleanly. Hook failures exit silently (never block editing).
- **State lifecycle risks:** Source-path resolution is highest risk — incorrect remapping writes to wrong locations. Three-layer defense: correct logic, pre-commit detection, process docs. Baseline file (`.agentsmith-baselines.json`) stored per-plugin in each plugin's source directory, committed to repo.
- **API surface parity:** After agentsmith ships, skillsmith's `/ss-improve` redirects agents to agentsmith (not plugin-dev). Agentsmith's `/as-improve` redirects skills to skillsmith. Bidirectional routing.
- **Unchanged invariants:** Skillsmith's evaluation of skills is not affected. Marketplace-manager's validation, sync, and pre-commit hook workflows are consumed, not modified. Plugin-dev's specs are referenced for guidance, not invoked at runtime. Upstream compliance is enforced at commit time, not reimplemented in agentsmith.

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Quality dimensions don't differentiate agents meaningfully | Unit 2 calibration step against 5 real agents; adjust weights before shipping |
| Source-path resolution fails for edge cases | Reuse skillsmith's proven Step 0a logic |
| False positives in system prompt analysis | Parse frontmatter separately from body; skip code blocks and example blocks (learned from skillsmith lesson) |
| Structural validation rules change upstream | Enforced at commit time by marketplace-manager hook — agentsmith is not affected since it doesn't reimplement or invoke structural checks |
| Hook performance stacking with skillsmith | Bash fast-path filter exits in milliseconds for non-agent files; 2-second target for agent files |
| Regression detection baseline lost | Baseline file committed to source repo; survives across sessions and machines |

## Sources & References

- Related issues: #163 (umbrella), #152 (validation gap), #153 (skillsmith workflow gaps), #160 (agent-native audit)
- Related code: `plugins/skillsmith/` (structural template), `plugin-dev:agent-development` (upstream agent spec reference), `marketplace-manager` pre-commit hook (structural validation at commit time)
- Institutional learnings: `docs/lessons/plugin-integration-and-architecture.md`, `docs/lessons/evaluate-skill-false-positives.md`, `docs/solutions/logic-errors/multi-skill-plugin-version-sync.md`
