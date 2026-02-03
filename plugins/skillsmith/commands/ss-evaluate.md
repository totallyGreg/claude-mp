Full evaluation of a skill with quality metrics.

Run the evaluation command:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/evaluate_skill.py $ARGUMENTS
```

Common arguments:
- `<skill-path>` - Path to skill directory (required)
- `--quick` - Fast structural checks only (skip metrics)
- `--strict` - Treat warnings as errors
- `--export-table-row` - Output as markdown table row for IMPROVEMENT_PLAN.md
- `--version <X.Y.Z>` - Version for table row export
- `--issue <number>` - GitHub issue number for table row export

Examples:
```
/ss-evaluate skills/my-skill
/ss-evaluate ./my-skill --quick
/ss-evaluate skills/skillsmith --export-table-row --version 4.0.0 --issue 28
```

Metrics evaluated:
- **Conciseness** (0-100): SKILL.md line count efficiency
- **Complexity** (0-100): Cognitive load assessment
- **Spec Compliance** (0-100): AgentSkills specification adherence
- **Progressive Disclosure** (0-100): Reference file usage

Report the evaluation results with metrics and any recommendations.
