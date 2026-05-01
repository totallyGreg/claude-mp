/**
 * Task Operations - Correct OmniFocus API Usage Patterns
 *
 * This file demonstrates validated patterns for working with tasks
 * in OmniFocus Omni Automation plugins.
 *
 * KEY RULES:
 * - Properties: Access directly WITHOUT parentheses
 * - Methods: Call WITH parentheses
 * - Global variables: Use flattenedTasks, folders, etc. (NOT Document.defaultDocument)
 */

// ============================================================================
// READING TASK PROPERTIES (No Parentheses)
// ============================================================================

// ✅ CORRECT: Properties accessed directly
const taskName = task.name;
const taskNote = task.note;
const isCompleted = task.completed;
const isDue = task.dueDate;
const isDeferred = task.deferDate;
const isFlagged = task.flagged;
const isDropped = task.dropped;
const completedDate = task.completionDate;
const estimatedMinutes = task.estimatedMinutes;
const taskTags = task.tags;
const parentProject = task.containingProject;
const childTasks = task.children;

// ❌ WRONG: Don't call properties as functions
// const taskName = task.name();  // ERROR! name is a property
// const isCompleted = task.completed();  // ERROR!

// ============================================================================
// CALLING TASK METHODS (With Parentheses)
// ============================================================================

// ✅ CORRECT: Methods called with parentheses
task.markComplete();
task.markIncomplete();
task.drop(true);  // Drop task
task.drop(false); // Undrop task
task.addTag(myTag);
task.removeTag(myTag);
task.clearTags();
task.remove();  // Delete task

// ❌ WRONG: Don't access methods without calling
// const fn = task.markComplete;  // Gets function, doesn't execute

// ============================================================================
// ACCESSING DATABASE (Global Variables)
// ============================================================================

// ✅ CORRECT: Use global variables directly
const allTasks = flattenedTasks;
const allProjects = flattenedProjects;
const allFolders = flattenedFolders;
const allTags = flattenedTags;
const rootFolders = folders;
const rootProjects = projects;
const rootTags = tags;
const inboxTasks = inbox;
const libraryData = library;

// ❌ WRONG: Don't use Document.defaultDocument
// const doc = Document.defaultDocument;
// const tasks = doc.flattenedTasks;  // ERROR! flattenedTasks not on Document

// ============================================================================
// CREATING TASKS
// ============================================================================

// ✅ CORRECT: Create task in inbox
const newTask = new Task("Task name", inbox);
newTask.note = "Task details and notes";
newTask.dueDate = new Date("2025-12-31");
newTask.deferDate = new Date("2025-12-01");
newTask.flagged = true;
newTask.estimatedMinutes = 30;

// Add tags to task
const workTag = tags.byName("work");
if (workTag) {
    newTask.addTag(workTag);
}

// ✅ CORRECT: Create task in project
const project = projects.byName("My Project");
if (project) {
    const projectTask = new Task("Project task", project.task);
    projectTask.note = "This task belongs to a project";
}

// ============================================================================
// COMMON FILTERING PATTERNS
// ============================================================================

// Get active tasks (not completed, not dropped)
const activeTasks = flattenedTasks.filter(t => !t.completed && !t.dropped);

// Get flagged tasks
const flaggedTasks = flattenedTasks.filter(t => t.flagged && !t.completed);

// Get today's tasks
const today = new Date();
today.setHours(0, 0, 0, 0);
const tomorrow = new Date(today);
tomorrow.setDate(tomorrow.getDate() + 1);

const todayTasks = flattenedTasks.filter(t => {
    if (t.completed || t.dropped) return false;
    if (!t.dueDate) return false;
    const due = new Date(t.dueDate);
    due.setHours(0, 0, 0, 0);
    return due.getTime() === today.getTime();
});

// Get overdue tasks
const overdueTasks = flattenedTasks.filter(t => {
    if (t.completed || t.dropped) return false;
    if (!t.dueDate) return false;
    return t.dueDate < today;
});

// ============================================================================
// WORKING WITH TAGS
// ============================================================================

// ✅ CORRECT: Find tag by name
const urgentTag = tags.byName("urgent");

// Get all tasks with specific tag
if (urgentTag) {
    const urgentTasks = urgentTag.flattenedTasks;
    urgentTasks.forEach(task => {
        console.log(task.name);
    });
}

// Create new tag
const newTag = new Tag("important");

// ============================================================================
// ITERATING WITH ARROW FUNCTIONS
// ============================================================================

// ✅ CORRECT: Arrow functions inherit 'this' automatically
activeTasks.forEach(task => {
    console.log(task.name);
    if (task.dueDate) {
        console.log(`Due: ${task.dueDate}`);
    }
});

// ❌ WRONG: Never use .bind(this) on arrow functions
// activeTasks.forEach(task => {
//     console.log(task.name);
// }.bind(this));  // ERROR! Invalid syntax

// ✅ CORRECT: Regular function can use .bind(this) if needed
activeTasks.forEach(function(task) {
    console.log(task.name);
}.bind(this));

// But arrow functions are preferred (cleaner, no binding needed)
activeTasks.forEach(task => console.log(task.name));

// ============================================================================
// COMPLETE WORKFLOW EXAMPLE
// ============================================================================

// Create a new task with full setup
function createCompleteTask(taskName, projectName, tagNames, dueInDays) {
    // Find or use inbox
    let parent = inbox;
    if (projectName) {
        const project = projects.byName(projectName);
        if (project) {
            parent = project.task;
        }
    }

    // Create task
    const task = new Task(taskName, parent);

    // Set due date
    if (dueInDays !== undefined) {
        const dueDate = new Date();
        dueDate.setDate(dueDate.getDate() + dueInDays);
        dueDate.setHours(23, 59, 59, 999);
        task.dueDate = dueDate;
    }

    // Add tags
    if (tagNames && tagNames.length > 0) {
        tagNames.forEach(tagName => {
            const tag = tags.byName(tagName);
            if (tag) {
                task.addTag(tag);
            }
        });
    }

    return task;
}

// Usage example
const myTask = createCompleteTask("Review quarterly report", "Work", ["urgent", "review"], 7);
