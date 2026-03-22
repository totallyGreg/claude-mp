---
name: skillsmith
description: This skill should be used when users ask to "create a skill", "validate a skill for quality", "evaluate skill improvements", "improve my skill", "update my skill", "fix skill", "iterate on skill", "optimize skill", "skill quality", "skill performance", "skill isn't working", "analyze skill metrics", "init a new skill", "check skill compliance", or "sync skill to marketplace". Provides comprehensive skill development with automated validation, metrics tracking, and improvement workflows.
metadata:
  author: J. Greg Williams
  version: "6.5.1"
compatibility: Requires python3 and uv for script execution and validation
license: Complete terms in LICENSE.txt
---

# Skillsmith

Forge effective skills with automated validation, metrics tracking, and improvement workflows.

Skillsmith owns Steps 5–6 of the plugin-dev skill development loop (Validate and Iterate). For Steps 1–4, defer to `plugin-dev:skill-development`.

## Skill Development Routing

| Task | Use |
|------|-----|
| Skill anatomy, writing style, progressive disclosure | `plugin-dev:skill-development` |
| Creating hooks | `plugin-dev:hook-development` |
| Creating agents | `plugin-dev:agent-development` |
| Slash commands | `plugin-dev:command-development` |
| Plugin manifest/structure | `plugin-dev:plugin-structure` |
| **Validating, evaluating, improving skills** | **skillsmith** (this skill) |
| Syncing versions to marketplace | `marketplace-manager` |

## Skill Development Loop

### Step 1: Understand the Skill

See `plugin-dev:skill-development` Step 1 for guidance on identifying usage examples, trigger phrases, and resource types needed.

### Step 2: Plan Reusable Contents

See `plugin-dev:skill-development` Step 2 for content planning, choosing reference files vs. inline content, and progressive disclosure strategy.

### Step 3: Create Structure

```bash
uv run scripts/init_skill.py <skill-name> --path <output-directory>
```

Generates SKILL.md template, README.md stub, and resource directories (`scripts/`, `references/`, `examples/`). See `plugin-dev:skill-development` Step 3 for full structure guidance.

### Step 4: Edit SKILL.md

See `plugin-dev:skill-development` Step 4 for writing style, frontmatter format, and progressive disclosure. Skillsmith-specific requirements:

- **Frontmatter**: `name`, `description` (max 1024 chars), `metadata.version`, `compatibility`, `license`
- **Python scripts**: PEP 723 inline metadata required for `uv run`. See `references/python_uv_guide.md`
- **Size target**: <300 lines, <2000 tokens; move detailed content to `references/`

### Step 5: Validate

```bash
# Quick validation during development
uv run scripts/evaluate_skill.py <skill-path> --quick

# Full evaluation with metrics
uv run scripts/evaluate_skill.py <skill-path>

# Per-metric coaching with actionable improvements
uv run scripts/evaluate_skill.py <skill-path> --explain
```

**Quality scores** (0–100 each):

| Score | What It Measures | How to Improve |
|-------|-----------------|----------------|
| Conciseness | Lines and tokens vs. targets | Move content to `references/` |
| Complexity | Section count, nesting, code blocks | Merge sections, move examples to references |
| Spec Compliance | Required and recommended frontmatter fields | Add `metadata.version`, `compatibility`, `license` |
| Progressive Disclosure | Use of references alongside SKILL.md | Create `references/` for skills >200 lines |
| Description Quality | Trigger phrase format and specificity | Use action verb phrases ("create X", "fix Y") |

See `references/validation_tools_guide.md` for the complete flag reference.

### Step 6: Iterate (Skillsmith's Core Loop)

```
Evaluate → Explain → Fix → Re-evaluate → Update README → Sync
```

```bash
# Identify top-3 improvements with estimated score impact
uv run scripts/evaluate_skill.py <skill-path> --explain

# After fixes: re-evaluate and refresh README.md metrics
uv run scripts/evaluate_skill.py <skill-path> --update-readme

# Export version history row (paste into README.md Version History)
uv run scripts/evaluate_skill.py <skill-path> --export-table-row --version X.Y.Z
```

**Improvement routing:**
- **Quick updates** (<50 lines, single file): Fix directly, PATCH bump
- **Complex improvements** (multi-file, structural): GitHub Issue + README.md version row

**Version bumping:**
- PATCH: Bug fixes, docs, minor updates
- MINOR: New features, backward-compatible
- MAJOR: Breaking changes

After improvements, invoke **marketplace-manager** to sync `marketplace.json`.

## Reference Documentation

| Reference | Content |
|-----------|---------|
| `references/agentskills_specification.md` | Complete AgentSkills spec, validation checklist |
| `references/skill_creation_detailed_guide.md` | Detailed editing, writing style, progressive disclosure |
| `references/validation_tools_guide.md` | Full evaluate_skill.py flag reference |
| `references/python_uv_guide.md` | PEP 723 inline metadata for uv scripts |
| `references/improvement_workflow_guide.md` | Improvement routing and workflows |
| `references/progressive_disclosure_discipline.md` | Avoiding documentation bloat |
| `references/reference_management_guide.md` | Managing reference files |
| `references/improvement_plan_best_practices.md` | README.md format, version history documentation |
| `references/readme_template.md` | README.md template and authoring guidance |
| `references/integration_guide.md` | Integration patterns with marketplace-manager |
| `references/form_templates.md` | Form templates for structured data collection |
