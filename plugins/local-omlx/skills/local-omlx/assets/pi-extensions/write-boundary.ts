/**
 * Write Boundary — Pi's edit and write tools may only touch files under the
 * directory Pi was started in (its cwd), the way the Claude Code teammate is
 * limited by `Edit(//<dir>/**)`.
 *
 * Paths are resolved against the cwd, `~` is expanded, and both sides are
 * compared by real path (nearest existing ancestor), so `..`, symlinks and
 * macOS's /tmp → /private/tmp can't slip past. A write outside is blocked —
 * never prompted: pane teammates have nobody watching to answer — and the
 * reason goes back to the model.
 *
 * Not covered: the bash tool can still write anywhere (permission-gate only
 * catches rm -rf / sudo / chmod 777). `/write-boundary` toggles the check for
 * this session.
 */

import { existsSync, realpathSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, isAbsolute, relative, resolve } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

/** Real path of `p`, or of its nearest existing ancestor joined with the rest. */
function realish(p: string): string {
	let head = p;
	let tail = "";
	while (!existsSync(head)) {
		const parent = dirname(head);
		if (parent === head) return p;
		tail = tail ? `${head.slice(parent.length + 1)}/${tail}` : head.slice(parent.length + 1);
		head = parent;
	}
	const real = realpathSync(head);
	return tail ? resolve(real, tail) : real;
}

function inside(root: string, target: string): boolean {
	const rel = relative(root, target);
	return rel === "" || (!rel.startsWith("..") && !isAbsolute(rel));
}

export default function (pi: ExtensionAPI) {
	let enabled = true;

	pi.on("tool_call", async (event, ctx) => {
		if (!enabled || (event.toolName !== "edit" && event.toolName !== "write")) return undefined;

		const raw = String(event.input.path ?? "");
		const expanded = raw === "~" || raw.startsWith("~/") ? homedir() + raw.slice(1) : raw;
		const root = realish(resolve(ctx.cwd));
		const target = realish(resolve(ctx.cwd, expanded));
		if (inside(root, target)) return undefined;

		if (ctx.hasUI) ctx.ui.notify(`write-boundary: blocked ${event.toolName} to ${target}`, "warning");
		return {
			block: true,
			reason: `${target} is outside this session's directory (${root}). Only files under it may be edited or written; use paths relative to it.`,
		};
	});

	pi.registerCommand("write-boundary", {
		description: "Toggle the write boundary (edit/write only under the session's directory)",
		handler: async (_args, ctx) => {
			enabled = !enabled;
			ctx.ui.notify(enabled ? "Write boundary on" : "Write boundary OFF for this session", enabled ? "info" : "warning");
		},
	});
}
