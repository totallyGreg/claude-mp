/**
 * Template Engine Library for OmniFocus
 *
 * Provides template loading, variable substitution, and bulk task creation
 * functionality for OmniFocus automation.
 *
 * Usage (in OmniFocus plugin):
 *   // In manifest.json, declare as library:
 *   "libraries": ["templateEngine"]
 *
 *   // In action script:
 *   const engine = this.plugIn.library("templateEngine");
 *   const result = engine.createFromTemplate(doc, "weekly_review", {WEEK: "2025-W01"});
 *
 * Usage (in Omni Automation console):
 *   // Load library code and evaluate
 *   const engine = <paste this code>;
 *   const result = engine.createFromTemplate(document, "weekly_review", {});
 */

(() => {
    const templateEngine = new PlugIn.Library(function() {
        const lib = this;

        /**
         * Load templates from JSON file
         * @param {string} templatesPath - Path to templates JSON file (optional)
         * @returns {Object} Templates object keyed by template name
         * @throws {Error} If templates file not found or invalid
         */
        lib.loadTemplates = function(templatesPath) {
            // If no path provided, try default location
            if (!templatesPath) {
                // For plugins, look in Resources/templates/
                // For standalone scripts, construct relative path
                const fm = $.NSFileManager.defaultManager;

                // Try plugin bundle first
                const bundlePath = this.plugIn ? this.plugIn.resourceNamed("templates/task_templates.json") : null;
                if (bundlePath) {
                    templatesPath = bundlePath.toString();
                } else {
                    // Fall back to script-relative path
                    const scriptPath = $.NSString.alloc.initWithUTF8String($.getenv('_')).stringByDeletingLastPathComponent;
                    templatesPath = scriptPath.stringByAppendingPathComponent('../assets/templates/task_templates.json').js;
                }
            }

            const fileManager = $.NSFileManager.defaultManager;
            const exists = fileManager.fileExistsAtPath(templatesPath);

            if (!exists) {
                throw new Error(`Templates file not found at: ${templatesPath}`);
            }

            const data = $.NSData.dataWithContentsOfFile(templatesPath);
            if (!data) {
                throw new Error('Could not read templates file');
            }

            const jsonString = $.NSString.alloc.initWithDataEncoding(data, $.NSUTF8StringEncoding).js;
            return JSON.parse(jsonString);
        };

        /**
         * Parse variable arguments from command-line style args
         * @param {Array<string>} args - Array of arguments (e.g., ["--VAR1", "value1", "--VAR2", "value2"])
         * @returns {Object} Variables object keyed by variable name
         */
        lib.parseVariables = function(args) {
            const variables = {};

            for (let i = 0; i < args.length; i += 2) {
                if (args[i].startsWith('--')) {
                    const key = args[i].substring(2);
                    const value = args[i + 1] || '';
                    variables[key] = value;
                }
            }

            return variables;
        };

        /**
         * Substitute {{VARIABLE}} placeholders in template with actual values
         * @param {Object} template - Template object with string values containing {{VARIABLE}} placeholders
         * @param {Object} variables - Variables object keyed by variable name
         * @returns {Object} Template with all placeholders replaced
         */
        lib.substituteVariables = function(template, variables) {
            const result = {};

            for (const key in template) {
                let value = template[key];

                if (typeof value === 'string') {
                    // Replace all {{VARIABLE}} placeholders
                    value = value.replace(/\{\{(\w+)\}\}/g, (match, varName) => {
                        return variables[varName] || match;
                    });
                } else if (Array.isArray(value)) {
                    // Handle arrays (like tags)
                    value = value.map(item => {
                        if (typeof item === 'string') {
                            return item.replace(/\{\{(\w+)\}\}/g, (match, varName) => {
                                return variables[varName] || match;
                            });
                        }
                        return item;
                    });
                }

                result[key] = value;
            }

            return result;
        };

        /**
         * Extract variable names from template
         * @param {Object} template - Template object
         * @returns {Array<string>} Array of unique variable names found in template
         */
        lib.extractVariables = function(template) {
            const variables = new Set();

            for (const key in template) {
                const value = template[key];
                if (typeof value === 'string') {
                    const matches = value.matchAll(/\{\{(\w+)\}\}/g);
                    for (const match of matches) {
                        variables.add(match[1]);
                    }
                } else if (Array.isArray(value)) {
                    value.forEach(item => {
                        if (typeof item === 'string') {
                            const matches = item.matchAll(/\{\{(\w+)\}\}/g);
                            for (const match of matches) {
                                variables.add(match[1]);
                            }
                        }
                    });
                }
            }

            return Array.from(variables);
        };

        /**
         * Parse time estimate string to minutes
         * @param {string|number} estimate - Time estimate ("30m", "2h", "1h30m", or number)
         * @returns {number} Total minutes
         */
        lib.parseEstimate = function(estimate) {
            if (typeof estimate === 'number') {
                return estimate;
            }

            let totalMinutes = 0;
            const hourMatch = estimate.match(/(\d+)h/);
            const minuteMatch = estimate.match(/(\d+)m/);

            if (hourMatch) {
                totalMinutes += parseInt(hourMatch[1]) * 60;
            }
            if (minuteMatch) {
                totalMinutes += parseInt(minuteMatch[1]);
            }

            return totalMinutes;
        };

        /**
         * Create OmniFocus task from template data
         * @param {Document} doc - OmniFocus document
         * @param {Object} taskData - Template data with variables substituted
         * @returns {Object} Result object with success status and created task info
         */
        lib.createTaskFromTemplate = function(doc, taskData) {
            const app = Application('OmniFocus');

            // Create the task
            const task = app.Task({
                name: taskData.name
            });

            // Set note if provided
            if (taskData.note) {
                task.note = taskData.note;
            }

            // Set flagged status
            if (taskData.flagged) {
                task.flagged = taskData.flagged;
            }

            // Set estimate
            if (taskData.estimate) {
                const minutes = this.parseEstimate(taskData.estimate);
                if (minutes > 0) {
                    task.estimatedMinutes = minutes;
                }
            }

            // Set sequential
            if (taskData.sequential !== undefined) {
                task.sequential = taskData.sequential;
            }

            // Handle project
            let project = null;
            if (taskData.project) {
                // Find existing project
                const projects = doc.flattenedProjects;
                project = projects.find(p => p.name === taskData.project);

                // Create project if needed and create_project flag is set
                if (!project && taskData.create_project) {
                    project = app.Project({
                        name: taskData.project
                    });
                    doc.projects.push(project);
                }
            }

            // Add task to project or inbox
            if (project) {
                project.tasks.push(task);
            } else {
                doc.inboxTasks.push(task);
            }

            // Handle tags
            if (taskData.tags && taskData.tags.length > 0) {
                const allTags = doc.flattenedTags;

                taskData.tags.forEach(tagName => {
                    let tag = allTags.find(t => t.name === tagName);

                    // Create tag if it doesn't exist
                    if (!tag) {
                        tag = app.Tag({
                            name: tagName
                        });
                        doc.tags.push(tag);
                    }

                    task.addTag(tag);
                });
            }

            // Handle defer date if specified as days before meeting
            if (taskData.defer_days_before_meeting && taskData.due) {
                const dueDate = new Date(taskData.due);
                const deferDate = new Date(dueDate);
                deferDate.setDate(deferDate.getDate() - taskData.defer_days_before_meeting);
                task.deferDate = deferDate;
            }

            // Set due date if provided
            if (taskData.due) {
                task.dueDate = new Date(taskData.due);
            }

            // Set defer date if provided (overrides defer_days_before_meeting)
            if (taskData.defer) {
                task.deferDate = new Date(taskData.defer);
            }

            return {
                success: true,
                message: `Created task: ${taskData.name}`,
                task: {
                    id: task.id,
                    name: task.name,
                    project: project ? project.name : 'Inbox',
                    tags: taskData.tags || [],
                    note: taskData.note || ''
                }
            };
        };

        /**
         * Create task from named template with variable substitution
         * @param {Document} doc - OmniFocus document
         * @param {string} templateName - Name of template to use
         * @param {Object} variables - Variables to substitute in template
         * @param {string} templatesPath - Optional path to templates file
         * @returns {Object} Result object with success status and created task info
         * @throws {Error} If template not found
         */
        lib.createFromTemplate = function(doc, templateName, variables = {}, templatesPath = null) {
            // Load templates
            const templates = this.loadTemplates(templatesPath);

            // Check if template exists
            if (!templates[templateName]) {
                throw new Error(`Template '${templateName}' not found. Available: ${Object.keys(templates).join(', ')}`);
            }

            // Get template and substitute variables
            const template = templates[templateName];
            const taskData = this.substituteVariables(template, variables);

            // Create task
            return this.createTaskFromTemplate(doc, taskData);
        };

        /**
         * List all available templates
         * @param {string} templatesPath - Optional path to templates file
         * @returns {Object} Result object with array of template info
         */
        lib.listTemplates = function(templatesPath = null) {
            const templates = this.loadTemplates(templatesPath);
            const list = [];

            for (const name in templates) {
                const template = templates[name];
                list.push({
                    name: name,
                    title: template.name,
                    project: template.project || 'Inbox',
                    tags: template.tags || [],
                    estimate: template.estimate || 'N/A',
                    variables: this.extractVariables(template)
                });
            }

            return {
                success: true,
                count: list.length,
                templates: list
            };
        };

        /**
         * Get template info without creating task
         * @param {string} templateName - Name of template
         * @param {string} templatesPath - Optional path to templates file
         * @returns {Object} Template info object
         * @throws {Error} If template not found
         */
        lib.getTemplateInfo = function(templateName, templatesPath = null) {
            const templates = this.loadTemplates(templatesPath);

            if (!templates[templateName]) {
                throw new Error(`Template '${templateName}' not found`);
            }

            const template = templates[templateName];
            return {
                name: templateName,
                data: template,
                variables: this.extractVariables(template)
            };
        };

        return lib;
    });

    return templateEngine;
})();
