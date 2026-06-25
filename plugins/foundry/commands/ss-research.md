---
name: ss-research
description: Research a skill to identify improvement opportunities
argument-hint: [skill-path] [optional context lines...]
---

## Step 0: Parse arguments

`$ARGUMENTS` is structured: the **first non-empty line (trimmed)** is the skill path; any **remaining lines** are optional context (e.g., a `Focus: ...` hint).

- **TARGET** = first non-empty line of `$ARGUMENTS`
- **CONTEXT** = remaining lines (may be empty)

Substitute TARGET wherever you see `<TARGET>` below. **Never paste raw multi-line `$ARGUMENTS` into a path argument.** If TARGET is empty, ask the user for the skill path. CONTEXT is advisory framing for the research — incorporate it into your final summary; do NOT substitute it into bash commands.

## Run research

Research a skill for improvement opportunities using evaluate_skill.py with --explain:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/evaluate_skill.py <TARGET> --explain
```

For deep structural guidance on skill intent and domain understanding, use `plugin-dev:skill-development`.

Common arguments:
- `<skill-path>` - Path to skill directory (required)
- `--explain` - Per-metric coaching with actionable improvements (included by default)

Examples:
```
/ss-research skills/my-skill
/ss-research plugins/foundry/skills/skillsmith
```

Research analyzes:
- Per-metric scores with specific improvement suggestions
- Top-3 improvements with estimated score impact
- Reference file utilization and coverage gaps
- Description quality and trigger phrase effectiveness
- Reference freshness status (if provenance-tracked references exist)

After running the evaluation, check if the skill has provenance-tracked references:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/check_freshness.py <TARGET> --verbose
```

If provenance exists, include the freshness status in the research output alongside the evaluation metrics. If no provenance exists, skip silently.

Report the findings with specific recommendations for improvement.
