---
name: ss-validate
description: Quick structural validation of a skill with optional strict mode
argument-hint: <skill-path> [--strict]
---

Quick validation of a skill with optional strict mode.

Run the validation command:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/evaluate_skill.py $ARGUMENTS --quick
```

With `--strict`, if the skill lives under `plugins/<plugin>/skills/`, also run Anthropic's validator on its plugin when the `claude` CLI is available:

```bash
claude plugin validate plugins/<plugin> --strict
```

Common arguments:
- `<skill-path>` - Path to skill directory (required)
- `--strict` - Treat warnings as errors (for pre-release gates)

Examples:
```
/ss-validate skills/my-skill
/ss-validate ./my-skill --strict
/ss-validate plugins/foundry/skills/skillsmith --strict
```

The validator checks:
- YAML frontmatter structure and required fields
- Naming conventions (lowercase, hyphens only)
- PEP 723 compliance for Python scripts
- Directory structure compliance
- With `--strict`: plugin manifest, paths and hook quoting (`claude plugin validate`)

Report validation results with any errors or warnings found.
