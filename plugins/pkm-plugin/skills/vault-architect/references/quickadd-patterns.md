# Quickadd Patterns Reference

> **📝 TODO:** This reference needs to be completed with content from official Quickadd documentation.
>
> **Official Documentation:** https://github.com/chhoumann/quickadd
>
> **What to add:**
> - Capture template configurations
> - Template choice patterns
> - Macro scripts
> - Integration with Templater
> - Quick capture workflows
> - Common patterns and examples

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Capture Templates](#capture-templates)
3. [Template Choices](#template-choices)
4. [Macros](#macros)
5. [Templater Integration](#templater-integration)
6. [Common Patterns](#common-patterns)
7. [Troubleshooting](#troubleshooting)

## Core Concepts

Quickadd is an Obsidian plugin that provides quick capture workflows, template choices, and macro automation.

### Main Features

- **Capture** - Quick note creation from anywhere
- **Template Choice** - Select from multiple templates
- **Macros** - Automated multi-step workflows
- **Multi-Choice** - Combine different actions

## Capture Templates

### Basic Capture

Quickadd capture templates allow quick note creation with pre-defined structure.

**Configuration:**
1. Open Quickadd settings
2. Add new choice → Capture
3. Configure capture template
4. Set file name format
5. Set destination folder

### Capture to Daily Note

```markdown
Capture Format:
### {{TIME:HH:mm}} - {{VALUE}}
```

**Settings:**
- File Name Format: `{{DATE:YYYY-MM-DD}}`
- Folder: `Daily Notes/`
- Insert at: End of file
- Create if doesn't exist: ✓

**Result in daily note:**
```markdown
### 14:30 - Quick meeting note with customer
```

### Capture to Specific Note

```markdown
Capture Format:
- [ ] {{VALUE}}

Created: {{DATE:YYYY-MM-DD HH:mm}}
```

**Settings:**
- File Name Format: `Tasks`
- Folder: `Inbox/`
- Insert at: Top of file

## Template Choices

### Template Choice Configuration

Template choices present a menu of templates to select from.

**Configuration:**
1. Add new choice → Template
2. Create sub-choices for each template
3. Assign template files
4. Configure file naming

### Example - Note Type Choice

**Choices:**
- Meeting Note → `templates/meeting.md`
- Project Note → `templates/project.md`
- Person Note → `templates/person.md`

**File Naming:**
- Meeting: `{{DATE:YYYY-MM-DD}} {{VALUE}}`
- Project: `{{VALUE}}`
- Person: `{{VALUE}}`

## Macros

### Basic Macro Structure

Macros automate multi-step workflows.

**Example - Create Meeting with Related Tasks:**

1. User Input: Meeting title
2. Create meeting note from template
3. Create tasks note linked to meeting
4. Open meeting note

### Macro Actions

Common macro actions:

- **Templater** - Run Templater template
- **Capture** - Quick capture to note
- **Choice** - Run another Quickadd choice
- **Wait** - Pause between actions
- **Command** - Run Obsidian command
- **Open** - Open specific file/folder

## Templater Integration

### Using Templater in Quickadd

Quickadd can execute Templater templates.

**Macro step:**
1. Add step → Templater
2. Select template file
3. Configure file destination
4. Set file name format

**Template file uses Templater syntax:**
```markdown
---
title: "<% tp.file.title %>"
created: <% tp.date.now("YYYY-MM-DD") %>
---

# <% tp.file.title %>

Content: <% tp.system.prompt("Enter content") %>
```

### Combining Quickadd Variables and Templater

```markdown
---
title: "{{VALUE}}"
date: {{DATE:YYYY-MM-DD}}
---

# {{VALUE}}

Created by: <% tp.system.clipboard() %>
```

**Quickadd variables:**
- `{{VALUE}}` - User input
- `{{DATE:format}}` - Current date
- `{{TIME:format}}` - Current time
- `{{NAME}}` - File name
- `{{FOLDER}}` - Destination folder

## Common Patterns

### Pattern 1: Quick Meeting Log

**Capture to Daily Note:**

```markdown
### (log::⏱ {{TIME:HH:mm ZZ}}: {{VALUE}})
```

**Settings:**
- Type: Capture
- File Name: `{{DATE:YYYY-MM-DD}}`
- Folder: `Daily Notes/`
- Insert at: End
- Open file: No

**Usage:** Type `/quickadd`, enter "Meeting with customer", appends to today's daily note.

### Pattern 2: Template Menu

**Template Choice:**

**Main Choice:** "New Note"

**Sub-Choices:**
1. Meeting Note
   - Template: `templates/meeting.md`
   - File Name: `{{DATE:YYYY-MM-DD}} {{VALUE}}`
   - Folder: User choice from folder list

2. Daily Note
   - Template: `templates/daily.md`
   - File Name: `{{DATE:YYYY-MM-DD}}`
   - Folder: `Daily Notes/`

3. Person Note
   - Template: `templates/person.md`
   - File Name: `{{VALUE}}`
   - Folder: `People/`

### Pattern 3: Capture with Context

**Capture Format:**
```markdown
## {{DATE:YYYY-MM-DD HH:mm}}

**Context:** {{LINKCURRENT}}

{{VALUE}}

---
```

**Variables:**
- `{{LINKCURRENT}}` - Link to current note
- Captures with context of where you were

### Pattern 4: Multi-Step Macro

**Macro: "Create Project"**

Steps:
1. User Input → Project name
2. Templater → Create project note from template
3. Templater → Create project tasks note
4. Templater → Create project meetings folder
5. Command → Open project note
6. Command → Open file explorer to project folder

### Pattern 5: Quick Task Capture

**Capture to Inbox:**

```markdown
- [ ] {{VALUE}} 📅 {{DATE:YYYY-MM-DD}}
```

**Settings:**
- File Name: `Inbox`
- Folder: `Tasks/`
- Insert at: Top
- Task format: Checkbox
- Include created date

## Troubleshooting

### Capture not inserting at correct location

1. **Check "Insert at" setting:**
   - Top of file
   - Bottom of file
   - At cursor (if file is open)

2. **Verify file exists:**
   - Enable "Create file if it doesn't exist"

### Template choice not appearing

1. **Check choice type:**
   - Must be "Template" not "Capture"

2. **Verify template file exists:**
   - Path must be correct
   - Include `.md` extension

### Variables not expanding

1. **Check variable syntax:**
   ```markdown
   {{VALUE}}       # Correct
   {VALUE}         # Wrong
   ```

2. **Use correct format strings:**
   ```markdown
   {{DATE:YYYY-MM-DD}}    # Correct
   {{DATE:YYYY/MM/DD}}    # Also correct
   ```

### Macro steps failing

1. **Test steps individually**
2. **Add wait steps between actions**
3. **Check command names match exactly**

## Best Practices

### 1. Use Descriptive Choice Names

```
✓ Good:
- "Quick Meeting Log to Daily Note"
- "Create Project with Tasks"

✗ Bad:
- "Choice 1"
- "Macro"
```

### 2. Organize Templates by Workflow

```
templates/
├── capture/
│   ├── meeting-log.md
│   ├── task-capture.md
│   └── quick-note.md
├── structured/
│   ├── meeting.md
│   ├── project.md
│   └── person.md
└── workflows/
    ├── project-setup.md
    └── meeting-with-tasks.md
```

### 3. Consistent Variable Usage

```markdown
# ✓ Good - Consistent format
File Name: {{DATE:YYYY-MM-DD}} {{VALUE}}
Content: Created on {{DATE:YYYY-MM-DD}}

# ✗ Bad - Inconsistent format
File Name: {{DATE:YYYY-MM-DD}} {{VALUE}}
Content: Created on {{DATE:MM/DD/YYYY}}
```

### 4. Test Incrementally

1. Create basic capture
2. Test capture works
3. Add template processing
4. Test template
5. Add macro steps
6. Test full workflow

## Integration with PKM Workflows

### Meeting Note Quick Capture

**Step 1:** Quick capture to daily note (during meeting)

```markdown
### (log::⏱ {{TIME:HH:mm ZZ}}: {{VALUE}})

scope::
start::
```

**Step 2:** Later, extract to structured note using extraction command

### Project Creation Workflow

**Macro: "New Project"**

1. Input: Project name
2. Create project note (`templates/project.md`)
3. Create project tasks folder
4. Create project meetings folder
5. Link project to current area/company note
6. Open project note for editing

### Daily Note Setup

**Macro: "Daily Note"**

1. Check if today's daily note exists
2. If not, create from template
3. Link to yesterday's daily note
4. Link to this week's weekly note
5. Open daily note
6. Set cursor at "## Notes" section

## References

- **Official Repository:** https://github.com/chhoumann/quickadd
- **Community Examples:** https://obsidian.md/community/quickadd
- **Date Formats:** Uses Moment.js format strings

---

**📝 Note:** This reference needs to be expanded with content from the official Quickadd documentation. The patterns above are based on common use cases but should be verified against the official docs.
