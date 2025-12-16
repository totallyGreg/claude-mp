# Templater Patterns and Examples

This document provides common Templater patterns and code snippets for creating dynamic Obsidian templates.

## Core Templater Functions

### User Input

```javascript
// Simple text prompt
const name = await tp.system.prompt("Enter name:");

// Prompt with default value
const title = await tp.system.prompt("Title?", tp.file.title);

// Suggester - choose from list
const category = await tp.system.suggester(
  (item) => item.name,        // Display format
  [                           // Array of options
    {name: "Meeting", folder: "Meetings"},
    {name: "Note", folder: "Notes"}
  ]
);

// Suggester with simple array
const customer = await tp.system.suggester(
  (item) => item,
  ["Customer A", "Customer B", "Customer C"]
);

// Multi-line input (not built-in, requires user to paste)
const notes = await tp.system.prompt("Paste your notes:");
```

### File Operations

```javascript
// Rename current file
await tp.file.rename(newFileName);

// Move file (relative to vault root)
await tp.file.move("folder/subfolder/" + fileName);

// Move and rename in one operation
await tp.file.move("folder/" + newFileName);

// Get file creation date
tp.file.creation_date("YYYY-MM-DD")

// Get current file title (before rename)
tp.file.title

// Set cursor position (use after template execution)
tp.file.cursor(1)  // Primary cursor position
tp.file.cursor(2)  // Secondary position (tab to jump)

// Include another template
tp.file.include("[[Template Name]]")

// Focus the editor (useful at end of template)
app.workspace.activeLeaf.view.editor?.focus();
```

### Date Operations

```javascript
// Current date
tp.date.now("YYYY-MM-DD")

// Date with offset (days)
tp.date.now("YYYY-MM-DD", -1)  // Yesterday
tp.date.now("YYYY-MM-DD", 1)   // Tomorrow

// Custom format
tp.date.now("dddd, MMMM Do, YYYY")  // "Monday, December 15th, 2025"

// Parse and format a reference date
tp.date.now("YYYY-MM-DD", 0, tp.file.title, "YYYY-MM-DD")

// Week number
tp.date.now("YYYY-[W]WW")  // "2025-W50"

// Quarter
tp.date.now("Q")  // "4"
tp.date.now("YYYY[-Q]Q")  // "2025-Q4"
```

## Common Template Patterns

### Pattern 1: Simple Note with Auto-Categorization

```markdown
<%*
// Determine folder based on tags
const noteType = await tp.system.suggester(
  (item) => item.label,
  [
    {label: "Idea", folder: "Ideas", tag: "idea"},
    {label: "Reference", folder: "References", tag: "reference"},
    {label: "Project", folder: "Projects", tag: "project"}
  ]
);

// Prompt for title
const title = await tp.system.prompt("Note title?", tp.file.title);

// Move to appropriate folder
await tp.file.move(noteType.folder + "/" + title);
-%>
---
title: <% title %>
tags: [<% noteType.tag %>]
date created: <% tp.file.creation_date() %>
---
# <% title %>

<% tp.file.cursor(1) %>
```

### Pattern 2: Person Note with Contact Info

```markdown
<%*
const fullName = await tp.system.prompt("Full Name?", tp.file.title);
if (!fullName) return "";

const email = await tp.system.prompt("Email address:");
const company = await tp.system.prompt("Company:");

await tp.file.move("People/" + fullName);
-%>
---
title: <% fullName %>
tags: [person]
aliases:
  - <% fullName %>
<% if (email) { %>  - <% email %><% } %>
email: <% email || "" %>
company: <% company ? "[[" + company + "]]" : "" %>
---
# <% fullName %>

<% if (company) { %>Company: [[<% company %>]]<% } %>
<% if (email) { %>Email: <% email %><% } %>

## Notes

<% tp.file.cursor(1) %>

![[People.base#Person Card]]
```

### Pattern 3: Meeting Note with Date and Attendees

```markdown
<%*
const meetingDate = tp.date.now("YYYY-MM-DD");
const meetingTitle = await tp.system.prompt("Meeting title?");
const customer = await tp.system.suggester(
  (item) => item,
  // Could be dynamic list from existing customer notes
  ["Customer A", "Customer B", "Customer C", "Internal"]
);

const fileName = meetingDate + " " + meetingTitle;
await tp.file.move("Meetings/" + fileName);
-%>
---
title: <% meetingTitle %>
date: <% meetingDate %>
customer: <% customer !== "Internal" ? "[[" + customer + "]]" : "" %>
tags: [meeting, <% customer === "Internal" ? "internal" : "customer" %>]
---
# <% meetingTitle %>

**Date:** <% tp.date.now("dddd, MMMM Do, YYYY") %>
<% if (customer !== "Internal") { %>**Customer:** [[<% customer %>]]<% } %>

## Attendees
-

## Agenda
<% tp.file.cursor(1) %>

## Notes

## Action Items
- [ ]

## Next Steps

![[Notes.base#Related Files]]
```

### Pattern 4: Daily Note with Temporal Hierarchy

```markdown
---
aliases:
  - <% tp.date.now("dddd MMMM Do, YYYY") %>
tags: [daily]
date: <% tp.file.creation_date() %>
Week: "[[<% tp.date.now("YYYY-[W]WW") %>]]"
Month: "[[<% tp.date.now("YYYY-MM") %>|<% tp.date.now("MMMM") %>]]"
Quarter: "[[<% tp.date.now("YYYY") %>Q<% tp.date.now("Q") %>]]"
Year: "[[<% tp.date.now("YYYY") %>]]"
---
# <% tp.date.now("dddd MMMM Do, YYYY") %>

[[<% tp.date.now("YYYY-MM-DD", -1) %>|← Yesterday]] | [[<% tp.date.now("YYYY-MM-DD", 1) %>|Tomorrow →]]

## Morning

<% tp.file.cursor(1) %>

## Notes

## Evening Reflection

### Wins

### Challenges

### Tomorrow's Focus

![[Daily.base#Todays Notes]]
```

### Pattern 5: Conditional Logic and Error Handling

```markdown
<%*
// Check if title starts with "Untitled" (new file)
let title = tp.file.title;
let finalTitle;

if (title.startsWith("Untitled")) {
  finalTitle = await tp.system.prompt("What is the title?");
  if (!finalTitle) {
    // User cancelled, abort template
    return "";
  }
  await tp.file.rename(finalTitle);
} else {
  finalTitle = title;
}

// Optional abbreviation
const abbrev = await tp.system.prompt("Abbreviation (optional):", "", false, false);

await tp.file.move("Notes/" + finalTitle);
-%>
---
title: <% finalTitle %>
<% if (abbrev) { %>aliases: [<% abbrev %>]<% } %>
tags: [note]
---
# <% finalTitle %>

<% tp.file.cursor(1) %>
```

### Pattern 6: Dynamic Tag Generation

```markdown
<%*
const topic = await tp.system.suggester(
  (item) => item.name,
  [
    {name: "Development", tags: ["dev", "code"]},
    {name: "Design", tags: ["design", "ui"]},
    {name: "Research", tags: ["research", "analysis"]}
  ]
);

const isUrgent = await tp.system.suggester(
  (item) => item,
  ["Yes", "No"]
);

// Build tag list
const tagList = [...topic.tags];
if (isUrgent === "Yes") {
  tagList.push("urgent");
}
-%>
---
tags: [<% tagList.join(", ") %>]
---
```

### Pattern 7: Embedding Reusable Fragments

Create template fragments for reuse:

**Fragment:** `900 Templates/Fragments/Meeting-Header.md`
```markdown
**Date:** <% tp.date.now("YYYY-MM-DD") %>
**Time:** <% tp.date.now("HH:mm") %>

## Attendees
-
```

**Main Template:**
```markdown
---
title: <% title %>
---
# <% title %>

<% tp.file.include("[[Meeting-Header]]") %>

## Notes
<% tp.file.cursor(1) %>
```

## Advanced Patterns

### Pattern 8: Reading Existing Note Data

```javascript
<%*
// Get data from another note
const customerNote = tp.file.find_tfile("CustomerName");
if (customerNote) {
  const customerData = await tp.file.include("[[CustomerName]]");
  // Use the data...
}

// Access frontmatter from current note
const currentFrontmatter = tp.frontmatter;
-%>
```

### Pattern 9: JavaScript Logic in Templates

```javascript
<%*
// Calculate dates
const today = tp.date.now("YYYY-MM-DD");
const nextWeek = tp.date.now("YYYY-MM-DD", 7);

// String manipulation
const acronym = title
  .split(" ")
  .map(word => word[0])
  .join("")
  .toUpperCase();

// Array operations
const tags = ["meeting", "customer"];
const allTags = tags.concat(["work"]);

// Conditional rendering
if (condition) {
  // Output some content
}
-%>
```

### Pattern 10: Combining Suggester with Dynamic Data

```javascript
<%*
// Get list of existing customer notes
const customerFiles = app.vault.getMarkdownFiles()
  .filter(file => file.path.startsWith("Companies/"))
  .map(file => file.basename);

const customer = await tp.system.suggester(
  (item) => item,
  customerFiles
);
-%>
```

## Best Practices

1. **Always handle cancellation** - If user cancels prompt, return empty string
2. **Validate input** - Check for empty strings or invalid data
3. **Use descriptive prompts** - Clear questions get better answers
4. **Set sensible defaults** - Pre-fill prompts when possible
5. **Move files last** - Gather all info, then move once
6. **Focus editor** - End templates with cursor positioning and editor focus
7. **Comment your logic** - Future you will thank present you
8. **Test with edge cases** - What if user cancels? What if title has special characters?

## Debugging

```javascript
<%*
// Log to console (open developer tools to see)
console.log("Debug:", variable);

// Show alert
new Notice("Debug message: " + variable);

// Temporarily output to note
-%>
DEBUG: <% JSON.stringify(variable, null, 2) %>
```

## Common Pitfalls

1. **Don't use quotes inside prompt strings without escaping**
   ```javascript
   // Bad
   await tp.system.prompt("What's your name?");

   // Good
   await tp.system.prompt("What is your name?");
   await tp.system.prompt("What's your name?");  // Actually works in template literals
   ```

2. **File operations are async - use await**
   ```javascript
   // Bad
   tp.file.move("folder/file");  // Might not complete before next line

   // Good
   await tp.file.move("folder/file");
   ```

3. **Template execution blocks are separate**
   ```javascript
   // Can't access variables between different <%* %> blocks
   // Declare at top, use throughout
   ```

## Useful Snippets

### Get Week Start/End Dates

```javascript
<%*
const weekStart = tp.date.now("YYYY-MM-DD", 0, tp.file.title, "YYYY-[W]WW");
const weekEnd = tp.date.now("YYYY-MM-DD", 6, weekStart, "YYYY-MM-DD");
-%>
Week of <% weekStart %> to <% weekEnd %>
```

### Auto-increment Note Number

```javascript
<%*
// Find existing notes with pattern "Note-001", "Note-002", etc.
const notePattern = /Note-(\d{3})/;
const existingNotes = app.vault.getMarkdownFiles()
  .map(f => f.basename)
  .filter(name => notePattern.test(name))
  .map(name => parseInt(notePattern.exec(name)[1]));

const nextNumber = existingNotes.length > 0
  ? Math.max(...existingNotes) + 1
  : 1;

const noteNumber = String(nextNumber).padStart(3, '0');
const noteName = "Note-" + noteNumber;

await tp.file.rename(noteName);
-%>
```

### Create Linked Reference Note

```javascript
<%*
// When creating a note about a term that should link to parent concept
const term = await tp.system.prompt("Term name?");
const parentConcept = await tp.system.prompt("Parent concept:");

await tp.file.move("Terminology/" + term);
-%>
---
title: <% term %>
parent: [[<% parentConcept %>]]
---
# <% term %>

Parent: [[<% parentConcept %>]]

## Definition

<% tp.file.cursor(1) %>
```
