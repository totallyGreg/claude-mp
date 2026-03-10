var args = argument;
var result;

if (args.type === "project") {
  var p = Project.byIdentifier(args.id);
  if (p) {
    result = {
      success: true,
      project: {
        id: p.id.primaryKey,
        name: p.name,
        status: String(p.status),
        completed: p.completed,
        flagged: p.flagged,
        dueDate: p.dueDate ? p.dueDate.toISOString() : null,
        deferDate: p.deferDate ? p.deferDate.toISOString() : null,
        note: p.note,
        tags: p.tags.map(function(tag) { return tag.name; }),
        taskCount: p.flattenedTasks.length,
        sequential: p.sequential,
        parentFolder: p.parentFolder ? p.parentFolder.name : null
      }
    };
  } else {
    result = { success: false, error: "Project not found: " + args.id };
  }
} else if (args.type === "tag") {
  var tag = Tag.byIdentifier(args.id);
  if (tag) {
    var activeTasks = [];
    tag.flattenedTasks.forEach(function(t) {
      if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
      if (t.effectivelyCompleted || t.effectivelyDropped || t.completed) return;
      activeTasks.push(t);
    });
    result = {
      success: true,
      tag: {
        id: tag.id.primaryKey,
        name: tag.name,
        activeTaskCount: activeTasks.length,
        tasks: activeTasks.slice(0, 50).map(function(t) {
          return {
            id: t.id.primaryKey,
            name: t.name,
            project: t.containingProject ? t.containingProject.name : null,
            dueDate: t.dueDate ? t.dueDate.toISOString() : null,
            flagged: t.flagged
          };
        })
      }
    };
  } else {
    result = { success: false, error: "Tag not found: " + args.id };
  }
} else {
  var t = Task.byIdentifier(args.id);
  if (t) {
    result = {
      success: true,
      task: {
        id: t.id.primaryKey,
        name: t.name,
        completed: t.completed,
        flagged: t.flagged,
        dueDate: t.dueDate ? t.dueDate.toISOString() : null,
        deferDate: t.deferDate ? t.deferDate.toISOString() : null,
        completionDate: t.completionDate ? t.completionDate.toISOString() : null,
        note: t.note,
        project: t.containingProject ? t.containingProject.name : null,
        tags: t.tags.map(function(tag) { return tag.name; }),
        estimatedMinutes: t.estimatedMinutes
      }
    };
  } else {
    result = { success: false, error: "Task not found: " + args.id };
  }
}

Pasteboard.general.string = JSON.stringify(result);
