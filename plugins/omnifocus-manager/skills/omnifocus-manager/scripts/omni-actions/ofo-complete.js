var args = argument;
var t = flattenedTasks.find(function(task) {
  return task.id.primaryKey === args.id;
});

if (t) {
  t.markComplete();
  Pasteboard.general.string = JSON.stringify({
    success: true,
    task: { id: t.id.primaryKey, name: t.name, completed: true }
  });
} else {
  Pasteboard.general.string = JSON.stringify({
    success: false, error: "Task not found: " + args.id
  });
}
