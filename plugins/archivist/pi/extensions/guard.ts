/**
 * Archivist vault guard for Pi — the Pi side of hooks/vault_file_guard.py.
 *
 * Claude Code enforces the archivist's write rules with PreToolUse hooks that
 * Pi does not run. This module gives a Pi session the same rules by calling
 * the same code:
 *
 * - `edit` / `write` calls are passed to hooks/vault_file_guard.py in Claude's
 *   hook payload shape, with this session's archivist role as `agent_type`.
 *   "deny" and "ask" both block (a Pi subagent has nobody to answer a prompt);
 *   the reason goes back to the model.
 * - A `vault_write` tool runs `bin/vault-write apply` — the plugin's one
 *   guarded write path (zones, compare-and-swap, lint, git snapshot).
 *
 * The zone rules live only in the Python files; nothing is duplicated here.
 * Entry files (archivist.ts, archivist-architect.ts) pick the role.
 */

import { execFile } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

const PLUGIN = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const GUARD = resolve(PLUGIN, "hooks/vault_file_guard.py");
const VAULT_WRITE = resolve(PLUGIN, "bin/vault-write");
const CHECK_MERGE = resolve(PLUGIN, "skills/vault-curator/scripts/check_merge_preserved.py");

function run(cmd: string, args: string[], input: string, signal?: AbortSignal) {
	return new Promise<{ code: number; stdout: string; stderr: string }>((done) => {
		const child = execFile(cmd, args, { signal, maxBuffer: 16 * 1024 * 1024 }, (err, stdout, stderr) => {
			const code = err ? (typeof (err as any).code === "number" ? (err as any).code : 1) : 0;
			done({ code, stdout: String(stdout), stderr: String(stderr) });
		});
		child.stdin?.end(input);
	});
}

function absolute(raw: string, cwd: string): string {
	const expanded = raw === "~" || raw.startsWith("~/") ? homedir() + raw.slice(1) : raw;
	return resolve(cwd, expanded);
}

/** The configured vault's root (vault-write config), else the session directory. */
async function vaultRoot(cwd: string): Promise<string> {
	const { stdout } = await run(VAULT_WRITE, ["config"], "");
	try {
		return JSON.parse(stdout).vault ?? cwd;
	} catch {
		return cwd;
	}
}

export function archivistGuard(pi: ExtensionAPI, agentType: string) {
	pi.on("tool_call", async (event, ctx) => {
		if (event.toolName !== "edit" && event.toolName !== "write") return undefined;
		const filePath = absolute(String(event.input.path ?? ""), ctx.cwd);
		const payload = {
			tool_name: event.toolName === "edit" ? "Edit" : "Write",
			tool_input: { file_path: filePath },
			agent_type: agentType,
		};
		const { stdout } = await run("python3", [GUARD], JSON.stringify(payload));
		let decision: { permissionDecision?: string; permissionDecisionReason?: string } | undefined;
		try {
			decision = stdout.trim() ? JSON.parse(stdout).hookSpecificOutput : undefined;
		} catch {
			return { block: true, reason: `archivist guard returned unreadable output for ${filePath}; not writing.` };
		}
		if (!decision?.permissionDecision || decision.permissionDecision === "allow") return undefined;
		const hint = decision.permissionDecision === "ask" ? " Use the vault_write tool instead." : "";
		return { block: true, reason: `${decision.permissionDecisionReason ?? "Blocked by the archivist guard."}${hint}` };
	});

	pi.registerTool({
		name: "vault_stat",
		label: "Vault stat",
		description:
			"Hash, line count and zone of a vault note (vault-write stat). Call it when you read a note you will " +
			"overwrite, and pass the hash as vault_write's `base`: overwriting an existing note needs it.",
		parameters: Type.Object({
			note: Type.String({ description: "Vault-relative path of the note" }),
		}),
		async execute(_id, params, signal) {
			const { code, stdout, stderr } = await run(VAULT_WRITE, ["stat", params.note], "", signal);
			return {
				content: [{ type: "text", text: (stdout || stderr).trim() || `vault-write exited ${code}` }],
				details: { exitCode: code },
			};
		},
	});

	pi.registerTool({
		name: "vault_write",
		label: "Vault write",
		description:
			"Write a vault note through the archivist's guarded write path (zone check, drift check, lint, git snapshot). " +
			"Replaces the whole note, or one heading's section with `section`. Overwriting an existing note needs `base`: " +
			"the hash vault_stat gave when you read it (the write is refused if the note changed since). Returns " +
			"vault-write's JSON result; `refused` means nothing was written.",
		parameters: Type.Object({
			note: Type.String({ description: "Vault-relative path of the note, e.g. '700 Notes/Tools/X.md'" }),
			content: Type.String({ description: "Full new content of the note (or of the section)" }),
			section: Type.Optional(Type.String({ description: "Replace only this heading's section, e.g. '## Summary'" })),
			base: Type.Optional(Type.String({ description: "Expected current hash; the write is refused if the note differs" })),
			merged_from: Type.Optional(
				Type.Array(Type.String(), {
					description:
						"For a merge: vault-relative paths of every note merged into this content. The write is refused " +
						"unless all their lines, URLs and wikilinks are still in it (check_merge_preserved.py).",
				}),
			),
		}),
		async execute(_id, params, signal, _onUpdate, ctx) {
			if (params.merged_from?.length) {
				const dir = mkdtempSync(join(tmpdir(), "archivist-merge-"));
				const merged = join(dir, "merged.md");
				writeFileSync(merged, params.content);
				const root = await vaultRoot(ctx.cwd);
				const sources = params.merged_from.map((p) => resolve(root, p));
				const check = await run("python3", [CHECK_MERGE, "--merged", merged, ...sources], "", signal);
				rmSync(dir, { recursive: true, force: true });
				if (check.code !== 0) {
					return {
						content: [{ type: "text", text: `Refused: the merge drops source text; nothing was written.\n${check.stdout || check.stderr}` }],
						details: { exitCode: check.code },
					};
				}
			}
			const args = ["apply", params.note, "--from", "-"];
			if (params.section) args.push("--section", params.section);
			if (params.base) args.push("--base", params.base);
			const { code, stdout, stderr } = await run(VAULT_WRITE, args, params.content, signal);
			return {
				content: [{ type: "text", text: (stdout || stderr).trim() || `vault-write exited ${code}` }],
				details: { exitCode: code },
			};
		},
	});
}
