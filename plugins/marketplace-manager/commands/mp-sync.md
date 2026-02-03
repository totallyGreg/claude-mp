Sync SKILL.md versions to marketplace.json.

Run the sync script to detect and update version mismatches:

```bash
uv run plugins/marketplace-manager/skills/marketplace-manager/scripts/sync_marketplace_versions.py $ARGUMENTS
```

Common arguments:
- (no args) - Sync all skill versions in auto mode
- `--dry-run` - Preview changes without saving
- `--mode=manual` - Warn about mismatches instead of auto-updating (for multi-skill plugins)

Report the sync results:
- List any version updates made
- Show warnings for skills with deprecated `version` field
- Confirm marketplace.json is synchronized
