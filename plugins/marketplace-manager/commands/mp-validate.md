Validate marketplace.json against the official Anthropic marketplace schema.

Run the validation command:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/repo/validate.py $ARGUMENTS
```

Common arguments:
- (no args) - Validate marketplace.json schema and plugin references
- `--fix` - Auto-add unregistered plugins found on disk (reverse scan)
- `--format json` - Output results as JSON for CI/CD integration
- `--staged` - Check staged files for version bump requirements
- `--check-structure` - Detect anti-patterns (e.g. shared source paths)

The validator checks:
- Required root fields (name, owner, plugins)
- Plugin entry required fields (name, source)
- Semantic versioning format, kebab-case names
- Source path existence and component discoverability
- Reverse scan for unregistered plugins on disk
- Duplicate plugin name detection

Report validation results with any errors or warnings found.
