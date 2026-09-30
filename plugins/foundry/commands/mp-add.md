---
name: mp-add
description: Scaffold a new plugin or migrate a legacy skill into plugin structure
argument-hint: create <plugin-name> | migrate <skill-path> [options]
---

Scaffold a new plugin or migrate a legacy skill into plugin structure.

**To create a new plugin:**

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/scaffold.py create $ARGUMENTS
```

**To migrate a legacy skill to plugin structure:**

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/scaffold.py migrate $ARGUMENTS
```

Common arguments for `create`:
- `--description "..."` - Set the plugin description (written to plugin.json)
- `--with-commands` - Add commands/ directory
- `--with-agents` - Add agents/ directory
- `--with-mcp` - Add .mcp.json template

Common arguments for `migrate`:
- `--dry-run` - Preview planned changes without executing

After creating a plugin:
- Put `description`, `author`, and `version` in `plugin.json` only
- Run `/mp-validate --fix` to register it in marketplace.json as `{name, source}`; add `category` by hand if the marketplace uses categories
