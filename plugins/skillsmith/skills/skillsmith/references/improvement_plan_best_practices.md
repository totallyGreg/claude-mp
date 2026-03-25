# Skill Metrics Best Practices

## Overview

Skill quality is tracked with measurable metrics in the **plugin-level README.md** under `## Skill: <name>` sections. GitHub Issues are the canonical source of truth for all planning. The plugin README reflects issue state with version history and metrics.

See `references/plugin_readme_template.md` for the exact format.

## Key Principles

1. **Plugin README is the metrics artifact**: `--update-readme` writes to the plugin README, not the skill directory
2. **GitHub Issues are source of truth**: All detailed planning happens there, not in README sections
3. **Version History with metrics**: Track quality over time using `--export-table-row`
4. **Two-commit strategy**: Implementation separate from release

## Version Management

### Semantic Versioning

- **PATCH** (1.0.0 → 1.0.1): Bug fixes, typo corrections, minor docs
- **MINOR** (1.0.0 → 1.1.0): New features, backward-compatible changes
- **MAJOR** (1.0.0 → 2.0.0): Breaking changes, major rewrites

### Version Decision Tree

```
Does this change the skill's behavior or capabilities?
│
├─ NO → Just commit implementation (no version change)
│
└─ YES → Which type of change?
         ├─ PATCH: Bug fixes, typos, minor docs
         ├─ MINOR: New features, enhancements
         └─ MAJOR: Breaking changes, renames, restructuring
```

## Release Workflow

### Two-Commit Strategy

**Commit 1: Implementation**
```bash
git commit -m "feat(skill-name): Add feature (#123)"
```

**Commit 2: Release**
```bash
# 1. Evaluate and export table row
uv run scripts/evaluate_skill.py <skill-path> --export-table-row --version X.Y.Z --issue 123

# 2. Paste row into ### Version History in plugin README
# 3. Update SKILL.md metadata.version
# 4. Commit release
git commit -m "chore: Release skill-name vX.Y.Z

Closes #123"
```

## Metrics Tracking

Metrics are scored 0-100:

- **Conciseness (Concs)**: How lean is SKILL.md? Lower token counts = higher scores
- **Complexity (Complx)**: How manageable is the skill? Fewer files/lines = higher scores
- **Spec Compliance (Spec)**: Does it follow the spec? Full compliance = 100
- **Progressive Disclosure (Progr)**: Are references used well? Good balance = higher scores
- **Description Quality (Descr)**: Does the description follow the formula and include triggers?

### Using --export-table-row

```bash
uv run scripts/evaluate_skill.py <skill-path> --export-table-row --version 2.0.0 --issue 123
# Output:
# | 2.0.0 | 2026-01-23 | [#123](url) | skill-name v2.0.0 | 67 | 90 | 100 | 100 | 95 | 89 |
```

## Common Pitfalls

1. **Detailed planning in README**: Put it in GitHub Issues, not Active Work sections
2. **Missing metrics in version rows**: Always use `--export-table-row` to avoid transcription errors
3. **Forgetting to remove from Active Work**: When adding a version row, also remove the issue from Active Work
4. **Not referencing issues in commits**: Always include `(#123)` in commit messages
