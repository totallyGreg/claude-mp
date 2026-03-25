# Plugin README Template and Authoring Guide

Per-skill metrics are tracked in the **plugin-level README.md** (`plugins/<plugin>/README.md`), not in skill directories. Each skill's metrics live under a `## Skill: <name>` section within the plugin README.

## When to Update

- **Update metrics**: `uv run scripts/evaluate_skill.py <skill-path> --update-readme` — updates `### Current Metrics` in the correct `## Skill:` section of the plugin README
- **Add version row**: `uv run scripts/evaluate_skill.py <skill-path> --export-table-row --version X.Y.Z` and paste into `### Version History`
- **Auto-migration**: If a skill-level README.md or IMPROVEMENT_PLAN.md is detected, `--update-readme` offers to migrate it to the plugin README automatically

## Plugin README Structure

```markdown
# {plugin-name}

{Plugin description — what it provides and when to use it.}

## Components

### Agent: {name}
{Description}

### Skill: {name}
{Description}

### Commands
{List}

### Hooks
{Table}

## Changelog

| Version | Changes |
|---------|---------|
| X.Y.Z | {What changed} |

## Skill: {skill-name}

### Current Metrics

**Score: X/100** (Excellent) — YYYY-MM-DD

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| X | X | X | X | X |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| X.Y.Z | YYYY-MM-DD | [#N](url) | {What changed and why} | X | X | X | X | X | X |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)
```

## Authoring Notes

### Skill Sections
- One `## Skill: <name>` section per skill in the plugin
- `<name>` is the skill directory name (matches SKILL.md `name:` frontmatter)
- Single-skill plugins still use the `## Skill:` structure for consistency

### Current Metrics (### level)
- **Auto-managed**: Do not hand-edit — run `--update-readme` to refresh
- **Interpretation**: Excellent (>=95), Good (>=80), Fair (>=60), Needs work (<60)
- **Metrics authority**: Plugin README is the sole metrics record; do not write metrics to SKILL.md frontmatter

### Version History (### level)
- **Newest first**: Most recent version at the top
- **All columns required**: Use `-` for metrics not available for that version
- **Column headers**: Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality, Score=Overall
- **Summary**: Focus on what changed and why, not implementation details

### Changelog (## level)
- Plugin-level version history (distinct from per-skill metrics history)
- Tracks plugin-wide changes: new skills added, components reorganized, hooks added

## Idempotency Guarantee

`--update-readme` **only replaces the `### Current Metrics` subsection** within the targeted `## Skill:` section. All other content in the plugin README — including other skill sections, Components, Changelog, and any hand-edited content — is preserved verbatim.
