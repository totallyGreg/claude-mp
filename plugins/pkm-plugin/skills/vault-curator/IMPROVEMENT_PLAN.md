# Vault Curator - Improvement Plan

## Current Version: 1.4.0

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.4.0 | 2026-02-16 | Discovery workflows: find_related.py, progressive discovery views, auto-linking suggestions. SKILL.md + pkm-manager agent updated |
| 1.3.0 | 2026-02-16 | Consolidation workflows: find_similar_notes.py, merge_notes.py, redirect_links.py, consolidation-protocol.md reference. Skillsmith eval: 89/100 |
| 1.2.0 | 2026-02-15 | Scope selection, metadata workflows (suggest_properties.py, detect_schema_drift.py), SKILL.md restructure, pkm-manager agent CLI integration |
| 1.0.0 | 2026-02-10 | Initial release with meeting extraction, migration patterns, and pattern detection workflows |

## Planned Improvements

| Issue | Priority | Title | Status |
|-------|----------|-------|--------|
| [#44](https://github.com/totallyGreg/claude-mp/issues/44) | High | Foundation + Metadata Workflows (Phase 1) | Done |
| [#45](https://github.com/totallyGreg/claude-mp/issues/45) | High | Consolidation Workflows (Phase 2) | Done |
| [#46](https://github.com/totallyGreg/claude-mp/issues/46) | Medium | Discovery Workflows (Phase 3) | Done |
| [#47](https://github.com/totallyGreg/claude-mp/issues/47) | Medium | Visualization Workflows (Phase 4) | Planning |
| — | High | Phase 4 Scripts (original): import_calendar_event.py, migrate_meetings_scope.py, match_person_by_email.py, find_orphans.py | Planned |
| — | Medium | Slash Commands: /extract-meeting, /import-calendar, /migrate-meetings | Planned |
| — | Medium | Test Suite: pytest tests for Python scripts | Planned |
| — | Low | Consolidate Dataview Script | Planned |

## Completed Improvements

| Version | Date | Key Changes |
|---------|------|-------------|
| 1.0.0 | 2026-02-10 | - SKILL.md with vault evolution workflows (449 lines) - extract_section_to_meeting.py with PEP 723 - migration-strategies.md reference - Path validation + JSON outputs |

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

## Related

- vault-architect skill - Complementary skill for creating new structures
- pkm-manager agent - Orchestrates both skills
- Plan: `docs/plans/2026-02-15-feat-vault-curator-cli-intelligence-workflows-plan.md`
- Brainstorm: `docs/brainstorms/2026-02-15-pkm-plugin-cli-integration-brainstorm.md`
