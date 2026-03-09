var args = argument;
var t = Task.byIdentifier(args.id);

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
