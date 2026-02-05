/**
 * AI Hierarchical Analyzer - Omni Automation Plug-In
 *
 * Analyzes the complete OmniFocus hierarchy with configurable depth levels,
 * composable parsers, hierarchical batching for context window management,
 * and comprehensive GTD-aligned insights.
 *
 * Features:
 * - Configurable analysis depth (folders / folders+projects / complete)
 * - Hierarchical batching to respect Foundation Model context windows
 * - GTD-aligned insights: organizational health, flow/bottlenecks, workload, review quality
 * - Markdown report generation and export
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - macOS 15.2+, iOS 18.2+, or later
 * - Apple Silicon or iPhone 15 Pro+ for on-device AI
 */

(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        // Load foundationModelsUtils library first
        const fmUtils = this.plugIn.library("foundationModelsUtils");

        // Check availability IMMEDIATELY before doing anything else
        if (!fmUtils.isAvailable()) {
            fmUtils.showUnavailableAlert();
            return;
        }

        try {
            // Load all required libraries
            const folderParser = this.plugIn.library("folderParser");
            const projectParser = this.plugIn.library("projectParser");
            const taskParser = this.plugIn.library("taskParser");
            const batcher = this.plugIn.library("hierarchicalBatcher");
            const exportUtils = this.plugIn.library("exportUtils");

            // Step 1: Configuration Form
            const configForm = new Form();

            // Depth Level Selection
            const depthField = new Form.Field.Option(
                "depthLevel",
                "Analysis Depth",
                ["folders", "folders-projects", "complete"],
                [
                    "Folders Only (Quick - organizational structure)",
                    "Folders + Projects (Standard - includes flow analysis)",
                    "Complete Hierarchy (Deep - includes task quality)"
                ],
                "folders-projects"  // Default to standard
            );
            configForm.addField(depthField);

            // Folder Selection
            const allFoldersOption = folderParser.getAllFolders();

            // Create a special marker for "All Folders" option
            const ALL_FOLDERS_MARKER = "__ALL_FOLDERS__";

            const folderOptions = [ALL_FOLDERS_MARKER, ...allFoldersOption.map(f => f.folder)];
            const folderNames = ["All Folders", ...allFoldersOption.map(f => f.name)];

            const folderField = new Form.Field.Option(
                "selectedFolder",
                "Starting Folder",
                folderOptions,
                folderNames,
                folderOptions[0]  // Default to "All Folders"
            );
            configForm.addField(folderField);

            // Include Subfolders
            configForm.addField(new Form.Field.Checkbox(
                "includeSubfolders",
                "Include Subfolders Recursively",
                true
            ));

            // Generate Markdown Report
            configForm.addField(new Form.Field.Checkbox(
                "generateMarkdown",
                "Generate Markdown Report",
                true
            ));

            // Export to File
            configForm.addField(new Form.Field.Checkbox(
                "exportToFile",
                "Save Report to File (vs clipboard)",
                false
            ));

            const formResult = await configForm.show("Hierarchical Analysis", "Analyze");

            // Handle form cancellation
            if (!formResult) {
                return;  // User cancelled
            }

            // Extract form values
            const depthLevel = formResult.values["depthLevel"];
            const selectedFolder = formResult.values["selectedFolder"];
            const includeSubfolders = formResult.values["includeSubfolders"];
            const generateMarkdown = formResult.values["generateMarkdown"];
            const exportToFile = formResult.values["exportToFile"];

            // Step 2: Parse Hierarchy to Selected Depth
            let parsedData = { folders: [], projects: [] };

            if (selectedFolder === "__ALL_FOLDERS__") {
                // All folders selected
                const includeProjects = depthLevel === "folders-projects" || depthLevel === "complete";
                parsedData.folders = folderParser.parseAllFolders(includeProjects);
            } else {
                // Specific folder selected
                const includeProjects = depthLevel === "folders-projects" || depthLevel === "complete";
                const parsedFolder = folderParser.parseFolder(
                    selectedFolder,
                    0,
                    includeSubfolders,
                    includeProjects
                );
                parsedData.folders = [parsedFolder];
            }

            // If complete depth, parse tasks for each project
            if (depthLevel === "complete") {
                parsedData.projects = [];

                // Collect all projects from parsed folders
                const collectProjects = (folder) => {
                    if (folder.projects) {
                        folder.projects.forEach(projectSummary => {
                            // Find the actual project object
                            const project = flattenedProjects.find(p =>
                                p.id.primaryKey === projectSummary.id
                            );
                            if (project) {
                                const parsedProject = projectParser.parseProject(project, true);
                                // Parse tasks with taskParser for enhanced analysis
                                if (parsedProject.tasks) {
                                    parsedProject.tasks = parsedProject.tasks.map(task => {
                                        const fullTask = flattenedTasks.find(t =>
                                            t.id.primaryKey === task.id
                                        );
                                        return fullTask ? taskParser.parseTask(fullTask) : task;
                                    });
                                }
                                parsedData.projects.push(parsedProject);
                            }
                        });
                    }
                    if (folder.subfolders) {
                        folder.subfolders.forEach(collectProjects);
                    }
                };

                parsedData.folders.forEach(collectProjects);
            }

            // Step 3: Create Batches
            const batches = batcher.batchByLevel(parsedData, depthLevel);

            if (batches.length === 0) {
                const alert = new Alert(
                    "No Data to Analyze",
                    "The selected scope has no data. Please select a folder with projects or tasks."
                );
                alert.show();
                return;
            }

            // Step 4: Process Batches with AI
            const session = fmUtils.createSession();
            const results = {
                folder: [],
                project: [],
                task: []
            };

            for (const batch of batches) {
                try {
                    const prompt = batcher.generatePromptForBatch(batch);
                    const schema = batcher.getSchemaForLevel(batch.level);
                    const response = await session.respondWithSchema(prompt, schema);
                    const analysis = JSON.parse(response);

                    results[batch.level].push({
                        batch: batch,
                        analysis: analysis
                    });
                } catch (err) {
                    console.error(`Error processing ${batch.level} batch:`, err);
                    // Continue with other batches
                    results[batch.level].push({
                        batch: batch,
                        error: err.message
                    });
                }
            }

            // Step 5: Aggregate Insights
            const aggregatedInsights = aggregateInsights(results, parsedData, depthLevel);

            // Step 6: Generate Report
            const folderNameForReport = selectedFolder === "__ALL_FOLDERS__" ? "All Folders" : selectedFolder.name;
            const report = generateReport(aggregatedInsights, depthLevel, folderNameForReport);

            // Step 7: Display Results
            if (generateMarkdown) {
                if (exportToFile) {
                    // Export to file
                    const folderName = selectedFolder === "__ALL_FOLDERS__" ? "AllFolders" : selectedFolder.name.replace(/[^a-zA-Z0-9]/g, '_');
                    const dateStr = new Date().toISOString().split('T')[0];
                    const filename = `OmniFocus_Hierarchy_${folderName}_${dateStr}.md`;

                    const wrapper = FileWrapper.withContents(filename, Data.fromString(report));
                    const fileSaver = new FileSaver();
                    await fileSaver.show(wrapper);
                } else {
                    // Copy to clipboard
                    Pasteboard.general.string = report;

                    const alert = new Alert(
                        "Analysis Complete",
                        "Markdown report copied to clipboard!"
                    );
                    alert.addOption("OK");
                    alert.show();
                }
            } else {
                // Display in alert
                const alert = new Alert("Hierarchical Analysis", report);
                alert.addOption("Copy to Clipboard");
                alert.addOption("Done");

                const buttonIndex = await alert.show();
                if (buttonIndex === 0) {
                    Pasteboard.general.string = report;
                }
            }

        } catch (err) {
            new Alert(err.name, err.message).show();
            console.error(err);
        }
    });

    // Helper Functions

    /**
     * Aggregate insights from all batch results
     */
    function aggregateInsights(results, parsedData, depthLevel) {
        const insights = {
            timestamp: new Date().toISOString(),
            depthLevel: depthLevel,
            totalFolders: 0,
            totalProjects: 0,
            totalTasks: 0
        };

        // Calculate totals
        if (parsedData.folders) {
            const metrics = this.plugIn.library("folderParser").aggregateMetrics(parsedData.folders);
            insights.totalFolders = metrics.totalFolders;
            insights.totalProjects = metrics.totalProjects;
            insights.totalTasks = metrics.totalTasks;
            insights.overallCompletionRate = metrics.overallCompletionRate;
        }

        // Aggregate folder-level insights
        if (results.folder && results.folder.length > 0) {
            insights.organizationalHealth = aggregateFolderInsights(results.folder);
        }

        // Aggregate project-level insights
        if (results.project && results.project.length > 0) {
            insights.flowAndBottlenecks = aggregateProjectInsights(results.project);
        }

        // Aggregate task-level insights
        if (results.task && results.task.length > 0) {
            insights.workloadDistribution = aggregateTaskInsights(results.task);
        }

        // Calculate GTD alignment score
        insights.gtdAlignmentScore = calculateGTDScore(insights);

        return insights;
    }

    /**
     * Aggregate folder-level insights from multiple batches
     */
    function aggregateFolderInsights(folderResults) {
        const allStrengths = [];
        const allWeaknesses = [];
        const allFolderInsights = [];
        const allRecommendations = [];
        let avgScore = 0;

        folderResults.forEach(result => {
            if (result.error) return;

            const analysis = result.analysis;
            avgScore += analysis.organizationalHealth.score || 0;

            if (analysis.organizationalHealth.strengths) {
                allStrengths.push(...analysis.organizationalHealth.strengths);
            }
            if (analysis.organizationalHealth.weaknesses) {
                allWeaknesses.push(...analysis.organizationalHealth.weaknesses);
            }
            if (analysis.folderInsights) {
                allFolderInsights.push(...analysis.folderInsights);
            }
            if (analysis.recommendations) {
                allRecommendations.push(...analysis.recommendations);
            }
        });

        avgScore = folderResults.length > 0 ? avgScore / folderResults.length : 0;

        return {
            score: Math.round(avgScore * 10) / 10,
            strengths: [...new Set(allStrengths)],  // Remove duplicates
            weaknesses: [...new Set(allWeaknesses)],
            folderInsights: allFolderInsights,
            recommendations: [...new Set(allRecommendations)]
        };
    }

    /**
     * Aggregate project-level insights from multiple batches
     */
    function aggregateProjectInsights(projectResults) {
        let totalHealthy = 0;
        let totalStalled = 0;
        const allBottlenecks = [];
        const allPriorityProjects = [];

        projectResults.forEach(result => {
            if (result.error) return;

            const analysis = result.analysis;
            totalHealthy += analysis.flowAnalysis.healthyFlowCount || 0;
            totalStalled += analysis.flowAnalysis.stalledCount || 0;

            if (analysis.bottlenecks) {
                allBottlenecks.push(...analysis.bottlenecks);
            }
            if (analysis.priorityProjects) {
                allPriorityProjects.push(...analysis.priorityProjects);
            }
        });

        return {
            healthyProjects: totalHealthy,
            stalledProjects: totalStalled,
            bottlenecks: allBottlenecks,
            priorityProjects: allPriorityProjects
        };
    }

    /**
     * Aggregate task-level insights from multiple batches
     */
    function aggregateTaskInsights(taskResults) {
        let totalOverloaded = 0;
        let totalManageable = 0;
        const allQualityIssues = [];
        const allNextActions = [];

        taskResults.forEach(result => {
            if (result.error) return;

            const analysis = result.analysis;
            if (analysis.workloadAssessment.isOverloaded) {
                totalOverloaded++;
            } else {
                totalManageable++;
            }

            if (analysis.taskQualityIssues) {
                allQualityIssues.push(...analysis.taskQualityIssues);
            }
            if (analysis.nextActionRecommendations) {
                allNextActions.push(...analysis.nextActionRecommendations);
            }
        });

        return {
            overloadedProjects: totalOverloaded,
            manageableProjects: totalManageable,
            taskQualityIssues: allQualityIssues,
            nextActionRecommendations: allNextActions
        };
    }

    /**
     * Calculate overall GTD alignment score
     */
    function calculateGTDScore(insights) {
        let score = 0;
        let factors = 0;

        // Factor 1: Organizational health
        if (insights.organizationalHealth) {
            score += insights.organizationalHealth.score;
            factors++;
        }

        // Factor 2: Project flow (healthy vs stalled ratio)
        if (insights.flowAndBottlenecks) {
            const total = insights.flowAndBottlenecks.healthyProjects + insights.flowAndBottlenecks.stalledProjects;
            if (total > 0) {
                const flowScore = (insights.flowAndBottlenecks.healthyProjects / total) * 10;
                score += flowScore;
                factors++;
            }
        }

        // Factor 3: Workload balance
        if (insights.workloadDistribution) {
            const total = insights.workloadDistribution.overloadedProjects + insights.workloadDistribution.manageableProjects;
            if (total > 0) {
                const workloadScore = (insights.workloadDistribution.manageableProjects / total) * 10;
                score += workloadScore;
                factors++;
            }
        }

        return factors > 0 ? Math.round((score / factors) * 10) / 10 : 0;
    }

    /**
     * Generate Markdown report from aggregated insights
     */
    function generateReport(insights, depthLevel, folderName) {
        const lines = [];

        // Header
        lines.push("# OmniFocus Hierarchical Analysis Report");
        lines.push("");
        lines.push(`**Generated:** ${new Date().toLocaleString()}`);
        lines.push(`**Scope:** ${folderName}`);
        lines.push(`**Depth:** ${depthLevel}`);
        lines.push("");
        lines.push("---");
        lines.push("");

        // Executive Summary
        lines.push("## Executive Summary");
        lines.push("");
        lines.push(`**Overall GTD Alignment Score:** ${insights.gtdAlignmentScore}/10`);
        lines.push("");
        lines.push(`**Scope:**`);
        lines.push(`- Total Folders: ${insights.totalFolders}`);
        lines.push(`- Total Projects: ${insights.totalProjects}`);
        if (depthLevel === "complete") {
            lines.push(`- Total Tasks: ${insights.totalTasks}`);
        }
        if (insights.overallCompletionRate !== undefined) {
            lines.push(`- Overall Completion Rate: ${insights.overallCompletionRate}%`);
        }
        lines.push("");

        // Key Findings
        lines.push(`**Key Findings:**`);
        if (insights.organizationalHealth) {
            lines.push(`- Organizational Health: ${insights.organizationalHealth.score}/10`);
        }
        if (insights.flowAndBottlenecks) {
            lines.push(`- Stalled Projects: ${insights.flowAndBottlenecks.stalledProjects}`);
            lines.push(`- Healthy Projects: ${insights.flowAndBottlenecks.healthyProjects}`);
        }
        if (insights.workloadDistribution) {
            lines.push(`- Overloaded Projects: ${insights.workloadDistribution.overloadedProjects}`);
        }
        lines.push("");
        lines.push("---");
        lines.push("");

        // 1. Organizational Health (Folders)
        if (insights.organizationalHealth) {
            lines.push("## 1. Organizational Health (Folders)");
            lines.push("");
            lines.push(`**Score:** ${insights.organizationalHealth.score}/10`);
            lines.push("");

            if (insights.organizationalHealth.strengths.length > 0) {
                lines.push("**Strengths:**");
                insights.organizationalHealth.strengths.forEach(s => {
                    lines.push(`- ✅ ${s}`);
                });
                lines.push("");
            }

            if (insights.organizationalHealth.weaknesses.length > 0) {
                lines.push("**Concerns:**");
                insights.organizationalHealth.weaknesses.forEach(w => {
                    lines.push(`- ⚠️ ${w}`);
                });
                lines.push("");
            }

            if (insights.organizationalHealth.recommendations.length > 0) {
                lines.push("**Recommendations:**");
                insights.organizationalHealth.recommendations.forEach((r, i) => {
                    lines.push(`${i + 1}. ${r}`);
                });
                lines.push("");
            }

            lines.push("---");
            lines.push("");
        }

        // 2. Flow & Bottlenecks (Projects)
        if (insights.flowAndBottlenecks) {
            lines.push("## 2. Flow & Bottlenecks (Projects)");
            lines.push("");
            lines.push(`**Healthy Projects:** ${insights.flowAndBottlenecks.healthyProjects}`);
            lines.push(`**Stalled Projects:** ${insights.flowAndBottlenecks.stalledProjects}`);
            lines.push("");

            if (insights.flowAndBottlenecks.bottlenecks.length > 0) {
                lines.push("### Bottlenecks Detected:");
                lines.push("");
                insights.flowAndBottlenecks.bottlenecks.forEach((b, i) => {
                    lines.push(`**${i + 1}. ${b.projectName}** (ID: ${b.projectId})`);
                    lines.push(`- Issue: ${b.issue}`);
                    if (b.daysStalled) {
                        lines.push(`- Days Stalled: ${b.daysStalled}`);
                    }
                    lines.push(`- Recommendation: ${b.recommendation}`);
                    lines.push("");
                });
            }

            if (insights.flowAndBottlenecks.priorityProjects.length > 0) {
                lines.push("### Priority Projects:");
                lines.push("");
                insights.flowAndBottlenecks.priorityProjects.forEach((p, i) => {
                    const urgencyEmoji = p.urgency === "High" ? "🔴" : p.urgency === "Medium" ? "🟡" : "🟢";
                    lines.push(`**${i + 1}. ${p.projectName}** ${urgencyEmoji} ${p.urgency} Urgency`);
                    lines.push(`- ${p.reason}`);
                    lines.push("");
                });
            }

            lines.push("---");
            lines.push("");
        }

        // 3. Workload Distribution (Tasks)
        if (insights.workloadDistribution) {
            lines.push("## 3. Workload Distribution (Tasks)");
            lines.push("");
            lines.push(`**Overloaded Projects:** ${insights.workloadDistribution.overloadedProjects}`);
            lines.push(`**Manageable Projects:** ${insights.workloadDistribution.manageableProjects}`);
            lines.push("");

            if (insights.workloadDistribution.taskQualityIssues.length > 0) {
                lines.push("### Task Quality Issues:");
                lines.push("");
                const issueCount = Math.min(10, insights.workloadDistribution.taskQualityIssues.length);
                for (let i = 0; i < issueCount; i++) {
                    const issue = insights.workloadDistribution.taskQualityIssues[i];
                    lines.push(`**${i + 1}. "${issue.taskName}"**`);
                    lines.push(`- Issue: ${issue.issue}`);
                    lines.push(`- Improvement: ${issue.improvement}`);
                    lines.push("");
                }
                if (insights.workloadDistribution.taskQualityIssues.length > 10) {
                    lines.push(`_...and ${insights.workloadDistribution.taskQualityIssues.length - 10} more issues_`);
                    lines.push("");
                }
            }

            if (insights.workloadDistribution.nextActionRecommendations.length > 0) {
                lines.push("### Recommended Next Actions:");
                lines.push("");
                const actionCount = Math.min(5, insights.workloadDistribution.nextActionRecommendations.length);
                for (let i = 0; i < actionCount; i++) {
                    const action = insights.workloadDistribution.nextActionRecommendations[i];
                    lines.push(`**${i + 1}. ${action.suggestedNextAction}**`);
                    lines.push(`- ${action.reasoning}`);
                    lines.push("");
                }
            }

            lines.push("---");
            lines.push("");
        }

        // Footer
        lines.push("---");
        lines.push("");
        lines.push("_Generated by AITaskAnalyzer v3.2.0_");
        lines.push("");
        lines.push("_Powered by Apple Foundation Models (on-device AI)_");

        return lines.join("\n");
    }

    // Validation
    action.validate = function(selection, sender) {
        return Device.current.operatingSystemVersion.atLeast(new Version('26'));
    };

    return action;
})();
