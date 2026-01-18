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

See WORKFLOW.md for details.
