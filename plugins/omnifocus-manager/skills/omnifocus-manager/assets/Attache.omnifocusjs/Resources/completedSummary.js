/**
 * Completed Summary - Show accomplished work with period selection
 *
 * Displays completed tasks grouped by project for today, this week,
 * or this month. Absorbs CompletedTasksSummary plugin functionality.
 *
 * Requirements:
 * - OmniFocus 4.8+
 */

(() => {
    function section(title) {
        return `── ${title}`;
    }

    const action = new PlugIn.Action(async function(selection, sender) {
        try {
            const metrics = this.plugIn.library("taskMetrics");

            // Period selection form
            const form = new Form();
            const periodField = new Form.Field.Option(
                "period", "Time Period",
                ["today", "week", "month"],
                ["Today", "This Week (7 days)", "This Month (30 days)"],
                "today"
            );
            form.addField(periodField);

            const formResult = await form.show("Completed Summary", "Show");
            if (!formResult) return;

            const period = formResult.values["period"];

            // Get completed tasks for selected period
            let tasks;
            let periodLabel;
            switch (period) {
                case "today":
                    tasks = metrics.getCompletedToday();
                    periodLabel = "Today";
                    break;
                case "week":
                    tasks = metrics.getCompletedThisWeek();
                    periodLabel = "This Week";
                    break;
                case "month":
                    tasks = metrics.getCompletedThisMonth();
                    periodLabel = "This Month";
                    break;
            }

            if (!tasks || tasks.length === 0) {
                const alert = new Alert("Completed Summary",
                    `No tasks completed ${periodLabel.toLowerCase()}.`
                );
                alert.addOption("OK");
                await alert.show();
                return;
            }

            // Group by project
            const byProject = {};
            tasks.forEach(t => {
                const proj = t.project || "Inbox";
                if (!byProject[proj]) byProject[proj] = [];
                byProject[proj].push(t);
            });

            // Sort project names (Inbox last)
            const projectNames = Object.keys(byProject).sort((a, b) => {
                if (a === "Inbox") return 1;
                if (b === "Inbox") return -1;
                return a.localeCompare(b);
            });

            // Format message
            const dateStr = new Date().toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            let message = `Completed ${periodLabel}: ${tasks.length} task${tasks.length !== 1 ? 's' : ''}\n`;
            message += `${dateStr}\n\n`;

            projectNames.forEach(proj => {
                const projectTasks = byProject[proj];
                message += `${section(`${proj} (${projectTasks.length})`)}\n`;
                projectTasks.forEach(t => {
                    const time = t.completionTime ? `${t.completionTime} - ` : "";
                    message += `  · ${time}${t.name}\n`;
                });
                message += "\n";
            });

            const alert = new Alert("Wins Report", message);
            alert.addOption("Copy to Clipboard");
            alert.addOption("Done");
            const choice = await alert.show();

            if (choice === 0) {
                Pasteboard.general.string = message;
            }

        } catch (error) {
            console.error("Completed Summary error:", error);
            const errorAlert = new Alert("Completed Summary Error", error.message);
            errorAlert.show();
        }
    });

    // Always available — no FM required
    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
