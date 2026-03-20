// ofo-dispatcher.js — Single Omni Automation dispatcher for all ofo commands.
// Routes on argument.action field. One script = one OmniFocus approval.
var args = argument;
var action = args.action;
var result;

try {
  switch (action) {
    case 'ofo-info':
      result = ofoInfo(args);
      break;
    case 'ofo-complete':
      result = ofoComplete(args);
      break;
    case 'ofo-create':
      result = ofoCreate(args);
      break;
    case 'ofo-update':
      result = ofoUpdate(args);
      break;
    case 'ofo-search':
      result = ofoSearch(args);
      break;
    case 'ofo-list':
      result = ofoList(args);
      break;
    case 'ofo-perspective':
      result = ofoPerspective(args);
      break;
    default:
      result = { success: false, error: 'Unknown action: ' + action };
  }
} catch (e) {
  result = { success: false, error: e.toString() };
}

Pasteboard.general.string = JSON.stringify(result);

// === INFO ===
function ofoInfo(args) {
  if (args.type === 'project') {
    var p = Project.byIdentifier(args.id);
    if (!p) return { success: false, error: 'Project not found: ' + args.id };
    return {
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
  } else if (args.type === 'tag') {
    var tag = Tag.byIdentifier(args.id);
    if (!tag) return { success: false, error: 'Tag not found: ' + args.id };
    var activeTasks = [];
    tag.remainingTasks.forEach(function(t) {
      if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
      if (t.effectivelyCompleted || t.effectivelyDropped || t.completed) return;
      activeTasks.push(t);
    });
    return {
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
    var t = Task.byIdentifier(args.id);
    if (!t) return { success: false, error: 'Task not found: ' + args.id };
    return {
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
  }
}

// === COMPLETE ===
function ofoComplete(args) {
  var t = Task.byIdentifier(args.id);
  if (!t) return { success: false, error: 'Task not found: ' + args.id };
  t.markComplete();
  return { success: true, task: { id: t.id.primaryKey, name: t.name, completed: true } };
}

// === CREATE ===
function ofoCreate(args) {
  var location = inbox.ending;
  if (args.project) {
    var proj = flattenedProjects.byName(args.project);
    if (proj) location = proj.task.ending;
  }
  var t = new Task(args.name, location);
  if (args.note) t.note = args.note;
  if (args.flagged) t.flagged = true;
  if (args.due) t.dueDate = new Date(args.due);
  if (args.defer) t.deferDate = new Date(args.defer);
  if (args.estimate) t.estimatedMinutes = args.estimate;
  if (args.tags) {
    args.tags.forEach(function(tagName) {
      var tag = flattenedTags.byName(tagName);
      if (tag) t.addTag(tag);
    });
  }
  return {
    success: true,
    task: {
      id: t.id.primaryKey,
      name: t.name,
      project: t.containingProject ? t.containingProject.name : 'Inbox'
    }
  };
}

// === UPDATE ===
function ofoUpdate(args) {
  var t = Task.byIdentifier(args.id);
  if (!t) return { success: false, error: 'Task not found: ' + args.id };
  if (args.name !== undefined) t.name = args.name;
  if (args.note !== undefined) t.note = args.note;
  if (args.flagged !== undefined) t.flagged = args.flagged;
  if (args.due !== undefined) t.dueDate = args.due === null ? null : new Date(args.due);
  if (args.defer !== undefined) t.deferDate = args.defer === null ? null : new Date(args.defer);
  if (args.estimate !== undefined) t.estimatedMinutes = args.estimate;
  if (args.tags !== undefined) {
    t.clearTags();
    args.tags.forEach(function(tagName) {
      var tag = flattenedTags.byName(tagName);
      if (tag) t.addTag(tag);
    });
  }
  return {
    success: true,
    task: {
      id: t.id.primaryKey,
      name: t.name,
      flagged: t.flagged,
      dueDate: t.dueDate ? t.dueDate.toISOString() : null,
      deferDate: t.deferDate ? t.deferDate.toISOString() : null
    }
  };
}

// === SEARCH ===
function ofoSearch(args) {
  var query = (args.query || '').toLowerCase();
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
  return { success: true, count: results.length, tasks: results };
}

// === LIST ===
function ofoList(args) {
  var filter = args.filter || 'inbox';
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

  if (filter === 'inbox') {
    inbox.forEach(function(t) {
      if (results.length >= limit) return;
      if (t.taskStatus !== Task.Status.Available) return;
      results.push(taskSummary(t));
    });
  } else if (filter === 'flagged') {
    flattenedTasks.forEach(function(t) {
      if (results.length >= limit) return;
      if (t.flagged && t.taskStatus === Task.Status.Available) {
        results.push(taskSummary(t));
      }
    });
  } else if (filter === 'today') {
    flattenedTasks.forEach(function(t) {
      if (results.length >= limit) return;
      if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
      if (t.effectivelyCompleted || t.effectivelyDropped || t.completed) return;
      var isDueToday = t.dueDate && t.dueDate >= todayStart && t.dueDate < todayEnd;
      var isFlagged = t.flagged;
      if (isDueToday || isFlagged) {
        results.push(taskSummary(t));
      }
    });
  } else if (filter === 'overdue') {
    flattenedTasks.forEach(function(t) {
      if (results.length >= limit) return;
      if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
      if (t.effectivelyCompleted || t.effectivelyDropped || t.completed) return;
      if (t.dueDate && t.dueDate < todayStart) {
        results.push(taskSummary(t));
      }
    });
  }

  return { success: true, filter: filter, count: results.length, tasks: results };
}

// === PERSPECTIVE ===
function ofoPerspective(args) {
  var name = args.name || null;
  var id = args.id || null;
  var limit = args.limit || 100;

  var target = null;
  if (id) target = Perspective.Custom.byIdentifier(id);
  else if (name) target = Perspective.Custom.byName(name);

  if (!target) return { success: false, error: 'Perspective not found: ' + (name || id) };

  var rules = target.archivedFilterRules;
  var aggregation = target.archivedTopLevelFilterAggregation;
  var isStalled = rules.some(function(r) {
    return r.actionHasProjectWithStatus === 'stalled';
  });

  var results = [];
  if (isStalled) {
    flattenedProjects.forEach(function(p) {
      if (results.length >= limit) return;
      if (p.status !== Project.Status.Active) return;
      var remaining = p.flattenedTasks.filter(function(t) {
        return t.taskStatus === Task.Status.Available || t.taskStatus === Task.Status.Blocked;
      });
      var available = p.flattenedTasks.filter(function(t) {
        return t.taskStatus === Task.Status.Available;
      });
      if (remaining.length > 0 && available.length === 0) {
        results.push({
          id: p.id.primaryKey, name: p.name, type: 'project',
          remainingTasks: remaining.length, availableTasks: 0,
          modifiedDate: p.modified ? p.modified.toISOString() : null
        });
      }
    });
  } else {
    flattenedTasks.forEach(function(t) {
      if (results.length >= limit) return;
      if (t.taskStatus !== Task.Status.Available) return;
      results.push({
        id: t.id.primaryKey, name: t.name, type: 'task',
        project: t.containingProject ? t.containingProject.name : null,
        dueDate: t.dueDate ? t.dueDate.toISOString() : null,
        flagged: t.flagged,
        tags: t.tags.map(function(tag) { return tag.name; })
      });
    });
  }

  return {
    success: true,
    perspective: target.name,
    perspectiveId: target.id.primaryKey,
    filterRules: rules,
    aggregation: aggregation,
    count: results.length,
    items: results
  };
}
