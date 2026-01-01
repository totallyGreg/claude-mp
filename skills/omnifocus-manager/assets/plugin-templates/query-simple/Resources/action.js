/**
 * {{PLUGIN_NAME}} - OmniFocus Plugin
 *
 * {{DESCRIPTION}}
 */

(() => {
    const action = new PlugIn.Action(function(selection, sender) {
        try {
            // Access OmniFocus data using global variables
            const tasks = flattenedTasks;
            const projects = flattenedProjects;

            // Example: Count active tasks
            const activeTasks = tasks.filter(t => !t.completed && !t.dropped);

            // Build message
            let message = `Found ${activeTasks.length} active tasks\n\n`;

            // Add your custom logic here
            // Examples:
            // - Filter tasks by specific criteria
            // - Group tasks by project/tag
            // - Calculate statistics
            // - Format display message

            // Display alert
            const alert = new Alert('{{PLUGIN_NAME}}', message);
            alert.show();

        } catch (error) {
            console.error('Error:', error);
            new Alert('Error', error.message).show();
        }
    });

    // Always enable this action
    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
