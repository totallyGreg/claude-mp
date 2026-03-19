Full evaluation of a skill with quality metrics.

Run the evaluation command:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/evaluate_skill.py $ARGUMENTS
```

Common arguments:
- `<skill-path>` - Path to skill directory (required)
- `--quick` - Fast structural checks only (skip metrics)
- `--strict` - Treat warnings as errors
- `--explain` - Per-metric coaching with actionable improvement suggestions (incompatible with --quick)
- `--validate-references` - Validate references/ structure and mention coverage
- `--detect-duplicates` - Detect consolidation opportunities across reference files
- `--update-readme` - Generate/update README.md with capabilities prose + metrics + version history
- `--export-table-row` - Output as markdown table row for version history
- `--version <X.Y.Z>` - Version for table row export
- `--issue <number>` - GitHub issue number for table row export

Examples:
```
/ss-evaluate skills/my-skill
/ss-evaluate ./my-skill --quick
/ss-evaluate skills/my-skill --explain
/ss-evaluate skills/my-skill --validate-references
/ss-evaluate skills/my-skill --update-readme
/ss-evaluate skills/skillsmith --export-table-row --version 5.3.0 --issue 37
```

Metrics evaluated:
- **Conciseness** (0-100): SKILL.md line count efficiency
- **Complexity** (0-100): Cognitive load assessment
- **Spec Compliance** (0-100): AgentSkills specification adherence
- **Progressive Disclosure** (0-100): Reference file usage
- **Description Quality** (0-100): Trigger phrase quality and format

Report the evaluation results with metrics and any recommendations.
