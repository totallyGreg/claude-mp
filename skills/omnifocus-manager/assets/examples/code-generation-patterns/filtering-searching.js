/**
 * Filtering and Searching - Correct OmniFocus API Usage Patterns
 *
 * This file demonstrates validated patterns for filtering and searching
 * tasks, projects, and other OmniFocus objects.
 *
 * KEY PRINCIPLES:
 * - Use Array.filter() for filtering
 * - Use Array.find() for single results
 * - Use .byName() methods on collections
 * - Properties are accessed directly (no parentheses)
 */

// ============================================================================
// BASIC FILTERING PATTERNS
// ============================================================================

// Get all active tasks (not completed, not dropped)
const activeTasks = flattenedTasks.filter(t => !t.completed && !t.dropped);

// Get completed tasks
const completedTasks = flattenedTasks.filter(t => t.completed);

// Get dropped tasks
const droppedTasks = flattenedTasks.filter(t => t.dropped);

// Get flagged tasks
const flaggedTasks = flattenedTasks.filter(t => t.flagged);

// Get tasks with notes
const tasksWithNotes = flattenedTasks.filter(t => t.note && t.note.length > 0);

// Get tasks with estimates
const tasksWithEstimates = flattenedTasks.filter(t =>
    t.estimatedMinutes !== null && t.estimatedMinutes > 0
);

// ============================================================================
// DATE-BASED FILTERING
// ============================================================================

// Helper function: Get date at midnight
function getMidnight(date) {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);
    return d;
}

// Get today's date range
const today = getMidnight(new Date());
const tomorrow = new Date(today);
tomorrow.setDate(tomorrow.getDate() + 1);

// Get tasks due today
const todayTasks = flattenedTasks.filter(t => {
    if (t.completed || t.dropped) return false;
    if (!t.dueDate) return false;
    const due = getMidnight(t.dueDate);
    return due.getTime() === today.getTime();
});

// Get overdue tasks
const overdueTasks = flattenedTasks.filter(t => {
    if (t.completed || t.dropped) return false;
    if (!t.dueDate) return false;
    return t.dueDate < today;
});

// Get tasks due in next N days
function getTasksDueInDays(days) {
    const endDate = new Date(today);
    endDate.setDate(endDate.getDate() + days);

    return flattenedTasks.filter(t => {
        if (t.completed || t.dropped) return false;
        if (!t.dueDate) return false;
        return t.dueDate >= today && t.dueDate < endDate;
    });
}

const dueSoon = getTasksDueInDays(7);

// Get tasks deferred until today or earlier (available now)
const availableTasks = flattenedTasks.filter(t => {
    if (t.completed || t.dropped) return false;
    if (!t.deferDate) return true;  // No defer date = available
    return t.deferDate <= new Date();
});

// Get tasks completed in last N days
function getRecentlyCompletedTasks(days) {
    const startDate = new Date(today);
    startDate.setDate(startDate.getDate() - days);

    return flattenedTasks.filter(t => {
        if (!t.completed) return false;
        if (!t.completionDate) return false;
        return t.completionDate >= startDate;
    });
}

const recentlyCompleted = getRecentlyCompletedTasks(7);

// ============================================================================
// TAG-BASED FILTERING
// ============================================================================

// Find tasks with specific tag
const workTag = tags.byName("work");
const workTasks = workTag ? workTag.flattenedTasks.filter(t => !t.completed) : [];

// Find tasks with multiple tags (AND logic)
function getTasksWithAllTags(tagNames) {
    return flattenedTasks.filter(t => {
        if (t.completed || t.dropped) return false;
        return tagNames.every(tagName => {
            const tag = tags.byName(tagName);
            return tag && t.tags.includes(tag);
        });
    });
}

const urgentWorkTasks = getTasksWithAllTags(["urgent", "work"]);

// Find tasks with any of multiple tags (OR logic)
function getTasksWithAnyTag(tagNames) {
    return flattenedTasks.filter(t => {
        if (t.completed || t.dropped) return false;
        return tagNames.some(tagName => {
            const tag = tags.byName(tagName);
            return tag && t.tags.includes(tag);
        });
    });
}

const importantTasks = getTasksWithAnyTag(["urgent", "important", "high-priority"]);

// Get tasks without any tags
const untaggedTasks = flattenedTasks.filter(t => {
    if (t.completed || t.dropped) return false;
    return t.tags.length === 0;
});

// ============================================================================
// PROJECT-BASED FILTERING
// ============================================================================

// Find tasks in specific project
const project = projects.byName("My Project");
const projectTasks = project ? project.flattenedTasks.filter(t => !t.completed) : [];

// Find tasks NOT in any project (inbox tasks only)
const inboxOnly = flattenedTasks.filter(t => {
    if (t.completed || t.dropped) return false;
    return !t.containingProject;
});

// Find tasks in projects with specific status
const activeProjects = flattenedProjects.filter(p => p.status === Project.Status.Active);
const activeProjectTasks = flattenedTasks.filter(t => {
    if (t.completed || t.dropped) return false;
    const proj = t.containingProject;
    return proj && proj.status === Project.Status.Active;
});

// Find tasks in on-hold projects
const onHoldProjectTasks = flattenedTasks.filter(t => {
    const proj = t.containingProject;
    return proj && proj.status === Project.Status.OnHold;
});

// ============================================================================
// TEXT SEARCH PATTERNS
// ============================================================================

// Case-insensitive search in task name
function searchTasksByName(query) {
    const lowerQuery = query.toLowerCase();
    return flattenedTasks.filter(t => {
        if (t.completed || t.dropped) return false;
        return t.name.toLowerCase().includes(lowerQuery);
    });
}

const meetingTasks = searchTasksByName("meeting");

// Search in name OR note
function searchTasksInNameOrNote(query) {
    const lowerQuery = query.toLowerCase();
    return flattenedTasks.filter(t => {
        if (t.completed || t.dropped) return false;
        const inName = t.name.toLowerCase().includes(lowerQuery);
        const inNote = t.note && t.note.toLowerCase().includes(lowerQuery);
        return inName || inNote;
    });
}

const emailTasks = searchTasksInNameOrNote("email");

// Search with multiple keywords (AND logic)
function searchTasksWithAllKeywords(keywords) {
    const lowerKeywords = keywords.map(k => k.toLowerCase());
    return flattenedTasks.filter(t => {
        if (t.completed || t.dropped) return false;
        const searchText = `${t.name} ${t.note || ""}`.toLowerCase();
        return lowerKeywords.every(keyword => searchText.includes(keyword));
    });
}

const reportTasks = searchTasksWithAllKeywords(["report", "quarterly"]);

// ============================================================================
// COMPLEX FILTERING COMBINATIONS
// ============================================================================

// Flagged tasks due this week
const flaggedDueSoon = flattenedTasks.filter(t => {
    if (t.completed || t.dropped || !t.flagged) return false;
    if (!t.dueDate) return false;
    const weekFromNow = new Date(today);
    weekFromNow.setDate(weekFromNow.getDate() + 7);
    return t.dueDate >= today && t.dueDate < weekFromNow;
});

// Overdue tasks with specific tag
const overdueWorkTasks = flattenedTasks.filter(t => {
    if (t.completed || t.dropped) return false;
    if (!t.dueDate || t.dueDate >= today) return false;
    const workTag = tags.byName("work");
    return workTag && t.tags.includes(workTag);
});

// Available tasks (not deferred, not completed, not dropped)
const availableNow = flattenedTasks.filter(t => {
    if (t.completed || t.dropped) return false;
    if (t.deferDate && t.deferDate > new Date()) return false;
    return true;
});

// Stalled projects (no remaining tasks)
const stalledProjects = flattenedProjects.filter(p => {
    if (p.completed || p.status === Project.Status.Done) return false;
    const remainingTasks = p.flattenedTasks.filter(t => !t.completed && !t.dropped);
    return remainingTasks.length === 0;
});

// ============================================================================
// FINDING SINGLE ITEMS
// ============================================================================

// Find first matching task
const firstFlagged = flattenedTasks.find(t => t.flagged && !t.completed);

// Find project by name (case-sensitive)
const workProject = projects.byName("Work");

// Find tag by name (case-sensitive)
const urgentTag = tags.byName("urgent");

// Find folder by name
const workFolder = folders.byName("Work");

// ============================================================================
// SORTING PATTERNS
// ============================================================================

// Sort tasks by due date (earliest first)
const sortedByDue = activeTasks.filter(t => t.dueDate).sort((a, b) => {
    return a.dueDate.getTime() - b.dueDate.getTime();
});

// Sort tasks by name (alphabetical)
const sortedByName = activeTasks.sort((a, b) => {
    return a.name.localeCompare(b.name);
});

// Sort tasks by flagged status (flagged first)
const sortedByFlagged = activeTasks.sort((a, b) => {
    if (a.flagged === b.flagged) return 0;
    return a.flagged ? -1 : 1;
});

// Sort tasks by multiple criteria (flagged, then due date)
const sortedMultiple = activeTasks.sort((a, b) => {
    // Flagged first
    if (a.flagged !== b.flagged) {
        return a.flagged ? -1 : 1;
    }
    // Then by due date
    if (a.dueDate && b.dueDate) {
        return a.dueDate.getTime() - b.dueDate.getTime();
    }
    if (a.dueDate) return -1;
    if (b.dueDate) return 1;
    return 0;
});

// ============================================================================
// COUNTING AND AGGREGATION
// ============================================================================

// Count tasks by criteria
const taskCounts = {
    total: flattenedTasks.length,
    active: flattenedTasks.filter(t => !t.completed && !t.dropped).length,
    completed: flattenedTasks.filter(t => t.completed).length,
    dropped: flattenedTasks.filter(t => t.dropped).length,
    flagged: flattenedTasks.filter(t => t.flagged && !t.completed).length,
    overdue: overdueTasks.length,
    dueToday: todayTasks.length
};

// Sum estimated time
const totalEstimatedMinutes = activeTasks.reduce((sum, task) => {
    return sum + (task.estimatedMinutes || 0);
}, 0);

// Group tasks by project
const tasksByProject = {};
activeTasks.forEach(task => {
    const projectName = task.containingProject ? task.containingProject.name : "Inbox";
    if (!tasksByProject[projectName]) {
        tasksByProject[projectName] = [];
    }
    tasksByProject[projectName].push(task);
});

// ============================================================================
// PRACTICAL WORKFLOW EXAMPLES
// ============================================================================

// Get "next actions" - available, not deferred, no project or first in sequential project
function getNextActions() {
    return flattenedTasks.filter(t => {
        if (t.completed || t.dropped) return false;
        if (t.deferDate && t.deferDate > new Date()) return false;

        const project = t.containingProject;
        if (!project) return true;  // Inbox items are next actions

        // If in parallel project, all available tasks are next actions
        if (project.task.children.length > 0 && !project.sequential) {
            return true;
        }

        // If in sequential project, only first incomplete task is next action
        if (project.sequential) {
            const siblings = t.parent ? t.parent.children : project.task.children;
            const firstIncomplete = siblings.find(sibling => !sibling.completed && !sibling.dropped);
            return firstIncomplete === t;
        }

        return true;
    });
}

const nextActions = getNextActions();
