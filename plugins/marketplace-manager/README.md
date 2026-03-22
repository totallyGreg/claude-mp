# marketplace-manager

Plugin marketplace operations: version syncing, skill publishing, and marketplace.json maintenance.

## Components

### Skill: marketplace-manager
Programmatic marketplace management with git integration:
- Version syncing from plugin.json/SKILL.md to marketplace.json
- Validation including undeclared skill detection (skills on disk missing from skills array)
- Plugin scaffolding, skill migration, and deprecation tooling
- Pre-commit hook for automatic version sync

### Commands (5)
`/mp-sync`, `/mp-validate`, `/mp-add`, `/mp-list`, `/mp-status`

## Version History

| Version | Changes |
|---------|---------|
| 2.8.0 | Undeclared skill detection in validate; uv guard; license frontmatter fix |
| 2.7.0 | Add trigger phrases to description |
| 2.5.0 | plugin-dev docs, two-pass find_repo_root(), plugin.json schema validation, pre-commit hook v5.0.0 |
| 2.0.0 | Migrated to plugin structure |
