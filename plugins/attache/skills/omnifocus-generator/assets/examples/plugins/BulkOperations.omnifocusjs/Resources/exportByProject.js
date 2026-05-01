/**
 * Export Project Tasks Action
 *
 * Demonstrates using patterns library for query+export workflow.
 */

(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        // Get project name from selection or ask user
        let projectName = null;

        if (selection.projects.length === 1) {
            projectName = selection.projects[0].name;
        } else {
            // Ask user for project name
            const form = new Form();
            form.addField(new Form.Field.String("project", "Project Name", null));

            const formPrompt = new FormPrompt("Export Project Tasks", form);
            const formResult = await formPrompt.show("Export", "Cancel");

            if (!formResult || !formResult.values.project) {
                return; // Cancelled
            }

            projectName = formResult.values.project;
        }

        // Use patterns library to query and export
        const patterns = this.plugIn.library("patterns");

        const result = await patterns.queryAndExport({
            query: {
                filter: "project",
                projectName: projectName
            },
            transform: "detailed",
            export: {
                format: "markdown",
                destination: "clipboard"
            }
        });

        if (result.success) {
            const alert = new Alert(
                "Export Complete",
                `Exported ${result.count} tasks from project "${projectName}" to clipboard as Markdown.`
            );
            await alert.show();
        } else {
            const alert = new Alert("Export Failed", result.error.message);
            await alert.show();
        }
    });

    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
