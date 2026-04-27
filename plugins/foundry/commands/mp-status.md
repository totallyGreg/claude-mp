Show version mismatches and validation summary for the marketplace.

Run the sync script in dry-run mode and validate:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/repo/sync.py --dry-run
python3 ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/repo/validate.py $ARGUMENTS
```

Common arguments:
- (no args) - Show version mismatches and validation status
- `--check-structure` - Also detect structural anti-patterns

Report:
- Plugins with version mismatches (source vs marketplace.json)
- Plugins that are in sync
- Validation errors or warnings
- Suggest running `/mp-sync` if updates needed
