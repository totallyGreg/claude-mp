# Skillsmith Plugin Migration Plan

**Issues:**
- [#28](https://github.com/totallyGreg/claude-mp/issues/28) - Migrate to standalone plugin structure
- [#16](https://github.com/totallyGreg/claude-mp/issues/16) - Create /evaluate-skill command wrapper (incorporated)

**Created:** 2026-02-03

## Overview

Migrate skillsmith from legacy `skills/skillsmith/` to standalone plugin structure at `plugins/skillsmith/`. This migration incorporates #16 by implementing slash commands as part of the new plugin structure.

## Pre-Migration State

- **Current Version:** 3.7.2
- **Location:** `skills/skillsmith/`
- **Marketplace Entry:** Uses legacy `source: ./skills/skillsmith` format

## Target State

- **New Version:** 4.0.0 (major bump - breaking path change)
- **Location:** `plugins/skillsmith/`
- **Structure:**
  ```
  plugins/skillsmith/
  ├── .claude-plugin/
  │   └── plugin.json
  ├── commands/
  │   ├── ss-validate.md
  │   ├── ss-init.md
  │   ├── ss-evaluate.md
  │   └── ss-research.md
  └── skills/skillsmith/
      ├── SKILL.md
      ├── IMPROVEMENT_PLAN.md
      ├── LICENSE.txt
      ├── scripts/
      ├── references/
      └── tests/
  ```

## Migration Steps

### Phase 1: Execute Migration Script

```bash
# Preview
uv run plugins/marketplace-manager/skills/marketplace-manager/scripts/migrate_to_plugin.py skillsmith --dry-run --verbose

# Execute
uv run plugins/marketplace-manager/skills/marketplace-manager/scripts/migrate_to_plugin.py skillsmith --verbose
```

The script will:
1. Create plugin directory structure
2. Move files with `git mv` (preserves history)
3. Create `plugin.json` manifest
4. Update `marketplace.json`
5. Remove empty source directory

### Phase 2: Create Slash Commands (incorporates #16)

Create user-friendly commands in `plugins/skillsmith/commands/`:

| Command | Script | Purpose |
|---------|--------|---------|
| `/ss-validate` | `evaluate_skill.py --quick` | Quick validation with optional `--strict` mode |
| `/ss-init` | `init_skill.py` | Initialize new skill from template |
| `/ss-evaluate` | `evaluate_skill.py` | Full evaluation with metrics (addresses #16) |
| `/ss-research` | `research_skill.py` | Research skill for improvements |

**Command Requirements from #16:**
- Support relative and absolute skill paths
- Pass through all evaluate_skill.py flags (`--quick`, `--strict`, `--export-table-row`, etc.)
- Work from any directory using `${CLAUDE_PLUGIN_ROOT}` for script paths

**Example Usage:**
```bash
/ss-evaluate skills/my-skill
/ss-evaluate ./my-skill --quick
/ss-evaluate skills/skillsmith --export-table-row --version 4.0.0 --issue 28
/ss-validate skills/my-skill --strict
/ss-init my-new-skill --path ./skills
```

### Phase 3: Update plugin.json

Ensure version reflects the actual current version (3.7.2 -> 4.0.0):

```json
{
  "name": "skillsmith",
  "version": "4.0.0",
  "description": "Guide for creating, evaluating, researching, and improving effective skills...",
  "author": {
    "name": "J. Greg Williams",
    "email": "283704+totallyGreg@users.noreply.github.com"
  },
  "license": "MIT",
  "keywords": ["skills", "development", "validation", "claude-code"]
}
```

### Phase 4: Verify and Test

1. Verify scripts work from new location:
   ```bash
   uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py plugins/skillsmith/skills/skillsmith --quick
   ```

2. Verify slash commands work:
   ```
   /ss-validate
   /ss-init
   ```

3. Run marketplace sync to ensure consistency:
   ```bash
   uv run plugins/marketplace-manager/skills/marketplace-manager/scripts/sync_marketplace_versions.py
   ```

### Phase 5: Update Documentation

1. Update IMPROVEMENT_PLAN.md with 4.0.0 entry
2. Update SKILL.md frontmatter version to 4.0.0
3. Add migration note to any breaking changes

## Commit Strategy

Following repository WORKFLOW.md pattern:

**Commit 1: Migration**
```
refactor(skillsmith): Migrate to standalone plugin structure

- Move from skills/skillsmith to plugins/skillsmith
- Add .claude-plugin/plugin.json manifest
- Update marketplace.json source path

Closes #28
```

**Commit 2: Commands and Release**
```
feat(skillsmith): Add slash commands and bump to v4.0.0

- Add /ss-validate, /ss-init, /ss-evaluate, /ss-research commands
- Bump version 3.7.2 -> 4.0.0 (breaking path change)
- Update IMPROVEMENT_PLAN.md

Closes #16
```

## Rollback Plan

If issues arise:
```bash
git revert <commit-hash>
```

The migration uses `git mv` so history is preserved and reverting is straightforward.

## Success Criteria

- [ ] Plugin loads correctly from new location
- [ ] All scripts execute successfully
- [ ] Slash commands work
- [ ] marketplace.json reflects new structure
- [ ] Version bumped to 4.0.0
- [ ] IMPROVEMENT_PLAN.md updated
