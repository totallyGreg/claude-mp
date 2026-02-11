# Bases Query Reference

Complete reference for Obsidian Bases plugin query syntax, filters, and view configuration.

**Official Documentation:** https://help.obsidian.md/bases/syntax

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [File Structure](#file-structure)
3. [Filters](#filters)
4. [Views](#views)
5. [File Properties (this.file)](#file-properties-thisfile)
6. [Custom Properties](#custom-properties)
7. [Functions and Formulas](#functions-and-formulas)
8. [View Types](#view-types)
9. [Common Patterns](#common-patterns)
10. [Troubleshooting](#troubleshooting)

## Core Concepts

### What is Bases?

Bases is Obsidian's native database/query system that:
- Creates dynamic views of vault files based on metadata
- Filters files using frontmatter properties
- Supports multiple view types (table, cards, timeline)
- Embeds views into notes with transclude syntax
- Replaces Dataview for many use cases

### .base Files

Bases are defined in `.base` files with YAML syntax:

```yaml
filters:
  and:
    - fileClass == "Meeting"
    - start >= "2026-01-01"

views:
  - name: Recent Meetings
    order: [file.name, start, attendees]
    sort: start DESC
```

### Embedding Views

```markdown
## Meetings
![[Meetings.base#Recent Meetings]]

## Full base (all views)
![[Meetings.base]]
```

## File Structure

### Basic .base File

```yaml
filters:
  # Base-level filters (apply to all views)
  and:
    - fileClass == "Meeting"

views:
  - name: View Name
    filters:
      # View-specific filters (combined with base filters via AND)
      - scope.contains(this.file)
    order: [file.name, start, end]
    sort: start DESC
    groupBy: type
```

### Multiple Views in One Base

```yaml
filters:
  and:
    - fileClass == "Note"

views:
  - name: All Notes
    order: [file.name, created]
    sort: file.name ASC

  - name: Recent Notes
    filters:
      - file.ctime >= "2026-01-01"
    order: [file.name, file.ctime]
    sort: file.ctime DESC
    limit: 50

  - name: Tagged Urgent
    filters:
      - tags.contains("urgent")
    order: [file.name, priority]
```

## Filters

### Filter Structure

Filters can be simple expressions or complex logic:

```yaml
# Simple filter
filters:
  - fileClass == "Meeting"

# AND conditions
filters:
  and:
    - fileClass == "Meeting"
    - start >= "2026-01-01"
    - status != "cancelled"

# OR conditions
filters:
  or:
    - status == "active"
    - priority == "high"

# Nested logic (AND with nested OR)
filters:
  and:
    - fileClass == "Project"
    - or:
        - status == "active"
        - status == "planning"
```

### Comparison Operators

```yaml
==    # Equal
!=    # Not equal
>     # Greater than
>=    # Greater than or equal
<     # Less than
<=    # Less than or equal
```

**Examples:**

```yaml
# Date comparisons
filters:
  - start >= "2026-01-01"
  - due < "2026-12-31"

# Number comparisons
filters:
  - priority > 5
  - participants <= 10

# String comparisons
filters:
  - status == "active"
  - type != "archived"
```

### String Methods

```yaml
contains(value)     # Check if string/array contains value
startsWith(prefix)  # Check if starts with prefix
endsWith(suffix)    # Check if ends with suffix
```

**Examples:**

```yaml
# Array contains
filters:
  - tags.contains("meeting")
  - attendees.contains(this.file)
  - scope.contains("[[Project Name]]")

# String contains
filters:
  - file.name.contains("2026")
  - title.contains("Review")

# String prefix/suffix
filters:
  - file.name.startsWith("Meeting")
  - file.path.endsWith(".md")
```

### Existence Checks

```yaml
# Check if property exists
filters:
  - priority    # Has priority property

# Check if property doesn't exist
filters:
  - not priority    # Missing priority property
```

**Examples:**

```yaml
# Notes with due dates
filters:
  - due

# Notes without tags
filters:
  - not tags

# Has attendees
filters:
  - attendees
```

## Views

### View Configuration

```yaml
views:
  - name: View Name             # Required: Display name
    type: table                 # Optional: View type (default: table)
    filters: []                 # Optional: View-specific filters
    order: []                   # Required: Columns to display
    sort: property ASC/DESC     # Optional: Sort order
    groupBy: property           # Optional: Group by property
    limit: 100                  # Optional: Max results
```

### Order (Columns)

Specify which properties appear as columns:

```yaml
views:
  - name: Meeting List
    order: [file.name, start, end, attendees, scope]
```

**Column types:**
- File properties: `file.name`, `file.ctime`, `file.mtime`, `file.path`
- Custom properties: `start`, `end`, `attendees`, `priority`, etc.
- Nested properties: `metadata.author`, `contact.email`

### Sort

Sort by any property in ascending or descending order:

```yaml
# Single sort
sort: start DESC

# Common patterns
sort: file.name ASC           # Alphabetical
sort: file.ctime DESC         # Newest first
sort: priority DESC           # High priority first
sort: due ASC                 # Earliest deadline first
```

**Multiple sort criteria** (primary then secondary):
```yaml
sort: priority DESC, due ASC
```

### GroupBy

Group results by property value:

```yaml
views:
  - name: Meetings by Type
    order: [file.name, start, attendees]
    groupBy: type
    sort: start DESC
```

**Result:**
```
customer-meeting
  - 2026-02-10 Customer Sync
  - 2026-02-08 Quarterly Review

internal
  - 2026-02-09 Team Standup
  - 2026-02-07 Planning Session
```

### Limit

Restrict number of results:

```yaml
views:
  - name: Recent 10 Meetings
    order: [file.name, start]
    sort: start DESC
    limit: 10
```

## File Properties (this.file)

### Built-in File Properties

Every file has these implicit properties:

```yaml
# File metadata
file.name       # Filename (without extension)
file.path       # Full file path
file.folder     # Parent folder path
file.ext        # File extension
file.size       # File size in bytes

# Timestamps
file.ctime      # Creation time (ISO 8601)
file.mtime      # Modified time (ISO 8601)

# Links
file.inlinks    # Array of files linking to this file
file.outlinks   # Array of files this file links to

# Tags
file.tags       # Array of all tags in file
```

**Examples:**

```yaml
# Files created this year
filters:
  - file.ctime >= "2026-01-01"

# Files modified recently
filters:
  - file.mtime >= "2026-02-01"

# Files in specific folder
filters:
  - file.folder.contains("Projects")

# Files with inlinks (referenced by others)
filters:
  - file.inlinks

# Large files
filters:
  - file.size > 10000
```

### this.file Reference

`this.file` refers to the file **containing the embedded view**, not the files being queried.

**Use cases:**

1. **Related notes queries:**
```yaml
# In a Company note, show related meetings
filters:
  and:
    - fileClass == "Meeting"
    - scope.contains(this.file)
```

2. **Contextual views:**
```yaml
# In a Project note, show tasks
filters:
  and:
    - fileClass == "Task"
    - project == this.file.name
```

3. **Bi-directional linking:**
```yaml
# Notes that link to current file
filters:
  - file.outlinks.contains(this.file)

# Notes linked from current file
filters:
  - this.file.outlinks.contains(file)
```

**Example - Meetings.base embedded in Company note:**

```yaml
# Meetings.base
filters:
  and:
    - fileClass == "Meeting"

views:
  - name: Related Meetings
    filters:
      - scope.contains(this.file)    # When embedded in "Acme Corp" note,
    order: [file.name, start]         # filters to meetings with Acme Corp in scope
    sort: start DESC
```

**Embedded in:**
```markdown
# Acme Corp

## Meetings
![[Meetings.base#Related Meetings]]
```

## Custom Properties

Any frontmatter property can be used in queries.

### Simple Properties

```yaml
---
title: "Meeting Title"
status: active
priority: 5
due: 2026-02-15
---
```

**Query:**
```yaml
filters:
  and:
    - status == "active"
    - priority > 3
    - due <= "2026-02-20"
```

### Array Properties

```yaml
---
tags:
  - meeting
  - urgent
attendees:
  - "[[Alice]]"
  - "[[Bob]]"
---
```

**Query:**
```yaml
filters:
  - tags.contains("urgent")
  - attendees.contains("[[Alice]]")
```

### Nested Properties

```yaml
---
contact:
  email: alice@example.com
  phone: "555-1234"
metadata:
  author: "Bob Smith"
  version: 2
---
```

**Query:**
```yaml
filters:
  - contact.email.contains("@example.com")
  - metadata.version > 1
```

## Functions and Formulas

### String Functions

```javascript
contains(substring)     // Check if contains substring
startsWith(prefix)      // Check if starts with prefix
endsWith(suffix)        // Check if ends with suffix
toLowerCase()           // Convert to lowercase
toUpperCase()           // Convert to uppercase
```

**Examples:**

```yaml
# Case-insensitive search
filters:
  - title.toLowerCase().contains("review")

# File extension check
filters:
  - file.name.endsWith(".md")
```

### Array Functions

```javascript
contains(item)          // Check if array contains item
length                  // Get array length
```

**Examples:**

```yaml
# Has multiple attendees
filters:
  - attendees.length > 1

# No tags
filters:
  - tags.length == 0

# Contains specific item
filters:
  - scope.contains("[[Project Name]]")
```

### Date Functions

Dates use ISO 8601 format: `YYYY-MM-DD` or `YYYY-MM-DDTHH:mm:ss`

**Examples:**

```yaml
# Past meetings
filters:
  - start < "2026-02-10"

# Future meetings
filters:
  - start >= "2026-02-10"

# This month
filters:
  - start >= "2026-02-01"
  - start < "2026-03-01"

# Files created this week
filters:
  - file.ctime >= "2026-02-03"
```

### Formulas (Calculated Columns)

**Coming soon** - Bases will support formulas for calculated values:

```yaml
views:
  - name: Projects with Progress
    order: [file.name, progress]
    formulas:
      progress: (completedTasks / totalTasks) * 100
```

## View Types

### Table View (Default)

Standard table with rows and columns.

```yaml
views:
  - name: Meeting Table
    type: table                     # Optional (default)
    order: [file.name, start, attendees]
    sort: start DESC
```

### Card View

Display as cards with custom layout.

```yaml
views:
  - name: Meeting Cards
    type: cards
    order: [file.name, start, attendees, type]
    groupBy: type
```

### Chronos Timeline View

Displays events on a timeline (requires Chronos Timeline plugin).

```yaml
views:
  - name: Meeting Timeline
    type: chronos-timeline-view
    filters:
      - scope.contains(this.file)
    order: [file.name, start, end, color, type]
```

**Required properties for timeline:**
- `start`: Start datetime
- `end`: End datetime (optional)
- `color`: Event color (optional)

**Example frontmatter for timeline:**
```yaml
---
title: "Customer Sync"
start: 2026-02-10T14:30:00
end: 2026-02-10T15:30:00
color: "#blue"
---
```

### Gallery View

Display files as image gallery.

```yaml
views:
  - name: Photo Gallery
    type: gallery
    filters:
      - file.ext == "png" or file.ext == "jpg"
```

## Common Patterns

### Pattern 1: Related Notes

Show notes related to current note via scope metadata.

```yaml
# Related.base
filters:
  and:
    - fileClass == "Note"

views:
  - name: Related Notes
    filters:
      - scope.contains(this.file)
    order: [file.name, created, tags]
    sort: created DESC
```

**Usage:**
```markdown
# Project Alpha

## Related Notes
![[Related.base#Related Notes]]
```

### Pattern 2: Meetings with Person

Show meetings where person is an attendee.

```yaml
# Meetings.base
filters:
  and:
    - fileClass == "Meeting"

views:
  - name: Meetings with Person
    filters:
      - attendees.contains(this.file)
    order: [file.name, start, scope, type]
    sort: start DESC
```

**Usage in Person note:**
```markdown
# Alice Johnson

## Meetings
![[Meetings.base#Meetings with Person]]
```

### Pattern 3: Upcoming vs. Historical

Separate views for future and past items.

```yaml
# Events.base
filters:
  and:
    - fileClass == "Event"

views:
  - name: Upcoming Events
    filters:
      - start >= "2026-02-10"    # Today's date
    order: [file.name, start, location]
    sort: start ASC

  - name: Past Events
    filters:
      - start < "2026-02-10"
    order: [file.name, start, location]
    sort: start DESC
    limit: 20
```

### Pattern 4: Status-Based Views

Multiple views for different statuses.

```yaml
# Tasks.base
filters:
  and:
    - fileClass == "Task"

views:
  - name: Active Tasks
    filters:
      - status == "active"
    order: [file.name, priority, due]
    sort: priority DESC

  - name: Completed Tasks
    filters:
      - status == "completed"
    order: [file.name, completed]
    sort: completed DESC

  - name: Blocked Tasks
    filters:
      - status == "blocked"
    order: [file.name, blocker, priority]
```

### Pattern 5: Hierarchical Views

Show parent-child relationships.

```yaml
# Projects.base
filters:
  and:
    - fileClass == "Project"

views:
  - name: Active Projects
    filters:
      - status == "active"
    order: [file.name, owner, due]
    groupBy: owner

  - name: Sub-Projects
    filters:
      - parentProject == this.file.name
    order: [file.name, status, progress]
    sort: file.name ASC
```

### Pattern 6: Tag-Based Collections

Group by tags for organization.

```yaml
# Notes.base
filters:
  and:
    - fileClass == "Note"

views:
  - name: Notes by Tag
    order: [file.name, created, tags]
    groupBy: tags
    sort: created DESC

  - name: Untagged Notes
    filters:
      - not tags
    order: [file.name, created]
```

### Pattern 7: Temporal Rollup

Daily → Weekly → Monthly aggregation.

```yaml
# Daily.base (embedded in weekly note)
filters:
  and:
    - fileClass == "DailyNote"
    - date >= "2026-02-03"    # Start of week
    - date < "2026-02-10"     # End of week

views:
  - name: This Week
    order: [file.name, highlights]
    sort: date ASC
```

### Pattern 8: Multi-Criteria Search

Complex filtering for specific use cases.

```yaml
# HighPriority.base
filters:
  and:
    - or:
        - priority == "high"
        - tags.contains("urgent")
    - status != "completed"
    - or:
        - not assigned
        - assigned == "[[Me]]"

views:
  - name: My Urgent Items
    order: [file.name, type, due, priority]
    sort: due ASC
```

## Troubleshooting

### Query returns no results

1. **Check filter syntax:**
   - Use `==` not `=`
   - Use double quotes for strings: `"value"`
   - Array contains: `array.contains("value")`

2. **Verify property names:**
   - Must match frontmatter exactly (case-sensitive)
   - Use `file.name` not `name` for filename

3. **Check date formats:**
   - Use ISO 8601: `YYYY-MM-DD`
   - Ensure dates in frontmatter match format

### this.file not working

1. **Verify context:**
   - `this.file` refers to file containing embedded view
   - Only works when view is embedded, not when opening .base directly

2. **Check property reference:**
   - `scope.contains(this.file)` not `scope.contains("this.file")`
   - Use file object, not string

### View not updating

1. **Refresh:**
   - Close and reopen note
   - Restart Obsidian

2. **Check filters:**
   - Base-level filters apply to all views
   - View filters combine with AND

### Performance issues

1. **Limit results:**
   ```yaml
   limit: 100
   ```

2. **Add specific filters:**
   ```yaml
   filters:
     - file.folder == "Active Projects"
   ```

3. **Avoid complex nested filters on large vaults**

### Array comparison not working

**Use `.contains()` not `==`:**

```yaml
# ✓ Correct
filters:
  - tags.contains("urgent")

# ✗ Wrong
filters:
  - tags == "urgent"
```

### Missing columns in view

**Ensure properties exist in frontmatter:**

```yaml
# If some files lack 'due' property, it shows blank
order: [file.name, due, status]

# Fix: Add due property to all filtered files
```

## Best Practices

### 1. Use Descriptive View Names

```yaml
# ✓ Good
views:
  - name: Meetings with Customer (Last 90 Days)

# ✗ Bad
views:
  - name: View 1
```

### 2. Consistent Property Naming

```yaml
# ✓ Good - Use consistent naming
fileClass: Meeting
start: 2026-02-10
attendees: ["[[Alice]]"]

# ✗ Bad - Inconsistent
type: meeting
meetingDate: 2026-02-10
people: ["Alice"]
```

### 3. Explicit Over Implicit

```yaml
# ✓ Good - Explicit scope
scope: ["[[Company]]", "[[Project]]"]

# ✗ Bad - Relying on folder inference
# (no scope field)
```

### 4. Base for Grouping, View for Specifics

```yaml
# ✓ Good - Base has broad filter, views narrow down
filters:
  and:
    - fileClass == "Note"

views:
  - name: Work Notes
    filters:
      - folder.contains("Work")

  - name: Personal Notes
    filters:
      - folder.contains("Personal")
```

### 5. Test Incrementally

Build complex queries step by step:

1. Start with simple filter
2. Add one condition at a time
3. Test after each addition
4. Use specific examples to debug

## References

- **Official Documentation:** https://help.obsidian.md/bases/syntax
- **Bases Overview:** https://practicalpkm.com/bases-plugin-overview/
- **ISO 8601 Dates:** https://en.wikipedia.org/wiki/ISO_8601
