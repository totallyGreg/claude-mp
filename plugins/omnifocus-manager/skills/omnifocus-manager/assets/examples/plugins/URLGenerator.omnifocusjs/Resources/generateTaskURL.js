/**
 * Generate Task URL from Selection Action
 *
 * Creates an omnifocus:// URL for selected tasks that can be shared.
 * Demonstrates loading shared urlBuilder library in Omni Automation.
 *
 * Note: urlBuilder is in shared/ directory, so we load it via eval.
 */

(() => {
    // Load urlBuilder library (shared library, not PlugIn.Library)
    function loadURLBuilder() {
        // In a real plugin, you would copy urlBuilder.js to Resources/ and load it
        // For this example, we'll create a simplified version inline
        return {
            buildTaskURL: function(params) {
                if (!params.name) throw new Error("Task name is required");

                const queryParams = { name: params.name };
                if (params.project) queryParams.project = params.project;
                if (params.tags) {
                    queryParams.tags = Array.isArray(params.tags)
                        ? params.tags.join(',')
                        : params.tags;
                }
                if (params.due) queryParams.due = params.due;
                if (params.flagged) queryParams.flagged = 'true';
                if (params.note) queryParams.note = params.note;

                const queryString = Object.keys(queryParams)
                    .map(key => `${key}=${encodeURIComponent(queryParams[key])}`)
                    .join('&');

                return `omnifocus:///add?${queryString}`;
            },

            buildMarkdownLink: function(name, params) {
                const url = this.buildTaskURL(params);
                return `[${name}](${url})`;
            }
        };
    }

    const action = new PlugIn.Action(async function(selection, sender) {
        const urlBuilder = loadURLBuilder();

        if (selection.tasks.length === 0) {
            const alert = new Alert("No Selection", "Please select a task first.");
            await alert.show();
            return;
        }

        const task = selection.tasks[0];

        // Build URL from task
        const params = {
            name: task.name,
            note: task.note || undefined,
            flagged: task.flagged || undefined
        };

        if (task.containingProject) {
            params.project = task.containingProject.name;
        }

        if (task.tags.length > 0) {
            params.tags = task.tags.map(t => t.name);
        }

        if (task.dueDate) {
            const due = task.dueDate;
            params.due = `${due.getFullYear()}-${String(due.getMonth() + 1).padStart(2, '0')}-${String(due.getDate()).padStart(2, '0')}`;
        }

        // Generate URL and Markdown link
        const url = urlBuilder.buildTaskURL(params);
        const markdown = urlBuilder.buildMarkdownLink(task.name, params);

        // Copy to clipboard
        Pasteboard.general.string = url;

        // Show result
        const alert = new Alert(
            "URL Generated",
            `URL copied to clipboard!\n\nTask: ${task.name}\n\nURL:\n${url}\n\nMarkdown:\n${markdown}`
        );
        await alert.show();
    });

    action.validate = function(selection, sender) {
        return selection.tasks.length > 0;
    };

    return action;
})();
