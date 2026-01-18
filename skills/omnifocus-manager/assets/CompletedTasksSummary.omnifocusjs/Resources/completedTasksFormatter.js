/**
 * Completed Tasks Formatter Library
 *
 * Formats completed tasks into markdown with project grouping.
 *
 * Usage in plugin actions:
 *   const formatter = this.plugIn.library("completedTasksFormatter");
 *   const markdown = formatter.formatAsMarkdown(tasks);
 *
 * @version 1.0.0
 */

(() => {
	var lib = new PlugIn.Library(new Version("1.0"));

	/**
	 * Format completed tasks grouped by project as markdown
	 * @param {Array} tasks - Array of completed task objects
	 * @returns {string} Formatted markdown string
	 */
	lib.formatAsMarkdown = function(tasks) {
		if (!tasks || tasks.length === 0) {
			return "# Daily Completed Tasks\n\nNo tasks completed today.";
		}

		const dateStr = new Date().toLocaleDateString('en-US', {
			weekday: 'long',
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});

		let markdown = `# Daily Completed Tasks\n\n`;
		markdown += `**Date:** ${dateStr}\n`;
		markdown += `**Total Tasks Completed:** ${tasks.length}\n\n`;
		markdown += `---\n\n`;

		// Group by project
		const byProject = this.groupByProject(tasks);

		// Sort project names (Inbox last)
		const projectNames = Object.keys(byProject).sort((a, b) => {
			if (a === 'Inbox') return 1;
			if (b === 'Inbox') return -1;
			return a.localeCompare(b);
		});

		// Format each project section
		projectNames.forEach(projectName => {
			markdown += `## ${projectName}\n\n`;

			// Sort tasks by completion time
			const projectTasks = byProject[projectName].sort((a, b) =>
				a.completionDate - b.completionDate
			);

			projectTasks.forEach(task => {
				markdown += `- **${task.completionTime}** - ${task.name}\n`;
			});

			markdown += `\n`;
		});

		return markdown;
	};

	/**
	 * Group tasks by project
	 * @param {Array} tasks - Array of task objects
	 * @returns {Object} Tasks grouped by project name
	 */
	lib.groupByProject = function(tasks) {
		const grouped = {};

		tasks.forEach(task => {
			const projectName = task.project || 'Inbox';
			if (!grouped[projectName]) {
				grouped[projectName] = [];
			}
			grouped[projectName].push(task);
		});

		return grouped;
	};

	return lib;
})();
