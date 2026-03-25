---
title: "feat(skillsmith): Align skill guidance with Anthropic's Complete Guide to Building Skills"
type: feat
status: active
date: 2026-03-24
origin: https://github.com/totallyGreg/claude-mp/issues/146
---

# feat(skillsmith): Align skill guidance with Anthropic's Complete Guide to Building Skills

## Overview

Issue #146 identified 8 gaps between the current skillsmith plugin and Anthropic's published "Complete Guide to Building Skills for Claude." This plan addresses all 8 gaps through a combination of reference document additions and evaluator script enhancements.

## Problem Frame

The skillsmith plugin guides skill authors through creation, evaluation, and improvement — but it predates Anthropic's official guide. Several canonical patterns (use-case definition, description formula, negative triggers, body structure, proven patterns, testing methodology, and diagnostic signals) are absent or incomplete. Aligning with the official guide improves skill quality and makes skillsmith authoritative rather than supplemental.

## Requirements Trace

- R1. Add pre-writing use-case definition template (High priority)
- R2. Add description formula with good/bad examples (High priority)
- R3. Add negative trigger presence detection in evaluator (High priority)
- R4. Add SKILL.md recommended body structure template (High priority)
- R5. Create 5 proven skill patterns reference document (Medium priority)
- R6. Add 3-area testing methodology reference (Medium priority)
- R7. Surface over/undertriggering signals in `--explain` output (Medium priority)
- R8. Document README.md divergence from guide as intentional (Low priority)

## Scope Boundaries

- Does not re-implement the description formula trigger-verb fix shipped in the completed v6 plan (`2026-03-18-001`); this plan adds formula documentation and bad-example coaching that builds on the already-fixed evaluator
- Does not re-address closed issues #82 (orphan detection), #96 (qualitative conciseness), #37 (--explain mode), or #24 (script consolidation) — those are closed; plan references to their prior work are for context only
- Does not implement behavioral triggering tests (whether Claude actually fires the skill) — classified as manual per existing `validation_tools_guide.md`
- Does not modify the complexity metric penalty for scannable structure (tracked separately in v6 plan); body structure templates authored here should use fewer, denser sections until that fix lands

## Context & Research

### Relevant Code and Patterns

- `plugins/skillsmith/skills/skillsmith/references/form_templates.md` — existing Skill Proposal, Improvement Request, Research Analysis forms; Gap 1 adds here
- `plugins/skillsmith/skills/skillsmith/references/skill_creation_detailed_guide.md` — Step 4–6 deep dive; Gaps 2, 4, 6 add here
- `plugins/skillsmith/skills/skillsmith/references/agentskills_specification.md` — official spec with six-section recommended body structure; Gap 8 adds here
- `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py` — `validate_description_quality()` scores trigger phrases, third-person, specificity, length; `--explain` generates per-metric coaching; Gaps 3 and 7 modify here
- `plugins/skillsmith/skills/skillsmith/scripts/init_skill.py` — standard template includes deletable `## Structuring This Skill` section with four structural patterns; Gap 4 reconciles this with the guide's four-section body structure; Gap 5 promotes the four patterns to a permanent reference
- `plugins/skillsmith/skills/skillsmith/references/validation_tools_guide.md` — documents all `evaluate_skill.py` flags; Gap 7 documentation lands here too

### Institutional Learnings

- **Complexity metric penalizes scannable structure** (`docs/plans/2026-03-18-001`): penalizes raw H2 count, so body structure templates (Gap 4) should use fewer, larger sections until the complexity metric fix lands. Note this constraint explicitly in Gap 4 template guidance.
- **v6 description quality fix (completed)** (`docs/plans/2026-03-18-001`): the trigger-verb-first-word fix shipped in v6. The description formula documentation in this plan builds on the now-correct evaluator behavior.
- **Evaluate_skill.py false positives** (`docs/lessons/evaluate-skill-false-positives.md`): `validate_file_references()` fires on example paths in code blocks. Gap 7's `--explain` changes must not introduce new false positives from code-block content.
- **Orphan detection** (issue #82, closed): both code paths are fixed and `check_qualitative_conciseness()` is implemented. When touching `evaluate_skill.py` for Gaps 3/7, avoid unintentional side effects to these functions.
- **Qualitative conciseness** (issue #96, closed): `check_qualitative_conciseness()` is live at line 713. Gap 7's --explain additions should sit alongside, not inside, this existing function.

### External References

- Anthropic's "Complete Guide to Building Skills for Claude" (referenced in issue #146): canonical source for all 8 gaps — use-case format, description formula, negative triggers, body structure, 5 patterns, testing areas, trigger diagnostics, README guidance

## Key Technical Decisions

- **Gap 3 scope clarification**: The issue requests detecting `"Do NOT use for X (use Y instead)"` clauses as a *positive* best-practice signal. This is distinct from the v6 fix (filtering negation words from trigger counting). Implement as a bonus coaching item in `--explain` Description Quality, not as a scored deduction.
- **Gap 5 pattern set**: Use the Anthropic guide's 5 patterns (Sequential workflow orchestration, Multi-MCP coordination, Iterative refinement, Context-aware tool selection, Domain-specific intelligence) rather than the init_skill.py scaffold's 4 structural patterns. The scaffold's 4 patterns describe body *structure*; the guide's 5 patterns describe runtime *behavior* — complementary, not duplicates. Keep both; promote the guide's 5 to a reference file.
- **Gap 6 scope**: Testing methodology belongs in a new `references/testing_guide.md` rather than growing `skill_creation_detailed_guide.md` further. The guide's 3 areas (triggering, functional, performance) map cleanly to manual, automated, and benchmark categories.
- **Gap 7 implementation**: Add two diagnostic signals to the Description Quality `--explain` block: (a) undertrigger signal when trigger phrase count < 2 or all phrases ≤ 2 words, (b) overtrigger signal when trigger phrase count ≥ 8 or all phrases contain common generic verbs with no noun specificity. Do not implement cross-skill overlap detection (requires runtime graph, deferred).
- **Evaluation before and after**: Run `evaluate_skill.py` on skillsmith's own skill directory before committing any evaluator change and record the baseline. Re-run after each evaluator change. Record both in the skill README.md version history.

## Open Questions

### Resolved During Planning

- **Can Gap 7 detect cross-skill overtriggering?**: No — that requires a runtime skill graph not available at static analysis time. Deferred to a future enhancement. Gap 7 scopes to within-description signals only.
- **Should the 5 Anthropic patterns replace the 4 scaffold patterns?**: No — they are complementary (behavioral vs. structural). Keep the scaffold's 4 patterns as init_skill.py guidance; create a separate reference for the 5 runtime patterns.
- **Should Gap 2 description formula wait for v6 Phase 1 regex fix?**: No — document the formula first (this plan); the regex fix lands independently. Authors can apply the formula immediately; the evaluator will score it more accurately once the fix lands.

### Deferred to Implementation

- Exact scoring weight or bonus points for negative trigger presence (Gap 3) — implementer should check whether adding a scored component vs. coaching-only in `--explain` breaks existing test expectations in `tests/test_evaluate_skill.py`
- Specific wording of the overtrigger/undertrigger signals (Gap 7) — depends on reading the current `--explain` output format closely to match tone and structure

## Implementation Units

- [ ] **Unit 1: Add use-case definition template to form_templates.md**

  **Goal:** Surface the guide's canonical use-case format as a pre-writing exercise before authors scaffold a skill.

  **Requirements:** R1

  **Dependencies:** None

  **Files:**
  - Modify: `plugins/skillsmith/skills/skillsmith/references/form_templates.md`
  - Modify: `plugins/skillsmith/commands/ss-init.md` (reference the template as step 0)

  **Approach:**
  - Add a new form section "Use-Case Definition" before the Skill Proposal form
  - Template should elicit: the concrete user trigger phrase, the problem without the skill, required tools/MCP, success outcome
  - Frame it as a pre-scaffolding exercise ("Before running `/ss-init`, fill out this form")
  - Update `ss-init.md` command to reference this form in its preamble

  **Patterns to follow:**
  - Existing Skill Proposal form structure in `form_templates.md`
  - Guide's canonical format: `Use Case: [name] / Trigger: User says "[phrase]" / Steps: 1... 2... 3... / Result: [outcome]`

  **Test scenarios:**
  - A new skill author filling out the form should produce enough signal to write a specific, accurate description
  - The form should prompt for at least one concrete trigger phrase (feeds directly into Gap 2 formula)

  **Verification:**
  - Form section is present and coherent in `form_templates.md`
  - `ss-init.md` references the pre-writing form

- [ ] **Unit 2: Add description formula with good/bad examples to skill_creation_detailed_guide.md**

  **Goal:** Give authors a composable formula for descriptions with concrete examples of what fails.

  **Requirements:** R2

  **Dependencies:** None (v6 evaluator fix already shipped — formula docs build on current evaluator behavior)

  **Files:**
  - Modify: `plugins/skillsmith/skills/skillsmith/references/skill_creation_detailed_guide.md`

  **Approach:**
  - Add a "Description Formula" subsection within the existing description/writing guidance
  - Formula: `[What it does] + [When to use it] + [Key capabilities]`
  - Include the 3 bad examples from the guide: "Helps with projects" (too vague), "Creates sophisticated multi-page documentation systems" (missing trigger), "Implements the Project entity model" (too technical, no user trigger)
  - Add 1 good example contrasting against each bad example
  - Note that the evaluator's trigger-phrase scoring rewards formula-compliant descriptions

  **Patterns to follow:**
  - `skill_creation_detailed_guide.md` existing writing style — concise bullets, not prose paragraphs

  **Test scenarios:**
  - An author reading the guide can distinguish the bad examples from the good on first read
  - The formula maps unambiguously to the three scoring components in `validate_description_quality()`

  **Verification:**
  - Formula section present with at least 3 bad/good pairs
  - Internally consistent with the trigger-phrase scoring logic in `evaluate_skill.py`

- [ ] **Unit 3: Add negative trigger presence detection to evaluate_skill.py**

  **Goal:** Coach authors to add "Do NOT use for X (use Y skill instead)" clauses to prevent overtriggering.

  **Requirements:** R3

  **Dependencies:** None (distinct from v6 Phase 1 negation-word regex fix)

  **Files:**
  - Modify: `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py`
  - Modify: `plugins/skillsmith/skills/skillsmith/tests/test_evaluate_skill.py`

  **Approach:**
  - In `validate_description_quality()`, detect presence of "do not use", "not for", "when not to", "avoid when", "instead use" patterns (case-insensitive) in the description
  - Surface as a coaching item in `--explain` Description Quality block: if absent, suggest adding a negative trigger clause; if present, affirm as best practice
  - Implement as coaching-only (not a scored component) to avoid breaking test expectations — verify against `tests/test_evaluate_skill.py` before deciding to add scoring
  - Add to the "To improve" suggestions under Description Quality in `--explain` output

  **Patterns to follow:**
  - Existing `--explain` Description Quality coaching block structure in `evaluate_skill.py`
  - `_is_valid_trigger_phrase()` function style for pattern detection

  **Test scenarios:**
  - Description with "Do NOT use for general coding help (use code-review instead)" → detected as present, affirmed
  - Description with no negative trigger clause → detected as absent, coaching suggestion emitted
  - Description with "never recommend" (negation in a different context) → should not false-positive

  **Verification:**
  - `--explain` output for a skill without negative triggers includes a coaching suggestion
  - `--explain` output for a skill with "Do NOT use for X" affirms the pattern
  - Existing test suite passes unchanged (or new tests added, old tests not broken)

- [ ] **Unit 4: Add SKILL.md recommended body structure template to skill_creation_detailed_guide.md**

  **Goal:** Give authors the guide's canonical four-section body structure with an implementation note about the current complexity metric constraint.

  **Requirements:** R4

  **Dependencies:** None (complexity metric fix deferred; note constraint explicitly)

  **Files:**
  - Modify: `plugins/skillsmith/skills/skillsmith/references/skill_creation_detailed_guide.md`
  - Modify: `plugins/skillsmith/skills/skillsmith/references/agentskills_specification.md` (reconcile six-section spec with four-section guide)

  **Approach:**
  - Add a "Recommended Body Structure" section to `skill_creation_detailed_guide.md`
  - Canonical four sections: **Instructions** (overview + when to use) → **Steps** (numbered workflow) → **Examples** (concrete input/output pairs) → **Troubleshooting** (common failures + fixes)
  - Also include guide's `## Important` / `## Critical` header recommendation for key instructions
  - Add implementation note: "Until the complexity metric penalty for scannable structure is fixed (tracked in v6 plan), prefer 3-5 sections with ≥15 lines each over 7+ shorter sections to avoid score penalty"
  - In `agentskills_specification.md`, reconcile the six-section spec (Purpose / When to use / Steps / Examples / Edge case handling / Resource references) with the four-section guide — note that both are valid; the guide's four-section format is optimized for Claude consumption, the six-section spec is optimized for spec compliance

  **Patterns to follow:**
  - `agentskills_specification.md` existing reconciliation/rationale style

  **Test scenarios:**
  - An author using the four-section template for a new skill should not score below 40/50 on complexity
  - The reconciliation note in `agentskills_specification.md` should make clear which to follow and when

  **Verification:**
  - Body structure section present in `skill_creation_detailed_guide.md` with all four sections and the `## Important` / `## Critical` guidance
  - Reconciliation note present in `agentskills_specification.md`

- [ ] **Unit 5: Create references/skill_patterns.md with 5 proven skill patterns**

  **Goal:** Document the Anthropic guide's 5 runtime behavioral patterns as a durable reference.

  **Requirements:** R5

  **Dependencies:** None

  **Files:**
  - Create: `plugins/skillsmith/skills/skillsmith/references/skill_patterns.md`
  - Modify: `plugins/skillsmith/skills/skillsmith/SKILL.md` (link to new reference in Resources section)

  **Approach:**
  - Document all 5 patterns: Sequential workflow orchestration, Multi-MCP coordination, Iterative refinement, Context-aware tool selection, Domain-specific intelligence
  - For each pattern: name, when to use, structural characteristics, example trigger scenario, and a cross-reference to a real skill in the repo if one exists
  - Frame as complementary to the 4 structural patterns in `init_skill.py` scaffold (behavioral vs. structural)
  - Add note distinguishing these behavioral patterns from the scaffold's 4 structural patterns

  **Patterns to follow:**
  - `references/progressive_disclosure_discipline.md` format — named patterns with when-to-apply guidance

  **Test scenarios:**
  - An author building a skill that orchestrates multiple MCP servers can identify "Multi-MCP coordination" as their pattern and understand what makes the skill successful
  - The reference should be discoverable via `--explain` or direct reference

  **Verification:**
  - File exists with all 5 patterns
  - Each pattern has: name, when to use, structural signal, example trigger
  - SKILL.md Resources section links to `references/skill_patterns.md`

- [ ] **Unit 6: Add testing methodology reference**

  **Goal:** Give authors concrete guidance on the 3 testing areas with measurable targets from the guide.

  **Requirements:** R6

  **Dependencies:** None

  **Files:**
  - Create: `plugins/skillsmith/skills/skillsmith/references/testing_guide.md`
  - Modify: `plugins/skillsmith/skills/skillsmith/references/validation_tools_guide.md` (link to new testing guide from manual validation section)
  - Modify: `plugins/skillsmith/skills/skillsmith/SKILL.md` (link to new reference)

  **Approach:**
  - Document 3 testing areas with guide-specified targets:
    - **Triggering tests**: 90% trigger rate on relevant queries — how to manually construct test queries, what pass/fail looks like
    - **Functional tests**: valid outputs, 0 failed API/tool calls — tie to `--validate-functionality` as the automated portion
    - **Performance tests**: token/message counts with vs. without skill — how to measure context budget impact
  - Frame `--validate-functionality` as the automated subset of functional testing; manual testing covers the rest
  - Note which areas correspond to existing `[MANUAL]` markers in `validation_tools_guide.md`

  **Patterns to follow:**
  - `validation_tools_guide.md` structure — clear section per testing area with practical instructions

  **Test scenarios:**
  - An author completing a new skill can run all 3 testing areas using this guide as the only reference
  - The guide clearly distinguishes automated checks (what `evaluate_skill.py` covers) from manual checks

  **Verification:**
  - File exists with all 3 testing areas, measurable targets, and instructions
  - `validation_tools_guide.md` links to it from the manual validation section

- [ ] **Unit 7: Surface over/undertriggering diagnostic signals in `--explain`**

  **Goal:** Help authors distinguish overtriggering (too broad) from undertriggering (too narrow/sparse) with actionable coaching.

  **Requirements:** R7

  **Dependencies:** Unit 3 (shares --explain Description Quality modification; implement in same editing pass to avoid conflicts)

  **Files:**
  - Modify: `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py`
  - Modify: `plugins/skillsmith/skills/skillsmith/tests/test_evaluate_skill.py`
  - Modify: `plugins/skillsmith/skills/skillsmith/references/validation_tools_guide.md` (document new signals)

  **Approach:**
  - In the Description Quality `--explain` block, add two diagnostic signals after existing trigger-phrase analysis:
    - **Undertrigger signal**: emit when trigger phrase count < 2 OR all phrases are ≤ 2 words long → suggest adding more specific trigger phrases or expanding narrow phrases
    - **Overtrigger signal**: emit when trigger phrase count ≥ 8 OR description lacks any noun/domain specificity (generic verbs with no object) → suggest narrowing with negative triggers or more specific nouns
  - Cross-reference to the negative trigger coaching from Unit 3 in the overtrigger signal
  - Do NOT implement cross-skill overlap detection (requires runtime skill graph — deferred)

  **Patterns to follow:**
  - Existing `--explain` coaching block pattern: "Why / To improve / estimated delta"
  - Do not accidentally break orphan detection code (~lines 1095, 1372, 1523) — those paths are complete (issue #82 closed)

  **Test scenarios:**
  - A description with 1 two-word trigger phrase → undertrigger signal emitted with suggestion
  - A description with 10 trigger phrases and no domain noun → overtrigger signal emitted
  - A description with 3 well-formed trigger phrases → neither signal emitted
  - A description with a negative trigger clause + 2 trigger phrases → overtrigger not triggered despite presence of negative language

  **Verification:**
  - `--explain` output for under/overtrigger cases shows correct signal
  - Existing test suite passes; new test cases added for both signals
  - `validation_tools_guide.md` documents both new signals

- [ ] **Unit 8: Document README.md divergence in agentskills_specification.md**

  **Goal:** Note explicitly that `init_skill.py`-generated README.md inside the skill folder is an intentional divergence from the Anthropic guide's "don't include README.md inside your skill folder" guidance.

  **Requirements:** R8

  **Dependencies:** None

  **Files:**
  - Modify: `plugins/skillsmith/skills/skillsmith/references/agentskills_specification.md`

  **Approach:**
  - Add a brief "Intentional Divergences from Anthropic's Guide" section (or subsection)
  - Note: Anthropic guide says "Don't include README.md inside your skill folder." Skillsmith generates one there because it serves as the metrics-tracking artifact (Current Metrics table, Version History) — a plugin-specific concern not anticipated in the general guide
  - Keep it factual and brief — no need for extended justification

  **Patterns to follow:**
  - `agentskills_specification.md` existing rationale-note style

  **Verification:**
  - Divergence is documented with a clear "why" in `agentskills_specification.md`

## System-Wide Impact

- **Interaction graph:** Changes to `evaluate_skill.py` will affect the `ss-evaluate` command output and any automated pipelines that parse `--explain` text (pre-commit hooks, `ss-improve` workflow). The hooks in `plugins/skillsmith/hooks/on-skill-edit.sh` and `on-script-edit.sh` trigger on file saves — Units 3 and 7 will trigger `on-script-edit.sh` during development.
- **Error propagation:** No new error paths — all evaluator additions are informational/coaching only. Test suite must pass before committing.
- **State lifecycle risks:** `--update-readme` is idempotent; adding new `--explain` signals does not affect README generation.
- **API surface parity:** The `skillsmith:skillsmith` SKILL.md routes `ss-evaluate` through `evaluate_skill.py`. No command interface changes needed — all additions are within existing flag behavior.
- **Integration coverage:** Run `evaluate_skill.py` on the skillsmith skill itself before and after evaluator changes; record both scores in the skill README.md version history entry.

## Risks & Dependencies

- **v6 already shipped (Gaps 2/3):** The description formula evaluator fix landed in v6 (completed). Documentation additions here should accurately reflect what the evaluator now does — read the current `validate_description_quality()` before writing examples.
- **Complexity metric constraint (Gap 4):** Body structure templates may score poorly under the current unfixed complexity metric. Mitigated by documenting the constraint explicitly and keeping templates to 3-5 sections.
- **test_evaluate_skill.py coupling:** Units 3 and 7 modify `evaluate_skill.py` behavior; all 12 existing tests must continue to pass. Run the test suite before committing evaluator changes.
- **Evaluator scoring baseline:** Must record baseline scores before making any evaluator change to establish a stable before/after comparison.

## Documentation / Operational Notes

- After all units land, run skillsmith evaluation on skillsmith itself: `uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py plugins/skillsmith/skills/skillsmith/ --version 6.1.0 --export-table-row` (version number to confirm with plugin's current state)
- Update skill README.md version history with the score row and a one-line summary of changes
- Update plugin-level `plugins/skillsmith/README.md` with a plain one-line summary per the memory guidance

## Sources & References

- **Origin issue:** [#146 feat(skillsmith): align skill guidance with Anthropic's Complete Guide](https://github.com/totallyGreg/claude-mp/issues/146)
- **v6 plan (completed, ships trigger-verb fix):** `docs/plans/2026-03-18-001-feat-skillsmith-v6-skill-improvement-companion-plan.md`
- **Complexity metric context:** `docs/plans/2026-03-18-001` (line ~734–787) — check if complexity metric fix also landed in v6
- **Evaluator false positives:** `docs/lessons/evaluate-skill-false-positives.md`
- **Orphan detection (closed #82, implemented):** `docs/plans/2026-03-04-feat-skillsmith-lifecycle-awareness-plan.md`
- **Qualitative conciseness (closed #96, implemented):** `docs/plans/2026-03-22-007-feat-skillsmith-pass2-qualitative-conciseness-observer-fix-plan.md`
- **Key evaluator files:** `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py`, `plugins/skillsmith/skills/skillsmith/scripts/init_skill.py`
- **Key reference files:** `references/form_templates.md`, `references/skill_creation_detailed_guide.md`, `references/agentskills_specification.md`, `references/validation_tools_guide.md`
- **Test file:** `plugins/skillsmith/skills/skillsmith/tests/test_evaluate_skill.py`
