# Chronos Timeline Syntax Reference

> **📝 TODO:** This reference needs to be completed with content from official Chronos Timeline documentation.
>
> **Official Documentation:** https://github.com/clairefro/obsidian-plugin-chronos
>
> **What to add:**
> - Complete event type syntax (events `-`, periods `@`, points `*`, markers `=`)
> - Frontmatter integration patterns
> - Color and grouping syntax
> - Date formats and ranges
> - Bases integration for chronos-timeline-view
> - Examples of meeting timelines
> - Common patterns and troubleshooting

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Event Types](#event-types)
3. [Frontmatter Integration](#frontmatter-integration)
4. [Color and Grouping](#color-and-grouping)
5. [Date Formats](#date-formats)
6. [Bases Integration](#bases-integration)
7. [Common Patterns](#common-patterns)
8. [Troubleshooting](#troubleshooting)

## Core Concepts

Chronos Timeline is an Obsidian plugin that visualizes events, periods, and points on interactive timelines.

### Timeline Types

- **Events** (`-`) - Single point in time
- **Periods** (`@`) - Duration with start and end
- **Points** (`*`) - Milestone markers
- **Markers** (`=`) - Reference lines

## Event Types

### Events (-)

Single-point events on timeline.

```markdown
- 2026-02-10: Meeting with customer
- 2026-02-10 14:30: Customer sync call
```

### Periods (@)

Durations with start and end dates.

```markdown
@ 2026-02-01 - 2026-02-28: February Sprint
@ 2026-01-15 - 2026-03-15: Q1 Project
```

### Points (*)

Milestone markers.

```markdown
* 2026-02-10: Product Launch
* 2026-12-31: End of Year
```

### Markers (=)

Reference lines on timeline.

```markdown
= 2026-02-10: Today
= 2026-01-01: Year Start
```

## Frontmatter Integration

### Basic Event

```yaml
---
title: "Customer Meeting"
start: 2026-02-10T14:30:00
end: 2026-02-10T15:30:00
color: "#blue"
type: "customer-meeting"
---
```

### Timeline Properties

| Property | Type | Description |
|----------|------|-------------|
| `start` | ISO 8601 | Start datetime |
| `end` | ISO 8601 | End datetime (optional for events) |
| `color` | String | Event color (`#blue`, `#red`, `#green`) |
| `type` | String | Event category for grouping |

## Color and Grouping

### Color Syntax

```yaml
# Predefined colors
color: "#blue"
color: "#red"
color: "#green"
color: "#yellow"
color: "#purple"
color: "#orange"

# Hex codes
color: "#3b82f6"
color: "#ef4444"
```

### Grouping by Type

```yaml
# Meeting notes with type
type: "customer-meeting"
type: "internal"
type: "1-on-1"
```

Timeline groups events by `type` property automatically.

## Date Formats

### ISO 8601 Format

```yaml
# Date only
start: 2026-02-10

# Date + time
start: 2026-02-10T14:30:00

# Date + time + timezone
start: 2026-02-10T14:30:00-05:00
```

### Range Syntax

```yaml
# Period
start: 2026-02-01
end: 2026-02-28

# Multi-day event
start: 2026-02-10T00:00:00
end: 2026-02-12T23:59:59
```

## Bases Integration

### Chronos Timeline View in Bases

```yaml
# Meetings.base
filters:
  and:
    - fileClass == "Meeting"

views:
  - name: Timeline
    type: chronos-timeline-view
    filters:
      - scope.contains(this.file)
    order: [file.name, start, end, color, type]
```

### Required Properties for Timeline View

Files displayed in chronos-timeline-view must have:

1. `start` property (required)
2. `end` property (optional, for periods)
3. `color` property (optional, for color coding)
4. `type` property (optional, for grouping)

### Example - Meeting Timeline

**Meetings.base:**
```yaml
filters:
  and:
    - fileClass == "Meeting"

views:
  - name: Meeting Timeline
    type: chronos-timeline-view
    filters:
      - scope.contains(this.file)
    order: [file.name, start, end, color, type]
```

**Meeting note frontmatter:**
```yaml
---
title: "Q1 Planning"
fileClass: Meeting
scope: ["[[Acme Corp]]"]
start: 2026-02-10T14:00:00
end: 2026-02-10T15:30:00
color: "#blue"
type: "planning-meeting"
---
```

**Embedded in company note:**
```markdown
# Acme Corp

## Meeting Timeline
![[Meetings.base#Meeting Timeline]]
```

## Common Patterns

### Pattern 1: Project Timeline

```yaml
---
title: "Project Alpha"
fileClass: Project
start: 2026-01-01
end: 2026-03-31
color: "#blue"
milestones:
  - 2026-01-15: "Kickoff"
  - 2026-02-15: "Prototype"
  - 2026-03-15: "Beta"
  - 2026-03-31: "Launch"
---
```

### Pattern 2: Meeting Schedule

```yaml
# Weekly.base - Show week's meetings on timeline
filters:
  and:
    - fileClass == "Meeting"
    - start >= "2026-02-03"
    - start < "2026-02-10"

views:
  - name: This Week Timeline
    type: chronos-timeline-view
    order: [file.name, start, end, color, type]
```

### Pattern 3: Multi-Type Events

```yaml
# Events.base - Mixed event types
filters:
  and:
    - or:
        - fileClass == "Meeting"
        - fileClass == "Event"
        - fileClass == "Milestone"

views:
  - name: All Events
    type: chronos-timeline-view
    order: [file.name, start, end, color, type]
    groupBy: type
```

## Troubleshooting

### Events not showing on timeline

1. **Check `start` property:**
   - Must be ISO 8601 format
   - Must be valid date/time

2. **Check view type:**
   ```yaml
   type: chronos-timeline-view  # Required
   ```

3. **Check required columns:**
   ```yaml
   order: [file.name, start, end, color, type]
   # Must include start, end (for periods), color (for colors)
   ```

### Colors not appearing

1. **Verify color property:**
   ```yaml
   color: "#blue"    # Correct
   color: "blue"     # May not work (check docs)
   ```

2. **Include color in view order:**
   ```yaml
   order: [file.name, start, end, color]
   ```

### Grouping not working

1. **Include type in frontmatter:**
   ```yaml
   type: "meeting"
   ```

2. **Use groupBy in view:**
   ```yaml
   groupBy: type
   ```

## Best Practices

### 1. Consistent Date Formats

```yaml
# ✓ Good - ISO 8601
start: 2026-02-10T14:30:00

# ✗ Bad - Ambiguous
start: 2/10/26 2:30 PM
```

### 2. Meaningful Colors

```yaml
# ✓ Good - Color by importance/type
color: "#red"      # Urgent
color: "#blue"     # Normal
color: "#green"    # Completed

# ✗ Bad - Random colors
```

### 3. Descriptive Types

```yaml
# ✓ Good
type: "customer-meeting"
type: "internal-standup"
type: "project-milestone"

# ✗ Bad
type: "mtg1"
type: "event"
```

## References

- **Official Repository:** https://github.com/clairefro/obsidian-plugin-chronos
- **ISO 8601 Standard:** https://en.wikipedia.org/wiki/ISO_8601

---

**📝 Note:** This reference needs to be expanded with content from the official Chronos Timeline documentation. The patterns above are based on common use cases but should be verified against the official docs.
