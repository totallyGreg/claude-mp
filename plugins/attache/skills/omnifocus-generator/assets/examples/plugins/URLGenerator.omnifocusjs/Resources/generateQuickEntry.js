/**
 * Generate Quick Entry URL Action
 *
 * Shows a form to create a quick task entry URL for sharing.
 */

(() => {
    // Load simplified urlBuilder
    function loadURLBuilder() {
        return {
            buildTaskURL: function(params) {
                if (!params.name) throw new Error("Task name is required");

                const queryParams = { name: params.name };
                if (params.project) queryParams.project = params.project;
                if (params.tags) queryParams.tags = params.tags;
                if (params.due) queryParams.due = params.due;
                if (params.flagged) queryParams.flagged = 'true';
                if (params.note) queryParams.note = params.note;
                if (params.autosave) queryParams.autosave = 'true';

                const queryString = Object.keys(queryParams)
                    .map(key => `${key}=${encodeURIComponent(queryParams[key])}`)
                    .join('&');

                return `omnifocus:///add?${queryString}`;
            }
        };
    }

    const action = new PlugIn.Action(async function(selection, sender) {
        const urlBuilder = loadURLBuilder();

        // Show form to collect task details
        const form = new Form();
        form.addField(new Form.Field.String("name", "Task Name", null));
        form.addField(new Form.Field.String("project", "Project (optional)", null));
        form.addField(new Form.Field.String("tags", "Tags (comma-separated)", null));
        form.addField(new Form.Field.String("note", "Note (optional)", null));
        form.addField(new Form.Field.Checkbox("flagged", "Flagged", false));
        form.addField(new Form.Field.Checkbox("autosave", "Auto-save (no confirmation)", false));

        const formPrompt = new FormPrompt("Generate Task URL", form);
        const formResult = await formPrompt.show("Generate", "Cancel");

        if (!formResult) {
            return; // Cancelled
        }

        const values = formResult.values;

        if (!values.name) {
            const alert = new Alert("Error", "Task name is required.");
            await alert.show();
            return;
        }

        // Build parameters
        const params = {
            name: values.name
        };

        if (values.project) params.project = values.project;
        if (values.tags) params.tags = values.tags;
        if (values.note) params.note = values.note;
        if (values.flagged) params.flagged = true;
        if (values.autosave) params.autosave = true;

        // Generate URL
        const url = urlBuilder.buildTaskURL(params);

        // Copy to clipboard
        Pasteboard.general.string = url;

        // Show result
        const alert = new Alert(
            "URL Generated",
            `URL copied to clipboard!\n\nYou can now:\n• Paste into emails\n• Share with others\n• Create bookmarks\n• Use in automation\n\nURL:\n${url}`
        );
        await alert.show();
    });

    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
