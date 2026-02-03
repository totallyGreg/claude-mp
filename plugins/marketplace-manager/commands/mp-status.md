Show version mismatches between SKILL.md files and marketplace.json.

Run the detection script:

```bash
uv run plugins/marketplace-manager/skills/marketplace-manager/scripts/detect_version_changes.py $ARGUMENTS
```

Common arguments:
- (no args) - Check all plugins for version mismatches
- `--verbose` - Show detailed version information for each skill

Report:
- Plugins with version mismatches (SKILL.md vs marketplace.json)
- Plugins that are in sync
- Recommended actions to resolve mismatches
- Suggest running `/mp-sync` if updates needed
