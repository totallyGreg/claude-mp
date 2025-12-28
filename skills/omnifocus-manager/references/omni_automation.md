# OmniFocus Omni Automation Reference

Complete reference for Omni Automation, the native JavaScript-based automation framework for OmniFocus.

## Overview

Omni Automation is OmniFocus's modern, device-independent JavaScript automation framework. Unlike JXA (JavaScript for Automation) or AppleScript, Omni Automation:

- Works on both macOS and iOS/iPadOS
- Runs natively within OmniFocus (no external scripting required)
- Uses a clean, documented JavaScript API
- Supports plug-ins for reusable automation
- Integrates with Shortcuts and other iOS automation

**When to Use:**
- Cross-platform automation (Mac and iOS)
- Building reusable plug-ins
- User-triggered automation within OmniFocus
- Integration with iOS Shortcuts

## Getting Started

### Running Scripts

**Within OmniFocus:**
1. Console: View → Automation → Console (⌃⌥⌘I)
2. Type JavaScript code directly
3. Scripts run in the context of the current document

**As Plug-Ins:**
1. Create plug-in bundle (.omnifocusjs directory - see `omnifocus_plugin_structure.md`)
2. Install in OmniFocus
3. Trigger via Tools → Plug-In Name

**Via URL:**
```
omnifocus:///omnijs-run?script=<encoded-script>
```

### Basic Script Structure

```javascript
(() => {
    const app = Application.currentApplication();
    app.includeStandardAdditions = true;

    const omniFocus = Application('OmniFocus');
    const doc = omniFocus.defaultDocument;

    // Your automation code here

    return "Success!";
})();
```

## Core Objects

### Application

Access OmniFocus application instance:

```javascript
const omniFocus = Application('OmniFocus');
const doc = omniFocus.defaultDocument;
```

### Document

The main document containing all OmniFocus data:

```javascript
const doc = omniFocus.defaultDocument;

// Access data
doc.flattenedTasks()    // All tasks
doc.flattenedProjects()  // All projects
doc.flattenedTags()     // All tags
doc.folders()           // All folders
doc.inboxTasks()        // Inbox tasks
```

### Task

Properties:
- `name` - Task name (string)
- `note` - Task description (string)
- `completed` - Completion status (boolean, read-only)
- `completionDate` - When completed (Date)
- `flagged` - Flag status (boolean)
- `dueDate` - Due date (Date)
- `deferDate` - Defer/start date (Date)
- `dropDate` - When dropped (Date)
- `estimatedMinutes` - Time estimate (number)
- `taskStatus` - Status enum (Available, Blocked, Completed, Dropped, DueSoon, Next, Overdue)
- `tags` - Array of Tag objects
- `containingProject` - Parent Project object
- `parent` - Parent Task or Project
- `children` - Array of child Tasks
- `sequential` - Sequential flag (boolean)
- `attachments` - Array of file attachments
- `linkedFileURLs` - Array of linked file URLs

Methods:
- `markComplete(date)` - Mark task complete
- `markIncomplete()` - Mark task incomplete
- `drop(allOccurrences)` - Drop the task
- `addTag(tag)` - Add a single tag
- `addTags([tag1, tag2])` - Add multiple tags
- `removeTag(tag)` - Remove a tag
- `removeTags([tag1, tag2])` - Remove multiple tags
- `clearTags()` - Remove all tags
- `addAttachment(fileWrapper)` - Add file attachment
- `addLinkedFileURL(url)` - Add linked file
- `removeAttachmentAtIndex(index)` - Remove attachment

### Project

Properties:
- `name` - Project name
- `note` - Project description
- `status` - Status (active, on-hold, completed, dropped)
- `flagged` - Flag status
- `dueDate` - Due date
- `deferDate` - Defer date
- `completedByChildren` - Auto-complete when children complete
- `sequential` - Sequential flag
- `tags` - Array of tags
- `tasks` - Array of tasks in project
- `folder` - Containing folder

### Tag

Properties:
- `name` - Tag name
- `active` - Active status
- `availableTaskCount` - Number of available tasks

### Folder

Properties:
- `name` - Folder name
- `projects` - Projects in folder
- `folders` - Subfolders

## Common Patterns

### Querying Tasks

**Get Today's Tasks:**
```javascript
(() => {
    const doc = omniFocus.defaultDocument;
    const tasks = doc.flattenedTasks();

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const todayTasks = tasks.filter(task => {
        if (task.completed()) return false;

        const due = task.dueDate();
        const defer = task.deferDate();

        return (due >= today && due < tomorrow) ||
               (defer >= today && defer < tomorrow);
    });

    return todayTasks.map(t => t.name());
})();
```

**Get Flagged Tasks:**
```javascript
(() => {
    const doc = omniFocus.defaultDocument;
    const tasks = doc.flattenedTasks();

    const flagged = tasks.filter(task =>
        task.flagged() && !task.completed()
    );

    return flagged.map(t => ({
        name: t.name(),
        project: t.containingProject() ? t.containingProject().name() : 'Inbox',
        due: t.dueDate()
    }));
})();
```

**Search Tasks:**
```javascript
(() => {
    const doc = omniFocus.defaultDocument;
    const searchTerm = "meeting";

    const tasks = doc.flattenedTasks();
    const matches = tasks.filter(task => {
        const name = task.name().toLowerCase();
        const note = task.note() ? task.note().toLowerCase() : '';
        return name.includes(searchTerm) || note.includes(searchTerm);
    });

    return matches.map(t => t.name());
})();
```

**Tasks Due Soon:**
```javascript
(() => {
    const doc = omniFocus.defaultDocument;
    const days = 7;

    const now = new Date();
    const future = new Date();
    future.setDate(future.getDate() + days);

    const tasks = doc.flattenedTasks();
    const dueSoon = tasks.filter(task => {
        if (task.completed()) return false;
        const due = task.dueDate();
        return due && due >= now && due <= future;
    });

    return dueSoon.map(t => ({
        name: t.name(),
        due: t.dueDate()
    }));
})();
```

### Creating Tasks

**Simple Inbox Task:**
```javascript
(() => {
    const doc = omniFocus.defaultDocument;

    const task = new Task("Buy groceries");
    doc.inboxTasks.push(task);

    return "Created: " + task.name();
})();
```

**Task with All Properties:**
```javascript
(() => {
    const doc = omniFocus.defaultDocument;

    // Create task
    const task = new Task("Project Review");
    task.note = "Prepare slides and metrics";
    task.flagged = true;
    task.dueDate = new Date("2025-12-30T14:00:00");
    task.deferDate = new Date("2025-12-28");
    task.estimatedMinutes = 90;

    // Find or create project
    let project = doc.flattenedProjects().find(p => p.name() === "Q4 Planning");
    if (!project) {
        project = new Project("Q4 Planning");
        doc.projects.push(project);
    }

    // Add to project
    project.tasks.push(task);

    // Add tags
    const urgentTag = doc.flattenedTags().find(t => t.name() === "urgent");
    if (urgentTag) {
        task.addTag(urgentTag);
    }

    return "Created: " + task.name();
})();
```

### Updating Tasks

**Mark Task Complete:**
```javascript
(() => {
    const doc = omniFocus.defaultDocument;

    const task = doc.flattenedTasks().find(t =>
        t.name() === "Call dentist"
    );

    if (task) {
        task.markComplete();
        return "Completed: " + task.name();
    }

    return "Task not found";
})();
```

**Update Task Properties:**
```javascript
(() => {
    const doc = omniFocus.defaultDocument;

    const task = doc.flattenedTasks().find(t =>
        t.name() === "Review proposal"
    );

    if (task) {
        task.dueDate = new Date("2025-12-31");
        task.flagged = true;
        task.note = "Updated priority";
        return "Updated: " + task.name();
    }

    return "Task not found";
})();
```

**Add Tags to Task:**
```javascript
(() => {
    const doc = omniFocus.defaultDocument;

    const task = doc.flattenedTasks().find(t =>
        t.name() === "Important meeting"
    );

    if (!task) return "Task not found";

    // Find tags
    const urgentTag = doc.flattenedTags().find(t => t.name() === "urgent");
    const meetingTag = doc.flattenedTags().find(t => t.name() === "meeting");

    // Add tags
    if (urgentTag) task.addTag(urgentTag);
    if (meetingTag) task.addTag(meetingTag);

    return "Tags added to: " + task.name();
})();
```

### Working with Projects

**List All Projects:**
```javascript
(() => {
    const doc = omniFocus.defaultDocument;
    const projects = doc.flattenedProjects();

    return projects.map(p => ({
        name: p.name(),
        status: p.status(),
        tasks: p.tasks().length
    }));
})();
```

**Create Project with Tasks:**
```javascript
(() => {
    const doc = omniFocus.defaultDocument;

    // Create project
    const project = new Project("Website Redesign");
    project.note = "Q4 project for new website";
    project.sequential = true;
    doc.projects.push(project);

    // Add tasks
    const tasks = [
        "Research competitors",
        "Create wireframes",
        "Design mockups",
        "Development",
        "Testing"
    ];

    tasks.forEach(taskName => {
        const task = new Task(taskName);
        project.tasks.push(task);
    });

    return "Created project with " + tasks.length + " tasks";
})();
```

## Plug-In Development

**For complete plug-in documentation, see `omnifocus_plugin_structure.md`:**
- Full manifest.json schema with all available fields
- Complete bundle structure and file organization
- Step-by-step creation guide
- Action script templates and patterns
- Installation and testing procedures
- Common Glob/Grep patterns for working with plugins

**Important:** `.omnifocusjs` is a directory bundle, not a single file. See `omnifocus_plugin_structure.md` for detailed explanation of bundle structure and how to work with plugin files.

### Plug-In Structure

A plug-in is a directory bundle with `.omnifocusjs` extension containing:

```
MyPlugin.omnifocusjs/
├── manifest.json
└── Resources/
    ├── script.js
    └── icon.png (optional)
```

### Manifest File

```json
{
  "identifier": "com.example.myplugin",
  "version": "1.0",
  "author": "Your Name",
  "description": "Plugin description",
  "label": "My Plugin",
  "mediumLabel": "My Plugin",
  "paletteLabel": "My Plugin",
  "actions": [
    {
      "identifier": "myAction",
      "label": "Do Something",
      "mediumLabel": "Do Something",
      "paletteLabel": "Do Something"
    }
  ]
}
```

### Example Plug-In: Today's Tasks

**manifest.json:**
```json
{
  "identifier": "com.example.todaystasks",
  "version": "1.0",
  "author": "Your Name",
  "description": "Show tasks due or deferred to today",
  "label": "Today's Tasks",
  "actions": [
    {
      "identifier": "showToday",
      "label": "Show Today's Tasks"
    }
  ]
}
```

**Resources/showToday.js:**
```javascript
(() => {
    const action = new PlugIn.Action(function(selection, sender) {
        const doc = Document.defaultDocument;
        const tasks = doc.flattenedTasks;

        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);

        const todayTasks = tasks.filter(task => {
            if (task.completed) return false;

            const due = task.dueDate;
            const defer = task.deferDate;

            return (due && due >= today && due < tomorrow) ||
                   (defer && defer >= today && defer < tomorrow);
        });

        // Display results
        const alert = new Alert("Today's Tasks", `Found ${todayTasks.length} tasks`);
        todayTasks.forEach(task => {
            const project = task.containingProject;
            const projectName = project ? project.name : "Inbox";
            alert.message += `\n• ${task.name} (${projectName})`;
        });
        alert.show();
    });

    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
```

## Integration

### Shortcuts Integration (iOS/macOS)

Omni Automation scripts can be triggered from Shortcuts:

```
Run Script Over OmniFocus
  Script: <your JavaScript code>
```

### URL Scheme

```
omnifocus:///omnijs-run?script=<url-encoded-javascript>
```

**Example:**
```javascript
// JavaScript to encode:
(() => {
    const task = new Task("Quick task");
    Document.defaultDocument.inboxTasks.push(task);
})();

// URL:
omnifocus:///omnijs-run?script=%28%29%3D%3E%7B...
```

## Best Practices

1. **Error Handling:**
   ```javascript
   try {
       const task = doc.flattenedTasks().find(...);
       if (!task) throw new Error("Task not found");
       task.markComplete();
   } catch (error) {
       console.error("Error:", error.message);
       new Alert("Error", error.message).show();
   }
   ```

2. **User Feedback:**
   ```javascript
   const alert = new Alert("Success", "Task created!");
   alert.show();
   ```

3. **Validation:**
   ```javascript
   action.validate = function(selection, sender) {
       // Return true if action should be enabled
       return selection.tasks.length > 0;
   };
   ```

4. **Selection Context:**
   ```javascript
   const selection = document.windows[0].content.selectedNodes;
   const selectedTasks = selection.filter(node => node instanceof Task);
   ```

## Resources

- **Official Documentation:** [omni-automation.com/omnifocus](https://omni-automation.com/omnifocus/)
- **Tutorial:** [omni-automation.com/omnifocus/tutorial](https://omni-automation.com/omnifocus/tutorial/)
- **Plug-In Library:** [omni-automation.com/omnifocus/actions.html](https://omni-automation.com/omnifocus/actions.html)
- **Community:** [Omni Automation Forum](https://discourse.omnigroup.com/c/omni-automation)

## Comparison: Omni Automation vs JXA

| Feature | Omni Automation | JXA |
|---------|----------------|-----|
| Platform | Mac + iOS | Mac only |
| Environment | Within OmniFocus | External script |
| API | Native OmniFocus API | AppleScript bridge |
| Plug-ins | Built-in support | N/A |
| Shortcuts | Native integration | Limited |
| Performance | Fast | Slower (bridge overhead) |
| Debugging | Built-in console | External tools |

**Recommendation:** Use Omni Automation for most automation tasks, especially if you need iOS support or want to create reusable plug-ins. Use JXA only when you need to integrate with external Mac automation or when Omni Automation doesn't provide the needed functionality.
