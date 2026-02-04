/**
 * System Discovery Library for OmniFocus
 *
 * Auto-discovers the user's unique OmniFocus organizational structure using
 * a hybrid approach: rule-based pattern matching + Apple Foundation Models
 * for semantic understanding.
 *
 * Features:
 * - Folder type inference (area, archive, someday, reference)
 * - Tag categorization (context, person, status, energy, time, area)
 * - Convention detection (prefixes, nesting styles)
 * - GTD health scoring
 * - AI-enhanced semantic analysis
 *
 * Usage (in OmniFocus plugin):
 *   const discovery = this.plugIn.library("systemDiscovery");
 *   const systemMap = discovery.discoverSystem({ depth: "full" });
 *
 * @version 1.0.0
 */

(() => {
    var lib = new PlugIn.Library(new Version("1.0"));

    // ==================== Pattern Constants ====================

    // Context detection patterns
    const CONTEXT_PREFIXES = ["@"];
    const CONTEXT_PATTERNS = [
        "home", "office", "work", "computer", "mac", "phone", "iphone",
        "errands", "online", "anywhere", "calls", "email", "desk"
    ];

    // Person/waiting detection patterns
    const PERSON_PATTERNS = ["waiting", "delegated", "pending", "from:", "to:"];
    const WAITING_PREFIXES = ["waiting:", "w:", "delegate:"];

    // Status tag patterns
    const STATUS_PATTERNS = ["hold", "someday", "maybe", "review", "later", "paused"];

    // Energy/effort patterns
    const ENERGY_PATTERNS = ["high", "medium", "low", "quick", "deep", "focus", "brain-dead"];

    // Time-based patterns
    const TIME_PATTERNS = ["morning", "afternoon", "evening", "weekend", "weekday", "15min", "30min", "1hr"];

    // Folder type patterns
    const ARCHIVE_PATTERNS = ["archive", "archived", "completed", "done", "old", "past", "finished"];
    const SOMEDAY_PATTERNS = ["someday", "maybe", "future", "ideas", "backlog", "wishlist"];
    const REFERENCE_PATTERNS = ["reference", "resources", "templates", "library", "support"];
    const AREA_PATTERNS = ["work", "personal", "home", "health", "finance", "family", "career", "admin"];

    // ==================== Main Discovery Functions ====================

    /**
     * Main entry point - discovers system structure
     * @param {Object} options - { depth: "quick"|"full" }
     * @returns {Object} SystemMap
     */
    lib.discoverSystem = function(options = {}) {
        const depth = options.depth || "quick";

        // Phase 1: Collect raw data
        const rawData = {
            folders: this.collectFolderData(),
            tags: this.collectTagData(),
            projects: this.collectProjectData(),
            tasks: depth === "full" ? this.collectTaskSample() : null
        };

        // Phase 2: Infer patterns (rule-based)
        const inferences = {
            folderTypes: this.inferFolderTypes(rawData.folders),
            tagCategories: this.inferTagCategories(rawData.tags),
            conventions: this.detectConventions(rawData)
        };

        // Phase 3: Calculate GTD health
        const gtdHealth = this.calculateGTDHealth(rawData);

        // Phase 4: Build and return SystemMap
        return this.buildSystemMap(rawData, inferences, gtdHealth, depth);
    };

    /**
     * AI-enhanced discovery using Foundation Models
     * @param {LanguageModel.Session} session
     * @param {Object} systemMap - Basic system map from rule-based discovery
     * @returns {Promise<Object>} AI-enhanced insights
     */
    lib.discoverWithAI = async function(session, systemMap) {
        const schema = this.getDiscoverySchema();
        const prompt = this.buildDiscoveryPrompt(systemMap);

        const response = await session.respondWithSchema(prompt, schema);
        return JSON.parse(response);
    };

    /**
     * Merge AI insights into the system map
     * @param {Object} systemMap - Base system map
     * @param {Object} aiInsights - AI-generated insights
     * @returns {Object} Enhanced system map
     */
    lib.mergeAIInsights = function(systemMap, aiInsights) {
        const enhanced = Object.assign({}, systemMap);
        enhanced.aiEnhanced = true;

        // Merge folder insights
        if (aiInsights.folderInsights && enhanced.structure.topLevelFolders) {
            aiInsights.folderInsights.forEach(insight => {
                const folder = enhanced.structure.topLevelFolders.find(
                    f => f.name === insight.folderName
                );
                if (folder) {
                    folder.aiInferredType = insight.inferredType;
                    folder.aiConfidence = insight.confidence;
                    folder.aiReasoning = insight.reasoning;
                }
            });
        }

        // Merge tag insights
        if (aiInsights.tagInsights && enhanced.tags.categories) {
            aiInsights.tagInsights.forEach(insight => {
                // Find the tag in any category and add AI insights
                for (const category of Object.values(enhanced.tags.categories)) {
                    const tag = category.find(t => t.tag === insight.tagName);
                    if (tag) {
                        tag.aiCategory = insight.inferredCategory;
                        tag.aiMeaning = insight.suggestedMeaning;
                        break;
                    }
                }
            });
        }

        // Add organizational style insights
        if (aiInsights.organizationalStyle) {
            enhanced.organizationalStyle = aiInsights.organizationalStyle;
        }

        // Add AI recommendations
        if (aiInsights.recommendations) {
            enhanced.recommendations = [
                ...(enhanced.recommendations || []),
                ...aiInsights.recommendations
            ];
        }

        return enhanced;
    };

    // ==================== Data Collection ====================

    /**
     * Collect folder structure data
     * @returns {Array} Array of folder data objects
     */
    lib.collectFolderData = function() {
        const allFolders = [];
        const rootFolders = folders || [];

        const processFolder = (folder, depth, parent) => {
            const folderData = {
                id: folder.id.primaryKey,
                name: folder.name,
                depth: depth,
                parentName: parent ? parent.name : null,
                projectCount: folder.projects ? folder.projects.length : 0,
                activeProjectCount: folder.flattenedProjects ?
                    folder.flattenedProjects.filter(p => !p.completed && p.status.name === "active").length : 0,
                subfolderCount: folder.folders ? folder.folders.length : 0
            };

            allFolders.push(folderData);

            // Process subfolders
            if (folder.folders) {
                folder.folders.forEach(subfolder => {
                    processFolder(subfolder, depth + 1, folder);
                });
            }
        };

        rootFolders.forEach(folder => processFolder(folder, 0, null));

        return allFolders;
    };

    /**
     * Collect tag hierarchy data
     * @returns {Array} Array of tag data objects
     */
    lib.collectTagData = function() {
        const allTags = [];
        const rootTags = tags || [];

        const processTag = (tag, depth, parent) => {
            // Count tasks with this tag
            const taggedTasks = flattenedTasks ?
                flattenedTasks.filter(t => t.tags.includes(tag)).length : 0;

            const tagData = {
                id: tag.id.primaryKey,
                name: tag.name,
                depth: depth,
                parentName: parent ? parent.name : null,
                hasChildren: tag.tags && tag.tags.length > 0,
                childCount: tag.tags ? tag.tags.length : 0,
                taskCount: taggedTasks
            };

            allTags.push(tagData);

            // Process child tags
            if (tag.tags) {
                tag.tags.forEach(childTag => {
                    processTag(childTag, depth + 1, tag);
                });
            }
        };

        rootTags.forEach(tag => processTag(tag, 0, null));

        return allTags;
    };

    /**
     * Collect project data for analysis
     * @returns {Object} Project statistics
     */
    lib.collectProjectData = function() {
        const allProjects = flattenedProjects || [];

        const stats = {
            total: allProjects.length,
            active: 0,
            onHold: 0,
            completed: 0,
            dropped: 0,
            sequential: 0,
            parallel: 0,
            singleAction: 0,
            withDueDate: 0,
            withDeferDate: 0,
            overdue: 0,
            stalled: 0
        };

        const now = new Date();

        allProjects.forEach(project => {
            // Status counts
            if (project.completed) {
                stats.completed++;
            } else if (project.status.name === "active") {
                stats.active++;
            } else if (project.status.name === "on hold") {
                stats.onHold++;
            } else if (project.status.name === "dropped") {
                stats.dropped++;
            }

            // Type counts
            if (!project.completed) {
                if (project.sequential) {
                    stats.sequential++;
                } else if (project.containsSingletonActions) {
                    stats.singleAction++;
                } else {
                    stats.parallel++;
                }
            }

            // Date analysis
            if (project.dueDate) {
                stats.withDueDate++;
                if (!project.completed && project.dueDate < now) {
                    stats.overdue++;
                }
            }
            if (project.deferDate) {
                stats.withDeferDate++;
            }

            // Stalled detection (active but no available tasks)
            if (!project.completed && project.status.name === "active") {
                const availableTasks = project.flattenedTasks ?
                    project.flattenedTasks.filter(t => !t.completed && !t.blocked).length : 0;
                if (availableTasks === 0) {
                    stats.stalled++;
                }
            }
        });

        return stats;
    };

    /**
     * Collect sample of tasks for pattern analysis
     * @returns {Object} Task statistics and patterns
     */
    lib.collectTaskSample = function() {
        const allTasks = flattenedTasks || [];
        const activeTasks = allTasks.filter(t => !t.completed && !t.dropped);

        const stats = {
            total: allTasks.length,
            active: activeTasks.length,
            completed: allTasks.filter(t => t.completed).length,
            withDueDate: 0,
            withDeferDate: 0,
            withDuration: 0,
            withTags: 0,
            withNotes: 0,
            overdue: 0,
            flagged: 0,
            inInbox: 0
        };

        const now = new Date();

        activeTasks.forEach(task => {
            if (task.dueDate) {
                stats.withDueDate++;
                if (task.dueDate < now) {
                    stats.overdue++;
                }
            }
            if (task.deferDate) stats.withDeferDate++;
            if (task.estimatedMinutes && task.estimatedMinutes > 0) stats.withDuration++;
            if (task.tags && task.tags.length > 0) stats.withTags++;
            if (task.note && task.note.length > 0) stats.withNotes++;
            if (task.flagged) stats.flagged++;
            if (task.inInbox) stats.inInbox++;
        });

        // Calculate percentages
        const total = activeTasks.length || 1;
        stats.percentWithDueDate = Math.round((stats.withDueDate / total) * 100);
        stats.percentWithDuration = Math.round((stats.withDuration / total) * 100);
        stats.percentWithTags = Math.round((stats.withTags / total) * 100);

        return stats;
    };

    // ==================== Pattern Inference ====================

    /**
     * Infer folder types based on names and structure
     * @param {Array} folderData - Collected folder data
     * @returns {Object} Map of folder names to inferred types
     */
    lib.inferFolderTypes = function(folderData) {
        const types = {};

        folderData.forEach(folder => {
            const name = folder.name.toLowerCase();
            let type = "general";
            let confidence = "medium";

            // Check archive patterns
            if (ARCHIVE_PATTERNS.some(p => name.includes(p))) {
                type = "archive";
                confidence = "high";
            }
            // Check someday patterns
            else if (SOMEDAY_PATTERNS.some(p => name.includes(p))) {
                type = "someday";
                confidence = "high";
            }
            // Check reference patterns
            else if (REFERENCE_PATTERNS.some(p => name.includes(p))) {
                type = "reference";
                confidence = "high";
            }
            // Check area patterns
            else if (AREA_PATTERNS.some(p => name.includes(p))) {
                type = "area";
                confidence = "medium";
            }
            // Infer from structure
            else if (folder.depth === 0 && folder.projectCount > 0) {
                type = "area";
                confidence = "low";
            }

            types[folder.name] = {
                type: type,
                confidence: confidence
            };
        });

        return types;
    };

    /**
     * Infer tag categories based on names and patterns
     * @param {Array} tagData - Collected tag data
     * @returns {Object} Categorized tags
     */
    lib.inferTagCategories = function(tagData) {
        const categories = {
            contexts: [],
            people: [],
            status: [],
            energy: [],
            time: [],
            areas: [],
            uncategorized: []
        };

        tagData.forEach(tag => {
            const name = tag.name.toLowerCase();
            let category = "uncategorized";
            let meaning = null;

            // Check for @ prefix (context)
            if (CONTEXT_PREFIXES.some(p => name.startsWith(p))) {
                category = "contexts";
                meaning = "location or tool context";
            }
            // Check context patterns
            else if (CONTEXT_PATTERNS.some(p => name.includes(p))) {
                category = "contexts";
                meaning = "location or tool context";
            }
            // Check waiting/person patterns
            else if (PERSON_PATTERNS.some(p => name.includes(p)) ||
                     WAITING_PREFIXES.some(p => name.startsWith(p))) {
                category = "people";
                meaning = "delegated or waiting for";
            }
            // Check status patterns
            else if (STATUS_PATTERNS.some(p => name.includes(p))) {
                category = "status";
                meaning = "project or task status";
            }
            // Check energy patterns
            else if (ENERGY_PATTERNS.some(p => name.includes(p))) {
                category = "energy";
                meaning = "energy or focus level";
            }
            // Check time patterns
            else if (TIME_PATTERNS.some(p => name.includes(p))) {
                category = "time";
                meaning = "time of day or duration";
            }
            // Check if it looks like an area (top-level, multiple tasks)
            else if (tag.depth === 0 && tag.taskCount > 10) {
                category = "areas";
                meaning = "area of responsibility";
            }

            categories[category].push({
                tag: tag.name,
                usage: tag.taskCount,
                meaning: meaning,
                hasChildren: tag.hasChildren
            });
        });

        return categories;
    };

    /**
     * Detect naming conventions and organizational patterns
     * @param {Object} rawData - All collected data
     * @returns {Object} Detected conventions
     */
    lib.detectConventions = function(rawData) {
        const conventions = {
            tagConventions: {},
            folderConventions: {},
            taskConventions: {}
        };

        // Analyze tag naming conventions
        const tagNames = rawData.tags.map(t => t.name);
        conventions.tagConventions = {
            usesAtPrefix: tagNames.some(n => n.startsWith("@")),
            usesColonNesting: tagNames.some(n => n.includes(":")),
            usesEmoji: tagNames.some(n => /[\u{1F300}-\u{1F9FF}]/u.test(n)),
            usesCamelCase: tagNames.some(n => /[a-z][A-Z]/.test(n)),
            averageNameLength: Math.round(
                tagNames.reduce((sum, n) => sum + n.length, 0) / (tagNames.length || 1)
            )
        };

        // Analyze folder structure
        const folderDepths = rawData.folders.map(f => f.depth);
        const maxDepth = Math.max(...folderDepths, 0);
        const topLevelCount = rawData.folders.filter(f => f.depth === 0).length;

        conventions.folderConventions = {
            maxNestingDepth: maxDepth,
            topLevelFolderCount: topLevelCount,
            averageProjectsPerFolder: Math.round(
                rawData.folders.reduce((sum, f) => sum + f.projectCount, 0) /
                (rawData.folders.length || 1)
            ),
            usesEmoji: rawData.folders.some(f => /[\u{1F300}-\u{1F9FF}]/u.test(f.name))
        };

        // Analyze task conventions (if available)
        if (rawData.tasks) {
            conventions.taskConventions = {
                durationUsageRate: rawData.tasks.percentWithDuration,
                tagUsageRate: rawData.tasks.percentWithTags,
                dueDateUsageRate: rawData.tasks.percentWithDueDate
            };
        }

        return conventions;
    };

    // ==================== GTD Health Calculation ====================

    /**
     * Calculate GTD health scores across all phases
     * @param {Object} rawData - Collected system data
     * @returns {Object} GTD health assessment
     */
    lib.calculateGTDHealth = function(rawData) {
        const health = {
            overallScore: 0,
            phases: {}
        };

        // Phase 1: Capture/Collection
        const inboxSize = rawData.tasks ? rawData.tasks.inInbox : 0;
        health.phases.collection = {
            score: this.scoreInboxHealth(inboxSize),
            inboxSize: inboxSize,
            assessment: inboxSize <= 10 ? "Healthy" :
                        inboxSize <= 25 ? "Needs processing" : "Overflowing"
        };

        // Phase 2: Clarifying
        const taskClarity = rawData.tasks ?
            (rawData.tasks.percentWithDuration + rawData.tasks.percentWithTags) / 2 / 10 : 5;
        health.phases.clarifying = {
            score: Math.min(10, Math.round(taskClarity)),
            taskClarity: rawData.tasks ? rawData.tasks.percentWithDuration : 0,
            assessment: taskClarity >= 7 ? "Well-defined tasks" :
                        taskClarity >= 4 ? "Some tasks need clarity" : "Many vague tasks"
        };

        // Phase 3: Organizing
        const folderStructure = this.assessFolderStructure(rawData.folders);
        health.phases.organizing = {
            score: folderStructure.score,
            folderStructure: folderStructure.quality,
            assessment: folderStructure.assessment
        };

        // Phase 4: Reflecting/Reviewing
        const reviewScore = this.assessReviewHealth(rawData.projects);
        health.phases.reviewing = {
            score: reviewScore.score,
            stalledProjects: rawData.projects.stalled,
            assessment: reviewScore.assessment
        };

        // Phase 5: Engaging
        const engageScore = this.assessEngageHealth(rawData);
        health.phases.engaging = {
            score: engageScore.score,
            nextActionAvailability: engageScore.availability,
            assessment: engageScore.assessment
        };

        // Calculate overall score (weighted average)
        const weights = { collection: 1, clarifying: 1.5, organizing: 2, reviewing: 1.5, engaging: 2 };
        let totalWeight = 0;
        let weightedSum = 0;

        for (const [phase, data] of Object.entries(health.phases)) {
            const weight = weights[phase] || 1;
            weightedSum += data.score * weight;
            totalWeight += weight;
        }

        health.overallScore = Math.round((weightedSum / totalWeight) * 10) / 10;

        return health;
    };

    /**
     * Score inbox health based on size
     * @param {number} inboxSize
     * @returns {number} Score 1-10
     */
    lib.scoreInboxHealth = function(inboxSize) {
        if (inboxSize === 0) return 10;
        if (inboxSize <= 5) return 9;
        if (inboxSize <= 10) return 8;
        if (inboxSize <= 20) return 6;
        if (inboxSize <= 50) return 4;
        return 2;
    };

    /**
     * Assess folder structure quality
     * @param {Array} folders
     * @returns {Object} Structure assessment
     */
    lib.assessFolderStructure = function(folders) {
        const topLevel = folders.filter(f => f.depth === 0).length;
        const maxDepth = Math.max(...folders.map(f => f.depth), 0);

        let score = 7;
        let quality = "good";
        let assessment = "Well-organized structure";

        // Penalize too many or too few top-level folders
        if (topLevel > 12) {
            score -= 2;
            quality = "complex";
            assessment = "Consider consolidating top-level folders";
        } else if (topLevel < 3) {
            score -= 1;
            quality = "minimal";
            assessment = "Consider adding area folders";
        }

        // Penalize deep nesting
        if (maxDepth > 4) {
            score -= 2;
            assessment = "Deep nesting may hinder navigation";
        }

        return { score: Math.max(1, score), quality, assessment };
    };

    /**
     * Assess review health based on project states
     * @param {Object} projects
     * @returns {Object} Review assessment
     */
    lib.assessReviewHealth = function(projects) {
        const stalledRatio = projects.active > 0 ?
            projects.stalled / projects.active : 0;

        let score = 8;
        let assessment = "Projects are active and flowing";

        if (stalledRatio > 0.3) {
            score = 4;
            assessment = "Many projects need next actions";
        } else if (stalledRatio > 0.15) {
            score = 6;
            assessment = "Some projects may need attention";
        }

        return { score, assessment };
    };

    /**
     * Assess engaging phase health
     * @param {Object} rawData
     * @returns {Object} Engage assessment
     */
    lib.assessEngageHealth = function(rawData) {
        const active = rawData.projects.active || 1;
        const available = active - rawData.projects.stalled;
        const availability = Math.round((available / active) * 100);

        let score = 7;
        let assessment = "Good next action availability";

        if (availability >= 90) {
            score = 9;
            assessment = "Excellent next action coverage";
        } else if (availability < 70) {
            score = 5;
            assessment = "Define more next actions";
        }

        return { score, availability, assessment };
    };

    // ==================== System Map Building ====================

    /**
     * Build the final SystemMap structure
     * @param {Object} rawData
     * @param {Object} inferences
     * @param {Object} gtdHealth
     * @param {string} depth
     * @returns {Object} Complete SystemMap
     */
    lib.buildSystemMap = function(rawData, inferences, gtdHealth, depth) {
        const topLevelFolders = rawData.folders
            .filter(f => f.depth === 0)
            .map(f => ({
                name: f.name,
                inferredType: inferences.folderTypes[f.name]?.type || "general",
                confidence: inferences.folderTypes[f.name]?.confidence || "low",
                projectCount: f.projectCount,
                activeProjectCount: f.activeProjectCount,
                subfolderCount: f.subfolderCount
            }));

        // Count tags by category
        const tagCategoryCounts = {};
        for (const [category, tags] of Object.entries(inferences.tagCategories)) {
            tagCategoryCounts[category] = tags.length;
        }

        // Build recommendations based on findings
        const recommendations = this.generateRecommendations(rawData, inferences, gtdHealth);

        return {
            // Metadata
            discoveredAt: new Date().toISOString(),
            discoveryMode: depth,
            aiEnhanced: false,

            // Structure
            structure: {
                folderDepth: Math.max(...rawData.folders.map(f => f.depth), 0),
                totalFolders: rawData.folders.length,
                totalProjects: rawData.projects.total,
                totalActiveTasks: rawData.tasks ? rawData.tasks.active : null,
                topLevelFolders: topLevelFolders
            },

            // Tags
            tags: {
                totalTags: rawData.tags.length,
                taxonomyStyle: this.detectTaxonomyStyle(rawData.tags),
                categories: inferences.tagCategories,
                categoryCounts: tagCategoryCounts,
                conventions: inferences.conventions.tagConventions
            },

            // Projects
            projects: {
                total: rawData.projects.total,
                active: rawData.projects.active,
                onHold: rawData.projects.onHold,
                completed: rawData.projects.completed,
                stalled: rawData.projects.stalled,
                overdue: rawData.projects.overdue,
                typeBreakdown: {
                    sequential: rawData.projects.sequential,
                    parallel: rawData.projects.parallel,
                    singleAction: rawData.projects.singleAction
                }
            },

            // Tasks (if full depth)
            tasks: rawData.tasks ? {
                total: rawData.tasks.total,
                active: rawData.tasks.active,
                inInbox: rawData.tasks.inInbox,
                flagged: rawData.tasks.flagged,
                overdue: rawData.tasks.overdue,
                dataQuality: {
                    withDuration: rawData.tasks.percentWithDuration,
                    withTags: rawData.tasks.percentWithTags,
                    withDueDate: rawData.tasks.percentWithDueDate
                }
            } : null,

            // GTD Health
            gtdHealth: gtdHealth,

            // Conventions
            conventions: inferences.conventions,

            // Recommendations
            recommendations: recommendations
        };
    };

    /**
     * Detect taxonomy style (flat, hierarchical, mixed)
     * @param {Array} tags
     * @returns {string} Taxonomy style
     */
    lib.detectTaxonomyStyle = function(tags) {
        const hasChildren = tags.some(t => t.hasChildren);
        const maxDepth = Math.max(...tags.map(t => t.depth), 0);

        if (maxDepth === 0 && !hasChildren) return "flat";
        if (maxDepth >= 2) return "hierarchical";
        return "mixed";
    };

    /**
     * Generate actionable recommendations
     * @param {Object} rawData
     * @param {Object} inferences
     * @param {Object} gtdHealth
     * @returns {Array} Recommendations
     */
    lib.generateRecommendations = function(rawData, inferences, gtdHealth) {
        const recommendations = [];

        // Inbox recommendation
        if (gtdHealth.phases.collection.inboxSize > 20) {
            recommendations.push({
                area: "inbox",
                severity: "high",
                finding: `Inbox has ${gtdHealth.phases.collection.inboxSize} items`,
                suggestion: "Process inbox during daily review to maintain clarity"
            });
        }

        // Stalled projects recommendation
        if (rawData.projects.stalled > 5) {
            recommendations.push({
                area: "projects",
                severity: "medium",
                finding: `${rawData.projects.stalled} projects have no available next actions`,
                suggestion: "Add next actions to stalled projects during weekly review"
            });
        }

        // Duration estimation recommendation
        if (rawData.tasks && rawData.tasks.percentWithDuration < 50) {
            recommendations.push({
                area: "durations",
                severity: "medium",
                finding: `Only ${rawData.tasks.percentWithDuration}% of tasks have duration estimates`,
                suggestion: "Add durations during weekly review to improve planning"
            });
        }

        // Tag usage recommendation
        if (rawData.tasks && rawData.tasks.percentWithTags < 50) {
            recommendations.push({
                area: "tags",
                severity: "low",
                finding: `Only ${rawData.tasks.percentWithTags}% of tasks are tagged`,
                suggestion: "Consider using tags for context-based working"
            });
        }

        // Overdue tasks recommendation
        if (rawData.tasks && rawData.tasks.overdue > 10) {
            recommendations.push({
                area: "due-dates",
                severity: "high",
                finding: `${rawData.tasks.overdue} tasks are overdue`,
                suggestion: "Review overdue items and update or remove unrealistic due dates"
            });
        }

        // Context tags recommendation
        if (inferences.tagCategories.contexts.length === 0) {
            recommendations.push({
                area: "contexts",
                severity: "low",
                finding: "No context tags detected (e.g., @computer, @phone)",
                suggestion: "Consider adding context tags for location-based task filtering"
            });
        }

        return recommendations;
    };

    // ==================== AI Schema & Prompts ====================

    /**
     * Get LanguageModel.Schema for AI discovery
     * Uses OmniFocus schema format (NOT JSON Schema)
     * @returns {LanguageModel.Schema}
     */
    lib.getDiscoverySchema = function() {
        return LanguageModel.Schema.fromJSON({
            name: "system-discovery-schema",
            properties: [
                {
                    name: "folderInsights",
                    schema: {
                        arrayOf: {
                            name: "folder-insight",
                            properties: [
                                { name: "folderName" },
                                {
                                    name: "inferredType",
                                    description: "area, archive, someday, reference, or general"
                                },
                                { name: "confidence", description: "high, medium, or low" },
                                { name: "reasoning", isOptional: true }
                            ]
                        }
                    }
                },
                {
                    name: "tagInsights",
                    schema: {
                        arrayOf: {
                            name: "tag-insight",
                            properties: [
                                { name: "tagName" },
                                {
                                    name: "inferredCategory",
                                    description: "context, person, status, energy, time, area, or uncategorized"
                                },
                                { name: "suggestedMeaning" }
                            ]
                        }
                    }
                },
                {
                    name: "organizationalStyle",
                    schema: {
                        properties: [
                            { name: "description" },
                            { name: "gtdAlignment", description: "Score 1-10" },
                            {
                                name: "strengths",
                                schema: { arrayOf: { constant: "strength" } }
                            },
                            {
                                name: "suggestions",
                                schema: { arrayOf: { constant: "suggestion" } }
                            }
                        ]
                    }
                },
                {
                    name: "recommendations",
                    schema: {
                        arrayOf: {
                            name: "recommendation",
                            properties: [
                                { name: "area" },
                                { name: "severity", description: "high, medium, or low" },
                                { name: "finding" },
                                { name: "suggestion" }
                            ]
                        }
                    }
                }
            ]
        });
    };

    /**
     * Build discovery prompt for AI analysis
     * @param {Object} systemMap - Basic system map
     * @returns {string} Prompt for Foundation Models
     */
    lib.buildDiscoveryPrompt = function(systemMap) {
        const folderList = systemMap.structure.topLevelFolders
            .map(f => `- "${f.name}" (${f.projectCount} projects, rule-based type: ${f.inferredType})`)
            .join("\n");

        const tagList = [];
        for (const [category, tags] of Object.entries(systemMap.tags.categories)) {
            tags.slice(0, 5).forEach(t => {
                tagList.push(`- "${t.tag}" (${t.usage} tasks, rule-based: ${category})`);
            });
        }

        return `Analyze this OmniFocus system structure and provide semantic insights.

## Current Structure

### Folders (${systemMap.structure.totalFolders} total)
${folderList}

### Tags (${systemMap.tags.totalTags} total, taxonomy: ${systemMap.tags.taxonomyStyle})
${tagList.join("\n")}

### Statistics
- Active Projects: ${systemMap.projects.active}
- Stalled Projects: ${systemMap.projects.stalled}
- Tasks in Inbox: ${systemMap.tasks?.inInbox || "N/A"}
- GTD Health Score: ${systemMap.gtdHealth.overallScore}/10

## Your Task
1. Analyze each folder name semantically to infer its purpose (area of life, archive, someday/maybe, reference, or general)
2. Analyze tag names to suggest their semantic meaning and better categorization
3. Assess the overall organizational style and GTD alignment
4. Provide actionable recommendations for improvement

Focus on semantic understanding - what do these names MEAN to the user, not just pattern matching.`;
    };

    // ==================== Report Generation ====================

    /**
     * Generate a markdown report from SystemMap
     * @param {Object} systemMap
     * @returns {string} Markdown report
     */
    lib.generateMarkdownReport = function(systemMap) {
        const lines = [];

        // Header
        lines.push("# OmniFocus System Discovery Report");
        lines.push("");
        lines.push(`**Generated:** ${new Date().toLocaleString()}`);
        lines.push(`**Discovery Mode:** ${systemMap.discoveryMode}`);
        lines.push(`**AI Enhanced:** ${systemMap.aiEnhanced ? "Yes" : "No"}`);
        lines.push("");
        lines.push("---");
        lines.push("");

        // Executive Summary
        lines.push("## Executive Summary");
        lines.push("");
        lines.push(`**Overall GTD Health Score:** ${systemMap.gtdHealth.overallScore}/10`);
        lines.push("");
        lines.push("### At a Glance");
        lines.push(`- **Folders:** ${systemMap.structure.totalFolders}`);
        lines.push(`- **Projects:** ${systemMap.projects.total} (${systemMap.projects.active} active)`);
        if (systemMap.tasks) {
            lines.push(`- **Tasks:** ${systemMap.tasks.total} (${systemMap.tasks.active} active)`);
        }
        lines.push(`- **Tags:** ${systemMap.tags.totalTags}`);
        lines.push("");

        // GTD Health Breakdown
        lines.push("## GTD Health Analysis");
        lines.push("");

        for (const [phase, data] of Object.entries(systemMap.gtdHealth.phases)) {
            const phaseName = phase.charAt(0).toUpperCase() + phase.slice(1);
            const emoji = data.score >= 7 ? "✅" : data.score >= 5 ? "⚠️" : "❌";
            lines.push(`### ${emoji} ${phaseName} (${data.score}/10)`);
            lines.push(`${data.assessment}`);
            lines.push("");
        }

        // Folder Structure
        lines.push("## Folder Structure");
        lines.push("");
        lines.push(`**Max Depth:** ${systemMap.structure.folderDepth}`);
        lines.push(`**Top-Level Folders:** ${systemMap.structure.topLevelFolders.length}`);
        lines.push("");
        lines.push("| Folder | Type | Confidence | Projects |");
        lines.push("|--------|------|------------|----------|");
        systemMap.structure.topLevelFolders.forEach(f => {
            const type = f.aiInferredType || f.inferredType;
            const confidence = f.aiConfidence || f.confidence;
            lines.push(`| ${f.name} | ${type} | ${confidence} | ${f.projectCount} |`);
        });
        lines.push("");

        // Tag Taxonomy
        lines.push("## Tag Taxonomy");
        lines.push("");
        lines.push(`**Style:** ${systemMap.tags.taxonomyStyle}`);
        lines.push("");

        for (const [category, tags] of Object.entries(systemMap.tags.categories)) {
            if (tags.length > 0) {
                const categoryName = category.charAt(0).toUpperCase() + category.slice(1);
                lines.push(`### ${categoryName} (${tags.length})`);
                tags.slice(0, 10).forEach(t => {
                    lines.push(`- **${t.tag}** (${t.usage} tasks)${t.meaning ? ` - ${t.meaning}` : ""}`);
                });
                if (tags.length > 10) {
                    lines.push(`- _...and ${tags.length - 10} more_`);
                }
                lines.push("");
            }
        }

        // Conventions
        lines.push("## Detected Conventions");
        lines.push("");
        const tc = systemMap.conventions.tagConventions;
        lines.push("### Tag Naming");
        lines.push(`- Uses @ prefix: ${tc.usesAtPrefix ? "Yes" : "No"}`);
        lines.push(`- Uses colon nesting: ${tc.usesColonNesting ? "Yes" : "No"}`);
        lines.push(`- Uses emoji: ${tc.usesEmoji ? "Yes" : "No"}`);
        lines.push("");

        // Recommendations
        if (systemMap.recommendations && systemMap.recommendations.length > 0) {
            lines.push("## Recommendations");
            lines.push("");

            const severityOrder = { high: 1, medium: 2, low: 3 };
            const sortedRecs = [...systemMap.recommendations].sort(
                (a, b) => (severityOrder[a.severity] || 3) - (severityOrder[b.severity] || 3)
            );

            sortedRecs.forEach((rec, i) => {
                const emoji = rec.severity === "high" ? "🔴" :
                              rec.severity === "medium" ? "🟡" : "🟢";
                lines.push(`### ${i + 1}. ${emoji} ${rec.area.charAt(0).toUpperCase() + rec.area.slice(1)}`);
                lines.push(`**Finding:** ${rec.finding}`);
                lines.push(`**Suggestion:** ${rec.suggestion}`);
                lines.push("");
            });
        }

        // AI Insights (if available)
        if (systemMap.aiEnhanced && systemMap.organizationalStyle) {
            lines.push("## AI Organizational Insights");
            lines.push("");
            lines.push(`**Description:** ${systemMap.organizationalStyle.description}`);
            lines.push(`**GTD Alignment:** ${systemMap.organizationalStyle.gtdAlignment}/10`);
            lines.push("");

            if (systemMap.organizationalStyle.strengths?.length > 0) {
                lines.push("### Strengths");
                systemMap.organizationalStyle.strengths.forEach(s => {
                    lines.push(`- ✅ ${s}`);
                });
                lines.push("");
            }

            if (systemMap.organizationalStyle.suggestions?.length > 0) {
                lines.push("### Suggestions");
                systemMap.organizationalStyle.suggestions.forEach(s => {
                    lines.push(`- 💡 ${s}`);
                });
                lines.push("");
            }
        }

        // Footer
        lines.push("---");
        lines.push("");
        lines.push("_Generated by AITaskAnalyzer v3.3.0_");
        lines.push("");
        lines.push("_Powered by Apple Foundation Models (on-device AI)_");

        return lines.join("\n");
    };

    /**
     * Generate a summary string for alert display
     * @param {Object} systemMap
     * @returns {string} Summary text
     */
    lib.generateSummary = function(systemMap) {
        const lines = [];

        lines.push(`GTD Health Score: ${systemMap.gtdHealth.overallScore}/10`);
        lines.push("");
        lines.push(`Folders: ${systemMap.structure.totalFolders}`);
        lines.push(`Projects: ${systemMap.projects.active} active / ${systemMap.projects.total} total`);
        if (systemMap.tasks) {
            lines.push(`Tasks: ${systemMap.tasks.active} active`);
            lines.push(`Inbox: ${systemMap.tasks.inInbox} items`);
        }
        lines.push(`Tags: ${systemMap.tags.totalTags}`);
        lines.push("");
        lines.push("GTD Phases:");

        for (const [phase, data] of Object.entries(systemMap.gtdHealth.phases)) {
            const emoji = data.score >= 7 ? "✓" : data.score >= 5 ? "~" : "✗";
            lines.push(`  ${emoji} ${phase}: ${data.score}/10`);
        }

        if (systemMap.recommendations?.length > 0) {
            lines.push("");
            lines.push(`${systemMap.recommendations.length} recommendations available`);
        }

        return lines.join("\n");
    };

    return lib;
})();
