/**
 * Tree Builder Library for OmniFocus
 *
 * Composable library for building tree structures from OmniFocus hierarchies.
 * Supports database objects and OmniFocus 4 window trees (TreeNode API).
 * Provides export to Markdown, JSON, OPML and interactive navigation operations.
 *
 * Usage (in OmniFocus plugin):
 *   const treeBuilder = this.plugIn.library("treeBuilder");
 *   const tree = treeBuilder.buildTreeFromDatabase({ includeMetrics: true });
 *   const markdown = treeBuilder.exportToMarkdown(tree);
 *
 * OmniFocus 4 Features:
 *   const window = document.windows[0];
 *   const contentTree = treeBuilder.buildTreeFromWindow(window, "content");
 *   treeBuilder.revealNodes(window, [projectId]);
 *
 * @version 1.0.0
 */

(() => {
    var lib = new PlugIn.Library(new Version("1.0"));

    // ============================================================================
    // DATABASE TREE BUILDING
    // ============================================================================

    /**
     * Build tree structure from OmniFocus database hierarchy
     * Starts from root folders and recursively includes subfolders/projects/tasks
     * @param {Object} options - Build options
     * @param {boolean} options.includeMetrics - Include metrics from parsers (default: true)
     * @param {boolean} options.includeHealth - Include health assessment (default: true)
     * @param {number} options.maxDepth - Maximum depth to traverse (default: unlimited)
     * @param {Function} options.filter - Optional filter predicate for nodes
     * @returns {Object} Root tree node with children
     */
    lib.buildTreeFromDatabase = function(options = {}) {
        const maxDepth = options.maxDepth || Infinity;

        // Create virtual root node
        const root = {
            id: "root",
            name: "OmniFocus Hierarchy",
            nodeType: "root",
            depth: -1,
            path: [],
            parentId: null,
            children: [],
            metrics: null,
            health: null,
            ofObject: null,
            treeNode: null
        };

        // Get root folders (global variable from OmniFocus)
        const rootFolders = folders || [];

        // Build tree for each root folder
        rootFolders.forEach(folder => {
            if (maxDepth >= 0) {
                const folderNode = this.buildTreeFromFolder(folder, {
                    ...options,
                    _depth: 0,
                    _parentPath: []
                });
                root.children.push(folderNode);
            }
        });

        return root;
    };

    /**
     * Build tree structure from a single folder
     * Recursively includes subfolders and projects
     * @param {Folder} folder - The folder object to build from
     * @param {Object} options - Build options
     * @param {boolean} options.includeMetrics - Include metrics from folderParser
     * @param {boolean} options.includeHealth - Include health assessment
     * @param {number} options.maxDepth - Maximum depth to traverse
     * @param {number} options._depth - Internal: current depth
     * @param {Array} options._parentPath - Internal: parent path array
     * @returns {Object} Tree node with folder data and children
     */
    lib.buildTreeFromFolder = function(folder, options = {}) {
        if (!folder) {
            throw new Error("Folder parameter is required");
        }

        const includeMetrics = options.includeMetrics !== false;
        const includeHealth = options.includeHealth !== false;
        const maxDepth = options.maxDepth || Infinity;
        const depth = options._depth || 0;
        const parentPath = options._parentPath || [];

        // Try to use folderParser if available
        let parsedData = {};
        try {
            const folderParser = this.plugIn?.library("folderParser");
            if (folderParser) {
                parsedData = folderParser.parseFolder(folder, depth, false, false);
            }
        } catch (e) {
            // Fallback: basic folder parsing
            parsedData = this._basicFolderParse(folder);
        }

        // Build tree node with metadata
        const path = [...parentPath, folder.name];
        const node = {
            id: folder.id.primaryKey,
            name: folder.name,
            nodeType: "folder",
            depth: depth,
            path: path,
            parentId: parentPath.length > 0 ? null : null, // Set by parent
            children: [],
            ofObject: folder,
            treeNode: null,
            metrics: includeMetrics ? parsedData.metrics : null,
            health: includeHealth ? parsedData.health : null
        };

        // Stop if max depth reached
        if (depth >= maxDepth) {
            return node;
        }

        // Add subfolders
        if (folder.folders && folder.folders.length > 0) {
            folder.folders.forEach(subfolder => {
                const childNode = this.buildTreeFromFolder(subfolder, {
                    ...options,
                    _depth: depth + 1,
                    _parentPath: path
                });
                childNode.parentId = node.id;
                node.children.push(childNode);
            });
        }

        // Add projects
        if (folder.projects && folder.projects.length > 0) {
            folder.projects.forEach(project => {
                const projectNode = this.buildTreeFromProject(project, {
                    ...options,
                    _depth: depth + 1,
                    _parentPath: path,
                    _parentId: node.id
                });
                node.children.push(projectNode);
            });
        }

        return node;
    };

    /**
     * Build tree structure from a single project
     * Includes tasks as children
     * @param {Project} project - The project object to build from
     * @param {Object} options - Build options
     * @param {boolean} options.includeMetrics - Include metrics from projectParser
     * @param {boolean} options.includeHealth - Include GTD health
     * @param {boolean} options.includeTasks - Include task children (default: true)
     * @param {number} options.maxDepth - Maximum depth to traverse
     * @param {number} options._depth - Internal: current depth
     * @param {Array} options._parentPath - Internal: parent path array
     * @param {string} options._parentId - Internal: parent folder ID
     * @returns {Object} Tree node with project data and task children
     */
    lib.buildTreeFromProject = function(project, options = {}) {
        if (!project) {
            throw new Error("Project parameter is required");
        }

        const includeMetrics = options.includeMetrics !== false;
        const includeHealth = options.includeHealth !== false;
        const includeTasks = options.includeTasks !== false;
        const maxDepth = options.maxDepth || Infinity;
        const depth = options._depth || 0;
        const parentPath = options._parentPath || [];
        const parentId = options._parentId || null;

        // Try to use projectParser if available
        let parsedData = {};
        try {
            const projectParser = this.plugIn?.library("projectParser");
            if (projectParser) {
                parsedData = projectParser.parseProject(project, false); // Don't include task details yet
            }
        } catch (e) {
            // Fallback: basic project parsing
            parsedData = this._basicProjectParse(project);
        }

        // Build tree node
        const path = [...parentPath, project.name];
        const node = {
            id: project.id.primaryKey,
            name: project.name,
            nodeType: "project",
            depth: depth,
            path: path,
            parentId: parentId,
            children: [],
            ofObject: project,
            treeNode: null,
            status: project.status.name,
            completed: project.completed,
            metrics: includeMetrics ? parsedData.metrics : null,
            health: includeHealth ? parsedData.gtdHealth : null
        };

        // Stop if max depth reached or tasks not requested
        if (depth >= maxDepth || !includeTasks) {
            return node;
        }

        // Add tasks (only root-level tasks, not nested)
        const tasks = project.task ? project.task.tasks : [];
        if (tasks && tasks.length > 0) {
            tasks.forEach(task => {
                const taskNode = this._buildTaskNode(task, depth + 1, path, node.id, options);
                node.children.push(taskNode);
            });
        }

        return node;
    };

    /**
     * Build tree node for a task (internal helper)
     * @param {Task} task - Task object
     * @param {number} depth - Current depth
     * @param {Array} parentPath - Parent path array
     * @param {string} parentId - Parent project ID
     * @param {Object} options - Build options
     * @returns {Object} Task tree node
     * @private
     */
    lib._buildTaskNode = function(task, depth, parentPath, parentId, options) {
        const includeMetrics = options.includeMetrics !== false;
        const includeHealth = options.includeHealth !== false;

        // Try to use taskParser if available
        let parsedData = {};
        try {
            const taskParser = this.plugIn?.library("taskParser");
            if (taskParser) {
                parsedData = taskParser.parseTask(task);
            }
        } catch (e) {
            // Fallback: basic task parsing
            parsedData = this._basicTaskParse(task);
        }

        const path = [...parentPath, task.name];
        const node = {
            id: task.id.primaryKey,
            name: task.name,
            nodeType: "task",
            depth: depth,
            path: path,
            parentId: parentId,
            children: [],
            ofObject: task,
            treeNode: null,
            completed: task.completed,
            dropped: task.dropped,
            flagged: task.flagged,
            dueDate: task.dueDate,
            metrics: includeMetrics ? (parsedData.age || null) : null,
            health: includeHealth ? (parsedData.clarity || null) : null
        };

        // Add subtasks recursively
        if (task.tasks && task.tasks.length > 0) {
            task.tasks.forEach(subtask => {
                const subtaskNode = this._buildTaskNode(
                    subtask,
                    depth + 1,
                    path,
                    node.id,
                    options
                );
                node.children.push(subtaskNode);
            });
        }

        return node;
    };

    // ============================================================================
    // FALLBACK PARSING (when libraries unavailable)
    // ============================================================================

    /**
     * Basic folder parsing fallback
     * @param {Folder} folder - Folder to parse
     * @returns {Object} Basic folder data
     * @private
     */
    lib._basicFolderParse = function(folder) {
        return {
            id: folder.id.primaryKey,
            name: folder.name,
            metrics: null,
            health: null
        };
    };

    /**
     * Basic project parsing fallback
     * @param {Project} project - Project to parse
     * @returns {Object} Basic project data
     * @private
     */
    lib._basicProjectParse = function(project) {
        return {
            id: project.id.primaryKey,
            name: project.name,
            status: project.status.name,
            completed: project.completed,
            metrics: null,
            gtdHealth: null
        };
    };

    /**
     * Basic task parsing fallback
     * @param {Task} task - Task to parse
     * @returns {Object} Basic task data
     * @private
     */
    lib._basicTaskParse = function(task) {
        return {
            id: task.id.primaryKey,
            name: task.name,
            completed: task.completed,
            dropped: task.dropped
        };
    };

    // ============================================================================
    // TREE UTILITY FUNCTIONS
    // ============================================================================

    /**
     * Traverse tree with depth-first traversal
     * Calls callback for each node
     * @param {Object} rootNode - Root of tree to traverse
     * @param {Function} callback - Callback function(node, depth, parent)
     * @param {number} _depth - Internal: current depth
     * @param {Object} _parent - Internal: parent node
     */
    lib.traverseTree = function(rootNode, callback, _depth = 0, _parent = null) {
        if (!rootNode || !callback) return;

        // Call callback for current node
        callback(rootNode, _depth, _parent);

        // Recursively traverse children
        if (rootNode.children && rootNode.children.length > 0) {
            rootNode.children.forEach(child => {
                this.traverseTree(child, callback, _depth + 1, rootNode);
            });
        }
    };

    /**
     * Flatten tree to array of nodes
     * @param {Object} rootNode - Root of tree
     * @returns {Array} Flat array of all nodes
     */
    lib.flattenTree = function(rootNode) {
        const result = [];
        this.traverseTree(rootNode, (node) => {
            result.push(node);
        });
        return result;
    };

    /**
     * Find node by ID
     * @param {Object} tree - Tree to search
     * @param {string} id - Node ID to find
     * @returns {Object|null} Found node or null
     */
    lib.findNodeById = function(tree, id) {
        let found = null;
        this.traverseTree(tree, (node) => {
            if (node.id === id) {
                found = node;
            }
        });
        return found;
    };

    /**
     * Find nodes by path
     * @param {Object} tree - Tree to search
     * @param {Array} pathArray - Path components (e.g., ["Folder", "Project", "Task"])
     * @returns {Array} Array of nodes matching path
     */
    lib.findNodesByPath = function(tree, pathArray) {
        const results = [];
        this.traverseTree(tree, (node) => {
            if (node.path && node.path.length === pathArray.length) {
                let matches = true;
                for (let i = 0; i < pathArray.length; i++) {
                    if (node.path[i] !== pathArray[i]) {
                        matches = false;
                        break;
                    }
                }
                if (matches) {
                    results.push(node);
                }
            }
        });
        return results;
    };

    /**
     * Filter nodes by predicate
     * @param {Object} tree - Tree to filter
     * @param {Function} predicate - Filter function(node) => boolean
     * @returns {Array} Array of nodes matching predicate
     */
    lib.filterNodes = function(tree, predicate) {
        const results = [];
        this.traverseTree(tree, (node) => {
            if (predicate(node)) {
                results.push(node);
            }
        });
        return results;
    };

    /**
     * Get tree statistics
     * @param {Object} rootNode - Root of tree
     * @returns {Object} Statistics object
     */
    lib.getTreeStatistics = function(rootNode) {
        let totalNodes = 0;
        let folderCount = 0;
        let projectCount = 0;
        let taskCount = 0;
        let maxDepth = 0;

        this.traverseTree(rootNode, (node, depth) => {
            totalNodes++;
            if (node.nodeType === "folder") folderCount++;
            else if (node.nodeType === "project") projectCount++;
            else if (node.nodeType === "task") taskCount++;

            if (depth > maxDepth) maxDepth = depth;
        });

        return {
            totalNodes,
            folderCount,
            projectCount,
            taskCount,
            maxDepth
        };
    };

    // ============================================================================
    // EXPORT FUNCTIONS
    // ============================================================================

    /**
     * Export tree to Markdown format
     * Uses hierarchical indentation to represent structure
     * @param {Object} tree - Tree to export
     * @param {Object} options - Export options
     * @param {string} options.indent - Indentation string (default: "  ")
     * @param {boolean} options.includeMetrics - Include metrics (default: true)
     * @param {boolean} options.includeHealth - Include health indicators (default: true)
     * @param {boolean} options.includeIcons - Include emoji icons (default: false)
     * @returns {string} Markdown formatted string
     */
    lib.exportToMarkdown = function(tree, options = {}) {
        const indent = options.indent || "  ";
        const includeMetrics = options.includeMetrics !== false;
        const includeHealth = options.includeHealth !== false;
        const includeIcons = options.includeIcons === true;

        const lines = [];

        // Add header
        lines.push(`# ${tree.name}\n`);
        lines.push(`**Generated:** ${new Date().toLocaleString()}\n`);

        // Traverse and format
        this.traverseTree(tree, (node, depth) => {
            if (depth === -1) return; // Skip root

            const prefix = indent.repeat(depth);
            let line = prefix;

            // Add icon
            if (includeIcons) {
                if (node.nodeType === "folder") line += "📁 ";
                else if (node.nodeType === "project") line += "📋 ";
                else if (node.nodeType === "task") {
                    if (node.completed) line += "✅ ";
                    else if (node.flagged) line += "🚩 ";
                    else line += "⬜ ";
                }
            }

            // Add bullet and name
            line += `- **${node.name}**`;

            // Add type indicator
            line += ` _(${node.nodeType})_`;

            // Add status for projects/tasks
            if (node.nodeType === "project" && node.status) {
                line += ` [${node.status}]`;
            } else if (node.nodeType === "task") {
                if (node.completed) line += ` [completed]`;
                else if (node.dropped) line += ` [dropped]`;
                else if (node.flagged) line += ` [flagged]`;
            }

            // Add health
            if (includeHealth && node.health) {
                if (typeof node.health === 'string') {
                    line += ` **Health:** ${node.health}`;
                } else if (typeof node.health === 'object' && node.health.score) {
                    line += ` **Clarity:** ${node.health.score}/10`;
                }
            }

            lines.push(line);

            // Add metrics on next line if requested and available
            if (includeMetrics && node.metrics) {
                const metricsLine = this._formatMetricsMarkdown(node.metrics, depth, indent);
                if (metricsLine) {
                    lines.push(metricsLine);
                }
            }
        });

        return lines.join("\n");
    };

    /**
     * Format metrics as Markdown (internal helper)
     * @param {Object} metrics - Metrics object
     * @param {number} depth - Current depth for indentation
     * @param {string} indent - Indentation string
     * @returns {string} Formatted metrics line
     * @private
     */
    lib._formatMetricsMarkdown = function(metrics, depth, indent) {
        if (!metrics) return "";

        const prefix = indent.repeat(depth + 1);
        const parts = [];

        // Folder metrics
        if (metrics.projectCount !== undefined) {
            parts.push(`Projects: ${metrics.activeProjects}/${metrics.projectCount}`);
            parts.push(`Tasks: ${metrics.activeTasks}/${metrics.totalTasks}`);
            if (metrics.completionRate !== undefined) {
                parts.push(`Completion: ${metrics.completionRate}%`);
            }
        }
        // Project metrics
        else if (metrics.taskCount !== undefined) {
            parts.push(`Tasks: ${metrics.activeTasks}/${metrics.taskCount}`);
            if (metrics.completionRate !== undefined) {
                parts.push(`Completion: ${metrics.completionRate}%`);
            }
            if (metrics.daysActive !== undefined) {
                parts.push(`Days Active: ${metrics.daysActive}`);
            }
        }
        // Task age metrics
        else if (metrics.daysOld !== undefined) {
            parts.push(`Age: ${metrics.daysOld} days`);
            if (metrics.isOverdue) {
                parts.push(`Overdue: ${metrics.daysOverdue} days`);
            }
        }

        return parts.length > 0 ? `${prefix}_${parts.join(", ")}_` : "";
    };

    /**
     * Export tree to JSON format
     * @param {Object} tree - Tree to export
     * @param {Object} options - Export options
     * @param {boolean} options.pretty - Pretty print JSON (default: true)
     * @param {boolean} options.includeOFRefs - Include OmniFocus object references (default: false)
     * @returns {string} JSON formatted string
     */
    lib.exportToJSON = function(tree, options = {}) {
        const pretty = options.pretty !== false;
        const includeOFRefs = options.includeOFRefs === true;

        // Clean tree for JSON (remove circular references, OmniFocus objects)
        const cleaned = this._cleanTreeForJSON(tree, includeOFRefs);

        return pretty
            ? JSON.stringify(cleaned, null, 2)
            : JSON.stringify(cleaned);
    };

    /**
     * Clean tree for JSON export (internal helper)
     * Removes circular references and optionally OmniFocus objects
     * @param {Object} node - Node to clean
     * @param {boolean} includeOFRefs - Include ofObject references
     * @returns {Object} Cleaned node
     * @private
     */
    lib._cleanTreeForJSON = function(node, includeOFRefs) {
        if (!node) return null;

        const cleaned = {
            id: node.id,
            name: node.name,
            nodeType: node.nodeType,
            depth: node.depth,
            path: node.path,
            parentId: node.parentId
        };

        // Add optional fields
        if (node.status) cleaned.status = node.status;
        if (node.completed !== undefined) cleaned.completed = node.completed;
        if (node.dropped !== undefined) cleaned.dropped = node.dropped;
        if (node.flagged !== undefined) cleaned.flagged = node.flagged;
        if (node.dueDate) cleaned.dueDate = node.dueDate.toISOString();
        if (node.metrics) cleaned.metrics = node.metrics;
        if (node.health) cleaned.health = node.health;

        // Don't include ofObject and treeNode (circular references)
        // unless specifically requested
        if (includeOFRefs) {
            cleaned.ofObjectId = node.ofObject?.id?.primaryKey || null;
        }

        // Recursively clean children
        if (node.children && node.children.length > 0) {
            cleaned.children = node.children.map(child =>
                this._cleanTreeForJSON(child, includeOFRefs)
            );
        } else {
            cleaned.children = [];
        }

        return cleaned;
    };

    /**
     * Export tree to OPML format
     * Compatible with outliner applications
     * @param {Object} tree - Tree to export
     * @param {Object} options - Export options
     * @param {string} options.title - Document title (default: tree name)
     * @param {boolean} options.includeMetrics - Include metrics as attributes (default: true)
     * @returns {string} OPML XML string
     */
    lib.exportToOPML = function(tree, options = {}) {
        const title = options.title || tree.name || "OmniFocus Outline";
        const includeMetrics = options.includeMetrics !== false;

        const lines = [];
        lines.push('<?xml version="1.0" encoding="UTF-8"?>');
        lines.push('<opml version="2.0">');
        lines.push('  <head>');
        lines.push(`    <title>${this._escapeXML(title)}</title>`);
        lines.push(`    <dateCreated>${new Date().toISOString()}</dateCreated>`);
        lines.push('    <ownerName>OmniFocus Tree Builder</ownerName>');
        lines.push('  </head>');
        lines.push('  <body>');

        // Convert tree to OPML outline elements
        if (tree.children && tree.children.length > 0) {
            tree.children.forEach(child => {
                lines.push(this._nodeToOPML(child, 2, includeMetrics));
            });
        }

        lines.push('  </body>');
        lines.push('</opml>');

        return lines.join("\n");
    };

    /**
     * Convert tree node to OPML outline element (internal helper)
     * @param {Object} node - Tree node
     * @param {number} indentLevel - Indentation level
     * @param {boolean} includeMetrics - Include metrics as attributes
     * @returns {string} OPML outline element
     * @private
     */
    lib._nodeToOPML = function(node, indentLevel, includeMetrics) {
        const indent = "  ".repeat(indentLevel);
        let attrs = [];

        // Required: text attribute
        attrs.push(`text="${this._escapeXML(node.name)}"`);

        // Add type
        attrs.push(`type="${node.nodeType}"`);

        // Add optional attributes
        if (node.id) attrs.push(`id="${this._escapeXML(node.id)}"`);
        if (node.status) attrs.push(`status="${this._escapeXML(node.status)}"`);
        if (node.completed) attrs.push(`completed="true"`);
        if (node.flagged) attrs.push(`flagged="true"`);

        // Add metrics as attributes if requested
        if (includeMetrics && node.metrics) {
            if (node.metrics.projectCount !== undefined) {
                attrs.push(`projectCount="${node.metrics.projectCount}"`);
                attrs.push(`activeProjects="${node.metrics.activeProjects}"`);
            }
            if (node.metrics.taskCount !== undefined) {
                attrs.push(`taskCount="${node.metrics.taskCount}"`);
            }
            if (node.metrics.completionRate !== undefined) {
                attrs.push(`completionRate="${node.metrics.completionRate}"`);
            }
        }

        // Check if node has children
        if (node.children && node.children.length > 0) {
            // Open tag with children
            let opml = `${indent}<outline ${attrs.join(" ")}>\n`;

            // Add children recursively
            node.children.forEach(child => {
                opml += this._nodeToOPML(child, indentLevel + 1, includeMetrics);
            });

            // Close tag
            opml += `${indent}</outline>\n`;
            return opml;
        } else {
            // Self-closing tag
            return `${indent}<outline ${attrs.join(" ")} />\n`;
        }
    };

    /**
     * Escape XML special characters
     * @param {string} str - String to escape
     * @returns {string} Escaped string
     * @private
     */
    lib._escapeXML = function(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&apos;");
    };

    // ============================================================================
    // OMNIFOCUS 4 WINDOW TREE API
    // ============================================================================

    /**
     * Build tree from OmniFocus 4 window tree
     * Captures current window state (expanded, selected, revealed)
     * @param {DocumentWindow} window - OmniFocus window
     * @param {string} treeType - "content" or "sidebar"
     * @param {Object} options - Build options
     * @returns {Object} Tree structure with TreeNode references
     */
    lib.buildTreeFromWindow = function(window, treeType = "content", options = {}) {
        if (!window) {
            throw new Error("Window parameter is required");
        }

        // Get tree (ContentTree or SidebarTree)
        const tree = treeType === "sidebar" ? window.sidebar : window.content;
        if (!tree) {
            throw new Error(`Window ${treeType} tree not available (OmniFocus 4+ required)`);
        }

        const rootNode = tree.rootNode;
        if (!rootNode) {
            throw new Error("Window tree rootNode not available");
        }

        // Traverse TreeNode hierarchy
        return this._traverseTreeNode(rootNode, 0, [], options);
    };

    /**
     * Traverse TreeNode and build tree structure (internal helper)
     * @param {TreeNode} treeNode - TreeNode to traverse
     * @param {number} depth - Current depth
     * @param {Array} parentPath - Parent path array
     * @param {Object} options - Build options
     * @returns {Object} Tree node
     * @private
     */
    lib._traverseTreeNode = function(treeNode, depth, parentPath, options) {
        const maxDepth = options.maxDepth || Infinity;
        const includeMetrics = options.includeMetrics !== false;
        const includeHealth = options.includeHealth !== false;

        // Get underlying OmniFocus object
        const obj = treeNode.object;
        if (!obj) {
            return null;
        }

        // Determine node type
        let nodeType = "unknown";
        if (obj.constructor.name === "Folder") nodeType = "folder";
        else if (obj.constructor.name === "Project") nodeType = "project";
        else if (obj.constructor.name === "Task") nodeType = "task";

        // Parse object based on type
        let parsedData = {};
        if (nodeType === "folder") {
            parsedData = this.buildTreeFromFolder(obj, { ...options, _depth: 0, _parentPath: [] });
        } else if (nodeType === "project") {
            parsedData = this.buildTreeFromProject(obj, { ...options, _depth: 0, _parentPath: [] });
        } else if (nodeType === "task") {
            parsedData = this._buildTaskNode(obj, 0, [], null, options);
        }

        // Build enhanced node
        const path = [...parentPath, obj.name];
        const node = {
            id: obj.id.primaryKey,
            name: obj.name,
            nodeType: nodeType,
            depth: depth,
            path: path,
            parentId: treeNode.parent?.object?.id?.primaryKey || null,
            children: [],
            ofObject: obj,
            treeNode: treeNode,
            isExpanded: treeNode.isExpanded,
            isSelected: treeNode.isSelected,
            isRevealed: treeNode.isRevealed,
            metrics: includeMetrics ? parsedData.metrics : null,
            health: includeHealth ? parsedData.health : null
        };

        // Add type-specific fields
        if (nodeType === "project") {
            node.status = obj.status.name;
            node.completed = obj.completed;
        } else if (nodeType === "task") {
            node.completed = obj.completed;
            node.dropped = obj.dropped;
            node.flagged = obj.flagged;
        }

        // Stop if max depth reached
        if (depth >= maxDepth) {
            return node;
        }

        // Recursively process children
        if (treeNode.children && treeNode.children.length > 0) {
            treeNode.children.forEach(childTreeNode => {
                const childNode = this._traverseTreeNode(childTreeNode, depth + 1, path, options);
                if (childNode) {
                    node.children.push(childNode);
                }
            });
        }

        return node;
    };

    /**
     * Check if OmniFocus 4 tree API is supported
     * @returns {boolean} True if tree API available
     */
    lib.checkOF4TreeSupport = function() {
        try {
            const window = document.windows[0];
            if (!window) return false;
            return (window.content !== undefined && window.sidebar !== undefined);
        } catch (e) {
            return false;
        }
    };

    // ============================================================================
    // INTERACTIVE OPERATIONS (OmniFocus 4)
    // ============================================================================

    /**
     * Reveal nodes in window tree
     * Expands ancestors to make nodes visible
     * @param {DocumentWindow} window - OmniFocus window
     * @param {Array<string>} nodeIds - Array of node IDs to reveal
     * @param {string} treeType - "content" or "sidebar" (default: "content")
     * @returns {boolean} Success status
     */
    lib.revealNodes = function(window, nodeIds, treeType = "content") {
        if (!window || !nodeIds || nodeIds.length === 0) {
            return false;
        }

        const tree = treeType === "sidebar" ? window.sidebar : window.content;
        if (!tree) {
            console.error("Window tree not available (OmniFocus 4+ required)");
            return false;
        }

        try {
            // Find OmniFocus objects by ID
            const objects = [];
            nodeIds.forEach(id => {
                const obj = this._findObjectById(id);
                if (obj) objects.push(obj);
            });

            if (objects.length === 0) {
                return false;
            }

            // Get TreeNodes for objects
            const treeNodes = tree.nodesForObjects(objects);

            // Reveal all nodes
            if (treeNodes && treeNodes.length > 0) {
                tree.reveal(treeNodes);
                return true;
            }

            return false;
        } catch (error) {
            console.error("Reveal nodes failed:", error);
            return false;
        }
    };

    /**
     * Select nodes in window tree
     * @param {DocumentWindow} window - OmniFocus window
     * @param {Array<string>} nodeIds - Array of node IDs to select
     * @param {boolean} extending - Extend selection (default: false)
     * @param {string} treeType - "content" or "sidebar" (default: "content")
     * @returns {boolean} Success status
     */
    lib.selectNodes = function(window, nodeIds, extending = false, treeType = "content") {
        if (!window || !nodeIds || nodeIds.length === 0) {
            return false;
        }

        const tree = treeType === "sidebar" ? window.sidebar : window.content;
        if (!tree) {
            console.error("Window tree not available (OmniFocus 4+ required)");
            return false;
        }

        try {
            // Find OmniFocus objects by ID
            const objects = [];
            nodeIds.forEach(id => {
                const obj = this._findObjectById(id);
                if (obj) objects.push(obj);
            });

            if (objects.length === 0) {
                return false;
            }

            // Get TreeNodes for objects
            const treeNodes = tree.nodesForObjects(objects);

            // Select nodes
            if (treeNodes && treeNodes.length > 0) {
                tree.select(treeNodes, extending);
                return true;
            }

            return false;
        } catch (error) {
            console.error("Select nodes failed:", error);
            return false;
        }
    };

    /**
     * Expand nodes in window tree
     * @param {DocumentWindow} window - OmniFocus window
     * @param {Array<string>} nodeIds - Array of node IDs to expand
     * @param {boolean} completely - Expand completely (all descendants)
     * @param {string} treeType - "content" or "sidebar" (default: "content")
     * @returns {boolean} Success status
     */
    lib.expandNodes = function(window, nodeIds, completely = false, treeType = "content") {
        if (!window || !nodeIds || nodeIds.length === 0) {
            return false;
        }

        const tree = treeType === "sidebar" ? window.sidebar : window.content;
        if (!tree) {
            console.error("Window tree not available (OmniFocus 4+ required)");
            return false;
        }

        try {
            nodeIds.forEach(id => {
                const obj = this._findObjectById(id);
                if (obj) {
                    const treeNode = tree.nodeForObject(obj);
                    if (treeNode && treeNode.canExpand) {
                        treeNode.expand(completely);
                    }
                }
            });
            return true;
        } catch (error) {
            console.error("Expand nodes failed:", error);
            return false;
        }
    };

    /**
     * Collapse nodes in window tree
     * @param {DocumentWindow} window - OmniFocus window
     * @param {Array<string>} nodeIds - Array of node IDs to collapse
     * @param {boolean} completely - Collapse completely (all descendants)
     * @param {string} treeType - "content" or "sidebar" (default: "content")
     * @returns {boolean} Success status
     */
    lib.collapseNodes = function(window, nodeIds, completely = false, treeType = "content") {
        if (!window || !nodeIds || nodeIds.length === 0) {
            return false;
        }

        const tree = treeType === "sidebar" ? window.sidebar : window.content;
        if (!tree) {
            console.error("Window tree not available (OmniFocus 4+ required)");
            return false;
        }

        try {
            nodeIds.forEach(id => {
                const obj = this._findObjectById(id);
                if (obj) {
                    const treeNode = tree.nodeForObject(obj);
                    if (treeNode && treeNode.canCollapse) {
                        treeNode.collapse(completely);
                    }
                }
            });
            return true;
        } catch (error) {
            console.error("Collapse nodes failed:", error);
            return false;
        }
    };

    /**
     * Find OmniFocus object by ID (internal helper)
     * Searches across flattenedFolders, flattenedProjects, flattenedTasks
     * @param {string} id - Object ID to find
     * @returns {Object|null} Found object or null
     * @private
     */
    lib._findObjectById = function(id) {
        // Search in flattened folders
        if (flattenedFolders) {
            const folder = flattenedFolders.find(f => f.id.primaryKey === id);
            if (folder) return folder;
        }

        // Search in flattened projects
        if (flattenedProjects) {
            const project = flattenedProjects.find(p => p.id.primaryKey === id);
            if (project) return project;
        }

        // Search in flattened tasks
        if (flattenedTasks) {
            const task = flattenedTasks.find(t => t.id.primaryKey === id);
            if (task) return task;
        }

        return null;
    };

    return lib;
})();
