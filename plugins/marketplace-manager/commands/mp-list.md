List all plugins in the marketplace.

Run the list command:

```bash
uv run plugins/marketplace-manager/skills/marketplace-manager/scripts/add_to_marketplace.py list $ARGUMENTS
```

Common arguments:
- (no args) - List all plugins with basic info
- `--verbose` - Show full plugin details including skills and source paths

Display the results in a formatted table showing:
- Plugin name and version
- Description
- Category
- Number of skills (if multi-skill plugin)
- Source path
