---
title: "feat: Add reference provenance tracking and freshness detection"
type: feat
status: active
date: 2026-04-28
---

# feat: Add reference provenance tracking and freshness detection

## Overview

Add a self-improvement capability to skills by tracking where reference content comes from and detecting when it goes stale. This generalizes a production-proven pattern from the prisma-airs plugin into a foundry-level capability that any skill can use. Additionally, support tracking cross-plugin dependencies (e.g., archivist referencing obsidian plugins) so skills that rely on other plugins can detect when new functionality has been added upstream.

---

## Problem Frame

Skills accumulate reference files that derive from external sources — API docs, engineering repos, upstream plugins, Slack channels. Once written, these references become invisible liabilities: there is no mechanism to detect when the upstream source has changed, new features have been added, or content has drifted. This makes staleness invisible until a human manually notices.

The prisma-airs plugin solved this for itself with a domain-specific refresh workflow including provenance frontmatter, a freshness checker script, and a `/refresh-references` command. That pattern should be generalized so any skill — including skills that depend on other Claude Code plugins — can benefit.

---

## Requirements Trace

- R1. Standardize a provenance frontmatter format for reference files in the AgentSkills specification
- R2. Build a generic freshness detection script that works on any skill with provenance-tracked references
- R3. Add a Reference Currency metric to evaluate_skill.py (opt-in, no penalty for skills without provenance)
- R4. Create an `/ss-refresh` command that guides reference updates for any skill
- R5. Support cross-plugin dependency tracking as a source type (skills referencing other plugins)
- R6. Integrate freshness awareness into existing skillsmith workflows (`ss-improve`, `ss-research`, `init_skill.py`)
- R7. Dogfood: add provenance frontmatter to foundry's own references
- R8. Validate against ai-risk-mapper as primary test case — its references track a GitHub repo (cosai-oasis/secure-ai-tooling) with structured YAML/JSON schemas and bundled assets

---

## Scope Boundaries

- Not changing the overall skillsmith evaluation weight distribution (Reference Currency is a sixth dimension that adjusts weights proportionally)
- Not building domain-specific parsers (skills handle those via `custom_checker`)
- Not auto-updating references — freshness detection reports drift; humans decide what to change
- Not requiring provenance on all references — opt-in with graceful neutral scoring

### Deferred to Follow-Up Work

- Custom parser registration via `custom_checker` frontmatter field: separate iteration after core provenance lands
- PostToolUse hook for stale-reference warnings on edit: explore after metrics integration proves useful
- Automated scheduled refresh runs: needs cron/CI infrastructure beyond current scope

---

## Context & Research

### Relevant Code and Patterns

- **prisma-airs prior art**: `refresh_references.py` (492 lines) — production provenance checker with `last_verified`, `sources`, `engineering_sources` frontmatter; supports GitLab, GitHub, Slack, URL probes, and full-audit mode
- **prisma-airs `/refresh-references` command**: 10-step workflow — freshness report → identify gaps → research sources → update references → evaluate → version bump → commit/MR
- **prisma-airs reference frontmatter format**: `last_verified` date, `sources` list (description + URL), `engineering_sources` list (gitlab/github project IDs + paths)
- **evaluate_skill.py**: 3,169 lines, 5 dimensions with configurable weights. `calculate_overall_score()` at line 1114 — weights sum to 1.0. Adding a 6th dimension requires proportional redistribution
- **`init_skill.py`**: 595 lines, 3 templates (minimal/standard/complete). Standard and complete templates create `references/` with placeholder files — good injection point for provenance template
- **`validate_file_references()`** at line 1210: validates orphaned/missing references — can co-locate freshness validation
- **`parse_frontmatter()`** at line 637: already parses YAML frontmatter from SKILL.md — reference files use the same format
- **Hook system**: `on-skill-edit.sh` triggers on SKILL.md writes — reference file edits don't currently trigger hooks

### Institutional Learnings

- **Plugin validation pipeline**: 6-step mandatory pre-commit workflow (version bump → eval → export row → plugin-validator → plugin version → marketplace sync). New scripts must fit this flow
- **Delegation principle**: Each tool retains its identity. `check_freshness.py` should be a standalone tool that `ss-refresh`, `ss-improve`, and `ss-research` orchestrate — not embedded in any of them
- **False positives**: `validate_file_references()` has known false positives with paths in documentation examples. `check_freshness.py` should avoid this pattern
- **Self-referential design**: Skillsmith evaluates itself. Foundry references getting provenance frontmatter (R7) ensures the new metric exercises its own tooling

### ai-risk-mapper as Test Case

The ai-risk-mapper plugin is the ideal validation target because its references exhibit a different pattern from prisma-airs:
- **6 reference files** (1,360 total lines) tracking the CoSAI framework from `cosai-oasis/secure-ai-tooling` GitHub repo
- **Bundled assets** — `assets/cosai-schemas/` contains cached YAML and JSON schema files fetched by `fetch_cosai_schemas.py`
- **Structured upstream data** — references like `schemas_reference.md` and `cosai_overview.md` track specific GitHub repo paths (YAML data files, JSON schema files)
- **Prior manual refresh** — `docs/plans/2026-02-25-feat-cosai-upstream-data-refresh-plan.md` documents a painful manual upstream sync (persona model change, taxonomy fixes, fabricated data cleanup), exactly the kind of drift the provenance system should detect automatically
- **No existing provenance frontmatter** — references cite GitHub URLs in prose but have no structured tracking

This exercises the `github` source type with multiple tracked paths and validates that `check_freshness.py` can handle the pattern where references summarize structured data from a GitHub repo rather than just linking to documentation URLs.

### User Input: Cross-Plugin Dependency Tracking

The user specifically requested that skills referencing other plugins (e.g., archivist referencing obsidian plugins) should be able to detect when those plugins add new features. This maps to a new source type `plugin` in the provenance spec that checks installed plugin versions, changelogs, or marketplace metadata.

---

## Key Technical Decisions

- **Opt-in scoring**: Skills without provenance frontmatter score neutral (100) on Reference Currency, not penalized. This avoids forcing adoption while rewarding skills that track provenance
- **Separate script, not embedded**: `check_freshness.py` is a standalone script in `skillsmith/scripts/`, following the delegation principle. It is not coupled to `evaluate_skill.py` internals
- **`evaluate_skill.py` calls `check_freshness.py`**: The `--check-freshness` flag invokes the script as a subprocess, following the existing pattern where evaluate stays the orchestrator
- **Source-type extensibility**: Four built-in source types (`web`, `github`, `gitlab`, `slack`) plus `plugin` for cross-plugin dependencies. Custom parsers deferred to follow-up
- **GitHub source handles both doc URLs and structured data repos**: The `github` type must work for both simple documentation URLs (like Anthropic's guide) and structured repos with tracked paths containing YAML/JSON data files (like `cosai-oasis/secure-ai-tooling`). Path-level commit tracking is critical for the latter pattern
- **Weight redistribution**: Adding Reference Currency as a 6th dimension. Take weight proportionally from all existing dimensions so their relative importance stays the same (redistribute 0.08 from 5 existing dimensions)
- **Frontmatter compatibility**: Use the same field names as prisma-airs where applicable (`last_verified`, `sources`) for consistency, but make the format more generic (no `engineering_sources` — just `sources` with a `type` discriminator)

---

## Open Questions

### Resolved During Planning

- **Should `check_freshness.py` import `evaluate_skill.py` or vice versa?**: Neither. `check_freshness.py` is standalone. `evaluate_skill.py` calls it as a subprocess when `--check-freshness` is passed, captures structured output, and incorporates the score. This keeps both scripts independently testable and avoids circular dependencies
- **How should cross-plugin dependencies be checked?**: Via the `plugin` source type — checks the installed plugin's `plugin.json` version, compares against a `known_version` in provenance, and optionally reads CHANGELOG.md or README.md for new capabilities
- **What staleness threshold?**: 90 days, matching prisma-airs. Configurable via `--threshold-days` flag

### Deferred to Implementation

- Exact JSON output format from `check_freshness.py` — will be determined when implementing structured output
- How to gracefully degrade when `gh`/`glab` CLI tools are not installed — pattern exists in prisma-airs, adapt as needed
- Whether the `plugin` source type should check marketplace.json or installed plugin paths — implementation will explore both

---

## Output Structure

```
plugins/foundry/skills/skillsmith/
├── scripts/
│   ├── check_freshness.py          (new — generic freshness checker)
│   └── evaluate_skill.py           (modify — add Reference Currency dimension)
├── references/
│   ├── agentskills_specification.md (modify — add provenance spec)
│   └── validation_tools_guide.md   (modify — document Reference Currency metric)
├── SKILL.md                         (modify — reference new content)
plugins/foundry/commands/
│   └── ss-refresh.md                (new — refresh command)
```

---

## Implementation Units

- U1. **Reference Provenance Specification**

**Goal:** Define the standardized optional provenance frontmatter format in the AgentSkills specification.

**Requirements:** R1, R5

**Dependencies:** None

**Files:**
- Modify: `plugins/foundry/skills/skillsmith/references/agentskills_specification.md`

**Approach:**
- Add a new section "Reference Provenance (Optional)" after the existing reference management guidance
- Define frontmatter schema: `last_verified` (date), `sources` list with `type` discriminator
- Supported source types: `web` (URL probe), `github` (repo + paths), `gitlab` (project_id + paths), `slack` (channel_id), `plugin` (plugin name + known_version)
- Include examples for each source type
- Note that provenance is opt-in — references without it are valid

**Patterns to follow:**
- Existing frontmatter documentation style in `agentskills_specification.md`
- prisma-airs reference frontmatter as proven prior art (simplify `engineering_sources` into unified `sources` list)

**Test scenarios:**
- Test expectation: none — specification documentation only

**Verification:**
- The new section is clear enough that a skill author can add provenance frontmatter to a reference without reading any other documentation

---

- U2. **Generic Freshness Detection Script**

**Goal:** Build `check_freshness.py` that scans any skill's references for provenance frontmatter and reports staleness.

**Requirements:** R2, R5

**Dependencies:** U1

**Files:**
- Create: `plugins/foundry/skills/skillsmith/scripts/check_freshness.py`
- Test: manual testing against prisma-airs references and foundry's own references (after U7)

**Approach:**
- PEP 723 inline metadata header (only `pyyaml` dependency, matching prisma-airs pattern)
- Accept skill path as positional argument, default to current directory
- Scan `references/` for files with YAML frontmatter containing `last_verified`
- For each source type, check for activity since `last_verified`:
  - `web`: HTTP HEAD check via curl subprocess, report status code
  - `github`: `gh api repos/{repo}/commits?since={date}&path={path}` — report commit count
  - `gitlab`: `glab api projects/{id}/repository/commits?since={date}&path={path}` — report commit count
  - `slack`: Slack API `conversations.history` via curl with `$SLACK_USER_TOKEN` — report message count
  - `plugin`: Check installed plugin version at `~/.claude/plugins/` against `known_version` in frontmatter; optionally read plugin's CHANGELOG.md or README.md for new entries
- Flags: `--since <date>` override, `--full-audit` mode, `--threshold-days N` (default 90), `--format json` for machine-readable output, `--probe` for URL checks
- Graceful degradation: warn on missing CLI tools, don't fail
- Structured JSON output mode for programmatic consumption by `evaluate_skill.py`

**Patterns to follow:**
- `refresh_references.py` from prisma-airs (492 lines) — `parse_frontmatter()`, `check_engineering_activity()`, `check_url()` patterns
- PEP 723 header style from existing foundry scripts
- `utils.py` for `find_repo_root()` if needed

**Test scenarios:**
- Happy path: scan a skill directory with 3 provenance-tracked references, all within threshold → report "all fresh"
- Happy path: scan a skill with 1 stale reference (last_verified > 90 days ago) → report staleness with source details
- Edge case: reference has `last_verified` but no `sources` → warn, don't crash
- Edge case: reference has `sources` but no `last_verified` → treat as stale (never verified)
- Edge case: `gh`/`glab` not installed → warn per source, report what can be checked
- Edge case: `plugin` source type with plugin not installed → warn, skip
- Happy path: `--format json` outputs valid JSON parseable by `evaluate_skill.py`
- Happy path: `--full-audit` shows all source activity regardless of `last_verified` cutoff

**Verification:**
- Running `uv run check_freshness.py <skill-path>` produces a readable markdown freshness report
- Running with `--format json` produces structured output with per-reference scores

---

- U3. **Reference Currency Metric in evaluate_skill.py**

**Goal:** Add Reference Currency as a sixth evaluation dimension, opt-in with neutral scoring for non-provenance skills.

**Requirements:** R3

**Dependencies:** U2

**Files:**
- Modify: `plugins/foundry/skills/skillsmith/scripts/evaluate_skill.py`

**Approach:**
- Add `calculate_reference_currency_score()` function that:
  - Scans `references/` for files with provenance frontmatter
  - If no references have provenance → return score 100 (neutral, opt-in)
  - If provenance exists → run `check_freshness.py --format json` as subprocess, parse output
  - Score = percentage of tracked references within staleness threshold
- Update `calculate_overall_score()` to accept optional `reference_currency` parameter
- Redistribute weights when Reference Currency is present (6 dimensions):
  - Conciseness: 0.18 (was 0.20)
  - Complexity: 0.18 (was 0.20)
  - Spec Compliance: 0.27 (was 0.30)
  - Progressive Disclosure: 0.18 (was 0.20)
  - Description Quality: 0.09 (was 0.10)
  - Reference Currency: 0.10 (new)
- Add `--check-freshness` flag to CLI argument parser
- When `--check-freshness` is passed OR provenance frontmatter is detected, include Reference Currency in output
- Update `--explain` output to include Reference Currency coaching when applicable
- Update `store_metrics_in_metadata()` to include reference_currency when scored

**Patterns to follow:**
- Existing dimension functions (`calculate_conciseness_score`, etc.) — return dict with `score` and `details` keys
- Existing weight handling in `calculate_overall_score()` at line 1114
- `--explain` output format in `print_explain_output()`

**Test scenarios:**
- Happy path: skill with no provenance references → Reference Currency = 100, overall score unchanged from 5-dimension calculation
- Happy path: skill with all fresh provenance references → Reference Currency = 100
- Happy path: skill with 2/4 stale provenance references → Reference Currency = 50
- Edge case: skill with provenance but `check_freshness.py` not accessible → graceful fallback to neutral (100)
- Happy path: `--explain` output includes Reference Currency coaching with "Why" and "To improve" sections
- Integration: overall score with 6 dimensions matches expected weight redistribution (compare 5-dim and 6-dim results for same skill)

**Verification:**
- `uv run evaluate_skill.py <skill-with-provenance> --check-freshness` reports Reference Currency alongside existing 5 dimensions
- Skills without provenance frontmatter see no change in their scores

---

- U4. **`/ss-refresh` Command**

**Goal:** Create a slash command that guides reference updates for any skill, generalizing prisma-airs's `/refresh-references` workflow.

**Requirements:** R4

**Dependencies:** U2

**Files:**
- Create: `plugins/foundry/commands/ss-refresh.md`

**Approach:**
- Follow the prisma-airs `/refresh-references` command structure (10-step workflow) but make it generic:
  1. Run `check_freshness.py` on target skill (incremental or full-audit mode)
  2. Present freshness report to user
  3. If gaps found, summarize which references need updating and which sources have activity
  4. Ask user for confirmation to proceed
  5. For each stale reference, research upstream sources using the source metadata:
     - `web`: fetch via `defuddle parse --md` or `WebFetch`
     - `github`/`gitlab`: read files via CLI API
     - `slack`: fetch recent messages from channel
     - `plugin`: read upstream plugin's SKILL.md, README, CHANGELOG
  6. Update reference content and `last_verified` date
  7. Update SKILL.md if new capabilities were added
  8. Run skillsmith evaluation — block if score regresses
  9. Version bump (PATCH for content updates, MINOR for new capabilities)
  10. Optionally commit and create branch/PR
- Use `${CLAUDE_PLUGIN_ROOT}` for script paths
- Reference `allowed_tools: Bash, Read, Edit, Write, Glob, Grep, Agent, AskUserQuestion`

**Patterns to follow:**
- prisma-airs `refresh-references.md` command structure
- Existing `ss-improve.md` for foundry command conventions (frontmatter, allowed_tools, step structure)

**Test scenarios:**
- Happy path: run on a skill with stale references → freshness report shows gaps, user confirms, references updated, eval passes
- Happy path: run on a skill with all fresh references → "no gaps detected" message, stops early
- Edge case: run on a skill with no provenance frontmatter → inform user that no references are tracked, suggest adding provenance
- Integration: after refresh, `evaluate_skill.py --check-freshness` shows improved Reference Currency score

**Verification:**
- `/ss-refresh <skill-path>` produces a useful freshness report and can guide a reference update workflow

---

- U5. **Integrate Freshness into `ss-improve` and `ss-research`**

**Goal:** Surface stale references as improvement opportunities in existing skillsmith workflows.

**Requirements:** R6

**Dependencies:** U2, U4

**Files:**
- Modify: `plugins/foundry/commands/ss-improve.md`
- Modify: `plugins/foundry/commands/ss-research.md`

**Approach:**
- **`ss-improve`**: After running `evaluate_skill.py --explain`, check if any references have provenance frontmatter. If stale references exist, add a note: "Reference X hasn't been verified in N days. Run `/ss-refresh` to check for upstream changes." This is informational — don't auto-refresh during improvement
- **`ss-research`**: Include freshness status in the research output. When reporting skill state, run `check_freshness.py` if provenance exists and report findings alongside existing evaluation metrics

**Patterns to follow:**
- Existing `ss-improve.md` step structure — add freshness check after evaluation step
- Existing `ss-research.md` research output format

**Test scenarios:**
- Happy path: `/ss-improve` on a skill with stale references → improvement output includes freshness warning with `/ss-refresh` suggestion
- Happy path: `/ss-research` on a skill with provenance → research output includes freshness status section
- Edge case: skill has no provenance → no freshness-related output (clean absence, not a warning)

**Verification:**
- Running `/ss-improve` or `/ss-research` on a skill with provenance naturally surfaces freshness information without disrupting existing workflows

---

- U6. **Update `init_skill.py` Templates**

**Goal:** Include provenance frontmatter template in scaffolded reference files for standard and complete templates.

**Requirements:** R6

**Dependencies:** U1

**Files:**
- Modify: `plugins/foundry/skills/skillsmith/scripts/init_skill.py`

**Approach:**
- In the `standard` template: add commented-out provenance frontmatter to `references/detailed_guide.md` as an example
- In the `complete` template: add provenance frontmatter to at least one reference file (`references/detailed_guide.md`) with placeholder values
- Include a brief comment in the generated reference explaining what provenance tracking does and linking to the spec

**Patterns to follow:**
- Existing template generation in `init_skill.py` — string templates with placeholder comments

**Test scenarios:**
- Happy path: `init_skill.py --template standard my-skill` creates reference file with commented provenance frontmatter example
- Happy path: `init_skill.py --template complete my-skill` creates reference file with active provenance frontmatter placeholders
- Edge case: `init_skill.py --template minimal my-skill` does not create any provenance content (minimal has no references/)

**Verification:**
- Scaffolded skills from standard/complete templates include provenance awareness in reference files

---

- U7. **Dogfood: Add Provenance to Foundry References**

**Goal:** Add provenance frontmatter to foundry's own reference files as a proof of concept and self-test.

**Requirements:** R7

**Dependencies:** U1

**Files:**
- Modify: `plugins/foundry/skills/skillsmith/references/agentskills_specification.md`
- Modify: `plugins/foundry/skills/skillsmith/references/skill_patterns.md`
- Modify: `plugins/foundry/skills/skillsmith/references/testing_guide.md`

**Approach:**
- Add provenance frontmatter to the 3 references that have known upstream sources:
  - `agentskills_specification.md` → sources: AgentSkills GitHub repo, agentskills.io spec page
  - `skill_patterns.md` → sources: Anthropic's "Complete Guide to Building Skills for Claude" (web URL)
  - `testing_guide.md` → sources: Anthropic's "Complete Guide to Building Skills for Claude" (web URL)
- Set `last_verified` to today's date
- Leave other references (internally-authored) without provenance — they don't track external sources

**Patterns to follow:**
- prisma-airs reference frontmatter (proven format)
- The provenance spec defined in U1

**Test scenarios:**
- Test expectation: none — metadata-only changes to existing reference files
- Integration: after U2 and U3 land, `check_freshness.py` and `evaluate_skill.py --check-freshness` work correctly on foundry's own references

**Verification:**
- Foundry's references with known upstream sources have valid provenance frontmatter
- Running `check_freshness.py` on skillsmith produces a meaningful report

---

- U8. **Document Reference Currency in validation_tools_guide.md**

**Goal:** Document the new metric, `check_freshness.py` usage, and `/ss-refresh` workflow in the validation tools guide.

**Requirements:** R3, R4

**Dependencies:** U2, U3, U4

**Files:**
- Modify: `plugins/foundry/skills/skillsmith/references/validation_tools_guide.md`
- Modify: `plugins/foundry/skills/skillsmith/SKILL.md`

**Approach:**
- Add Reference Currency section to validation_tools_guide.md alongside existing metric documentation:
  - Scoring model (opt-in neutral, proportional reduction for staleness)
  - `check_freshness.py` CLI flags and usage examples
  - `--check-freshness` flag for evaluate_skill.py
  - `/ss-refresh` workflow overview
- Update SKILL.md to contextually reference the new content where appropriate (provenance tracking, freshness checking)

**Patterns to follow:**
- Existing metric documentation sections in `validation_tools_guide.md` (scoring breakdown, flag reference, workflow examples)
- SKILL.md reference mention style ("See `references/validation_tools_guide.md` for details on...")

**Test scenarios:**
- Test expectation: none — documentation only
- Integration: `evaluate_skill.py --validate-references` does not flag the new content as orphaned

**Verification:**
- A skill developer reading the validation tools guide can understand what Reference Currency measures, how to enable it, and how to refresh stale references

---

- U9. **Test Case: Add Provenance to ai-risk-mapper References**

**Goal:** Add provenance frontmatter to ai-risk-mapper's references as the primary validation test case, exercising the `github` source type with structured YAML/JSON upstream data.

**Requirements:** R8

**Dependencies:** U1, U2

**Files:**
- Modify: `plugins/ai-risk-mapper/skills/ai-risk-mapper/references/cosai_overview.md`
- Modify: `plugins/ai-risk-mapper/skills/ai-risk-mapper/references/schemas_reference.md`
- Modify: `plugins/ai-risk-mapper/skills/ai-risk-mapper/references/exploration_guide.md`
- Modify: `plugins/ai-risk-mapper/skills/ai-risk-mapper/references/personas_guide.md`
- Modify: `plugins/ai-risk-mapper/skills/ai-risk-mapper/references/workflow_guide.md`
- Modify: `plugins/ai-risk-mapper/skills/ai-risk-mapper/references/forms.md`

**Approach:**
- Add provenance frontmatter to each reference file that tracks the upstream CoSAI repo:
  - `cosai_overview.md` → `github` source: `cosai-oasis/secure-ai-tooling`, paths: `risk-map/`
  - `schemas_reference.md` → `github` source: `cosai-oasis/secure-ai-tooling`, paths: `risk-map/schemas/`
  - `exploration_guide.md` → `github` source: `cosai-oasis/secure-ai-tooling`, paths: `risk-map/` (risk IDs, persona IDs, framework mappings all derive from upstream YAML)
  - `personas_guide.md` → `github` source: `cosai-oasis/secure-ai-tooling`, paths: `risk-map/personas.yaml`
  - `workflow_guide.md` → internally authored, may reference the CoSAI repo for validation patterns
  - `forms.md` → internally authored, no upstream source (skip provenance or mark as internal)
- Set `last_verified` to today's date for files with actual upstream sources
- Run `check_freshness.py` against the ai-risk-mapper skill to validate it produces a meaningful report
- Compare output against the manual refresh documented in `docs/plans/2026-02-25-feat-cosai-upstream-data-refresh-plan.md` — the provenance system should have detected the same drift signals

**Patterns to follow:**
- The provenance spec defined in U1
- prisma-airs reference frontmatter as format example

**Test scenarios:**
- Happy path: `check_freshness.py plugins/ai-risk-mapper/skills/ai-risk-mapper` scans 6 references, reports freshness status for provenance-tracked files, skips internally-authored files
- Happy path: `--full-audit` mode shows all GitHub commits since `last_verified` for tracked paths in `cosai-oasis/secure-ai-tooling`
- Integration: if upstream CoSAI repo has commits since today, future runs will correctly report drift
- Edge case: references with no upstream source (forms.md) are cleanly skipped, not flagged as errors

**Verification:**
- Running `check_freshness.py` on ai-risk-mapper produces a report that would have detected the persona model change and taxonomy updates documented in the Feb 2026 manual refresh plan
- The provenance format accommodates structured data repos (YAML/JSON files), not just documentation URLs

---

## System-Wide Impact

- **Interaction graph:** `ss-refresh` → `check_freshness.py` → external APIs (GitHub/GitLab/Slack/URL). `evaluate_skill.py --check-freshness` → `check_freshness.py --format json`. `ss-improve` and `ss-research` → `check_freshness.py` (informational). Hook system (`on-skill-edit.sh`) is NOT affected — reference file edits don't trigger it
- **Error propagation:** External API failures (gh/glab not installed, Slack token missing, URL unreachable) should warn per-source and continue, never fail the overall operation. `check_freshness.py` failures in `evaluate_skill.py` should fall back to neutral (100) score
- **State lifecycle risks:** `last_verified` dates in reference frontmatter are the only persistent state. No cache, no database. Risk of drift between actual verification and recorded date is mitigated by updating `last_verified` only through the `/ss-refresh` workflow
- **API surface parity:** The `--check-freshness` flag in `evaluate_skill.py` extends the existing CLI interface. No breaking changes to existing flags or output format. JSON output adds a `reference_currency` key when present
- **Unchanged invariants:** Existing 5-dimension scoring is unchanged for skills without provenance. Weight redistribution only activates when Reference Currency is scored. All existing `evaluate_skill.py` flags continue to work identically

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| External API rate limits (GitHub, GitLab, Slack) | `check_freshness.py` makes minimal API calls (1 per source per reference). Caching is unnecessary at this scale |
| `check_freshness.py` adds latency to `evaluate_skill.py` | Only runs when `--check-freshness` flag is passed or provenance is detected. Subprocess isolation prevents blocking |
| Weight redistribution changes existing scores | Only activates when Reference Currency is scored. Skills without provenance see identical scores. Change is small (0.02 per existing dimension) |
| prisma-airs frontmatter format diverges from generic spec | The generic spec is a superset of prisma-airs format. Existing prisma-airs frontmatter is valid under the new spec with minor field mapping |

---

## Sources & References

- Related issue: #165
- Prior art: `/Users/gregwilliams/Documents/PAN_Projects/AIRS/claude-skills/plugins/prisma-airs/skills/prisma-airs/scripts/refresh_references.py`
- Prior art: `/Users/gregwilliams/Documents/PAN_Projects/AIRS/claude-skills/plugins/prisma-airs/commands/refresh-references.md`
- Existing code: `plugins/foundry/skills/skillsmith/scripts/evaluate_skill.py` (scoring system)
- Existing code: `plugins/foundry/skills/skillsmith/scripts/init_skill.py` (scaffolding)
- Existing spec: `plugins/foundry/skills/skillsmith/references/agentskills_specification.md`
- Test case: `plugins/ai-risk-mapper/skills/ai-risk-mapper/references/` (6 files tracking cosai-oasis/secure-ai-tooling)
- Test case prior refresh: `docs/plans/2026-02-25-feat-cosai-upstream-data-refresh-plan.md` (manual upstream sync that provenance should have caught)
