/**
 * OmniFocus Insight Analyzer
 *
 * Omni Automation script that analyzes task patterns and generates actionable insights.
 *
 * Usage (macOS Console):
 *   View → Automation → Console (⌃⌥⌘I)
 *   Paste this script and run
 *
 * Usage (as plugin):
 *   Save as .omnifocusjs bundle
 *   Install by double-clicking
 *   Run via Tools → Analyze Insights
 */

(() => {
    const app = Application.currentApplication();
    app.includeStandardAdditions = true;

    const omniFocus = Application('OmniFocus');
    const doc = omniFocus.defaultDocument;

    // Collect all insights
    const insights = [];

    // ========================================
    // BLOCKER PATTERNS
    // ========================================

    function detectStalledProjects() {
        const projects = doc.flattenedProjects().filter(p =>
            p.status() === Project.Status.Active
        );

        projects.forEach(project => {
            const tasks = project.tasks();
            if (tasks.length === 0) return; // Skip empty projects

            const availableTasks = tasks.filter(t =>
                !t.completed() &&
                t.taskStatus() === Task.Status.Available
            );

            if (availableTasks.length === 0) {
                insights.push({
                    category: "BLOCKER",
                    severity: "HIGH",
                    pattern: "Stalled Project",
                    title: `Project '${project.name()}' has no next actions`,
                    details: `This project has ${tasks.length} tasks but none are available to work on.`,
                    recommendation: "Add concrete next action, mark tasks as waiting, or put project On Hold",
                    project: project.name()
                });
            }
        });
    }

    function detectWaitingForAging() {
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - 30); // 30 days ago

        const waitingTasks = doc.flattenedTasks().filter(t => {
            if (t.completed()) return false;
            const tags = t.tags();
            return tags.some(tag => tag.name().toLowerCase().includes('waiting'));
        });

        const agingWaiting = waitingTasks.filter(t => {
            const added = t.addedDate();
            return added && added < cutoffDate;
        });

        if (agingWaiting.length > 0) {
            const taskList = agingWaiting.slice(0, 5).map(t => {
                const daysSince = Math.floor((new Date() - t.addedDate()) / (1000 * 60 * 60 * 24));
                return `  • '${t.name()}' (${daysSince} days)`;
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
    }

    // ========================================
    // HEALTH ISSUE PATTERNS
    // ========================================

    function detectOverdueAccumulation() {
        const now = new Date();
        const projects = doc.flattenedProjects().filter(p =>
            p.status() === Project.Status.Active
        );

        projects.forEach(project => {
            const overdueTasks = project.tasks().filter(t => {
                if (t.completed()) return false;
                const due = t.dueDate();
                return due && due < now;
            });

            if (overdueTasks.length >= 10) {
                const oldestOverdue = Math.max(...overdueTasks.map(t =>
                    Math.floor((now - t.dueDate()) / (1000 * 60 * 60 * 24))
                ));

                insights.push({
                    category: "HEALTH",
                    severity: "HIGH",
                    pattern: "Overdue Accumulation",
                    title: `Project '${project.name()}' has ${overdueTasks.length} overdue tasks`,
                    details: `Oldest is ${oldestOverdue} days overdue. This suggests unrealistic planning or scope issues.`,
                    recommendation: "Reschedule with realistic dates, drop low-priority tasks, or split into smaller projects",
                    project: project.name()
                });
            }
        });
    }

    function detectInboxOverflow() {
        const inboxTasks = doc.inboxTasks().filter(t => !t.completed());

        if (inboxTasks.length > 20) {
            const cutoffDate = new Date();
            cutoffDate.setDate(cutoffDate.getDate() - 7);

            const oldItems = inboxTasks.filter(t => {
                const added = t.addedDate();
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
    }

    function detectTaglessTasksPattern() {
        const activeTasks = doc.flattenedTasks().filter(t => {
            if (t.completed()) return false;
            const project = t.containingProject();
            return !project || project.status() === Project.Status.Active;
        });

        const taglessTasks = activeTasks.filter(t => t.tags().length === 0);

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
    }

    // ========================================
    // OPTIMIZATION OPPORTUNITIES
    // ========================================

    function detectRepeatedTaskPatterns() {
        const completedTasks = doc.flattenedTasks().filter(t => t.completed());

        // Group tasks by similar names (simple pattern matching)
        const taskNameCounts = {};
        completedTasks.forEach(t => {
            const name = t.name().toLowerCase();
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
    }

    function detectFlagOveruse() {
        const activeTasks = doc.flattenedTasks().filter(t => !t.completed());
        const flaggedTasks = activeTasks.filter(t => t.flagged());

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
    }

    // ========================================
    // EXECUTE ANALYSIS
    // ========================================

    detectStalledProjects();
    detectWaitingForAging();
    detectOverdueAccumulation();
    detectInboxOverflow();
    detectTaglessTasksPattern();
    detectRepeatedTaskPatterns();
    detectFlagOveruse();

    // ========================================
    // FORMAT AND PRESENT RESULTS
    // ========================================

    function formatReport() {
        if (insights.length === 0) {
            return "✅ No significant issues detected!\n\nYour OmniFocus system looks healthy.";
        }

        // Group by category
        const blockers = insights.filter(i => i.category === "BLOCKER");
        const health = insights.filter(i => i.category === "HEALTH");
        const opportunities = insights.filter(i => i.category === "OPPORTUNITY");

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

        // Calculate overall health score (simple heuristic)
        const totalIssues = blockers.length + health.length;
        const healthScore = Math.max(0, 10 - totalIssues);
        report += `Overall Health: ${healthScore}/10\n`;

        if (blockers.length > 0) {
            report += "Next Steps: Address blockers first\n";
        } else if (health.length > 0) {
            report += "Next Steps: Resolve health issues\n";
        } else {
            report += "Next Steps: Consider optimization opportunities\n";
        }

        report += "========================================\n";

        return report;
    }

    const report = formatReport();

    // Output report
    console.log(report);

    // Return report for plugin use (can be displayed in alert or saved to file)
    return report;
})();
