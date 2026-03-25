# Skill README.md Template and Authoring Guide

Every skill directory should contain a `README.md` that serves as the human-readable companion to `SKILL.md`. It documents capabilities, tracks metric history, and provides onboarding context for developers — not just trigger descriptions.

## When to Create or Update

- **Create**: When initializing a new skill (`init_skill.py` generates a stub automatically for standard/complete templates)
- **Migrate**: When `/ss-improve` touches a skill that still has `IMPROVEMENT_PLAN.md` but no `README.md`
- **Update metrics**: Run `uv run scripts/evaluate_skill.py <path> --update-readme` — only `## Current Metrics` is replaced; all other sections are preserved
- **Add version row**: Run `uv run scripts/evaluate_skill.py <path> --export-table-row` and paste the row into `## Version History`

## README.md Format

```markdown
# {Skill Name}

{2-4 sentence prose description of what this skill enables and when to use it.
Written for a developer onboarding to the skill — not a trigger description.
Explain the problem it solves and what makes it distinct from related skills.}

## Capabilities

- {Concrete capability 1 — what the user can do, not what the skill "provides"}
- {Concrete capability 2}
- {Concrete capability 3}
...

## Current Metrics

**Score: X/100** (Excellent) — YYYY-MM-DD

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| X | X | X | X | X |

## Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| X.Y.Z | YYYY-MM-DD | [#N](url) | {What changed and why} | X | X | X | X | X | X |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

## Active Work

- [#N](link): {Description} (Status)

See GitHub Issues for detailed plans and task checklists.

## Known Issues

- {Issue description} — or "None." if none exist

## Archive

- Git history: `git log --grep="{skill-name}"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:enhancement+is:closed
- Cross-skill learnings: `docs/lessons/`

---

*Run `uv run scripts/evaluate_skill.py <path> --update-readme` to refresh metrics.*
```

## Authoring Notes

### Prose Description (before ## Capabilities)
- **Who it's for**: A developer onboarding to this skill, not the LLM trigger system
- **Length**: 2-4 sentences maximum
- **Content**: What problem does it solve? When should you reach for it? What makes it distinct?
- **Not**: A rephrasing of the SKILL.md `description` frontmatter trigger phrases

### Capabilities (bullet list)
- **Start with a verb**: "Evaluate...", "Generate...", "Detect..."
- **Concrete, not vague**: "Evaluate five structural metrics with per-metric scoring" not "Provides metrics"
- **User-facing**: What can the user/developer accomplish, not what the skill internally does

### Current Metrics
- **Auto-managed**: Do not hand-edit this section — run `--update-readme` to refresh
- **Interpretation guidance**: Excellent (≥95), Good (≥80), Fair (≥60), Needs work (<60)
- **Metrics authority**: Plugin-level README.md is the sole metrics record; do not write metrics to SKILL.md frontmatter

### Version History
- **Newest first**: Most recent version at the top
- **All columns required**: Use `-` for metrics not available for that version
- **Column headers**: Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality, Score=Overall
- **Summary**: Focus on what changed and why, not implementation details

### Active Work
- Link to GitHub Issues — they are the source of truth, not this section
- Remove entries when issues close; they move to Version History via a new row

### Known Issues
- Actionable, not aspirational — describe the actual symptom and workaround if any
- Cross-reference the GitHub Issue number if one exists
- Delete when resolved (don't just strikethrough in README)

## Idempotency Guarantee

`--update-readme` **only replaces the `## Current Metrics` section**. All other sections (prose, capabilities, version history, known issues, archive) are preserved verbatim on every run. This means:

- You can safely hand-edit any section except `## Current Metrics`
- Running `--update-readme` after every evaluation is always safe
- Version history rows must be manually added via `--export-table-row`
