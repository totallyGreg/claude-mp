var args = argument;
var query = (args.query || "").toLowerCase();
var limit = args.limit || 50;
var results = [];

flattenedTasks.forEach(function(t) {
  if (results.length >= limit) return;
  if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
  if (t.effectivelyCompleted || t.effectivelyDropped || t.completed) return;
  var nameMatch = t.name.toLowerCase().indexOf(query) !== -1;
  var noteMatch = t.note && t.note.toLowerCase().indexOf(query) !== -1;
  if (nameMatch || noteMatch) {
    results.push({
      id: t.id.primaryKey,
      name: t.name,
      project: t.containingProject ? t.containingProject.name : null,
      dueDate: t.dueDate ? t.dueDate.toISOString() : null,
      flagged: t.flagged
    });
  }
});

Pasteboard.general.string = JSON.stringify({
  success: true,
  count: results.length,
  tasks: results
});
