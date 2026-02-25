Get the risk profile for a specific persona.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_persona_profile.py $ARGUMENTS
```

Arguments:
- `<persona-id>` - Persona identifier (required)
  - `personaModelProvider` - Organizations that train and serve AI models
  - `personaDataProvider` - Organizations supplying training/evaluation data
  - `personaPlatformProvider` - Infrastructure and platform providers
  - `personaModelServing` - Organizations managing model serving endpoints
  - `personaAgenticProvider` - Agentic platform and framework providers
  - `personaApplicationDeveloper` - Organizations building AI-powered applications
  - `personaGovernance` - AI system governance and compliance
  - `personaEndUser` - End users of AI systems
  - `personaModelCreator` - _(deprecated)_ Legacy: use personaModelProvider
  - `personaModelConsumer` - _(deprecated)_ Legacy: use personaApplicationDeveloper
- `--offline` - Use bundled schemas

Examples:
```
/arm-persona-profile personaModelProvider
/arm-persona-profile personaApplicationDeveloper --offline
```
