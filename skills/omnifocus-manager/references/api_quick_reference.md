# OmniFocus API Quick Reference

**Purpose:** Fast lookup for code generation - prevents API hallucination and property/method confusion.

**Last Updated:** 2025-12-31
**OmniFocus Version:** 4.8+

---

## Critical Distinction: Properties vs Methods

⚠️ **CRITICAL:** Properties are accessed **without** `()`, methods are called **with** `()`

```javascript
// ✅ CORRECT
const name = task.name;              // Property - no parentheses
const due = task.dueDate;            // Property - no parentheses
task.markComplete();                 // Method - with parentheses
task.addTag(myTag);                  // Method - with parentheses

// ❌ WRONG
const name = task.name();            // ERROR! name is a property
const result = task.markComplete;    // Gets function, doesn't call it
```

---

## Global Variables

OmniFocus exposes these Database properties as **global variables** (no Document.defaultDocument needed):

### Database Collections (Read-Only)
```javascript
flattenedTasks      // TaskArray - ALL tasks in database
flattenedProjects   // ProjectArray - ALL projects
flattenedFolders    // FolderArray - ALL folders
flattenedTags       // TagArray - ALL tags
```

### Top-Level Collections (Read-Only)
```javascript
folders             // FolderArray - root-level folders only
projects            // ProjectArray - root-level projects only
tags                // Tags - root-level tags only
inbox               // Inbox - inbox tasks
library             // Library - folders & projects
```

### Common Classes
```javascript
Document, Task, Project, Folder, Tag
PlugIn, Version, Alert, Form
FileSaver, FileWrapper, Pasteboard
Calendar, LanguageModel
```

---

## Task Class

### Properties (Direct Access - No Parentheses)
| Property | Type | Example | Description |
|----------|------|---------|-------------|
| `name` | String | `task.name` | Task name |
| `note` | String | `task.note` | Task note/description |
| `completed` | Boolean | `task.completed` | Is task completed? |
| `completionDate` | Date\|null | `task.completionDate` | When completed |
| `dropped` | Boolean | `task.dropped` | Is task dropped? |
| `flagged` | Boolean | `task.flagged` | Is task flagged? |
| `dueDate` | Date\|null | `task.dueDate` | Task due date |
| `deferDate` | Date\|null | `task.deferDate` | Task defer date |
| `estimatedMinutes` | Number\|null | `task.estimatedMinutes` | Time estimate |
| `added` | Date | `task.added` | Date task was created |
| `modified` | Date | `task.modified` | Date last modified |
| `tags` | TagArray | `task.tags` | Array of tags |
| `containingProject` | Project\|null | `task.containingProject` | Parent project |
| `taskStatus` | Task.Status | `task.taskStatus` | Status enum |
| `children` | TaskArray | `task.children` | Child tasks |
| `flattenedTasks` | TaskArray | `task.flattenedTasks` | All descendant tasks |

### Methods (Function Calls - Require Parentheses)
| Method | Returns | Example | Description |
|--------|---------|---------|-------------|
| `markComplete()` | Task | `task.markComplete()` | Mark complete |
| `markIncomplete()` | Task | `task.markIncomplete()` | Mark incomplete |
| `drop(shouldDrop)` | Task | `task.drop(true)` | Drop/undrop task |
| `addTag(tag)` | void | `task.addTag(myTag)` | Add tag to task |
| `removeTag(tag)` | void | `task.removeTag(myTag)` | Remove tag |
| `clearTags()` | void | `task.clearTags()` | Remove all tags |
| `remove()` | void | `task.remove()` | Delete task |

### Common Patterns
```javascript
// Create new inbox task
const newTask = new Task("Task name", inbox);
newTask.note = "Task details";
newTask.dueDate = new Date("2025-12-31");
newTask.flagged = true;

// Filter tasks
const activeTasks = flattenedTasks.filter(t => !t.completed && !t.dropped);
const flaggedTasks = flattenedTasks.filter(t => t.flagged && !t.completed);

// Mark complete
task.markComplete();

// Add tags
const tag = tags.byName("work");
if (tag) task.addTag(tag);
```

---

## Project Class

### Properties (Direct Access)
| Property | Type | Example | Description |
|----------|------|---------|-------------|
| `name` | String | `project.name` | Project name |
| `note` | String | `project.note` | Project note |
| `status` | Project.Status | `project.status` | Active/On Hold/Done/Dropped |
| `completed` | Boolean | `project.completed` | Is completed? |
| `completionDate` | Date\|null | `project.completionDate` | When completed |
| `dueDate` | Date\|null | `project.dueDate` | Project due date |
| `deferDate` | Date\|null | `project.deferDate` | Project defer date |
| `flagged` | Boolean | `project.flagged` | Is flagged? |
| `tags` | TagArray | `project.tags` | Tags on project |
| `task` | Task | `project.task` | Root task of project |
| `flattenedTasks` | TaskArray | `project.flattenedTasks` | All tasks in project |
| `parentFolder` | Folder\|null | `project.parentFolder` | Containing folder |

### Methods
| Method | Returns | Example | Description |
|--------|---------|---------|-------------|
| `markComplete()` | Project | `project.markComplete()` | Mark complete |
| `markIncomplete()` | Project | `project.markIncomplete()` | Mark incomplete |
| `addTag(tag)` | void | `project.addTag(tag)` | Add tag |

### Common Patterns
```javascript
// Create new project
const folder = folders.byName("Work");
const newProject = new Project("Project name", folder);

// Access project's tasks
const projectTasks = project.flattenedTasks;
const incompleteTasks = projectTasks.filter(t => !t.completed);

// Change status
project.status = Project.Status.OnHold;
```

---

## Folder Class

### Properties (Direct Access)
| Property | Type | Example | Description |
|----------|------|---------|-------------|
| `name` | String | `folder.name` | Folder name |
| `note` | String | `folder.note` | Folder note |
| `folders` | FolderArray | `folder.folders` | Child folders |
| `projects` | ProjectArray | `folder.projects` | Projects in folder |
| `flattenedFolders` | FolderArray | `folder.flattenedFolders` | All descendant folders |
| `flattenedProjects` | ProjectArray | `folder.flattenedProjects` | All descendant projects |

### Methods
| Method | Returns | Example | Description |
|--------|---------|---------|-------------|
| `folderNamed(name)` | Folder\|null | `folder.folderNamed("Sub")` | Find child folder |
| `projectNamed(name)` | Project\|null | `folder.projectNamed("Proj")` | Find child project |

### Common Patterns
```javascript
// Find folder by name
const workFolder = folders.byName("Work");

// Create subfolder
const newFolder = new Folder("Subfolder", workFolder);

// Iterate projects in folder
folder.projects.forEach(project => {
    console.log(project.name);
});
```

---

## Tag Class

### Properties (Direct Access)
| Property | Type | Example | Description |
|----------|------|---------|-------------|
| `name` | String | `tag.name` | Tag name |
| `allowsNextAction` | Boolean | `tag.allowsNextAction` | Next action tag? |
| `tags` | TagArray | `tag.tags` | Child tags |
| `flattenedTags` | TagArray | `tag.flattenedTags` | All descendant tags |
| `tasks` | TaskArray | `tag.tasks` | Tasks with this tag |
| `flattenedTasks` | TaskArray | `tag.flattenedTasks` | All tagged tasks |
| `projects` | ProjectArray | `tag.projects` | Projects with tag |
| `flattenedProjects` | ProjectArray | `tag.flattenedProjects` | All tagged projects |

### Common Patterns
```javascript
// Find tag by name
const workTag = tags.byName("work");

// Get all tasks with tag
const taggedTasks = workTag.flattenedTasks;

// Create new tag
const newTag = new Tag("urgent");
```

---

## LanguageModel (Apple Foundation Models)

### Session Class
```javascript
// Create session
const session = new LanguageModel.Session();
const session = new LanguageModel.Session("system instructions");

// Simple text response
const response = await session.respond("prompt text");

// Structured response with schema
const schema = LanguageModel.Schema.fromJSON({...});
const jsonResponse = await session.respondWithSchema("prompt", schema);
const data = JSON.parse(jsonResponse);
```

### Schema Format (NOT JSON Schema!)

**⚠️ CRITICAL:** OmniFocus uses **custom schema format**, NOT JSON Schema!

```javascript
// ✅ CORRECT - OmniFocus Schema Format
const schema = LanguageModel.Schema.fromJSON({
    name: "person-schema",
    properties: [
        {name: "firstName"},
        {name: "lastName", isOptional: true},
        {
            name: "tags",
            schema: {arrayOf: {constant: "tag"}}
        },
        {
            name: "priority",
            schema: {
                anyOf: [
                    {constant: "high"},
                    {constant: "medium"},
                    {constant: "low"}
                ]
            }
        }
    ]
});

// ❌ WRONG - JSON Schema (doesn't work!)
new LanguageModel.Schema({  // NOT a constructor!
    type: "object",
    properties: {
        name: {type: "string"}
    }
});
```

**Schema Patterns:**
- **Object with properties:** `properties: [{name: "field"}]`
- **Array of strings:** `{arrayOf: {constant: "item"}}`
- **Array of objects:** `{arrayOf: {name: "schema", properties: [...]}}`
- **Enum:** `{anyOf: [{constant: "val1"}, {constant: "val2"}]}`
- **Optional:** `{name: "field", isOptional: true}`

---

## Form Class

### Creating Forms
```javascript
const form = new Form();

// Add fields
form.addField(new Form.Field.String("name", "Label", "default"));
form.addField(new Form.Field.Date("date", "Date", new Date()));
form.addField(new Form.Field.Checkbox("flag", "Checkbox", true));
form.addField(new Form.Field.Option(
    "choice",
    "Select One",
    ["Option 1", "Option 2"],  // values
    null,                       // names (null = use values)
    "Option 1"                  // default
));

// Show form
const result = await form.show("Title", "OK");
if (!result) return; // User cancelled

const values = result.values;
const name = values["name"];
```

---

## Alert Class

```javascript
// Simple alert
const alert = new Alert("Title", "Message");
alert.show();

// Alert with options
const alert = new Alert("Title", "Message");
alert.addOption("Option 1");
alert.addOption("Option 2");
const choice = await alert.show();  // Returns 0, 1, 2...
```

---

## FileSaver & Pasteboard

### FileSaver
```javascript
const saver = new FileSaver();
saver.nameLabel = "Save as:";
saver.defaultFileName = "report.md";

const url = await saver.show();
if (url) {
    url.write("file contents");  // Write string to URL
}
```

### Pasteboard
```javascript
// Copy to clipboard
Pasteboard.general.string = "text to copy";

// Read from clipboard
const text = Pasteboard.general.string;
```

---

## Common Anti-Patterns to AVOID

### ❌ WRONG: Using Document.defaultDocument
```javascript
// ❌ WRONG
const doc = Document.defaultDocument;
const tasks = doc.flattenedTasks;

// ✅ CORRECT - Use global variables
const tasks = flattenedTasks;
```

### ❌ WRONG: Calling properties as functions
```javascript
// ❌ WRONG
const name = task.name();
const completed = task.completed();

// ✅ CORRECT
const name = task.name;
const completed = task.completed;
```

### ❌ WRONG: Using .bind(this) on arrow functions
```javascript
// ❌ WRONG
tasks.forEach(t => {
    console.log(this.name);
}.bind(this));

// ✅ CORRECT - Arrow functions inherit 'this'
tasks.forEach(t => {
    console.log(this.name);
});
```

### ❌ WRONG: Using new LanguageModel.Schema()
```javascript
// ❌ WRONG - Not a constructor!
const schema = new LanguageModel.Schema({...});

// ✅ CORRECT - Use factory method
const schema = LanguageModel.Schema.fromJSON({...});
```

### ❌ WRONG: Using non-existent APIs
```javascript
// ❌ These don't exist:
Progress              // No Progress class
Document.defaultDocument.flattenedTasks  // Use global flattenedTasks
FileType.fromExtension()  // Doesn't exist
new LanguageModel.Schema()  // Not a constructor
```

---

## Quick Validation Checklist

Before suggesting any OmniFocus code:

- [ ] All classes verified in this document
- [ ] Properties accessed without `()`
- [ ] Methods called with `()`
- [ ] Using global variables (flattenedTasks, folders, etc.) not Document.defaultDocument
- [ ] LanguageModel.Schema uses `fromJSON()` factory method
- [ ] Schema uses OmniFocus format (properties array), not JSON Schema
- [ ] No `.bind(this)` on arrow functions
- [ ] No hallucinated APIs (Progress, etc.)

---

## See Also

- **Complete API:** `OmniFocus-API.md` - Full API documentation
- **Validation Rules:** `code_generation_validation.md` - Code validation guidelines
- **Examples:** `../assets/examples/` - Working code patterns
- **Plugin Guide:** `plugin_development_guide.md` - Creating plugins

---

**Generated:** 2025-12-31
**OmniFocus Version:** 4.8+
**API Version:** Omni Automation 1.0
