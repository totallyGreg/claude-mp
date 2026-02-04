Search CoSAI controls by keyword.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_control_search.py $ARGUMENTS
```

Arguments:
- `<query>` - Search term (required)
- `--offline` - Use bundled schemas

Examples:
```
/arm-control-search validation
/arm-control-search "access control" --offline
```
