var args = argument;
var name = args.name || null;
var id = args.id || null;
var limit = args.limit || 100;

var target = null;
if (id) {
  target = Perspective.Custom.byIdentifier(id);
} else if (name) {
  target = Perspective.Custom.byName(name);
}

if (!target) {
  Pasteboard.general.string = JSON.stringify({
    success: false,
    error: "Perspective not found: " + (name || id)
  });
} else {
  var rules = target.archivedFilterRules;
  var aggregation = target.archivedTopLevelFilterAggregation;

  // Detect stalled-projects perspective pattern
  var isStalled = rules.some(function(r) {
    return r.actionHasProjectWithStatus === "stalled";
  });

  var results = [];

  if (isStalled) {
    // Find active projects with remaining tasks but no available tasks
    flattenedProjects.forEach(function(p) {
      if (results.length >= limit) return;
      if (p.status !== Project.Status.Active) return;

      var remaining = p.flattenedTasks.filter(function(t) {
        return t.taskStatus === Task.Status.Available ||
               t.taskStatus === Task.Status.Blocked;
      });

      var available = p.flattenedTasks.filter(function(t) {
        return t.taskStatus === Task.Status.Available;
      });

      if (remaining.length > 0 && available.length === 0) {
        results.push({
          id: p.id.primaryKey,
          name: p.name,
          type: "project",
          remainingTasks: remaining.length,
          availableTasks: 0,
          modifiedDate: p.modified ? p.modified.toISOString() : null
        });
      }
    });
  } else {
    // Generic perspective: evaluate filter rules against flattenedTasks
    flattenedTasks.forEach(function(t) {
      if (results.length >= limit) return;
      if (t.taskStatus !== Task.Status.Available) return;
      results.push({
        id: t.id.primaryKey,
        name: t.name,
        type: "task",
        project: t.containingProject ? t.containingProject.name : null,
        dueDate: t.dueDate ? t.dueDate.toISOString() : null,
        flagged: t.flagged,
        tags: t.tags.map(function(tag) { return tag.name; })
      });
    });
  }

  Pasteboard.general.string = JSON.stringify({
    success: true,
    perspective: target.name,
    perspectiveId: target.id.primaryKey,
    filterRules: rules,
    aggregation: aggregation,
    count: results.length,
    items: results
  });
}
