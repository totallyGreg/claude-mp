Map a risk to external compliance frameworks.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_framework_map.py $ARGUMENTS
```

Arguments:
- `<risk-id>` - Risk identifier (required, e.g., PIJ, DP)
- `--framework <name>` - Filter by framework (optional): mitre-atlas, nist-ai-rmf, owasp-llm
- `--offline` - Use bundled schemas

Examples:
```
/arm-framework-map PIJ
/arm-framework-map PIJ --framework mitre-atlas
/arm-framework-map DP --framework owasp-llm --offline
```
