---
name: skillsmith
description: This skill should be used when users ask to "create a skill", "validate a skill for quality", "evaluate skill improvements", "research skill opportunities", "analyze skill metrics", "improve skill quality", "init a new skill", "check skill compliance", or "sync skill to marketplace". Provides comprehensive skill development with automated validation, metrics tracking, and improvement workflows.
metadata:
  author: J. Greg Williams
  version: "5.3.0"
compatibility: Requires python3 and uv for script execution and validation
license: Complete terms in LICENSE.txt
---

# Skillsmith

Forge effective skills with automated validation, metrics tracking, and improvement workflows.

For foundational skill concepts (anatomy, progressive disclosure, writing style, common mistakes), defer to `plugin-dev:skill-development`. Skillsmith extends the official guidance with tooling, metrics-driven evaluation, and self-improvement workflows.

## When NOT to Use Skillsmith

- **Adding commands to existing plugins** → Use `plugin-dev:command-development`
- **Plugin structure/manifest changes** → Use `plugin-dev:plugin-structure`
- **Creating hooks or agents** → Use `plugin-dev:hook-development` or `plugin-dev:agent-development`

## Skill Creation Process

### Step 1: Understand the Skill

Identify concrete usage examples and trigger phrases. Ask targeted questions:

- "What functionality should this skill support?"
- "What would a user say that should trigger this skill?"
- "What scripts, references, or assets would help?"

### Step 2: Initialize the Skill

```bash
uv run scripts/init_skill.py <skill-name> --path <output-directory>
```

Generates a skill directory with SKILL.md template, frontmatter TODOs, and example resource directories (`scripts/`, `references/`, `assets/`). Customize or remove generated files as needed.

### Step 3: Edit the Skill

Write SKILL.md using imperative form, keeping it lean (<500 lines, <2000 tokens ideal). Focus on procedural knowledge non-obvious to Claude. Move detailed content to `references/`.

**Frontmatter requirements** (AgentSkills spec):
- `name`: 1-64 chars, lowercase alphanumeric and hyphens, must match directory name
- `description`: Max 1024 chars, third-person format with trigger phrases
- Optional: `license`, `compatibility`, `metadata` (including `version`), `allowed-tools`

**Python scripts** must use PEP 723 inline metadata for uv execution. See `references/python_uv_guide.md`.

See `references/skill_creation_detailed_guide.md` for comprehensive editing guidance and `references/agentskills_specification.md` for complete spec.

### Step 4: Validate the Skill

```bash
# Quick validation (structure-only) — use during development
uv run scripts/evaluate_skill.py <skill-path> --quick

# Strict validation (warnings as errors) — use before release
uv run scripts/evaluate_skill.py <skill-path> --quick --strict

# Full evaluation with metrics
uv run scripts/evaluate_skill.py <skill-path>
```

**Quality scores** (0-100 each):

| Score | What It Measures | How to Improve |
|-------|-----------------|----------------|
| Conciseness | Lines (<300 rec, <500 max) and tokens (<2000 max) | Move content to `references/` |
| Complexity | Section count (<10 H2s), nesting depth (<3), code blocks (<10) | Consolidate sections, move examples to references |
| Spec Compliance | Required fields (name, description), recommended fields (metadata, compatibility, license), structure | Add missing frontmatter fields |
| Progressive Disclosure | Use of references, scripts, assets alongside SKILL.md | Add `references/` for skills >200 lines |
| Description | Trigger phrases with action verbs, third-person format, specificity | Add phrases like "create X", "validate Y", "configure Z" |

See `references/validation_tools_guide.md` for complete command reference.

### Step 5: Iterate and Self-Improve

Skillsmith supports a **metrics-driven improvement cycle**. After any change, re-evaluate and use the scores to identify the next fix.

**Self-improvement loop:**

```
Evaluate → Identify lowest score → Apply targeted fix → Re-evaluate → Repeat
```

**Targeted fixes by score:**

| Low Score | Diagnosis | Fix |
|-----------|-----------|-----|
| Conciseness <80 | SKILL.md too long | Extract sections to `references/`, condense examples |
| Complexity <80 | Too many sections or code blocks | Merge related H2 sections, move code examples to references |
| Spec Compliance <90 | Missing frontmatter fields | Add `metadata.version`, `compatibility`, `license` |
| Progressive <90 | No bundled resources | Create `references/` for detailed content |
| Description <90 | Weak triggers or wrong format | Rewrite with "This skill should be used when..." and action verb phrases |

**Improvement routing** (see `references/improvement_workflow_guide.md`):
- **Quick updates** (<50 lines, single file, additive): Fix directly, auto PATCH bump
- **Complex improvements** (>50 lines, multi-file, structural): GitHub Issue + IMPROVEMENT_PLAN.md

**Additional commands:**

```bash
# Store metrics in SKILL.md frontmatter
uv run scripts/evaluate_skill.py <skill-path> --store-metrics

# Compare before/after improvement
uv run scripts/evaluate_skill.py <skill-path> --compare <original-path>

# Export version history row for IMPROVEMENT_PLAN.md
uv run scripts/evaluate_skill.py <skill-path> --export-table-row --version 2.0.0
```

**Version bumping:**
- PATCH (auto): Bug fixes, docs, minor updates
- MINOR (user selects): New features, backward-compatible
- MAJOR (user selects): Breaking changes

After improvements, optionally invoke **marketplace-manager** to sync versions to marketplace.json.

## Reference Documentation

| Reference | Content |
|-----------|---------|
| `references/agentskills_specification.md` | Complete AgentSkills spec, validation checklist, naming rules |
| `references/skill_creation_detailed_guide.md` | Detailed editing, writing style, progressive disclosure |
| `references/validation_tools_guide.md` | Full evaluate_skill.py and research_skill.py documentation |
| `references/python_uv_guide.md` | Python scripts with uv and PEP 723 inline metadata |
| `references/improvement_workflow_guide.md` | Improvement routing logic and workflows |
| `references/progressive_disclosure_discipline.md` | Avoiding documentation bloat |
| `references/reference_management_guide.md` | Managing reference files |
| `references/improvement_plan_best_practices.md` | Version history and planning documentation |
| `references/research_guide.md` | Research phases, metrics interpretation |
| `references/integration_guide.md` | Integration patterns with marketplace-manager |
| `references/form_templates.md` | Form templates for structured data collection |
