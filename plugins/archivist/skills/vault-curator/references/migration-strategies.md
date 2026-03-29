# Migration Strategies Reference

Comprehensive guide for vault migrations, rollback patterns, and validation strategies.

## Table of Contents

1. [Migration Philosophy](#migration-philosophy)
2. [Pre-Migration Checklist](#pre-migration-checklist)
3. [Rollback Patterns](#rollback-patterns)
4. [Dry-Run Implementation](#dry-run-implementation)
5. [Progress Tracking](#progress-tracking)
6. [Validation Strategies](#validation-strategies)
7. [Common Migration Patterns](#common-migration-patterns)
8. [Extraction Patterns](#extraction-patterns)
9. [Calendar Import Patterns](#calendar-import-patterns)
10. [Troubleshooting](#troubleshooting)

## Migration Philosophy

### Core Principles

1. **Evolution, Not Revolution**
   - Migrate incrementally
   - Test on small batches
   - Validate before expanding

2. **Reversibility**
   - Every migration must be reversible
   - Document rollback procedure
   - Create backups before modification

3. **Validation**
   - Dry-run shows intended changes
   - User approval required
   - Post-migration verification

4. **Transparency**
   - Log all changes
   - Report progress
   - Summarize at completion

## Pre-Migration Checklist

Before running any migration:

- [ ] **Backup vault**
  ```bash
  # Git commit
  cd ${VAULT_PATH}
  git add -A
  git commit -m "Pre-migration snapshot: [migration name]"
  git tag pre-migration-$(date +%Y%m%d)

  # Or create backup
  tar -czf vault-backup-$(date +%Y%m%d).tar.gz ${VAULT_PATH}
  ```

- [ ] **Run dry-run**
  - Show what would change
  - Validate output format
  - Check for unexpected modifications

- [ ] **Test on small batch**
  - Select 5-10 representative notes
  - Verify changes are correct
  - Check Bases queries work with new schema

- [ ] **Document rollback procedure**
  - How to revert changes
  - What to verify after rollback
  - When to consider migration failed

- [ ] **Get user approval**
  - Show dry-run results
  - Explain impact
  - Confirm before proceeding

## Rollback Patterns

### Pattern 1: Git-Based Rollback

**Setup:**
```bash
cd ${VAULT_PATH}
git add -A
git commit -m "Pre-migration: Add scope to meetings"
git tag pre-migration-scope
```

**Rollback:**
```bash
git reset --hard pre-migration-scope
```

**Pros:** Clean, complete revert
**Cons:** Requires git, loses any manual changes made after migration

### Pattern 2: Backup-Based Rollback

**Setup:**
```bash
# Create backup with metadata
mkdir -p backups
tar -czf backups/pre-migration-$(date +%Y%m%d-%H%M%S).tar.gz \
  --exclude='backups' \
  ${VAULT_PATH}
```

**Rollback:**
```bash
# Extract backup (will overwrite!)
tar -xzf backups/pre-migration-TIMESTAMP.tar.gz -C /tmp/
cp -r /tmp/vault/* ${VAULT_PATH}/
```

**Pros:** Works without git, preserves full state
**Cons:** Requires disk space, manual restore process

### Pattern 3: Reverse Migration Script

**Migration script creates reverse operations:**

```python
# migrations/add_scope.py
changes = []

for note in notes:
    # Record original state
    changes.append({
        "file": note.path,
        "original": note.frontmatter.copy()
    })

    # Apply migration
    note.frontmatter['scope'] = infer_scope(note)
    note.save()

# Save changes log
with open('migration-log.json', 'w') as f:
    json.dump(changes, f)
```

**Rollback script:**

```python
# migrations/rollback_add_scope.py
with open('migration-log.json') as f:
    changes = json.load(f)

for change in changes:
    note = load_note(change['file'])
    note.frontmatter = change['original']
    note.save()
```

**Pros:** Precise rollback, restores exact state
**Cons:** Requires writing rollback script

## Dry-Run Implementation

### Basic Dry-Run Pattern

```python
def migrate_add_scope(vault_path: Path, dry_run: bool = False):
    """
    Add scope field to meeting notes.

    Args:
        vault_path: Path to vault
        dry_run: If True, only show what would change
    """
    notes = find_meetings(vault_path)
    changes = []

    for note in notes:
        scope = infer_scope_from_path(note.path)

        if dry_run:
            changes.append({
                "file": note.path,
                "action": "add",
                "field": "scope",
                "value": scope
            })
        else:
            note.frontmatter['scope'] = scope
            note.save()

    if dry_run:
        print(json.dumps({
            "status": "dry-run",
            "changes": changes,
            "count": len(changes)
        }, indent=2))
    else:
        print(json.dumps({
            "status": "success",
            "migrated": len(notes)
        }))
```

**Usage:**
```bash
# See what would change
uv run add_scope.py vault/ --dry-run

# Apply changes
uv run add_scope.py vault/
```

### Detailed Dry-Run Output

```python
def format_dry_run_change(change: Dict) -> str:
    """Format dry-run change for display."""
    file = change['file']
    action = change['action']
    field = change['field']
    value = change['value']

    return f"""
File: {file}
Action: {action}
Field: {field}
Value: {value}
---"""

# In main()
if dry_run:
    print("=== DRY RUN ===")
    print(f"Would modify {len(changes)} files:\n")

    for change in changes[:10]:  # Show first 10
        print(format_dry_run_change(change))

    if len(changes) > 10:
        print(f"\n... and {len(changes) - 10} more files")

    print(f"\nTotal changes: {len(changes)}")
    print("Run without --dry-run to apply changes")
```

## Progress Tracking

### Console Progress Bar

```python
def migrate_with_progress(notes: List[Note]):
    """Migrate with progress tracking."""
    total = len(notes)

    for i, note in enumerate(notes, 1):
        # Perform migration
        migrate_note(note)

        # Update progress
        percent = (i / total) * 100
        bar_length = 40
        filled = int(bar_length * i / total)
        bar = '█' * filled + '-' * (bar_length - filled)

        print(f'\rProgress: |{bar}| {percent:.1f}% ({i}/{total})', end='')

    print()  # New line after completion
```

### File-Based Progress Log

```python
def migrate_with_logging(notes: List[Note], log_file: Path):
    """Migrate with file logging."""
    with open(log_file, 'w') as log:
        log.write(f"Migration started: {datetime.now()}\n")
        log.write(f"Total notes: {len(notes)}\n\n")

        for i, note in enumerate(notes, 1):
            try:
                migrate_note(note)
                log.write(f"[OK] {note.path}\n")
            except Exception as e:
                log.write(f"[ERROR] {note.path}: {e}\n")

        log.write(f"\nMigration completed: {datetime.now()}\n")
```

### JSON Progress Report

```python
def migration_summary(results: List[Dict]) -> Dict:
    """Generate migration summary."""
    success = [r for r in results if r['status'] == 'success']
    errors = [r for r in results if r['status'] == 'error']

    return {
        "total": len(results),
        "success": len(success),
        "errors": len(errors),
        "error_details": errors,
        "completion_time": datetime.now().isoformat()
    }
```

## Validation Strategies

### Pre-Migration Validation

```python
def validate_before_migration(notes: List[Note]) -> bool:
    """Validate notes are ready for migration."""
    issues = []

    for note in notes:
        # Check frontmatter is valid YAML
        if not note.has_valid_frontmatter():
            issues.append(f"{note.path}: Invalid YAML")

        # Check required fields exist
        if not note.has_field('fileClass'):
            issues.append(f"{note.path}: Missing fileClass")

    if issues:
        print("Validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    return True
```

### Post-Migration Validation

```python
def validate_after_migration(vault_path: Path) -> Dict:
    """Validate migration completed correctly."""
    results = {
        "all_have_scope": True,
        "scope_format_correct": True,
        "bases_queries_work": True,
        "issues": []
    }

    meetings = find_meetings(vault_path)

    # Check all have scope
    for meeting in meetings:
        if 'scope' not in meeting.frontmatter:
            results['all_have_scope'] = False
            results['issues'].append(f"{meeting.path}: Missing scope")

        # Check scope is array of wikilinks
        scope = meeting.frontmatter.get('scope', [])
        if not isinstance(scope, list):
            results['scope_format_correct'] = False
            results['issues'].append(f"{meeting.path}: scope not array")

    # Test Bases query
    # (Would need to actually query Bases here)

    return results
```

## Common Migration Patterns

### Pattern 1: Add Missing Field

```python
def add_field_with_default(
    notes: List[Note],
    field: str,
    default_value: Any,
    dry_run: bool = False
) -> Dict:
    """Add field to notes that are missing it."""
    changes = []

    for note in notes:
        if field not in note.frontmatter:
            if dry_run:
                changes.append({
                    "file": note.path,
                    "action": "add",
                    "field": field,
                    "value": default_value
                })
            else:
                note.frontmatter[field] = default_value
                note.save()
                changes.append(note.path)

    return {
        "status": "dry-run" if dry_run else "success",
        "modified": len(changes),
        "changes": changes
    }
```

### Pattern 2: Rename Field

```python
def rename_field(
    notes: List[Note],
    old_name: str,
    new_name: str,
    dry_run: bool = False
) -> Dict:
    """Rename field across notes."""
    changes = []

    for note in notes:
        if old_name in note.frontmatter:
            value = note.frontmatter[old_name]

            if dry_run:
                changes.append({
                    "file": note.path,
                    "action": "rename",
                    "from": old_name,
                    "to": new_name,
                    "value": value
                })
            else:
                del note.frontmatter[old_name]
                note.frontmatter[new_name] = value
                note.save()
                changes.append(note.path)

    return {"modified": len(changes), "changes": changes}
```

### Pattern 3: Transform Field Value

```python
def transform_field(
    notes: List[Note],
    field: str,
    transform_fn: callable,
    dry_run: bool = False
) -> Dict:
    """Apply transformation to field values."""
    changes = []

    for note in notes:
        if field in note.frontmatter:
            old_value = note.frontmatter[field]
            new_value = transform_fn(old_value)

            if old_value != new_value:
                if dry_run:
                    changes.append({
                        "file": note.path,
                        "field": field,
                        "old": old_value,
                        "new": new_value
                    })
                else:
                    note.frontmatter[field] = new_value
                    note.save()
                    changes.append(note.path)

    return {"modified": len(changes), "changes": changes}

# Example transformation functions
def normalize_tag(tag: str) -> str:
    """Normalize tag to lowercase singular."""
    return tag.lower().rstrip('s')

def wikilink_array(value: str) -> List[str]:
    """Convert comma-separated string to wikilink array."""
    items = [item.strip() for item in value.split(',')]
    return [f"[[{item}]]" for item in items]
```

## Extraction Patterns

### Meeting Extraction from Daily Notes

**Input patterns:**
```markdown
### (log::⏱ 14:30 -0500: Customer sync with Acme)

Discussed roadmap priorities.

scope:: [[Acme Corp]], [[Project Alpha]]
attendees:: [[Alice]], [[Bob]]
```

**Extraction logic:**

```python
def extract_meeting_from_log(
    vault_path: Path,
    daily_note_path: Path,
    selection: str
) -> Dict:
    """Extract meeting note from daily note log entry."""

    # 1. Parse log syntax
    log_pattern = r'###\s*\(log::⏱\s*(\d{1,2}:\d{2})\s*([-+]\d{4})?:\s*(.+?)\)'
    match = re.search(log_pattern, selection)

    if not match:
        return {"error": "Not a valid log entry"}

    time = match.group(1)
    timezone = match.group(2) or ""
    title = match.group(3).strip()

    # 2. Extract date from daily note filename
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', daily_note_path.name)
    date = date_match.group(1) if date_match else None

    # 3. Parse inline fields
    inline_fields = {}
    field_pattern = r'(\w+)::\s*(.+?)(?:\n|$)'
    for match in re.finditer(field_pattern, selection):
        field = match.group(1)
        value = match.group(2).strip()
        inline_fields[field] = parse_wikilinks(value)

    # 4. Infer company from daily note path
    company = infer_company_from_path(daily_note_path)

    # 5. Combine datetime
    start = f"{date}T{time}:00{timezone}" if date and time else None

    return {
        "title": title,
        "start": start,
        "scope": inline_fields.get('scope', [f"[[{company}]]"] if company else []),
        "attendees": inline_fields.get('attendees', []),
        "company": company,
        "folder": f"{company}/Meetings" if company else "Meetings"
    }
```

## Calendar Import Patterns

### iCal/Google Calendar Import

**Input:** Calendar event with attendees

```python
def import_calendar_event(
    vault_path: Path,
    event_data: Dict
) -> Dict:
    """
    Import calendar event as meeting note.

    Args:
        event_data: {
            "summary": "Q1 Planning",
            "start": "2026-02-10T14:00:00Z",
            "end": "2026-02-10T15:30:00Z",
            "location": "Conference Room A",
            "attendees": [
                {"name": "Alice", "email": "alice@example.com"},
                {"name": "Bob", "email": "bob@example.com"}
            ]
        }

    Returns:
        Meeting metadata dict
    """

    # 1. Match attendees to Person notes by email
    matched_attendees = []
    unknown_attendees = []

    for attendee in event_data['attendees']:
        person = match_person_by_email(vault_path, attendee['email'])

        if person:
            matched_attendees.append(f"[[{person.name}]]")
        else:
            unknown_attendees.append(attendee)

    # 2. Infer company from attendees' employers
    companies = set()
    for attendee_link in matched_attendees:
        person = load_person(vault_path, attendee_link)
        if person.employer:
            companies.add(person.employer)

    # 3. Determine primary company
    if len(companies) == 1:
        primary_company = list(companies)[0]
    elif len(companies) > 1:
        # Prompt user to select
        primary_company = None  # Would prompt here
    else:
        primary_company = None

    # 4. Create minimal Person notes for unknowns
    for attendee in unknown_attendees:
        create_minimal_person(
            vault_path,
            name=attendee['name'],
            email=attendee['email']
        )
        matched_attendees.append(f"[[{attendee['name']}]]")

    return {
        "title": event_data['summary'],
        "start": event_data['start'],
        "end": event_data['end'],
        "location": event_data.get('location'),
        "attendees": matched_attendees,
        "scope": [f"[[{c}]]" for c in companies],
        "company": primary_company,
        "folder": f"{primary_company}/Meetings" if primary_company else "Meetings",
        "unknown_attendees": unknown_attendees
    }
```

## Troubleshooting

### Migration doesn't complete

**Symptoms:** Script stops mid-migration, incomplete changes

**Causes:**
- Exception in migration logic
- Invalid YAML in frontmatter
- File permission issues

**Solutions:**
- Add try/except around individual note processing
- Continue on errors, log failures
- Validate frontmatter before migration

### Rollback fails

**Symptoms:** Can't revert to pre-migration state

**Causes:**
- No backup created
- Git not initialized
- Manual changes after migration

**Solutions:**
- Always create backup before migration
- Use git tags for clean restore points
- Document rollback procedure in migration script

### Schema validation fails post-migration

**Symptoms:** Not all notes have expected fields

**Causes:**
- Migration logic missed edge cases
- Some notes excluded from batch
- Frontmatter parsing failed

**Solutions:**
- Run validation on small batch first
- Log all skipped notes
- Re-run migration on failed notes only

## References

- **Python frontmatter:** https://pypi.org/project/python-frontmatter/
- **PEP 723 (inline metadata):** https://peps.python.org/pep-0723/
- **Obsidian frontmatter:** https://help.obsidian.md/Editing+and+formatting/Properties
