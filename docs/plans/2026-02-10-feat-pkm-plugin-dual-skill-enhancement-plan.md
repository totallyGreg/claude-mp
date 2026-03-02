---
title: "feat: Enhance PKM plugin with dual-skill architecture (vault-architect / vault-curator)"
type: feat
date: 2026-02-10
---

# Enhance PKM Plugin with Dual-Skill Architecture

## Overview

Split pkm-plugin into two focused skills following Single Responsibility Principle: `vault-architect` (creates new PKM structures) and `vault-curator` (improves existing structures). Add documentation references for Obsidian plugins (Templater, Bases, Chronos, Quickadd) and Python scripts for meeting organization workflows.

## Problem Statement

Current `obsidian-pkm-manager` skill is at capacity (486/500 lines) and combines two distinct domains:
- **Creation domain**: Designing templates, Bases queries, vault structure
- **Evolution domain**: Migrating notes, detecting patterns, improving organization

This creates:
- Unclear triggering conditions (too many use cases in one skill)
- Difficulty maintaining as workflows expand
- Violation of YAGNI (would need to add 250+ lines for planned features)

Additionally, meeting notes organization patterns implemented in user's Obsidian vault need to be captured as reusable tooling.

## Proposed Solution

### Architecture Decision

Create two skills with clear separation of concerns:

| Skill | Domain | Trigger Examples | Line Count Target |
|-------|--------|------------------|-------------------|
| **vault-architect** | Creation - Design new structures | "create template", "design Bases query", "set up vault" | 300-400 lines |
| **vault-curator** | Evolution - Improve existing structures | "extract meeting", "migrate notes", "detect patterns" | 250-350 lines |

**Rationale:**
- Each skill stays within skillsmith's 500-line progressive disclosure target
- Clear mental models (architect = build, curator = maintain/improve)
- Follows proven pattern from terminal-guru plugin (terminal-emulation + zsh-dev)
- Better trigger clarity for Claude and users

### Migration Path

**Rename existing skill:**
```bash
mv plugins/pkm-plugin/skills/obsidian-pkm-manager \
   plugins/pkm-plugin/skills/vault-architect
```

**Update references:**
- plugin.json metadata
- agent/pkm-manager.md skill loading paths
- SKILL.md frontmatter (name field)
- marketplace.json entry

**Create new skill:**
```bash
uv run scripts/init_skill.py vault-curator --path plugins/pkm-plugin/skills/
```

## Technical Approach

### Phase 1: Foundation (v1.1.0 - vault-architect)

**Goal:** Add Obsidian plugin documentation references to vault-architect

**Changes:**
1. Rename `obsidian-pkm-manager` → `vault-architect`
2. Update SKILL.md frontmatter:
   ```yaml
   name: vault-architect
   description: This skill should be used when users ask to "create Obsidian templates", "design Bases queries", "set up vault structure", or "configure Templater workflows". Architects new PKM structures and provides guidance for Templater, Bases, Chronos, and Quickadd patterns.
   metadata:
     version: "1.1.0"
   ```
3. Add 4 new reference files to `vault-architect/references/`:
   - `templater-api.md` - Complete Templater API reference with tp.system, tp.file, tp.date, multi-select patterns
   - `bases-query-reference.md` - Bases query syntax, filter expressions, this.file patterns, view types
   - `chronos-syntax.md` - Chronos event syntax, frontmatter integration, timeline patterns
   - `quickadd-patterns.md` - Capture templates, macros, Templater integration
4. Update SKILL.md to reference new documentation (~20 lines added)
5. Keep existing scripts unchanged (analyze_vault.py, validate_frontmatter.py)

**Files affected:**
- `plugins/pkm-plugin/skills/vault-architect/SKILL.md` (rename + update frontmatter + add reference links)
- `plugins/pkm-plugin/skills/vault-architect/references/templater-api.md` (new)
- `plugins/pkm-plugin/skills/vault-architect/references/bases-query-reference.md` (new)
- `plugins/pkm-plugin/skills/vault-architect/references/chronos-syntax.md` (new)
- `plugins/pkm-plugin/skills/vault-architect/references/quickadd-patterns.md` (new)
- `plugins/pkm-plugin/.claude-plugin/plugin.json` (update skill name)
- `plugins/pkm-plugin/agents/pkm-manager.md` (update skill loading path)

**Validation:**
```bash
uv run scripts/evaluate_skill.py plugins/pkm-plugin/skills/vault-architect --quick --strict
```

**Success Criteria:**
- [ ] Skill passes strict validation
- [ ] All 4 reference files created with comprehensive content
- [ ] SKILL.md mentions when to load each reference
- [ ] Skill size remains <500 lines
- [ ] Agent successfully loads renamed skill

### Phase 2: Create Second Skill (v1.0.0 - vault-curator)

**Goal:** Create minimal viable vault-curator skill with one script

**Changes:**
1. Initialize skill:
   ```bash
   uv run scripts/init_skill.py vault-curator --path plugins/pkm-plugin/skills/
   ```
2. Write SKILL.md (250-300 lines):
   ```yaml
   name: vault-curator
   description: This skill should be used when users ask to "migrate vault notes", "extract meeting from log", "import calendar event", "detect schema drift", "find orphaned notes", or "consolidate Dataview queries". Curates and evolves existing vault content through pattern detection and migration workflows.
   metadata:
     version: "1.0.0"
     plugin: "pkm-plugin"
   compatibility: Requires python3.11+ and uv for script execution
   ```
3. Add IMPROVEMENT_PLAN.md for vault-curator
4. Create ONE Python script with PEP 723:
   - `scripts/extract_section_to_meeting.py` - Parse log entry, infer metadata, generate Templater template
5. Add ONE reference file:
   - `references/migration-strategies.md` - Rollback patterns, validation, progress tracking
6. Update agent to load both skills:
   ```markdown
   **Skill Loading:**

   Load ${CLAUDE_PLUGIN_ROOT}/skills/vault-architect/SKILL.md for:
   - Template creation, Bases design, vault setup

   Load ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/SKILL.md for:
   - Meeting extraction, migration, pattern detection
   ```

**Files affected:**
- `plugins/pkm-plugin/skills/vault-curator/SKILL.md` (new)
- `plugins/pkm-plugin/skills/vault-curator/IMPROVEMENT_PLAN.md` (new)
- `plugins/pkm-plugin/skills/vault-curator/scripts/extract_section_to_meeting.py` (new)
- `plugins/pkm-plugin/skills/vault-curator/references/migration-strategies.md` (new)
- `plugins/pkm-plugin/agents/pkm-manager.md` (update to load both skills)
- `plugins/pkm-plugin/.claude-plugin/plugin.json` (add vault-curator to auto-discovery)

**Script Structure (extract_section_to_meeting.py):**
```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
#   "python-frontmatter>=1.0.0",
#   "python-dateutil>=2.8.2",
# ]
# ///

"""
Extract meeting note from daily/company note section.

Usage:
    uv run extract_section_to_meeting.py <vault-path> <note-path> <selection>

Returns:
    JSON with meeting metadata and Templater template path
"""

import sys
import json
from pathlib import Path

def validate_vault_path(vault_path_str: str) -> Path:
    """Validate vault path for security."""
    vault_path = Path(vault_path_str).resolve()
    forbidden = ['/etc', '/var', '/usr', '/bin', '/sbin', '/root']
    if any(str(vault_path).startswith(p) for p in forbidden):
        raise ValueError(f"Access denied: {vault_path}")
    return vault_path

def parse_selection(selection: str) -> dict:
    """Parse selected text for meeting metadata."""
    # TODO: Parse heading, inline fields (scope::, start::)
    # TODO: Infer metadata from context
    return {}

def main():
    vault_path = validate_vault_path(sys.argv[1])
    # TODO: Implementation
    print(json.dumps({"status": "success", "metadata": {}}))

if __name__ == "__main__":
    main()
```

**Validation:**
```bash
uv run scripts/evaluate_skill.py plugins/pkm-plugin/skills/vault-curator --quick --strict
```

**Success Criteria:**
- [ ] Skill passes strict validation
- [ ] SKILL.md clearly describes vault evolution workflows
- [ ] extract_section_to_meeting.py has PEP 723 header
- [ ] Script executes without errors (even if stubbed)
- [ ] migration-strategies.md documents rollback patterns
- [ ] Agent can load both skills independently

### Phase 3: First Command (Proof of Concept)

**Goal:** Create `/extract-meeting` command using hybrid Python + Templater approach

**Changes:**
1. Create `commands/extract-meeting.md`:
   ```yaml
   ---
   name: extract-meeting
   description: Extract selected daily/company note section into structured meeting note
   examples:
     - description: Extract log entry from daily note
       prompt: "Extract this meeting log to a proper meeting note"
     - description: Extract dated section from company note
       prompt: "Convert this section to a meeting note"
   ---

   # Extract Meeting Command

   Extract selected section from daily note or company note into structured meeting note.

   ## Workflow

   1. Get selected text from user
   2. Run extract_section_to_meeting.py to parse metadata
   3. Prompt user for missing fields (scope, attendees, etc.)
   4. Create meeting note using Templater template
   5. Replace selection with link to new meeting note

   ## Implementation

   [Bash script to execute Python + Templater workflow]
   ```

2. Test end-to-end workflow with actual vault

**Files affected:**
- `plugins/pkm-plugin/commands/extract-meeting.md` (new)

**Success Criteria:**
- [ ] Command appears in slash command list
- [ ] Python script executes successfully
- [ ] User receives clear prompts for missing data
- [ ] Meeting note created in correct folder
- [ ] Original selection replaced with wikilink

### Phase 4: Incremental Expansion (Future)

**Remaining scripts to add (as needed):**
- `vault-curator/scripts/import_calendar_event.py` - Parse calendar data, match attendees
- `vault-curator/scripts/migrate_meetings_scope.py` - Batch add scope to existing meetings
- `vault-curator/scripts/match_person_by_email.py` - Find Person note by email field
- `vault-curator/scripts/find_note_clusters.py` - Identify related but disorganized notes
- `vault-curator/scripts/detect_schema_drift.py` - Find inconsistent metadata patterns
- `vault-curator/scripts/find_orphans.py` - Find notes with no connections

**Remaining commands to add (based on usage):**
- `/import-calendar` - Import meeting from calendar event
- `/migrate-meetings` - Batch migrate old meeting notes

**Remaining references to add:**
- `vault-curator/references/pattern-detection.md` - Cluster analysis, orphan finding
- `vault-curator/references/vault-evolution-history.md` - Document transitions (Dataview → Bases, etc.)

## Acceptance Criteria

### Phase 1: vault-architect v1.1.0
- [ ] Skill renamed from obsidian-pkm-manager to vault-architect
- [ ] SKILL.md frontmatter updated with new name and description
- [ ] 4 new reference files added (Templater, Bases, Chronos, Quickadd)
- [ ] Each reference file is comprehensive (500+ lines with examples)
- [ ] SKILL.md references new documentation contextually
- [ ] Skill passes strict validation
- [ ] Agent successfully loads renamed skill
- [ ] Marketplace.json updated

### Phase 2: vault-curator v1.0.0
- [ ] New skill initialized with proper structure
- [ ] SKILL.md describes vault evolution workflows (250-300 lines)
- [ ] extract_section_to_meeting.py created with PEP 723 header
- [ ] Script includes path validation function
- [ ] migration-strategies.md documents rollback patterns
- [ ] IMPROVEMENT_PLAN.md tracks future enhancements
- [ ] Skill passes strict validation
- [ ] Agent loads both skills independently
- [ ] Plugin.json lists both skills in auto-discovery

### Phase 3: First Command
- [ ] /extract-meeting command created
- [ ] Command description includes 2+ usage examples
- [ ] Python script executes successfully
- [ ] Hybrid Python + Templater workflow proven
- [ ] Meeting note created with correct frontmatter
- [ ] Original selection replaced with wikilink
- [ ] Error handling provides clear user feedback

### Overall Quality Gates
- [ ] .gitignore added (exclude .venv/, __pycache__, .local.md)
- [ ] LICENSE file added (MIT)
- [ ] Both skills validated with --strict flag
- [ ] All Python scripts follow PEP 723 pattern
- [ ] pyproject.toml includes all dependencies
- [ ] Plugin version bumped to 1.1.0 in plugin.json
- [ ] All ${CLAUDE_PLUGIN_ROOT} references updated
- [ ] Agent orchestrates both skills correctly

## Dependencies & Prerequisites

**Tooling:**
- uv for Python script execution (already installed)
- skillsmith for skill validation (available in claude-mp)
- plugin-dev:plugin-validator for plugin validation

**User's Vault:**
- Templater plugin installed
- Bases plugin installed
- Chronos Timeline plugin installed
- Quickadd plugin installed (for capture workflows)
- Meeting note structure already implemented (per vault-implementation brainstorm)

## Risk Analysis & Mitigation

### Risk 1: Skill Renaming Breaks Existing Users
**Impact:** Medium - Users invoking "obsidian-pkm-manager" would get skill not found
**Mitigation:**
- Add deprecation notice to marketplace.json
- Update plugin README with migration guide
- Version bump indicates breaking change (1.0.0 → 1.1.0 is minor, but rename is noted)

### Risk 2: Two Skills Create Confusion
**Impact:** Low - Users might not know which skill to use
**Mitigation:**
- Clear trigger phrases in descriptions
- Agent handles skill selection automatically
- SKILL.md of each skill cross-references the other

### Risk 3: Python Script Security (Path Traversal)
**Impact:** High - Scripts could access system files if vault path not validated
**Mitigation:**
- All scripts MUST include validate_vault_path() function
- Forbidden paths: /etc, /var, /usr, /bin, /sbin, /root
- Test with malicious inputs before release

### Risk 4: PEP 723 Dependencies Not Installed
**Impact:** Medium - Scripts fail if dependencies missing
**Mitigation:**
- pyproject.toml includes all dependencies at plugin level
- Skills specify compatibility: "Requires python3.11+ and uv"
- Scripts output clear error if dependencies missing

### Risk 5: Hybrid Python + Templater Coordination Fails
**Impact:** Medium - Command creates partial state (file without link, or link without file)
**Mitigation:**
- Python script validates before creating files
- Templater template uses try/catch for file operations
- Add rollback logic if any step fails
- Log all operations for debugging

## Success Metrics

**Adoption:**
- vault-architect triggered for template/Bases questions
- vault-curator triggered for migration/extraction requests
- /extract-meeting command used successfully

**Quality:**
- Both skills pass strict validation
- No security issues in Python scripts
- Agent successfully orchestrates both skills

**Maintainability:**
- Each skill stays <500 lines
- References loaded progressively as needed
- Scripts follow consistent PEP 723 pattern

## References & Research

### Internal References
- Brainstorm: `plugins/pkm-plugin/docs/brainstorms/2026-02-10-pkm-plugin-enhancement-brainstorm.md`
- Vault implementation: `plugins/pkm-plugin/docs/brainstorms/2026-02-10-meeting-notes-vault-implementation-brainstorm.md`
- Current skill: `plugins/pkm-plugin/skills/obsidian-pkm-manager/SKILL.md`
- Plugin-validator report: Completed validation with 4 warnings (add .gitignore, LICENSE, etc.)
- Institutional learnings: `docs/lessons/plugin-integration-and-architecture.md:246-321`
- Migration patterns: `docs/lessons/skill-to-plugin-migration.md:112-136`

### External References
- Templater docs: https://silentvoid13.github.io/Templater/
- Chronos docs: https://github.com/clairefro/obsidian-plugin-chronos
- Quickadd docs: https://github.com/chhoumann/quickadd
- PEP 723 spec: https://peps.python.org/pep-0723/
- AgentSkills spec: skillsmith references/agentskills_specification.md

### Related Work
- terminal-guru plugin v3.0.0 - Two-skill pattern (terminal-emulation + zsh-dev)
- Plugin-validator recommendations (add .gitignore, LICENSE)
- Python security patterns (path validation from learnings)

## Implementation Notes

**YAGNI Principle Applied:**
- Phase 1-3 are minimal viable implementation
- Phase 4 scripts added only when needed
- Commands added based on actual usage
- URI handlers deferred (mentioned in brainstorm but not essential)

**SOLID Principles:**
- Single Responsibility: Each skill has one clear domain
- Open/Closed: Skills can be extended with references/scripts without modifying core
- Dependency Inversion: Agent depends on skill abstractions, not implementations

**Progressive Disclosure:**
- SKILL.md stays lean (~250-400 lines each)
- Detailed content in references/ (loaded as needed)
- Scripts in scripts/ (executed without loading to context)

**Version Strategy:**
- vault-architect: 1.0.0 → 1.1.0 (minor, adds references)
- vault-curator: Start at 1.0.0 (new skill)
- pkm-plugin: 1.0.0 → 1.1.0 (skill architecture change)

## File Structure Summary

```
plugins/pkm-plugin/
├── .claude-plugin/
│   └── plugin.json (update: version 1.1.0, both skills listed)
├── .gitignore (new)
├── LICENSE (new)
├── agents/
│   └── pkm-manager.md (update: load both skills)
├── skills/
│   ├── vault-architect/ (renamed from obsidian-pkm-manager)
│   │   ├── SKILL.md (update: name, description, references)
│   │   ├── IMPROVEMENT_PLAN.md (update: rename noted)
│   │   ├── references/
│   │   │   ├── bases-patterns.md (existing)
│   │   │   ├── templater-patterns.md (existing)
│   │   │   ├── excalibrain-metadata.md (existing)
│   │   │   ├── folder-structures.md (existing)
│   │   │   ├── templater-api.md (new)
│   │   │   ├── bases-query-reference.md (new)
│   │   │   ├── chronos-syntax.md (new)
│   │   │   └── quickadd-patterns.md (new)
│   │   ├── scripts/
│   │   │   ├── analyze_vault.py (existing)
│   │   │   └── validate_frontmatter.py (existing)
│   │   └── assets/
│   │       └── base-templates/ (existing)
│   └── vault-curator/ (new)
│       ├── SKILL.md (new)
│       ├── IMPROVEMENT_PLAN.md (new)
│       ├── references/
│       │   └── migration-strategies.md (new)
│       └── scripts/
│           └── extract_section_to_meeting.py (new)
└── commands/
    └── extract-meeting.md (new)
```

## Next Steps After Plan Approval

1. **Review plan** - Validate approach with user
2. **Run /workflows:work** - Begin implementation of Phase 1
3. **Validate each phase** - Use strict validation before proceeding
4. **Test with real vault** - Verify workflows end-to-end
5. **Document learnings** - Capture patterns in docs/lessons/
6. **Update marketplace** - Sync changes via marketplace-manager
