# skillsmith

Skill quality evaluation, improvement, and marketplace integration for Claude Code skills.

## Components

### Agent: skill-observer
Analyzes saved Claude Code session transcripts to identify where a skill failed to guide Claude effectively. Returns ranked structural gaps with installed→source path mapping.

### Skill: skillsmith
End-to-end skill development with automated quality metrics:
- Skill evaluation with scored dimensions (conciseness, complexity, spec compliance, progressive disclosure, description quality)
- Improvement loop: evaluate → apply fixes → re-evaluate → update README → bump version
- Marketplace sync via marketplace-manager
- Session transcript analysis for skill gap detection

### Commands (7)
`/ss-evaluate`, `/ss-improve`, `/ss-init`, `/ss-observe`, `/ss-package`, `/ss-research`, `/ss-validate`

### Hooks

| Hook | Trigger | Purpose |
|------|---------|---------|
| `on-skill-edit.sh` | PostToolUse Write\|Edit on `SKILL.md` | Quick skill quality evaluation; score fed back to Claude |
| `on-script-edit.sh` | PostToolUse Write\|Edit on `scripts/*.py` | Enforces PEP 723 header and bans `click`/`typer` (argparse standard) |

## Version History

| Version | Changes |
|---------|---------|
| 6.5.0 | Add `/ss-package` command for skill.zip packaging; add `on-script-edit.sh` hook to enforce argparse + PEP 723 standard; document argparse standard in `python_uv_guide.md` |
| 6.4.0 | Previous release |
| 6.0.0 | Migrated to plugin structure with skill-observer agent |
