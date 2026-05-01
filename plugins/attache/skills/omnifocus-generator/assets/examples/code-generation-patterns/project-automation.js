/**
 * Project and Folder Automation - Correct OmniFocus API Usage Patterns
 *
 * This file demonstrates validated patterns for working with projects
 * and folders in OmniFocus Omni Automation plugins.
 *
 * KEY PRINCIPLES:
 * - Projects have a root task accessible via .task property
 * - Use global variables (projects, folders) not Document.defaultDocument
 * - Project status is an enum (Project.Status.Active, .OnHold, .Done, .Dropped)
 */

// ============================================================================
// ACCESSING PROJECTS AND FOLDERS
// ============================================================================

// ✅ CORRECT: Use global variables
const allProjects = flattenedProjects;  // All projects (including nested)
const topLevelProjects = projects;       // Only root-level projects
const allFolders = flattenedFolders;     // All folders (including nested)
const topLevelFolders = folders;         // Only root-level folders

// Find project by name
const myProject = projects.byName("My Project");

// Find folder by name
const workFolder = folders.byName("Work");

// ❌ WRONG: Don't use Document.defaultDocument
// const doc = Document.defaultDocument;
// const projects = doc.flattenedProjects;  // ERROR!

// ============================================================================
// READING PROJECT PROPERTIES
// ============================================================================

// ✅ CORRECT: Properties accessed directly (no parentheses)
const projectName = myProject.name;
const projectNote = myProject.note;
const projectStatus = myProject.status;
const isCompleted = myProject.completed;
const completionDate = myProject.completionDate;
const dueDate = myProject.dueDate;
const deferDate = myProject.deferDate;
const isFlagged = myProject.flagged;
const projectTags = myProject.tags;
const rootTask = myProject.task;
const allTasks = myProject.flattenedTasks;
const parentFolder = myProject.parentFolder;

// ============================================================================
// PROJECT STATUS MANAGEMENT
// ============================================================================

// Project status enum values
const statusValues = {
    active: Project.Status.Active,
    onHold: Project.Status.OnHold,
    done: Project.Status.Done,
    dropped: Project.Status.Dropped
};

// ✅ CORRECT: Set project status
myProject.status = Project.Status.Active;
myProject.status = Project.Status.OnHold;
myProject.status = Project.Status.Done;
myProject.status = Project.Status.Dropped;

// ✅ CORRECT: Mark project complete/incomplete
myProject.markComplete();
myProject.markIncomplete();

// Filter projects by status
const activeProjects = flattenedProjects.filter(p => p.status === Project.Status.Active);
const onHoldProjects = flattenedProjects.filter(p => p.status === Project.Status.OnHold);
const completedProjects = flattenedProjects.filter(p => p.completed);

// ============================================================================
// CREATING PROJECTS
// ============================================================================

// ✅ CORRECT: Create project at root level
const newProject = new Project("New Project Name");
newProject.note = "Project description and goals";
newProject.dueDate = new Date("2025-12-31");
newProject.status = Project.Status.Active;

// ✅ CORRECT: Create project in folder
const folder = folders.byName("Work");
if (folder) {
    const workProject = new Project("Work Project", folder);
    workProject.note = "Work-related project";
}

// ✅ CORRECT: Create project with tags
const project = new Project("Tagged Project");
const urgentTag = tags.byName("urgent");
if (urgentTag) {
    project.addTag(urgentTag);
}

// ============================================================================
// WORKING WITH PROJECT TASKS
// ============================================================================

// Access project's root task
const rootTask = myProject.task;

// Add task to project (add to root task)
const newTask = new Task("First task", rootTask);
newTask.note = "Task details";

// Get all tasks in project (including nested)
const projectTasks = myProject.flattenedTasks;

// Get only direct child tasks (first level)
const directTasks = myProject.task.children;

// Count incomplete tasks in project
const incompleteTasks = myProject.flattenedTasks.filter(t => !t.completed && !t.dropped);
const incompleteCount = incompleteTasks.length;

// Check if project is stalled (no remaining tasks)
const isStalled = myProject.flattenedTasks.every(t => t.completed || t.dropped);

// ============================================================================
// FOLDER OPERATIONS
// ============================================================================

// ✅ CORRECT: Create folder at root level
const newFolder = new Folder("New Folder");
newFolder.note = "Folder description";

// ✅ CORRECT: Create nested folder
const parentFolder = folders.byName("Work");
if (parentFolder) {
    const subFolder = new Folder("Subfolder", parentFolder);
}

// Access folder's projects
const folderProjects = workFolder.projects;  // Direct child projects only
const allFolderProjects = workFolder.flattenedProjects;  // All nested projects

// Access folder's subfolders
const subFolders = workFolder.folders;  // Direct child folders
const allSubFolders = workFolder.flattenedFolders;  // All nested folders

// Find project within folder
const projectInFolder = workFolder.projectNamed("Specific Project");

// Find subfolder within folder
const subFolder = workFolder.folderNamed("Subfolder");

// ============================================================================
// FILTERING PROJECTS
// ============================================================================

// Get active projects
const active = flattenedProjects.filter(p => p.status === Project.Status.Active);

// Get flagged projects
const flagged = flattenedProjects.filter(p => p.flagged);

// Get projects due soon
const today = new Date();
today.setHours(0, 0, 0, 0);
const weekFromNow = new Date(today);
weekFromNow.setDate(weekFromNow.getDate() + 7);

const dueSoon = flattenedProjects.filter(p => {
    if (!p.dueDate) return false;
    return p.dueDate >= today && p.dueDate < weekFromNow;
});

// Get overdue projects
const overdue = flattenedProjects.filter(p => {
    if (p.completed) return false;
    if (!p.dueDate) return false;
    return p.dueDate < today;
});

// Get projects in specific folder
const workProjects = flattenedProjects.filter(p => {
    const folder = p.parentFolder;
    return folder && folder.name === "Work";
});

// Get projects with specific tag
const urgentProjects = flattenedProjects.filter(p => {
    const urgentTag = tags.byName("urgent");
    return urgentTag && p.tags.includes(urgentTag);
});

// ============================================================================
// SEQUENTIAL VS PARALLEL PROJECTS
// ============================================================================

// Check if project is sequential
// Note: Sequential is a property of the root task, not the project itself
const isSequential = myProject.task.sequential;

// Set project to sequential
myProject.task.sequential = true;

// Set project to parallel
myProject.task.sequential = false;

// ============================================================================
// BULK PROJECT OPERATIONS
// ============================================================================

// Put all projects in folder on hold
function putFolderOnHold(folderName) {
    const folder = folders.byName(folderName);
    if (!folder) return;

    folder.flattenedProjects.forEach(project => {
        if (project.status === Project.Status.Active) {
            project.status = Project.Status.OnHold;
        }
    });
}

// Activate all projects in folder
function activateFolderProjects(folderName) {
    const folder = folders.byName(folderName);
    if (!folder) return;

    folder.flattenedProjects.forEach(project => {
        if (project.status === Project.Status.OnHold) {
            project.status = Project.Status.Active;
        }
    });
}

// Mark all completed projects as done
function archiveCompletedProjects() {
    flattenedProjects.forEach(project => {
        if (project.completed && project.status !== Project.Status.Done) {
            project.status = Project.Status.Done;
        }
    });
}

// Find and mark stalled projects
function markStalledProjects() {
    const stalledProjects = flattenedProjects.filter(project => {
        if (project.completed) return false;
        if (project.status !== Project.Status.Active) return false;

        const remainingTasks = project.flattenedTasks.filter(t => !t.completed && !t.dropped);
        return remainingTasks.length === 0;
    });

    stalledProjects.forEach(project => {
        project.status = Project.Status.OnHold;
        project.note = (project.note || "") + "\n\n[Auto-marked on hold: No remaining tasks]";
    });

    return stalledProjects;
}

// ============================================================================
// PROJECT TEMPLATES
// ============================================================================

// Create project from template structure
function createProjectFromTemplate(projectName, folderName, taskList) {
    // Find or create folder
    let folder = null;
    if (folderName) {
        folder = folders.byName(folderName);
        if (!folder) {
            folder = new Folder(folderName);
        }
    }

    // Create project
    const project = folder ? new Project(projectName, folder) : new Project(projectName);

    // Add tasks from template
    taskList.forEach(taskInfo => {
        const task = new Task(taskInfo.name, project.task);
        if (taskInfo.note) task.note = taskInfo.note;
        if (taskInfo.estimatedMinutes) task.estimatedMinutes = taskInfo.estimatedMinutes;
        if (taskInfo.tags) {
            taskInfo.tags.forEach(tagName => {
                const tag = tags.byName(tagName);
                if (tag) task.addTag(tag);
            });
        }
    });

    return project;
}

// Usage example
const weeklyReview = createProjectFromTemplate(
    "Weekly Review - 2025 W01",
    "Personal",
    [
        { name: "Review inbox", estimatedMinutes: 15 },
        { name: "Process email", estimatedMinutes: 30 },
        { name: "Review calendar", estimatedMinutes: 10 },
        { name: "Update project statuses", estimatedMinutes: 20, tags: ["review"] },
        { name: "Plan next week", estimatedMinutes: 30, tags: ["planning"] }
    ]
);

// ============================================================================
// PROJECT REPORTING
// ============================================================================

// Generate project statistics
function getProjectStats(project) {
    const allTasks = project.flattenedTasks;

    return {
        name: project.name,
        status: project.status,
        totalTasks: allTasks.length,
        completedTasks: allTasks.filter(t => t.completed).length,
        remainingTasks: allTasks.filter(t => !t.completed && !t.dropped).length,
        droppedTasks: allTasks.filter(t => t.dropped).length,
        flaggedTasks: allTasks.filter(t => t.flagged && !t.completed).length,
        estimatedMinutes: allTasks.reduce((sum, t) => sum + (t.estimatedMinutes || 0), 0),
        dueDate: project.dueDate,
        completionDate: project.completionDate
    };
}

// Generate folder summary
function getFolderSummary(folderName) {
    const folder = folders.byName(folderName);
    if (!folder) return null;

    const projects = folder.flattenedProjects;

    return {
        folderName: folder.name,
        totalProjects: projects.length,
        activeProjects: projects.filter(p => p.status === Project.Status.Active).length,
        onHoldProjects: projects.filter(p => p.status === Project.Status.OnHold).length,
        completedProjects: projects.filter(p => p.completed).length,
        totalTasks: projects.reduce((sum, p) => sum + p.flattenedTasks.length, 0),
        remainingTasks: projects.reduce((sum, p) => {
            return sum + p.flattenedTasks.filter(t => !t.completed && !t.dropped).length;
        }, 0)
    };
}

// ============================================================================
// COMPLETE WORKFLOW EXAMPLE
// ============================================================================

// Quarterly project review workflow
function quarterlyProjectReview() {
    const results = {
        archived: [],
        putOnHold: [],
        reactivated: [],
        stalled: []
    };

    flattenedProjects.forEach(project => {
        // Skip already archived/dropped projects
        if (project.status === Project.Status.Done || project.status === Project.Status.Dropped) {
            return;
        }

        // Archive completed projects
        if (project.completed) {
            project.status = Project.Status.Done;
            results.archived.push(project.name);
            return;
        }

        // Find stalled projects (no remaining tasks)
        const remainingTasks = project.flattenedTasks.filter(t => !t.completed && !t.dropped);
        if (remainingTasks.length === 0 && project.status === Project.Status.Active) {
            project.status = Project.Status.OnHold;
            project.note = (project.note || "") + "\n\n[Auto-review: No remaining tasks]";
            results.stalled.push(project.name);
            return;
        }

        // Reactivate projects with due dates in next 30 days
        if (project.status === Project.Status.OnHold && project.dueDate) {
            const thirtyDaysOut = new Date();
            thirtyDaysOut.setDate(thirtyDaysOut.getDate() + 30);

            if (project.dueDate <= thirtyDaysOut) {
                project.status = Project.Status.Active;
                results.reactivated.push(project.name);
            }
        }
    });

    return results;
}
