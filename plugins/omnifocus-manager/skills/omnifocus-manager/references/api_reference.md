# Omni Automation API Reference

This document provides a complete reference for the OmniFocus Omni Automation API. It combines quick reference tables for code generation with the full API specification.

**Last Updated:** 2026-01-17
**OmniFocus Version:** 4.8+

---

## **Part 1: API Quick Reference**

**Purpose:** Fast lookup for code generation - prevents API hallucination and property/method confusion.

---

### Critical Distinction: Properties vs Methods

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

### Global Variables

OmniFocus exposes these Database properties as **global variables** (no Document.defaultDocument needed):

#### Database Collections (Read-Only)
```javascript
flattenedTasks      // TaskArray - ALL tasks in database
flattenedProjects   // ProjectArray - ALL projects
flattenedFolders    // FolderArray - ALL folders
flattenedTags       // TagArray - ALL tags
```

#### Top-Level Collections (Read-Only)
```javascript
folders             // FolderArray - root-level folders only
projects            // ProjectArray - root-level projects only
tags                // Tags - root-level tags only
inbox               // Inbox - inbox tasks
library             // Library - folders & projects
```

#### Common Classes
```javascript
Document, Task, Project, Folder, Tag
PlugIn, Version, Alert, Form
FileSaver, FileWrapper, Pasteboard
Calendar, LanguageModel
```

---

### Task Class

#### Properties (Direct Access - No Parentheses)
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

#### Methods (Function Calls - Require Parentheses)
| Method | Returns | Example | Description |
|--------|---------|---------|-------------|
| `markComplete()` | Task | `task.markComplete()` | Mark complete |
| `markIncomplete()` | Task | `task.markIncomplete()` | Mark incomplete |
| `drop(shouldDrop)` | Task | `task.drop(true)` | Drop/undrop task |
| `addTag(tag)` | void | `task.addTag(myTag)` | Add tag to task |
| `removeTag(tag)` | void | `task.removeTag(myTag)` | Remove tag |
| `clearTags()` | void | `task.clearTags()` | Remove all tags |
| `remove()` | void | `task.remove()` | Delete task |

#### Common Patterns
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

### Project Class

#### Properties (Direct Access)
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

#### Methods
| Method | Returns | Example | Description |
|--------|---------|---------|-------------|
| `markComplete()` | Project | `project.markComplete()` | Mark complete |
| `markIncomplete()` | Project | `project.markIncomplete()` | Mark incomplete |
| `addTag(tag)` | void | `project.addTag(tag)` | Add tag |

#### Common Patterns
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

### Folder Class

#### Properties (Direct Access)
| Property | Type | Example | Description |
|----------|------|---------|-------------|
| `name` | String | `folder.name` | Folder name |
| `note` | String | `folder.note` | Folder note |
| `folders` | FolderArray | `folder.folders` | Child folders |
| `projects` | ProjectArray | `folder.projects` | Projects in folder |
| `flattenedFolders` | FolderArray | `folder.flattenedFolders` | All descendant folders |
| `flattenedProjects` | ProjectArray | `folder.flattenedProjects` | All descendant projects |

#### Methods
| Method | Returns | Example | Description |
|--------|---------|---------|-------------|
| `folderNamed(name)` | Folder\|null | `folder.folderNamed("Sub")` | Find child folder |
| `projectNamed(name)` | Project\|null | `folder.projectNamed("Proj")` | Find child project |

#### Common Patterns
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

### Tag Class

#### Properties (Direct Access)
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

#### Common Patterns
```javascript
// Find tag by name
const workTag = tags.byName("work");

// Get all tasks with tag
const taggedTasks = workTag.flattenedTasks;

// Create new tag
const newTag = new Tag("urgent");
```

---

### LanguageModel (Apple Foundation Models)

#### Session Class
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

#### Schema Format (NOT JSON Schema!)

⚠️ **CRITICAL:** OmniFocus uses **custom schema format**, NOT JSON Schema!

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

### Form Class

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

### Alert Class

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

### FileSaver & Pasteboard

#### FileSaver
```javascript
const saver = new FileSaver();
saver.nameLabel = "Save as:";
saver.defaultFileName = "report.md";

const url = await saver.show();
if (url) {
    url.write("file contents");  // Write string to URL
}
```

#### Pasteboard
```javascript
// Copy to clipboard
Pasteboard.general.string = "text to copy";

// Read from clipboard
const text = Pasteboard.general.string;
```

---

### Common Anti-Patterns to AVOID

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| `Document.defaultDocument` | Old JXA API | Use `flattenedTasks` global |
| `task.name()` | name is a property | Use `task.name` |
| `new LanguageModel.Schema()` | Not a constructor | Use `LanguageModel.Schema.fromJSON()` |
| `Progress` | Doesn't exist | No equivalent |
| `.bind(this)` on arrow functions | Invalid syntax | Arrow functions inherit `this` |

---

### Quick Validation Checklist

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

## **Part 2: Shared API Classes**

These classes are common across all Omni Automation applications (OmniFocus, OmniGraffle, etc.) and provide core functionalities.

### `Alert`
Used to display information or get confirmation from the user.
```javascript
const alert = new Alert("Action Complete", "The task has been processed.");
await alert.show();
```

### `Form`
Used to collect structured input from the user.
```javascript
const form = new Form();
form.addField(new Form.Field.String("name", "Task Name"));
form.addField(new Form.Field.Date("due", "Due Date"));
const formObject = await form.show("Create Task", "OK");
if (formObject) {
    console.log(formObject.values.name);
}
```

### `FileSaver` & `FilePicker`
Used for saving and opening files.
```javascript
// Saving a file
const saver = new FileSaver();
const url = await saver.show();
if(url) url.write("file content");

// Picking a file
const picker = new FilePicker();
const urls = await picker.show();
if(urls.length > 0) console.log(urls[0].lastPathComponent);
```

### `URL`
For handling URLs, including fetching content and creating callbacks.
```javascript
const request = URL.FetchRequest.fromString("https://api.example.com/data");
const response = await request.fetch();
const json = response.bodyString;
```

### Other Shared Classes
*   `Pasteboard`: For clipboard interaction.
*   `Device`: To get information about the current device (macOS vs. iOS).
*   `Credentials`: For securely storing passwords or API keys.
*   `Color`, `Calendar`, `Formatter`, etc.

---

## **Part 3: Full OmniFocus API Specification**

This section contains the raw, detailed, and exhaustive specification for all OmniFocus Omni Automation classes. Use this as the ultimate source of truth.

```
Alert

```
An alert interface for displaying information to the user, blocking further interaction until the alert is dismissed.    
## Constructors  
## new Alert(title: String, message: String) → ++Alert++  
Create a new alert panel with the given title and text contents.    
## Instance Functions  
## function show(callback: ++Function++(‍option: Number‍) or null) → ++Promise++ of Number  
Displays the alert. If no options have yet been added, a default “OK” option is added. Once the user selects an option, the alert is dismissed. If a callback function was supplied, it is invoked with the zero-based index of the selected option as its argument. A Promise is returned as well, which may also be used to collect the result of the Alert.    
## function addOption(string: String)  
Adds an option button to the alert.    
```
Application

```
## Instance Functions  
## function openDocument(from: ++Document++ or null, url: ++URL++, completed: ++Function++(‍documentOrError: ++Document++ or ++Error++, alreadyOpen: Boolean‍))  
Attempts to open the specified document and return a reference to it asynchronously. If the document is already open, the reference is passed along. Note that due to platform sandboxing restrictions, opening the document may fail if the application doesn’t have currently permission to access the given URL. The document, if any, that is associated with the calling script can be passed along to help grant permission to open the new document. The passed in function will be passed two argument. The first will be either either the Document or an Error. On success, the second argument is a Boolean specifying whether the document was already open.    
## Instance Properties  
## var buildVersion → ++Version++ *read-only*  
The internal build version number for the app. See also userVersion.    
## var commandKeyDown → Boolean *read-only*  
Whether the Command key is currently down.    
## var controlKeyDown → Boolean *read-only*  
Whether the Control key is currently down.    
## var name → String *read-only*  
Application name.    
## var optionKeyDown → Boolean *read-only*  
Whether the Option key is currently down.    
## var platformName → String *read-only*  
Returns a string describing the current platform, currently "iOS" or "macOS".    
## var shiftKeyDown → Boolean *read-only*  
Whether the Shift key is currently down.    
## var userVersion → ++Version++ *read-only*  
The user-visible version number for the app. See also buildVersion.    
## var version → String *read-only*  
Deprecated: Recommend using either userVersion or buildVersion.  
For backwards compatibility with existing scripts, this returns the same result as buildVersion.versionString. We recommend using either the user-visible userVersion or the internal buildVersion instead, which are more clear about which version they’re returning and provide their results as Version objects which can be semantically compared with other Version objects.    
```
ApplyResult

```
## Class Properties  
## var SkipChildren → ++ApplyResult++ *read-only*  
The descendants of the current item are skipped.    
## var SkipPeers → ++ApplyResult++ *read-only*  
The unvisited peers of the current item are skipped.    
## var Stop → ++ApplyResult++ *read-only*  
The call to apply terminates with no further items being visited.    
## var all → Array of ++ApplyResult++ *read-only*  
```
Array

```
The built-in JavaScript ++[Array](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array)++ constructor.    
## FolderArray : ++Array++  
An Array containing Folder objects.    
## Instance Functions  
## function byName(name: String) → ++Folder++ or null  
Returns the first Folder contained directly in this array with the given name.    
## ProjectArray : ++Array++  
An Array containing Project objects.    
## Instance Functions  
## function byName(name: String) → ++Project++ or null  
Returns the first Project contained directly in this array with the given name.    
## SectionArray : ++Array++  
An Array containing Project and Folder objects.    
## Instance Functions  
## function byName(name: String) → ++Project++ or ++Folder++ or null  
Returns the first Project or Folder contained directly in this array with the given name.    
## Library : ++SectionArray++  
An Array of folders and projects at the top level of the database. (This can be referenced via the top-level global variable library.)    
## Instance Functions  
## function apply(function: ++Function++(‍section: ++Project++ or ++Folder++‍) → ++ApplyResult++ or null) → ++ApplyResult++ or null  
Calls the given function for each Folder and Project in the Library and recursively into any child folders. Note that the tasks in projects are not included. The supplied function can optionally return a ApplyResult to skip enumeration of some elements.    
## Instance Properties  
## var beginning → ++Folder.ChildInsertionLocation++ *read-only*  
Returns a location referring to the beginning of the top-level projects and folders in the database. (Reference this using library.beginning.)    
## var ending → ++Folder.ChildInsertionLocation++ *read-only*  
Returns a location referring to the ending of the top-level projects and folders in the database. (Reference this using library.ending.)    
## TagArray : ++Array++  
An Array containing Tag objects.    
## Instance Functions  
## function byName(name: String) → ++Tag++ or null  
Returns the first Tag contained directly in this array with the given name.    
## Tags : ++TagArray++  
An Array of tags at the top level of the database.    
## Instance Functions  
## function apply(function: ++Function++(‍tag: ++Tag++‍) → ++ApplyResult++ or null) → ++ApplyResult++ or null  
Calls the given function for each Tag in the Library and recursively into any child tags. The supplied function can optionally return a ApplyResult to skip enumeration of some elements.    
## Instance Properties  
## var beginning → ++Tag.ChildInsertionLocation++ *read-only*  
Returns a location referring to the beginning of the top-level tags in the database.    
## var ending → ++Tag.ChildInsertionLocation++ *read-only*  
Returns a location referring to the ending of the top-level tags in the database.    
## TaskArray : ++Array++  
An Array containing Task objects.    
## Instance Functions  
## function byName(name: String) → ++Task++ or null  
Returns the first Task contained directly in this array with the given name.    
## Inbox : ++TaskArray++  
An Array of tasks that are in the inbox.    
## Instance Functions  
## function apply(function: ++Function++(‍task: ++Task++‍) → ++ApplyResult++ or null) → ++ApplyResult++ or null  
Calls the given function for each Task in the Inbox and recursively into any child tasks. The supplied function can optionally return a ApplyResult to skip enumeration of some elements.    
## Instance Properties  
## var beginning → ++Task.ChildInsertionLocation++ *read-only*  
A location that can be used when adding, duplicating, or moving tasks.    
## var ending → ++Task.ChildInsertionLocation++ *read-only*  
A location that can be used when adding, duplicating, or moving tasks.    
```
Audio

```
## Class Functions  
## function playAlert(alert: ++Audio.Alert++ or null, completed: ++Function++(‍‍) or null)  
Play the specified Audio.Alert. On macOS, if no alert is specified, the user’s default alert sound will be played. On iOS, there is no default alert sound and nothing will be done without specifying an alert.    
```
Audio.Alert

```
## Constructors  
## new Audio.Alert(url: ++URL++) → ++Audio.Alert++  
```
Calendar

```
## Class Properties  
## var buddhist → ++Calendar++ *read-only*  
## var chinese → ++Calendar++ *read-only*  
## var coptic → ++Calendar++ *read-only*  
## var current → ++Calendar++ *read-only*  
The user’s preferred calendar    
## var ethiopicAmeteAlem → ++Calendar++ *read-only*  
## var ethiopicAmeteMihret → ++Calendar++ *read-only*  
## var gregorian → ++Calendar++ *read-only*  
The Gregorian calendar.    
## var hebrew → ++Calendar++ *read-only*  
## var indian → ++Calendar++ *read-only*  
## var islamic → ++Calendar++ *read-only*  
## var islamicCivil → ++Calendar++ *read-only*  
## var islamicTabular → ++Calendar++ *read-only*  
## var islamicUmmAlQura → ++Calendar++ *read-only*  
## var iso8601 → ++Calendar++ *read-only*  
## var japanese → ++Calendar++ *read-only*  
## var persian → ++Calendar++ *read-only*  
## var republicOfChina → ++Calendar++ *read-only*  
## Instance Functions  
## function dateByAddingDateComponents(date: Date, components: ++DateComponents++) → Date or null  
Returns a new Date by adding the given DateComponents, or null if no date could be calculated.    
## function dateFromDateComponents(components: ++DateComponents++) → Date or null  
Returns a new Date from the given DateComponents, or null if no date could be calculated.    
## function dateComponentsFromDate(date: Date) → ++DateComponents++  
Returns a new DateComponents for the given Date.    
## function dateComponentsBetweenDates(start: Date, end: Date) → ++DateComponents++  
Returns the difference from the start Date to the end Date as a DateComponents.    
## function startOfDay(date: Date) → Date  
Returns a Date for the first moment of the day containing the given Date according to this Calendar.    
## Instance Properties  
## var identifier → String *read-only*  
The ISO identifier for the calendar.    
## var locale → ++Locale++ or null *read-only*  
The locale of the calendar.    
## var timeZone → ++TimeZone++ *read-only*  
The time zone of the calendar.    
```
Color

```
## Class Functions  
## function RGB(r: Number, g: Number, b: Number, a: Number or null) → ++Color++  
Makes a new color in the RGB colorspace, with the given components. If the alpha component is not given, 1.0 is used.    
## function hex(hexString: String, a: Number or null) → ++Color++ or null  
Makes a new color in the RGB colorspace from the provided hexadecimal string. If the alpha component is not provided, 1.0 is used.    
## function HSB(h: Number, s: Number, b: Number, a: Number or null) → ++Color++  
Makes a new color in the HSB colorspace, with the given components. If the alpha component is not given, 1.0 is used.    
## function White(w: Number, a: Number or null) → ++Color++  
Makes a new color in the White colorspace, with the given components. If the alpha component is not given, 1.0 is used.    
## Class Properties  
## var black → ++Color++ *read-only*  
A color in the White colorspace with white component of 0.0.    
## var blue → ++Color++ *read-only*  
A color in the RGB colorspace with components (0, 0, 1, 1).    
## var brown → ++Color++ *read-only*  
A color in the RGB colorspace with components (0.6, 0.4, 0.2, 1).    
## var clear → ++Color++ *read-only*  
A color in the White colorspace with white component of 0.0 and alpha of 0.0 (“transparent black”).    
## var cyan → ++Color++ *read-only*  
A color in the RGB colorspace with components (0, 1, 1, 1).    
## var darkGray → ++Color++ *read-only*  
A color in the White colorspace with white component of 0.333.    
## var gray → ++Color++ *read-only*  
A color in the White colorspace with white component of 0.5.    
## var green → ++Color++ *read-only*  
A color in the RGB colorspace with components (0, 1, 0, 1).    
## var lightGray → ++Color++ *read-only*  
A color in the White colorspace with white component of 0.667.    
## var magenta → ++Color++ *read-only*  
A color in the RGB colorspace with components (1, 0, 1, 1).    
## var orange → ++Color++ *read-only*  
A color in the RGB colorspace with components (1, 0.5, 0, 1).    
## var purple → ++Color++ *read-only*  
A color in the RGB colorspace with components (1, 0, 1, 1).    
## var red → ++Color++ *read-only*  
A color in the RGB colorspace with components (1, 0, 0, 1).    
## var white → ++Color++ *read-only*  
A color in the White colorspace with white component of 1.0.    
## var yellow → ++Color++ *read-only*  
A color in the RGB colorspace with components (1, 1, 0, 1).    
## Instance Functions  
## function blend(otherColor: ++Color++, fraction: Number) → ++Color++ or null  
Returns a new color that is a linear combination of the receiver and fraction of the other color (so, a fraction of 1.0 would just return the otherColor. If the colors cannot be blended (for example, if they cannot be converted to the same colorspace), then null is returned.    
## Instance Properties  
## var alpha → Number *read-only*  
Returns the alpha component of the color.    
## var blue → Number *read-only*  
Returns the blue component of the color, after converting to an RGB colorspace.    
## var brightness → Number *read-only*  
Returns the brightness component of the color, after converting to an HSB colorspace.    
## var colorSpace → ++ColorSpace++ *read-only*  
Returns the colorspace of the instance.    
## var green → Number *read-only*  
Returns the green component of the color, after converting to an RGB colorspace.    
## var hex → String *read-only*  
Returns a 6-character hexadecimal string for the color, after converting to an RGB colorspace (ignoring alpha).    
## var hue → Number *read-only*  
Returns the hue component of the color, after converting to an HSB colorspace.    
## var red → Number *read-only*  
Returns the red component of the color, after converting to an RGB colorspace.    
## var saturation → Number *read-only*  
Returns the saturation component of the color, after converting to an HSB colorspace.    
## var white → Number *read-only*  
Returns the white component of the color, after converting to a White colorspace.    
## ColorSpace
...and so on...
<AND THE REST OF THE FILE CONTENT>
