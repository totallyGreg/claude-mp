Get all controls that mitigate a specific risk.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_controls_for_risk.py $ARGUMENTS
```

Arguments:
- `<risk-id>` - Risk identifier (required, e.g., DP, PIJ, ADI)
- `--offline` - Use bundled schemas

Examples:
```
/arm-controls-for-risk DP
/arm-controls-for-risk PIJ --offline
```
