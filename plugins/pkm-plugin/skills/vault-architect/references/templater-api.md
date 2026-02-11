# Templater API Reference

Complete reference for Templater plugin internal functions and patterns.

**Official Documentation:** https://silentvoid13.github.io/Templater/

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [tp.file Module](#tpfile-module)
3. [tp.date Module](#tpdate-module)
4. [tp.system Module](#tpsystem-module)
5. [tp.frontmatter Module](#tpfrontmatter-module)
6. [tp.obsidian Module](#tpobsidian-module)
7. [tp.config Module](#tpconfig-module)
8. [tp.web Module](#tpweb-module)
9. [User Functions](#user-functions)
10. [Multi-Select Patterns](#multi-select-patterns)
11. [Common Patterns](#common-patterns)

## Core Concepts

### Template Syntax

```javascript
<% /* JavaScript code */ %>          // Code execution (no output)
<%= expression %>                    // Output expression result
<%* /* JavaScript code */ %>         // Code execution with await support
<%- expression %>                    // Output without escaping HTML
<%+ template_name %>                 // Include another template
```

### Template Context

- Templates execute in a sandboxed JavaScript environment
- All `tp.*` functions are available in template scope
- Can use async/await with `<%* %>` syntax
- Access to Obsidian API via `tp.obsidian`

## tp.file Module

File manipulation and metadata access functions.

**Documentation:** https://silentvoid13.github.io/Templater/internal-functions/internal-modules/file-module.html

### tp.file.content

Get the current file's content.

```javascript
<% tp.file.content %>
```

**Returns:** String containing file content

### tp.file.creation_date(format?)

Get file creation date.

```javascript
<%= tp.file.creation_date() %>                    // Default format
<%= tp.file.creation_date("YYYY-MM-DD") %>       // Custom format
<%= tp.file.creation_date("dddd, MMMM Do YYYY") %>
```

**Parameters:**
- `format` (optional): Moment.js format string

**Returns:** Formatted date string

### tp.file.create_new(template, filename?, open_new?, folder?)

Create a new file from template.

```javascript
<%* await tp.file.create_new("templates/daily-note", "2026-02-10", false, "Daily Notes") %>
```

**Parameters:**
- `template`: Template file to use (path or name)
- `filename` (optional): New file name (without extension)
- `open_new` (optional): Open the new file? (default: false)
- `folder` (optional): Folder path for new file

**Returns:** TFile object for new file

**Example - Create meeting note:**
```javascript
<%*
const title = await tp.system.prompt("Meeting title");
const date = tp.date.now("YYYY-MM-DD");
const filename = `${date} ${title}`;
await tp.file.create_new("Meeting Template", filename, true, "Meetings");
%>
```

### tp.file.cursor(order?)

Set cursor position after template insertion.

```javascript
Meeting with <% tp.file.cursor(1) %> on <% tp.file.cursor(2) %>
```

**Parameters:**
- `order` (optional): Cursor position order (for multiple cursors)

**Usage:** After template inserts, cursor jumps to first tp.file.cursor() position. Press Tab to jump to next position.

### tp.file.cursor_append(content)

Append content at cursor position after template.

```javascript
<%* tp.file.cursor_append("## Notes\n\n") %>
```

**Parameters:**
- `content`: String to append at cursor

### tp.file.exists(filepath)

Check if file exists.

```javascript
<%* if (!tp.file.exists("Daily Notes/2026-02-10.md")) {
    await tp.file.create_new("daily-template", "2026-02-10", false, "Daily Notes");
} %>
```

**Parameters:**
- `filepath`: File path to check (relative or absolute)

**Returns:** Boolean

### tp.file.find_tfile(filename)

Find TFile object by name.

```javascript
<%* const file = tp.file.find_tfile("My Note") %>
```

**Parameters:**
- `filename`: File name (with or without extension)

**Returns:** TFile object or null

### tp.file.folder(relative?)

Get current file's folder path.

```javascript
<%= tp.file.folder() %>              // Full path
<%= tp.file.folder(true) %>          // Relative to vault
```

**Parameters:**
- `relative` (optional): Return relative path? (default: false)

**Returns:** String folder path

### tp.file.include(file)

Include content from another file.

```javascript
<%* tp.file.include("[[Templates/Header]]") %>
```

**Parameters:**
- `file`: File to include (wikilink or path)

**Returns:** File content as string

### tp.file.last_modified_date(format?)

Get file's last modified date.

```javascript
<%= tp.file.last_modified_date("YYYY-MM-DD HH:mm") %>
```

**Parameters:**
- `format` (optional): Moment.js format string

**Returns:** Formatted date string

### tp.file.move(new_path, file_to_move?)

Move/rename file.

```javascript
<%* await tp.file.move("/Archive/" + tp.file.title) %>
<%* await tp.file.move("/Work/Projects/Project-" + tp.file.title) %>
```

**Parameters:**
- `new_path`: New file path (must include filename)
- `file_to_move` (optional): TFile to move (default: current file)

**Returns:** Promise\<void>

### tp.file.path(relative?)

Get current file's full path.

```javascript
<%= tp.file.path() %>                // Full path
<%= tp.file.path(true) %>            // Relative to vault
```

**Parameters:**
- `relative` (optional): Return relative path? (default: false)

**Returns:** String file path

### tp.file.rename(new_title)

Rename current file.

```javascript
<%* await tp.file.rename("New File Name") %>
```

**Parameters:**
- `new_title`: New file name (without extension)

**Returns:** Promise\<void>

### tp.file.selection()

Get selected text when template is triggered.

```javascript
Original: <% tp.file.selection() %>
Modified: <% tp.file.selection().toUpperCase() %>
```

**Returns:** String of selected text

**Example - Wrap selection in callout:**
```javascript
> [!note]
> <% tp.file.selection() %>
```

### tp.file.tags

Get file's tags array.

```javascript
<%= tp.file.tags %>                  // All tags
<%= tp.file.tags.join(", ") %>      // Comma-separated
```

**Returns:** Array of tag strings (with # prefix)

### tp.file.title

Get file name without extension.

```javascript
# <%= tp.file.title %>
```

**Returns:** String filename

## tp.date Module

Date manipulation and formatting functions.

**Documentation:** https://silentvoid13.github.io/Templater/internal-functions/internal-modules/date-module.html

### tp.date.now(format?, offset?, reference?, reference_format?)

Get current date/time with optional offset.

```javascript
<%= tp.date.now() %>                                    // Default format
<%= tp.date.now("YYYY-MM-DD") %>                       // ISO date
<%= tp.date.now("YYYY-MM-DD HH:mm") %>                 // Date + time
<%= tp.date.now("dddd, MMMM Do YYYY") %>               // Long format
<%= tp.date.now("YYYY-MM-DD", 0) %>                    // Today
<%= tp.date.now("YYYY-MM-DD", -1) %>                   // Yesterday
<%= tp.date.now("YYYY-MM-DD", 1) %>                    // Tomorrow
<%= tp.date.now("YYYY-MM-DD", 7) %>                    // Next week
<%= tp.date.now("YYYY-MM-DD", 0, "2026-01-01") %>     // From reference date
```

**Parameters:**
- `format` (optional): Moment.js format string (default: "YYYY-MM-DD")
- `offset` (optional): Days offset (negative for past, positive for future)
- `reference` (optional): Reference date string
- `reference_format` (optional): Format of reference date

**Returns:** Formatted date string

**Common Formats:**
```
YYYY-MM-DD              → 2026-02-10
YYYY-MM-DD HH:mm        → 2026-02-10 14:30
dddd, MMMM Do YYYY      → Monday, February 10th 2026
MMMM YYYY               → February 2026
YYYY-[W]WW              → 2026-W07
```

### tp.date.tomorrow(format?)

Get tomorrow's date.

```javascript
<%= tp.date.tomorrow("YYYY-MM-DD") %>
```

**Parameters:**
- `format` (optional): Moment.js format string

**Returns:** Formatted date string

### tp.date.yesterday(format?)

Get yesterday's date.

```javascript
<%= tp.date.yesterday("YYYY-MM-DD") %>
```

**Parameters:**
- `format` (optional): Moment.js format string

**Returns:** Formatted date string

### tp.date.weekday(format?, offset?, reference?)

Get weekday with offset.

```javascript
<%= tp.date.weekday("YYYY-MM-DD", 0) %>    // This Monday
<%= tp.date.weekday("YYYY-MM-DD", 1) %>    // Next Monday
<%= tp.date.weekday("YYYY-MM-DD", -1) %>   // Last Monday
```

**Parameters:**
- `format` (optional): Moment.js format string
- `offset` (optional): Week offset
- `reference` (optional): Reference date

**Returns:** Formatted date string for Monday of week

## tp.system Module

User interaction and system functions.

### tp.system.clipboard()

Get clipboard content.

```javascript
Pasted: <% tp.system.clipboard() %>
```

**Returns:** String from clipboard

**Example - Create note from clipboard:**
```javascript
<%*
const content = tp.system.clipboard();
if (content.includes("http")) {
    tR += `[Link](${content})`;
}
%>
```

### tp.system.prompt(prompt_text?, default_value?, throw_on_cancel?, multiline?)

Prompt user for text input.

```javascript
<%* const name = await tp.system.prompt("Enter name") %>
<%* const description = await tp.system.prompt("Description", "Default text") %>
<%* const notes = await tp.system.prompt("Notes", "", false, true) %>  // Multiline
```

**Parameters:**
- `prompt_text` (optional): Prompt message
- `default_value` (optional): Pre-filled text
- `throw_on_cancel` (optional): Throw error if cancelled? (default: false)
- `multiline` (optional): Multi-line input? (default: false)

**Returns:** Promise\<string> or null if cancelled

**Example - Required field:**
```javascript
<%*
let title = null;
while (!title) {
    title = await tp.system.prompt("Meeting title (required)");
    if (!title) {
        new Notice("Title is required!");
    }
}
%>
```

### tp.system.suggester(text_items, items, throw_on_cancel?, placeholder?, limit?)

Prompt user to select from list.

```javascript
<%*
const options = ["Meeting", "Call", "Email"];
const type = await tp.system.suggester(options, options);
%>
Selected: <%= type %>
```

**Parameters:**
- `text_items`: Array of strings to display
- `items`: Array of values to return (same length as text_items)
- `throw_on_cancel` (optional): Throw error if cancelled?
- `placeholder` (optional): Placeholder text
- `limit` (optional): Max items to show

**Returns:** Promise\<T> selected item or null if cancelled

**Example - With different display vs. values:**
```javascript
<%*
const companies = ["Palo Alto Networks", "Acme Corp", "SASE Ltd"];
const folders = ["PAN", "Acme", "SASE"];
const selected = await tp.system.suggester(companies, folders);
%>
Folder: <%= selected %>
```

**Example - From file list:**
```javascript
<%*
const files = app.vault.getMarkdownFiles();
const fileNames = files.map(f => f.basename);
const selectedName = await tp.system.suggester(fileNames, fileNames);
const selectedFile = files.find(f => f.basename === selectedName);
%>
```

## Multi-Select Patterns

Templater doesn't have built-in multi-select, but you can implement it with suggester loops.

### Pattern 1: Add items until done

```javascript
<%*
const allPeople = ["Alice", "Bob", "Charlie", "Diana"];
const attendees = [];

while (true) {
    const remaining = allPeople.filter(p => !attendees.includes(p));
    if (remaining.length === 0) break;

    const person = await tp.system.suggester(
        [...remaining, "✓ Done"],
        [...remaining, null],
        false,
        "Add attendee"
    );

    if (person === null) break;
    attendees.push(person);
}
%>
Attendees: <%= attendees.map(p => `[[${p}]]`).join(", ") %>
```

### Pattern 2: Toggle selection with checkmarks

```javascript
<%*
const allTags = ["project", "meeting", "urgent", "followup"];
const selectedTags = [];

while (true) {
    const options = allTags.map(tag =>
        selectedTags.includes(tag) ? `☑ ${tag}` : `☐ ${tag}`
    );
    options.push("✓ Done");

    const choice = await tp.system.suggester(
        options,
        [...allTags, "DONE"]
    );

    if (choice === "DONE") break;

    if (selectedTags.includes(choice)) {
        selectedTags.splice(selectedTags.indexOf(choice), 1);
    } else {
        selectedTags.push(choice);
    }
}
%>
Tags: <%= selectedTags.map(t => `#${t}`).join(" ") %>
```

### Pattern 3: Multi-select from notes

```javascript
<%*
// Get all Person notes
const personFiles = app.vault.getMarkdownFiles()
    .filter(f => f.path.includes("People/"));
const personNames = personFiles.map(f => f.basename);
const attendees = [];

while (true) {
    const available = personNames.filter(p => !attendees.includes(p));
    const displayOptions = [
        ...available.map(p => `Add: ${p}`),
        ...(attendees.length > 0 ? ["✓ Done"] : [])
    ];

    if (available.length === 0) break;

    const choice = await tp.system.suggester(
        displayOptions,
        [...available, null],
        false,
        `Selected: ${attendees.length}`
    );

    if (choice === null) break;
    attendees.push(choice);
}
%>
attendees: [<%- attendees.map(p => `"[[${p}]]"`).join(", ") %>]
```

## tp.frontmatter Module

Access frontmatter properties.

```javascript
<%= tp.frontmatter.title %>
<%= tp.frontmatter["my-property"] %>
<%= tp.frontmatter.tags %>
```

**Returns:** Value of frontmatter property

**Note:** Returns undefined if property doesn't exist.

## tp.obsidian Module

Access Obsidian API.

**Documentation:** https://silentvoid13.github.io/Templater/internal-functions/internal-modules/obsidian-module.html

```javascript
<%* tp.obsidian.Notice("Hello!") %>
<%* new tp.obsidian.Notice("Template applied", 3000) %>
```

**Common Uses:**
- `tp.obsidian.Notice(message, duration)` - Show notification
- `tp.obsidian.normalizePath(path)` - Normalize file path
- `app.vault` - Vault API
- `app.workspace` - Workspace API
- `app.metadataCache` - Metadata cache

## tp.config Module

Template configuration and context.

```javascript
<%= tp.config.active_file %>         // TFile object
<%= tp.config.run_mode %>            // "CreateNewFromTemplate", "AppendActiveFile", etc.
<%= tp.config.target_file %>         // Target TFile
<%= tp.config.template_file %>       // Template TFile
```

## tp.web Module

Web requests (requires user function).

```javascript
<%* const response = await tp.web.daily_quote() %>
```

**Note:** Requires defining web functions in Templater settings.

## User Functions

Custom functions defined in Templater settings.

**Example user function (in Templater settings):**

```javascript
// File: scripts/get_weekly_note.js
function get_weekly_note(tp) {
    const weekNumber = tp.date.now("WW");
    const year = tp.date.now("YYYY");
    return `${year}-W${weekNumber}`;
}
module.exports = get_weekly_note;
```

**Usage in template:**
```javascript
Weekly Note: [[<% tp.user.get_weekly_note(tp) %>]]
```

## Common Patterns

### Daily Note Template

```markdown
---
date: <% tp.date.now("YYYY-MM-DD") %>
day: <% tp.date.now("dddd") %>
week: [[<% tp.date.now("YYYY-[W]WW") %>]]
tags:
  - daily-note
---

# <% tp.date.now("YYYY-MM-DD") %> - <% tp.date.now("dddd") %>

## Schedule

-

## Notes

<% tp.file.cursor(1) %>

## Meetings

```dataviewjs
const today = "<% tp.date.now("YYYY-MM-DD") %>";
// Query meetings for today
```

---
Previous: [[<% tp.date.yesterday("YYYY-MM-DD") %>]] | Next: [[<% tp.date.tomorrow("YYYY-MM-DD") %>]]
```

### Meeting Note Template

```markdown
<%*
// Prompt for meeting details
const title = await tp.system.prompt("Meeting title");
const type = await tp.system.suggester(
    ["Customer Meeting", "Internal", "1-on-1", "Standup"],
    ["customer-meeting", "internal", "one-on-one", "standup"]
);

// Multi-select attendees
const allPeople = app.vault.getMarkdownFiles()
    .filter(f => f.path.includes("People/"))
    .map(f => f.basename);
const attendees = [];

while (true) {
    const remaining = allPeople.filter(p => !attendees.includes(p));
    if (remaining.length === 0) break;

    const person = await tp.system.suggester(
        [...remaining, "✓ Done"],
        [...remaining, null],
        false,
        `Attendees: ${attendees.length}`
    );

    if (person === null) break;
    attendees.push(person);
}

// Get current folder for company context
const folder = tp.file.folder(true);
const company = folder.split("/")[1] || "General";

// Set filename
const date = tp.date.now("YYYY-MM-DD");
const filename = `${date} ${title}`;
await tp.file.rename(filename);
%>
---
title: "<%= title %>"
fileClass: Meeting
scope: ["[[<%= company %>]]"]
attendees: [<%- attendees.map(p => `"[[${p}]]"`).join(", ") %>]
start: <% tp.date.now("YYYY-MM-DD") %>T<% tp.file.cursor(1) %>
type: "<%= type %>"
tags:
  - action/scheduled
---

# <%= title %>

## Attendees

<%- attendees.map(p => `- [[${p}]]`).join("\n") %>

## Agenda

<% tp.file.cursor(2) %>

## Notes

<% tp.file.cursor(3) %>

## Action Items

- [ ]
```

### Context-Aware File Creation

```javascript
<%*
// Infer context from current note
const currentFile = tp.file.title;
const currentFolder = tp.file.folder(true);

// Extract company from folder structure
const pathParts = currentFolder.split("/");
const company = pathParts.find(p => p.includes("Company")) || "General";

// Create related note
const noteName = await tp.system.prompt("Note name");
const newFile = await tp.file.create_new(
    "templates/project-note",
    noteName,
    false,
    currentFolder + "/Projects"
);

// Link to new note
tR += `Created: [[${noteName}]]`;
%>
```

### Conditional Template Logic

```javascript
<%*
const noteType = await tp.system.suggester(
    ["Project", "Person", "Company"],
    ["project", "person", "company"]
);

if (noteType === "project") {
%>
---
fileClass: Project
status: active
---

# Project: <% tp.file.cursor(1) %>

## Overview

## Tasks

<%* } else if (noteType === "person") { %>
---
fileClass: Person
employer: <% tp.file.cursor(1) %>
---

# <% tp.file.cursor(2) %>

## Contact Info

## Notes

<%* } else { %>
---
fileClass: Company
industry: <% tp.file.cursor(1) %>
---

# <% tp.file.cursor(2) %>

## Overview

<%* } %>
```

### Batch File Creation

```javascript
<%*
const count = parseInt(await tp.system.prompt("How many notes?"));
const prefix = await tp.system.prompt("Note prefix");

for (let i = 1; i <= count; i++) {
    const filename = `${prefix}-${i.toString().padStart(2, '0')}`;
    await tp.file.create_new(
        "templates/basic-note",
        filename,
        false,
        tp.file.folder(true)
    );
}

new tp.obsidian.Notice(`Created ${count} notes`);
%>
```

## Best Practices

### 1. Error Handling

```javascript
<%*
try {
    const result = await tp.system.prompt("Input");
    if (!result) throw new Error("Cancelled");
    // Process result
} catch (error) {
    new tp.obsidian.Notice(`Error: ${error.message}`);
}
%>
```

### 2. Validate User Input

```javascript
<%*
let email = "";
while (!/^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/.test(email)) {
    email = await tp.system.prompt("Enter valid email");
    if (!email) {
        new tp.obsidian.Notice("Email is required");
    }
}
%>
```

### 3. Reusable Logic in User Functions

Instead of complex template logic, create user functions:

```javascript
// templates/scripts/meeting_helpers.js
function formatAttendees(attendeesList) {
    return attendeesList.map(name => `[[${name}]]`).join(", ");
}

function inferCompanyFromFolder(folderPath) {
    const parts = folderPath.split("/");
    return parts.find(p => !p.includes("Notes") && !p.includes("Meetings"));
}

module.exports = { formatAttendees, inferCompanyFromFolder };
```

### 4. Use YAML Arrays for Lists

```yaml
# ✓ Good - Proper YAML array
attendees: ["[[Alice]]", "[[Bob]]", "[[Charlie]]"]

# ✗ Bad - String concatenation
attendees: "[[Alice]], [[Bob]], [[Charlie]]"
```

### 5. Keep Templates Maintainable

- Extract complex logic to user functions
- Use descriptive variable names
- Add comments for non-obvious logic
- Break long templates into smaller includes

## Troubleshooting

### Template doesn't execute

- Check for syntax errors in JavaScript
- Ensure `<%* %>` for async operations
- Verify Templater plugin is enabled

### Suggester returns null

- User cancelled - handle null case
- Check `throw_on_cancel` parameter

### File creation fails

- Verify folder exists
- Check file naming (no invalid characters: `\ / : * ? " < > |`)
- Ensure unique filename (doesn't already exist)

### Variables not working

- Use `<%* %>` for variable assignment
- Use `<%= %>` to output variable value
- Check variable scope (defined before usage)

## References

- **Official Documentation:** https://silentvoid13.github.io/Templater/
- **GitHub Repository:** https://github.com/SilentVoid13/Templater
- **Moment.js Formats:** https://momentjs.com/docs/#/displaying/format/
