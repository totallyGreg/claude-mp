# Claude-MP Repository Instructions

This repository contains Claude Code skills and follows a GitHub Issues + IMPROVEMENT_PLAN.md workflow.

## Development Workflow

See `/WORKFLOW.md` for complete documentation on:
- Simple vs complex change workflows
- GitHub Issue integration
- IMPROVEMENT_PLAN.md management
- Two-commit release strategy

## Repository Structure

- `skills/*/` - Individual skills with IMPROVEMENT_PLAN.md
- `docs/plans/` - Ephemeral planning for complex work
- `docs/lessons/` - Cross-skill learnings
- `WORKFLOW.md` - Primary workflow documentation

## Workflow Hierarchy

```
docs/lessons/         →  docs/plans/           →  GitHub Issues      →  IMPROVEMENT_PLAN.md
(Post-work learnings)    (Pre-work planning)      (Active tracking)      (Issue state summary)
                                                  (SOURCE OF TRUTH)
```

## When Working on Skills

1. **Simple changes**: Commit directly to main
2. **Complex work**:
   - Add to skill's IMPROVEMENT_PLAN.md (simple table format)
   - Create GitHub Issue for tracking (source of truth)
   - Link issue in commits and IMPROVEMENT_PLAN.md

**IMPORTANT**: GitHub Issues are the canonical source of truth for work tracking. IMPROVEMENT_PLAN.md should be a simple table that reflects issue state, not detailed planning.

**IMPORTANT**: When modifying any skill (SKILL.md, scripts, references), run skillsmith evaluation before committing:
```bash
uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py <skill-path>
```
Record the eval score in the skill's IMPROVEMENT_PLAN.md version history entry.

See WORKFLOW.md for details.

## Tool Preferences for Repository Examination

When exploring the marketplace, repository structure, or migration status:

### Directory & Structure Analysis
- Start with `tree -L 2 -d` for quick visual overview
- Use `tree -P "pattern"` to filter by filename pattern
- Use **Glob tool** for precise file searches by pattern

### Migration & Status Checks
- **Grep tool** for config analysis (marketplace.json, plugin.json)
- **Glob** for finding IMPROVEMENT_PLAN.md, plugin manifests, etc.
- **Explore agent** for understanding complex migration patterns

### Example workflow for marketplace examination
1. `tree -L 2 -d` → See full structure
2. Glob `**/.claude-plugin/plugin.json` → Find all migrated plugins
3. Glob `skills/*/IMPROVEMENT_PLAN.md` → Find remaining skills
4. Grep for "source" in marketplace.json → Compare declared vs actual locations

## Search Best Practices

When searching this repository, use `rg` (ripgrep) for targeted searches instead of `find -exec` or broad globs.

### File Type Filtering
- `rg "pattern" --type py` - Search only Python files
- `rg "pattern" --type js` - Search only JavaScript files
- `rg "pattern" --type md` - Search only Markdown files
- `rg "pattern" --type-list` - List all built-in file types

### Glob-Based Filtering
- `rg "pattern" -g '*.ts' -g '!*.test.ts'` - Include/exclude by glob
- `rg "pattern" -g 'skills/**/*.md'` - Restrict to skills directory
- `rg "pattern" -g 'plugins/**/*.py'` - Restrict to plugins directory

### Precision Flags
- `rg -w "error"` - Whole word matches only
- `rg -l "pattern"` - File names only (fast)
- `rg "pattern" --max-depth 2` - Limit directory depth
- `rg -U "pattern"` - Multiline matching
- `rg "pattern" --count` - Match counts per file

### Contextual Search
- `rg "def process" -A 5` - Show 5 lines after match
- `rg "class Config" -B 2 -A 10` - Show surrounding context

### Combining Searches
- `rg -l "pattern1" | xargs rg -l "pattern2"` - Files matching both patterns
- `rg -l "pattern" $(git diff --name-only HEAD~5)` - Search only recently changed files

### Fallback: Silver Searcher (`ag`)
- `ag "pattern" --python` - File type filter
- `ag -G '\.tsx$' "pattern"` - Regex-based file filter
- `ag --depth 3 "pattern"` - Limit directory depth
