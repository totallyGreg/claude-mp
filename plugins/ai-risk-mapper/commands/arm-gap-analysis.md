Assess control coverage gaps for a specific risk.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_gap_analysis.py $ARGUMENTS
```

Arguments:
- `<risk-id>` - Risk identifier (required, e.g., DP, PIJ)
- `--implemented <control-ids>` - Space-separated list of implemented controls
- `--offline` - Use bundled schemas

Examples:
```
/arm-gap-analysis DP --implemented controlTrainingDataSanitization
/arm-gap-analysis PIJ --implemented controlInputValidation controlOutputFiltering --offline
```
