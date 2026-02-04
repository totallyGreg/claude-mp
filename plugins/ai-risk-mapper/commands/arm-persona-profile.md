Get the risk profile for a specific persona.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_persona_profile.py $ARGUMENTS
```

Arguments:
- `<persona-id>` - Persona identifier (required)
  - `personaModelCreator` - Organizations training/fine-tuning models
  - `personaModelConsumer` - Organizations deploying pre-trained models
- `--offline` - Use bundled schemas

Examples:
```
/arm-persona-profile personaModelCreator
/arm-persona-profile personaModelConsumer --offline
```
