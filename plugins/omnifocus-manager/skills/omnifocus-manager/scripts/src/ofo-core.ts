/// <reference path="../../typescript/omnifocus.d.ts" />

// ofo-core.ts — OmniFocus plugin library core logic.
// Compiled by tsc, then wrapped in PlugIn.Library IIFE by build script.
// All functions are plain — no imports/exports. The build script assigns
// all named functions (getTask, completeTask, createTask, ...) and
// `dispatch` to `lib.*` in the IIFE wrapper, making them accessible to
// other plugins via: PlugIn.find("com.totally-tools.ofo-core").library("ofoCore").getTask(args)
//
// OfoAction, OfoArgs, OfoResult are declared as ambient types in
// ofo-core-ambient.d.ts (included via tsconfig.plugin.json).

// === INFO ===

function getTask(args: OfoArgs): OfoResult {
  const id = args.id as string;
  const type = (args.type as string) || 'task';

  if (type === 'project') {
    const p = Project.byIdentifier(id);
    if (!p) return { success: false, error: 'Project not found: ' + id };
    let projPlannedDate: string | null = null;
    try { projPlannedDate = p.plannedDate ? p.plannedDate.toISOString() : null; } catch (_) {}
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
        plannedDate: projPlannedDate,
        estimatedMinutes: p.estimatedMinutes,
        note: p.note,
        tags: p.tags.map(function(tag: Tag) { return tag.name; }),
        taskCount: p.flattenedTasks.length,
        sequential: p.sequential,
        parentFolder: p.parentFolder ? p.parentFolder.name : null,
        reviewInterval: p.reviewInterval ? {
          steps: p.reviewInterval.steps,
          unit: String(p.reviewInterval.unit)
        } : null,
        nextReviewDate: p.nextReviewDate ? p.nextReviewDate.toISOString() : null,
        lastReviewDate: p.lastReviewDate ? p.lastReviewDate.toISOString() : null
      }
    };
  } else if (type === 'tag') {
    const tag = Tag.byIdentifier(id);
    if (!tag) return { success: false, error: 'Tag not found: ' + id };
    const activeTasks: Task[] = [];
    tag.remainingTasks.forEach(function(t: Task) {
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
        tasks: activeTasks.slice(0, 50).map(function(t: Task) {
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
    const t = Task.byIdentifier(id);
    if (!t) return { success: false, error: 'Task not found: ' + id };
    let taskPlannedDate: string | null = null;
    try { taskPlannedDate = t.plannedDate ? t.plannedDate.toISOString() : null; } catch (_) {}
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
        plannedDate: taskPlannedDate,
        note: t.note,
        project: t.containingProject ? t.containingProject.name : null,
        tags: t.tags.map(function(tag: Tag) { return tag.name; }),
        estimatedMinutes: t.estimatedMinutes,
        repetitionRule: t.repetitionRule ? {
          ruleString: t.repetitionRule.ruleString,
          method: String(t.repetitionRule.method)
        } : null
      }
    };
  }
}

// === COMPLETE ===

function completeTask(args: OfoArgs): OfoResult {
  const id = args.id as string;
  const t = Task.byIdentifier(id);
  if (!t) return { success: false, error: 'Task not found: ' + id };
  t.markComplete();
  return { success: true, task: { id: t.id.primaryKey, name: t.name, completed: true } };
}

// === CREATE ===

function createTask(args: OfoArgs): OfoResult {
  let location = inbox.ending;
  if (args.project) {
    const proj = flattenedProjects.byName(args.project as string);
    if (proj) location = proj.task.ending;
  }
  const t = new Task(args.name as string, location);
  if (args.note) t.note = args.note as string;
  if (args.flagged) t.flagged = true;
  if (args.due) t.dueDate = new Date(args.due as string);
  if (args.defer) t.deferDate = new Date(args.defer as string);
  if (args.estimate) t.estimatedMinutes = args.estimate as number;
  if (args.plannedDate !== undefined) {
    try { t.plannedDate = args.plannedDate === null ? null : new Date(args.plannedDate as string); } catch (_) {}
  }
  if (args.tags) {
    (args.tags as string[]).forEach(function(tagName: string) {
      const tag = flattenedTags.byName(tagName);
      if (tag) t.addTag(tag);
    });
  }
  let createPlannedDate: string | null = null;
  try { createPlannedDate = t.plannedDate ? t.plannedDate.toISOString() : null; } catch (_) {}
  return {
    success: true,
    task: {
      id: t.id.primaryKey,
      name: t.name,
      project: t.containingProject ? t.containingProject.name : 'Inbox',
      plannedDate: createPlannedDate
    }
  };
}

// === UPDATE ===

function updateTask(args: OfoArgs): OfoResult {
  const id = args.id as string;
  const t = Task.byIdentifier(id);
  if (!t) return { success: false, error: 'Task not found: ' + id };
  if (args.name !== undefined) t.name = args.name as string;
  if (args.note !== undefined) t.note = args.note as string;
  if (args.noteAppend !== undefined) {
    const existing = t.note || '';
    const sep = existing.length > 0 ? '\n' : '';
    t.note = existing + sep + (args.noteAppend as string);
  }
  if (args.flagged !== undefined) t.flagged = args.flagged as boolean;
  if (args.due !== undefined) t.dueDate = args.due === null ? null : new Date(args.due as string);
  if (args.defer !== undefined) t.deferDate = args.defer === null ? null : new Date(args.defer as string);
  if (args.estimate !== undefined) t.estimatedMinutes = args.estimate as number;
  if (args.plannedDate !== undefined) {
    try { t.plannedDate = args.plannedDate === null ? null : new Date(args.plannedDate as string); } catch (_) {}
  }
  if (args.tags !== undefined) {
    t.clearTags();
    (args.tags as string[]).forEach(function(tagName: string) {
      const tag = flattenedTags.byName(tagName);
      if (tag) t.addTag(tag);
    });
  }
  let updatePlannedDate: string | null = null;
  try { updatePlannedDate = t.plannedDate ? t.plannedDate.toISOString() : null; } catch (_) {}
  return {
    success: true,
    task: {
      id: t.id.primaryKey,
      name: t.name,
      flagged: t.flagged,
      dueDate: t.dueDate ? t.dueDate.toISOString() : null,
      deferDate: t.deferDate ? t.deferDate.toISOString() : null,
      plannedDate: updatePlannedDate
    }
  };
}

// === SEARCH ===

function searchTasks(args: OfoArgs): OfoResult {
  const query = ((args.query as string) || '').toLowerCase();
  const limit = (args.limit as number) || 50;
  const results: object[] = [];
  flattenedTasks.forEach(function(t: Task) {
    if (results.length >= limit) return;
    if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
    if (t.effectivelyCompleted || t.effectivelyDropped || t.completed) return;
    const nameMatch = t.name.toLowerCase().indexOf(query) !== -1;
    const noteMatch = t.note && t.note.toLowerCase().indexOf(query) !== -1;
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

function listTasks(args: OfoArgs): OfoResult {
  const filter = (args.filter as string) || 'inbox';
  const limit = (args.limit as number) || 100;
  const results: object[] = [];
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const todayEnd = new Date(todayStart.getTime() + 86400000);

  function taskSummary(t: Task) {
    return {
      id: t.id.primaryKey,
      name: t.name,
      project: t.containingProject ? t.containingProject.name : null,
      dueDate: t.dueDate ? t.dueDate.toISOString() : null,
      deferDate: t.deferDate ? t.deferDate.toISOString() : null,
      flagged: t.flagged,
      estimatedMinutes: t.estimatedMinutes,
      tags: t.tags.map(function(tag: Tag) { return tag.name; })
    };
  }

  if (filter === 'inbox') {
    inbox.forEach(function(t: Task) {
      if (results.length >= limit) return;
      if (t.taskStatus !== Task.Status.Available) return;
      results.push(taskSummary(t));
    });
  } else if (filter === 'flagged') {
    flattenedTasks.forEach(function(t: Task) {
      if (results.length >= limit) return;
      if (t.flagged && t.taskStatus === Task.Status.Available) {
        results.push(taskSummary(t));
      }
    });
  } else if (filter === 'today') {
    flattenedTasks.forEach(function(t: Task) {
      if (results.length >= limit) return;
      if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
      if (t.effectivelyCompleted || t.effectivelyDropped || t.completed) return;
      const isDueToday = t.dueDate && t.dueDate >= todayStart && t.dueDate < todayEnd;
      const isFlagged = t.flagged;
      let isPlannedToday = false;
      try { isPlannedToday = !!(t.plannedDate && t.plannedDate >= todayStart && t.plannedDate < todayEnd); } catch (_) {}
      if (isDueToday || isFlagged || isPlannedToday) {
        results.push(taskSummary(t));
      }
    });
  } else if (filter === 'overdue') {
    flattenedTasks.forEach(function(t: Task) {
      if (results.length >= limit) return;
      if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
      if (t.effectivelyCompleted || t.effectivelyDropped || t.completed) return;
      if (t.dueDate && t.dueDate < todayStart) {
        results.push(taskSummary(t));
      }
    });
  } else if (filter === 'due-soon') {
    const days = (args.days as number) || 7;
    const cutoff = new Date(todayStart.getTime() + days * 86400000);
    flattenedTasks.forEach(function(t: Task) {
      if (results.length >= limit) return;
      if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
      if (t.effectivelyCompleted || t.effectivelyDropped || t.completed) return;
      if (t.dueDate && t.dueDate >= todayStart && t.dueDate < cutoff) {
        results.push(taskSummary(t));
      }
    });
  }

  return { success: true, filter: filter, count: results.length, tasks: results };
}

// === PERSPECTIVE ===

function getPerspective(args: OfoArgs): OfoResult {
  const name = (args.name as string) || null;
  const id = (args.id as string) || null;
  const limit = (args.limit as number) || 100;

  let target: Perspective.Custom | null = null;
  if (id) target = Perspective.Custom.byIdentifier(id);
  else if (name) target = Perspective.Custom.byName(name);

  if (!target) return { success: false, error: 'Perspective not found: ' + (name || id) };

  const rules = target.archivedFilterRules;
  const aggregation = target.archivedTopLevelFilterAggregation;
  const isStalled = rules.some(function(r: any) {
    return r.actionHasProjectWithStatus === 'stalled';
  });
  const isCompletedToday = rules.some(function(r: any) {
    return r.actionAvailability === 'completed';
  }) && rules.some(function(r: any) {
    return r.actionDateField === 'completed' && r.actionDateIsToday === true;
  });

  const results: object[] = [];
  if (isStalled) {
    flattenedProjects.forEach(function(p: Project) {
      if (results.length >= limit) return;
      if (p.status !== Project.Status.Active) return;
      const remaining = p.flattenedTasks.filter(function(t: Task) {
        return t.taskStatus === Task.Status.Available || t.taskStatus === Task.Status.Blocked;
      });
      const available = p.flattenedTasks.filter(function(t: Task) {
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
  } else if (isCompletedToday) {
    const todayStart = new Date();
    todayStart.setHours(0, 0, 0, 0);
    const todayEnd = new Date(todayStart);
    todayEnd.setDate(todayEnd.getDate() + 1);
    flattenedTasks.forEach(function(t: Task) {
      if (results.length >= limit) return;
      if (t.taskStatus !== Task.Status.Completed) return;
      if (!t.completionDate || t.completionDate < todayStart || t.completionDate >= todayEnd) return;
      results.push({
        id: t.id.primaryKey, name: t.name, type: 'task',
        project: t.containingProject ? t.containingProject.name : null,
        dueDate: t.dueDate ? t.dueDate.toISOString() : null,
        flagged: t.flagged,
        tags: t.tags.map(function(tag: Tag) { return tag.name; })
      });
    });
  } else {
    flattenedTasks.forEach(function(t: Task) {
      if (results.length >= limit) return;
      if (t.taskStatus !== Task.Status.Available) return;
      results.push({
        id: t.id.primaryKey, name: t.name, type: 'task',
        project: t.containingProject ? t.containingProject.name : null,
        dueDate: t.dueDate ? t.dueDate.toISOString() : null,
        flagged: t.flagged,
        tags: t.tags.map(function(tag: Tag) { return tag.name; })
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

// === PERSPECTIVE CONFIGURE ===

function configurePerspective(args: OfoArgs): OfoResult {
  const name = (args.name as string) || null;
  const id = (args.id as string) || null;

  let target: Perspective.Custom | null = null;
  if (id) target = Perspective.Custom.byIdentifier(id);
  else if (name) target = Perspective.Custom.byName(name);

  if (!target) return { success: false, error: 'Perspective not found: ' + (name || id) };

  const rules = args.rules as object[] | undefined;
  const aggregation = args.aggregation as string | undefined;

  if (!rules && !aggregation) {
    return { success: false, error: 'At least one of rules or aggregation is required' };
  }

  if (rules) target.archivedFilterRules = rules;
  if (aggregation) target.archivedTopLevelFilterAggregation = aggregation;

  return {
    success: true,
    perspective: target.name,
    perspectiveId: target.id.primaryKey,
    filterRules: target.archivedFilterRules,
    aggregation: target.archivedTopLevelFilterAggregation
  };
}

// === TAG ===

function tagTask(args: OfoArgs): OfoResult {
  const id = args.id as string;
  const t = Task.byIdentifier(id);
  if (!t) return { success: false, error: 'Task not found: ' + id };

  const warnings: string[] = [];
  const addNames = (args.add as string[]) || [];
  const removeNames = (args.remove as string[]) || [];

  // Check for add+remove conflict
  for (let i = 0; i < addNames.length; i++) {
    if (removeNames.indexOf(addNames[i]!) !== -1) {
      return { success: false, error: 'Cannot add and remove the same tag: ' + addNames[i] };
    }
  }

  // Remove first (idempotent)
  removeNames.forEach(function(tagName: string) {
    const tag = flattenedTags.byName(tagName);
    if (tag) t.removeTag(tag);
  });

  // Then add
  addNames.forEach(function(tagName: string) {
    const tag = flattenedTags.byName(tagName);
    if (tag) {
      t.addTag(tag);
    } else {
      warnings.push("Tag '" + tagName + "' not found, skipped");
    }
  });

  const result: OfoResult = {
    success: true,
    task: {
      id: t.id.primaryKey,
      name: t.name,
      tags: t.tags.map(function(tag: Tag) { return tag.name; })
    }
  };
  if (warnings.length > 0) result.warnings = warnings;
  return result;
}

// === TAGS ===

function getTags(_args: OfoArgs): OfoResult {
  function buildTree(tagList: Tag[]): object[] {
    const result: object[] = [];
    tagList.forEach(function(t: Tag) {
      if (t.status === Tag.Status.Dropped) return;
      result.push({
        id: t.id.primaryKey,
        name: t.name,
        status: t.status === Tag.Status.Active ? 'active' : 'on-hold',
        children: t.children.length > 0 ? buildTree(t.children) : [],
        activeTaskCount: t.remainingTasks.length
      });
    });
    return result;
  }
  return { success: true, tags: buildTree(tags) };
}

// === CREATE BATCH ===

function createBatch(args: OfoArgs): OfoResult {
  const items = args.items as OfoArgs[];
  const results: OfoResult[] = [];
  items.forEach(function(item: OfoArgs) {
    try {
      results.push(createTask(item));
    } catch (e) {
      results.push({ success: false, error: String(e) });
    }
  });
  const created = results.filter(function(r: OfoResult) { return r.success; }).length;
  return { success: true, results: results, created: created, failed: items.length - created };
}

// === PERSPECTIVE RULES ===

function resolveIds(obj: any): any {
  if (Array.isArray(obj)) return obj.map(resolveIds);
  if (obj && typeof obj === 'object') {
    const out: any = {};
    for (const k of Object.keys(obj)) {
      if (k === 'actionWithinFocus') {
        out[k] = (obj[k] as string[]).map(function(id: string) {
          const f = Folder.byIdentifier(id);
          if (f) return '[' + f.name + '](omnifocus:///folder/' + id + ')';
          const p = Project.byIdentifier(id);
          if (p) return '[' + p.name + '](omnifocus:///task/' + id + ')';
          return id;
        });
      } else if (k === 'actionHasAnyOfTags' || k === 'actionHasAllOfTags') {
        out[k] = (obj[k] as string[]).map(function(id: string) {
          const t = Tag.byIdentifier(id);
          return t ? '[' + t.name + '](omnifocus:///tag/' + id + ')' : id;
        });
      } else {
        out[k] = resolveIds(obj[k]);
      }
    }
    return out;
  }
  return obj;
}

function getPerspectiveRules(args: OfoArgs): OfoResult {
  const name = (args.name as string) || null;

  const perspectives: Perspective.Custom[] = name
    ? (function() { const p = Perspective.Custom.byName(name); return p ? [p] : []; })()
    : Perspective.Custom.all;

  if (name && perspectives.length === 0) {
    return { success: false, error: 'Perspective not found: ' + name };
  }

  const result: Record<string, any> = {};
  perspectives.forEach(function(p: Perspective.Custom) {
    result[p.name] = resolveIds((p as any).archivedFilterRules);
  });

  return { success: true, rules: result };
}

// === DUMP ===

function dumpDatabase(_args: OfoArgs): OfoResult {
  const MAX_ITEMS = 500;

  const activeTasks: object[] = [];
  flattenedTasks.forEach(function(t: Task) {
    if (activeTasks.length >= MAX_ITEMS) return;
    if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
    if (t.effectivelyCompleted || t.effectivelyDropped) return;
    activeTasks.push({
      id: t.id.primaryKey,
      name: t.name,
      project: t.containingProject ? t.containingProject.name : null,
      flagged: t.flagged,
      dueDate: t.dueDate ? t.dueDate.toISOString() : null,
      deferDate: t.deferDate ? t.deferDate.toISOString() : null,
      tags: t.tags.map(function(tag: Tag) { return tag.name; }),
      estimatedMinutes: t.estimatedMinutes
    });
  });

  const activeProjects: object[] = [];
  flattenedProjects.forEach(function(p: Project) {
    if (p.status !== Project.Status.Active) return;
    activeProjects.push({
      id: p.id.primaryKey,
      name: p.name,
      folder: p.parentFolder ? p.parentFolder.name : null,
      flagged: p.flagged,
      dueDate: p.dueDate ? p.dueDate.toISOString() : null,
      taskCount: p.flattenedTasks.length
    });
  });

  const perspectiveNames: string[] = Perspective.Custom.all.map(function(p: Perspective.Custom) {
    return p.name;
  });

  const warnings: string[] = [];
  if (activeTasks.length >= MAX_ITEMS) warnings.push('Task list truncated at ' + MAX_ITEMS + ' items');

  const result: OfoResult = {
    success: true,
    taskCount: activeTasks.length,
    projectCount: activeProjects.length,
    tasks: activeTasks,
    projects: activeProjects,
    perspectives: perspectiveNames
  };
  if (warnings.length > 0) result.warnings = warnings;
  return result;
}

// === STATS ===

function getStats(_args: OfoArgs): OfoResult {
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  const todayEnd = new Date(todayStart.getTime() + 86400000);
  let inbox_count = 0;
  let flagged = 0;
  let overdue = 0;
  let totalActive = 0;
  let withEstimate = 0;
  let plannedToday = 0;

  inbox.forEach(function(t: Task) {
    if (t.taskStatus === Task.Status.Available) inbox_count++;
  });

  flattenedTasks.forEach(function(t: Task) {
    if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
    if (t.effectivelyCompleted || t.effectivelyDropped) return;
    totalActive++;
    if (t.flagged && t.taskStatus === Task.Status.Available) flagged++;
    if (t.dueDate && t.dueDate < todayStart) overdue++;
    if (t.estimatedMinutes != null && t.estimatedMinutes > 0) withEstimate++;
    try {
      if (t.plannedDate && t.plannedDate >= todayStart && t.plannedDate < todayEnd) plannedToday++;
    } catch (_) {}
  });

  let projectCount = 0;
  let reviewOverdue = 0;
  flattenedProjects.forEach(function(p: Project) {
    if (p.status !== Project.Status.Active) return;
    projectCount++;
    if (p.nextReviewDate && p.nextReviewDate < todayStart) reviewOverdue++;
  });

  return {
    success: true,
    inbox: inbox_count,
    flagged: flagged,
    overdue: overdue,
    activeProjects: projectCount,
    activeTasks: totalActive,
    reviewOverdue: reviewOverdue,
    plannedToday: plannedToday,
    withEstimate: withEstimate
  };
}

// === DISPATCH ===

function dispatch(args: OfoArgs): OfoResult {
  switch (args.action) {
    case 'ofo-info':        return getTask(args);
    case 'ofo-complete':    return completeTask(args);
    case 'ofo-create':      return createTask(args);
    case 'ofo-update':      return updateTask(args);
    case 'ofo-search':      return searchTasks(args);
    case 'ofo-list':        return listTasks(args);
    case 'ofo-perspective': return getPerspective(args);
    case 'ofo-perspective-configure': return configurePerspective(args);
    case 'ofo-perspective-rules':     return getPerspectiveRules(args);
    case 'ofo-tag':         return tagTask(args);
    case 'ofo-tags':        return getTags(args);
    case 'ofo-create-batch': return createBatch(args);
    case 'ofo-dump':        return dumpDatabase(args);
    case 'ofo-stats':       return getStats(args);
    default: {
      // Exhaustiveness check: TypeScript will error here if a new OfoAction
      // is added to the union in ofo-types.ts / ofo-core-ambient.d.ts but
      // not handled in this switch.
      const _exhaustive: never = args.action;
      return { success: false, error: 'Unknown action: ' + (_exhaustive as string) };
    }
  }
}
