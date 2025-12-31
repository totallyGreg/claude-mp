/**
 * Insight Patterns Library for OmniFocus
 *
 * Provides pattern detection functions for analyzing OmniFocus data and generating
 * actionable insights about blockers, health issues, and optimization opportunities.
 *
 * Usage (in OmniFocus plugin):
 *   // In manifest.json, declare as library:
 *   "libraries": ["insightPatterns"]
 *
 *   // In action script:
 *   const patterns = this.plugIn.library("insightPatterns");
 *   const insights = patterns.generateInsights(document);
 *
 * Usage (in Omni Automation console):
 *   // Load library code and evaluate
 *   const patterns = <paste this code>;
 *   const insights = patterns.generateInsights(document);
 */

(() => {
    const insightPatterns = new PlugIn.Library(function() {
        const lib = this;

        /**
         * Detect projects with no available next actions
         * @param {Document} doc - OmniFocus document
         * @returns {Array<Object>} Array of stalled project insights
         */
        lib.detectStalledProjects = function(doc) {
            const insights = [];
            const projects = doc.flattenedProjects.filter(p =>
                p.status === Project.Status.Active
            );

            projects.forEach(project => {
                const tasks = project.tasks;
                if (tasks.length === 0) return; // Skip empty projects

                const availableTasks = tasks.filter(t =>
                    !t.completed &&
                    t.taskStatus === Task.Status.Available
                );

                if (availableTasks.length === 0) {
                    insights.push({
                        category: "BLOCKER",
                        severity: "HIGH",
                        pattern: "Stalled Project",
                        title: `Project '${project.name}' has no next actions`,
                        details: `This project has ${tasks.length} tasks but none are available to work on.`,
                        recommendation: "Add concrete next action, mark tasks as waiting, or put project On Hold",
                        project: project.name
                    });
                }
            });

            return insights;
        };

        /**
         * Detect aging waiting-for items (>30 days)
         * @param {Document} doc - OmniFocus document
         * @returns {Array<Object>} Array of aging waiting insights
         */
        lib.detectWaitingForAging = function(doc) {
            const insights = [];
            const cutoffDate = new Date();
            cutoffDate.setDate(cutoffDate.getDate() - 30); // 30 days ago

            const waitingTasks = doc.flattenedTasks.filter(t => {
                if (t.completed) return false;
                const tags = t.tags;
                return tags.some(tag => tag.name.toLowerCase().includes('waiting'));
            });

            const agingWaiting = waitingTasks.filter(t => {
                const added = t.addedDate;
                return added && added < cutoffDate;
            });

            if (agingWaiting.length > 0) {
                const taskList = agingWaiting.slice(0, 5).map(t => {
                    const daysSince = Math.floor((new Date() - t.addedDate) / (1000 * 60 * 60 * 24));
                    return `  • '${t.name}' (${daysSince} days)`;
                }).join('\n');

                insights.push({
                    category: "BLOCKER",
                    severity: "MEDIUM",
                    pattern: "Aging Waiting Items",
                    title: `${agingWaiting.length} tasks tagged 'Waiting For' are older than 30 days`,
                    details: `Top items:\n${taskList}${agingWaiting.length > 5 ? '\n  ...' : ''}`,
                    recommendation: "Follow up on these items or re-evaluate if still blocked"
                });
            }

            return insights;
        };

        /**
         * Detect projects with excessive overdue tasks (10+)
         * @param {Document} doc - OmniFocus document
         * @returns {Array<Object>} Array of overdue accumulation insights
         */
        lib.detectOverdueAccumulation = function(doc) {
            const insights = [];
            const now = new Date();
            const projects = doc.flattenedProjects.filter(p =>
                p.status === Project.Status.Active
            );

            projects.forEach(project => {
                const overdueTasks = project.tasks.filter(t => {
                    if (t.completed) return false;
                    const due = t.dueDate;
                    return due && due < now;
                });

                if (overdueTasks.length >= 10) {
                    const oldestOverdue = Math.max(...overdueTasks.map(t =>
                        Math.floor((now - t.dueDate) / (1000 * 60 * 60 * 24))
                    ));

                    insights.push({
                        category: "HEALTH",
                        severity: "HIGH",
                        pattern: "Overdue Accumulation",
                        title: `Project '${project.name}' has ${overdueTasks.length} overdue tasks`,
                        details: `Oldest is ${oldestOverdue} days overdue. This suggests unrealistic planning or scope issues.`,
                        recommendation: "Reschedule with realistic dates, drop low-priority tasks, or split into smaller projects",
                        project: project.name
                    });
                }
            });

            return insights;
        };

        /**
         * Detect inbox overflow (>20 items, especially old ones)
         * @param {Document} doc - OmniFocus document
         * @returns {Array<Object>} Array of inbox overflow insights
         */
        lib.detectInboxOverflow = function(doc) {
            const insights = [];
            const inboxTasks = doc.inboxTasks.filter(t => !t.completed);

            if (inboxTasks.length > 20) {
                const cutoffDate = new Date();
                cutoffDate.setDate(cutoffDate.getDate() - 7);

                const oldItems = inboxTasks.filter(t => {
                    const added = t.addedDate;
                    return added && added < cutoffDate;
                });

                insights.push({
                    category: "HEALTH",
                    severity: "MEDIUM",
                    pattern: "Inbox Overflow",
                    title: `Inbox contains ${inboxTasks.length} unprocessed items`,
                    details: `${oldItems.length} items are older than 7 days. Processing is falling behind capture.`,
                    recommendation: "Schedule 15-30 minutes to process inbox to zero. Review each item and move to projects or delete."
                });
            }

            return insights;
        };

        /**
         * Detect high percentage of tasks without tags
         * @param {Document} doc - OmniFocus document
         * @returns {Array<Object>} Array of tagless task insights
         */
        lib.detectTaglessTasksPattern = function(doc) {
            const insights = [];
            const activeTasks = doc.flattenedTasks.filter(t => {
                if (t.completed) return false;
                const project = t.containingProject;
                return !project || project.status === Project.Status.Active;
            });

            const taglessTasks = activeTasks.filter(t => t.tags.length === 0);

            if (taglessTasks.length >= 15) {
                const percentage = Math.round((taglessTasks.length / activeTasks.length) * 100);

                insights.push({
                    category: "HEALTH",
                    severity: "LOW",
                    pattern: "Missing Context Tags",
                    title: `${taglessTasks.length} tasks (${percentage}%) have no tags`,
                    details: "Tasks without tags can't be filtered by context (@home, @office, @phone, etc.)",
                    recommendation: "Add context tags to enable filtering. Consider creating 'Next Actions by Context' perspective."
                });
            }

            return insights;
        };

        /**
         * Detect repeated task patterns that could become templates
         * @param {Document} doc - OmniFocus document
         * @returns {Array<Object>} Array of repeated pattern insights
         */
        lib.detectRepeatedTaskPatterns = function(doc) {
            const insights = [];
            const completedTasks = doc.flattenedTasks.filter(t => t.completed);

            // Group tasks by similar names (simple pattern matching)
            const taskNameCounts = {};
            completedTasks.forEach(t => {
                const name = t.name.toLowerCase();
                // Extract potential pattern (first 3-4 words)
                const words = name.split(' ').slice(0, 3).join(' ');
                if (words.length > 5) { // Avoid very short patterns
                    taskNameCounts[words] = (taskNameCounts[words] || 0) + 1;
                }
            });

            // Find patterns that repeat
            Object.keys(taskNameCounts).forEach(pattern => {
                if (taskNameCounts[pattern] >= 5) {
                    insights.push({
                        category: "OPPORTUNITY",
                        severity: "LOW",
                        pattern: "Repeated Manual Tasks",
                        title: `Pattern detected: '${pattern}...' created ${taskNameCounts[pattern]} times`,
                        details: "Creating similar tasks repeatedly suggests template opportunity.",
                        recommendation: "Consider creating a task template plugin or repeating task for this pattern."
                    });
                }
            });

            return insights;
        };

        /**
         * Detect flag overuse or underuse
         * @param {Document} doc - OmniFocus document
         * @returns {Array<Object>} Array of flag usage insights
         */
        lib.detectFlagOveruse = function(doc) {
            const insights = [];
            const activeTasks = doc.flattenedTasks.filter(t => !t.completed);
            const flaggedTasks = activeTasks.filter(t => t.flagged);

            if (activeTasks.length > 0) {
                const flaggedPercentage = (flaggedTasks.length / activeTasks.length) * 100;

                if (flaggedPercentage > 30) {
                    insights.push({
                        category: "OPPORTUNITY",
                        severity: "LOW",
                        pattern: "Flag Overuse",
                        title: `${flaggedTasks.length} of ${activeTasks.length} tasks (${Math.round(flaggedPercentage)}%) are flagged`,
                        details: "When most tasks are flagged, flags lose their meaning as priority indicators.",
                        recommendation: "Flag <10% of tasks for true priorities only. Unflag completed or non-critical items."
                    });
                } else if (flaggedPercentage < 5 && activeTasks.length > 20) {
                    insights.push({
                        category: "OPPORTUNITY",
                        severity: "LOW",
                        pattern: "Flag Underuse",
                        title: `Only ${flaggedTasks.length} of ${activeTasks.length} tasks are flagged`,
                        details: "Flags help highlight top priorities for quick access.",
                        recommendation: "Consider flagging 5-10% of tasks that are most important or time-sensitive."
                    });
                }
            }

            return insights;
        };

        /**
         * Run all pattern detections and generate comprehensive insights
         * @param {Document} doc - OmniFocus document
         * @param {Object} options - Options object
         * @param {Array<string>} options.patterns - Array of pattern names to run (optional, defaults to all)
         * @returns {Object} Structured insights object with categories and summary
         */
        lib.generateInsights = function(doc, options = {}) {
            const allInsights = [];

            // Determine which patterns to run
            const patternsToRun = options.patterns || [
                'stalledProjects',
                'waitingForAging',
                'overdueAccumulation',
                'inboxOverflow',
                'taglessTasksPattern',
                'repeatedTaskPatterns',
                'flagOveruse'
            ];

            // Run requested patterns
            if (patternsToRun.includes('stalledProjects')) {
                allInsights.push(...this.detectStalledProjects(doc));
            }
            if (patternsToRun.includes('waitingForAging')) {
                allInsights.push(...this.detectWaitingForAging(doc));
            }
            if (patternsToRun.includes('overdueAccumulation')) {
                allInsights.push(...this.detectOverdueAccumulation(doc));
            }
            if (patternsToRun.includes('inboxOverflow')) {
                allInsights.push(...this.detectInboxOverflow(doc));
            }
            if (patternsToRun.includes('taglessTasksPattern')) {
                allInsights.push(...this.detectTaglessTasksPattern(doc));
            }
            if (patternsToRun.includes('repeatedTaskPatterns')) {
                allInsights.push(...this.detectRepeatedTaskPatterns(doc));
            }
            if (patternsToRun.includes('flagOveruse')) {
                allInsights.push(...this.detectFlagOveruse(doc));
            }

            // Group by category
            const blockers = allInsights.filter(i => i.category === "BLOCKER");
            const health = allInsights.filter(i => i.category === "HEALTH");
            const opportunities = allInsights.filter(i => i.category === "OPPORTUNITY");

            // Calculate health score
            const totalIssues = blockers.length + health.length;
            const healthScore = Math.max(0, 10 - totalIssues);

            return {
                success: true,
                insights: allInsights,
                summary: {
                    total: allInsights.length,
                    blockers: blockers.length,
                    health: health.length,
                    opportunities: opportunities.length,
                    healthScore: healthScore
                },
                categorized: {
                    blockers: blockers,
                    health: health,
                    opportunities: opportunities
                }
            };
        };

        /**
         * Format insights into a readable text report
         * @param {Object} insightsResult - Result from generateInsights()
         * @returns {string} Formatted text report
         */
        lib.formatReport = function(insightsResult) {
            if (insightsResult.summary.total === 0) {
                return "✅ No significant issues detected!\n\nYour OmniFocus system looks healthy.";
            }

            const { blockers, health, opportunities } = insightsResult.categorized;
            let report = "========================================\n";
            report += "OmniFocus Insight Report\n";
            report += "========================================\n\n";

            if (blockers.length > 0) {
                report += `BLOCKERS (${blockers.length}):\n`;
                report += "─────────────────────────\n";
                blockers.forEach(i => {
                    report += `\n⚠️  ${i.title}\n`;
                    report += `    ${i.details}\n`;
                    report += `    → ${i.recommendation}\n`;
                });
                report += "\n";
            }

            if (health.length > 0) {
                report += `HEALTH ISSUES (${health.length}):\n`;
                report += "─────────────────────────\n";
                health.forEach(i => {
                    report += `\n⚠️  ${i.title}\n`;
                    report += `    ${i.details}\n`;
                    report += `    → ${i.recommendation}\n`;
                });
                report += "\n";
            }

            if (opportunities.length > 0) {
                report += `OPTIMIZATION OPPORTUNITIES (${opportunities.length}):\n`;
                report += "─────────────────────────────────────\n";
                opportunities.forEach(i => {
                    report += `\n💡 ${i.title}\n`;
                    report += `    ${i.details}\n`;
                    report += `    → ${i.recommendation}\n`;
                });
                report += "\n";
            }

            report += "========================================\n";
            report += `Overall Health: ${insightsResult.summary.healthScore}/10\n`;

            if (blockers.length > 0) {
                report += "Next Steps: Address blockers first\n";
            } else if (health.length > 0) {
                report += "Next Steps: Resolve health issues\n";
            } else {
                report += "Next Steps: Consider optimization opportunities\n";
            }

            report += "========================================\n";

            return report;
        };

        return lib;
    });

    return insightPatterns;
})();
