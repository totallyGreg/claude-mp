/**
 * Status line — Pi's footer, laid out like ~/.claude/statusline-command.sh:
 *
 *   user ~/rel/path on branch !+ [tier · model] think:level ↑in ↓out <extension statuses>
 *
 * The [tier · model] bar fills with context use: green <50%, yellow 50–89%, red ≥90%.
 * Same Solarized palette as the Claude Code status line. Git dirty state is
 * refreshed at session start and after each turn, not on every render.
 * `/statusline` toggles back to Pi's built-in footer.
 */

import { execFileSync } from "node:child_process";
import { userInfo } from "node:os";
import { relative } from "node:path";
import type { AssistantMessage } from "@earendil-works/pi-ai";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { truncateToWidth } from "@earendil-works/pi-tui";

const RS = "\x1b[0m";
const DIM = "\x1b[2m";
const FG = {
	yellow: "\x1b[38;2;133;153;0m",
	violet: "\x1b[38;2;108;113;196m",
	cyan: "\x1b[38;2;42;161;152m",
	blue: "\x1b[38;2;38;139;210m",
	red: "\x1b[38;2;220;50;47m",
};
const FILL = {
	green: "\x1b[48;2;133;153;0m\x1b[38;2;0;43;54m",
	yellow: "\x1b[48;2;181;137;0m\x1b[38;2;0;43;54m",
	red: "\x1b[48;2;220;50;47m\x1b[97m",
};

function git(cwd: string, ...args: string[]): string | null {
	try {
		return execFileSync("git", args, { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
	} catch {
		return null;
	}
}

function clean(cwd: string, ...args: string[]): boolean {
	return git(cwd, ...args) !== null; // `git diff --quiet` exits non-zero when dirty
}

/** `[text]` with the first pct% of its characters filled in the alert color. */
function fillBar(text: string, pct: number): string {
	const chars = [...text];
	let n = Math.floor((pct * chars.length) / 100);
	if (pct > 0 && n === 0) n = 1;
	const fill = pct >= 90 ? FILL.red : pct >= 50 ? FILL.yellow : FILL.green;
	return `[${chars.map((c, i) => (i < n ? `${fill}${c}${RS}` : `${DIM}${c}${RS}`)).join("")}]`;
}

function fmt(n: number): string {
	return n < 1000 ? `${n}` : `${(n / 1000).toFixed(1)}k`;
}

export default function (pi: ExtensionAPI) {
	let enabled = true;
	let root: string | null = null;
	let dirty = "";
	let requestRender = () => {};

	const refreshGit = (cwd: string) => {
		root = git(cwd, "rev-parse", "--show-toplevel");
		dirty = root
			? (clean(cwd, "diff", "--quiet") ? "" : `${FG.red}!${RS}`) +
				(clean(cwd, "diff", "--cached", "--quiet") ? "" : `${FG.yellow}+${RS}`)
			: "";
		requestRender();
	};

	const install = (ctx: ExtensionContext) => {
		ctx.ui.setFooter((tui, _theme, footerData) => {
			requestRender = () => tui.requestRender();
			const unsub = footerData.onBranchChange(() => refreshGit(ctx.cwd));
			return {
				dispose: unsub,
				invalidate() {},
				render(width: number): string[] {
					const parts = [userInfo().username];

					if (root) {
						const rel = relative(root, ctx.cwd);
						parts.push(`${FG.violet}~/${rel}${RS}`);
					} else {
						parts.push(`${FG.violet}.../${ctx.cwd.split("/").slice(-3).join("/")}${RS}`);
					}

					const branch = footerData.getGitBranch();
					if (branch) parts.push(`${FG.cyan}on ${branch}${RS}${dirty}`);

					// "code — Qwen3.6-35B-A3B oQ4e+MTP" → "code · Qwen3.6-35B-A3B oQ4e+MTP"
					const name = ctx.model?.name ?? ctx.model?.id ?? "no model";
					const usage = ctx.getContextUsage();
					parts.push(fillBar(name.replace(" — ", " · "), Math.min(100, Math.max(0, usage?.percent ?? 0))));

					if (ctx.model?.reasoning) parts.push(`${FG.blue}think:${pi.getThinkingLevel()}${RS}`);

					let input = 0;
					let output = 0;
					for (const e of ctx.sessionManager.getBranch()) {
						if (e.type === "message" && e.message.role === "assistant") {
							const m = e.message as AssistantMessage;
							input += m.usage.input;
							output += m.usage.output;
						}
					}
					parts.push(`${FG.yellow}↑${fmt(input)} ↓${fmt(output)}${RS}`);

					for (const status of footerData.getExtensionStatuses().values()) parts.push(status);

					return [truncateToWidth(parts.join(" "), width)];
				},
			};
		});
		refreshGit(ctx.cwd);
	};

	pi.on("session_start", async (_event, ctx) => {
		if (enabled) install(ctx);
	});

	pi.on("turn_end", async (_event, ctx) => {
		if (enabled) refreshGit(ctx.cwd);
	});

	pi.registerCommand("statusline", {
		description: "Toggle the custom status line (off restores Pi's built-in footer)",
		handler: async (_args, ctx) => {
			enabled = !enabled;
			if (enabled) install(ctx);
			else ctx.ui.setFooter(undefined);
			ctx.ui.notify(enabled ? "Custom status line on" : "Built-in footer restored", "info");
		},
	});
}
