Quick validation of a skill with optional strict mode.

Run the validation command:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/evaluate_skill.py $ARGUMENTS --quick
```

Common arguments:
- `<skill-path>` - Path to skill directory (required)
- `--strict` - Treat warnings as errors (for pre-release gates)

Examples:
```
/ss-validate skills/my-skill
/ss-validate ./my-skill --strict
/ss-validate plugins/skillsmith/skills/skillsmith --strict
```

The validator checks:
- YAML frontmatter structure and required fields
- Naming conventions (lowercase, hyphens only)
- PEP 723 compliance for Python scripts
- Directory structure compliance

Report validation results with any errors or warnings found.
