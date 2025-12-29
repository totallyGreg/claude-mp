/**
 * AI Selected Task Analyzer - Omni Automation Plug-In
 *
 * Analyzes selected tasks (1-5) using Apple Foundation Models to provide
 * detailed per-task analysis including clarity scoring, improvements, tags,
 * priority recommendations, and missing information.
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - macOS 15.2+, iOS 18.2+, or later
 * - Apple Silicon or iPhone 15 Pro+ for on-device AI
 */

(() => {
	const action = new PlugIn.Action(async function(selection, sender) {
		try {
			// Validation
			const tasks = selection.tasks;

			if (tasks.length === 0) {
				throw new Error("Please select at least one task to analyze.");
			}

			// Limit to 5 tasks to avoid long processing times
			if (tasks.length > 5) {
				throw new Error("Please select 5 or fewer tasks. AI analysis can take time for multiple tasks.");
			}

			// Check if AFM is available
			if (typeof LanguageModel === 'undefined') {
				throw new Error("Apple Foundation Models not available. Requires OmniFocus 4.8+ and macOS/iOS 26+.");
			}

			// AI Analysis
			const session = new LanguageModel.Session();
			const progress = new Progress("Analyzing tasks with AI...");
			progress.totalUnitCount = tasks.length;

			const results = [];

			try {
				for (const task of tasks) {
					// Build context for the AI
					const taskContext = buildTaskContext(task);

					// Define the analysis schema for structured output
					const schema = new LanguageModel.Schema({
						type: "object",
						properties: {
							clarity: {
								type: "number",
								minimum: 1,
								maximum: 10,
								description: "How clear and actionable the task is (1-10)"
							},
							suggestedName: {
								type: "string",
								description: "Improved task name if current one could be clearer"
							},
							suggestedTags: {
								type: "array",
								items: { type: "string" },
								description: "2-3 relevant tags based on task content"
							},
							priority: {
								type: "string",
								enum: ["high", "medium", "low"],
								description: "Suggested priority level"
							},
							estimatedMinutes: {
								type: "number",
								minimum: 1,
								description: "Estimated time to complete in minutes"
							},
							improvements: {
								type: "array",
								items: { type: "string" },
								description: "Specific suggestions for improving the task"
							},
							missingInfo: {
								type: "array",
								items: { type: "string" },
								description: "Information that would help complete this task"
							}
						},
						required: ["clarity", "suggestedTags", "priority", "improvements"]
					});

					// Craft the prompt
					const prompt = `Analyze this OmniFocus task and provide structured feedback:

TASK DETAILS:
${taskContext}

Please analyze:
1. How clear and actionable is this task? (Rate 1-10)
2. Would a different task name be clearer? If yes, suggest one.
3. What 2-3 tags would be most relevant?
4. What priority should this have? (high/medium/low)
5. How long might this take? (in minutes)
6. What specific improvements would make this task better?
7. What information is missing that would help complete this task?

Be specific and practical in your suggestions.`;

					// Get AI analysis
					const response = await session.respondWithSchema(prompt, schema);
					const analysis = JSON.parse(response);

					results.push({
						task: task,
						analysis: analysis
					});

					progress.completedUnitCount++;
				}
			} finally {
				progress.finish();
			}

			// Display Results
			displayResults(results);

		} catch(err) {
			new Alert(err.name, err.message).show();
			console.error(err);
		}
	});

	// Helper Functions

	/**
	 * Build comprehensive context about a task for AI analysis
	 */
	function buildTaskContext(task) {
		const lines = [];

		lines.push(`Name: ${task.name}`);

		if (task.note) {
			lines.push(`Note: ${task.note}`);
		}

		if (task.containingProject) {
			lines.push(`Project: ${task.containingProject.name}`);
		}

		if (task.tags.length > 0) {
			lines.push(`Current Tags: ${task.tags.map(t => t.name).join(', ')}`);
		}

		if (task.dueDate) {
			const dueStr = task.dueDate.toLocaleDateString();
			lines.push(`Due Date: ${dueStr}`);
		}

		if (task.deferDate) {
			const deferStr = task.deferDate.toLocaleDateString();
			lines.push(`Defer Date: ${deferStr}`);
		}

		if (task.estimatedMinutes) {
			lines.push(`Current Estimate: ${task.estimatedMinutes} minutes`);
		}

		lines.push(`Flagged: ${task.flagged ? 'Yes' : 'No'}`);

		return lines.join('\n');
	}

	/**
	 * Display analysis results in a formatted alert
	 */
	function displayResults(results) {
		let message = "";

		results.forEach((result, index) => {
			const { task, analysis } = result;

			if (index > 0) message += "\n\n" + "=".repeat(40) + "\n\n";

			message += `TASK: ${task.name}\n\n`;

			// Clarity score
			message += `Clarity Score: ${analysis.clarity}/10\n`;

			// Suggested improvements
			if (analysis.suggestedName) {
				message += `\nSuggested Name:\n→ ${analysis.suggestedName}\n`;
			}

			// Priority and estimate
			message += `\nPriority: ${analysis.priority.toUpperCase()}\n`;
			if (analysis.estimatedMinutes) {
				message += `Est. Time: ${analysis.estimatedMinutes} minutes\n`;
			}

			// Tags
			if (analysis.suggestedTags.length > 0) {
				message += `\nSuggested Tags:\n`;
				analysis.suggestedTags.forEach(tag => {
					message += `  • ${tag}\n`;
				});
			}

			// Improvements
			if (analysis.improvements.length > 0) {
				message += `\nImprovements:\n`;
				analysis.improvements.forEach(improvement => {
					message += `  • ${improvement}\n`;
				});
			}

			// Missing info
			if (analysis.missingInfo && analysis.missingInfo.length > 0) {
				message += `\nMissing Information:\n`;
				analysis.missingInfo.forEach(info => {
					message += `  • ${info}\n`;
				});
			}
		});

		// Show results
		const alert = new Alert("AI Task Analysis", message);
		alert.addOption("Copy to Clipboard");
		alert.addOption("Done");

		alert.show().then(buttonIndex => {
			if (buttonIndex === 0) {
				// Copy to clipboard
				Pasteboard.general.string = message;
			}
		});
	}

	// Validation
	action.validate = function(selection, sender) {
		// Enable when at least one task is selected
		return (selection.tasks.length > 0);
	};

	return action;
})();
