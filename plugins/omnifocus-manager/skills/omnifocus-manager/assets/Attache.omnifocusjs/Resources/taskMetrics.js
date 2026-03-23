/**
 * Task Metrics Library
 *
 * Reusable functions for collecting task data from OmniFocus.
 * Includes single-pass collector for performance on large databases.
 *
 * Usage in plugin actions:
 *   const core = this.plugIn.library("ofoCore");
 *   const metrics = this.plugIn.library("taskMetrics");
 *   const all = metrics.collectAllMetrics(core);
 */

(() => {
	var lib = new PlugIn.Library(new Version("5.0"));

	/**
	 * Single-pass metrics collector — buckets all categories simultaneously.
	 * On a 5,000-task database this is 4-5x faster than calling individual methods.
	 *
	 * @param {Object} core - ofoCore library ref (provides normalizeTask)
	 * @returns {Object} { inbox, today, overdue, flagged, completedToday, deferredToday }
	 */
	lib.collectAllMetrics = function(core) {
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		const tomorrow = new Date(today);
		tomorrow.setDate(tomorrow.getDate() + 1);

		const result = {
			inbox: [],
			today: [],
			overdue: [],
			flagged: [],
			completedToday: [],
			deferredToday: []
		};

		for (const task of flattenedTasks) {
			if (task.completed) {
				if (task.completionDate && task.completionDate >= today && task.completionDate < tomorrow) {
					result.completedToday.push(lib.normalizeCompletedTask(task));
				}
				continue;
			}
			if (task.dropped) continue;

			// Active task buckets
			if (task.inInbox && task.taskStatus === Task.Status.Available) {
				result.inbox.push(core.normalizeTask(task));
			}
			if (task.flagged) {
				result.flagged.push(core.normalizeTask(task));
			}
			if (task.dueDate) {
				if (task.dueDate < today) {
					result.overdue.push(core.normalizeTask(task));
				} else if (task.dueDate < tomorrow) {
					result.today.push(core.normalizeTask(task));
				}
			}
			if (task.deferDate && task.deferDate >= today && task.deferDate < tomorrow) {
				result.deferredToday.push(core.normalizeTask(task));
				// Also add to today if not already there via dueDate
				if (!task.dueDate || task.dueDate < today || task.dueDate >= tomorrow) {
					result.today.push(core.normalizeTask(task));
				}
			}
		}

		return result;
	};

	lib.getTodayTasks = function(core) {
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

		return todayTasks.map(t => core.normalizeTask(t));
	};

	lib.getOverdueTasks = function(core) {
		const tasks = flattenedTasks;

		const today = new Date();
		today.setHours(0, 0, 0, 0);

		const overdueTasks = tasks.filter(task => {
			if (task.completed || task.dropped) return false;
			const due = task.dueDate;
			return due && due < today;
		});

		return overdueTasks.map(t => core.normalizeTask(t));
	};

	lib.getFlaggedTasks = function(core) {
		const tasks = flattenedTasks;

		const flaggedTasks = tasks.filter(task => {
			return task.flagged && !task.completed && !task.dropped;
		});

		return flaggedTasks.map(t => core.normalizeTask(t));
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

	lib.getCompletedThisWeek = function() {
		const today = new Date();
		today.setHours(23, 59, 59, 999);
		const weekAgo = new Date();
		weekAgo.setDate(weekAgo.getDate() - 7);
		weekAgo.setHours(0, 0, 0, 0);

		return flattenedTasks.filter(task => {
			if (!task.completed) return false;
			const d = task.completionDate;
			return d && d >= weekAgo && d <= today;
		}).slice(0, 100).map(lib.normalizeCompletedTask.bind(lib));
	};

	lib.getCompletedThisMonth = function() {
		const today = new Date();
		today.setHours(23, 59, 59, 999);
		const monthAgo = new Date();
		monthAgo.setDate(monthAgo.getDate() - 30);
		monthAgo.setHours(0, 0, 0, 0);

		return flattenedTasks.filter(task => {
			if (!task.completed) return false;
			const d = task.completionDate;
			return d && d >= monthAgo && d <= today;
		}).slice(0, 200).map(lib.normalizeCompletedTask.bind(lib));
	};

	lib.getOnHoldProjects = function() {
		const cutoff = new Date();
		cutoff.setDate(cutoff.getDate() - 90);

		return flattenedProjects.filter(p => {
			return p.status === Project.Status.OnHold &&
			       (!p.modified || p.modified < cutoff);
		}).slice(0, 100).map(p => ({
			name: p.name,
			lastModified: p.modified
		}));
	};

	lib.WAITING_PATTERNS = ["waiting", "delegated", "pending", "w:"];

	return lib;
})();
