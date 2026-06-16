/**
 * Apply Form Library
 *
 * Per-item confirmation Form helper for "apply paths" — the shared UI pattern
 * across Attache analysis actions (Clarify Tasks, Project Health, Weekly
 * Review waiting-for, Wins Report follow-ups).
 *
 * The caller composes a list of self-describing proposed changes; the helper
 * renders a Form with per-change checkboxes and returns the per-key accept
 * decisions. The caller then dispatches accepted changes via `ofoCore.*`.
 *
 * Usage in PlugIn.Action:
 *   const applyForm = this.plugIn.library("applyForm");
 *   const decision = await applyForm.confirmApply({
 *     itemName: task.name,
 *     changes: [
 *       { key: "name",     label: 'Rename to: "Pay quarterly tax"' },
 *       { key: "estimate", label: "Set estimate: 30 min" },
 *       { key: "tags",     label: "Add tags: finance, errands" },
 *     ],
 *   });
 *   if (decision.cancelled) continue;        // user skipped this item
 *   const upd: Record<string, unknown> = { id: task.id.primaryKey };
 *   if (decision.apply.name)     upd.name = analysis.suggestedName;
 *   if (decision.apply.estimate) upd.estimate = analysis.estimatedMinutes;
 *   const res = ofoCore.updateTask(upd);
 *   if (!res.success) new Alert("Update failed", res.error || "").show();
 *
 * Design notes:
 * - Caller owns suggested values and the dispatch logic. The helper deliberately
 *   does NOT know about ofoCore — it's a pure UI primitive so it stays reusable
 *   across analysis actions that touch different ofoCore methods.
 * - One Form per item (per task / per project / per waiting-for entry). Cancelling
 *   one item never aborts the outer loop — caller decides whether to break or
 *   continue based on `decision.cancelled`.
 * - Checkbox labels are self-describing strings the caller composes. The helper
 *   does NOT format current-vs-suggested — that's caller policy (some fields
 *   read naturally as "Rename to X", others as "Current: A → Suggested: B").
 */

interface ProposedChange {
	/** Stable key returned in `decision.apply` map. */
	key: string;
	/** Checkbox label shown to the user. Should be self-describing. */
	label: string;
	/** Default checkbox state. Defaults to true. */
	enabled?: boolean;
}

interface ApplyProposal {
	/** Item name — shown in form title. */
	itemName: string;
	/** Per-change proposals to render as checkboxes. Empty list → no-op (returns cancelled=true). */
	changes: ProposedChange[];
	/** Form title prefix (default "Apply Changes"). Final title is "{title}: {itemName}". */
	title?: string;
	/** Confirm button label (default "Apply"). */
	confirmLabel?: string;
}

interface ApplyDecision {
	/** True if the user dismissed the form (Cancel / Escape). When true, `apply` is empty. */
	cancelled: boolean;
	/** Per-key decision: true = user kept the checkbox checked (apply). */
	apply: { [key: string]: boolean };
}

(() => {
	var lib = new PlugIn.Library(new Version("1.0"));

	/**
	 * Show a per-item confirmation Form with per-change checkboxes.
	 *
	 * Returns immediately with `{cancelled: true, apply: {}}` if the proposal has
	 * no changes (no fields would render → no decision to make).
	 *
	 * Otherwise renders a Form whose checkbox values become the boolean entries
	 * in `decision.apply`. The caller is responsible for dispatching the accepted
	 * changes via the appropriate `ofoCore.*` calls and for surfacing errors.
	 */
	lib.confirmApply = async function(proposal: ApplyProposal): Promise<ApplyDecision> {
		if (!proposal || !proposal.changes || proposal.changes.length === 0) {
			return { cancelled: true, apply: {} };
		}

		const form = new Form();
		for (let i = 0; i < proposal.changes.length; i++) {
			const change = proposal.changes[i];
			if (!change) continue;
			const enabledByDefault = change.enabled !== false;
			form.addField(new Form.Field.Checkbox(change.key, change.label, enabledByDefault));
		}

		const titlePrefix = proposal.title || "Apply Changes";
		const fullTitle = titlePrefix + ": " + proposal.itemName;
		const confirmLabel = proposal.confirmLabel || "Apply";

		const result = await form.show(fullTitle, confirmLabel);
		if (!result) {
			return { cancelled: true, apply: {} };
		}

		const apply: { [key: string]: boolean } = {};
		for (let i = 0; i < proposal.changes.length; i++) {
			const change = proposal.changes[i];
			if (!change) continue;
			apply[change.key] = !!result.values[change.key];
		}
		return { cancelled: false, apply };
	};

	/**
	 * Convenience: returns true iff at least one key in the apply map is true.
	 * Useful for the caller's "user accepted nothing, skip dispatch" guard.
	 */
	lib.anyAccepted = function(decision: ApplyDecision): boolean {
		if (!decision || decision.cancelled) return false;
		const keys = Object.keys(decision.apply);
		for (let i = 0; i < keys.length; i++) {
			const k = keys[i];
			if (k && decision.apply[k]) return true;
		}
		return false;
	};

	return lib;
})();
