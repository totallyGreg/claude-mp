#!/usr/bin/env osascript -l JavaScript

/**
 * Create OmniFocus tasks from templates
 *
 * Usage:
 *   osascript -l JavaScript create_from_template.js <template_name> [variables...]
 *
 * Examples:
 *   osascript -l JavaScript create_from_template.js weekly_review
 *   osascript -l JavaScript create_from_template.js meeting_prep --MEETING_NAME "Team Standup" --PROJECT_NAME "Work"
 *   osascript -l JavaScript create_from_template.js project_kickoff --PROJECT_NAME "Website Redesign"
 */

ObjC.import('Foundation');
ObjC.import('stdlib');

function run(argv) {
    try {
        // Parse arguments
        if (argv.length < 1) {
            return JSON.stringify({
                success: false,
                error: "Usage: create_from_template.js <template_name> [--VAR value ...]",
                available_templates: getAvailableTemplates()
            }, null, 2);
        }

        const templateName = argv[0];
        const variables = parseVariables(argv.slice(1));

        // Load templates
        const templates = loadTemplates();

        if (!templates[templateName]) {
            return JSON.stringify({
                success: false,
                error: `Template '${templateName}' not found`,
                available_templates: Object.keys(templates)
            }, null, 2);
        }

        // Get template
        const template = templates[templateName];

        // Substitute variables
        const taskData = substituteVariables(template, variables);

        // Create task in OmniFocus
        const result = createTaskFromTemplate(taskData);

        return JSON.stringify(result, null, 2);

    } catch (error) {
        return JSON.stringify({
            success: false,
            error: error.message || error.toString()
        }, null, 2);
    }
}

function loadTemplates() {
    const scriptPath = $.NSString.alloc.initWithUTF8String($.getenv('_')).stringByDeletingLastPathComponent;
    const templatesPath = scriptPath.stringByAppendingPathComponent('../assets/templates/task_templates.json');

    const fileManager = $.NSFileManager.defaultManager;
    const exists = fileManager.fileExistsAtPath(templatesPath);

    if (!exists) {
        throw new Error(`Templates file not found at: ${templatesPath.js}`);
    }

    const data = $.NSData.dataWithContentsOfFile(templatesPath);
    if (!data) {
        throw new Error('Could not read templates file');
    }

    const jsonString = $.NSString.alloc.initWithDataEncoding(data, $.NSUTF8StringEncoding).js;
    return JSON.parse(jsonString);
}

function parseVariables(args) {
    const variables = {};

    for (let i = 0; i < args.length; i += 2) {
        if (args[i].startsWith('--')) {
            const key = args[i].substring(2);
            const value = args[i + 1] || '';
            variables[key] = value;
        }
    }

    return variables;
}

function substituteVariables(template, variables) {
    const result = {};

    for (const key in template) {
        let value = template[key];

        if (typeof value === 'string') {
            // Replace all {{VARIABLE}} placeholders
            value = value.replace(/\{\{(\w+)\}\}/g, (match, varName) => {
                return variables[varName] || match;
            });
        }

        result[key] = value;
    }

    return result;
}

function createTaskFromTemplate(taskData) {
    const app = Application.currentApplication();
    app.includeStandardAdditions = true;

    const omniFocus = Application('OmniFocus');
    const doc = omniFocus.defaultDocument;

    // Create the task
    const task = omniFocus.Task({
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
        const minutes = parseEstimate(taskData.estimate);
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
        const projects = doc.flattenedProjects();
        project = projects.find(p => p.name() === taskData.project);

        // Create project if needed and create_project flag is set
        if (!project && taskData.create_project) {
            project = omniFocus.Project({
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
        const allTags = doc.flattenedTags();

        taskData.tags.forEach(tagName => {
            let tag = allTags.find(t => t.name() === tagName);

            // Create tag if it doesn't exist
            if (!tag) {
                tag = omniFocus.Tag({
                    name: tagName
                });
                doc.flattenedTags.push(tag);
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

    // Set defer date if provided
    if (taskData.defer) {
        task.deferDate = new Date(taskData.defer);
    }

    return {
        success: true,
        message: `Created task: ${taskData.name}`,
        task: {
            id: task.id(),
            name: task.name(),
            project: project ? project.name() : 'Inbox',
            tags: taskData.tags || [],
            note: taskData.note || ''
        }
    };
}

function parseEstimate(estimate) {
    // Parse estimate strings like "30m", "2h", "1h30m"
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
}

function getAvailableTemplates() {
    try {
        const templates = loadTemplates();
        return Object.keys(templates);
    } catch (e) {
        return [];
    }
}

// List templates command
function listTemplates() {
    const templates = loadTemplates();
    const list = [];

    for (const name in templates) {
        const template = templates[name];
        list.push({
            name: name,
            title: template.name,
            project: template.project || 'Inbox',
            tags: template.tags || [],
            estimate: template.estimate || 'N/A',
            variables: extractVariables(template)
        });
    }

    return {
        success: true,
        templates: list
    };
}

function extractVariables(template) {
    const variables = new Set();

    for (const key in template) {
        const value = template[key];
        if (typeof value === 'string') {
            const matches = value.matchAll(/\{\{(\w+)\}\}/g);
            for (const match of matches) {
                variables.add(match[1]);
            }
        }
    }

    return Array.from(variables);
}

// Handle special commands
if ($.NSProcessInfo.processInfo.arguments.js.length > 4) {
    const firstArg = $.NSProcessInfo.processInfo.arguments.js[4];
    if (firstArg === '--list') {
        const result = listTemplates();
        console.log(JSON.stringify(result, null, 2));
        $.exit(0);
    }
}
