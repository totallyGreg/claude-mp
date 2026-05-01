/**
 * Hierarchical Batcher Library for OmniFocus
 *
 * Context window management and batch creation for hierarchical AI analysis.
 * Creates level-appropriate batches with prompts and schemas for Foundation Models.
 *
 * Usage (in OmniFocus plugin):
 *   const batcher = this.plugIn.library("hierarchicalBatcher");
 *   const batches = batcher.batchByLevel(parsedData, "folders-projects");
 *
 * @version 1.0.0
 */

(() => {
    var lib = new PlugIn.Library(new Version("1.0"));

    // Constants for batch sizing
    const MAX_FOLDER_BATCH_CHARS = 20000;   // ~5000 tokens
    const MAX_PROJECT_BATCH_CHARS = 18000;  // ~4500 tokens
    const MAX_TASKS_PER_PROJECT = 15;        // Limit tasks to avoid overwhelming analysis

    /**
     * Create batches based on parsed data and depth level
     * Main entry point for batching
     * @param {Object} parsedData - Parsed hierarchy data
     * @param {string} depthLevel - "folders" | "folders-projects" | "complete"
     * @returns {Array} Array of batch objects with level, data, prompt, and schema
     */
    lib.batchByLevel = function(parsedData, depthLevel) {
        const batches = [];

        // Always include folder-level analysis
        const folderBatches = this.batchFoldersForAnalysis(parsedData.folders || []);
        batches.push(...folderBatches);

        // Include project-level if requested
        if (depthLevel === "folders-projects" || depthLevel === "complete") {
            const projectBatches = this.batchProjectsForAnalysis(parsedData.folders || []);
            batches.push(...projectBatches);
        }

        // Include task-level if complete analysis requested
        if (depthLevel === "complete") {
            const taskBatches = this.batchTasksForAnalysis(parsedData.projects || []);
            batches.push(...taskBatches);
        }

        return batches;
    };

    /**
     * Create batches for folder-level analysis
     * Batches folder aggregate metrics to stay within context window
     * @param {Array} parsedFolders - Array of parsed folder objects
     * @returns {Array} Array of folder batch objects
     */
    lib.batchFoldersForAnalysis = function(parsedFolders) {
        if (!parsedFolders || parsedFolders.length === 0) {
            return [];
        }

        const batches = [];
        let currentBatch = [];
        let currentSize = 0;

        parsedFolders.forEach(folder => {
            // Create folder summary (metrics only, no full hierarchy)
            const folderSummary = {
                name: folder.name,
                depth: folder.depth,
                health: folder.health,
                metrics: folder.metrics,
                subfolderCount: folder.subfolders ? folder.subfolders.length : 0,
                projectCount: folder.projects ? folder.projects.length : 0
            };

            const summarySize = JSON.stringify(folderSummary).length;

            // Check if adding this would exceed limit
            if (currentSize + summarySize > MAX_FOLDER_BATCH_CHARS && currentBatch.length > 0) {
                batches.push({
                    level: "folder",
                    folders: currentBatch,
                    batchNumber: batches.length + 1
                });
                currentBatch = [];
                currentSize = 0;
            }

            currentBatch.push(folderSummary);
            currentSize += summarySize;
        });

        // Add remaining batch
        if (currentBatch.length > 0) {
            batches.push({
                level: "folder",
                folders: currentBatch,
                batchNumber: batches.length + 1
            });
        }

        return batches;
    };

    /**
     * Create batches for project-level analysis
     * Creates one batch per folder to maintain context
     * @param {Array} parsedFolders - Array of parsed folder objects with projects
     * @returns {Array} Array of project batch objects
     */
    lib.batchProjectsForAnalysis = function(parsedFolders) {
        if (!parsedFolders || parsedFolders.length === 0) {
            return [];
        }

        const batches = [];

        // Process each folder separately to maintain context
        parsedFolders.forEach(folder => {
            if (!folder.projects || folder.projects.length === 0) {
                return;  // Skip folders with no projects
            }

            // If folder has many projects, split into multiple batches
            let currentBatch = [];
            let currentSize = 0;

            folder.projects.forEach(project => {
                const projectSummary = {
                    id: project.id,
                    name: project.name,
                    status: project.status,
                    type: project.type,
                    metrics: project.metrics,
                    gtdHealth: project.gtdHealth,
                    taskCount: project.taskCount || 0
                };

                const summarySize = JSON.stringify(projectSummary).length;

                // Check if we need to start a new batch
                if (currentSize + summarySize > MAX_PROJECT_BATCH_CHARS && currentBatch.length > 0) {
                    batches.push({
                        level: "project",
                        folderName: folder.name,
                        folderHealth: folder.health,
                        projects: currentBatch,
                        batchNumber: batches.length + 1
                    });
                    currentBatch = [];
                    currentSize = 0;
                }

                currentBatch.push(projectSummary);
                currentSize += summarySize;
            });

            // Add remaining projects for this folder
            if (currentBatch.length > 0) {
                batches.push({
                    level: "project",
                    folderName: folder.name,
                    folderHealth: folder.health,
                    projects: currentBatch,
                    batchNumber: batches.length + 1
                });
            }
        });

        return batches;
    };

    /**
     * Create batches for task-level analysis
     * One batch per project, limited to max tasks
     * @param {Array} parsedProjects - Array of parsed project objects with tasks
     * @returns {Array} Array of task batch objects
     */
    lib.batchTasksForAnalysis = function(parsedProjects) {
        if (!parsedProjects || parsedProjects.length === 0) {
            return [];
        }

        const batches = [];

        parsedProjects.forEach(project => {
            if (!project.tasks || project.tasks.length === 0) {
                return;  // Skip projects with no tasks
            }

            // Limit tasks to prevent overwhelming analysis
            const tasksToAnalyze = project.tasks.slice(0, MAX_TASKS_PER_PROJECT);

            // Create task summaries (limit note length)
            const taskSummaries = tasksToAnalyze.map(task => ({
                id: task.id,
                name: task.name,
                completed: task.completed,
                flagged: task.flagged,
                dueDate: task.dueDate,
                tags: task.tags,
                clarity: task.clarity,
                age: task.age,
                note: task.note ? task.note.substring(0, 200) : null  // Limit note length
            }));

            batches.push({
                level: "task",
                projectId: project.id,
                projectName: project.name,
                projectStatus: project.status,
                totalTasks: project.tasks.length,
                analyzingTasks: tasksToAnalyze.length,
                tasks: taskSummaries,
                batchNumber: batches.length + 1
            });
        });

        return batches;
    };

    /**
     * Generate GTD-aligned prompt for a batch
     * @param {Object} batch - Batch object with level and data
     * @returns {string} Prompt text for Foundation Model
     */
    lib.generatePromptForBatch = function(batch) {
        switch (batch.level) {
            case "folder":
                return this._generateFolderPrompt(batch);
            case "project":
                return this._generateProjectPrompt(batch);
            case "task":
                return this._generateTaskPrompt(batch);
            default:
                throw new Error(`Unknown batch level: ${batch.level}`);
        }
    };

    /**
     * Generate folder-level prompt (private)
     * @private
     */
    lib._generateFolderPrompt = function(batch) {
        const folderData = JSON.stringify(batch.folders, null, 2);

        return `Analyze the organizational structure of this OmniFocus folder hierarchy using GTD (Getting Things Done) principles.

FOLDERS (${batch.folders.length} folders in this batch):
${folderData}

Provide insights on:
1. **Organizational Health** - How well structured is the folder hierarchy? Is it balanced or are some folders overloaded?
2. **Folder-Level Insights** - Which specific folders need attention and why? (health, metrics, balance)
3. **Recommendations** - How to improve the organizational structure based on GTD best practices?

Focus on:
- Folder balance and distribution of work
- Clear separation of concerns
- Appropriate depth (not too flat, not too deep)
- Active vs. completed project ratios
- Areas needing consolidation or reorganization

Keep analysis actionable and specific to the folders shown.`;
    };

    /**
     * Generate project-level prompt (private)
     * @private
     */
    lib._generateProjectPrompt = function(batch) {
        const projectData = JSON.stringify(batch.projects, null, 2);

        return `Analyze the projects in folder "${batch.folderName}" (Folder Health: ${batch.folderHealth}) using GTD flow principles.

PROJECTS (${batch.projects.length} projects in this batch):
${projectData}

Provide insights on:
1. **Flow Analysis** - Which projects are moving well vs. stalled? What's the overall momentum?
2. **Bottlenecks** - Identify specific projects with issues:
   - No available next actions (stalled)
   - Overdue task accumulation (scope creep)
   - Missing context or notes (unclear outcomes)
   - Need review (30+ days since last review)
3. **Priority Projects** - Which projects need immediate attention and why? (urgency assessment)

For bottlenecks, provide:
- Project name and ID
- Specific issue description
- Days stalled (if applicable)
- Concrete recommendation to unblock

Focus on:
- GTD project health indicators
- Next action availability
- Clear completion criteria
- Review cadence
- Momentum and progress patterns

Keep recommendations specific and actionable.`;
    };

    /**
     * Generate task-level prompt (private)
     * @private
     */
    lib._generateTaskPrompt = function(batch) {
        const showingNote = batch.analyzingTasks < batch.totalTasks
            ? ` (showing ${batch.analyzingTasks} of ${batch.totalTasks} tasks)`
            : "";

        const taskData = JSON.stringify(batch.tasks, null, 2);

        return `Analyze the tasks in project "${batch.projectName}" (Status: ${batch.projectStatus}) for workload and quality${showingNote}.

TASKS:
${taskData}

Provide insights on:
1. **Workload Assessment** - Is this project overloaded? What's the task distribution? Is it realistic?
2. **Task Quality Issues** - Identify tasks with clarity problems:
   - Vague or unclear action language
   - Missing context (no tags)
   - Unclear scope or outcome
   - Questions or uncertainty in task names
3. **Next Action Recommendations** - What should be the clear, actionable next steps for this project?

For quality issues, reference specific tasks and suggest improvements.

Focus on:
- GTD next action criteria (clear, concrete, actionable)
- Task clarity and specificity
- Appropriate context tags
- Realistic time estimates
- Workload balance

Keep recommendations practical and specific to the tasks shown.`;
    };

    /**
     * Get LanguageModel.Schema for a batch level
     * @param {string} level - "folder" | "project" | "task"
     * @returns {LanguageModel.Schema} Schema object for structured output
     */
    lib.getSchemaForLevel = function(level) {
        switch (level) {
            case "folder":
                return this._getFolderSchema();
            case "project":
                return this._getProjectSchema();
            case "task":
                return this._getTaskSchema();
            default:
                throw new Error(`Unknown level: ${level}`);
        }
    };

    /**
     * Get folder-level schema (private)
     * @private
     */
    lib._getFolderSchema = function() {
        return LanguageModel.Schema.fromJSON({
            name: "folder-analysis-schema",
            properties: [
                {
                    name: "organizationalHealth",
                    description: "Overall assessment of folder hierarchy organization",
                    schema: {
                        properties: [
                            {
                                name: "score",
                                description: "Organizational quality score from 1-10"
                            },
                            {
                                name: "structure",
                                description: "Assessment of the folder structure (balanced, clear, etc.)"
                            },
                            {
                                name: "strengths",
                                description: "What's working well in the organization",
                                schema: { arrayOf: { constant: "strength" } }
                            },
                            {
                                name: "weaknesses",
                                description: "What needs improvement in the organization",
                                schema: { arrayOf: { constant: "weakness" } }
                            }
                        ]
                    }
                },
                {
                    name: "folderInsights",
                    description: "Specific insights for individual folders",
                    schema: {
                        arrayOf: {
                            properties: [
                                { name: "folderName", description: "Name of the folder" },
                                { name: "health", description: "Excellent, Good, Fair, or Needs Attention" },
                                { name: "concern", description: "Specific issue or observation", isOptional: true }
                            ]
                        }
                    }
                },
                {
                    name: "recommendations",
                    description: "Actionable recommendations for improving folder organization",
                    schema: { arrayOf: { constant: "recommendation" } }
                }
            ]
        });
    };

    /**
     * Get project-level schema (private)
     * @private
     */
    lib._getProjectSchema = function() {
        return LanguageModel.Schema.fromJSON({
            name: "project-analysis-schema",
            properties: [
                {
                    name: "flowAnalysis",
                    description: "Overall project flow and momentum assessment",
                    schema: {
                        properties: [
                            { name: "healthyFlowCount", description: "Number of projects with good momentum" },
                            { name: "stalledCount", description: "Number of stalled projects" },
                            { name: "summary", description: "Brief assessment of overall project flow" }
                        ]
                    }
                },
                {
                    name: "bottlenecks",
                    description: "Projects with specific issues blocking progress",
                    schema: {
                        arrayOf: {
                            properties: [
                                { name: "projectName", description: "Name of the project" },
                                { name: "projectId", description: "Project ID for reference" },
                                { name: "issue", description: "Specific issue: stalled, no next action, overdue accumulation, missing context, etc." },
                                { name: "daysStalled", description: "How many days the project has been stalled", isOptional: true },
                                { name: "recommendation", description: "Specific action to unblock this project" }
                            ]
                        }
                    }
                },
                {
                    name: "priorityProjects",
                    description: "Projects requiring immediate attention",
                    schema: {
                        arrayOf: {
                            properties: [
                                { name: "projectName", description: "Name of the project" },
                                { name: "reason", description: "Why this project needs attention now" },
                                { name: "urgency", description: "High, Medium, or Low urgency level" }
                            ]
                        }
                    }
                }
            ]
        });
    };

    /**
     * Get task-level schema (private)
     * @private
     */
    lib._getTaskSchema = function() {
        return LanguageModel.Schema.fromJSON({
            name: "task-analysis-schema",
            properties: [
                {
                    name: "workloadAssessment",
                    description: "Assessment of task workload in this project",
                    schema: {
                        properties: [
                            { name: "isOverloaded", description: "true if too many tasks, false if manageable" },
                            { name: "totalEstimatedHours", description: "Estimated total hours for all tasks", isOptional: true },
                            { name: "distribution", description: "Description of how tasks are distributed" }
                        ]
                    }
                },
                {
                    name: "taskQualityIssues",
                    description: "Specific tasks with clarity or quality problems",
                    schema: {
                        arrayOf: {
                            properties: [
                                { name: "taskName", description: "Name of the task with issues" },
                                { name: "issue", description: "Specific problem: vague language, missing context, unclear scope, etc." },
                                { name: "improvement", description: "Suggested improvement for this task" }
                            ]
                        }
                    }
                },
                {
                    name: "nextActionRecommendations",
                    description: "Recommended next actions for this project",
                    schema: {
                        arrayOf: {
                            properties: [
                                { name: "suggestedNextAction", description: "Clear, concrete next action" },
                                { name: "reasoning", description: "Why this should be the next action" }
                            ]
                        }
                    }
                }
            ]
        });
    };

    /**
     * Estimate tokens for data (rough approximation)
     * Uses character count / 4 as rough estimate
     * @param {*} data - Data to estimate (will be JSON stringified)
     * @returns {number} Estimated token count
     */
    lib.estimateTokens = function(data) {
        const jsonString = JSON.stringify(data);
        return Math.ceil(jsonString.length / 4);
    };

    return lib;
})();
