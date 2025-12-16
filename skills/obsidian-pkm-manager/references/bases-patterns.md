# Bases Query Patterns

This document provides common Bases query patterns and examples for creating dynamic relationship views in Obsidian.

## Bases File Structure

A `.base` file is YAML-formatted with three main sections:

```yaml
formulas:
  FormulaName: calculation or transformation

properties:
  property.path:
    displayName: Human Readable Name

views:
  - type: table
    name: View Name
    filters:
      # Query logic
    order:
      # Column order
    sort:
      # Sort criteria
    columnSize:
      # Column widths
    rowHeight: small|medium|tall
```

## Core Concepts

### Properties

Properties define which data fields can be displayed in views:

```yaml
properties:
  file.name:
    displayName: Note Title
  file.tags:
    displayName: Tags
  file.links:
    displayName: Linked Notes
  file.backlinks:
    displayName: Mentioned In
  file.folder:
    displayName: Folder
  file.ctime:
    displayName: Created
  file.mtime:
    displayName: Modified
  note.summary:
    displayName: Summary
  note.customer:
    displayName: Customer
```

### Formulas

Formulas create calculated values:

```yaml
formulas:
  # Get all files that link to this note
  Mentioned In: file.backlinks.map(value.asFile())

  # Count backlinks
  Link Count: file.backlinks.length

  # Extract first tag
  Primary Tag: file.tags[0]

  # Format date
  Created Date: file.ctime.toFormat("yyyy-MM-dd")
```

### Filters

Filters determine which notes appear in a view.

**Basic Filters:**

```yaml
filters:
  # Single condition
  file.tags.contains("meeting")

  # Multiple AND conditions
  and:
    - file.tags.contains("meeting")
    - file.folder.startsWith("Work")

  # Multiple OR conditions
  or:
    - file.tags.contains("meeting")
    - file.tags.contains("note")

  # Combined AND/OR
  and:
    - or:
        - file.tags.contains("meeting")
        - file.tags.contains("note")
    - file.folder.startsWith("Work")
```

**Common Filter Patterns:**

```yaml
# Notes with specific tag
file.tags.contains("term")

# Notes in folder (exact)
file.folder == "700 Notes/Terminology"

# Notes in folder (starts with)
file.folder.startsWith("700 Notes")

# Notes with any of multiple tags
or:
  - file.tags.contains("meeting")
  - file.tags.contains("call")

# Notes linking to current note
file.hasLink(this.file)

# Notes with matching alias
aliases == [this.file.name]

# Notes created this week (requires date comparison)
file.ctime >= startOf('week')

# Notes in folder OR with tag (flexible categorization)
or:
  - file.folder.containsAny("Meetings")
  - file.tags.contains("meeting")
```

### Sort

Sort criteria determine display order:

```yaml
sort:
  # Single sort
  - property: file.name
    direction: ASC

  # Multiple sorts (priority order)
  - property: file.tags
    direction: DESC
  - property: file.name
    direction: ASC

  # By formula
  - property: formula.Link Count
    direction: DESC
```

## Common Query Patterns

### Pattern 1: Related Files (Backlinks)

Shows all notes that link to the current note:

```yaml
formulas:
  Mentioned In: file.backlinks.map(value.asFile())

properties:
  file.name:
    displayName: Note
  file.tags:
    displayName: Tags
  file.ctime:
    displayName: Created

views:
  - type: table
    name: Related Files
    filters:
      file.hasLink(this.file)
    order:
      - file.name
      - file.tags
      - file.ctime
    sort:
      - property: file.ctime
        direction: DESC
    rowHeight: medium
```

**Usage in note:**
```markdown
## Related Notes
![[Notes.base#Related Files]]
```

### Pattern 2: Terminology Aggregation (Alias Matching)

Shows all terms that share the same abbreviation:

```yaml
formulas:
  Mentioned In: file.backlinks.map(value.asFile())

properties:
  file.name:
    displayName: Term
  note.summary:
    displayName: Summary
  file.links:
    displayName: Context
  file.backlinks:
    displayName: Used In

views:
  - type: table
    name: Terms with Context
    filters:
      and:
        - aliases == [this.file.name]
        - file.path.startsWith("700 Notes")
    order:
      - file.name
      - summary
      - file.backlinks
      - file.links
    sort:
      - property: file.links
        direction: DESC
    columnSize:
      file.name: 200
      note.summary: 600
    rowHeight: tall
```

**How it works:**
- Abbreviation note named "API"
- Term notes have `aliases: [API]` in frontmatter
- Query shows all terms with "API" as alias
- Each term displays its summary and context links

### Pattern 3: Temporal Rollup (This Week's Notes)

Shows all daily notes from the current week:

```yaml
properties:
  file.name:
    displayName: Day
  note.wins:
    displayName: Wins
  note.challenges:
    displayName: Challenges
  file.links:
    displayName: Activities

views:
  - type: table
    name: This Week
    filters:
      and:
        - file.tags.contains("daily")
        - Week == [this.file.link]
    order:
      - file.name
      - wins
      - challenges
      - file.links
    sort:
      - property: file.name
        direction: ASC
    rowHeight: medium
```

**Requirements:**
- Daily notes have `Week: "[[2025-W50]]"` in frontmatter
- Weekly note is named "2025-W50"
- Query matches on the Week property

### Pattern 4: Customer Meetings View

Shows all meetings for a specific customer:

```yaml
properties:
  file.name:
    displayName: Meeting
  file.ctime:
    displayName: Date
  note.attendees:
    displayName: Attendees
  file.tags:
    displayName: Type

views:
  - type: table
    name: Company Meetings
    filters:
      and:
        - file.tags.contains("meeting")
        - customer == [this.file.link]
    order:
      - file.name
      - file.ctime
      - attendees
    sort:
      - property: file.ctime
        direction: DESC
    rowHeight: medium
```

**Usage:**
- Company note: `[[Acme Corp]]`
- Meeting notes have: `customer: [[Acme Corp]]`
- Embedded in company note: `![[Notes.base#Company Meetings]]`

### Pattern 5: Untagged Notes (Maintenance)

Shows notes that need categorization:

```yaml
views:
  - type: table
    name: Untagged Notes
    filters:
      and:
        - file.tags.length == 0
        - file.folder.startsWith("700 Notes")
        - not:
            file.name.startsWith("_")
    order:
      - file.name
      - file.ctime
      - file.folder
    sort:
      - property: file.ctime
        direction: DESC
```

### Pattern 6: Project Dashboard

Shows all notes related to a project:

```yaml
formulas:
  Type: |
    if (file.tags.contains("meeting")) "Meeting"
    else if (file.tags.contains("task")) "Task"
    else "Note"

properties:
  file.name:
    displayName: Item
  formula.Type:
    displayName: Type
  file.ctime:
    displayName: Created

views:
  - type: table
    name: Project Items
    filters:
      or:
        - project == [this.file.link]
        - file.hasLink(this.file)
    order:
      - file.name
      - Type
      - file.ctime
    sort:
      - property: formula.Type
        direction: ASC
      - property: file.ctime
        direction: DESC
    groupBy: formula.Type
```

### Pattern 7: Recent Activity

Shows recently modified notes in a folder:

```yaml
views:
  - type: table
    name: Recent Activity
    filters:
      and:
        - file.folder.startsWith("700 Notes")
        - file.mtime >= ago(7 days)
    order:
      - file.name
      - file.mtime
      - file.tags
    sort:
      - property: file.mtime
        direction: DESC
    columnSize:
      file.name: 300
      file.mtime: 150
    rowHeight: small
```

### Pattern 8: Tag-Based Organization

Shows notes by tag category:

```yaml
views:
  - type: table
    name: Ideas
    filters:
      file.tags.contains("idea")
    order:
      - file.name
      - file.ctime
    sort:
      - property: file.ctime
        direction: DESC

  - type: table
    name: References
    filters:
      file.tags.contains("reference")
    order:
      - file.name
      - file.ctime
    sort:
      - property: file.ctime
        direction: DESC
```

### Pattern 9: Multi-Level Filtering

Shows notes matching complex criteria:

```yaml
views:
  - type: table
    name: Active Work Items
    filters:
      and:
        - or:
            - file.tags.contains("meeting")
            - file.tags.contains("task")
            - file.tags.contains("project")
        - file.folder.startsWith("Work")
        - not:
            file.tags.contains("archived")
        - file.mtime >= ago(30 days)
    order:
      - file.name
      - file.tags
      - file.mtime
    sort:
      - property: file.mtime
        direction: DESC
```

### Pattern 10: People Interaction Tracking

Shows all notes mentioning a person:

```yaml
formulas:
  Interaction Type: |
    if (file.tags.contains("meeting")) "Meeting"
    else if (file.tags.contains("email")) "Email"
    else if (file.tags.contains("chat")) "Chat"
    else "Note"

views:
  - type: table
    name: Person Card
    filters:
      or:
        - file.hasLink(this.file)
        - file.embeds.contains(this.file.name)
    order:
      - file.name
      - Interaction Type
      - file.ctime
    sort:
      - property: file.ctime
        direction: DESC
    groupBy: formula.Interaction Type
```

## Advanced Techniques

### Dynamic Property References

```yaml
# Reference properties from frontmatter
properties:
  note.custom_field:
    displayName: My Custom Field

# Use in filters
filters:
  note.custom_field == "specific value"
```

### Context-Aware Queries

```yaml
# Query relative to current note
filters:
  # Notes in same folder
  file.folder == this.file.folder

  # Notes with same tags
  file.tags.containsAny(this.file.tags)

  # Notes linking to same targets
  file.links.containsAny(this.file.links)
```

### Combining Multiple Base Files

Different .base files for different purposes:

**Notes.base** - General relationships
```yaml
views:
  - name: Related Files
  - name: Recent Notes
```

**Meetings.base** - Meeting-specific
```yaml
views:
  - name: Customer Meetings
  - name: This Month's Meetings
```

**Projects.base** - Project tracking
```yaml
views:
  - name: Project Dashboard
  - name: Active Tasks
```

Then embed appropriate views in each note type.

## Best Practices

1. **Name views clearly** - Descriptive names help when embedding
2. **Use OR for flexible categorization** - Catch notes by tag OR folder
3. **Filter broadly** - Don't over-constrain, let sort order handle prioritization
4. **Leverage aliases** - Powerful for automatic aggregation
5. **Document formulas** - Comment complex calculations
6. **Test iteratively** - Build filters step by step
7. **Use meaningful displayNames** - Clear column headers improve readability
8. **Set appropriate rowHeight** - `small` for lists, `tall` for rich content

## Debugging Queries

### Check Filter Logic

If a view isn't showing expected notes:

1. Simplify filter to just one condition
2. Verify property names match frontmatter exactly (case-sensitive)
3. Check that `note.propertyName` is used for custom frontmatter
4. Verify folder paths are correct (use exact strings)
5. Test `or` vs `and` logic

### Common Issues

**Notes not appearing:**
- Property name typo: `note.Summary` vs `note.summary`
- Missing property in frontmatter
- Folder path doesn't match: `"Notes"` vs `"700 Notes"`
- Wrong containment check: `contains()` vs `containsAny()`

**Empty results:**
- Filter too restrictive (too many AND conditions)
- Property doesn't exist on target notes
- Using `file.property` instead of `note.property` for custom fields

## Migration from Dataview

Bases equivalents for common Dataview patterns:

| Dataview | Bases |
|----------|-------|
| `FROM #tag` | `filters: file.tags.contains("tag")` |
| `WHERE contains(file.name, "text")` | `filters: file.name.contains("text")` |
| `SORT file.ctime DESC` | `sort: [{property: file.ctime, direction: DESC}]` |
| `WHERE file.mtime >= date(today) - dur(7 days)` | `filters: file.mtime >= ago(7 days)` |
| `WHERE contains(file.outlinks, [[Note]])` | `filters: file.hasLink([[Note]])` |
| `TABLE field1, field2` | `order: [field1, field2]` |

**Key Difference:** Bases uses frontmatter properties only (no inline fields like `field:: value`).

## Example: Complete .base File

```yaml
# Complete example for work notes organization

formulas:
  Mentioned In: file.backlinks.map(value.asFile())
  Days Ago: Math.floor((now - file.ctime) / 86400000)

properties:
  file.name:
    displayName: Note
  file.tags:
    displayName: Tags
  note.customer:
    displayName: Customer
  note.priority:
    displayName: Priority
  file.ctime:
    displayName: Created
  formula.Days Ago:
    displayName: Age

views:
  - type: table
    name: Related Files
    filters:
      file.hasLink(this.file)
    order:
      - file.name
      - file.tags
      - file.ctime
    sort:
      - property: file.ctime
        direction: DESC
    rowHeight: medium

  - type: table
    name: Customer Notes
    filters:
      and:
        - customer == [this.file.link]
        - file.folder.startsWith("Work")
    order:
      - file.name
      - file.tags
      - file.ctime
    sort:
      - property: file.ctime
        direction: DESC
    columnSize:
      file.name: 300
      file.tags: 150
    rowHeight: medium

  - type: table
    name: High Priority
    filters:
      and:
        - note.priority == "high"
        - not:
            file.tags.contains("completed")
    order:
      - file.name
      - customer
      - Days Ago
    sort:
      - property: formula.Days Ago
        direction: ASC
    rowHeight: small

  - type: table
    name: Recent Activity
    filters:
      and:
        - file.folder.startsWith("Work")
        - file.mtime >= ago(7 days)
    order:
      - file.name
      - file.tags
      - file.mtime
    sort:
      - property: file.mtime
        direction: DESC
    rowHeight: small
```

This .base file provides multiple views that can be embedded in different notes:
- Company notes embed "Customer Notes"
- Dashboard embeds "High Priority" and "Recent Activity"
- Individual notes embed "Related Files"
