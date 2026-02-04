Search CoSAI risks by keyword.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_risk_search.py $ARGUMENTS
```

Arguments:
- `<query>` - Search term (required)
- `--offline` - Use bundled schemas

Examples:
```
/arm-risk-search injection
/arm-risk-search "data poisoning" --offline
```
