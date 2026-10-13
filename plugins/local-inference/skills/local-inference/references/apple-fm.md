# Apple Foundation Model CLI (`fm`)

`/usr/bin/fm` ships with macOS 27: Apple's on-device model (`system`, an
`instruct_3b` with a draft model for speculative decoding) behind a CLI.
Nothing to install or start, no network, no account. A one-time machine-wide
licence acceptance is required before anything runs: `sudo fm license`
(declining exits 69).

Sources: tests on this Mac (2026-10-13, macOS 27, marked **[here]**) and
Nikhil Vemu, "macOS 27's Hidden LLM Upgrade — 10 (Amazing) New Things You Can
Do With It", MacOClock, 2026-10-04 (marked **[NV]**). The man page (June 2026)
predates `--tool`, `--label` and the server endpoints; trust `fm <cmd> --help`.

## What it is good for

A small model: it **reads well and reasons badly**. Use it to look at an image
or a short text and hand back a shape; let `jq`, `diff`, `sqlite3` or the
shell do anything that must be right [NV].

| Good | Bad |
|------|-----|
| Receipt/invoice/screenshot → JSON | Arithmetic, totals, comparisons |
| Transcribe one image to JSON, then `diff` two transcriptions | "What changed between these two images?" (missed the change that mattered, invented one) [NV] |
| Pick one label from an enum | World knowledge (it thinks the newest iPhone is the 15 Pro) [NV] |
| Tag/summarize one note at a time | Shell commands and flags — confidently wrong, and the wrong flag often runs [NV] |
| Read QR/barcode payloads | Tool calling via `fm serve` (accepts `tools`, ignores them, invents results) [NV] |

Compared with the oMLX tiers: `fm` wins on images (built-in Vision OCR and
barcode tools) and on zero setup; the oMLX models win on context (8K vs
16–128K), reasoning and code. On the `eval_decide.py` set `fm` was 3× faster
than `decide` but 7–10 of 62 items less accurate (type 38 vs 45, area 44 vs 54;
references/tiers.md derivation 10) — do not use it in place of `decide`.

## The `see` tier — `scripts/see.sh` and Pi's `see` tool

`scripts/see.sh` wraps the rules below so callers don't re-learn them:

```bash
S=${CLAUDE_PLUGIN_ROOT}/skills/local-inference/scripts/see.sh
$S --text --schema fields.json receipt.png          # letters: OCR + schema → JSON (--text refuses without a schema)
$S chart.png 'Which month is highest?'              # meaning in pixels: plain vision
$S --code label.png                                 # QR/barcode → exact payload
$S --text --with-text --schema fields.json r.png    # {"answer": …, "read_text": "<what OCR read>"}
```

- The schema may be ordinary JSON Schema: `see.sh` adds `title` (unique per
  object — `fm` merges objects that share a title, turning nested items into
  copies of the root), `additionalProperties`, `x-order` and `required`.
- `read_text` comes from the transcript (`--save-transcript`), so every value
  in the answer can be checked against what OCR actually read. When the OCR or
  barcode tool reads nothing, `see.sh` fails (exit 1) instead of returning the
  invented empties and zeros `fm` fills the schema with.
- Retries OCR/barcode calls (intermittent failures), passes the prompt after
  `--`, exits 3 when `fm` is unavailable.

**Pi's `see` tool** (`assets/pi-extensions/see.ts`, installed with
`see.sh` next to it by `install_pi_extensions.sh`) gives the text-only oMLX
tiers eyes: `see(path, kind: text|picture|code, schema?, question?)`.
`fm` is never Pi's model — `fm serve` ignores tool definitions (asked to read
a file it answered `"Read: README.md"`, `finish_reason: stop`) and 8K can't
hold Pi's prompt and tools.

Tested 2026-10-13, `omlx/code`, a folder of `img1–3.png` (two receipts, one
printing a wrong total; one QR code), 3 runs: the agent called `see` on every
image with the right `kind` (once it tried `text` on the QR, then switched to
`code`) and every value it extracted was exact. **Its own check of the sums
was not:** it passed the wrong total in 2 of 3 runs — once writing
"12.00 + 1.00 = 13.00 ✅ matches" against a printed 15.00 — and ignored the
tool description's instruction to compute with `bash`. Verify anything that
must be right (sums, comparisons) with `jq`/code on the extracted values, in
the orchestrator. Evidence rows: references/pi-vs-claude.md.

## Commands

```bash
fm available                          # "System model available"
fm respond --no-stream -g [opts] 'prompt'
fm count-tokens -q [-i ...] 'prompt'  # bare integer
fm schema object --name T ...         # build a --schema file
fm serve [--port 1976 | --socket p]   # OpenAI-style Chat Completions server
fm chat [-i ...]                      # interactive; sessions in ~/.fm/sessions/
```

`respond` options worth knowing: `-i/--instructions`, `--schema <file>`,
`--image <path>` (repeatable, paired by order with `--label`), `--text <t>`,
`--tool ocr|barcode` (repeatable), `-g/--greedy`, `--save-transcript`/
`--resume`, `--use-case content-tagging`, `--guardrails
permissive-content-transformations`.

In scripts always pass `--no-stream` (streaming is the default) and usually
`-g` (greedy, reproducible). Output on stdout is just the answer — with a
schema, just the JSON object, no prose, no fence [here].

## Images — pick the right eye

| Image holds | Use | Why |
|-------------|-----|-----|
| Letters: receipt, invoice, form, screenshot of text | `--tool ocr --image f --schema s` | On a real receipt, `--image` + `--schema` swapped digits (615 for 651) 2/5 runs; OCR + schema was right 5/5 [NV] |
| Meaning in pixels: chart, diagram, photo | plain `--image f` | OCR read a bar chart's axis labels as the values [NV] |
| QR / barcode | `--tool barcode --image f 'Print ONLY the exact payload.'` | Asking for "the number" made it invent 13 digits for an alphanumeric code [NV] |

Never use `--tool ocr` without a schema: OCR returns columns (all labels, then
all numbers) and the model pairs them wrongly [NV]. The first OCR call after
a while is slow (27 s cold vs ~3.3 s warm here) [here]; the OCR tool also
fails intermittently (5 of 12 runs [NV]) — retry in scripts. Vision OCR does
not read most Indic scripts (Telugu came back as Thai) [NV].

Receipt example (verified [here], ~3 s warm):

```bash
fm schema object --name Receipt \
  --string merchant --string date --description 'YYYY-MM-DD' \
  --object items --schema "$(fm schema object --name Item --string name --double price)" --array \
  --double subtotal --double tax --double total \
  --string currency --description 'ISO 4217 code' > receipt.schema.json

fm respond --no-stream -g --tool ocr --image receipt.png \
  --schema receipt.schema.json 'Extract this receipt.'
# {"merchant": "BLUE BOTTLE COFFEE", "date": "2026-10-11", "items": [{"name": "Latte 12oz", "price": 5.5}, ...], "total": 16.11, ...}
```

## Schemas — Apple's dialect, not JSON Schema

- `title`, `type`, `additionalProperties`, `x-order`, `required` and
  `properties` are all mandatory. A plain JSON Schema fails with `The data
  couldn't be read because it is missing.` [here]
- Generate with `fm schema object`, or hand-write in that shape.
  `--array` goes **after** the thing it modifies, including after
  `--object x --schema "$(...)"`; dot names (`tax.cgst`) make nested objects.
  The help's `--nested` example is wrong — use `--object` [here][NV].
- `enum` works in a hand-written schema [here] — use it for classification:

  ```json
  {"title":"Label","type":"object","additionalProperties":false,"x-order":["label"],
   "required":["label"],"properties":{"label":{"type":"string","enum":["bug","improvement","other"]}}}
  ```

  An enum guarantees the shape, not the truth; it cannot say "none of these",
  so always include `other` [NV].

## Context — 8,192 tokens, shared

The window is 8,192 tokens for instructions + input + answer together [NV];
overflow fails with `The session's transcript exceeded the model's context
size.` and exit 1 [here]. Check with `fm count-tokens -q` first. For folders,
index one file per call (summary/tags per file into a CSV), then route a
question to the one file the index names [NV].

## Input traps [here]

- A prompt argument that starts with `-` (e.g. YAML frontmatter `---`) is
  parsed as an option: `Error: Invalid option: ---`. `--text "$x"` fails the
  same way. Use `--text="$x"`, or put the document on stdin and the task in
  `-i`.
- With both a prompt argument and stdin, stdin is ignored.
- Safe pattern for documents: `fm respond --no-stream -g -i 'task' < doc.md`.

## Refusals

`Error: The model's safety guardrails were triggered.` / `The model refused
to answer.` Fiction with violence needs `--guardrails
permissive-content-transformations` [NV]. Some benign inputs are refused
anyway (non-English translations, a tax note with a schema, degenerate
repeated text [here]); no flag helps — route those to the oMLX tiers.

## `fm chat`

Without `-i`, chat injects Apple's own "Format responses using Markdown"
instruction, which degraded extraction (615 vs 651) — always give `-i`.
Chat cannot see the filesystem; asked about a folder, it invents files [NV].

## `fm serve`

```bash
fm serve --port 1976                       # or --socket /tmp/fm.sock
curl -s 127.0.0.1:1976/health              # {"models":[{"name":"system","available":true}],"status":"fm serve is running"}
```

- **Streams by default** — unlike OpenAI. Send `"stream": false` or you get
  SSE `data:` lines (the `openai` SDK then returns a string) [here].
- Model id is `system`; no key needed. The API accepts `seed` for
  reproducible sampling, which the CLI lacks [NV].
- `tools` are accepted and ignored — never use it for tool calling [NV].

## Shortcuts' Use Model action

Shortcuts' **Use Model** action reaches Apple's Private Cloud Compute models
(Cloud, default; Cloud Pro with iCloud+), which `fm` cannot (`--model pcc` is
gone) [NV]. That is cloud, not local — out of scope for this skill.
