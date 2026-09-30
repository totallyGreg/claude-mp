---
name: mp-validate
description: Validate the marketplace with claude plugin validate plus version-bump, duplicate-metadata, and unregistered-plugin checks
argument-hint: [--fix] [--check-versions] [--check-structure] [--format json]
---

Validate the marketplace in the current repo.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/repo/validate.py $ARGUMENTS
```

Arguments:
- (no args) - Run `claude plugin validate` on the marketplace (strict) and every listed plugin, reject `version` in marketplace entries, and list plugins on disk that the manifest doesn't register
- `--fix` - Add unregistered plugins as minimal `{name, source}` entries
- `--check-versions` - Also require version bumps for plugins and skills changed since the base (see `/mp-status`)
- `--staged` - Version check against the git index (what the pre-commit hook runs)
- `--check-structure` - Detect anti-patterns such as plugins sharing a source path
- `--format json` - Machine-readable output

Schema checks come from Anthropic's `claude plugin validate`. This script adds only the checks it doesn't cover.

Report errors first, then warnings, then any unregistered plugins.
