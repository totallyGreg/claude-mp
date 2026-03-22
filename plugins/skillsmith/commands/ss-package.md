---
description: Package a skill directory into a distributable skill.zip
argument-hint: [skill-path]
---
Package a skill directory into a spec-compliant skill.zip for distribution via agentskills.io.

Run the packaging command:

```bash
uv run --quiet ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/package_skill.py $ARGUMENTS
```

Common arguments:
- `<skill-path>` - Path to skill directory (required)
- `--output <path>` - Output path for the zip (default: `<skill-name>.zip` in cwd)
- `--dry-run` - Preview included files without creating the zip

Examples:
```
/ss-package skills/my-skill
/ss-package ./pdf-editor --output dist/pdf-editor-1.0.0.zip
/ss-package plugins/skillsmith/skills/skillsmith --dry-run
```

The packager:
- Validates SKILL.md frontmatter (`name`, `description`) against AgentSkills spec
- Verifies `name` matches the directory name and follows naming rules
- Includes `SKILL.md`, `README.md`, `LICENSE*`, and the `scripts/`, `references/`, `assets/` directories
- Respects `.skillignore` in the skill root (falls back to sensible defaults)
- Zips with `<skill-name>/` as the archive prefix so extraction produces a clean directory

Report the output path and file count on success, or validation errors on failure.
