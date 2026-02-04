/**
 * Task Metrics Library
 *
 * Reusable functions for collecting task data from OmniFocus.
 *
 * Usage in plugin actions:
 *   const metrics = this.plugIn.library("taskMetrics");
 *   const tasks = metrics.getTodayTasks();
 */

(() => {
	var lib = new PlugIn.Library(new Version("3.0"));

	lib.getTodayTasks = function() {
		const tasks = flattenedTasks;

		const today = new Date();
		today.setHours(0, 0, 0, 0);
		const tomorrow = new Date(today);
		tomorrow.setDate(tomorrow.getDate() + 1);

		const todayTasks = tasks.filter(task => {
			if (task.completed || task.dropped) return false;

			const due = task.dueDate;
			const defer = task.deferDate;

			const isDueToday = due && due >= today && due < tomorrow;
			const isDeferredToday = defer && defer >= today && defer < tomorrow;

			return isDueToday || isDeferredToday;
		});

		return todayTasks.map(lib.normalizeTask.bind(lib));
	};

	lib.getOverdueTasks = function() {
		const tasks = flattenedTasks;

		const today = new Date();
		today.setHours(0, 0, 0, 0);

		const overdueTasks = tasks.filter(task => {
			if (task.completed || task.dropped) return false;
			const due = task.dueDate;
			return due && due < today;
		});

		return overdueTasks.map(lib.normalizeTask.bind(lib));
	};

	lib.getFlaggedTasks = function() {
		const tasks = flattenedTasks;

		const flaggedTasks = tasks.filter(task => {
			return task.flagged && !task.completed && !task.dropped;
		});

		return flaggedTasks.map(lib.normalizeTask.bind(lib));
	};

	lib.normalizeTask = function(task) {
		return {
			name: task.name,
			project: task.containingProject ? task.containingProject.name : null,
			tags: task.tags.map(tag => tag.name),
			dueDate: task.dueDate,
			deferDate: task.deferDate,
			flagged: task.flagged,
			completed: task.completed,
			estimatedMinutes: task.estimatedMinutes,
			note: task.note || "",
			added: task.added,
			modified: task.modified
		};
	};

	lib.getCompletedToday = function() {
		const tasks = flattenedTasks;

		const today = new Date();
		today.setHours(0, 0, 0, 0);
		const tomorrow = new Date(today);
		tomorrow.setDate(tomorrow.getDate() + 1);

		const completedToday = tasks.filter(task => {
			if (!task.completed) return false;
			const completionDate = task.completionDate;
			return completionDate && completionDate >= today && completionDate < tomorrow;
		});

		return completedToday.map(lib.normalizeCompletedTask.bind(lib));
	};

	lib.normalizeCompletedTask = function(task) {
		return {
			name: task.name,
			project: task.containingProject ? task.containingProject.name : null,
			completionDate: task.completionDate,
			completionTime: task.completionDate ?
				task.completionDate.toLocaleTimeString('en-US', {
					hour: 'numeric',
					minute: '2-digit',
					hour12: true
				}) : null
		};
	};

	return lib;
})();
