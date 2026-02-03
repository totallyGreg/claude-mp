Validate marketplace.json structure and skill references.

Run the validation command:

```bash
uv run plugins/marketplace-manager/skills/marketplace-manager/scripts/add_to_marketplace.py validate $ARGUMENTS
```

Common arguments:
- (no args) - Validate all plugins in marketplace.json
- `--format json` - Output results as JSON for CI/CD integration

The validator checks:
- Marketplace.json schema compliance
- Semantic versioning format (X.Y.Z)
- Skill directory and SKILL.md existence
- Duplicate plugin name detection
- Frontmatter metadata completeness

Report validation results with any errors or warnings found.
