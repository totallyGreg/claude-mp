/**
 * Project Parser Library for OmniFocus
 *
 * Composable library for parsing project objects with GTD health indicators
 * and task metrics. Designed for hierarchical analysis and bottleneck detection.
 *
 * Usage (in OmniFocus plugin):
 *   const projectParser = this.plugIn.library("projectParser");
 *   const parsedProject = projectParser.parseProject(project, true);
 *
 * @version 1.0.0
 */

(() => {
    var lib = new PlugIn.Library(new Version("1.0"));

    /**
     * Parse a project with metrics and optional task details
     * @param {Project} project - The project to parse
     * @param {boolean} includeTaskDetails - Whether to include detailed task information
     * @returns {Object} Structured project data with metrics and GTD health
     */
    lib.parseProject = function(project, includeTaskDetails = false) {
        if (!project) {
            throw new Error("Project parameter is required");
        }

        const parsedProject = {
            id: project.id.primaryKey,
            name: project.name,
            status: project.status.name,  // "active", "on hold", "done", "dropped"
            type: project.sequential ? "sequential" : "parallel",
            completed: project.completed,
            completionDate: project.completionDate
        };

        // Add folder context if available
        if (project.parentFolder) {
            parsedProject.folder = project.parentFolder.name;
        }

        // Calculate project metrics
        parsedProject.metrics = this.calculateProjectMetrics(project);

        // Assess GTD health indicators
        parsedProject.gtdHealth = this.assessGTDHealth(project);

        // Include task details if requested
        if (includeTaskDetails) {
            parsedProject.tasks = this._parseTasksBasic(project);
        } else {
            // Just include task count for summary
            parsedProject.taskCount = project.tasks.length;
        }

        return parsedProject;
    };

    /**
     * Calculate project-level metrics
     * Includes task counts, completion rates, and health indicators
     * @param {Project} project - The project to analyze
     * @returns {Object} Metrics object
     */
    lib.calculateProjectMetrics = function(project) {
        if (!project) {
            return {
                taskCount: 0,
                completedTasks: 0,
                activeTasks: 0,
                overdueTasks: 0,
                flaggedTasks: 0,
                completionRate: 0,
                daysActive: 0,
                hasOverdueAccumulation: false
            };
        }

        const tasks = project.flattenedTasks || [];
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // Task counts
        const totalTasks = tasks.length;
        const completedTasks = tasks.filter(t => t.completed).length;
        const activeTasks = tasks.filter(t => !t.completed && !t.dropped).length;
        const droppedTasks = tasks.filter(t => t.dropped).length;

        // Overdue and flagged
        const overdueTasks = tasks.filter(t => {
            if (t.completed || t.dropped) return false;
            return t.dueDate && t.dueDate < today;
        }).length;

        const flaggedTasks = tasks.filter(t => !t.completed && !t.dropped && t.flagged).length;

        // Completion rate (exclude dropped tasks)
        const completableTasks = totalTasks - droppedTasks;
        const completionRate = completableTasks > 0
            ? Math.round((completedTasks / completableTasks) * 100)
            : 0;

        // Days since project creation
        const daysActive = project.added
            ? Math.floor((today - project.added) / (1000 * 60 * 60 * 24))
            : 0;

        // Check for overdue accumulation (more than 3 overdue tasks suggests scope creep)
        const hasOverdueAccumulation = overdueTasks > 3;

        return {
            taskCount: totalTasks,
            completedTasks: completedTasks,
            activeTasks: activeTasks,
            droppedTasks: droppedTasks,
            overdueTasks: overdueTasks,
            flaggedTasks: flaggedTasks,
            completionRate: completionRate,
            daysActive: daysActive,
            hasOverdueAccumulation: hasOverdueAccumulation
        };
    };

    /**
     * Assess GTD health indicators for a project
     * Checks for note/context, next actions, and review status
     * @param {Project} project - The project to assess
     * @returns {Object} GTD health indicators
     */
    lib.assessGTDHealth = function(project) {
        if (!project) {
            return {
                hasNote: false,
                hasNextAction: false,
                nextActionCount: 0,
                daysSinceReview: null,
                needsReview: false,
                isStalledRisk: false
            };
        }

        // Check for project note (context/outcome definition)
        const hasNote = project.note && project.note.trim().length > 0;

        // Count available next actions (tasks that are actionable now)
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const tasks = project.flattenedTasks || [];
        const availableTasks = tasks.filter(t => {
            if (t.completed || t.dropped) return false;

            // Check if task is available (not deferred to future)
            const isAvailable = !t.deferDate || t.deferDate <= today;
            return isAvailable;
        });

        const nextActionCount = availableTasks.length;
        const hasNextAction = nextActionCount > 0;

        // Check review status
        const lastReviewed = project.lastReviewedDate;
        let daysSinceReview = null;
        let needsReview = false;

        if (lastReviewed) {
            daysSinceReview = Math.floor((today - lastReviewed) / (1000 * 60 * 60 * 24));
            // Projects should be reviewed at least monthly (30 days)
            needsReview = daysSinceReview > 30;
        } else {
            // Never reviewed
            needsReview = true;
        }

        // Stalled risk: Active project with no next actions
        const isStalledRisk = project.status.name === "active" && !hasNextAction;

        return {
            hasNote: hasNote,
            hasNextAction: hasNextAction,
            nextActionCount: nextActionCount,
            daysSinceReview: daysSinceReview,
            needsReview: needsReview,
            isStalledRisk: isStalledRisk
        };
    };

    /**
     * Get basic task information for a project (private helper)
     * Used when includeTaskDetails is true
     * @param {Project} project - The project to extract tasks from
     * @returns {Array} Array of basic task objects
     * @private
     */
    lib._parseTasksBasic = function(project) {
        const tasks = project.flattenedTasks || [];

        return tasks.map(task => ({
            id: task.id.primaryKey,
            name: task.name,
            completed: task.completed,
            dropped: task.dropped,
            flagged: task.flagged,
            dueDate: task.dueDate,
            deferDate: task.deferDate,
            tags: task.tags.map(tag => tag.name),
            hasNote: task.note && task.note.trim().length > 0
        }));
    };

    /**
     * Parse multiple projects efficiently
     * @param {Array} projects - Array of project objects
     * @param {boolean} includeTaskDetails - Whether to include task details
     * @returns {Array} Array of parsed project objects
     */
    lib.parseProjects = function(projects, includeTaskDetails = false) {
        if (!projects || projects.length === 0) {
            return [];
        }

        return projects.map(project => this.parseProject(project, includeTaskDetails));
    };

    /**
     * Filter projects by status for analysis
     * @param {Array} parsedProjects - Array of parsed project objects
     * @param {string} status - Status filter: "active", "on hold", "completed", "all"
     * @returns {Array} Filtered array of projects
     */
    lib.filterByStatus = function(parsedProjects, status = "active") {
        if (!parsedProjects || parsedProjects.length === 0) {
            return [];
        }

        if (status === "all") {
            return parsedProjects;
        }

        return parsedProjects.filter(p => p.status === status);
    };

    /**
     * Identify stalled projects (active projects with no next actions)
     * @param {Array} parsedProjects - Array of parsed project objects
     * @returns {Array} Array of stalled projects with stall duration
     */
    lib.identifyStalledProjects = function(parsedProjects) {
        if (!parsedProjects || parsedProjects.length === 0) {
            return [];
        }

        return parsedProjects
            .filter(p => p.gtdHealth.isStalledRisk)
            .map(p => ({
                id: p.id,
                name: p.name,
                folder: p.folder,
                daysActive: p.metrics.daysActive,
                taskCount: p.metrics.taskCount,
                reason: this._determineStalledReason(p)
            }));
    };

    /**
     * Determine why a project is stalled (private helper)
     * @param {Object} parsedProject - Parsed project object
     * @returns {string} Reason for stall
     * @private
     */
    lib._determineStalledReason = function(parsedProject) {
        const { metrics, gtdHealth } = parsedProject;

        if (metrics.taskCount === 0) {
            return "No tasks defined";
        }

        if (metrics.activeTasks === 0 && metrics.completedTasks > 0) {
            return "All tasks deferred or blocked";
        }

        if (metrics.activeTasks > 0 && gtdHealth.nextActionCount === 0) {
            return "All tasks deferred to future";
        }

        return "No available next actions";
    };

    /**
     * Identify projects needing more context/exposition
     * Projects without notes or with stall risk
     * @param {Array} parsedProjects - Array of parsed project objects
     * @returns {Array} Array of projects needing exposition
     */
    lib.identifyProjectsNeedingExposition = function(parsedProjects) {
        if (!parsedProjects || parsedProjects.length === 0) {
            return [];
        }

        return parsedProjects
            .filter(p => {
                // Active or on hold projects only
                if (p.completed || p.status === "dropped") return false;

                // Missing note is primary indicator
                if (!p.gtdHealth.hasNote) return true;

                // Stalled projects also need exposition
                if (p.gtdHealth.isStalledRisk) return true;

                // Projects with poor progress (< 20% complete after 30+ days)
                if (p.metrics.daysActive > 30 && p.metrics.completionRate < 20) return true;

                return false;
            })
            .map(p => ({
                id: p.id,
                name: p.name,
                folder: p.folder,
                reasons: this._getExpositionReasons(p)
            }));
    };

    /**
     * Get reasons why a project needs exposition (private helper)
     * @param {Object} parsedProject - Parsed project object
     * @returns {Array} Array of reason strings
     * @private
     */
    lib._getExpositionReasons = function(parsedProject) {
        const reasons = [];

        if (!parsedProject.gtdHealth.hasNote) {
            reasons.push("No project note or outcome defined");
        }

        if (parsedProject.gtdHealth.isStalledRisk) {
            reasons.push("Stalled - no available next actions");
        }

        if (parsedProject.metrics.daysActive > 30 && parsedProject.metrics.completionRate < 20) {
            reasons.push("Minimal progress after 30+ days");
        }

        if (parsedProject.gtdHealth.needsReview) {
            reasons.push("Needs review (30+ days since last review)");
        }

        return reasons;
    };

    return lib;
})();
