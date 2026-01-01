/**
 * Composable Patterns Library for OmniFocus
 *
 * MCP-ready pattern functions for common OmniFocus automation workflows.
 * Each function has clean JSON input/output contracts designed for:
 * - Direct use in OmniFocus plugins
 * - Future MCP server tool definitions
 * - Skill execution architecture (execute over generate)
 *
 * Usage (in OmniFocus plugin):
 *   // In manifest.json, declare as library with dependencies:
 *   "libraries": ["patterns", "taskMetrics", "exportUtils", "insightPatterns"]
 *
 *   // In action script:
 *   const patterns = this.plugIn.library("patterns");
 *   const result = await patterns.queryAndExport({
 *     query: { filter: "today" },
 *     export: { format: "markdown", destination: "clipboard" }
 *   });
 *
 * Usage (in Omni Automation console):
 *   // Load library code and evaluate
 *   const patterns = <paste this code>;
 *   const result = await patterns.queryAndExport({...});
 *
 * @version 3.0.0
 */

(() => {
    const patterns = new PlugIn.Library(function() {
        const lib = this;

        /**
         * Query tasks and analyze with AI-powered insights
         *
         * PRIMARY NEW CAPABILITY: Designed for Apple Foundation Models integration.
         * Currently uses rule-based insightPatterns library. When Foundation Models
         * API becomes available, this function will call on-device AI for analysis.
         *
         * MCP Tool Contract:
         * @param {Object} config - Analysis configuration
         * @param {Object} config.query - Task query filter
         * @param {string} config.query.filter - Filter type: "today", "overdue", "flagged", "available", "tag", "project"
         * @param {string} config.query.tagName - Tag name (when filter="tag")
         * @param {string} config.query.projectName - Project name (when filter="project")
         * @param {number} config.query.days - Days to look ahead (when filter="upcoming")
         * @param {string} config.prompt - Analysis prompt for AI (future use)
         * @param {Object} config.schema - Expected response schema (future use)
         * @param {Array<string>} config.patterns - Patterns to detect (default: all)
         * @returns {Promise<Object>} Analysis result
         * @returns {boolean} .success - Operation success status
         * @returns {Array} .tasks - Queried tasks
         * @returns {Object} .analysis - AI-generated or rule-based analysis
         * @returns {Array} .recommendations - Actionable recommendations
         * @returns {Object} .metadata - Request metadata (duration, count, version)
         */
        lib.queryAndAnalyzeWithAI = async function(config) {
            const startTime = Date.now();

            try {
                // Step 1: Query tasks based on filter
                const tasks = this.queryTasks(config.query || {});

                // Step 2: Detect patterns using rule-based library
                // NOTE: When Foundation Models API available, replace with:
                // const analysis = await this.callFoundationModel(tasks, config.prompt, config.schema);
                const metrics = this.plugIn.library("taskMetrics");
                const insights = this.plugIn.library("insightPatterns");

                const insightResult = insights.generateInsights({
                    patterns: config.patterns
                });

                // Step 3: Format analysis results
                const analysis = {
                    summary: insightResult.summary,
                    insights: insightResult.insights,
                    healthScore: insightResult.summary.healthScore
                };

                // Step 4: Generate recommendations
                const recommendations = this.generateRecommendations(insightResult);

                return {
                    success: true,
                    tasks: tasks,
                    analysis: analysis,
                    recommendations: recommendations,
                    metadata: {
                        duration: Date.now() - startTime,
                        taskCount: tasks.length,
                        insightCount: insightResult.insights.length,
                        version: "3.0.0"
                    }
                };
            } catch (error) {
                return {
                    success: false,
                    error: {
                        code: "ANALYSIS_ERROR",
                        message: error.message || error.toString(),
                        details: { config: config }
                    },
                    metadata: {
                        duration: Date.now() - startTime,
                        version: "3.0.0"
                    }
                };
            }
        };

        /**
         * Query tasks, optionally transform, and export to format/destination
         *
         * MCP Tool Contract:
         * @param {Object} config - Export configuration
         * @param {Object} config.query - Task query filter (same as queryAndAnalyzeWithAI)
         * @param {string} config.transform - Transform type: "summary", "detailed", "custom"
         * @param {Object} config.export - Export configuration
         * @param {string} config.export.format - Format: "json", "csv", "markdown", "html"
         * @param {string} config.export.destination - Destination: "clipboard", "file"
         * @param {string} config.export.filename - Filename for file export
         * @param {string} config.export.title - Title for markdown export
         * @returns {Promise<Object>} Export result
         * @returns {boolean} .success - Operation success status
         * @returns {number} .count - Number of tasks exported
         * @returns {string} .destination - Where data was exported
         * @returns {string} .preview - Preview of exported data (first 200 chars)
         * @returns {Object} .metadata - Request metadata
         */
        lib.queryAndExport = async function(config) {
            const startTime = Date.now();

            try {
                // Step 1: Query tasks
                const tasks = this.queryTasks(config.query || {});

                // Step 2: Transform if requested
                const transformed = this.transformTasks(tasks, config.transform || "detailed");

                // Step 3: Export to destination
                const exporter = this.plugIn.library("exportUtils");
                const exportConfig = config.export || {};
                const format = exportConfig.format || "json";
                const destination = exportConfig.destination || "clipboard";

                let exportSuccess = false;
                let exportedTo = "";

                if (destination === "clipboard") {
                    exportSuccess = exporter.toClipboard(transformed, {
                        format: format,
                        title: exportConfig.title
                    });
                    exportedTo = "clipboard";
                } else if (destination === "file") {
                    exportSuccess = await exporter.toFile(transformed, {
                        format: format,
                        filename: exportConfig.filename,
                        title: exportConfig.title
                    });
                    exportedTo = exportConfig.filename || "file";
                }

                // Step 4: Generate preview
                const preview = this.generatePreview(transformed, format);

                return {
                    success: exportSuccess,
                    count: Array.isArray(transformed) ? transformed.length : 1,
                    destination: exportedTo,
                    format: format,
                    preview: preview,
                    metadata: {
                        duration: Date.now() - startTime,
                        version: "3.0.0"
                    }
                };
            } catch (error) {
                return {
                    success: false,
                    error: {
                        code: "EXPORT_ERROR",
                        message: error.message || error.toString(),
                        details: { config: config }
                    },
                    metadata: {
                        duration: Date.now() - startTime,
                        version: "3.0.0"
                    }
                };
            }
        };

        /**
         * Batch update tasks matching selector
         *
         * MCP Tool Contract:
         * @param {Object} config - Batch update configuration
         * @param {Object} config.selector - Task selection criteria
         * @param {string} config.selector.filter - Filter type (same as query)
         * @param {Object} config.updates - Properties to update
         * @param {boolean} config.updates.flagged - Set flag status
         * @param {string} config.updates.tag - Add tag
         * @param {string} config.updates.project - Move to project
         * @param {string} config.updates.defer - Set defer date
         * @param {boolean} config.dryRun - Preview changes without applying (default: true)
         * @returns {Promise<Object>} Batch update result
         * @returns {boolean} .success - Operation success status
         * @returns {number} .matched - Number of tasks matched by selector
         * @returns {number} .updated - Number of tasks updated
         * @returns {Array} .changes - Preview of changes made
         * @returns {Array} .errors - Errors encountered
         * @returns {Object} .metadata - Request metadata
         */
        lib.batchUpdate = async function(config) {
            const startTime = Date.now();

            try {
                const dryRun = config.dryRun !== false; // Default to true for safety

                // Step 1: Select tasks
                const tasks = this.queryTasks(config.selector || {});

                // Step 2: Apply updates
                const changes = [];
                const errors = [];
                let updated = 0;

                tasks.forEach((taskData, index) => {
                    try {
                        // Find actual task object (taskData is normalized)
                        const task = this.findTaskByName(taskData.name);
                        if (!task) {
                            errors.push({
                                task: taskData.name,
                                error: "Task not found"
                            });
                            return;
                        }

                        const change = {
                            task: taskData.name,
                            before: {},
                            after: {}
                        };

                        // Apply each update
                        if (config.updates.flagged !== undefined) {
                            change.before.flagged = task.flagged;
                            if (!dryRun) task.flagged = config.updates.flagged;
                            change.after.flagged = config.updates.flagged;
                        }

                        if (config.updates.tag) {
                            const tag = this.findOrCreateTag(config.updates.tag);
                            if (tag) {
                                change.before.tags = task.tags.map(t => t.name);
                                if (!dryRun) task.addTag(tag);
                                change.after.tags = [...change.before.tags, config.updates.tag];
                            }
                        }

                        // Add more update types as needed...

                        changes.push(change);
                        if (!dryRun) updated++;
                    } catch (error) {
                        errors.push({
                            task: taskData.name,
                            error: error.message
                        });
                    }
                });

                return {
                    success: true,
                    matched: tasks.length,
                    updated: updated,
                    dryRun: dryRun,
                    changes: changes,
                    errors: errors,
                    metadata: {
                        duration: Date.now() - startTime,
                        version: "3.0.0"
                    }
                };
            } catch (error) {
                return {
                    success: false,
                    error: {
                        code: "BATCH_UPDATE_ERROR",
                        message: error.message || error.toString(),
                        details: { config: config }
                    },
                    metadata: {
                        duration: Date.now() - startTime,
                        version: "3.0.0"
                    }
                };
            }
        };

        /**
         * Perform periodic review (daily, weekly, monthly)
         *
         * MCP Tool Contract:
         * @param {Object} config - Review configuration
         * @param {string} config.period - Period: "daily", "weekly", "monthly"
         * @param {string} config.focus - Focus area: "inbox", "projects", "waiting", "all"
         * @returns {Promise<Object>} Review result
         * @returns {boolean} .success - Operation success status
         * @returns {Object} .tasks - Tasks grouped by category
         * @returns {Object} .insights - Review insights
         * @returns {Array} .actions - Suggested actions
         * @returns {Object} .metadata - Request metadata
         */
        lib.periodicReview = async function(config) {
            const startTime = Date.now();

            try {
                const metrics = this.plugIn.library("taskMetrics");
                const insights = this.plugIn.library("insightPatterns");

                // Step 1: Gather tasks for review period
                const taskGroups = {
                    overdue: metrics.getOverdueTasks(),
                    today: metrics.getTodayTasks(),
                    upcoming: metrics.getUpcomingTasks(7),
                    flagged: metrics.getFlaggedTasks()
                };

                // Step 2: Run insight analysis
                const insightResult = insights.generateInsights();

                // Step 3: Generate period-specific actions
                const actions = this.generateReviewActions(config.period, taskGroups, insightResult);

                return {
                    success: true,
                    tasks: taskGroups,
                    insights: insightResult,
                    actions: actions,
                    metadata: {
                        duration: Date.now() - startTime,
                        period: config.period,
                        totalTasks: Object.values(taskGroups).reduce((sum, arr) => sum + arr.length, 0),
                        version: "3.0.0"
                    }
                };
            } catch (error) {
                return {
                    success: false,
                    error: {
                        code: "REVIEW_ERROR",
                        message: error.message || error.toString(),
                        details: { config: config }
                    },
                    metadata: {
                        duration: Date.now() - startTime,
                        version: "3.0.0"
                    }
                };
            }
        };

        /**
         * Detect specific patterns in task data
         *
         * MCP Tool Contract:
         * @param {Object} config - Pattern detection configuration
         * @param {Array<string>} config.patterns - Patterns to detect:
         *   "stalled", "over-committed", "aging-waiting", "inbox-overflow", "tagless", "flag-overuse"
         * @param {Object} config.threshold - Custom thresholds for detection
         * @returns {Promise<Object>} Detection result
         * @returns {boolean} .success - Operation success status
         * @returns {Array} .detected - Detected patterns with details
         * @returns {Object} .summary - Detection summary
         * @returns {Object} .metadata - Request metadata
         */
        lib.detectPatterns = async function(config) {
            const startTime = Date.now();

            try {
                const insights = this.plugIn.library("insightPatterns");

                // Map pattern names to library functions
                const patternMap = {
                    "stalled": "stalledProjects",
                    "over-committed": "overdueAccumulation",
                    "aging-waiting": "waitingForAging",
                    "inbox-overflow": "inboxOverflow",
                    "tagless": "taglessTasksPattern",
                    "repeated": "repeatedTaskPatterns",
                    "flag-overuse": "flagOveruse"
                };

                // Map requested patterns
                const libraryPatterns = (config.patterns || Object.keys(patternMap)).map(
                    p => patternMap[p] || p
                );

                // Run detection
                const result = insights.generateInsights({
                    patterns: libraryPatterns
                });

                return {
                    success: true,
                    detected: result.insights,
                    summary: result.summary,
                    metadata: {
                        duration: Date.now() - startTime,
                        patternsRequested: config.patterns?.length || "all",
                        patternsDetected: result.insights.length,
                        version: "3.0.0"
                    }
                };
            } catch (error) {
                return {
                    success: false,
                    error: {
                        code: "PATTERN_DETECTION_ERROR",
                        message: error.message || error.toString(),
                        details: { config: config }
                    },
                    metadata: {
                        duration: Date.now() - startTime,
                        version: "3.0.0"
                    }
                };
            }
        };

        // ========================================
        // HELPER FUNCTIONS
        // ========================================

        /**
         * Query tasks based on filter configuration
         * @private
         */
        lib.queryTasks = function(queryConfig) {
            const metrics = this.plugIn.library("taskMetrics");
            const filter = queryConfig.filter || "all";

            switch (filter) {
                case "today":
                    return metrics.getTodayTasks();
                case "overdue":
                    return metrics.getOverdueTasks();
                case "upcoming":
                    return metrics.getUpcomingTasks(queryConfig.days || 7);
                case "flagged":
                    return metrics.getFlaggedTasks();
                case "available":
                    return metrics.getAvailableTasks();
                case "tag":
                    return metrics.getTasksByTag(queryConfig.tagName);
                case "project":
                    return metrics.getTasksByProject(queryConfig.projectName);
                default:
                    return metrics.getTodayTasks();
            }
        };

        /**
         * Transform tasks based on transform type
         * @private
         */
        lib.transformTasks = function(tasks, transformType) {
            switch (transformType) {
                case "summary":
                    return tasks.map(t => ({
                        name: t.name,
                        project: t.project,
                        due: t.dueDate
                    }));
                case "detailed":
                    return tasks;
                case "custom":
                    // Allow custom transforms in future
                    return tasks;
                default:
                    return tasks;
            }
        };

        /**
         * Generate preview of exported data
         * @private
         */
        lib.generatePreview = function(data, format) {
            const exporter = this.plugIn.library("exportUtils");
            let output;

            switch (format) {
                case "json":
                    output = exporter.toJSON(data);
                    break;
                case "csv":
                    output = exporter.toCSV(data);
                    break;
                case "markdown":
                    output = exporter.toMarkdown(data);
                    break;
                default:
                    output = JSON.stringify(data);
            }

            return output.substring(0, 200) + (output.length > 200 ? "..." : "");
        };

        /**
         * Generate recommendations from insights
         * @private
         */
        lib.generateRecommendations = function(insightResult) {
            const recommendations = [];

            insightResult.categorized.blockers.forEach(insight => {
                recommendations.push({
                    priority: "high",
                    action: insight.recommendation,
                    reason: insight.title
                });
            });

            insightResult.categorized.health.forEach(insight => {
                recommendations.push({
                    priority: "medium",
                    action: insight.recommendation,
                    reason: insight.title
                });
            });

            insightResult.categorized.opportunities.forEach(insight => {
                recommendations.push({
                    priority: "low",
                    action: insight.recommendation,
                    reason: insight.title
                });
            });

            return recommendations;
        };

        /**
         * Generate period-specific review actions
         * @private
         */
        lib.generateReviewActions = function(period, taskGroups, insightResult) {
            const actions = [];

            // Common actions
            if (taskGroups.overdue.length > 0) {
                actions.push({
                    action: `Reschedule or complete ${taskGroups.overdue.length} overdue tasks`,
                    tasks: taskGroups.overdue.slice(0, 5).map(t => t.name)
                });
            }

            // Period-specific actions
            if (period === "daily") {
                actions.push({
                    action: "Process inbox to zero",
                    reason: "Daily GTD practice"
                });
            } else if (period === "weekly") {
                actions.push({
                    action: "Review all projects for stalled items",
                    reason: "Weekly review best practice"
                });
                actions.push({
                    action: "Clear completed tasks",
                    reason: "Maintain clean workspace"
                });
            } else if (period === "monthly") {
                actions.push({
                    action: "Archive or delete inactive projects",
                    reason: "Monthly maintenance"
                });
                actions.push({
                    action: "Review someday/maybe list",
                    reason: "Monthly GTD review"
                });
            }

            return actions;
        };

        /**
         * Find task by name (helper for batch operations)
         * @private
         */
        lib.findTaskByName = function(name) {
            const tasks = flattenedTasks;
            return tasks.find(t => t.name === name);
        };

        /**
         * Find or create tag (helper for batch operations)
         * @private
         */
        lib.findOrCreateTag = function(tagName) {
            let tag = flattenedTags.find(t => t.name === tagName);

            if (!tag) {
                const app = Application('OmniFocus');
                tag = app.Tag({ name: tagName });
                doc.tags.push(tag);
            }

            return tag;
        };

        /**
         * Placeholder for future Foundation Models integration
         * @private
         */
        lib.callFoundationModel = async function(tasks, prompt, schema) {
            // TODO: When Apple Foundation Models API is available:
            // 1. Format tasks as context for AI
            // 2. Call Foundation Models API with prompt and schema
            // 3. Parse and validate response against schema
            // 4. Return structured analysis

            // For now, throw error indicating this is not yet implemented
            throw new Error("Foundation Models integration not yet available. Using rule-based patterns instead.");
        };

        return lib;
    });

    return patterns;
})();
