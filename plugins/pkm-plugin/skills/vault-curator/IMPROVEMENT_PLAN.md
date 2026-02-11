# Vault Curator - Improvement Plan

## Current Version: 1.0.0

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-10 | Initial release with meeting extraction, migration patterns, and pattern detection workflows |

## Completed Improvements

### v1.0.0 (2026-02-10)

**Goal:** Create minimal viable vault-curator skill

**Implemented:**
- ✅ SKILL.md with vault evolution workflows (449 lines)
- ✅ extract_section_to_meeting.py script with PEP 723 header
- ✅ migration-strategies.md reference with rollback patterns
- ✅ Path validation security checks
- ✅ JSON-based script outputs

**Success Criteria Met:**
- Skill passes strict validation
- Clear separation from vault-architect
- PEP 723 pattern established
- Security patterns documented

## Planned Improvements

### High Priority

| Item | Description | Benefit | Est. Effort |
|------|-------------|---------|-------------|
| Phase 4 Scripts | Implement remaining scripts: import_calendar_event.py, migrate_meetings_scope.py, match_person_by_email.py, find_orphans.py, detect_schema_drift.py, find_note_clusters.py | Complete toolset for vault curation | Medium |
| Slash Commands | Add /extract-meeting, /import-calendar, /migrate-meetings commands | User-facing operations | Medium |
| Pattern Detection Reference | Create pattern-detection.md with cluster analysis examples | Better pattern discovery guidance | Low |

### Medium Priority

| Item | Description | Benefit | Est. Effort |
|------|-------------|---------|-------------|
| Vault Evolution History | Create vault-evolution-history.md tracking common transitions (Dataview → Bases, folder reorganizations) | Learning from past migrations | Low |
| Test Suite | Add pytest tests for Python scripts | Reliability and confidence | Medium |
| Script README | Document each script in scripts/README.md | Better discoverability | Low |

### Low Priority

| Item | Description | Benefit | Est. Effort |
|------|-------------|---------|-------------|
| URI Handlers | Create simple URI commands (quick-meeting, extract-selection, import-clipboard) | External tool integration | Low |
| Consolidate Dataview Script | Script to find and replace Dataview queries with Bases | Migration automation | Medium |
| Performance Optimization | Optimize scripts for large vaults (>10k notes) | Better scaling | Medium |

## Enhancement Requests

_This section tracks user-requested features and improvements._

### User: gregwilliams

*No enhancement requests yet. Track requests here as they arise.*

## Technical Debt

| Item | Priority | Description |
|------|----------|-------------|
| Complete TODO in extract_section_to_meeting.py | Medium | Combine date + time to create full start datetime |
| Remove unused imports | Low | Clean up datetime import in extract script |
| Add type hints to all functions | Low | Improve code maintainability |

## User-Specific Customizations

### gregwilliams' Vault Patterns

Meeting notes organization:
- Log syntax: `### (log::⏱ HH:MM ZONE: Title)`
- Scope metadata: `scope:: [[Company]], [[Project]]`
- Folder structure: `Company/Meetings/` for work notes
- Frontmatter schema: fileClass, scope, attendees, start, end, type, color

These patterns are incorporated into extraction and migration scripts.

## Future Considerations

- Integration with calendar apps (Google Calendar, Outlook)
- Real-time sync for meeting imports
- AI-powered pattern detection (suggest consolidations)
- Visual migration planning tool
- Undo/redo for migrations

## Contributing

When adding improvements to this skill:

1. Follow PEP 723 pattern for all Python scripts
2. Include path validation in all scripts
3. Provide dry-run mode for destructive operations
4. Document rollback procedure
5. Test on sample data before vault-wide operations
6. Update this IMPROVEMENT_PLAN.md with changes
7. Increment version following semver

## Related

- vault-architect skill - Complementary skill for creating new structures
- pkm-manager agent - Orchestrates both skills
- Plugin version tracking in plugin.json
