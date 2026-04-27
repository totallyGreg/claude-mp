---
description: Package a skill directory into a distributable skill.zip
argument-hint: [skill-path]
---
Package a skill directory into a spec-compliant skill.zip for distribution via agentskills.io.

## Steps

1. Package to a temp path:

```bash
uv run --quiet ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/package_skill.py $ARGUMENTS --output /tmp/<skill-name>.zip
```

2. On success, show a macOS save dialog so the user can choose the final destination:

```bash
osascript -e 'set f to POSIX path of (choose file name with prompt "Save skill package:" default name "<skill-name>.zip")' 2>/dev/null
```

3. If the user chose a path (exit 0), move the temp zip there:

```bash
mv /tmp/<skill-name>.zip "<chosen-path>"
```

4. If the user cancelled (exit 1 or empty output), leave the zip at `/tmp/<skill-name>.zip` and report that location.

## Arguments

- `<skill-path>` - Path to skill directory (required)
- `--dry-run` - Preview included files without creating the zip (skip save dialog)

## Examples

```
/ss-package skills/my-skill
/ss-package plugins/skillsmith/skills/skillsmith --dry-run
```

## Packager behaviour

- Validates SKILL.md frontmatter (`name`, `description`) against AgentSkills spec
- Verifies `name` matches the directory name and follows naming rules
- Includes `SKILL.md`, `README.md`, `LICENSE*`, and the `scripts/`, `references/`, `assets/` directories
- Respects `.skillignore` in the skill root (falls back to sensible defaults)
- Zips with `<skill-name>/` as the archive prefix so extraction produces a clean directory

Report the final output path and file count on success, or validation errors on failure.
