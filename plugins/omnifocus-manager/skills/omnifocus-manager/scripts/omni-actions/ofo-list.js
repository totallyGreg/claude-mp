var args = argument;
var filter = args.filter || "inbox";
var limit = args.limit || 100;
var results = [];
var now = new Date();
var todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
var todayEnd = new Date(todayStart.getTime() + 86400000);

function taskSummary(t) {
  return {
    id: t.id.primaryKey,
    name: t.name,
    project: t.containingProject ? t.containingProject.name : null,
    dueDate: t.dueDate ? t.dueDate.toISOString() : null,
    deferDate: t.deferDate ? t.deferDate.toISOString() : null,
    flagged: t.flagged,
    tags: t.tags.map(function(tag) { return tag.name; })
  };
}

if (filter === "inbox") {
  inbox.forEach(function(t) {
    if (results.length >= limit) return;
    results.push(taskSummary(t));
  });
} else if (filter === "flagged") {
  flattenedTasks.forEach(function(t) {
    if (results.length >= limit) return;
    if (t.flagged && !t.effectivelyCompleted && !t.effectivelyDropped) {
      results.push(taskSummary(t));
    }
  });
} else if (filter === "today") {
  flattenedTasks.forEach(function(t) {
    if (results.length >= limit) return;
    if (t.effectivelyCompleted || t.effectivelyDropped) return;
    var isDueToday = t.dueDate && t.dueDate >= todayStart && t.dueDate < todayEnd;
    var isDeferredToday = t.deferDate && t.deferDate <= now && !t.deferDate.valueOf() === 0;
    var isFlagged = t.flagged;
    if (isDueToday || isFlagged) {
      results.push(taskSummary(t));
    }
  });
} else if (filter === "overdue") {
  flattenedTasks.forEach(function(t) {
    if (results.length >= limit) return;
    if (t.effectivelyCompleted || t.effectivelyDropped) return;
    if (t.dueDate && t.dueDate < todayStart) {
      results.push(taskSummary(t));
    }
  });
}

Pasteboard.general.string = JSON.stringify({
  success: true,
  filter: filter,
  count: results.length,
  tasks: results
});
