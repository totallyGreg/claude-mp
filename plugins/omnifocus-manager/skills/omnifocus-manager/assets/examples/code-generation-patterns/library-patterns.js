/**
 * PlugIn.Library Patterns - Correct OmniFocus API Usage
 *
 * This file demonstrates validated patterns for creating reusable
 * PlugIn.Library modules in OmniFocus Omni Automation plugins.
 *
 * KEY PRINCIPLES:
 * - Libraries use IIFE pattern: (() => { ... })()
 * - Create with: new PlugIn.Library(new Version("1.0"))
 * - Register in manifest.json "libraries" array
 * - Load with: this.plugIn.library("libraryName")
 * - Libraries can access global variables directly
 */

// ============================================================================
// BASIC LIBRARY STRUCTURE
// ============================================================================

// ✅ CORRECT: Basic library template
(() => {
    // Create library with version
    const lib = new PlugIn.Library(new Version("1.0"));

    // Add functions to library
    lib.myFunction = function() {
        // Library code here
    };

    lib.anotherFunction = function(param) {
        // More library code
        return result;
    };

    // Return library object
    return lib;
})();

// ❌ WRONG: Don't export like Node.js modules
// module.exports = { ... };  // ERROR! Not available in OmniFocus

// ============================================================================
// EXAMPLE: TASK METRICS LIBRARY
// ============================================================================

/**
 * taskMetrics.js - Library for task data collection
 *
 * Register in manifest.json:
 * {
 *   "libraries": [
 *     {"name": "taskMetrics", "file": "taskMetrics"}
 *   ]
 * }
 *
 * Load in action:
 * const metrics = this.plugIn.library("taskMetrics");
 */

(() => {
    const lib = new PlugIn.Library(new Version("3.0"));

    /**
     * Get tasks due today
     */
    lib.getTodayTasks = function() {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);

        return flattenedTasks.filter(t => {
            if (t.completed || t.dropped) return false;
            if (!t.dueDate) return false;
            const due = new Date(t.dueDate);
            due.setHours(0, 0, 0, 0);
            return due.getTime() === today.getTime();
        });
    };

    /**
     * Get overdue tasks
     */
    lib.getOverdueTasks = function() {
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        return flattenedTasks.filter(t => {
            if (t.completed || t.dropped) return false;
            if (!t.dueDate) return false;
            return t.dueDate < today;
        });
    };

    /**
     * Get flagged tasks
     */
    lib.getFlaggedTasks = function() {
        return flattenedTasks.filter(t => {
            return t.flagged && !t.completed && !t.dropped;
        });
    };

    return lib;
})();

// ============================================================================
// EXAMPLE: EXPORT UTILITIES LIBRARY
// ============================================================================

/**
 * exportUtils.js - Library for data export
 *
 * Register in manifest.json:
 * {
 *   "libraries": [
 *     {"name": "exportUtils", "file": "exportUtils"}
 *   ]
 * }
 */

(() => {
    const lib = new PlugIn.Library(new Version("3.0"));

    /**
     * Convert task array to JSON
     */
    lib.toJSON = function(tasks) {
        const data = tasks.map(task => ({
            name: task.name,
            note: task.note || "",
            completed: task.completed,
            flagged: task.flagged,
            dueDate: task.dueDate ? task.dueDate.toISOString() : null,
            project: task.containingProject ? task.containingProject.name : "Inbox",
            tags: task.tags.map(tag => tag.name)
        }));

        return JSON.stringify(data, null, 2);
    };

    /**
     * Convert task array to CSV
     */
    lib.toCSV = function(tasks) {
        const headers = ["Name", "Project", "Due Date", "Flagged", "Tags"];
        const rows = [headers.join(",")];

        // ✅ CORRECT: Arrow function inherits 'this' - no .bind() needed
        tasks.forEach(task => {
            const row = [
                this.escapeCSV(task.name),
                this.escapeCSV(task.containingProject ? task.containingProject.name : "Inbox"),
                task.dueDate ? task.dueDate.toLocaleDateString() : "",
                task.flagged ? "Yes" : "No",
                task.tags.map(t => t.name).join("; ")
            ];
            rows.push(row.join(","));
        });

        return rows.join("\n");
    };

    /**
     * Helper: Escape CSV value
     */
    lib.escapeCSV = function(value) {
        if (!value) return "";
        const str = String(value);
        if (str.includes(",") || str.includes('"') || str.includes("\n")) {
            return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
    };

    /**
     * Convert task array to Markdown
     */
    lib.toMarkdown = function(tasks) {
        let md = "# Tasks\n\n";

        tasks.forEach(task => {
            const checkbox = task.completed ? "[x]" : "[ ]";
            const flag = task.flagged ? "🚩 " : "";
            const projectName = task.containingProject ? task.containingProject.name : "Inbox";

            md += `- ${checkbox} ${flag}**${task.name}**\n`;
            md += `  - Project: ${projectName}\n`;

            if (task.dueDate) {
                md += `  - Due: ${task.dueDate.toLocaleDateString()}\n`;
            }

            if (task.tags.length > 0) {
                const tagNames = task.tags.map(t => t.name).join(", ");
                md += `  - Tags: ${tagNames}\n`;
            }

            if (task.note) {
                md += `  - Note: ${task.note}\n`;
            }

            md += "\n";
        });

        return md;
    };

    return lib;
})();

// ============================================================================
// EXAMPLE: DATE UTILITIES LIBRARY
// ============================================================================

/**
 * dateUtils.js - Library for date manipulation
 */

(() => {
    const lib = new PlugIn.Library(new Version("1.0"));

    /**
     * Get date at midnight (00:00:00)
     */
    lib.getMidnight = function(date) {
        const d = new Date(date || new Date());
        d.setHours(0, 0, 0, 0);
        return d;
    };

    /**
     * Get date at end of day (23:59:59)
     */
    lib.getEndOfDay = function(date) {
        const d = new Date(date || new Date());
        d.setHours(23, 59, 59, 999);
        return d;
    };

    /**
     * Add days to date
     */
    lib.addDays = function(date, days) {
        const result = new Date(date);
        result.setDate(result.getDate() + days);
        return result;
    };

    /**
     * Get start of week (Sunday)
     */
    lib.getStartOfWeek = function(date) {
        const d = new Date(date || new Date());
        const day = d.getDay();
        const diff = d.getDate() - day;
        return this.getMidnight(new Date(d.setDate(diff)));
    };

    /**
     * Get end of week (Saturday)
     */
    lib.getEndOfWeek = function(date) {
        const start = this.getStartOfWeek(date);
        return this.getEndOfDay(this.addDays(start, 6));
    };

    /**
     * Check if date is today
     */
    lib.isToday = function(date) {
        const today = this.getMidnight(new Date());
        const check = this.getMidnight(date);
        return today.getTime() === check.getTime();
    };

    /**
     * Format date for display
     */
    lib.formatDate = function(date, format) {
        if (!date) return "";

        const d = new Date(date);
        const pad = (n) => String(n).padStart(2, '0');

        switch (format) {
            case "ISO":
                return d.toISOString();
            case "US":
                return `${d.getMonth() + 1}/${d.getDate()}/${d.getFullYear()}`;
            case "YYYY-MM-DD":
                return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
            default:
                return d.toLocaleDateString();
        }
    };

    return lib;
})();

// ============================================================================
// LOADING LIBRARIES IN ACTIONS
// ============================================================================

/**
 * Example: Using libraries in a plugin action
 */

(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        try {
            // ✅ CORRECT: Load libraries via plugIn
            const metrics = this.plugIn.library("taskMetrics");
            const exportUtils = this.plugIn.library("exportUtils");
            const dateUtils = this.plugIn.library("dateUtils");

            // Use library functions
            const todayTasks = metrics.getTodayTasks();
            const overdueTasks = metrics.getOverdueTasks();

            // Export to different formats
            const jsonData = exportUtils.toJSON(todayTasks);
            const csvData = exportUtils.toCSV(todayTasks);
            const mdData = exportUtils.toMarkdown(todayTasks);

            // Use date utilities
            const today = dateUtils.getMidnight(new Date());
            const nextWeek = dateUtils.addDays(today, 7);

            // Display results
            const alert = new Alert(
                "Task Summary",
                `Today: ${todayTasks.length} tasks\nOverdue: ${overdueTasks.length} tasks`
            );
            await alert.show();

        } catch (error) {
            console.error("Error:", error);
            const errorAlert = new Alert("Error", error.message);
            errorAlert.show();
        }
    });

    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();

// ============================================================================
// LIBRARY WITH DEPENDENCIES (Loading Other Libraries)
// ============================================================================

/**
 * Example: Library that uses another library
 */

(() => {
    const lib = new PlugIn.Library(new Version("1.0"));

    // Note: Can't directly load other libraries in library code
    // Instead, pass them as parameters or use in actions

    /**
     * Generate task report using export utilities
     * @param {Object} exportUtils - The export utilities library
     * @param {Array} tasks - Tasks to report on
     */
    lib.generateReport = function(exportUtils, tasks) {
        const report = {
            summary: {
                total: tasks.length,
                completed: tasks.filter(t => t.completed).length,
                flagged: tasks.filter(t => t.flagged).length
            },
            markdown: exportUtils.toMarkdown(tasks),
            json: exportUtils.toJSON(tasks)
        };

        return report;
    };

    return lib;
})();

// Usage in action:
// const reportLib = this.plugIn.library("reportLib");
// const exportUtils = this.plugIn.library("exportUtils");
// const report = reportLib.generateReport(exportUtils, tasks);

// ============================================================================
// LIBRARY WITH FOUNDATION MODELS INTEGRATION
// ============================================================================

/**
 * Example: Library using LanguageModel for AI analysis
 */

(() => {
    const lib = new PlugIn.Library(new Version("1.0"));

    /**
     * Analyze tasks with AI
     */
    lib.analyzeTasks = async function(tasks) {
        // Limit tasks to avoid context window issues
        const limitedTasks = tasks.slice(0, 10);

        // Build concise prompt
        const taskList = limitedTasks.map(t => {
            const flag = t.flagged ? "🚩 " : "";
            const project = t.containingProject ? t.containingProject.name : "Inbox";
            return `- ${flag}${t.name} [${project}]`;
        }).join("\n");

        const prompt = `Analyze these tasks and suggest top 3 priorities:\n\n${taskList}`;

        // Create AI session
        const session = new LanguageModel.Session();

        // ✅ CORRECT: Use fromJSON factory method with OmniFocus schema format
        const schema = LanguageModel.Schema.fromJSON({
            name: "priorities-schema",
            properties: [
                {
                    name: "recommendations",
                    schema: {
                        arrayOf: {
                            name: "recommendation",
                            properties: [
                                {name: "taskName"},
                                {name: "reason"}
                            ]
                        }
                    }
                }
            ]
        });

        // Get structured response
        const response = await session.respondWithSchema(prompt, schema);
        return JSON.parse(response);
    };

    return lib;
})();

// ============================================================================
// MANIFEST.JSON CONFIGURATION
// ============================================================================

/**
 * Example manifest.json with multiple libraries:
 *
 * {
 *   "identifier": "com.example.my-plugin",
 *   "version": "1.0",
 *   "author": "Your Name",
 *   "description": "Plugin with multiple libraries",
 *   "libraries": [
 *     {"name": "taskMetrics", "file": "taskMetrics"},
 *     {"name": "exportUtils", "file": "exportUtils"},
 *     {"name": "dateUtils", "file": "dateUtils"}
 *   ],
 *   "actions": [
 *     {
 *       "identifier": "analyzeToday",
 *       "label": "Analyze Today's Tasks",
 *       "mediumLabel": "Analyze Today",
 *       "shortLabel": "Today",
 *       "image": "folder"
 *     }
 *   ]
 * }
 */

// ============================================================================
// LIBRARY VERSIONING
// ============================================================================

/**
 * Update library version when making changes
 */

// Version 1.0 - Initial release
(() => {
    const lib = new PlugIn.Library(new Version("1.0"));
    lib.myFunction = function() { /* ... */ };
    return lib;
})();

// Version 1.1 - Added new function
(() => {
    const lib = new PlugIn.Library(new Version("1.1"));
    lib.myFunction = function() { /* ... */ };
    lib.newFunction = function() { /* NEW */ };
    return lib;
})();

// Version 2.0 - Breaking changes
(() => {
    const lib = new PlugIn.Library(new Version("2.0"));
    // Changed function signature (breaking change)
    lib.myFunction = function(newParam) { /* ... */ };
    return lib;
})();

// ============================================================================
// TESTING LIBRARIES
// ============================================================================

/**
 * Test library in Automation Console before packaging
 */

// In OmniFocus Automation Console:
// 1. Paste library code
// 2. Test functions directly
// 3. Verify no errors

// Example test:
(() => {
    const lib = new PlugIn.Library(new Version("1.0"));

    lib.getTodayTasks = function() {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);

        return flattenedTasks.filter(t => {
            if (t.completed || t.dropped) return false;
            if (!t.dueDate) return false;
            const due = new Date(t.dueDate);
            due.setHours(0, 0, 0, 0);
            return due.getTime() === today.getTime();
        });
    };

    // Test the function
    const tasks = lib.getTodayTasks();
    console.log(`Found ${tasks.length} tasks due today`);
    tasks.forEach(t => console.log(`- ${t.name}`));

    return lib;
})();
