List all plugins in the marketplace.

Read marketplace.json directly and run validation to check plugin status:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/repo/validate.py $ARGUMENTS
```

Common arguments:
- (no args) - Validate and list all plugins with status
- `--format json` - Machine-readable output

Display the results in a formatted table showing:
- Plugin name and version
- Source path
- Description (if present)
- Validation status (errors/warnings)
