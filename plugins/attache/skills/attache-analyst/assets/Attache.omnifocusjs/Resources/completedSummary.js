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
            // @ts-ignore — 6th arg (nullOptionTitle) is optional at runtime
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

            // [P] Apply path — let the user capture follow-up tasks triggered
            // by any of these completions. Unlike analyzeSelected /
            // analyzeHierarchy / weeklyReview, completedSummary doesn't run
            // through Foundation Models — there are no per-item AI suggestions
            // to accept/reject. The natural shape here is bulk text-capture:
            // one Form with a text field per recent completion, user fills in
            // any rows that triggered follow-ups, we createTask the non-empty
            // ones. The applyForm helper (checkbox-only API) isn't a fit; we
            // route directly to ofoCore.
            const ofoCore = this.plugIn.library("ofoCore");

            const alert = new Alert("Wins Report", message);
            alert.addOption("Copy to Clipboard");
            if (ofoCore) {
                alert.addOption("Capture Follow-ups…");
            }
            alert.addOption("Done");
            const choice = await alert.show();

            if (choice === 0) {
                Pasteboard.general.string = message;
            } else if (ofoCore && choice === 1) {
                await captureFollowUps(tasks, ofoCore);
            }

        } catch (error) {
            console.error("Completed Summary error:", error);
            const errorAlert = new Alert("Completed Summary Error", error.message);
            errorAlert.show();
        }
    });

    /**
     * Show a single bulk Form with one text field per recent completion.
     * For any non-empty fields, createTask via ofoCore (routed to the
     * completion's original project, or Inbox if "Inbox"/unknown). Capped at
     * MAX_FU rows to keep the Form usable — when truncated the title
     * communicates the cap so the user knows older completions were dropped.
     */
    async function captureFollowUps(completedTasks, ofoCore) {
        const MAX_FU = 15;
        const subset = completedTasks.slice(0, MAX_FU);
        const truncated = completedTasks.length > MAX_FU;

        const form = new Form();
        subset.forEach((t, i) => {
            const label = t.project
                ? `${t.name} [${t.project}]`
                : t.name;
            form.addField(new Form.Field.String(`fu_${i}`, label, ""));
        });

        const title = truncated
            ? `Capture Follow-ups (top ${MAX_FU} of ${completedTasks.length})`
            : "Capture Follow-ups";
        const result = await form.show(title, "Create");
        if (!result) return;

        let created = 0;
        const issues = [];
        for (let i = 0; i < subset.length; i++) {
            const text = String(result.values[`fu_${i}`] || "").trim();
            if (!text) continue;
            const args = { name: text };
            const projName = subset[i].project;
            if (projName && projName !== "Inbox") {
                args.project = projName;
            }
            const res = ofoCore.createTask(args);
            if (!res.success) {
                issues.push(`${text}: ${res.error || 'createTask failed'}`);
                continue;
            }
            created++;
        }

        let summary = `Created ${created} follow-up task${created === 1 ? '' : 's'}.`;
        if (truncated) {
            summary += `\n(Showed top ${MAX_FU} of ${completedTasks.length} completions.)`;
        }
        if (issues.length > 0) {
            summary += `\n\nIssues:\n  · ${issues.join('\n  · ')}`;
        }
        new Alert("Wins Report — Follow-ups", summary).show();
    }

    // Always available — no FM required
    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
