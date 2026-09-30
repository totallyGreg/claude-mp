---
name: mp-status
description: Show which plugins and skills changed since main and still need a version bump
argument-hint: [--base REF]
---

Show pending version bumps for the marketplace in the current repo.

A plugin that changed since the base (merge-base of HEAD and `origin/main`) must raise its `plugin.json` version, and a skill that changed must raise its `SKILL.md` `metadata.version`. The pre-commit hook enforces this. This command previews it for the working tree.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/repo/validate.py --check-versions $ARGUMENTS
```

Arguments:
- (no args) - Compare the working tree against the merge-base with `origin/HEAD` (falls back to `origin/main`)
- `--base REF` - Compare against the merge-base with another ref

Report:
- Each plugin or skill that needs a bump, with the file to edit and the current base version
- Validation errors or warnings from `claude plugin validate` for the changed plugins
- "Nothing pending" when the check passes
