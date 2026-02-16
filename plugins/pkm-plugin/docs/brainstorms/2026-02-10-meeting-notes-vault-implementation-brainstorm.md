---
date: 2026-02-10
topic: meeting-notes-vault-implementation
status: implemented
---

# Meeting Notes Organization with Scope Metadata

## What We're Building

A unified meeting notes system that automatically surfaces meetings in relevant contexts (companies, projects, people) using a generic `scope:` metadata field and Obsidian Bases views. The system supports three capture workflows: structured meeting notes, quick logs in daily notes, and dated sections in company notes. Meetings are organized hierarchically by primary company (for confidentiality boundaries) while scope metadata enables cross-cutting discovery.

Integration with Chronos Timeline plugin provides visual timeline views. State tracking via tags (`action/scheduled` vs `action/completed`) distinguishes upcoming from historical meetings.

## Why This Approach

**Considered approaches:**

1. **Explicit metadata (chosen)** — `scope:` field contains all related entities
2. **Inference from attendees** — Derive relationships from people's employers
3. **Hierarchical location only** — Rely on folder structure
4. **Tag-based** — Use tags for relationships

**Rationale:** Explicit metadata in `scope:` provides the best balance of:
- **Clarity:** No ambiguity about relationships
- **Flexibility:** Works for any entity type (company, person, project, organization)
- **Queryability:** Simple Bases queries using `scope.contains(this.file)`
- **Reusability:** Same pattern works across all note types

Folder hierarchy remains for confidentiality boundaries (work meetings stay in company folders) while scope enables semantic discovery.

## Key Decisions

### Frontmatter Structure

```yaml
title: "2026-02-10 Customer Sync"
fileClass: Meeting
scope: ["[[Palo Alto Networks]]", "[[Acme Corp]]", "[[SASE Migration]]"]
attendees: ["[[John Smith]]", "[[Jane Doe]]"]
start: 2026-02-10T14:30:00
end: 2026-02-10T15:30:00
color: "#blue"
type: "customer-meeting"
location: "Zoom"
source: "Google Calendar"
tags:
  - action/scheduled  # or action/completed
```

**Key fields:**
- `scope:` — All related entities (companies, projects, departments)
- `attendees:` — People who attended (links to Person notes)
- `start/end:` — For Chronos timeline integration
- `color:` — For Chronos grouping
- `type:` — Meeting category (customer-meeting, internal, 1-on-1, standup)
- `tags:` — State tracking (scheduled vs completed)

**Removed from old template:**
- `pillars:` — Not actively used, removed per YAGNI principle
- `content:` — Redundant with note body
- `source_calendar:` → renamed to `source:`

### File Organization

**Hierarchical by primary company:**
- `700 Notes/Palo Alto Networks/Meetings/` — Work meetings
- `700 Notes/Solo.io/Meetings/` — Previous employer meetings
- `700 Notes/Meetings/` — Personal/generic meetings

**Rationale:** Folder location = confidentiality boundary. Work notes stay in company directory. Multi-entity meetings go in primary company folder, with all entities listed in `scope:`.

### Scope Field Contents

**Explicit > Implicit:** Include ALL related entities, even if redundant with folder location.

```yaml
scope:
  - "[[Palo Alto Networks]]"  # Primary (from folder)
  - "[[SASE Migration Project]]"  # Project
  - "[[NetSec R&D]]"  # Department
  - "[[Acme Corp]]"  # Customer
```

**Rationale:** Makes Bases queries uniform and simple. Migration scripts can auto-populate primary entity from folder structure.

### Capture Workflows

**Three methods, ordered by formality:**

1. **Structured meeting note** — Template or calendar import
   - Full frontmatter from start
   - Uses `🛠 New Meeting.md` template or import command

2. **Quick log in daily note** — Quickadd capture
   - Minimal: `### (log::⏱ 14:30 -0500: Meeting with Customer X)`
   - Extract to structured note when needed

3. **Dated section in company note** — Inline capture
   - `## 2026-02-05` heading with content
   - Extract to structured note when needed

**Philosophy:** Ephemeral stays inline, important converts to structured notes via extraction command.

### Bases Views

**Meetings.base structure:**

```yaml
filters:
  and:
    - fileClass == "Meeting"

views:
  - name: All Meetings
    # Full management view for editing metadata
    order: [file.name, start, end, attendees, scope, type, location, color, source]
    sort: start DESC

  - name: Related Meetings
    # For embedding in company/project notes
    filters:
      - scope.contains(this.file)
    order: [file.name, start, attendees, type]
    sort: start DESC

  - name: Meetings by Project
    # Grouped view for company notes
    filters:
      - scope.contains(this.file)
    groupBy: scope
    order: [file.name, start, attendees]
    sort: start DESC

  - name: Meetings with Person
    # For embedding in Person notes
    filters:
      - attendees.contains(this.file)
    order: [file.name, start, scope, type]
    sort: start DESC

  - name: Timeline
    # Chronos visual timeline
    type: chronos-timeline-view
    filters:
      - scope.contains(this.file)
    order: [file.name, start, end, color, type]
```

**Usage in entity notes:**

```markdown
## Meetings
![[Meetings.base#Related Meetings]]

## Project Timeline
![[Meetings.base#Timeline]]
```

### Tag Strategy for State Tracking

- `action/scheduled` — Future meetings (start date in future)
- `action/completed` — Past meetings (start date in past)
- `fileClass: Meeting` — All meetings regardless of state

**Rationale:** Enables useful filtering for upcoming vs. historical meetings while maintaining backward compatibility with existing Notes.base queries.

### Essential Commands

**1. Extract Log to Meeting**
- Input: Selected section from daily note or company note
- Logic:
  - Parse heading for time/topic
  - Detect inline fields (scope::, start::)
  - Prompt for missing metadata
  - Create meeting note in appropriate folder
  - Replace original section with link
- Output: `[[2026-02-10 Meeting Title]]`

**2. Import from Calendar**
- Input: Clipboard (calendar event) or manual entry
- Logic:
  - Parse title, time, attendees, location
  - Match attendees to Person notes by email field
  - Infer primary company from attendees' employers
  - If single company → auto-select folder
  - If multiple companies → prompt for primary
  - Auto-populate scope with all companies
  - Create Person notes for unknown attendees (with prompt)
- Output: Meeting note in `[Company]/Meetings/` folder

**3. Migrate Old Meetings** _(tracked but lower priority)_
- Input: All existing meeting notes
- Logic:
  - Find by: fileClass, action/scheduled tag, or */Meetings/ folder
  - Extract company from folder path → add to scope
  - Ensure fileClass: Meeting is set
  - Set tag based on start time (scheduled vs completed)
  - Prompt for additional scope items (projects, people)
- Output: Migration report with updated notes

## Related Notes & Templates

**Existing documentation:**
- [[700 Notes/Notes/How I take Meeting Notes]] — Current (outdated) process documentation
- [[900 📐Templates/910 File Templates/🛠 New Meeting]] — Meeting note template (needs updating)
- [[700 Notes/Tools/Chronos Timeline Cheatsheet]] — Chronos syntax reference
- [[700 Notes/Notes/dynamic timelines]] — Timeline experimentation
- [[700 Notes/Testing/Testing out Chronos Views]] — Chronos Bases testing

**Related Bases:**
- [[900 📐Templates/970 Bases/👤 People.base]] — Pattern for `this.file` references
- [[900 📐Templates/970 Bases/Organizations.base]] — Company card views
- [[900 📐Templates/970 Bases/Notes.base]] — Existing meeting views (to be replaced/enhanced)

**Scripts to consolidate:**
- [[900 📐Templates/Scripts/Timeline Event.js]] — Chronos event creation (may not be needed with new Bases integration)

**Experimental patterns to revisit:**
- [[000 🏛 Pillars/]] — Pillar-based categorization (research if valuable for PKM)

## Implementation Priority

1. **Start with going-forward system** — Focus on new meeting creation with proper metadata
2. **Migration as secondary** — Track existing meetings but don't block on full migration

**Rationale:** Get the new system working correctly first, migrate old notes gradually as needed.
