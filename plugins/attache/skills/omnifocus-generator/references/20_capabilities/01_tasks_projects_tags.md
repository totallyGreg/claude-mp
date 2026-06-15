# Tasks, Projects, and Tags

<!-- DRAFT — review during D2 integration -->

**What this covers:** Creating, reading, updating, and organizing Tasks, Projects, Tags, and Folders via the Omni Automation API.

**What this does NOT cover:** Perspectives, UI/Forms, Foundation Models. See `02_perspectives.md`, `03_forms_ui.md`, `04_foundation_models.md`.

---

## 1. First-Stop Solution: Check `ofoCore`

Before writing any Task/Project/Tag CRUD code, check whether `ofoCore` already exposes it:

```js
var ofoCore = PlugIn.find("com.totallytools.omnifocus.attache").library("ofoCore");
```

**ofoCore exports (as of D6):**
| Function | What it does |
|----------|-------------|
| `getTask(id)` | Fetch task by primaryKey |
| `updateTask(id, fields)` | Mutate name/note/dueDate/deferDate/flagged/tags/estimatedMinutes |
| `createTask(fields)` | Create task in inbox or project |
| `completeTask(id)` | Mark complete via `markComplete()` (safe) |
| `tagTask(id, {add, remove})` | Add/remove tags by name |
| `getProject(id)` | Fetch project by identifier |
| `createProject(fields)` | Create project in folder with status/review interval |
| `updateProject(id, fields)` | Mutate name/status/folder/sequential/note/reviewInterval |
| `markProjectReviewed(id)` | Set `lastReviewDate` |
| `listFolders(opts)` | List folder hierarchy |
| `listWaitingFor(opts)` | Tasks with waitingTag older than threshold |
| `listSomedayMaybe(opts)` | Tasks in somedayTag or somedayFolder |
| `listNeglectedProjects(opts)` | Projects not modified in N days |
| `listRecentlyCompleted(opts)` | Tasks completed since date |
| `listProjectsForReview(opts)` | Projects whose nextReviewDate ≤ beforeDate |

If what you need is there, **consume via library** — do not reimplement.

---

## 2. Native Omni Automation Classes

### Task

**Constructor:**
```js
new Task("Task name", inbox.ending)          // → Task in inbox
new Task("Task name", project.ending)        // → Task in project
new Task("Sub-task", parentTask.ending)      // → Task group child
```

**Key properties (read/write unless noted):**
```js
task.name                    // String
task.note                    // String
task.dueDate                 // Date | null
task.deferDate               // Date | null
task.flagged                 // Boolean
task.sequential              // Boolean (children must complete in order)
task.estimatedMinutes        // Number | null (macOS v3.5+)
task.plannedDate             // Date | null (v4.7+ — intention to work on date)

// Read-only computed
task.completed               // Boolean (read-only; use markComplete())
task.completionDate          // Date | null (read-only)
task.taskStatus              // Task.Status
task.containingProject       // Project | null
task.parent                  // Task | null
task.tags                    // TagArray (read-only)
task.effectiveDueDate        // Date | null (inherits from container)
task.effectiveDeferDate      // Date | null
task.inInbox                 // Boolean
task.modified                // Date | null
```

**Key methods:**
```js
task.markComplete()                          // Safe — use this, never task.completed = true
task.markIncomplete()
task.drop(allOccurrences)                    // allOccurrences: Boolean
task.addTag(tag)                             // tag: Tag object
task.addTags([tag1, tag2])
task.removeTag(tag)
task.removeTags([tag1, tag2])
task.clearTags()                             // v3.8+
task.appendStringToNote("text")
task.addNotification(dateOrOffset)
task.removeNotification(notification)
task.addAttachment(fileWrapper)
task.removeAttachmentAtIndex(i)
task.addLinkedFileURL(url)
task.apply(fn)                               // recursive descent into children
```

**Class functions:**
```js
Task.byIdentifier("abc123")                  // returns Task | null
Task.byParsingTransportText("text")          // parse TaskPaper-style → Task[]
```

**Task.Status enum:**
```
Task.Status.Available, Blocked, Completed, Dropped, DueSoon, Next, Overdue
```

**Insertion locations:**
```js
inbox.beginning / inbox.ending
project.beginning / project.ending
task.before / task.after / task.beginning / task.ending
```

**⚠️ Footguns:**
- `task.completed = true` **FAILS via Apple Events** (JXA context). Always use `task.markComplete()`.
- `Task.byIdentifier()` is a **class function**, not an instance method on arrays.
- `task.tags[0]` may be undefined — check length first.

---

### Project

**Constructor:**
```js
new Project("Project name", library.ending)           // top-level
new Project("Project name", folder.ending)            // in folder
new Project("Project name", anotherProject.after)     // after another
```

**Key properties:**
```js
project.name
project.note
project.status              // Project.Status — Active, OnHold, Done, Dropped
project.sequential          // Boolean
project.dueDate / project.deferDate
project.flagged
project.lastReviewDate      // Date (read/write for marking reviewed)
project.nextReviewDate      // Date (computed)
project.reviewInterval      // Project.ReviewInterval {steps, unit}
project.parentFolder        // Folder | null (read-only)
project.task                // root Task (read-only)
project.flattenedTasks      // TaskArray (all tasks recursively)
project.nextTask            // Task | null (first available)
```

**Key methods:**
```js
project.markComplete()
project.markIncomplete()
project.taskNamed("name")                    // → Task | null
project.addTag(tag) / project.clearTags()
project.appendStringToNote("text")
```

**Project.Status enum:**
```
Project.Status.Active, OnHold, Done, Dropped
```

**Project.ReviewInterval:**
```js
project.reviewInterval.steps  // Number (e.g. 14)
project.reviewInterval.unit   // String (e.g. "days", "weeks", "months")
```

**⚠️ Footguns:**
- `Project.byIdentifier(id)` is the lookup function (class function, not array method).
- Status is `Project.Status.OnHold` (not `"OnHold"` string) when comparing.
- Setting `project.lastReviewDate = new Date()` marks it reviewed — OmniFocus recomputes `nextReviewDate` automatically.

---

### Tag

**Constructor:**
```js
new Tag("Tag name", database.tags.ending)    // top-level
new Tag("Child", parentTag.ending)           // child tag
```

**Key properties:**
```js
tag.name
tag.parent                   // Tag | null
tag.status                   // Tag.Status (Active, OnHold, Dropped)
tag.allowsNextAction         // Boolean
tag.childrenAreMutuallyExclusive  // Boolean (v4.7+) — only one child assignable at once
tag.tasks                    // TaskArray (read-only)
tag.availableTasks           // TaskArray (available only)
tag.remainingTasks           // TaskArray (incomplete)
tag.tags                     // TagArray (child tags)
Tag.forecastTag              // Tag | null (class property — the Forecast Tag)
```

**Key methods:**
```js
tag.tagNamed("name")                         // → Tag | null
tag.apply(fn)                                // recursive descent
tag.moveTasks([task1], location)             // reorder tasks within tag
tag.beforeTask(task)                         // location before task in tag
tag.beginningOfTasks                         // location before all tag tasks
```

**Tag.Status enum:**
```
Tag.Status.Active, OnHold, Dropped
```

**⚠️ Footguns:**
- `database.tagNamed("X")` is the lookup for top-level tags.
- `tag.childrenAreMutuallyExclusive` is v4.7+ only — guard with version check if supporting older OF.
- Tag ordering within a task: use `task.afterTag(tag)`, `task.beforeTag(tag)`, `task.moveTag(tag, location)` (v4.0+).

---

### Folder

**Constructor:**
```js
new Folder("Folder name", library.ending)
new Folder("Sub-folder", parentFolder.ending)
```

**Key properties:**
```js
folder.name
folder.parent               // Folder | null
folder.status               // Folder.Status (Active, Dropped)
folder.projects             // ProjectArray (direct children only)
folder.folders              // FolderArray (direct child folders)
folder.sections             // SectionArray (projects + folders, has byName())
folder.flattenedProjects    // ProjectArray (recursive)
folder.flattenedFolders     // FolderArray (recursive)
```

**Key methods:**
```js
folder.folderNamed("name")   // → Folder | null
folder.projectNamed("name")  // → Project | null
folder.apply(fn)             // recursive descent
Folder.byIdentifier("id")    // class function → Folder | null
```

---

## 3. Database-Level Operations

```js
// Lookup
database.tagNamed("name")        // → Tag | null (top-level only)
database.folderNamed("name")     // → Folder | null (top-level only)
database.projectNamed("name")    // → Project | null (top-level only)
database.taskNamed("name")       // → Task | null (inbox top-level only)

// Search (Quick Open behavior)
database.tagsMatching("wait")    // → Tag[] matching search
database.foldersMatching("proj") // → Folder[]
database.projectsMatching("key") // → Project[]

// Flat iteration (entire database)
flattenedTasks                   // TaskArray — all tasks
flattenedProjects                // ProjectArray — all projects
flattenedFolders                 // FolderArray — all folders
flattenedTags                    // TagArray — all tags

// Move / Duplicate
database.moveTasks([task], location)
database.duplicateTasks([task], location)
database.moveSections([project], folderOrLocation)
database.duplicateSections([project], folderOrLocation)
database.moveTags([tag], location)
database.convertTasksToProjects([task], folderOrLocation)
database.deleteObject(object)
database.save()                  // persist + trigger sync
database.cleanUp()               // file inbox items into projects
```

---

## 4. Reach-Out Trigger

If the method you need isn't documented here or in `30_api_reference/omnifocus_api.md`:

```
WebFetch https://omni-automation.com/omnifocus/task.html   (or project.html / tag.html / folder.html / database.html)
Prompt: "I need the exact signature for [METHOD]. List parameters, return type, and version requirements."
```

See `50_external/web_fetch_protocol.md` for the full fetch template.
