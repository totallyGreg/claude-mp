var args = argument;
var t = Task.byIdentifier(args.id);

if (!t) {
  Pasteboard.general.string = JSON.stringify({
    success: false, error: "Task not found: " + args.id
  });
} else {
  if (args.name !== undefined) t.name = args.name;
  if (args.note !== undefined) t.note = args.note;
  if (args.flagged !== undefined) t.flagged = args.flagged;

  if (args.due !== undefined) {
    t.dueDate = args.due === null ? null : new Date(args.due);
  }

  if (args.defer !== undefined) {
    t.deferDate = args.defer === null ? null : new Date(args.defer);
  }

  if (args.estimate !== undefined) {
    t.estimatedMinutes = args.estimate;
  }

  if (args.tags !== undefined) {
    t.clearTags();
    args.tags.forEach(function(tagName) {
      var tag = flattenedTags.byName(tagName);
      if (tag) t.addTag(tag);
    });
  }

  Pasteboard.general.string = JSON.stringify({
    success: true,
    task: {
      id: t.id.primaryKey,
      name: t.name,
      flagged: t.flagged,
      dueDate: t.dueDate ? t.dueDate.toISOString() : null,
      deferDate: t.deferDate ? t.deferDate.toISOString() : null
    }
  });
}
