Full evaluation of an agent with quality metrics.

Run the evaluation command:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/agentsmith/scripts/evaluate_agent.py $ARGUMENTS
```

Common arguments:
- `<agent-path>` - Path to agent file or directory (required)
- `--quick` - One-line score summary (for hooks)
- `--explain` - Per-dimension coaching with top-3 improvements
- `--format json` - Machine-readable JSON output
- `--export-table-row` - Output as markdown table row for version history
- `--version <X.Y.Z>` - Version for table row export
- `--update-readme` - Update plugin README.md with agent metrics

Examples:
```
/as-evaluate plugins/archivist/agents/archivist.md
/as-evaluate plugins/foundry/agents/skill-observer
/as-evaluate plugins/archivist/agents/archivist.md --explain
/as-evaluate plugins/archivist/agents/archivist.md --format json
```

Dimensions evaluated:
- **Trigger Effectiveness** (0-100): Example count, variety, commentary, negative triggers, phrasing variety
- **System Prompt Quality** (0-100): Role specificity, process steps, quality standards, length, structure
- **Coherence** (0-100): Description-body alignment, tool scope fitness, terminology consistency

Report the evaluation results with per-dimension scores and any recommendations.

**Redirect**: If the target is a SKILL.md file, redirect to `/ss-evaluate` instead.
