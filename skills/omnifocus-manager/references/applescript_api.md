# OmniFocus AppleScript API Reference

Complete reference for the OmniFocus AppleScript API, which is accessible through JXA (JavaScript for Automation).

## Overview

The OmniFocus AppleScript API provides programmatic access to all OmniFocus data and functionality. This API is accessible through both traditional AppleScript and JXA (JavaScript for Automation).

**Note:** The JXA scripts in this skill use this API. This reference documents the underlying API structure.

## Application Object

The root object for accessing OmniFocus.

```javascript
const omniFocus = Application('OmniFocus');
const doc = omniFocus.defaultDocument;
```

### Properties

- `version` (text) - OmniFocus version number
- `defaultDocument` (document) - The main OmniFocus document
- `name` (text) - Application name

## Document Object

The main container for all OmniFocus data.

### Accessing the Document

```javascript
const doc = Application('OmniFocus').defaultDocument;
```

### Properties

- `name` (text) - Document name
- `modified` (boolean) - Whether document has unsaved changes
- `path` (text) - File path to document

### Collections

#### Projects

```javascript
// Get all projects (top-level only)
doc.projects()

// Get all projects including nested
doc.flattenedProjects()
```

#### Tasks

```javascript
// Get inbox tasks
doc.inboxTasks()

// Get all tasks (flattened hierarchy)
doc.flattenedTasks()
```

#### Tags

```javascript
// Get all tags
doc.flattenedTags()
```

#### Folders

```javascript
// Get all folders
doc.folders()

// Get flattened folders
doc.flattenedFolders()
```

### Methods

- `save()` - Save the document
- `undo()` - Undo last action
- `redo()` - Redo last undone action

## Task Object

Represents an individual task in OmniFocus.

### Properties

#### Basic Properties

- `name` (text) - Task name
- `note` (text) - Task note/description
- `id` (text) - Persistent identifier (read-only)
- `completed` (boolean) - Completion status (read-only)
- `completionDate` (date) - When task was completed
- `dropped` (boolean) - Whether task is dropped (read-only)
- `dropDate` (date) - When task was dropped

#### Scheduling Properties

- `dueDate` (date) - When task is due
- `deferDate` (date) - When task should start (defer until)
- `effectiveDueDate` (date) - Inherited or explicit due date (read-only)
- `effectiveDeferDate` (date) - Inherited or explicit defer date (read-only)

#### Status Properties

- `flagged` (boolean) - Whether task is flagged
- `taskStatus` (enum) - Current status (read-only)
  - `Available` - Can be worked on now
  - `Blocked` - Waiting on other tasks
  - `Completed` - Finished
  - `Dropped` - Abandoned
  - `DueSoon` - Due within 24 hours
  - `Next` - Next available task in sequential project
  - `Overdue` - Past due date

#### Organization Properties

- `containingProject` (project) - Parent project (read-only)
- `parentTask` (task) - Parent task if this is a subtask (read-only)
- `tasks` (list of tasks) - Child tasks
- `sequential` (boolean) - Whether children must be done in order
- `repetitionRule` (text) - Recurrence pattern
- `numberOfAvailableTasks` (integer) - Available child tasks (read-only)
- `numberOfCompletedTasks` (integer) - Completed child tasks (read-only)

#### Time Properties

- `estimatedMinutes` (integer) - Time estimate in minutes
- `repetition` (repetition) - Recurrence settings

#### Tag Properties

- `tags` (list of tags) - Tags assigned to task
- `primaryTag` (tag) - First tag in list (read-only)

#### Attachment Properties

- `attachments` (list of attachments) - File attachments
- `linkedFileURLs` (list of text) - URLs to linked files

### Methods

#### Completion

```javascript
// Mark complete
task.markComplete();

// Mark complete with specific date
task.markComplete(new Date());

// Mark incomplete
task.markIncomplete();
```

#### Dropping

```javascript
// Drop the task
task.drop();

// Drop with specific date
task.drop(allOccurrences = false);
```

#### Tags

```javascript
// Add single tag
task.addTag(tagObject);

// Add multiple tags
task.addTags([tag1, tag2, tag3]);

// Remove tag
task.removeTag(tagObject);

// Remove multiple tags
task.removeTags([tag1, tag2]);

// Clear all tags
task.clearTags();
```

#### Attachments

```javascript
// Add attachment
task.addAttachment(fileWrapper);

// Add linked file URL
task.addLinkedFileURL("file:///path/to/file");

// Remove attachment by index
task.removeAttachmentAtIndex(0);
```

## Project Object

Represents a project containing tasks.

### Properties

#### Basic Properties

- `name` (text) - Project name
- `note` (text) - Project description
- `id` (text) - Persistent identifier (read-only)
- `status` (enum) - Project status
  - `active` - Currently working on
  - `on hold` - Paused
  - `completed` - Finished
  - `dropped` - Abandoned

#### Scheduling Properties

- `dueDate` (date) - When project is due
- `deferDate` (date) - When project should start
- `completionDate` (date) - When project was completed

#### Status Properties

- `flagged` (boolean) - Whether project is flagged
- `completedByChildren` (boolean) - Auto-complete when all children complete
- `sequential` (boolean) - Whether tasks must be done in order
- `singleton action list` (boolean) - Whether this is a single action list

#### Organization Properties

- `parentFolder` (folder) - Containing folder (read-only)
- `containingProject` (project) - Parent project if this is a subproject (read-only)
- `tasks` (list of tasks) - Tasks in this project
- `flattenedTasks` (list of tasks) - All tasks including in subprojects (read-only)
- `rootTask` (task) - The project as a task object (read-only)

#### Statistics Properties

- `numberOfAvailableTasks` (integer) - Available tasks (read-only)
- `numberOfCompletedTasks` (integer) - Completed tasks (read-only)
- `numberOfDueTasks` (integer) - Tasks due soon (read-only)

#### Tag Properties

- `tags` (list of tags) - Tags assigned to project

### Methods

```javascript
// Mark complete
project.markComplete();

// Mark incomplete
project.markIncomplete();
```

## Tag Object

Represents a tag (formerly called "context").

### Properties

- `name` (text) - Tag name
- `id` (text) - Persistent identifier (read-only)
- `active` (boolean) - Whether tag is active
- `hidden` (boolean) - Whether tag is hidden
- `availableTaskCount` (integer) - Number of available tasks with this tag (read-only)
- `remainingTaskCount` (integer) - Number of remaining tasks with this tag (read-only)
- `parent` (tag) - Parent tag if nested (read-only)

## Folder Object

Represents a folder containing projects.

### Properties

- `name` (text) - Folder name
- `id` (text) - Persistent identifier (read-only)
- `status` (enum) - Folder status
  - `active`
  - `on hold`
  - `dropped`

#### Organization Properties

- `parentFolder` (folder) - Parent folder if nested (read-only)
- `projects` (list of projects) - Projects in this folder
- `folders` (list of folders) - Subfolders
- `flattenedProjects` (list of projects) - All projects including in subfolders (read-only)
- `flattenedFolders` (list of folders) - All subfolders recursively (read-only)

## Creating Objects

### Creating Tasks

```javascript
// Create new task
const task = new Task("Task name");

// Set properties
task.note = "Task description";
task.dueDate = new Date("2025-12-25");
task.flagged = true;

// Add to inbox
doc.inboxTasks.push(task);

// Or add to project
project.tasks.push(task);
```

### Creating Projects

```javascript
// Create new project
const project = new Project("Project name");

// Set properties
project.note = "Project description";
project.sequential = true;
project.deferDate = new Date("2025-12-20");

// Add to document
doc.projects.push(project);

// Or add to folder
folder.projects.push(project);
```

### Creating Tags

```javascript
// Create new tag
const tag = new Tag("Tag name");

// Set properties
tag.active = true;

// Add to document
doc.flattenedTags.push(tag);
```

### Creating Folders

```javascript
// Create new folder
const folder = new Folder("Folder name");

// Add to document
doc.folders.push(folder);

// Or add to another folder
parentFolder.folders.push(folder);
```

## Querying and Filtering

### Finding Objects

```javascript
// Find project by name
const project = doc.flattenedProjects().find(p => p.name() === "Project Name");

// Find task by ID
const task = doc.flattenedTasks().find(t => t.id() === "abc123xyz");

// Find tag by name
const tag = doc.flattenedTags().find(t => t.name() === "urgent");
```

### Filtering Tasks

```javascript
// Active tasks
const activeTasks = doc.flattenedTasks().filter(t =>
    !t.completed() && !t.dropped()
);

// Flagged tasks
const flaggedTasks = doc.flattenedTasks().filter(t =>
    t.flagged() && !t.completed()
);

// Tasks due today
const today = new Date();
today.setHours(0, 0, 0, 0);
const tomorrow = new Date(today);
tomorrow.setDate(tomorrow.getDate() + 1);

const dueToday = doc.flattenedTasks().filter(t => {
    const due = t.dueDate();
    return due && due >= today && due < tomorrow && !t.completed();
});

// Tasks with specific tag
const tag = doc.flattenedTags().find(t => t.name() === "work");
const workTasks = doc.flattenedTasks().filter(t =>
    t.tags().some(taskTag => taskTag.id() === tag.id())
);

// Tasks in project
const projectTasks = project.flattenedTasks().filter(t => !t.completed());
```

## Date Handling

### Creating Dates

```javascript
// From string (ISO 8601)
const date = new Date("2025-12-25T14:30:00");

// From components
const date = new Date(2025, 11, 25, 14, 30, 0);  // Month is 0-indexed!

// Current date
const now = new Date();

// Relative dates
const tomorrow = new Date();
tomorrow.setDate(tomorrow.getDate() + 1);

const nextWeek = new Date();
nextWeek.setDate(nextWeek.getDate() + 7);
```

### Comparing Dates

```javascript
const due = task.dueDate();
const now = new Date();

if (due < now) {
    // Overdue
} else if (due > now) {
    // Future
}
```

### Clearing Dates

```javascript
// Set to null to clear
task.dueDate = null;
task.deferDate = null;
```

## Error Handling

```javascript
try {
    const task = doc.flattenedTasks().find(t => t.name() === "Task Name");
    if (!task) {
        throw new Error("Task not found");
    }
    task.markComplete();
} catch (error) {
    console.error("Error:", error.message);
}
```

## Best Practices

### Use IDs for Reliability

```javascript
// Store task ID
const taskId = task.id();

// Later, find by ID (reliable even if name changes)
const task = doc.flattenedTasks().find(t => t.id() === taskId);
```

### Check Existence Before Operations

```javascript
const task = doc.flattenedTasks().find(t => t.name() === "Task Name");
if (task) {
    // Safe to operate on task
    task.markComplete();
} else {
    console.error("Task not found");
}
```

### Use Flattened Collections

```javascript
// Prefer this (gets all tasks including nested)
doc.flattenedTasks()

// Over this (only gets top-level tasks)
doc.inboxTasks()
```

### Handle Multiple Matches

```javascript
const matches = doc.flattenedTasks().filter(t => t.name() === "Meeting");

if (matches.length === 0) {
    console.error("No tasks found");
} else if (matches.length === 1) {
    // Single match, safe to proceed
    matches[0].markComplete();
} else {
    // Multiple matches, need user to clarify
    console.error("Multiple tasks found:", matches.map(t => ({
        id: t.id(),
        name: t.name(),
        project: t.containingProject() ? t.containingProject().name() : "Inbox"
    })));
}
```

## Common Patterns

### Creating Task with Full Details

```javascript
const task = new Task("Complete project proposal");
task.note = "Include budget, timeline, and deliverables";
task.dueDate = new Date("2025-12-31");
task.deferDate = new Date("2025-12-20");
task.estimatedMinutes = 120;
task.flagged = true;

// Find or create project
let project = doc.flattenedProjects().find(p => p.name() === "Q4 Projects");
if (!project) {
    project = new Project("Q4 Projects");
    doc.projects.push(project);
}

// Add task to project
project.tasks.push(task);

// Add tags
const urgentTag = doc.flattenedTags().find(t => t.name() === "urgent");
if (urgentTag) {
    task.addTag(urgentTag);
}
```

### Batch Completion

```javascript
// Complete all tasks in a project
const project = doc.flattenedProjects().find(p => p.name() === "Old Project");
if (project) {
    project.flattenedTasks().forEach(task => {
        if (!task.completed()) {
            task.markComplete();
        }
    });
}
```

### Rescheduling Tasks

```javascript
// Move all overdue tasks to next week
const now = new Date();
const nextWeek = new Date();
nextWeek.setDate(nextWeek.getDate() + 7);

doc.flattenedTasks().forEach(task => {
    const due = task.dueDate();
    if (due && due < now && !task.completed()) {
        task.dueDate = nextWeek;
    }
});
```

## Comparison: AppleScript vs Omni Automation

| Feature | AppleScript API (via JXA) | Omni Automation |
|---------|---------------------------|-----------------|
| Platform | Mac only | Mac + iOS |
| Access | External scripts | Within OmniFocus |
| Syntax | Uses parentheses: `task.name()` | Direct properties: `task.name` |
| Objects | Application('OmniFocus') | Document.defaultDocument |
| Collections | Methods: `flattenedTasks()` | Properties: `flattenedTasks` |
| New objects | `new Task()` | `new Task()` |

**Key Difference:** Omni Automation uses direct property access while JXA requires method calls with parentheses.

```javascript
// JXA (AppleScript bridge)
const name = task.name();
task.name = "New name";

// Omni Automation
const name = task.name;
task.name = "New name";
```

## Resources

- **OmniFocus AppleScript Documentation:** [support.omnigroup.com/omnifocus-applescript](https://support.omnigroup.com/omnifocus-applescript/)
- **Mac Automation Scripting Guide:** [developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- **JXA Resources:** [github.com/JXA-Cookbook/JXA-Cookbook](https://github.com/JXA-Cookbook/JXA-Cookbook)

## Scripting Dictionary

To view the complete OmniFocus scripting dictionary on your Mac:

```bash
# Extract dictionary to XML
sdef /Applications/OmniFocus.app > omnifocus_dictionary.xml

# View in Script Editor
open -a "Script Editor" /Applications/OmniFocus.app
# Then: File → Open Dictionary → OmniFocus
```
