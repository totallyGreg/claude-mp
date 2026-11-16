/**
 * Archivist guard for Pi: the Pi side of hooks/hooks.json.
 *
 * Claude Code runs the archivist's PreToolUse hooks; Pi doesn't. This module
 * sends Pi's tool calls to the same Python guards, with this agent's role as
 * `agent_type`, so both harnesses decide the same way:
 *
 * - `bash` → hooks/obsidian_guard.py. In the vault only `obsidian`,
 *   `vault-write` and the archivist's scripts run, inside the role's zones.
 *   This module replaces Pi's bash tool so the check sees exactly the command
 *   that runs, and so commands get what Claude Code gives a plugin's Bash:
 *   CLAUDE_PLUGIN_ROOT, the plugin's bin/ on PATH (vault-write), and
 *   ARCHIVIST_ROLE for this role.
 * - `edit` / `write` → hooks/vault_file_guard.py.
 *
 * "deny" and "ask" both block: a Pi subagent has nobody to answer a prompt.
 * The reason goes back to the model. No zone logic lives here.
 * Entry files (archivist.ts, archivist-architect.ts) pick the role.
 */

import { execFile } from "node:child_process";
import { homedir } from "node:os";
import { delimiter, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createBashTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

const PLUGIN = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const FILE_GUARD = resolve(PLUGIN, "hooks/vault_file_guard.py");
const SHELL_GUARD = resolve(PLUGIN, "hooks/obsidian_guard.py");
const ROLES: Record<string, string> = {
	"archivist:archivist": "curator",
	"archivist:archivist-architect": "architect",
};

type Decision = { permissionDecision?: string; permissionDecisionReason?: string };

function run(cmd: string, args: string[], input: string) {
	return new Promise<{ code: number; stdout: string }>((done) => {
		const child = execFile(cmd, args, { maxBuffer: 16 * 1024 * 1024 }, (err, stdout) => {
			const code = err ? (typeof (err as any).code === "number" ? (err as any).code : 1) : 0;
			done({ code, stdout: String(stdout) });
		});
		child.stdin?.end(input);
	});
}

/** Ask a Claude-style PreToolUse hook; returns the reason to block, or undefined to allow. */
export async function decide(guard: string, payload: object): Promise<string | undefined> {
	const { code, stdout } = await run("python3", [guard], JSON.stringify(payload));
	let decision: Decision | undefined;
	try {
		decision = stdout.trim() ? JSON.parse(stdout).hookSpecificOutput : undefined;
	} catch {
		return "The archivist guard returned unreadable output; not running this.";
	}
	if (code !== 0 && !decision) return `The archivist guard failed (exit ${code}); not running this.`;
	if (!decision?.permissionDecision || decision.permissionDecision === "allow") return undefined;
	const why = decision.permissionDecisionReason ?? "Blocked by the archivist guard.";
	return decision.permissionDecision === "ask"
		? `${why} (This needs the user's confirmation, which a Pi subagent can't get: stop and report it.)`
		: why;
}

function absolute(raw: string, cwd: string): string {
	const expanded = raw === "~" || raw.startsWith("~/") ? homedir() + raw.slice(1) : raw;
	return resolve(cwd, expanded);
}

export function archivistGuard(pi: ExtensionAPI, agentType: string) {
	const role = ROLES[agentType];

	pi.on("tool_call", async (event, ctx) => {
		if (event.toolName !== "edit" && event.toolName !== "write") return undefined;
		const reason = await decide(FILE_GUARD, {
			tool_name: event.toolName === "edit" ? "Edit" : "Write",
			tool_input: { file_path: absolute(String(event.input.path ?? ""), ctx.cwd) },
			agent_type: agentType,
		});
		return reason ? { block: true, reason } : undefined;
	});

	const spawnHook = ({ command, cwd, env }: { command: string; cwd: string; env: NodeJS.ProcessEnv }) => ({
		command,
		cwd,
		env: {
			...env,
			CLAUDE_PLUGIN_ROOT: PLUGIN,
			ARCHIVIST_ROLE: role ?? "",
			PATH: [resolve(PLUGIN, "bin"), env.PATH].filter(Boolean).join(delimiter),
		},
	});
	const template = createBashTool(process.cwd(), { spawnHook });

	pi.registerTool({
		...template,
		async execute(id, params, signal, onUpdate, ctx) {
			const reason = await decide(SHELL_GUARD, {
				tool_name: "Bash",
				tool_input: { command: params.command },
				agent_type: agentType,
				cwd: ctx.cwd,
			});
			if (reason) throw new Error(reason);
			return createBashTool(ctx.cwd, { spawnHook }).execute(id, params, signal, onUpdate);
		},
	});
}
