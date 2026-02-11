---
name: vault-curator
description: This skill should be used when users ask to "migrate vault notes", "extract meeting from log", "import calendar event", "detect schema drift", "find orphaned notes", or "consolidate Dataview queries". Curates and evolves existing vault content through pattern detection, migration workflows, and programmatic metadata manipulation.
metadata:
  version: "1.0.0"
  plugin: "pkm-plugin"
  stage: "3"
compatibility: Requires python3.11+ and uv for script execution
---

# Vault Curator

## Overview

Provide expert guidance for evolving and improving existing Obsidian vaults. Help users migrate notes, detect patterns, extract meeting information from logs, and maintain vault consistency through programmatic metadata manipulation.

## Core Principles

When curating vaults, prioritize these principles:

1. **Evolution Over Revolution** - Migrate gradually. Test patterns on small batches before vault-wide changes.

2. **Validation Before Execution** - Always run dry-run mode first. Show what would change before changing it.

3. **Rollback Readiness** - Document state before migration. Enable reverting if issues arise.

4. **Pattern Recognition** - Identify existing patterns before suggesting changes. Work with user's mental model, not against it.

5. **Incremental Improvement** - Small, testable changes compound better than large restructuring.

## When to Use This Skill

Use this skill when users ask for help with:

- Extracting meetings from daily note logs or company notes
- Importing calendar events and matching attendees to Person notes
- Migrating existing notes to new frontmatter schemas
- Detecting schema drift (inconsistent metadata patterns)
- Finding orphaned notes or note clusters
- Consolidating Dataview queries to Bases views
- Batch updating frontmatter properties
- Validating migration completeness

## Core Capabilities

### 1. Meeting Extraction from Logs

When asked to extract meeting information from daily notes or inline logs:

**Pattern Recognition:**
- Identify log entries: `### (log::⏱ 14:30 -0500: Meeting with Customer X)`
- Detect inline fields: `scope::`, `start::`, `attendees::`
- Parse headings with dates: `## 2026-02-05`

**Extraction Workflow:**

1. **Parse Selection**
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/extract_section_to_meeting.py \
     ${VAULT_PATH} \
     "${CURRENT_NOTE}" \
     "${SELECTED_TEXT}"
   ```

2. **Infer Metadata**
   - Extract time from log syntax
   - Infer company from current note's folder path
   - Parse inline fields for scope/attendees
   - Detect topic from heading or log text

3. **Prompt for Missing Data**
   - Meeting title (if not in heading)
   - Scope entities (if not in inline fields)
   - Attendees (if not specified)
   - Meeting type (customer-meeting, internal, 1-on-1, etc.)

4. **Create Meeting Note**
   - Use meeting template with pre-filled metadata
   - Place in appropriate folder (from company context)
   - Replace original selection with wikilink

**See:** `references/migration-strategies.md` for extraction patterns

### 2. Calendar Import and Person Matching

When asked to import calendar events:

**Import Workflow:**

1. **Parse Calendar Data**
   - Extract title, datetime, location
   - Parse attendee list (name + email)
   - Identify event type

2. **Match Attendees to Person Notes**
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/match_person_by_email.py \
     ${VAULT_PATH} \
     "email@example.com"
   ```

   Returns Person note path or null if not found.

3. **Infer Company from Attendees**
   - If all attendees from same company → auto-select folder
   - If multiple companies → prompt user for primary
   - Auto-populate scope with all detected companies

4. **Handle Unknown Attendees**
   - Option A: Create minimal Person note (name + email only)
   - Option B: Skip and log for manual creation
   - Option C: Prompt for Person template completion
   - **Default:** Option A (create minimal, enhance later)

5. **Create Meeting Note**
   - Pre-fill all available metadata
   - Prompt only for missing critical fields
   - Link to all Person notes in attendees array

**See:** `references/migration-strategies.md` for calendar import patterns

### 3. Vault Migration Patterns

When asked to migrate existing notes to new schemas:

**Migration Principles:**

1. **Dry-Run First**
   - Show what would change
   - Get user approval before modification
   - Log all planned changes

2. **Batch Validation**
   - Test on 5-10 notes first
   - Verify frontmatter format correct
   - Check Bases queries work with new schema
   - Expand to full vault only after validation

3. **Rollback Strategy**
   - Document original state
   - Create git commit before migration
   - Provide reverse migration script if needed

**Common Migrations:**

**Add scope to existing meetings:**
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/migrate_meetings_scope.py \
  ${VAULT_PATH} \
  --dry-run
```

Infers scope from:
- Folder path (Company/Meetings/ → add Company to scope)
- Existing frontmatter (customer: → add to scope)
- File name patterns (mentions of company/project names)

**Consolidate Dataview to Bases:**
- Identify Dataview callouts: `grep -r "dataviewjs" ${VAULT_PATH}`
- Group by functionality
- Create equivalent Bases views
- Replace occurrences incrementally
- Test each replacement

**See:** `references/migration-strategies.md` for comprehensive migration patterns

### 4. Pattern Detection

When asked to analyze vault for patterns or inconsistencies:

**Find Orphaned Notes:**
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/find_orphans.py ${VAULT_PATH}
```

Returns notes with:
- No inlinks (nothing links to them)
- No outlinks (they link to nothing)
- No frontmatter relationships

**Detect Schema Drift:**
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/detect_schema_drift.py \
  ${VAULT_PATH} \
  --file-class Meeting
```

Reports:
- Missing required properties across fileClass
- Inconsistent property types (string vs array)
- Different naming conventions (camelCase vs kebab-case)
- Recommendations for standardization

**Find Note Clusters:**
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/find_note_clusters.py ${VAULT_PATH}
```

Uses link analysis to identify:
- Groups of highly interconnected notes (potential project clusters)
- Notes that should be linked but aren't
- Opportunities for consolidation

**See:** `references/pattern-detection.md` (placeholder - to be created)

### 5. Programmatic Metadata Manipulation

When asked to bulk update frontmatter:

**Key Patterns:**

1. **Read Frontmatter**
   ```python
   import frontmatter
   with open(note_path) as f:
       post = frontmatter.load(f)
       title = post['title']
       tags = post.get('tags', [])
   ```

2. **Modify Properties**
   ```python
   post['newProperty'] = "value"
   post['tags'].append("new-tag")
   ```

3. **Write Back**
   ```python
   with open(note_path, 'w') as f:
       f.write(frontmatter.dumps(post))
   ```

4. **Batch Processing**
   - Collect all target notes
   - Validate changes on sample
   - Apply to full set with progress tracking
   - Log all modifications

**Safety Checks:**

- Always validate vault path (no system directories)
- Check file exists before modifying
- Preserve frontmatter YAML formatting
- Handle missing properties gracefully
- Log errors without stopping batch

**See:** scripts for reference implementations

## Python Script Patterns

All scripts follow PEP 723 inline metadata pattern:

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

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: script.py <vault-path>"}))
        sys.exit(1)

    vault_path = validate_vault_path(sys.argv[1])

    # Script logic here

    result = {"status": "success", "data": {}}
    print(json.dumps(result))

if __name__ == "__main__":
    main()
```

**Key Requirements:**

1. **PEP 723 Header** - Inline dependencies for uv
2. **Path Validation** - Security check for vault path
3. **JSON Output** - Structured output for parsing
4. **Error Handling** - Graceful failures with error JSON
5. **Type Hints** - Clear function signatures

## Best Practices

### Migration Best Practices

1. **Test Small First**
   - Migrate 5-10 notes as proof of concept
   - Verify Bases queries work with new schema
   - Get user feedback before expanding

2. **Version Control**
   - Create git commit before migration
   - Tag with migration name
   - Document rollback procedure

3. **Progress Tracking**
   - Show progress for long migrations (>100 notes)
   - Log all changes to file
   - Report summary at completion

4. **Validation**
   - Run schema validation after migration
   - Check Bases views render correctly
   - Verify no broken links introduced

### Script Development Best Practices

1. **Security**
   - Always validate vault path
   - Never execute arbitrary code
   - Handle file permissions gracefully

2. **Robustness**
   - Handle missing frontmatter
   - Preserve file formatting
   - Continue on errors (don't stop batch)

3. **Observability**
   - Log to stderr, output to stdout
   - Include --verbose flag for debugging
   - Return structured JSON

4. **Testing**
   - Test with edge cases (missing properties, malformed YAML)
   - Verify on different file classes
   - Check unicode handling

## Common Anti-Patterns to Avoid

1. **Migrating Everything at Once** - Always start small, validate, then expand.

2. **Ignoring Existing Patterns** - Work with user's conventions, don't impose new structure.

3. **No Rollback Plan** - Every migration should be reversible.

4. **Silent Failures** - Always log errors and continue processing batch.

5. **Hardcoded Assumptions** - Make scripts configurable for different vault structures.

6. **Destroying Data** - Preserve original files during migration (copy-modify-replace pattern).

## Examples

### Example 1: Extract meeting from daily note log

**User request:** "Extract this log entry to a meeting note"

**Selected text:**
```markdown
### (log::⏱ 14:30 -0500: Customer sync with Acme)

Discussed Q1 roadmap and feature priorities.

scope:: [[Acme Corp]]
attendees:: [[Alice]], [[Bob]]
```

**Workflow:**
1. Parse selection for metadata
2. Detected: time (14:30), company (Acme), attendees, scope
3. Infer folder from current note path (`Work/Palo Alto Networks/Daily Notes/`)
4. Prompt for meeting type → user selects "customer-meeting"
5. Create `2026-02-10 Customer sync with Acme.md` in `Work/Palo Alto Networks/Meetings/`
6. Replace selection with: `Meeting: [[2026-02-10 Customer sync with Acme]]`

### Example 2: Migrate meetings to add scope

**User request:** "Add scope field to all my meeting notes"

**Workflow:**
1. Run analysis:
   ```bash
   grep -r "fileClass: Meeting" vault/ | wc -l
   # Found 234 meetings
   ```

2. Run dry-run migration:
   ```bash
   uv run scripts/migrate_meetings_scope.py vault/ --dry-run
   ```
   Shows: Would update 234 files, adding scope inferred from folder path

3. Test on 5 meetings:
   ```bash
   uv run scripts/migrate_meetings_scope.py vault/ --limit 5
   ```
   Verify Bases queries work with new scope

4. User approves → run full migration:
   ```bash
   uv run scripts/migrate_meetings_scope.py vault/
   ```

5. Validation:
   - Check all meetings have scope
   - Verify Bases "Related Meetings" view works
   - Create git commit

### Example 3: Find orphaned notes for cleanup

**User request:** "Find notes I'm not using anymore"

**Workflow:**
1. Run orphan detection:
   ```bash
   uv run scripts/find_orphans.py vault/
   ```

2. Results show 23 orphans in categories:
   - 12 old meeting notes (pre-2024)
   - 7 scratch notes with no content
   - 4 project notes for completed projects

3. Recommendations:
   - Archive old meetings to `Archive/` folder
   - Delete scratch notes (or move to `Inbox/` for review)
   - Mark completed projects with `status: archived`

---

When working with users, always run dry-runs and show what would change before making bulk modifications. Every vault has unique patterns - discover them before imposing structure.
