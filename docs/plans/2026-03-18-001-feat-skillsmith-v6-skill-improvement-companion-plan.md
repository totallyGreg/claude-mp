---
title: "feat: Skillsmith v6 — Skill Improvement Companion"
type: feat
status: completed
date: 2026-03-18
origin: "800 Generated/820 Brainstorms/2026-03-18-skillsmith-v6-evolution-requirements.md"
---

# feat: Skillsmith v6 — Skill Improvement Companion

## Overview

Upgrade skillsmith from a structural validator (v5.x) into the **default companion for skill improvement workflows**. V6 closes three long-standing gaps: metric quality (structural scores only, no usage-driven signal), artifact sprawl (IMPROVEMENT_PLAN.md partially duplicates what a README should provide), and positioning (skillsmith is not the reflexive entry point when a developer edits a skill). This plan implements all seven requirements from the origin document and closes GitHub issues #37 and #24.

**Origin:** [800 Generated/820 Brainstorms/2026-03-18-skillsmith-v6-evolution-requirements.md](../../../Users/totally/Notes/800 Generated/820 Brainstorms/2026-03-18-skillsmith-v6-evolution-requirements.md)

Key decisions carried forward:
- README.md fully replaces IMPROVEMENT_PLAN.md per skill (breaking change → MAJOR version bump)
- All four "always consulted" triggers implemented together
- Plugin-dev skills pulled in at the right loop step, not reproduced
- Transcript replay (not live monitoring) for the observation agent
- Metric improvements land before the observation agent

---

## Problem Statement

1. **Metric quality**: `evaluate_skill.py` (2163 lines) scores are entirely syntactic. Token estimation uses `len(text) // 4` (crude). Progressive Disclosure is the most gameable metric — any reference file >50 lines eliminates the main penalty. Description quality has false positives (trigger verb anywhere in a quoted string counts). Complexity penalizes well-organized skills with 7 short sections over dense ones with 5 long sections. None of the metrics measure LLM effectiveness.

2. **Trigger gap**: Skillsmith is not reflexively consulted when a developer edits a skill. The SKILL.md description doesn't catch "improve my skill" intents. No hook fires on SKILL.md edits. No unified command orchestrates the full improvement loop end-to-end.

3. **Artifact sprawl**: IMPROVEMENT_PLAN.md contains version history and active work, but no prose description of capabilities — making it useful for tracking but not for onboarding or discovery. No skill-level README.md exists anywhere in the repo.

4. **Loop disconnect**: The official `plugin-dev:skill-development` Step 6 "Iterate" loop is the canonical skill improvement pattern but skillsmith doesn't position itself as the entry point for that loop or pull in the right plugin-dev skill at each step.

---

## Proposed Solution

Five sequential phases. Each phase is independently releasable as a MINOR version bump. The MAJOR v6.0.0 bump happens with Phase 2 (README replaces IMPROVEMENT_PLAN.md — breaking for any tooling that reads IMPROVEMENT_PLAN.md).

---

## Technical Approach

### Architecture

```
plugins/skillsmith/
├── .claude-plugin/
│   └── plugin.json               # version authority
├── commands/
│   ├── ss-evaluate.md            # existing (update examples for --explain)
│   ├── ss-init.md                # existing
│   ├── ss-validate.md            # existing
│   ├── ss-research.md            # existing
│   └── ss-improve.md             # NEW: unified improvement loop entry point
├── hooks/                        # NEW directory
│   ├── hooks.json                # NEW: PostToolUse hook registration
│   └── scripts/
│       └── on-skill-edit.sh      # NEW: runs quick eval when SKILL.md edited
├── skills/skillsmith/
│   ├── SKILL.md                  # updated: 6-step loop backbone, new triggers
│   ├── README.md                 # NEW: replaces IMPROVEMENT_PLAN.md
│   ├── references/
│   │   ├── agentskills_specification.md      # unchanged
│   │   ├── form_templates.md                 # unchanged
│   │   ├── improvement_workflow_guide.md     # updated: plugin-dev loop
│   │   ├── integration_guide.md              # updated: marketplace sync
│   │   ├── progressive_disclosure_discipline.md  # unchanged
│   │   ├── python_uv_guide.md                # unchanged
│   │   ├── readme_template.md                # NEW: skill README template
│   │   ├── reference_management_guide.md     # unchanged
│   │   ├── research_guide.md                 # unchanged
│   │   ├── skill_creation_detailed_guide.md  # updated
│   │   └── validation_tools_guide.md         # updated: new flags
│   └── scripts/
│       ├── evaluate_skill.py     # updated: metric fixes + --explain + --update-readme
│       ├── init_skill.py         # updated: README.md + examples/ dir, no IMPROVEMENT_PLAN.md
│       └── utils.py              # unchanged
│       # DELETED: audit_improvements.py, research_skill.py (plugin-dev covers intent/domain),
│       #          update_references.py, validate_workflow.py
└── agents/                       # NEW directory
    └── skill-observer/
        ├── AGENT.md              # transcript-replay observation agent
        └── scripts/
            └── analyze_transcript.py  # session JSON → gap analysis
```

### Implementation Phases

#### Phase 1: evaluate_skill.py Metric Improvements + Issues #37 + #24

**Scope:** Fix five metric weaknesses, implement `--explain` mode (#37), complete script consolidation (#24), add `--update-readme` flag.

**Metric fixes in `evaluate_skill.py`:**

1. **Token estimation** (line 593): Replace `len(text) // 4` with word-count-based approximation: `len(text.split()) * 1.3`. More accurate for English prose without requiring a real tokenizer.

2. **Progressive Disclosure gamability** (lines 836–871): Raise the reference content threshold. Currently `references_lines < 50` triggers a -15 deduction — raise to `references_lines < 100 OR reference_file_count < 2` (both). Also: the +10 bonus for "medium-length skill with references" should require at least one reference file >100 lines (not any file).

3. **Description quality false positives** (lines 874–963): Fix trigger verb detection. Currently regex `"([^"]+)"` matches any quoted string containing a trigger verb anywhere. Change to require the trigger verb to be the **first non-article word** of the quoted phrase (e.g., `"create a hook"` passes, `"do not update"` fails). Also: add negation detection — skip phrases containing "not", "don't", "never" before the verb.

4. **Complexity penalizes scannable structure** (lines 734–787): Instead of penalizing raw H2 count, also consider average section length. If `total_lines / h2_count < 15` (short sections = scannable), apply a 0.8x penalty multiplier to the heading count deduction. This rewards scannable reference tables over dense narrative blobs.

5. **False positive reference warnings** (lines 821–848, `validate_file_references()`): Implement context-aware parsing — skip content inside fenced code blocks (``` ``` ```) and inline backtick spans before checking for deep nested references. This resolves the known lesson in `docs/lessons/evaluate-skill-false-positives.md`.

**--explain mode (#37):** Add `--explain` flag to produce:
- Per-metric block: score, why, specific fixes, estimated improvement, relevant reference file
- Top-3 improvements summary with estimated overall score impact
- Template specified exactly in `plugins/skillsmith/docs/brainstorms/2026-02-16-skillsmith-companion-agent-priorities-brainstorm.md`

**Script consolidation (#24, Phases 2-3):**
- Add `--validate-references` flag (absorbs `update_references.py` validation logic)
- Add `--detect-duplicates` flag (opt-in, absorbs similarity checking)
- Add `--update-readme` flag (generates/updates README.md from current metrics + version history)
- Delete: `audit_improvements.py`, `research_skill.py`, `update_references.py`, `validate_workflow.py`
- Verify nothing in hooks or commands references the deleted scripts before deletion

**ss-evaluate.md command update:** Add `--explain` and `--update-readme` to the Common arguments list and examples.

**Acceptance criteria:**
- [ ] All five metric weaknesses addressed with targeted fixes (not rewrites)
- [ ] `--explain` produces per-metric output and top-3 summary matching the brainstorm spec
- [ ] `--validate-references` and `--detect-duplicates` flags work
- [ ] `--update-readme` generates a valid README.md from current state
- [ ] Four deprecated scripts deleted; nothing breaks
- [ ] Regression baseline: run metrics before and after; conciseness and description quality scores should improve or hold; no other scores regress
- [ ] `uv run` required (not `python3` directly)

**GitHub Issue:** Create new issue for Phase 1 (closes #37 and #24 when merged).

---

#### Phase 2: README.md Migration (R5) — MAJOR version bump to 6.0.0

**Scope:** README.md replaces IMPROVEMENT_PLAN.md as the per-skill artifact. Migrate skillsmith's own skill directory. Update init_skill.py. Create the template.

**README.md format** (per skill directory):

```markdown
# {Skill Name}

{2-4 sentence prose description of what this skill enables and when to use it.
Written for a developer onboarding to the skill — not a trigger description.}

## Capabilities

- {Concrete capability 1}
- {Concrete capability 2}
...

## Current Metrics

| Metric | Score | Interpretation |
|--------|-------|----------------|
| Conciseness | X/100 | {brief interpretation} |
| Complexity | X/100 | {brief interpretation} |
| Spec Compliance | X/100 | {brief interpretation} |
| Progressive Disclosure | X/100 | {brief interpretation} |
| Description Quality | X/100 | {brief interpretation} |
| **Overall** | **X/100** | {brief overall} |

*Last evaluated: YYYY-MM-DD (vX.Y.Z)*

**Metrics authority:** README.md is the human-readable record of metrics. SKILL.md frontmatter `--store-metrics` mode is deprecated — do not write metrics to frontmatter in v6. README.md is written by `--update-readme`; it is the only metrics record. No drift risk between frontmatter and README if frontmatter metrics are not used.

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Desc | Overall |
|---------|------|-------|---------|------|------|------|------|------|---------|
...rows newest-first...

## Active Work

- [#N](link): Description (Status)

## Known Issues

- ...

## Archive

- Git history: `git log --grep="{skill-name}"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:enhancement+is:closed
```

**Migration steps:**
1. Create `references/readme_template.md` with the above format and authoring guidance
2. Update `evaluate_skill.py --update-readme` to produce README.md matching this format (Current Metrics section pulls from live evaluation; Version History section is populated from existing IMPROVEMENT_PLAN.md data on first run, then maintained by `--export-table-row` equivalent flag)
3. Generate `plugins/skillsmith/skills/skillsmith/README.md` using `--update-readme`
4. Migrate the existing version history rows from IMPROVEMENT_PLAN.md into README.md manually (first skill migration is hand-verified)
5. Delete `plugins/skillsmith/skills/skillsmith/IMPROVEMENT_PLAN.md`
6. Update `init_skill.py` for plugin-dev alignment:
   - Generate README.md instead of IMPROVEMENT_PLAN.md for new skills
   - Add `examples/` directory creation alongside `references/` and `scripts/` (plugin-dev Step 3 standard)
   - Note that `research_skill.py` deletion is now doubly justified: plugin-dev:skill-development covers the intent/domain understanding it partially implemented
7. Update all references in SKILL.md, guides, and commands that mention IMPROVEMENT_PLAN.md
8. Update WORKFLOW.md to reflect the README.md pattern

**Automatic migration on improvement:** When `/ss-improve` runs on any skill, it checks for the presence of `IMPROVEMENT_PLAN.md` in that skill's directory. If found and no `README.md` exists, it automatically migrates: copy version history rows, generate prose + metrics sections, write README.md, delete IMPROVEMENT_PLAN.md. This means all skills in the repo migrate naturally as they are improved — no manual bulk migration needed.

**Note on `--export-table-row`:** Keep the existing flag name for backward compat. The row format gains a `Desc` column to capture Description Quality score alongside existing Conc/Comp/Spec/Disc columns.

**Acceptance criteria:**
- [ ] `plugins/skillsmith/skills/skillsmith/README.md` exists and is complete (pilot migration)
- [ ] `plugins/skillsmith/skills/skillsmith/IMPROVEMENT_PLAN.md` is deleted
- [ ] `/ss-improve` detects `IMPROVEMENT_PLAN.md` and auto-migrates it to `README.md` for any skill
- [ ] `init_skill.py` generates README.md (not IMPROVEMENT_PLAN.md) for new skills
- [ ] WORKFLOW.md updated to reflect README.md pattern
- [ ] All internal references to IMPROVEMENT_PLAN.md updated or removed
- [ ] MAJOR version bump: plugin.json → `6.0.0`
- [ ] marketplace.json synced

**GitHub Issue:** Create new issue for Phase 2.

---

#### Phase 3: Plugin-dev Loop Integration + SKILL.md Rewrite (R1 + R4a)

**Scope:** Rewrite SKILL.md to adopt the plugin-dev:skill-development 6-step loop as backbone. Update trigger phrases. Slim the skill body if it exceeds conciseness targets.

**SKILL.md structural changes:**

Replace the current "Skill Creation Process" section with a 6-step loop that explicitly maps to `plugin-dev:skill-development`:

```
Step 1: Understand the Skill → defer to plugin-dev:skill-development Step 1
Step 2: Plan Reusable Contents → defer to plugin-dev:skill-development Step 2
Step 3: Create Structure → defer to plugin-dev:skill-development Step 3
Step 4: Edit SKILL.md → defer to plugin-dev:skill-development Step 4 + skillsmith writing guidance
Step 5: Validate → run evaluate_skill.py (skillsmith's domain)
Step 6: Iterate → this is skillsmith's core loop (Evaluate → Explain → Fix → Re-evaluate)
```

Steps 1–4 reference `plugin-dev:skill-development` directly ("See `plugin-dev:skill-development` for detailed guidance on Step N"). Skillsmith owns Steps 5–6 with full procedural detail.

**Routing table** (add to SKILL.md):

| Task | Route to |
|------|---------|
| Skill anatomy, writing style | `plugin-dev:skill-development` |
| Creating hooks | `plugin-dev:hook-development` |
| Creating agents | `plugin-dev:agent-development` |
| Slash commands | `plugin-dev:command-development` |
| Plugin manifest/structure | `plugin-dev:plugin-structure` |
| Validating, evaluating, improving skills | **skillsmith** (this skill) |
| Syncing versions to marketplace | `marketplace-manager` |

**Trigger phrase additions (R4a):** Update the SKILL.md frontmatter `description` to add:
- `"improve my skill"`, `"update my skill"`, `"skill isn't working"`, `"skill quality"`, `"skill performance"`, `"optimize skill"`, `"fix skill"`, `"iterate on skill"`

Current description already has: create, validate, evaluate, research, analyze, improve, check, init, sync. Add the improvement-specific phrases.

**Acceptance criteria:**
- [ ] SKILL.md uses 6-step loop with plugin-dev references at Steps 1–4
- [ ] Routing table present and accurate
- [ ] Frontmatter description includes improvement-specific trigger phrases
- [ ] SKILL.md body stays ≤300 lines (conciseness target)
- [ ] Evaluate scores after: conciseness ≥ 70, description quality ≥ 90

**GitHub Issue:** Create new issue for Phase 3 (MINOR bump).

---

#### Phase 4: Always-Consulted Trigger Coverage (R4b + R4c + R4d)

**Scope:** PostToolUse hook, CLAUDE.md project instruction, `/ss-improve` unified command.

**R4b — PostToolUse hook on SKILL.md edits:**

Create `plugins/skillsmith/hooks/hooks.json`:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/on-skill-edit.sh"
          }
        ]
      }
    ]
  }
}
```

Create `plugins/skillsmith/hooks/scripts/on-skill-edit.sh`:
- Read `tool_input` JSON from stdin
- Extract `file_path` field
- Check if `file_path` ends in `/SKILL.md`
- If yes: detect if it's a repo source skill (contains `plugins/` or `skills/` in path, NOT `~/.claude/plugins/`)
- If repo source: run `uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/evaluate_skill.py <skill-dir> --quick`
- Output to stderr (exit 2) with format: `[skillsmith] Quick eval: Overall X/100 (Conc:X Comp:X Spec:X Disc:X Desc:X). Run /ss-evaluate for full report.`
- If not a SKILL.md or not a repo source: exit 0 silently

**Important constraints:**
- Only fires on repo source skills (not installed marketplace copies at `~/.claude/plugins/`)
- Must use `$CLAUDE_PLUGIN_ROOT` for portability
- Hook changes require Claude Code restart to take effect (document in README)

**R4c — CLAUDE.md project instruction:**

Add to the project's `.claude/CLAUDE.md` (not `plugin.json` — keeps it visible and auditable in the repo):

```markdown
## Skill Development

When editing any `SKILL.md` file, evaluate current quality state first:
```bash
uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py <skill-dir> --quick
```
Run `/ss-improve <skill-path>` for the full guided improvement loop.
```

**R4d — `/ss-improve` unified command:**

Create `plugins/skillsmith/commands/ss-improve.md`:

```markdown
---
name: ss-improve
description: Guided skill improvement loop — evaluate, explain, fix, sync
argument-hint: [skill-path]
---

Run the full skillsmith improvement loop for a skill:

1. **Evaluate current state**: Run `evaluate_skill.py <skill-path> --explain` to get scores and top-3 improvements
2. **Identify skill type**: Check if it's a skill, agent, or command — route to the appropriate plugin-dev skill for structural guidance if needed
3. **Apply improvements**: Work through the top-3 improvements identified by --explain
4. **Re-evaluate**: Run `evaluate_skill.py <skill-path>` again to confirm improvement
5. **Update README**: Run `evaluate_skill.py <skill-path> --update-readme` to write current metrics and version row
6. **Version bump**: Determine PATCH/MINOR/MAJOR; update plugin.json version
7. **Sync marketplace**: Invoke marketplace-manager to sync marketplace.json

Skill path: `$ARGUMENTS` (required — prompt for it if not provided)
```

**Non-skill artifact handling:** `/ss-improve` only accepts skill directories (`skills/<name>/` containing SKILL.md). If the user targets an agent, hook, or command, output a redirect message:
```
/ss-improve targets skills only. For agents → plugin-dev:agent-development,
for hooks → plugin-dev:hook-development, for commands → plugin-dev:command-development.
```

**Trigger deduplication semantics** (resolves four-trigger noise):
- R4b hook = quick evaluate only (score delta, no --explain); does not re-run if `/ss-improve` ran in the same session
- R4d `/ss-improve` = full evaluate + --explain + improvement loop
- R4a trigger phrases = full evaluate (no --explain unless user asks)
- R4c CLAUDE.md instruction = pre-edit consultation only (does not re-trigger on write)

**Acceptance criteria:**
- [ ] Hook fires on SKILL.md edits and outputs score summary to Claude's context
- [ ] Hook does NOT fire on installed marketplace copies
- [ ] CLAUDE.md project instruction present and correct
- [ ] `/ss-improve` command covers the 7-step loop end-to-end
- [ ] Hook documented in README.md (requires restart after install)

**GitHub Issue:** Create new issue for Phase 4 (MINOR bump).

---

#### Phase 5: Transcript-Replay Observation Agent (R3)

**Scope:** Agent that analyzes a saved conversation transcript to identify where a skill failed to guide Claude effectively and maps installed→source for improvement.

**Research prerequisite (defer to implementation):** The transcript schema at `~/.claude/sessions/*.json` was inaccessible during research (read permission denied). Implementation must begin by investigating the schema — read one session file to understand structure before writing the analysis script.

**Agent: `plugins/skillsmith/agents/skill-observer/AGENT.md`**

Agent type: subagent, invoked on demand via `/skill-observer` or from `/ss-improve` as an optional step.

**MVP scope (constrained):** The agent uses only structurally detectable signals from the session JSON — it does NOT attempt open-ended NLP gap detection. Hedging language analysis and "I'll assume..." detection are out of scope for MVP; those require LLM-based analysis and are a future iteration.

**MVP workflow:**
1. Accept a session ID or session file path as input
2. Read the session JSON from `~/.claude/sessions/<id>.json` (investigate schema first — see Research Prerequisite above)
3. Extract the list of skills that were loaded during the session (from skill-trigger events in the JSON, if present)
4. For each skill loaded: find all tool calls and assistant turns that occurred while the skill was active
5. Identify structural gaps: steps where Claude called tools or generated content not referenced in the skill's SKILL.md (e.g., read a file the skill doesn't mention, used a pattern the skill's references don't cover)
6. Map each gap to a skill: match skill name → installed path → source path in repo
7. Return: list of gaps with (skill, tool/action not covered by skill, suggested SKILL.md or reference addition)

**Out of scope for MVP:** Natural language hedging detection ("I'll assume...", "based on my general knowledge..."), semantic similarity analysis, and cross-session trend analysis. These are follow-on iterations once the structural approach is validated.

**Installed→source path resolution:**

```python
# Pattern:
# installed: ~/.claude/plugins/marketplaces/<marketplace>/<plugin>/<version>/skills/<skill>/
# source:    plugins/<plugin>/skills/<skill>/

def resolve_installed_to_source(installed_path: str, repo_root: str) -> str | None:
    # Parse the installed path to extract plugin name and skill name
    # Look up plugin name in marketplace.json to find local source entry
    # Return source path if found, None if third-party (no local source)
```

**Script: `plugins/skillsmith/agents/skill-observer/scripts/analyze_transcript.py`**

PEP 723 inline metadata, `uv run` invocation. Accepts `--session <id|path>` and `--skill <name>` (optional filter). Returns structured gap analysis as JSON or markdown.

**Note on script consolidation target:** The consolidation target (`evaluate_skill.py + init_skill.py + utils.py only`) applies to `plugins/skillsmith/skills/skillsmith/scripts/` only. `analyze_transcript.py` lives in the agent's own directory (`agents/skill-observer/scripts/`) and does not conflict with the consolidation target.

**Edge cases to handle (from SpecFlow analysis):**
- Session has no skill invocations → report "no skills detected, cannot analyze"
- Multiple skills active in session → report gaps per-skill, ranked separately
- Skill is third-party (no source in repo) → report gap but note "no local source found, cannot apply improvements"
- Session file unreadable → surface clear error with `chmod` guidance

**Acceptance criteria:**
- [ ] Agent can read and parse `~/.claude/sessions/*.json` (schema investigated first)
- [ ] Installed→source resolution works for all skills in this repo
- [ ] Gap analysis returns ranked list with skill mapping
- [ ] Third-party skills handled gracefully (gap reported, no source path)
- [ ] Agent invocable from `/ss-improve` as optional "analyze recent session" step

**GitHub Issue:** Create new issue for Phase 5 (MINOR bump).

---

#### Phase 6: Self-Application (Closes the Loop)

**Scope:** Apply all Phase 1–5 improvements to skillsmith's own SKILL.md. Final version bump to 6.x. Marketplace sync.

**Tasks:**
1. Run `uv run evaluate_skill.py plugins/skillsmith/skills/skillsmith --explain` with Phase 1 improvements applied
2. Apply any remaining low-hanging improvements identified
3. Run `evaluate_skill.py --update-readme` to populate README.md with final scores
4. Verify README.md is complete and accurate
5. Update `plugin.json` version to match the cumulative phase bumps
6. Run marketplace sync (pre-commit hook handles this automatically, or run `/mp-sync`)
7. Two-commit release: logic changes commit + version/README/marketplace commit

**Target scores after self-application:**
- Conciseness: ≥ 70 (up from 55)
- Complexity: ≥ 77 (hold)
- Spec Compliance: 100 (hold)
- Progressive Disclosure: 100 (hold)
- Description Quality: ≥ 95 (up from implied ~86)
- Overall: ≥ 90 (up from 86)

---

## Alternative Approaches Considered

### Alternative to transcript replay: Live observation hook
Rejected. A PostToolUse hook that watches all Claude tool calls in real-time and infers skill gaps is high complexity and fires constantly. Transcript replay is selective (user chooses which session to analyze), lower noise, and doesn't require a persistent observer.

### Alternative to per-skill README: Plugin-root README
Rejected per origin document decision. A plugin-root README covers all skills in aggregate (like terminal-guru's README) but is the wrong granularity — the goal is per-skill human-readable documentation that travels with the SKILL.md in the same directory, replacing IMPROVEMENT_PLAN.md.

### Alternative to four triggers: Pick one
Considered. The four triggers are complementary, not redundant: trigger phrases catch intent-based requests, the hook catches edit-time feedback, the CLAUDE.md rule catches habit-formation, and /ss-improve provides the full guided loop. The cost of maintaining all four is low.

---

## System-Wide Impact

### Interaction Graph

`/ss-improve` → `evaluate_skill.py --explain` → score output → plugin-dev:skill-development (if structural guidance needed) → SKILL.md edits → PostToolUse hook fires → `evaluate_skill.py --quick` → score delta → `evaluate_skill.py --update-readme` → README.md written → `plugin.json` version bump → pre-commit hook → `detect_version_changes.py` → `sync_marketplace_versions.py` → `marketplace.json` staged.

**Marketplace write ownership:** The pre-commit hook is the sole writer of `marketplace.json`. Skillsmith's `/ss-improve` step 7 ("Sync marketplace") triggers marketplace-manager as a preview/validation step, not a write step. The pre-commit hook is idempotent and always wins. This eliminates the double-write risk between skillsmith and the hook.

### Error & Failure Propagation

- `evaluate_skill.py` exits 1 on validation errors, 0 on success. The PostToolUse hook uses exit 2 to feed stderr to Claude. If the evaluation fails (malformed SKILL.md), the hook output makes the error visible.
- `analyze_transcript.py` should never block the improvement workflow — it's advisory. Errors should surface as warnings, not failures.
- If `--update-readme` fails (e.g., README.md write permission issue), the failure should be surfaced before the version bump, not after.

### State Lifecycle Risks

- **IMPROVEMENT_PLAN.md deletion**: Once deleted and README.md generated, the version history is in README.md only. If README.md is accidentally deleted, history is gone (git history remains). This is a deliberate trade-off — note it in the migration guide.
- **Hook side effects**: The PostToolUse hook runs `evaluate_skill.py --quick` on every SKILL.md write. For large skills, this adds latency. The `--quick` flag keeps it fast (structure-only, no full metrics).
- **Installed→source mismatch**: If a plugin is renamed or moved in the repo, the installed→source resolution in the observer agent will fail silently. Document this as a known limitation.

### API Surface Parity

- `ss-evaluate.md` command: update to show `--explain` and `--update-readme` flags
- `ss-validate.md` command: no change needed
- `ss-improve.md` command: new, covers the full loop
- `evaluate_skill.py`: gains `--explain`, `--validate-references`, `--detect-duplicates`, `--update-readme` flags
- `init_skill.py`: generates README.md instead of IMPROVEMENT_PLAN.md

### Integration Test Scenarios

1. Edit a SKILL.md → hook fires → score delta appears in Claude's context
2. Run `/ss-improve plugins/skillsmith/skills/skillsmith` → full loop completes → README.md updated → marketplace synced
3. Run `analyze_transcript.py --session <id>` on a session with no skills → graceful "no skills detected" output
4. Create new skill with `init_skill.py` → README.md generated (no IMPROVEMENT_PLAN.md)
5. Commit a SKILL.md change without version bump → pre-commit hook auto-syncs marketplace.json

---

## Acceptance Criteria

### Functional Requirements

- [ ] R1: SKILL.md adopts plugin-dev 6-step loop; routes to plugin-dev skills for Steps 1–4
- [ ] R2: All five metric weaknesses fixed; `--explain` mode produces per-metric + top-3 summary
- [ ] R3: Transcript-replay agent returns ranked gap list with installed→source mapping
- [ ] R4a: SKILL.md description triggers on "improve my skill", "skill isn't working", "skill quality"
- [ ] R4b: PostToolUse hook fires on SKILL.md edits; outputs score to Claude's context
- [ ] R4c: CLAUDE.md project instruction guides skill-edit behavior
- [ ] R4d: `/ss-improve` command covers 7-step improvement loop end-to-end
- [ ] R5: README.md present for skillsmith's own skill; IMPROVEMENT_PLAN.md deleted
- [ ] R5: `/ss-improve` auto-migrates IMPROVEMENT_PLAN.md → README.md for any skill it touches
- [ ] R5: `init_skill.py` generates README.md for new skills
- [ ] R5: `--update-readme` flag updates README.md with current metrics + new version row
- [ ] R6: marketplace-manager invoked as part of `/ss-improve` workflow

### Non-Functional Requirements

- [ ] `evaluate_skill.py` stays ≤ 2500 lines after new flags (no bloat)
- [ ] Hook runs in < 5 seconds for any skill (--quick is fast)
- [ ] All scripts remain PEP 723 compliant, invoked via `uv run`
- [ ] No `python3` direct invocation anywhere

### Quality Gates

- [ ] Run baseline scores before Phase 1 changes; record in README.md v5.x row
- [ ] Run scores after Phase 1 changes; confirm improvement or hold on all metrics
- [ ] Two-commit strategy followed for each phase: logic changes commit + release commit
- [ ] GitHub Issue created for each phase; closed via `Closes #N` in release commit message

---

## Success Metrics

- Overall skillsmith score ≥ 90 (was 86 at v5.2.0)
- Conciseness score ≥ 70 (was 55 — biggest gap due to SKILL.md length)
- Description quality score ≥ 95 (improved trigger phrases + false positive fix)
- `/ss-improve` runs end-to-end without requiring manual marketplace sync
- PostToolUse hook fires correctly on first SKILL.md edit after install

---

## Dependencies & Prerequisites

- Issues #37 and #24 are subsumed by Phase 1 — do not implement them independently
- Phase 2 (README migration) depends on Phase 1 (`--update-readme` flag)
- Phase 3 (SKILL.md rewrite) can proceed in parallel with Phase 2
- Phase 4 (triggers) depends on Phase 1 (`--explain` in `/ss-improve`)
- Phase 5 (observation agent) is independent but benefits from Phase 1 metric improvements for gap scoring
- Phase 6 (self-application) depends on all prior phases

---

## Risk Analysis & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Transcript schema unknown | High | Medium | Investigate first in Phase 5 before committing to agent design |
| Hook path-filtering complexity | Medium | Low | Test with a temp SKILL.md edit before releasing |
| README migration loses version history | Low | High | Manually verify first migration (skillsmith's own) before automating |
| `evaluate_skill.py` grows too large | Medium | Low | Target ≤ 2500 lines; extract helpers to `utils.py` if needed |
| Metric "improvements" change existing scores | Medium | Medium | Record baseline before Phase 1; any regression is a bug |

---

## Future Considerations

- **Synthetic testing agent** (R3 alternative): once the transcript-replay agent is validated, a synthetic test harness that runs a skill against standardized prompts and scores the output is a natural next step
- **Per-metric learning over time**: tracking metric scores per version in README.md creates a longitudinal dataset — future tooling could trend-analyze regression across the repo
- **README.md migration automation**: a `migrate_improvement_plan.py` script that converts IMPROVEMENT_PLAN.md to README.md format for bulk migration across all skills

---

## Sources & References

### Origin

- **Origin document:** `800 Generated/820 Brainstorms/2026-03-18-skillsmith-v6-evolution-requirements.md`
  Key decisions carried forward: README replaces IMPROVEMENT_PLAN.md (MAJOR bump), all four triggers together, transcript replay for observation agent, plugin-dev defers not duplicates, metric fixes before observation agent

### Internal References

- evaluate_skill.py scoring logic: `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py:684–963`
- Crude token estimation: `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py:593`
- False positive reference warnings: `docs/lessons/evaluate-skill-false-positives.md`
- Multi-skill version sync bug lesson: `docs/solutions/logic-errors/multi-skill-plugin-version-sync.md`
- Script consolidation brainstorm: `plugins/skillsmith/docs/brainstorms/2026-02-16-skillsmith-companion-agent-priorities-brainstorm.md`
- Plugin-root README model: `plugins/terminal-guru/README.md`
- Workflow conventions: `WORKFLOW.md:83–113` (IMPROVEMENT_PLAN.md format), `:174–226` (issue closing checklist)
- Hook patterns: `plugin-dev:hook-development` (installed marketplace skill)
- plugin-dev 6-step loop: `plugin-dev:skill-development` (installed marketplace skill)
- Session storage: `~/.claude/sessions/*.json` (schema unknown — investigate in Phase 5)

### Related Work

- Open issue #37: `--explain` mode (subsumed by Phase 1)
- Open issue #24: script consolidation phases 2–3 (subsumed by Phase 1)
- Closed issue #32: "When NOT to use" section (v5.1.0 — complete)
