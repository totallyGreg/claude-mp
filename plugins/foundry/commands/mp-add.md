Scaffold a new plugin or migrate a legacy skill into plugin structure.

**To create a new plugin:**

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/scaffold.py create <plugin-name> $ARGUMENTS
```

**To migrate a legacy skill to plugin structure:**

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/scaffold.py migrate <skill-path> $ARGUMENTS
```

Common arguments for `create`:
- `--description "..."` - Set plugin description
- `--with-commands` - Add commands/ directory
- `--with-agents` - Add agents/ directory
- `--with-mcp` - Add .mcp.json template
- `--no-plugin-json` - Rely on auto-discovery (omit plugin.json)

Common arguments for `migrate`:
- `--dry-run` - Preview planned changes without executing

Report:
- Plugin created or skill migrated
- Directory structure generated
- Suggest running `/mp-validate --fix` to register in marketplace.json
