/**
 * See — gives Pi's local models eyes: a `see` tool that reads an image through `see.sh`,
 * the skill's one implementation of the `see` tier. kind=text and kind=code pass
 * --with-text, so they use Apple's on-device model (`fm`, macOS 27) and its OCR/barcode
 * tools; kind=picture uses oMLX's :fast vision model when the server is up, else `fm`.
 * install_pi_extensions.sh copies see.sh next to this file; `$SEE_SH` overrides the path.
 *
 * Not `fm` as Pi's model: `fm serve` ignores tool definitions and has an 8K context.
 * Here the agent (e.g. omlx/code) does the reasoning and arithmetic; the tool only reads.
 */

import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { StringEnum, Type } from "@earendil-works/pi-ai";
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

const SEE_SH = process.env.SEE_SH ?? join(dirname(fileURLToPath(import.meta.url)), "see.sh");

export default function (pi: ExtensionAPI) {
	pi.registerTool(
		defineTool({
			name: "see",
			label: "See",
			description: [
				"Read an image file with a local vision model (a few seconds). You cannot see images yourself; use this.",
				"kind=text — receipts, invoices, forms, screenshots of text. Requires `schema` (JSON Schema of the fields to extract).",
				"  Returns {answer, read_text}: read_text is exactly what OCR read. Check every value in answer against read_text.",
				"  Ask only for fields printed on the image: a field that isn't there gets invented. Fails if the image has no text.",
				"Never add up or compare numbers in your head — you get sums wrong. Compute them with a tool (e.g. bash:",
				"  python3 -c '...'); with no such tool, report the check as UNVERIFIED.",
				"kind=picture — charts, diagrams, photos. Give a `question`; values read off a chart are approximate.",
				"kind=code — QR codes and barcodes. Returns {answer, read_text} with the exact payload.",
			].join("\n"),
			parameters: Type.Object({
				path: Type.String({ description: "Image file path (png, jpg, heic, tiff), relative to the working directory" }),
				kind: StringEnum(["text", "picture", "code"] as const),
				schema: Type.Optional(
					Type.Record(Type.String(), Type.Any(), {
						description: 'kind=text: JSON Schema object, e.g. {"type":"object","properties":{"total":{"type":"number"}}}',
					}),
				),
				question: Type.Optional(Type.String({ description: "kind=picture: what to answer about the image" })),
			}),
			annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false },

			async execute(_id, params, signal, _onUpdate, ctx) {
				const args: string[] = [];
				let dir: string | undefined;
				if (params.kind === "text") args.push("--text", "--with-text");
				if (params.kind === "code") args.push("--code", "--with-text");
				if (params.schema) {
					dir = mkdtempSync(join(tmpdir(), "see-"));
					writeFileSync(join(dir, "schema.json"), JSON.stringify(params.schema));
					args.push("--schema", join(dir, "schema.json"));
				}
				args.push("--", params.path);
				if (params.kind === "picture" && params.question) args.push(params.question);
				try {
					const r = await pi.exec(SEE_SH, args, { cwd: ctx.cwd, signal, timeout: 120_000 });
					if (r.code !== 0) throw new Error(r.stderr.trim() || `see.sh exited ${r.code}`);
					return { content: [{ type: "text", text: r.stdout.trim() }], details: undefined };
				} finally {
					if (dir) rmSync(dir, { recursive: true, force: true });
				}
			},
		}),
	);
}
