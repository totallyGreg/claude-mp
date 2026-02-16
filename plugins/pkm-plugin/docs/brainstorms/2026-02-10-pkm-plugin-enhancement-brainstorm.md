---
date: 2026-02-10
topic: pkm-plugin-enhancement
status: planning
relates-to: 2026-02-10-meeting-notes-vault-implementation-brainstorm.md
---

# PKM Plugin Enhancement: Capturing Meeting Organization Patterns

## Context

After implementing a meeting notes organization system in my Obsidian vault (see [meeting-notes-vault-implementation-brainstorm.md](2026-02-10-meeting-notes-vault-implementation-brainstorm.md)), I want to capture those patterns, workflows, and tooling in my pkm-plugin so they're reusable and can guide future vault improvements.

## Goal

Enhance pkm-plugin to:
1. Document Obsidian plugin patterns (Templater, Bases, Chronos) in skill references
2. Provide Python scripts for common operations (meeting extraction, calendar import, person matching)
3. Expose operations via slash commands
4. Enable pattern-based vault evolution and migration

## Plugin Directory Structure

```
pkm-plugin/
├── agents/
│   └── pkm-manager.md          # Existing: Orchestrator agent
├── skills/
│   ├── obsidian-pkm-manager/   # Existing: Template creation, Bases design
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── analyze_vault.py
│   │   │   └── validate_frontmatter.py
│   │   └── references/
│   │       ├── bases-patterns.md
│   │       ├── templater-patterns.md
│   │       ├── excalibrain-metadata.md
│   │       └── folder-structures.md
│   └── pkm-organization-patterns/  # NEW: Evolution & migration patterns
│       ├── SKILL.md
│       ├── scripts/
│       │   ├── extract_section_to_meeting.py
│       │   ├── import_calendar_event.py
│       │   ├── migrate_meetings_scope.py
│       │   ├── match_person_by_email.py
│       │   ├── find_note_clusters.py
│       │   ├── detect_schema_drift.py
│       │   └── consolidate_dataviewjs.py
│       └── references/
│           ├── vault-evolution-history.md
│           ├── migration-strategies.md
│           └── pattern-detection.md
└── commands/
    ├── extract-meeting.md      # NEW: User-invokable slash command
    ├── import-calendar.md      # NEW
    ├── migrate-meetings.md     # NEW
    └── uri-handlers/           # NEW: Simple URI commands
        ├── quick-meeting.js
        ├── extract-selection.js
        └── import-clipboard.js
```

## New Skill: pkm-organization-patterns

**Purpose:** Capture knowledge about PKM system evolution, migration strategies, and pattern recognition.

**Core Capabilities:**

1. **Vault Evolution Tracking**
   - Document transitions (Dataview → Bases, folder reorganization)
   - Capture rationale for changes in `docs/vault-evolution/`
   - Track what worked vs. what didn't

2. **Migration Pattern Library**
   - Reusable scripts for common migrations
   - Validation patterns (verify migration success)
   - Rollback strategies
   - Migration tracking (progress reports for long-running migrations)

3. **Pattern Detection**
   - Identify clusters of related-but-disorganized notes
   - Detect inconsistent metadata patterns
   - Suggest consolidation opportunities
   - Find orphaned notes

4. **Programmatic Metadata Manipulation**
   - Obsidian API patterns for frontmatter updates
   - Batch operations with safety checks
   - Metadata inference from content/context

## Command Architecture

**Two types of commands:**

1. **URI Commands** (Simple, callable from anywhere)
   - Single-purpose actions
   - Invokable from Obsidian links, OmniFocus, Raycast, etc.
   - Use `obsidian://pkm-plugin/<command>?params`
   - Examples:
     - `obsidian://pkm-plugin/quick-meeting?title=Customer%20Sync&scope=Palo%20Alto%20Networks`
     - `obsidian://pkm-plugin/extract-selection`
     - `obsidian://pkm-plugin/import-clipboard`

2. **Slash Commands** (Complex, multi-step)
   - `/extract-meeting` - Interactive prompts for metadata, extract section to meeting note
   - `/import-calendar` - Attendee matching, folder inference, create from calendar event
   - `/migrate-meetings` - Batch analysis and updates for existing meeting notes

## Python Script Pattern (PEP 723)

All Python scripts use inline script metadata (PEP 723) and are invoked via `uv run`:

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
Script description and usage.

Usage:
    uv run script_name.py <vault-path> <args>

Returns:
    JSON output for consumption by commands/agent
"""
```

**Benefits:**
- Self-contained dependencies
- No separate requirements.txt needed
- Easy to run and test
- Consistent with modern Python practices

## Command Implementation Pattern

**Hybrid Python + JavaScript approach for flexibility:**

1. **Python scripts** - Analysis and logic
   - Parse selections from notes
   - Infer metadata from context
   - Match entities (e.g., email → Person notes)
   - Generate Templater templates dynamically

2. **JavaScript/Templater** - Vault operations
   - Update frontmatter via Obsidian API
   - Create/move/rename files
   - Prompt user for input
   - Execute generated templates

**Example Flow** (Extract Meeting command):
```
1. User selects section, runs /extract-meeting
2. Python: Parse selection, infer scope from note context
3. Python: Generate Templater template with prompts for missing fields
4. JavaScript: Execute template (show prompts + create file)
5. JavaScript: Replace selection with link to new meeting note
6. Python: Clean up temporary template file
```

**Example Flow** (Import Calendar):
```
1. User runs /import-calendar (with clipboard data)
2. Python: Parse calendar event (title, time, attendees, location)
3. Python: Match attendee emails to Person notes
4. Python: Infer folder from attendees' employers
5. Python: Generate Templater template with pre-filled data
6. JavaScript: Execute template (prompt for missing data)
7. JavaScript: Create meeting note in correct folder
8. JavaScript: Open new note
```

## Division of Responsibilities

| Capability | obsidian-pkm-manager | pkm-organization-patterns |
|------------|---------------------|--------------------------|
| Template creation | ✅ Primary | Support |
| Bases query design | ✅ Primary | Support |
| Vault analysis | Basic structure | ✅ Deep pattern detection |
| Migration scripts | — | ✅ Primary |
| Evolution tracking | — | ✅ Primary |
| Frontmatter schema | ✅ Design | ✅ Validation & updates |
| Obsidian API usage | Templates | ✅ Programmatic manipulation |

**Rationale:** Keep concerns separated. `obsidian-pkm-manager` focuses on creating new structures (templates, Bases), while `pkm-organization-patterns` focuses on analyzing and improving existing structures.

## Key Scripts to Implement

**Meeting Organization:**
- `extract_section_to_meeting.py` - Parse log entry, infer metadata, create meeting note
- `import_calendar_event.py` - Parse calendar data, match attendees, create note
- `migrate_meetings_scope.py` - Batch add scope to existing meetings
- `match_person_by_email.py` - Find Person note by email field lookup

**Pattern Detection:**
- `find_note_clusters.py` - Identify related but disorganized notes using link analysis
- `detect_schema_drift.py` - Find inconsistent metadata across same file class
- `consolidate_dataviewjs.py` - Replace Dataview callouts with Bases views
- `find_orphans.py` - Find notes with no connections

**Validation:**
- `verify_bases_queries.py` - Test all .base files work correctly
- `validate_migration.py` - Check migration completeness

## Implementation Workflow

**When implementing this plugin enhancement:**

1. **Use skillsmith** - Create/update skills following marketplace workflow
2. **Validate changes** - Test scripts, validate skill quality
3. **Version appropriately** - Follow semantic versioning
4. **Update docs** - Document new commands and workflows
5. **Publish to marketplace** - Follow marketplace sync process

**For this brainstorm:** Design is captured here for future implementation. Do not directly edit plugin files in marketplace cache.

## Plugin Documentation References

**To be added to `obsidian-pkm-manager/references/`:**

1. **Templater Documentation**
   - `templater-api.md` - Complete API reference
   - Internal functions: `tp.system`, `tp.file`, `tp.date`, etc.
   - User functions and execution contexts
   - Multi-select patterns (like the scope/attendees workflow)
   - Official docs: https://silentvoid13.github.io/Templater/

2. **Bases Documentation**
   - `bases-query-reference.md` - Complete query syntax
   - Filter expressions, property references, formulas
   - View types (table, cards, chronos-timeline-view)
   - `this.file` context patterns
   - Grouping, sorting, column sizing
   - Official docs: (Bases plugin documentation)

3. **Chronos Timeline Documentation**
   - `chronos-syntax.md` - Event syntax and frontmatter integration
   - Event types: events (`-`), periods (`@`), points (`*`), markers (`=`)
   - Color and grouping syntax
   - Date formats and ranges
   - Bases integration for chronos-timeline-view
   - Official docs: https://github.com/clairefro/obsidian-plugin-chronos

4. **Quickadd Documentation**
   - `quickadd-patterns.md` - Capture templates and macros
   - Template choice configurations
   - Macro scripts
   - Integration with Templater
   - Official docs: https://github.com/chhoumann/quickadd

5. **Other Frequently Used Plugins**
   - `excalibrain-metadata.md` - Already exists (semantic relationships)
   - `dataview-reference.md` - For migration and compatibility (even though moving to Bases)
   - Natural Language Dates - For date parsing in templates
   - Any other plugins used for vault organization

6. **External Tools Integration**
   - `obsidian-nvim-reference.md` - obsidian-nvim/obsidian.nvim plugin patterns
     - Neovim integration for vault editing
     - Command patterns and workflows
     - Potential for CLI automation via nvim headless mode
     - Official docs: https://github.com/epwalsh/obsidian.nvim

   - `markdown-oxide-lsp.md` - markdown-oxide LSP capabilities
     - LSP features for markdown/Obsidian vaults
     - Symbol indexing and navigation
     - Potential for programmatic vault querying via LSP
     - Cross-reference resolution
     - Official docs: https://github.com/Feel-ix-343/markdown-oxide

**Reusable Template Utilities to Provide:**

Based on the meeting template implementation, the pkm-plugin should provide reusable utilities:

```javascript
// Common patterns to extract into plugin utilities
pkm.getNotesOfType(fileClass) // Get all notes with specific fileClass
pkm.getNotesInFolder(path) // Get notes in folder
pkm.multiSelectSuggester(options, prompt) // Multi-select workflow
pkm.formatYamlList(items, wikilinks=true) // Format proper YAML list
pkm.getCurrentContext() // Get context from current note (for scope inference)
pkm.matchPersonByEmail(email) // Find Person note by email
```

These utilities should be available to all templates and reduce boilerplate.

**Potential Use Cases for External Tools:**

**obsidian-nvim:**
- Headless vault operations via `nvim --headless`
- Batch editing with Neovim scripts
- Template rendering from CLI
- Integration with existing shell workflows

**markdown-oxide LSP:**
- Vault-wide symbol search via LSP protocol
- Fast reference/backlink resolution
- Potential for Python scripts to query vault via LSP client
- Index-based note discovery (faster than file scanning)
- Type-aware note suggestions

**Future Research:**
- Can markdown-oxide LSP provide faster vault queries than Python file scanning?
- Can obsidian-nvim be used for headless template execution?
- Integration patterns between pkm-plugin scripts and these tools
- Performance comparisons for different vault query approaches

## Deferred Features

### Canvas Integration

**Deferred for now, but noted:**
- Parse connections from Canvas documents
- Generate Canvas as top-level maps of content
- Replace Excalibrain reliance on inline fields

### Dataview to Bases Migration

**Deferred for now, but noted:**
- Identify remaining Dataview JavaScript callouts
- Group by functionality
- Create equivalent Bases views
- Replace occurrences systematically

**Note:** Inline fields still useful where Bases doesn't support them (yet?)

## Next Steps

### Immediate: Create Implementation Plan

Using `/workflows:plan`:

1. **Decide plugin architecture** — New skill vs. extend existing?
2. **Identify v1.0.0 scope** — What's essential vs. nice-to-have?
3. **Design error handling** — Path validation, security, user feedback
4. **Choose implementation approach** — YAGNI-first or comprehensive?

### Then: Incremental Implementation

Following terminal-guru migration pattern:

1. Add documentation references to existing skill
2. Create first Python script (minimal, tested)
3. Build first command (prove hybrid approach works)
4. Iterate based on usage
5. Extract new skill if clear separation emerges

### Later: Migration & Enhancement

After core workflows work:

1. Build migration scripts with rollback
2. Add remaining commands as needed
3. Document patterns learned
4. Consider Canvas/Dataview migrations if value is proven
