/**
 * Task Parser Library for OmniFocus
 *
 * Enhanced task parsing with clarity assessment and GTD metrics.
 * Extends the base taskMetrics library with additional analysis capabilities.
 *
 * Usage (in OmniFocus plugin):
 *   const taskParser = this.plugIn.library("taskParser");
 *   const parsedTask = taskParser.parseTask(task);
 *
 * @version 1.0.0
 */

(() => {
    var lib = new PlugIn.Library(new Version("1.0"));

    /**
     * Parse a task with enhanced clarity and aging metrics
     * Extends the basic normalizeTask from taskMetrics with additional analysis
     * @param {Task} task - The task to parse
     * @returns {Object} Enhanced task object with clarity and age metrics
     */
    lib.parseTask = function(task) {
        if (!task) {
            throw new Error("Task parameter is required");
        }

        // Start with basic task data (similar to taskMetrics.normalizeTask)
        const parsedTask = {
            id: task.id.primaryKey,
            name: task.name,
            completed: task.completed,
            dropped: task.dropped,
            flagged: task.flagged,
            dueDate: task.dueDate,
            deferDate: task.deferDate,
            estimatedMinutes: task.estimatedMinutes,
            note: task.note || "",
            added: task.added,
            modified: task.modified
        };

        // Add project context
        if (task.containingProject) {
            parsedTask.project = task.containingProject.name;
            parsedTask.projectStatus = task.containingProject.status.name;
        } else {
            parsedTask.project = "Inbox";
            parsedTask.projectStatus = null;
        }

        // Add tags
        parsedTask.tags = task.tags.map(tag => tag.name);

        // Add clarity assessment
        parsedTask.clarity = this.assessTaskClarity(task);

        // Add age metrics
        parsedTask.age = this.calculateTaskAge(task);

        return parsedTask;
    };

    /**
     * Assess task clarity and actionability
     * Checks for vague language, missing context, and GTD next action quality
     * @param {Task} task - The task to assess
     * @returns {Object} Clarity assessment with score and issues
     */
    lib.assessTaskClarity = function(task) {
        if (!task) {
            return {
                score: 0,
                isActionable: false,
                issues: ["Task is null or undefined"]
            };
        }

        const issues = [];
        let score = 10;  // Start with perfect score, deduct for issues

        const taskName = task.name.toLowerCase();

        // Check for vague verbs (reduce clarity)
        const vagueVerbs = [
            "deal with", "handle", "work on", "think about",
            "consider", "look into", "check on", "update",
            "fix", "improve", "organize", "plan"
        ];

        const hasVagueVerb = vagueVerbs.some(verb => taskName.includes(verb));
        if (hasVagueVerb) {
            issues.push("Contains vague action verb - specify concrete next action");
            score -= 2;
        }

        // Check for unclear scope
        const unclearPhrases = [
            "everything", "all the", "various", "stuff",
            "things", "misc", "etc"
        ];

        const hasUnclearScope = unclearPhrases.some(phrase => taskName.includes(phrase));
        if (hasUnclearScope) {
            issues.push("Unclear scope - be specific about what to do");
            score -= 2;
        }

        // Check for missing context (no tags and not in project)
        const hasTags = task.tags.length > 0;
        const hasProject = task.containingProject !== null;

        if (!hasTags && !hasProject) {
            issues.push("No context - add tags or assign to project");
            score -= 1;
        }

        // Check for missing note on complex tasks
        const hasNote = task.note && task.note.trim().length > 0;
        const nameLength = task.name.length;

        // Long task names (> 50 chars) might need notes for context
        if (nameLength > 50 && !hasNote) {
            issues.push("Complex task - consider adding note for context");
            score -= 1;
        }

        // Check for question marks (indicates uncertainty)
        if (taskName.includes("?")) {
            issues.push("Task name contains question - define clear outcome first");
            score -= 2;
        }

        // Check for "or" (indicates multiple options, not clear next action)
        if (taskName.includes(" or ")) {
            issues.push("Task has multiple options - choose one clear action");
            score -= 1;
        }

        // Very short names (< 10 chars) might be unclear
        if (nameLength < 10 && nameLength > 0) {
            issues.push("Very short name - add more detail for clarity");
            score -= 1;
        }

        // Check for good next action verbs (boost clarity)
        const goodVerbs = [
            "call", "email", "write", "create", "send",
            "schedule", "book", "buy", "order", "submit",
            "review", "read", "draft", "finalize", "complete"
        ];

        const hasGoodVerb = goodVerbs.some(verb => taskName.startsWith(verb));
        if (hasGoodVerb) {
            score += 1;  // Bonus for clear action verb
        }

        // Ensure score stays within 1-10 range
        score = Math.max(1, Math.min(10, score));

        // Actionable if score >= 7 and no critical issues
        const isActionable = score >= 7 && !taskName.includes("?");

        return {
            score: score,
            isActionable: isActionable,
            issues: issues
        };
    };

    /**
     * Calculate task age and overdue metrics
     * @param {Task} task - The task to analyze
     * @returns {Object} Age metrics
     */
    lib.calculateTaskAge = function(task) {
        if (!task) {
            return {
                daysOld: 0,
                daysOverdue: 0,
                isOverdue: false,
                isAging: false
            };
        }

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // Days since task was created
        let daysOld = 0;
        if (task.added) {
            daysOld = Math.floor((today - task.added) / (1000 * 60 * 60 * 24));
        }

        // Days overdue
        let daysOverdue = 0;
        let isOverdue = false;

        if (task.dueDate && !task.completed && !task.dropped) {
            const dueDate = new Date(task.dueDate);
            dueDate.setHours(0, 0, 0, 0);

            if (dueDate < today) {
                daysOverdue = Math.floor((today - dueDate) / (1000 * 60 * 60 * 24));
                isOverdue = true;
            }
        }

        // Consider tasks "aging" if they're > 30 days old and not complete
        const isAging = daysOld > 30 && !task.completed && !task.dropped;

        return {
            daysOld: daysOld,
            daysOverdue: daysOverdue,
            isOverdue: isOverdue,
            isAging: isAging
        };
    };

    /**
     * Parse multiple tasks efficiently
     * @param {Array} tasks - Array of task objects
     * @returns {Array} Array of parsed task objects
     */
    lib.parseTasks = function(tasks) {
        if (!tasks || tasks.length === 0) {
            return [];
        }

        return tasks.map(task => this.parseTask(task));
    };

    /**
     * Filter tasks by clarity score
     * Useful for identifying tasks that need improvement
     * @param {Array} parsedTasks - Array of parsed task objects
     * @param {number} minScore - Minimum clarity score (default: 7)
     * @returns {Object} Object with clear and unclear task arrays
     */
    lib.filterByClarity = function(parsedTasks, minScore = 7) {
        if (!parsedTasks || parsedTasks.length === 0) {
            return {
                clear: [],
                unclear: []
            };
        }

        const clear = parsedTasks.filter(t => t.clarity.score >= minScore);
        const unclear = parsedTasks.filter(t => t.clarity.score < minScore);

        return { clear, unclear };
    };

    /**
     * Identify tasks that are aging (> 30 days old, not complete)
     * @param {Array} parsedTasks - Array of parsed task objects
     * @returns {Array} Array of aging tasks sorted by age
     */
    lib.identifyAgingTasks = function(parsedTasks) {
        if (!parsedTasks || parsedTasks.length === 0) {
            return [];
        }

        return parsedTasks
            .filter(t => t.age.isAging)
            .sort((a, b) => b.age.daysOld - a.age.daysOld)  // Oldest first
            .map(t => ({
                id: t.id,
                name: t.name,
                project: t.project,
                daysOld: t.age.daysOld,
                clarityScore: t.clarity.score
            }));
    };

    /**
     * Identify overdue tasks sorted by severity
     * @param {Array} parsedTasks - Array of parsed task objects
     * @returns {Array} Array of overdue tasks sorted by days overdue
     */
    lib.identifyOverdueTasks = function(parsedTasks) {
        if (!parsedTasks || parsedTasks.length === 0) {
            return [];
        }

        return parsedTasks
            .filter(t => t.age.isOverdue)
            .sort((a, b) => b.age.daysOverdue - a.age.daysOverdue)  // Most overdue first
            .map(t => ({
                id: t.id,
                name: t.name,
                project: t.project,
                daysOverdue: t.age.daysOverdue,
                flagged: t.flagged
            }));
    };

    /**
     * Analyze task quality issues across a set of tasks
     * Provides aggregate clarity statistics
     * @param {Array} parsedTasks - Array of parsed task objects
     * @returns {Object} Quality analysis summary
     */
    lib.analyzeTaskQuality = function(parsedTasks) {
        if (!parsedTasks || parsedTasks.length === 0) {
            return {
                totalTasks: 0,
                averageClarity: 0,
                actionableTasks: 0,
                unclearTasks: 0,
                commonIssues: []
            };
        }

        const totalTasks = parsedTasks.length;
        const actionableTasks = parsedTasks.filter(t => t.clarity.isActionable).length;
        const unclearTasks = parsedTasks.filter(t => t.clarity.score < 7).length;

        // Calculate average clarity score
        const totalScore = parsedTasks.reduce((sum, t) => sum + t.clarity.score, 0);
        const averageClarity = totalScore / totalTasks;

        // Collect all issues and find most common
        const issueCount = {};
        parsedTasks.forEach(t => {
            t.clarity.issues.forEach(issue => {
                issueCount[issue] = (issueCount[issue] || 0) + 1;
            });
        });

        // Sort issues by frequency
        const commonIssues = Object.entries(issueCount)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)  // Top 5 issues
            .map(([issue, count]) => ({
                issue: issue,
                count: count,
                percentage: Math.round((count / totalTasks) * 100)
            }));

        return {
            totalTasks: totalTasks,
            averageClarity: Math.round(averageClarity * 10) / 10,  // Round to 1 decimal
            actionableTasks: actionableTasks,
            unclearTasks: unclearTasks,
            actionablePercentage: Math.round((actionableTasks / totalTasks) * 100),
            commonIssues: commonIssues
        };
    };

    return lib;
})();
