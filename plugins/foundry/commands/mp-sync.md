Sync plugin versions from plugin.json/SKILL.md to marketplace.json.

Run the sync script to detect and update version mismatches:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/repo/sync.py $ARGUMENTS
```

Common arguments:
- (no args) - Sync all plugin versions to marketplace.json
- `--dry-run` - Preview changes without writing

Report the sync results:
- List any version updates made to marketplace.json
- Show plugins that were already in sync
- Suggest running `/mp-validate` after syncing
