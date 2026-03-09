var args = argument;
var location = inbox.ending;

if (args.project) {
  var proj = flattenedProjects.byName(args.project);
  if (proj) {
    location = proj.task.ending;
  }
}

var t = new Task(args.name, location);

if (args.note) t.note = args.note;
if (args.flagged) t.flagged = true;

if (args.due) {
  t.dueDate = new Date(args.due);
}

if (args.defer) {
  t.deferDate = new Date(args.defer);
}

if (args.estimate) {
  t.estimatedMinutes = args.estimate;
}

if (args.tags) {
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
    project: t.containingProject ? t.containingProject.name : "Inbox"
  }
});
