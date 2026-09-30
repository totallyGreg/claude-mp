/// <reference path="../../typescript/omnifocus.d.ts" />

// ofo-core.ts — OmniFocus plugin library core logic.
// Compiled by tsc, then wrapped in PlugIn.Library IIFE by build script.
// All functions are plain — no imports/exports. The build script assigns
// all named functions (getTask, completeTask, createTask, ...) and
// `dispatch` to `lib.*` in the IIFE wrapper, making them accessible to
// the Attache plugin via: PlugIn.find("com.totallytools.omnifocus.attache").library("ofoCore").getTask(args)
//
// OfoAction, OfoArgs, OfoResult are declared as ambient types in
// ofo-core-ambient.d.ts (included via tsconfig.plugin.json).

// === SHARED HELPERS ===

/**
 * normalizeTask — single canonical task shape used by getTask, searchTasks, and listTasks.
 * Eliminates field-set drift across the three query functions.
 * OfoTask is declared in ofo-contract.d.ts (ambient, no import needed here).
 */
function normalizeTask(t: Task): OfoTask {
  let plannedDate: Date | null = null;
  try { plannedDate = t.plannedDate || null; } catch (_) {}
  let catchUp: boolean | null = null;
  let schedType: string | null = null;
  if (t.repetitionRule) {
    try { catchUp = t.repetitionRule.catchUpAutomatically; } catch (_) {}
    try {
      var st = String(t.repetitionRule.scheduleType);
      var m = st.match(/:\s*(\w+)\]$/);
      // noUncheckedIndexedAccess: m[1] is `string | undefined` even after a successful match.
      // In practice this regex always populates group 1 when it matches, but type system can't prove it.
      schedType = m ? (m[1] ?? st) : st;
    } catch (_) {}
  }
  return {
    id: t.id.primaryKey,
    name: t.name,
    project: t.containingProject ? t.containingProject.name : null,
    tags: t.tags.map(function(tag: Tag) { return tag.name; }),
    flagged: t.flagged,
    completed: t.completed,
    dueDate: t.dueDate || null,
    deferDate: t.deferDate || null,
    plannedDate: plannedDate,
    completionDate: t.completionDate || null,
    estimatedMinutes: t.estimatedMinutes || null,
    note: t.note || null,
    added: t.added || null,
    modified: t.modified || null,
    repetitionRule: t.repetitionRule ? t.repetitionRule.ruleString : null,
    repetitionCatchUp: catchUp,
    repetitionScheduleType: schedType,
    taskStatus: String(t.taskStatus),
  };
}

/**
 * computeStats — single-pass stats over all tasks, mirroring taskMetrics.collectAllMetrics().
 * Canonical inbox count: inbox.filter(Available) — matches what OmniFocus shows.
 */
function computeStats(allTasks: Task[]): OfoStats {
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const todayEnd = new Date(todayStart.getTime() + 86400000);

  let inboxCount = 0;
  inbox.forEach(function(t: Task) {
    if (t.taskStatus === Task.Status.Available) inboxCount++;
  });

  let overdue = 0, flagged = 0, dueToday = 0, totalActive = 0, withEstimate = 0, plannedToday = 0;
  allTasks.forEach(function(t: Task) {
    if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
    if (t.effectivelyCompleted || t.effectivelyDropped) return;
    totalActive++;
    if (t.flagged && t.taskStatus === Task.Status.Available) flagged++;
    if (t.dueDate && t.dueDate < todayStart) overdue++;
    if (t.dueDate && t.dueDate >= todayStart && t.dueDate < todayEnd) dueToday++;
    if (t.estimatedMinutes != null && t.estimatedMinutes > 0) withEstimate++;
    try {
      if (t.plannedDate && t.plannedDate >= todayStart && t.plannedDate < todayEnd) plannedToday++;
    } catch (_) {}
  });

  let activeProjects = 0, reviewOverdue = 0;
  flattenedProjects.forEach(function(p: Project) {
    if (p.status !== Project.Status.Active) return;
    activeProjects++;
    if (p.nextReviewDate && p.nextReviewDate < todayStart) reviewOverdue++;
  });

  return {
    inbox: inboxCount,
    overdue,
    flagged,
    dueToday,
    activeProjects,
    activeTasks: totalActive,
    reviewOverdue,
    plannedToday,
    withEstimate,
  };
}

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
    return { success: true, task: normalizeTask(t) };
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

// === DROP ===

function dropTask(args: OfoArgs): OfoResult {
  const id = args.id as string;
  const allOccurrences = args.allOccurrences as boolean || false;
  const t = Task.byIdentifier(id);
  if (!t) return { success: false, error: 'Task not found: ' + id };
  if (allOccurrences && !t.repetitionRule) {
    return { success: false, error: 'Task is not repeating; use without --all to drop it.' };
  }
  t.drop(allOccurrences);
  return { success: true, task: { id: t.id.primaryKey, name: t.name, dropped: true } };
}

// === CREATE ===

function createTask(args: OfoArgs): OfoResult {
  let location = inbox.ending;
  // `parent` (task ID) wins over `project` when both are supplied — nesting
  // a task under an existing parent implies that parent's containing project.
  if (args.parent) {
    const parentTask = Task.byIdentifier(args.parent as string);
    if (!parentTask) return { success: false, error: 'Parent task not found: ' + args.parent };
    location = parentTask.ending;
  } else if (args.project) {
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
  if (args.sequential !== undefined) t.sequential = args.sequential as boolean;
  if (args.due !== undefined) t.dueDate = args.due === null ? null : new Date(args.due as string);
  if (args.defer !== undefined) t.deferDate = args.defer === null ? null : new Date(args.defer as string);
  if (args.estimate !== undefined) t.estimatedMinutes = args.estimate as number;
  if (args.plannedDate !== undefined) {
    try { t.plannedDate = args.plannedDate === null ? null : new Date(args.plannedDate as string); } catch (_) {}
  }
  if (args.project !== undefined) {
    const projName = args.project as string;
    if (projName === 'inbox' || projName === '') {
      moveTasks([t], inbox.ending);
    } else {
      const proj = flattenedProjects.byName(projName);
      if (!proj) return { success: false, error: 'Project not found: ' + projName };
      moveTasks([t], proj.task.ending);
    }
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
      project: t.containingProject ? t.containingProject.name : 'Inbox',
      flagged: t.flagged,
      sequential: t.sequential,
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
      results.push(normalizeTask(t));
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

  const taskSummary = normalizeTask;

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

/** Normalize an aggregation value (string 'all'|'any'|'none' or numeric 0|1|2) → string. */
function normAggregation(val: any): 'all' | 'any' | 'none' {
  if (val === 'any' || val === 1) return 'any';
  if (val === 'none' || val === 2) return 'none';
  return 'all';
}

function startOfToday(): Date {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d;
}

/** Does a task's tag set include the given tag id-or-name? */
function taskHasTagRef(t: Task, ref: string): boolean {
  return t.tags.some(function(tag: Tag) {
    return tag.id.primaryKey === ref || tag.name === ref;
  });
}

/**
 * Evaluate one filter rule against a task.
 * Returns true/false when the rule is understood, or null when the rule key is
 * not supported (so the caller can log it and exclude it from the combination —
 * never silently drop fidelity).
 */
function evalTaskRule(t: Task, rule: any, unsupported: string[]): boolean | null {
  // Nested aggregation group: { rules: [...], aggregation|aggregateType }
  if (rule && Array.isArray(rule.rules)) {
    const agg = normAggregation(rule.aggregation !== undefined ? rule.aggregation : rule.aggregateType);
    return evalTaskRules(t, rule.rules, agg, unsupported);
  }
  if (!rule || typeof rule !== 'object') return null;

  const now = new Date();
  const todayStart = startOfToday();
  const done = t.completed || t.effectivelyCompleted || t.taskStatus === Task.Status.Completed;
  const dropped = t.effectivelyDropped || t.taskStatus === Task.Status.Dropped;
  let matched = false;

  for (const key of Object.keys(rule)) {
    const v = rule[key];
    switch (key) {
      case 'aggregation': case 'aggregateType': continue; // handled at group level
      case 'actionAvailability': {
        if (v === 'available') matched = t.taskStatus === Task.Status.Available;
        else if (v === 'firstAvailable') matched = t.taskStatus === Task.Status.Available;
        else if (v === 'remaining') matched = !done && !dropped;
        else if (v === 'completed') matched = done;
        else if (v === 'dropped') matched = dropped;
        else return unsupported.push(key + '=' + v), null;
        break;
      }
      case 'actionStatus': {
        if (v === 'flagged') matched = t.flagged;
        else if (v === 'due') matched = !!t.dueDate;
        else return unsupported.push(key + '=' + v), null;
        break;
      }
      case 'actionFlagged': matched = t.flagged === (v !== false); break;
      case 'actionOverdue': matched = !done && !dropped && !!t.dueDate && t.dueDate < todayStart; break;
      case 'actionHasDueDate': matched = (!!t.dueDate) === (v !== false); break;
      case 'actionHasDeferDate': matched = (!!t.deferDate) === (v !== false); break;
      case 'actionDueSoon': {
        const days = Number(v) || 0;
        const cutoff = new Date(todayStart.getTime() + days * 86400000);
        matched = !done && !dropped && !!t.dueDate && t.dueDate >= todayStart && t.dueDate < cutoff;
        break;
      }
      case 'actionCompletedWithinDays': {
        const days = Number(v) || 0;
        const since = new Date(now.getTime() - days * 86400000);
        matched = !!t.completionDate && t.completionDate >= since;
        break;
      }
      case 'actionHasAnyOfTags': matched = (v as string[]).some(function(r) { return taskHasTagRef(t, r); }); break;
      case 'actionHasAllOfTags': matched = (v as string[]).every(function(r) { return taskHasTagRef(t, r); }); break;
      case 'actionHasNoneOfTags': matched = !(v as string[]).some(function(r) { return taskHasTagRef(t, r); }); break;
      case 'actionHasNoTags': matched = (t.tags.length === 0) === (v !== false); break;
      case 'actionHasAnyTags': matched = (t.tags.length > 0) === (v !== false); break;
      case 'actionHasText': case 'actionMatchText': {
        const needle = String(v).toLowerCase();
        const hay = (t.name + ' ' + (t.note || '')).toLowerCase();
        matched = hay.indexOf(needle) !== -1;
        break;
      }
      case 'actionDateField': {
        // Paired with actionDateIsToday / relative flags on the same rule object.
        const field = v === 'defer' ? t.deferDate : v === 'completed' ? t.completionDate : t.dueDate;
        if (rule.actionDateIsToday === true) {
          const end = new Date(todayStart.getTime() + 86400000);
          matched = !!field && field >= todayStart && field < end;
        } else {
          return unsupported.push('actionDateField:' + JSON.stringify(rule)), null;
        }
        break;
      }
      case 'actionDateIsToday': continue; // consumed by actionDateField
      case 'projectStatus': case 'actionHasProjectWithStatus': {
        const proj = t.containingProject;
        const s = String(v).toLowerCase().replace(/[-_ ]/g, '');
        if (s === 'stalled') {
          matched = !!proj && proj.status === Project.Status.Active &&
            proj.flattenedTasks.every(function(x: Task) { return x.taskStatus !== Task.Status.Available; });
        } else if (s === 'active') matched = !!proj && proj.status === Project.Status.Active;
        else if (s === 'onhold') matched = !!proj && proj.status === Project.Status.OnHold;
        else if (s === 'dropped') matched = !!proj && proj.status === Project.Status.Dropped;
        else if (s === 'completed' || s === 'done') matched = !!proj && proj.status === Project.Status.Done;
        else return unsupported.push(key + '=' + v), null;
        break;
      }
      case 'actionWithinFocus': {
        const ids = v as string[];
        const proj = t.containingProject;
        matched = !!proj && ids.some(function(fid) {
          if (proj!.id.primaryKey === fid) return true;
          let f = proj!.parentFolder;
          while (f) { if (f.id.primaryKey === fid) return true; f = f.parent; }
          return false;
        });
        break;
      }
      default:
        return unsupported.push(key), null;
    }
    if (!matched) return false; // multiple keys on one rule = AND
  }
  return matched;
}

/** Combine a rule list against a task per aggregation (all/any/none). Unsupported rules are skipped + logged. */
function evalTaskRules(t: Task, rules: any[], aggregation: string, unsupported: string[]): boolean {
  const results: boolean[] = [];
  for (const rule of rules) {
    const r = evalTaskRule(t, rule, unsupported);
    if (r !== null) results.push(r);
  }
  if (results.length === 0) return true; // nothing evaluable → don't exclude
  if (aggregation === 'any') return results.some(function(x) { return x; });
  if (aggregation === 'none') return !results.some(function(x) { return x; });
  return results.every(function(x) { return x; }); // 'all'
}

function getPerspective(args: OfoArgs): OfoResult {
  const name = (args.name as string) || null;
  const id = (args.id as string) || null;
  // limit 0 (or unset) = uncapped; the old silent 100 cap is gone.
  const limit = (args.limit as number) || 0;

  let target: Perspective.Custom | null = null;
  if (id) target = Perspective.Custom.byIdentifier(id);
  else if (name) target = Perspective.Custom.byName(name);

  if (!target) return { success: false, error: 'Perspective not found: ' + (name || id) };

  const rules = target.archivedFilterRules || [];
  const aggregation = normAggregation(target.archivedTopLevelFilterAggregation);

  // Project-output fast path: a stalled-projects perspective returns projects, not tasks.
  const isStalledProjects = rules.some(function(r: any) {
    return r.actionHasProjectWithStatus === 'stalled' || r.projectHasNoAvailableActions === true;
  }) && !rules.some(function(r: any) {
    return r.actionHasAnyOfTags || r.actionHasAllOfTags || r.actionAvailability === 'completed';
  });

  const unsupported: string[] = [];
  const results: object[] = [];
  let truncated = false;

  if (isStalledProjects) {
    flattenedProjects.forEach(function(p: Project) {
      if (limit > 0 && results.length >= limit) { truncated = true; return; }
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
  } else {
    flattenedTasks.forEach(function(t: Task) {
      if (limit > 0 && results.length >= limit) { truncated = true; return; }
      if (!evalTaskRules(t, rules, aggregation, unsupported)) return;
      results.push({
        id: t.id.primaryKey, name: t.name, type: 'task',
        project: t.containingProject ? t.containingProject.name : null,
        dueDate: t.dueDate ? t.dueDate.toISOString() : null,
        flagged: t.flagged,
        tags: t.tags.map(function(tag: Tag) { return tag.name; })
      });
    });
  }

  // Deduplicate unsupported rule keys (logged, never silently dropped).
  const unsupportedUnique = unsupported.filter(function(v, i) { return unsupported.indexOf(v) === i; });

  const out: OfoResult = {
    success: true,
    perspective: target.name,
    perspectiveId: target.id.primaryKey,
    filterRules: rules,
    aggregation: aggregation,
    count: results.length,
    truncated: truncated,
    items: results
  };
  if (unsupportedUnique.length > 0) out.unsupportedRules = unsupportedUnique;
  return out;
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

// === TAGGED (first-class tag query) ===

/**
 * getTaggedTasks — all tasks carrying a tag, grouped by containing project with
 * per-project completed/total progress. Uncapped by default (pass limit to cap).
 * The generic tag-listing primitive that `list someday-maybe --tag` used to stand in for.
 */
function getTaggedTasks(args: OfoArgs): OfoResult {
  const tagName = (args['tag'] as string) || (args['name'] as string) || null;
  const activeOnly = args['activeOnly'] === true;
  const limit = (args['limit'] as number) || 0; // 0 = uncapped

  if (!tagName) return { success: false, error: 'Missing required arg: tag' };
  const tag = flattenedTags.byName(tagName);
  if (!tag) return { success: false, error: 'Tag not found: ' + tagName };

  // remainingTasks = incomplete; tasks = every task carrying the tag.
  const source: Task[] = activeOnly ? tag.remainingTasks : tag.tasks;
  const groups: Record<string, any> = {};
  let totalTasks = 0;
  let completedTasks = 0;

  source.forEach(function(t: Task) {
    if (limit > 0 && totalTasks >= limit) return;
    if (t.effectivelyDropped || t.taskStatus === Task.Status.Dropped) return;
    const projName = t.containingProject ? t.containingProject.name
      : (t.inInbox ? '(inbox)' : '(no project)');
    if (!groups[projName]) groups[projName] = { project: projName, total: 0, completed: 0, tasks: [] };
    const done = t.completed || t.effectivelyCompleted || t.taskStatus === Task.Status.Completed;
    groups[projName].total++;
    if (done) { groups[projName].completed++; completedTasks++; }
    totalTasks++;
    groups[projName].tasks.push(normalizeTask(t));
  });

  const groupList = Object.keys(groups).map(function(k) { return groups[k]; });
  return {
    success: true,
    tag: tag.name,
    tagId: tag.id.primaryKey,
    activeOnly: activeOnly,
    projectCount: groupList.length,
    taskCount: totalTasks,
    completed: completedTasks,
    total: totalTasks,
    truncated: limit > 0 && totalTasks >= limit,
    groups: groupList
  };
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

// === CLARITY + STALLED (GTD intelligence — Phase 5) ===

function clarityScore(t: Task): number {
  let score = 100;
  if (!t.estimatedMinutes) score -= 30;
  if (t.tags.length === 0) score -= 20;
  if (t.name.length < 10) score -= 20;
  if (!t.containingProject) score -= 30;
  return Math.max(0, score);
}

function assessClarity(args: OfoArgs): OfoResult {
  const limit = parseInt((args['limit'] as string) || '10');
  const tasks = flattenedTasks as Task[];
  const results = tasks
    .filter(function(t) { return !t.completed && t.taskStatus === Task.Status.Available; })
    .map(function(t) {
      return { id: t.id.primaryKey, name: t.name, score: clarityScore(t) };
    })
    .sort(function(a, b) { return a.score - b.score; })
    .slice(0, limit);
  return { success: true, tasks: results };
}

function stalledProjects(args: OfoArgs): OfoResult {
  const daysSince = parseInt((args['days'] as string) || '14');
  const cutoff = new Date(Date.now() - daysSince * 86400000);
  const projects = flattenedProjects as Project[];
  const stalled = projects
    .filter(function(p) { return p.status === Project.Status.Active; })
    .filter(function(p) {
      const hasNextAction = p.flattenedTasks.some(function(t) {
        return t.taskStatus === Task.Status.Available;
      });
      return !hasNextAction || (p.modified !== null && p.modified < cutoff);
    })
    .map(function(p) {
      return { id: p.id.primaryKey, name: p.name, taskCount: p.flattenedTasks.length };
    });
  return { success: true, projects: stalled };
}

// === HEALTH ===

function getHealth(args: OfoArgs): OfoResult {
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  // Inbox: available tasks in inbox
  const inboxTasks: object[] = [];
  inbox.forEach(function(t: Task) {
    if (t.taskStatus === Task.Status.Available) inboxTasks.push(normalizeTask(t));
  });

  // Overdue: past due date, not completed/dropped
  const overdueTasks: object[] = [];
  // Flagged: available + flagged, not completed/dropped
  const flaggedTasks: object[] = [];

  flattenedTasks.forEach(function(t: Task) {
    if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
    if (t.effectivelyCompleted || t.effectivelyDropped || t.completed) return;
    if (t.dueDate && t.dueDate < todayStart) {
      overdueTasks.push(normalizeTask(t));
    }
    if (t.flagged && t.taskStatus === Task.Status.Available) {
      flaggedTasks.push(normalizeTask(t));
    }
  });

  return {
    success: true,
    inbox: { count: inboxTasks.length, tasks: inboxTasks },
    overdue: { count: overdueTasks.length, tasks: overdueTasks },
    flagged: { count: flaggedTasks.length, tasks: flaggedTasks },
  };
}

// === D6.2 — GTD-ESSENTIAL QUERIES (System Map convention-dependent) ===

/**
 * listWaitingFor — tasks with the waitingTag, optionally filtered by age.
 * @requires SystemMap.conventions.waitingTag (caller passes via args.tag)
 */
function listWaitingFor(args: OfoArgs): OfoResult {
  const tagName = args['tag'] as string;
  if (!tagName) return { success: false, error: 'Missing required arg: tag (resolve from SystemMap.conventions.waitingTag)' };
  const limit = (args['limit'] as number) || 100;
  const ageThresholdDays = (args['ageThresholdDays'] as number) || 0;

  const tag = flattenedTags.byName(tagName);
  if (!tag) return { success: false, error: 'Waiting tag not found: ' + tagName };

  const cutoff = ageThresholdDays > 0 ? new Date(Date.now() - ageThresholdDays * 86400000) : null;
  const results: object[] = [];
  tag.remainingTasks.forEach(function(t: Task) {
    if (results.length >= limit) return;
    if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
    if (t.effectivelyCompleted || t.effectivelyDropped || t.completed) return;
    if (cutoff && t.modified && t.modified >= cutoff) return;
    results.push(normalizeTask(t));
  });
  return { success: true, tag: tagName, ageThresholdDays: ageThresholdDays, count: results.length, tasks: results };
}

/**
 * listSomedayMaybe — tasks in the somedayTag, or all tasks under projects in the somedayFolder.
 * @requires SystemMap.conventions.somedayTag AND/OR SystemMap.conventions.somedayFolder
 */
function listSomedayMaybe(args: OfoArgs): OfoResult {
  const tagName = args['tag'] as string | undefined;
  const folderName = args['folder'] as string | undefined;
  if (!tagName && !folderName) {
    return { success: false, error: 'Missing required arg: at least one of tag or folder (resolve from SystemMap.conventions.{somedayTag, somedayFolder})' };
  }
  const limit = (args['limit'] as number) || 100;
  const results: object[] = [];
  const seenIds: Record<string, boolean> = {};

  if (tagName) {
    const tag = flattenedTags.byName(tagName);
    if (tag) {
      tag.remainingTasks.forEach(function(t: Task) {
        if (results.length >= limit) return;
        if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
        if (t.effectivelyCompleted || t.effectivelyDropped) return;
        const idKey = t.id.primaryKey;
        if (seenIds[idKey]) return;
        seenIds[idKey] = true;
        results.push(normalizeTask(t));
      });
    }
  }

  if (folderName) {
    const folder = flattenedFolders.byName(folderName);
    if (folder) {
      folder.flattenedProjects.forEach(function(p: Project) {
        if (results.length >= limit) return;
        if (p.status !== Project.Status.Active && p.status !== Project.Status.OnHold) return;
        p.flattenedTasks.forEach(function(t: Task) {
          if (results.length >= limit) return;
          if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
          if (t.effectivelyCompleted || t.effectivelyDropped) return;
          const idKey = t.id.primaryKey;
          if (seenIds[idKey]) return;
          seenIds[idKey] = true;
          results.push(normalizeTask(t));
        });
      });
    }
  }

  return { success: true, count: results.length, tasks: results };
}

/**
 * listNeglectedProjects — active projects not modified in N days (default 30).
 * No System Map dependency (date-based only).
 */
function listNeglectedProjects(args: OfoArgs): OfoResult {
  const daysSinceModified = (args['daysSinceModified'] as number) || 30;
  const cutoff = new Date(Date.now() - daysSinceModified * 86400000);
  const limit = (args['limit'] as number) || 50;
  const results: object[] = [];
  flattenedProjects.forEach(function(p: Project) {
    if (results.length >= limit) return;
    if (p.status !== Project.Status.Active) return;
    if (p.modified && p.modified >= cutoff) return;
    const ageDays = p.modified ? Math.floor((Date.now() - p.modified.getTime()) / 86400000) : null;
    results.push({
      id: p.id.primaryKey,
      name: p.name,
      folder: p.parentFolder ? p.parentFolder.name : null,
      modified: p.modified ? p.modified.toISOString() : null,
      daysSinceModified: ageDays,
      taskCount: p.flattenedTasks.length
    });
  });
  return { success: true, daysSinceModified: daysSinceModified, count: results.length, projects: results };
}

/**
 * listRecentlyCompleted — tasks completed since the given date.
 * Optionally groups results by tag for "What did I accomplish?" reports.
 */
function listRecentlyCompleted(args: OfoArgs): OfoResult {
  const sinceDateStr = args['sinceDate'] as string | undefined;
  const groupByTag = args['groupByTag'] as boolean | undefined;
  const limit = (args['limit'] as number) || 200;
  const since = sinceDateStr ? new Date(sinceDateStr) : new Date(Date.now() - 7 * 86400000);

  const results: any[] = [];
  flattenedTasks.forEach(function(t: Task) {
    if (results.length >= limit) return;
    if (t.taskStatus !== Task.Status.Completed) return;
    if (!t.completionDate || t.completionDate < since) return;
    results.push({
      id: t.id.primaryKey,
      name: t.name,
      project: t.containingProject ? t.containingProject.name : null,
      completionDate: t.completionDate.toISOString(),
      tags: t.tags.map(function(tag: Tag) { return tag.name; })
    });
  });

  if (groupByTag) {
    const grouped: Record<string, any[]> = {};
    results.forEach(function(r: any) {
      if (!r.tags || r.tags.length === 0) {
        if (!grouped['(untagged)']) grouped['(untagged)'] = [];
        grouped['(untagged)'].push(r);
        return;
      }
      r.tags.forEach(function(tagName: string) {
        if (!grouped[tagName]) grouped[tagName] = [];
        grouped[tagName].push(r);
      });
    });
    return { success: true, since: since.toISOString(), count: results.length, grouped: grouped };
  }
  return { success: true, since: since.toISOString(), count: results.length, tasks: results };
}

/**
 * listProjectsForReview — active or on-hold projects whose nextReviewDate ≤ beforeDate (default now).
 */
function listProjectsForReview(args: OfoArgs): OfoResult {
  const beforeDateStr = args['beforeDate'] as string | undefined;
  const before = beforeDateStr ? new Date(beforeDateStr) : new Date();
  const limit = (args['limit'] as number) || 100;

  const results: object[] = [];
  flattenedProjects.forEach(function(p: Project) {
    if (results.length >= limit) return;
    if (p.status !== Project.Status.Active && p.status !== Project.Status.OnHold) return;
    if (!p.nextReviewDate || p.nextReviewDate > before) return;
    results.push({
      id: p.id.primaryKey,
      name: p.name,
      folder: p.parentFolder ? p.parentFolder.name : null,
      nextReviewDate: p.nextReviewDate.toISOString(),
      lastReviewDate: p.lastReviewDate ? p.lastReviewDate.toISOString() : null,
      status: String(p.status)
    });
  });
  return { success: true, beforeDate: before.toISOString(), count: results.length, projects: results };
}

// === D6.2 — PROJECT LIFECYCLE ===

/**
 * markProjectReviewed — set lastReviewDate (default: now). OmniFocus advances nextReviewDate
 * automatically based on reviewInterval.
 */
function markProjectReviewed(args: OfoArgs): OfoResult {
  const id = args['id'] as string;
  if (!id) return { success: false, error: 'Missing required arg: id' };
  const reviewDateStr = args['reviewDate'] as string | undefined;
  const p = Project.byIdentifier(id);
  if (!p) return { success: false, error: 'Project not found: ' + id };
  const reviewDate = reviewDateStr ? new Date(reviewDateStr) : new Date();
  p.lastReviewDate = reviewDate;
  return {
    success: true,
    project: {
      id: p.id.primaryKey,
      name: p.name,
      lastReviewDate: p.lastReviewDate ? p.lastReviewDate.toISOString() : null,
      nextReviewDate: p.nextReviewDate ? p.nextReviewDate.toISOString() : null
    }
  };
}

/**
 * listFolders — folder hierarchy as a tree. Optionally includes projects under each folder.
 */
function listFolders(args: OfoArgs): OfoResult {
  const includeProjects = args['includeProjects'] as boolean | undefined;

  function buildTree(folderList: FolderArray | Folder[]): object[] {
    const result: object[] = [];
    folderList.forEach(function(f: Folder) {
      if (f.status === Folder.Status.Dropped) return;
      const node: any = {
        id: f.id.primaryKey,
        name: f.name,
        children: f.folders.length > 0 ? buildTree(f.folders) : []
      };
      if (includeProjects) {
        node.projects = f.projects.map(function(p: Project) {
          return {
            id: p.id.primaryKey,
            name: p.name,
            status: String(p.status),
            taskCount: p.flattenedTasks.length
          };
        });
      }
      result.push(node);
    });
    return result;
  }
  return { success: true, folders: buildTree(folders) };
}

/**
 * createProject — create a project at root or inside a named folder.
 * Status mapping (Project.Status):
 *   'active'    → Project.Status.Active   (default for new projects)
 *   'onHold'    → Project.Status.OnHold
 *   'completed' → Project.Status.Done     (OmniFocus uses "Done" not "Completed")
 *   'dropped'   → Project.Status.Dropped
 */
function createProject(args: OfoArgs): OfoResult {
  const name = args['name'] as string;
  if (!name) return { success: false, error: 'Missing required arg: name' };

  let location: Folder.ChildInsertionLocation | null = null;
  if (args['folder']) {
    let folder = flattenedFolders.byName(args['folder'] as string);
    if (!folder && args['createMissing'] === true) {
      folder = new Folder(args['folder'] as string, null);
    }
    if (!folder) return { success: false, error: 'Folder not found: ' + args['folder'] };
    location = folder.ending;
  }

  const p = new Project(name, location);
  if (args['note']) p.note = args['note'] as string;
  if (args['sequential'] !== undefined) p.sequential = args['sequential'] as boolean;
  if (args['flagged']) p.flagged = true;
  if (args['due']) p.dueDate = new Date(args['due'] as string);
  if (args['defer']) p.deferDate = new Date(args['defer'] as string);
  // reviewInterval: { steps: number, unit: 'days'|'weeks'|'months'|... } per Project.ReviewInterval
  if (args['reviewInterval']) {
    try {
      p.reviewInterval = args['reviewInterval'] as any;
    } catch (_) {}
  }

  return {
    success: true,
    project: {
      id: p.id.primaryKey,
      name: p.name,
      folder: p.parentFolder ? p.parentFolder.name : null,
      sequential: p.sequential,
      status: String(p.status)
    }
  };
}

/**
 * updateProject — mutate any combination of name / note / status / folder / sequential / due / defer.
 * Status mapping documented in createProject above.
 */
function updateProject(args: OfoArgs): OfoResult {
  const id = args['id'] as string;
  if (!id) return { success: false, error: 'Missing required arg: id' };
  const p = Project.byIdentifier(id);
  if (!p) return { success: false, error: 'Project not found: ' + id };

  if (args['name'] !== undefined) p.name = args['name'] as string;
  if (args['note'] !== undefined) p.note = args['note'] as string;
  if (args['flagged'] !== undefined) p.flagged = args['flagged'] as boolean;
  if (args['sequential'] !== undefined) p.sequential = args['sequential'] as boolean;
  if (args['due'] !== undefined) p.dueDate = args['due'] === null ? null : new Date(args['due'] as string);
  if (args['defer'] !== undefined) p.deferDate = args['defer'] === null ? null : new Date(args['defer'] as string);

  if (args['status'] !== undefined) {
    const statusStr = String(args['status']).toLowerCase().replace(/[-_]/g, '');
    if (statusStr === 'active') p.status = Project.Status.Active;
    else if (statusStr === 'onhold') p.status = Project.Status.OnHold;
    else if (statusStr === 'completed' || statusStr === 'done') p.status = Project.Status.Done;
    else if (statusStr === 'dropped') p.status = Project.Status.Dropped;
    else return { success: false, error: 'Invalid status: ' + args['status'] + ' (expected active|onHold|completed|dropped)' };
  }

  // Move to root when --root is passed, or when --folder is set to empty string.
  const moveToRoot = args['root'] === true || args['folder'] === '';
  if (moveToRoot) {
    moveSections([p], library.ending);
  } else if (args['folder'] !== undefined && args['folder'] !== null) {
    const folderName = args['folder'] as string;
    let folder = flattenedFolders.byName(folderName);
    if (!folder && args['createMissing'] === true) {
      folder = new Folder(folderName, null);
    }
    if (!folder) return { success: false, error: 'Folder not found: ' + folderName };
    moveSections([p], folder.ending);
  }

  return {
    success: true,
    project: {
      id: p.id.primaryKey,
      name: p.name,
      folder: p.parentFolder ? p.parentFolder.name : null,
      status: String(p.status),
      sequential: p.sequential
    }
  };
}

// === FOLDER MUTATION ===

/** Resolve a folder by primaryKey id first, then by name. */
function resolveFolder(idOrName: string): Folder | null {
  const byId = Folder.byIdentifier(idOrName);
  if (byId) return byId;
  return flattenedFolders.byName(idOrName);
}

function folderSummary(f: Folder): object {
  return {
    id: f.id.primaryKey,
    name: f.name,
    parent: f.parent ? f.parent.name : null
  };
}

/** createFolder — create a folder at root or inside a named/id'd parent folder. */
function createFolder(args: OfoArgs): OfoResult {
  const name = args['name'] as string;
  if (!name) return { success: false, error: 'Missing required arg: name' };

  let position: Folder.ChildInsertionLocation | null = null;
  const parentRef = (args['parent'] as string) || null;
  if (parentRef) {
    const parent = resolveFolder(parentRef);
    if (!parent) return { success: false, error: 'Parent folder not found: ' + parentRef };
    position = parent.ending;
  }

  const f = new Folder(name, position);
  return { success: true, folder: folderSummary(f) };
}

/** renameFolder — rename a folder resolved by id or name. */
function renameFolder(args: OfoArgs): OfoResult {
  const ref = (args['id'] as string) || (args['folder'] as string);
  const newName = args['name'] as string;
  if (!ref) return { success: false, error: 'Missing required arg: id (or folder name to resolve)' };
  if (!newName) return { success: false, error: 'Missing required arg: name (the new name)' };

  const f = resolveFolder(ref);
  if (!f) return { success: false, error: 'Folder not found: ' + ref };
  f.name = newName;
  return { success: true, folder: folderSummary(f) };
}

/** moveFolder — reparent a folder under another folder, or to root (--root). */
function moveFolder(args: OfoArgs): OfoResult {
  const ref = (args['id'] as string) || (args['folder'] as string);
  if (!ref) return { success: false, error: 'Missing required arg: id (or folder name to resolve)' };

  const f = resolveFolder(ref);
  if (!f) return { success: false, error: 'Folder not found: ' + ref };

  const moveToRoot = args['root'] === true || args['parent'] === '';
  if (moveToRoot) {
    moveSections([f], library.ending);
  } else {
    const parentRef = args['parent'] as string;
    if (!parentRef) return { success: false, error: 'Provide --parent <name|id> or --root' };
    const parent = resolveFolder(parentRef);
    if (!parent) return { success: false, error: 'Parent folder not found: ' + parentRef };
    if (parent.id.primaryKey === f.id.primaryKey) {
      return { success: false, error: 'Cannot move a folder into itself' };
    }
    moveSections([f], parent.ending);
  }
  return { success: true, folder: folderSummary(f) };
}

// === DISPATCH ===

function dispatch(args: OfoArgs): OfoResult {
  switch (args.action) {
    case 'ofo-info':        return getTask(args);
    case 'ofo-complete':    return completeTask(args);
    case 'ofo-drop':        return dropTask(args);
    case 'ofo-create':      return createTask(args);
    case 'ofo-update':      return updateTask(args);
    case 'ofo-search':      return searchTasks(args);
    case 'ofo-list':        return listTasks(args);
    case 'ofo-perspective': return getPerspective(args);
    case 'ofo-perspective-configure': return configurePerspective(args);
    case 'ofo-perspective-rules':     return getPerspectiveRules(args);
    case 'ofo-tag':         return tagTask(args);
    case 'ofo-tags':        return getTags(args);
    case 'ofo-tagged':      return getTaggedTasks(args);
    case 'ofo-create-batch': return createBatch(args);
    case 'ofo-dump':        return dumpDatabase(args);
    case 'ofo-stats':       return getStats(args);
    case 'ofo-clarity':     return assessClarity(args);
    case 'ofo-stalled':     return stalledProjects(args);
    case 'ofo-health':      return getHealth(args);
    // D6.2 — GTD-essential queries
    case 'ofo-list-waiting-for':         return listWaitingFor(args);
    case 'ofo-list-someday-maybe':       return listSomedayMaybe(args);
    case 'ofo-list-neglected-projects':  return listNeglectedProjects(args);
    case 'ofo-list-recently-completed':  return listRecentlyCompleted(args);
    case 'ofo-list-projects-for-review': return listProjectsForReview(args);
    // D6.2 — project lifecycle
    case 'ofo-mark-project-reviewed':    return markProjectReviewed(args);
    case 'ofo-list-folders':             return listFolders(args);
    case 'ofo-create-project':           return createProject(args);
    case 'ofo-update-project':           return updateProject(args);
    // Folder mutation
    case 'ofo-create-folder':            return createFolder(args);
    case 'ofo-rename-folder':            return renameFolder(args);
    case 'ofo-move-folder':              return moveFolder(args);
    default: {
      // Exhaustiveness check: TypeScript will error here if a new OfoAction
      // is added to the union in ofo-types.ts / ofo-core-ambient.d.ts but
      // not handled in this switch.
      const _exhaustive: never = args.action;
      return { success: false, error: 'Unknown action: ' + (_exhaustive as string) };
    }
  }
}
