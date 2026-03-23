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

interface OfoCoreDep {
	normalizeTask(task: Task): OfoTask;
}

interface CompletedTask {
	name: string;
	project: string | null;
	completionDate: Date | null;
	completionTime: string | null;
}

interface MetricsBuckets {
	inbox: OfoTask[];
	today: OfoTask[];
	overdue: OfoTask[];
	flagged: OfoTask[];
	completedToday: CompletedTask[];
	deferredToday: OfoTask[];
}

(() => {
	var lib = new PlugIn.Library(new Version("5.0"));

	lib.collectAllMetrics = function(core: OfoCoreDep): MetricsBuckets {
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		const tomorrow = new Date(today);
		tomorrow.setDate(tomorrow.getDate() + 1);

		const result: MetricsBuckets = {
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
				if (!task.dueDate || task.dueDate < today || task.dueDate >= tomorrow) {
					result.today.push(core.normalizeTask(task));
				}
			}
		}

		return result;
	};

	lib.getTodayTasks = function(core: OfoCoreDep): OfoTask[] {
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		const tomorrow = new Date(today);
		tomorrow.setDate(tomorrow.getDate() + 1);

		const todayTasks = flattenedTasks.filter((task: Task) => {
			if (task.completed || task.dropped) return false;
			const due = task.dueDate;
			const defer = task.deferDate;
			return (due && due >= today && due < tomorrow) ||
			       (defer && defer >= today && defer < tomorrow);
		});

		return todayTasks.map((t: Task) => core.normalizeTask(t));
	};

	lib.getOverdueTasks = function(core: OfoCoreDep): OfoTask[] {
		const today = new Date();
		today.setHours(0, 0, 0, 0);

		const overdueTasks = flattenedTasks.filter((task: Task) => {
			if (task.completed || task.dropped) return false;
			return task.dueDate && task.dueDate < today;
		});

		return overdueTasks.map((t: Task) => core.normalizeTask(t));
	};

	lib.getFlaggedTasks = function(core: OfoCoreDep): OfoTask[] {
		return flattenedTasks
			.filter((task: Task) => task.flagged && !task.completed && !task.dropped)
			.map((t: Task) => core.normalizeTask(t));
	};

	lib.getCompletedToday = function(): CompletedTask[] {
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		const tomorrow = new Date(today);
		tomorrow.setDate(tomorrow.getDate() + 1);

		return flattenedTasks.filter((task: Task) => {
			if (!task.completed) return false;
			const d = task.completionDate;
			return d && d >= today && d < tomorrow;
		}).map((t: Task) => lib.normalizeCompletedTask(t));
	};

	lib.normalizeCompletedTask = function(task: Task): CompletedTask {
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

	lib.getCompletedThisWeek = function(): CompletedTask[] {
		const today = new Date();
		today.setHours(23, 59, 59, 999);
		const weekAgo = new Date();
		weekAgo.setDate(weekAgo.getDate() - 7);
		weekAgo.setHours(0, 0, 0, 0);

		return flattenedTasks.filter((task: Task) => {
			if (!task.completed) return false;
			const d = task.completionDate;
			return d && d >= weekAgo && d <= today;
		}).slice(0, 100).map((t: Task) => lib.normalizeCompletedTask(t));
	};

	lib.getCompletedThisMonth = function(): CompletedTask[] {
		const today = new Date();
		today.setHours(23, 59, 59, 999);
		const monthAgo = new Date();
		monthAgo.setDate(monthAgo.getDate() - 30);
		monthAgo.setHours(0, 0, 0, 0);

		return flattenedTasks.filter((task: Task) => {
			if (!task.completed) return false;
			const d = task.completionDate;
			return d && d >= monthAgo && d <= today;
		}).slice(0, 200).map((t: Task) => lib.normalizeCompletedTask(t));
	};

	lib.getOnHoldProjects = function(): { name: string; lastModified: Date | null }[] {
		const cutoff = new Date();
		cutoff.setDate(cutoff.getDate() - 90);

		return flattenedProjects.filter((p: Project) => {
			return p.status === Project.Status.OnHold &&
			       (!p.modified || p.modified < cutoff);
		}).slice(0, 100).map((p: Project) => ({
			name: p.name,
			lastModified: p.modified
		}));
	};

	lib.WAITING_PATTERNS = ["waiting", "delegated", "pending", "w:"];

	return lib;
})();
