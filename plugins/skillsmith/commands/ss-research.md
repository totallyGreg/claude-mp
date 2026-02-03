Research a skill to identify improvement opportunities.

Run the research command:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/research_skill.py $ARGUMENTS
```

Common arguments:
- `<skill-path>` - Path to skill directory (required)
- `--focus <area>` - Focus on specific area (conciseness, complexity, disclosure)
- `--output <format>` - Output format (text, json, markdown)

Examples:
```
/ss-research skills/my-skill
/ss-research ./my-skill --focus conciseness
/ss-research skills/skillsmith --output markdown
```

Research analyzes:
- Content structure and organization
- Reference file utilization
- Script complexity and coverage
- Improvement opportunities based on metrics

Report the research findings with specific recommendations for improvement.
