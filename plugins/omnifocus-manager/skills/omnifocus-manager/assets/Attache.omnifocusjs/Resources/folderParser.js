/**
 * Folder Parser Library for OmniFocus
 *
 * Composable library for parsing folder objects and calculating aggregate metrics
 * across folder hierarchies. Designed for hierarchical analysis with configurable depth.
 *
 * Usage (in OmniFocus plugin):
 *   const folderParser = this.plugIn.library("folderParser");
 *   const parsedFolder = folderParser.parseFolder(folder, 2, true);
 *
 * @version 1.0.0
 */

(() => {
    var lib = new PlugIn.Library(new Version("1.0"));

    /**
     * Parse a folder and optionally its hierarchy with metrics
     * @param {Folder} folder - The folder to parse
     * @param {number} depth - Current depth level (0 = root)
     * @param {boolean} includeSubfolders - Whether to recursively parse subfolders
     * @param {boolean} includeProjects - Whether to include project details
     * @returns {Object} Structured folder data with metrics
     */
    lib.parseFolder = function(folder, depth = 0, includeSubfolders = false, includeProjects = false) {
        if (!folder) {
            throw new Error("Folder parameter is required");
        }

        const parsedFolder = {
            id: folder.id.primaryKey,
            name: folder.name,
            depth: depth
        };

        // Calculate metrics for this folder
        parsedFolder.metrics = this.calculateFolderMetrics(folder);
        parsedFolder.health = this.getFolderHealth(parsedFolder.metrics);

        // Parse subfolders recursively if requested
        parsedFolder.subfolders = [];
        if (includeSubfolders && folder.folders && folder.folders.length > 0) {
            folder.folders.forEach(subfolder => {
                parsedFolder.subfolders.push(
                    this.parseFolder(subfolder, depth + 1, true, includeProjects)
                );
            });
        }

        // Include projects if requested
        parsedFolder.projects = [];
        if (includeProjects && folder.flattenedProjects && folder.flattenedProjects.length > 0) {
            // Store basic project info (detailed parsing done by projectParser)
            folder.flattenedProjects.forEach(project => {
                parsedFolder.projects.push({
                    id: project.id.primaryKey,
                    name: project.name,
                    status: project.status.name,
                    completed: project.completed
                });
            });
        }

        return parsedFolder;
    };

    /**
     * Calculate aggregate metrics for a folder
     * Includes project counts, task statistics, and completion rates
     * @param {Folder} folder - The folder to analyze
     * @returns {Object} Metrics object
     */
    lib.calculateFolderMetrics = function(folder) {
        if (!folder) {
            return {
                projectCount: 0,
                activeProjects: 0,
                onHoldProjects: 0,
                completedProjects: 0,
                totalTasks: 0,
                activeTasks: 0,
                completedTasks: 0,
                completionRate: 0
            };
        }

        const projects = folder.flattenedProjects || [];
        const tasks = folder.flattenedTasks || [];

        // Project statistics
        const activeProjects = projects.filter(p => !p.completed && p.status.name === "active").length;
        const onHoldProjects = projects.filter(p => !p.completed && p.status.name === "on hold").length;
        const completedProjects = projects.filter(p => p.completed).length;
        const droppedProjects = projects.filter(p => p.status.name === "dropped").length;
        const totalProjects = projects.length;

        // Task statistics (active tasks only from active projects)
        const activeTasks = tasks.filter(t => !t.completed && !t.dropped).length;
        const completedTasks = tasks.filter(t => t.completed).length;
        const totalTasks = tasks.length;

        // Calculate completion rate (avoid division by zero)
        const completableProjects = totalProjects - droppedProjects;
        const completionRate = completableProjects > 0
            ? Math.round((completedProjects / completableProjects) * 100)
            : 0;

        // Calculate task completion rate
        const taskCompletionRate = totalTasks > 0
            ? Math.round((completedTasks / totalTasks) * 100)
            : 0;

        return {
            projectCount: totalProjects,
            activeProjects: activeProjects,
            onHoldProjects: onHoldProjects,
            completedProjects: completedProjects,
            droppedProjects: droppedProjects,
            totalTasks: totalTasks,
            activeTasks: activeTasks,
            completedTasks: completedTasks,
            completionRate: completionRate,
            taskCompletionRate: taskCompletionRate
        };
    };

    /**
     * Assess folder health based on metrics
     * Returns a qualitative health assessment
     * @param {Object} metrics - Metrics from calculateFolderMetrics
     * @returns {string} Health status: "Excellent" | "Good" | "Fair" | "Needs Attention"
     */
    lib.getFolderHealth = function(metrics) {
        if (!metrics || metrics.projectCount === 0) {
            return "Empty";
        }

        const { activeProjects, completionRate, activeTasks } = metrics;

        // Excellent: High completion rate, healthy project count, making progress
        if (completionRate >= 50 && activeProjects > 0 && activeProjects <= 10) {
            return "Excellent";
        }

        // Good: Reasonable completion rate, manageable active projects
        if (completionRate >= 30 && activeProjects > 0 && activeProjects <= 15) {
            return "Good";
        }

        // Fair: Some completion, but many active projects or low completion
        if (completionRate >= 15 || (activeProjects > 0 && activeProjects <= 20)) {
            return "Fair";
        }

        // Needs Attention: Low completion, too many active projects, or stagnation
        return "Needs Attention";
    };

    /**
     * Get all folders from the database for folder selection
     * Returns array of folders suitable for form options
     * @returns {Array} Array of folder objects with id and name
     */
    lib.getAllFolders = function() {
        const allFolders = flattenedFolders || [];

        return allFolders.map(folder => ({
            id: folder.id.primaryKey,
            name: folder.name,
            folder: folder  // Keep reference to actual folder object
        }));
    };

    /**
     * Parse entire folder hierarchy starting from root
     * Useful for "All Folders" analysis
     * @param {boolean} includeProjects - Whether to include project details
     * @returns {Array} Array of parsed root-level folders
     */
    lib.parseAllFolders = function(includeProjects = false) {
        const rootFolders = folders || [];

        return rootFolders.map(folder =>
            this.parseFolder(folder, 0, true, includeProjects)
        );
    };

    /**
     * Calculate aggregate metrics across multiple folders
     * Useful for executive summary statistics
     * @param {Array} parsedFolders - Array of parsed folder objects
     * @returns {Object} Aggregated metrics
     */
    lib.aggregateMetrics = function(parsedFolders) {
        if (!parsedFolders || parsedFolders.length === 0) {
            return {
                totalFolders: 0,
                totalProjects: 0,
                totalActiveProjects: 0,
                totalTasks: 0,
                totalActiveTasks: 0,
                overallCompletionRate: 0
            };
        }

        let totalFolders = 0;
        let totalProjects = 0;
        let totalActiveProjects = 0;
        let totalCompletedProjects = 0;
        let totalTasks = 0;
        let totalActiveTasks = 0;
        let totalCompletedTasks = 0;

        // Recursive function to aggregate metrics from nested folders
        const aggregateFolder = (folder) => {
            totalFolders++;
            totalProjects += folder.metrics.projectCount;
            totalActiveProjects += folder.metrics.activeProjects;
            totalCompletedProjects += folder.metrics.completedProjects;
            totalTasks += folder.metrics.totalTasks;
            totalActiveTasks += folder.metrics.activeTasks;
            totalCompletedTasks += folder.metrics.completedTasks;

            // Recursively aggregate subfolders
            if (folder.subfolders && folder.subfolders.length > 0) {
                folder.subfolders.forEach(aggregateFolder);
            }
        };

        parsedFolders.forEach(aggregateFolder);

        // Calculate overall completion rate
        const overallCompletionRate = totalProjects > 0
            ? Math.round((totalCompletedProjects / totalProjects) * 100)
            : 0;

        return {
            totalFolders: totalFolders,
            totalProjects: totalProjects,
            totalActiveProjects: totalActiveProjects,
            totalCompletedProjects: totalCompletedProjects,
            totalTasks: totalTasks,
            totalActiveTasks: totalActiveTasks,
            totalCompletedTasks: totalCompletedTasks,
            overallCompletionRate: overallCompletionRate
        };
    };

    return lib;
})();
