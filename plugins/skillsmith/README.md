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

### Commands (6)
`/ss-evaluate`, `/ss-improve`, `/ss-init`, `/ss-observe`, `/ss-research`, `/ss-validate`

## Version History

| Version | Changes |
|---------|---------|
| 6.4.0 | Current release |
| 6.0.0 | Migrated to plugin structure with skill-observer agent |
