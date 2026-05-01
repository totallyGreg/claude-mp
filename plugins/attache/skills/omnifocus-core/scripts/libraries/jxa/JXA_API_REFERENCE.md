# OmniFocus JXA API Quick Reference

Reference for correct OmniFocus JavaScript for Automation (JXA) patterns.
Consult this before editing any `.js` file in this directory.

## Constructors

**MUST use `app.*()`, NEVER `app.defaultDocument.*()`**

```javascript
// CORRECT
app.Task({ name: "..." })
app.Project({ name: "..." })
app.Tag({ name: "..." })
app.Folder({ name: "..." })

// WRONG — causes -1700 Can't convert types
app.defaultDocument.Task({ name: "..." })
app.defaultDocument.Project({ name: "..." })
```

## Adding Objects to the Document

```javascript
doc.inboxTasks.push(task)       // add task to inbox
doc.projects.push(project)      // add project to root
doc.folders.push(folder)        // add folder to root
doc.tags.push(tag)              // add tag to root level
parentTag.tags.push(childTag)   // nest tag under parent
project.tasks.push(task)        // add task to project
groupTask.tasks.push(subtask)   // add subtask to action group
```

## Tag Operations on Tasks

```javascript
// CORRECT — use app.add() bridge pattern
app.add(tag, { to: task.tags })     // apply tag to task
app.remove(tag, { from: task.tags }) // remove tag from task
task.tags()                          // get array of tags on task

// WRONG — task.addTag() causes "Can't convert types" error
// Despite being documented, addTag()/removeTag() are broken in JXA.
// task.addTag(tag)      // BROKEN — use app.add() instead
// task.removeTag(tag)   // BROKEN — use app.remove() instead
// task.clearTags()      // status unknown — prefer iterating with app.remove()
```

## Tag Hierarchy Management

```javascript
// Rename (preserves all task associations)
tag.name = "New Name"

// Reparent (preserves all task associations)
newParent.tags.push(tag)    // moves tag under newParent

// Move to root level
doc.tags.push(tag)

// Delete
app.delete(tag)             // CORRECT
// tag.delete()             // WRONG for tags — use app.delete()
```

## Tag Lookup

```javascript
doc.flattenedTags.whose({ name: "..." })[0]   // find by exact name
doc.flattenedTags()                             // all tags flattened
tag.tags()                                      // direct children
tag.flattenedTags()                             // all descendants
tag.remainingTaskCount()                        // open tasks with this tag
tag.availableTaskCount()                        // available tasks with this tag
```

## Projects as Tasks (Workaround)

Projects inherit from Task internally. Use the flattenedTasks
workaround to access task-level operations on projects:

```javascript
// CORRECT — tag a project
var projectTask = doc.flattenedTasks.whose({ id: project.id() })[0];
app.add(tag, { to: projectTask.tags });

// WRONG — causes -1700 error
project.addTag(tag);
```

## Common Gotchas

1. **`whose()[0]` throws on empty results.** Unlike normal arrays, accessing `[0]` on an empty `whose()` result throws "Can't convert types" instead of returning `undefined`. Always check `whose().length > 0` before accessing `[0]`.

2. **`app.delete(obj)` is the correct delete pattern** for tags and other non-task objects. `task.delete()` works for tasks but don't assume it works for everything.

3. **Tag names are not unique across levels.** `flattenedTags.whose({name})` may return multiple matches. Use `--id` when precision is needed.

4. **Moving a tag preserves task associations.** Tasks reference the tag object, not its position in the hierarchy.
