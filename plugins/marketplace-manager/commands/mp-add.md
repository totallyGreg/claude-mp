Add a skill to the marketplace or create a new plugin.

**To add a skill to an existing plugin:**

```bash
uv run plugins/marketplace-manager/skills/marketplace-manager/scripts/add_to_marketplace.py add-skill <skill-path> --plugin <plugin-name> $ARGUMENTS
```

**To create a new plugin with a skill:**

```bash
uv run plugins/marketplace-manager/skills/marketplace-manager/scripts/add_to_marketplace.py create-plugin <plugin-name> --skill <skill-path> $ARGUMENTS
```

Common arguments:
- `--verbose` - Show detailed path resolution
- `--category <name>` - Set plugin category (development, productivity, etc.)

Report:
- Plugin created or skill added
- Updated marketplace.json entries
- Validation status of new entries
