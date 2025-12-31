/**
 * Flag All Overdue Tasks Action
 *
 * Demonstrates using patterns library for batch operations.
 */

(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        // Load patterns library
        const patterns = this.plugIn.library("patterns");

        // First, do a dry run to preview changes
        const preview = await patterns.batchUpdate({
            selector: { filter: "overdue" },
            updates: { flagged: true },
            dryRun: true
        });

        if (!preview.success) {
            const alert = new Alert("Error", preview.error.message);
            await alert.show();
            return;
        }

        if (preview.matched === 0) {
            const alert = new Alert("No Overdue Tasks", "You have no overdue tasks!");
            await alert.show();
            return;
        }

        // Show confirmation
        const confirmAlert = new Alert(
            "Confirm Bulk Operation",
            `This will flag ${preview.matched} overdue tasks.\n\nDo you want to continue?`
        );
        confirmAlert.addOption("Flag Tasks");
        confirmAlert.addOption("Cancel");

        const buttonIndex = await confirmAlert.show();

        if (buttonIndex === 1) {
            return; // Cancelled
        }

        // Execute the batch operation
        const result = await patterns.batchUpdate({
            selector: { filter: "overdue" },
            updates: { flagged: true },
            dryRun: false
        });

        if (result.success) {
            const successAlert = new Alert(
                "Batch Operation Complete",
                `Successfully flagged ${result.updated} overdue tasks.`
            );
            await successAlert.show();
        } else {
            const errorAlert = new Alert("Operation Failed", result.error.message);
            await errorAlert.show();
        }
    });

    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
