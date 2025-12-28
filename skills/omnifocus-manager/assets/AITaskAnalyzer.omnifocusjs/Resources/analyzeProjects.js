/**
 * AI Project Analyzer - Omni Automation Plug-In
 *
 * Analyzes selected folders and projects recursively using Apple Foundation Models
 * to provide intelligent insights about project structure, health, and recommendations.
 *
 * Features:
 * - Recursive folder analysis maintaining hierarchy
 * - Recognition of Folders, Projects, Project Types, Tasks, Tags
 * - Optional tagging of projects needing more exposition
 * - Optional Markdown report generation
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - macOS 15.2+, iOS 18.2+, or later
 * - Apple Silicon or iPhone 15 Pro+ for on-device AI
 */

(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        try {
            const doc = Document.defaultDocument;

            // Step 1: Folder Selection Form
            const selectionForm = new Form();
            selectionForm.addField(new Form.Field.String(
                "scope",
                "Project Scope",
                "What time frame or focus area? (e.g., 'This quarter', 'Work projects', 'All active')"
            ));

            const folderOptions = getAllFolders(doc);
            const folderField = new Form.Field.Option(
                "selectedFolder",
                "Select Folder to Analyze",
                folderOptions,
                folderOptions.map(f => f.name),
                folderOptions[0]
            );
            selectionForm.addField(folderField);

            selectionForm.addField(new Form.Field.Checkbox(
                "includeSubfolders",
                "Include Subfolders Recursively",
                true
            ));

            selectionForm.addField(new Form.Field.Checkbox(
                "tagProjects",
                "Tag projects needing exposition (adds 'needs-exposition' tag)",
                false
            ));

            selectionForm.addField(new Form.Field.Checkbox(
                "generateMarkdown",
                "Generate Markdown Report",
                true
            ));

            const formPrompt = new Form.Field.String(
                "customPrompt",
                "Custom Analysis Focus (optional)",
                "Leave blank for standard analysis"
            );
            selectionForm.addField(formPrompt);

            const formResult = await selectionForm.show("AI Project Analyzer", "Analyze");

            const selectedFolder = formResult.values["selectedFolder"];
            const includeSubfolders = formResult.values["includeSubfolders"];
            const scope = formResult.values["scope"] || "General analysis";
            const shouldTagProjects = formResult.values["tagProjects"];
            const shouldGenerateMarkdown = formResult.values["generateMarkdown"];
            const customPrompt = formResult.values["customPrompt"];

            // Step 2: Recursive Analysis - Gather Project Data
            const analysisData = {
                scope: scope,
                rootFolder: selectedFolder.name,
                timestamp: new Date().toISOString(),
                hierarchy: analyzeHierarchy(selectedFolder, includeSubfolders, 0)
            };

            // Step 3: Calculate Metrics
            const metrics = calculateMetrics(analysisData.hierarchy);
            analysisData.metrics = metrics;

            // Step 4: Prepare for AI Analysis
            const session = new LanguageModel.Session();

            const basePrompt = `You are analyzing an OmniFocus project hierarchy for GTD (Getting Things Done) methodology.

PROJECT SCOPE: ${scope}

ROOT FOLDER: ${analysisData.rootFolder}

HIERARCHY DATA:
${JSON.stringify(analysisData.hierarchy, null, 2)}

CURRENT METRICS:
- Total Folders: ${metrics.totalFolders}
- Total Projects: ${metrics.totalProjects}
- Active Projects: ${metrics.activeProjects}
- On Hold Projects: ${metrics.onHoldProjects}
- Completed Projects: ${metrics.completedProjects}
- Total Tasks: ${metrics.totalTasks}
- Active Tasks: ${metrics.activeTasks}
- Completed Tasks: ${metrics.completedTasks}
- Flagged Tasks: ${metrics.flaggedTasks}
- Overdue Tasks: ${metrics.overdueTasks}
- Unique Tags: ${metrics.uniqueTags.join(", ")}

${customPrompt ? `CUSTOM FOCUS: ${customPrompt}\n` : ""}
Please provide a comprehensive analysis focusing on:
1. **Project Health**: Overall assessment of project structure and progress
2. **Hierarchy Insights**: Evaluation of folder/project organization
3. **Bottlenecks**: Projects or areas that appear stalled or problematic
4. **Priority Recommendations**: Which projects/areas need attention
5. **Projects Needing Exposition**: List projects that lack sufficient detail, context, or next actions (return project IDs for tagging)
6. **Action Items**: Specific next steps to improve project management

Keep analysis actionable and GTD-aligned.`;

            const schema = new LanguageModel.Schema({
                type: "object",
                properties: {
                    projectHealth: {
                        type: "object",
                        properties: {
                            overallScore: {
                                type: "string",
                                description: "One of: Excellent, Good, Fair, Needs Attention"
                            },
                            summary: { type: "string" },
                            strengths: { type: "array", items: { type: "string" } },
                            concerns: { type: "array", items: { type: "string" } }
                        }
                    },
                    hierarchyInsights: {
                        type: "object",
                        properties: {
                            organizationQuality: { type: "string" },
                            suggestions: { type: "array", items: { type: "string" } }
                        }
                    },
                    bottlenecks: {
                        type: "array",
                        items: {
                            type: "object",
                            properties: {
                                projectName: { type: "string" },
                                projectId: { type: "string" },
                                issue: { type: "string" },
                                recommendation: { type: "string" }
                            }
                        }
                    },
                    priorityRecommendations: {
                        type: "array",
                        items: {
                            type: "object",
                            properties: {
                                area: { type: "string" },
                                reason: { type: "string" },
                                urgency: {
                                    type: "string",
                                    description: "One of: High, Medium, Low"
                                }
                            }
                        }
                    },
                    projectsNeedingExposition: {
                        type: "array",
                        items: {
                            type: "object",
                            properties: {
                                projectId: { type: "string" },
                                projectName: { type: "string" },
                                reason: { type: "string" }
                            }
                        }
                    },
                    actionItems: {
                        type: "array",
                        items: { type: "string" }
                    }
                }
            });

            // Step 5: Get AI Analysis
            const response = await session.respondWithSchema(basePrompt, schema);
            const analysis = JSON.parse(response);

            // Step 6: Optional Tagging
            let taggingResults = null;
            if (shouldTagProjects && analysis.projectsNeedingExposition.length > 0) {
                taggingResults = await tagProjectsNeedingExposition(
                    doc,
                    analysis.projectsNeedingExposition
                );
            }

            // Step 7: Generate Report
            const report = formatAnalysisReport(analysisData, metrics, analysis, taggingResults);

            // Step 8: Optional Markdown Export
            if (shouldGenerateMarkdown) {
                await saveMarkdownReport(report, analysisData);
            }

            // Step 9: Display Results
            const resultAlert = new Alert("AI Project Analysis", report.substring(0, 2000) + (report.length > 2000 ? "\n\n[See exported Markdown for full report]" : ""));
            resultAlert.addOption("Done");
            await resultAlert.show();

        } catch (error) {
            console.error("Error:", error);
            const errorAlert = new Alert(
                "Error",
                `Failed to analyze projects: ${error.message}\n\nRequirements:\n• OmniFocus 4.8+\n• macOS 15.2+ or iOS 18.2+\n• Apple Silicon/iPhone 15 Pro+`
            );
            errorAlert.show();
        }
    });

    // Helper Functions

    function getAllFolders(doc) {
        const folders = [];

        // Add root-level folders
        doc.folders.forEach(folder => {
            folders.push(folder);
            collectSubfolders(folder, folders);
        });

        // Add "All Projects" option (null folder)
        folders.unshift({ name: "All Projects (No Folder Filter)", id: "root" });

        return folders;
    }

    function collectSubfolders(folder, collection) {
        folder.folders.forEach(subfolder => {
            collection.push(subfolder);
            collectSubfolders(subfolder, collection);
        });
    }

    function analyzeHierarchy(folder, recursive, depth) {
        const result = {
            type: "folder",
            id: folder.id,
            name: folder.name,
            depth: depth,
            subfolders: [],
            projects: []
        };

        // Handle "All Projects" case
        if (folder.id === "root") {
            const doc = Document.defaultDocument;
            doc.flattenedProjects.forEach(project => {
                result.projects.push(analyzeProject(project, depth + 1));
            });
            return result;
        }

        // Analyze projects in this folder
        folder.projects.forEach(project => {
            result.projects.push(analyzeProject(project, depth + 1));
        });

        // Recursively analyze subfolders
        if (recursive) {
            folder.folders.forEach(subfolder => {
                result.subfolders.push(analyzeHierarchy(subfolder, recursive, depth + 1));
            });
        }

        return result;
    }

    function analyzeProject(project, depth) {
        const tasks = project.flattenedTasks;
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const projectData = {
            type: "project",
            id: project.id.primaryKey,
            name: project.name,
            depth: depth,
            status: project.status,
            projectType: getProjectType(project),
            completionDate: project.completionDate ? project.completionDate.toISOString() : null,
            dueDate: project.dueDate ? project.dueDate.toISOString() : null,
            deferDate: project.deferDate ? project.deferDate.toISOString() : null,
            note: project.note || "",
            taskStats: {
                total: tasks.length,
                completed: tasks.filter(t => t.completed).length,
                active: tasks.filter(t => !t.completed && !t.dropped).length,
                flagged: tasks.filter(t => t.flagged).length,
                overdue: tasks.filter(t => {
                    return !t.completed && t.dueDate && t.dueDate < today;
                }).length,
                noNextAction: tasks.filter(t => !t.completed && !t.dropped).length === 0 && !project.completed
            },
            tags: project.tags.map(tag => tag.name),
            estimatedMinutes: project.estimatedMinutes,
            hasNote: project.note && project.note.length > 0
        };

        return projectData;
    }

    function getProjectType(project) {
        // Determine if Sequential, Parallel, or Single Actions
        if (project.sequential) {
            return "Sequential";
        } else {
            return "Parallel";
        }
    }

    function calculateMetrics(hierarchy) {
        const metrics = {
            totalFolders: 0,
            totalProjects: 0,
            activeProjects: 0,
            onHoldProjects: 0,
            completedProjects: 0,
            droppedProjects: 0,
            totalTasks: 0,
            activeTasks: 0,
            completedTasks: 0,
            flaggedTasks: 0,
            overdueTasks: 0,
            projectsWithoutNextAction: 0,
            projectsWithoutNotes: 0,
            uniqueTags: new Set(),
            projectTypes: {
                sequential: 0,
                parallel: 0
            }
        };

        function traverse(node) {
            if (node.type === "folder") {
                metrics.totalFolders++;
                node.projects.forEach(traverse);
                node.subfolders.forEach(traverse);
            } else if (node.type === "project") {
                metrics.totalProjects++;

                if (node.status === "active") metrics.activeProjects++;
                else if (node.status === "on-hold") metrics.onHoldProjects++;
                else if (node.status === "done") metrics.completedProjects++;
                else if (node.status === "dropped") metrics.droppedProjects++;

                if (node.projectType === "Sequential") metrics.projectTypes.sequential++;
                else metrics.projectTypes.parallel++;

                metrics.totalTasks += node.taskStats.total;
                metrics.activeTasks += node.taskStats.active;
                metrics.completedTasks += node.taskStats.completed;
                metrics.flaggedTasks += node.taskStats.flagged;
                metrics.overdueTasks += node.taskStats.overdue;

                if (node.taskStats.noNextAction) metrics.projectsWithoutNextAction++;
                if (!node.hasNote) metrics.projectsWithoutNotes++;

                node.tags.forEach(tag => metrics.uniqueTags.add(tag));
            }
        }

        traverse(hierarchy);
        metrics.uniqueTags = Array.from(metrics.uniqueTags).sort();

        return metrics;
    }

    async function tagProjectsNeedingExposition(doc, projectList) {
        const results = {
            tagged: [],
            notFound: [],
            errors: []
        };

        // Get or create "needs-exposition" tag
        let expositionTag = doc.tags.byName("needs-exposition");
        if (!expositionTag) {
            expositionTag = new Tag("needs-exposition", doc);
        }

        for (const item of projectList) {
            try {
                // Find project by ID
                const project = doc.flattenedProjects.find(p =>
                    p.id.primaryKey === item.projectId
                );

                if (project) {
                    // Add tag if not already present
                    if (!project.tags.some(t => t.name === "needs-exposition")) {
                        project.addTag(expositionTag);
                        results.tagged.push(item.projectName);
                    } else {
                        results.tagged.push(item.projectName + " (already tagged)");
                    }
                } else {
                    results.notFound.push(item.projectName);
                }
            } catch (error) {
                results.errors.push(`${item.projectName}: ${error.message}`);
            }
        }

        return results;
    }

    function formatAnalysisReport(data, metrics, analysis, taggingResults) {
        let report = `# AI Project Analysis Report\n\n`;
        report += `**Generated:** ${new Date(data.timestamp).toLocaleString()}\n`;
        report += `**Scope:** ${data.scope}\n`;
        report += `**Root Folder:** ${data.rootFolder}\n\n`;

        report += `## 📊 Project Metrics\n\n`;
        report += `**Folders & Projects:**\n`;
        report += `- Total Folders: ${metrics.totalFolders}\n`;
        report += `- Total Projects: ${metrics.totalProjects}\n`;
        report += `  - Active: ${metrics.activeProjects}\n`;
        report += `  - On Hold: ${metrics.onHoldProjects}\n`;
        report += `  - Completed: ${metrics.completedProjects}\n`;
        report += `  - Sequential: ${metrics.projectTypes.sequential}\n`;
        report += `  - Parallel: ${metrics.projectTypes.parallel}\n\n`;

        report += `**Tasks:**\n`;
        report += `- Total Tasks: ${metrics.totalTasks}\n`;
        report += `- Active: ${metrics.activeTasks}\n`;
        report += `- Completed: ${metrics.completedTasks}\n`;
        report += `- Flagged: ${metrics.flaggedTasks}\n`;
        report += `- Overdue: ${metrics.overdueTasks}\n\n`;

        report += `**Health Indicators:**\n`;
        report += `- Projects without next actions: ${metrics.projectsWithoutNextAction}\n`;
        report += `- Projects without notes: ${metrics.projectsWithoutNotes}\n`;
        report += `- Unique tags in use: ${metrics.uniqueTags.length}\n\n`;

        report += `## 🏥 Project Health: ${analysis.projectHealth.overallScore}\n\n`;
        report += `${analysis.projectHealth.summary}\n\n`;

        if (analysis.projectHealth.strengths.length > 0) {
            report += `**Strengths:**\n`;
            analysis.projectHealth.strengths.forEach(s => {
                report += `- ✅ ${s}\n`;
            });
            report += `\n`;
        }

        if (analysis.projectHealth.concerns.length > 0) {
            report += `**Concerns:**\n`;
            analysis.projectHealth.concerns.forEach(c => {
                report += `- ⚠️ ${c}\n`;
            });
            report += `\n`;
        }

        report += `## 🏗️ Hierarchy Insights\n\n`;
        report += `**Organization Quality:** ${analysis.hierarchyInsights.organizationQuality}\n\n`;
        if (analysis.hierarchyInsights.suggestions.length > 0) {
            report += `**Suggestions:**\n`;
            analysis.hierarchyInsights.suggestions.forEach(s => {
                report += `- ${s}\n`;
            });
            report += `\n`;
        }

        if (analysis.bottlenecks.length > 0) {
            report += `## 🚧 Bottlenecks & Issues\n\n`;
            analysis.bottlenecks.forEach((b, i) => {
                report += `${i + 1}. **${b.projectName}**\n`;
                report += `   - Issue: ${b.issue}\n`;
                report += `   - Recommendation: ${b.recommendation}\n\n`;
            });
        }

        report += `## 🎯 Priority Recommendations\n\n`;
        analysis.priorityRecommendations.forEach((rec, i) => {
            const urgencyIcon = rec.urgency === "High" ? "🔴" : rec.urgency === "Medium" ? "🟡" : "🟢";
            report += `${i + 1}. ${urgencyIcon} **${rec.area}**\n`;
            report += `   ${rec.reason}\n\n`;
        });

        if (analysis.projectsNeedingExposition.length > 0) {
            report += `## 📝 Projects Needing More Exposition\n\n`;
            analysis.projectsNeedingExposition.forEach((proj, i) => {
                report += `${i + 1}. **${proj.projectName}**\n`;
                report += `   - Reason: ${proj.reason}\n`;
                if (taggingResults && taggingResults.tagged.includes(proj.projectName)) {
                    report += `   - ✅ Tagged with 'needs-exposition'\n`;
                }
                report += `\n`;
            });

            if (taggingResults) {
                report += `\n**Tagging Results:**\n`;
                report += `- Successfully tagged: ${taggingResults.tagged.length}\n`;
                if (taggingResults.notFound.length > 0) {
                    report += `- Not found: ${taggingResults.notFound.length}\n`;
                }
                if (taggingResults.errors.length > 0) {
                    report += `- Errors: ${taggingResults.errors.length}\n`;
                }
                report += `\n`;
            }
        }

        report += `## ✅ Action Items\n\n`;
        analysis.actionItems.forEach((item, i) => {
            report += `${i + 1}. ${item}\n`;
        });
        report += `\n`;

        return report;
    }

    async function saveMarkdownReport(report, data) {
        const filename = `OmniFocus_Analysis_${data.rootFolder.replace(/[^a-z0-9]/gi, '_')}_${new Date().toISOString().split('T')[0]}.md`;

        const fileSaver = new FileSaver();
        fileSaver.nameLabel = "Save Analysis Report";
        fileSaver.types = [FileType.fromExtension("md")];
        fileSaver.defaultFileName = filename;

        const url = await fileSaver.show();
        if (url) {
            const wrapper = FileWrapper.fromString(url.toString(), report);
            wrapper.write(url);

            const successAlert = new Alert(
                "Report Saved",
                `Analysis report saved to:\n${url.string}`
            );
            successAlert.show();
        }
    }

    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
