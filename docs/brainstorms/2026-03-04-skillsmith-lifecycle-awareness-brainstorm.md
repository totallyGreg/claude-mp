---
date: 2026-03-04
topic: skillsmith-lifecycle-awareness
---

# Skillsmith: Lifecycle-Aware Skill Management

## What We're Building

Evolve Skillsmith from a skill evaluator into a **lifecycle-aware companion** that understands the full spectrum of skill maturity — from simple SKILL.md to plugin bundles — and knows when to suggest graduation and hand off to plugin-dev skills.

**Approach**: Incremental Enhancement (Approach A) — build on existing evaluate_skill.py and SKILL.md, ship incrementally.

## Why This Matters

Skillsmith currently treats every skill as an isolated artifact. It validates structure and scores quality, but has no awareness that:
- A skill with 5 scripts and 12 references may have outgrown "skill" and should be a plugin
- A skill trying to do multiple distinct things should be split
- A skill needing slash commands, hooks, or agents should consult plugin-dev skills

The "When NOT to use" section (v5.1.0) was a first step, but it's a static redirect. What's needed is **dynamic detection** of graduation signals with actionable suggestions.

### Inspiration

Tessl CLI (`tessl skill review`) demonstrates a similar two-tier evaluation (structural validation + semantic assessment). Key difference: Tessl uses an LLM-as-judge for semantic scoring; Skillsmith keeps it deterministic, letting Claude itself serve as the semantic judge when reading skills.

## Key Decisions

### 1. Bugs First, Then Graduation as Umbrella

**Priority order:**
1. Fix #82 (orphan detection misses markdown links) — bug
2. Fix #81 (iteration workflow should mandate full eval) — bug
3. Graduation awareness — umbrella vision for v6.0
   - #24 (script consolidation) as prerequisite cleanup → v5.3.0
   - #37 (--explain mode) ships independently → v5.4.0
   - Graduation signals and maturity model → v6.0.0

### 2. Keep Evaluation Deterministic

No LLM-as-judge layer. Claude is already the judge when it reads a skill. The value is in sharper deterministic checks and clearer rubrics. This avoids API dependencies, keeps evaluation fast and reproducible.

### 3. Graduation Signals (Composite Detection)

evaluate_skill.py will detect these signals and suggest graduation paths:

| Signal | Threshold | Suggestion |
|--------|-----------|------------|
| Script count | >3 scripts | "Consider plugin structure for better organization → plugin-dev:plugin-structure" |
| Script complexity | Any script >500 lines | "Script exceeds recommended size — consider splitting or extracting a library" |
| Reference sprawl | >10 reference files or >50KB total | "Heavy reference load suggests plugin-level documentation → plugin-dev:plugin-structure" |

Three deterministic, measurable signals. Semantic judgments (e.g., "is this skill doing too much?") are left to Claude when it reads the skill.

### 4. Skill Maturity Model in SKILL.md

Add a decision tree to SKILL.md guidance:

```
Simple Skill (SKILL.md only)
  └─ Growing? Add references/ and scripts/
      └─ Complex? → Consult plugin-dev:plugin-structure
          └─ Needs commands? → plugin-dev:command-development
          └─ Needs hooks? → plugin-dev:hook-development
          └─ Needs agents? → plugin-dev:agent-development
          └─ Deterministic tools? → plugin-dev:mcp-integration
```

### 5. Where to Encode

- **evaluate_skill.py**: Deterministic graduation signal detection + suggestions in output
- **SKILL.md**: Maturity model decision tree + criteria for when to consult plugin-dev skills
- **--explain mode** (#37): Per-metric explanations include graduation suggestions when signals are detected

## Execution Plan

### Phase 1: Bug Fixes (v5.2.1)
- #82: Fix orphan detection to parse markdown link syntax
- #81: Update Step 6 to mandate full evaluation before commits

### Phase 2: Script Consolidation (#24, v5.3.0)
- Absorb update_references.py into evaluate_skill.py
- Delete deprecated scripts (4 scripts → 3)
- Prerequisite for clean graduation signal implementation

### Phase 3: Explain Mode (#37, v5.4.0)
- Add --explain flag with per-metric explanations and top-3 improvement summary
- Ships independently — already has a detailed plan in issue #37

### Phase 4: Graduation Awareness (v6.0.0)
- Add graduation signal detection to evaluate_skill.py (3 signals from Decision 3)
- Integrate graduation suggestions into --explain output
- Add Skill Maturity Model section to SKILL.md
- Update "When NOT to use" section with dynamic awareness

## Open Questions

None — all resolved during brainstorming.

## Next Steps

→ `/ce:plan` for implementation details on Phase 1 (bug fixes)
