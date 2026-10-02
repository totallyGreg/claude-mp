# Local model tiers — current mapping, derivation, and how to update

The tiers are defined by **task**; models are interchangeable parts behind
them. Three layers, each owning one thing:

| Layer | Where | Owns |
|-------|-------|------|
| oMLX **template** `fast` / `code` / `deep` | `~/.omlx/global_templates.json` (admin API `/admin/api/profile-templates`) | The task: thinking on/off and budget, context, max output, tool-result cap. Model-agnostic |
| oMLX **profile** on a model, `expose_as_model: true` | `~/.omlx/model_profiles.json` (admin API `/admin/api/models/<model>/profiles`) | Template settings **plus** the model family's sampling. Served as `<model>:<tier>` |
| Pi model entry | `~/.pi/agent/models.json` | `id` = `<model>:<tier>`, `name` starts with the tier (`fast — …`) so `--model omlx/<tier>` resolves |

## Current mapping (fast/code/decide swapped 2026-09-29)

| Tier | Served ID | Model notes |
|------|-----------|-------------|
| fast | `Qwen3.6-35B-A3B-oQ4e-mtp:fast` | MoE, 3B active, 20 GB, `Jundot/Qwen3.6-35B-A3B-oQ4e-mtp`. oMLX 0.7.0, 11K prompt: **2,929 tok/s prefill, 107 tok/s decode** with MTP |
| code | `Qwen3.6-35B-A3B-oQ4e-mtp:code` | Same model; thinking on; MTP engages with the thinking budget |
| deep | `Qwen3.8-27B-oQ4e-mtp:deep` | Dense, 16 GB, `Jundot/Qwen3.8-27B-oQ4e-mtp`, MTP on. oMLX 0.7.0, 11K prompt: ~34 tok/s decode, ~399 tok/s prefill. Qwen3.8 thinking sampling: temperature **1.0**, top_p 0.95, top_k 20 (not 3.6's 0.6). Set 2026-09-29 — derivation 7 |
| decide | `Qwen3.8-27B-oQ4e-mtp:decide` | Same model as deep. Moved 2026-09-29: 31/45 type, 42/45 area vs the 35B's 27 and 38, at ~1.1 s median vs 0.33 s — accuracy is the point of decide. Called via `scripts/decide.py`, not Pi. Grammar-constrained, so MTP doesn't engage — irrelevant for 1–3-token answers |

MTP is a **base-model** setting (`PUT /admin/api/models/<model>/settings
{"mtp_enabled": true}`), not a profile field the templates carry; profiles
inherit it. Confirm it runs: `MTP[…] … tok/cycle=… accept=…` lines in
`server.log` for tier requests.

oMLX's `omlx launch claude` tiers point at the **profiles**, matching Pi
(set 09-30): `claude_code.haiku_model` = `…:fast`, `sonnet_model` = `…:code`,
`opus_model` = `…:deep`; `integrations.pi_model` names the fast/code model.
Repoint them when a tier's model changes (`POST /admin/api/global-settings
{"claude_code_haiku_model": …, "claude_code_sonnet_model": …,
"claude_code_opus_model": …, "integrations_pi_model": …}`).

Template settings:

| | fast | code | deep | decide |
|---|---|---|---|---|
| `enable_thinking` | false | true | true | false |
| `thinking_budget_tokens` (enabled) | — | 4096 | 16384 | — |
| `max_context_window` | 65536 | 131072 | 131072 | 16384 |
| `max_tokens` | 4096 | 16384 | 32768 | 512 |
| `max_tool_result_tokens` | — | 8192 | — | — |
| `temperature` | (model card) | (model card) | (model card) | 0 — deterministic |

`decide` sets no default `guided_grammar`: every call brings its own
constraint (`structured_outputs: {"choice": [...]}` or `{"json": <schema>}`),
because the allowed answers differ per question. oMLX also accepts `regex`,
`grammar` (EBNF), and OpenAI `response_format` json_schema.

Qwen3.x sampling added in each profile (from Qwen's model cards):
thinking `temperature 0.6, top_p 0.95, top_k 20, min_p 0`;
non-thinking `temperature 0.7, top_p 0.8, top_k 20, min_p 0`.
Sampling is per model family, which is why it lives in the profile, not the template.

## How the choices were derived

Machine: Apple M5 Pro, 64 GB unified memory.

1. **Speed by architecture.** From `~/.omlx/stats.json` (per-model totals:
   `completion_tokens / generation_duration`, `(prompt_tokens - cached_tokens) / prefill_duration`)
   and from the per-request `Chat completion: … tok/s` lines in
   `~/.omlx/logs/server.log`. MoE models (Qwen3.6-35B-A3B, Nemotron-3-Nano-30B-A3B)
   decoded 3–7× faster than dense ones (Qwen3.6-27B, gemma-4-31b); Qwen3.8-27B
   at 8-bit decoded ~3 tok/s. The stats.json averages include cold loads and
   concurrency and read low (~35 tok/s for the 35B-A3B vs ~100–150 in the log) —
   compare models with the log lines or oMLX's bench page, not the averages.
   → back-and-forth tiers (fast, code) get the fastest good MoE model; deep gets
   the best dense model that is still usable (~15+ tok/s).
2. **Context fits memory.** KV cache per token =
   `full_attention_layers × 2 × num_key_value_heads × head_dim × 2 bytes` (read
   `text_config` in the model's `config.json`; Qwen3.6 is hybrid, only every 4th
   layer is full attention, the rest are linear/GDN with fixed-size state).
   35B-A3B: 10 × 2 × 2 × 256 × 2 = 20 KB/token → 2.5 GB at 128K.
   27B: 16 × 2 × 4 × 256 × 2 = 64 KB/token → 8 GB at 128K.
   Rule: model weights + KV at the tier's context for **every tier model loaded
   together** should stay under ~75% of RAM (oMLX's soft memory threshold is 0.85).
3. **Thinking by task.** Mechanical work gains nothing from thinking and pays
   latency → off. Agentic loops need some reasoning per step but many steps →
   bounded budget. One-off hard questions → large budget.
4. **Tool-result cap on code** keeps one huge `read` from flooding the context
   in a long loop.
5. **Decide is chosen by accuracy on real labels, not by size.** Expectation
   was a tiny model for speed; measurement said otherwise.
   `scripts/eval_decide.py <AudiobookOCD>/BACKLOG.md <models…>` classifies the
   45 Work items (true type and Area are on each line) with the same
   `choice` grammar decide uses. 2026-09-28:

   | Model | type (2-way) | area (11-way) | median / p90 |
   |---|---|---|---|
   | Qwen3.6-35B-A3B-4bit | 33/45 | **36/45** | 341 / 707 ms |
   | Qwen3-8B-4bit | 30/45 | 22/45 | 241 / 304 ms |
   | LFM2.5-1.2B-Thinking-8bit | 25/45 | 4/45 | 53 / 63 ms |

   The MoE model is accurate *and* fast enough, and it is already resident for
   fast/code, so decide costs no memory. Re-run the eval with any candidate;
   a decide model must beat the incumbent's area score, not just its latency.
6. **Swap to oQ4e + MTP, 2026-09-29.** Measured against the mlx-community
   4-bit it replaced, same machine, other models unloaded
   (`scripts/bench_decode.py <file> <model>` for decode, `eval_decide.py` for
   decisions):

   | | decode tok/s | type, original prompt | type, sharper prompt | area |
   |---|---|---|---|---|
   | mlx-community 4bit (deleted) | 103 | 33/45 | 35/45 | 36/45 |
   | oQ4e, MTP off | 90 | — | — | — |
   | **oQ4e + MTP** | **117** | 27/45 | 30/45 | **38/45** |

   oQ's mixed precision alone is ~12% *slower* to decode; MTP (2.6 tok/cycle,
   ~84% draft acceptance) more than recovers it. Decisions were mixed — better
   on the 11-way area, worse on bug/improvement, where the new build leans to
   "improvement" for items that describe a defect and then the fix. Taken
   because fast/code volume dominates, the model card's coding scores are
   higher (HumanEval 93.9% vs 92.1%), and keeping both 35B builds would cost
   19 GB of resident memory for decide alone.
   Lesson that holds for any model: **state the criterion exactly** — the
   sharper bug definition ("reports something wrong today, even when it also
   describes the fix") lifted both models by 2–3 items.
7. **Dense vs MoE, and Qwen3.8 (checked 2026-09-29).** Quality per the model
   cards: Jundot's oQ4e builds average 85.6% (3.6-27B dense) vs 83.9%
   (3.6-35B-A3B) on MMLU/Winogrande/HumanEval/MBPP. Qwen's own card puts
   Qwen3.8-27B well above Qwen3.6-27B on agentic coding (SWE-bench Pro 61.7 vs
   53.5, Terminal Bench 2.1 73.0 vs 63.4, IFBench 79.5 vs 69.1). Cost: dense
   27B decodes ~5–6× slower than the A3B MoE (~18 vs ~103 tok/s without MTP),
   and a second model is resident (17 GB + 8 GB KV at 128K; with the 35B that
   is ~47.5 GB, at the 75% ceiling). `Qwen3.8-Flash-Next` is a 180B MoE
   (106 GB at oQ4e) — does not fit 64 GB. The earlier Qwen3.8-27B-8bit's
   ~3 tok/s was 8-bit dense without MTP, not a property of 3.8.
   → The dense 3.8-27B is the better brain for `deep` (and arguably `code`);
   the 35B MoE is the better fit for anything latency- or volume-bound.

   Measured 2026-09-29, other model unloaded, `bench_decode.py` on
   AudiobookOCD `Scripts/dashboard.py` (~11.4K prompt tokens), `eval_decide.py`
   original prompts:

   | | prefill tok/s | decode tok/s | first token @11K | type | area | decide median |
   |---|---|---|---|---|---|---|
   | 3.6-35B-A3B oQ4e + MTP | **1517** | **83** | ~7.5 s | 27/45 | 38/45 | **332 ms** |
   | 3.8-27B oQ4e, MTP off | 338 | 13.7 | ~34 s | — | — | — |
   | 3.8-27B oQ4e + MTP | 265 | 19.3 | ~43 s | **31/45** | **42/45** | 1112 ms |

   (35B decode is 117 tok/s on a 2K prompt and 83 at 11K — always compare at
   the same prompt length.) MTP gives the dense model +40% decode (2.65
   tok/cycle, 84% accepted) but costs ~20% prefill.
   Result: `deep` → 3.8-27B. fast/code stay on the 35B — 5× slower prefill
   would make every agent turn wait. There is no Qwen3.8 MoE between 27B and
   180B, so "upgrade the 35B to 3.8" isn't available yet; watch for one.
   Both resident = 37.7 GB (oMLX "total"), measured.
   Skipped: `empero-ai/Qwen3.8-35B-A3B-Distill` — a third-party SFT of
   Qwen3.6-35B-A3B on Qwen3.8 traces, not Qwen3.8. Evidence was MMLU flat and
   ARC +3–5 only, no coding/agentic evals; it always opens with a thinking
   block (fights fast/decide); MTP builds carry a head not retrained with it;
   only oQ6/oQ8 builds (~28 GB+). Revisit if it gains real evals or an oQ4e-mtp
   build — and then it must match the 35B's MTP speed.

8. **oMLX 0.7.0 (2026-10-01).** Same `bench_decode.py` run (dashboard.py,
   ~11.4K prompt tokens, other model idle) against the 0.6.4 numbers above:

   | | prefill tok/s | decode tok/s |
   |---|---|---|
   | 3.6-35B-A3B oQ4e + MTP | 1,517 → **2,929** (+93%) | 83 → **107** (+29%) |
   | 3.8-27B oQ4e + MTP | 265 → **399** (+51%) | 19.3 → **34.3** (+78%) |

   Far above the r/oMLX "0.7.0 vs 0.7.0rc1" post's +11% for Qwen3.6-35B — that
   post compares against rc1; this machine jumped from 0.6.4 and got the whole
   0.7.0 cycle. Taken from that post (M5 Ultra, 256 GB):
   - **Concurrency:** 2 parallel requests ≈ 2× aggregate decode; from 16K
     context 4 parallel is worse than 2, from 64K worse than 1. → SKILL.md now
     says at most 2 in parallel.
   - **TurboQuant KV 8-bit** was on for all their Qwen runs. **Tested on
     `deep` 2026-10-01 and rejected.** One 56.7K-token request through
     `:deep`, model freshly loaded each time (probe: peak of the admin
     `/api/stats` `memory_pressure.current_bytes` while the request ran):

     | | TTFT | decode | peak memory (model + run) |
     |---|---|---|---|
     | off | 160 s | 21–22 tok/s | 30.0 GB |
     | 8-bit | 197 s | 10.8 tok/s | 39.3 GB |

     oMLX logged "converted 15/64 cache layers": in Qwen3.6/3.8's hybrid
     design only every 4th layer keeps a KV cache, the rest have fixed-size
     linear-attention state, so there is little KV to compress and the
     conversion costs more than it saves. Their gains were on other
     architectures. Leave it off for these models; re-test only for a model
     whose layers are mostly full attention.
   - **Memory ceiling under 0.7.0's guard** (`balanced` tier): oMLX's soft/hard
     limits here are ~38/40 GB, varying with what else runs. Both tier models
     are 37.7 GB, and one long `deep` request held ~13.6 GB more (oMLX keeps
     the cache for reuse). So a long `deep` session evicts the 35B and the
     next `fast`/`code` call reloads it. If that churn bites, try the
     `aggressive` tier (keeps ~2% of RAM free instead of ~8%) — at the cost of
     headroom for other apps.
   - **Determinism:** their oMLX JSON extraction (~600-token outputs, 8–16
     concurrent) repeated identically in only 1/16 cases at temperature 0.
     Checked here for `decide`: 8 sequential + 8 four-way-parallel label calls
     and 8 schema calls were all identical — at decide's scale it holds.
   - **Splash** (incoai/Qwen3.6-35B-A3B-Splash, a separate speculative-decoding
     server) did their JSON extraction 2–2.6× faster than oMLX with the same
     model. A candidate back end for bulk `decide --schema` work; not tried.
   - Flash-Next and GLM-5.3-Flash got the biggest gains, but neither fits 64 GB.

9. **Clef — Cloudflare's open Jev/SystemOne model (2026-10-02, rejected).**
   `Cloudflare/clef` (27B) and `clef-flash` (9B) are Qwen3.8 backbones with a
   joint schema head: one forward pass returns a probability for every option
   of every typed question (`choice`, ordered `score`, yes/no `noul`). Not a
   chat model — **oMLX can't serve it**; the mlx-community builds ship
   `clef_mlx.py` (`predict`, or `serve` = a SystemOne-compatible
   `POST /v1/systemone` server, one request at a time). Used the Jev way
   (TypeSafe's guide): plain, literal criteria per option; many questions per
   call; act on `confidence`, escalate below a threshold. Both engines got
   identical wording (AGENTS.md's Area descriptions, the sharp bug
   definition), 45 BACKLOG items, oMLX models unloaded during the Clef runs:

   | Per item | type | area | latency |
   |---|---|---|---|
   | Qwen3.8-27B `:decide`, same wording | **35** | 37 | 2.0 s (2 calls) |
   | Qwen3.8-27B `:decide`, `eval_decide.py`'s terse wording | 31 | **42** | 1.5 s |
   | clef-flash-4bit, area as one `choice` | 32 | 35 | **0.3 s** (2 questions) |
   | clef-flash-4bit, a `noul` per area (13 questions, one call) | 32 | 38 | 1.0 s |
   | clef-4bit (27B), a `noul` per area | 34 | 39 | 4.0 s |

   - **Accuracy is a wash; nothing earns a second runtime.** No Clef variant
     beats the incumbent's best area score, and the 7 GB (flash) it would keep
     resident sits on top of the 37.7 GB tier models.
   - **The cascade (Clef if confident, else Qwen) adds ~1 item.** Clef's
     confidence is honest (flash ≥ 0.8: type 21/25 right, area 3/3) but on
     11-way area it is rarely confident (3 of 45 items at ≥ 0.8), so nearly
     everything escalates.
   - **"A tenth question costs almost no time" is a GPU-cloud claim.** On this
     Mac 13 questions took 1.0 s vs 0.3 s for 2 — the questions are prompt tokens.
   - **Wording moved the score more than the model did:** Qwen went 42 → 37 on
     area from the longer AGENTS.md descriptions alone. With 45 items a 2–3
     item gap is noise; compare models only on identical wording.

   Revisit when a job needs calibrated probabilities across many questions at
   once — e.g. bulk triage that should abstain rather than guess — or a Clef
   build oMLX can serve. Re-run with `scripts/eval_clef.py` (Clef + the
   incumbent on identical wording, plus the cascade table).

## Gotcha: unknown model names must fail

`settings.json` → `model.model_fallback: true` makes oMLX answer a request for
a model it doesn't know with some other loaded model, with that model's
defaults — no error. A typo in a Pi `id` or a retired profile name then
*works*, wrongly. It was turned **off** on 2026-09-28 (admin API
`POST /admin/api/global-settings {"model_fallback": false}`); an unknown name
now returns "Model '…' not found". If a request answers from the wrong model,
check this first. `decide.py` still resolves the `:decide` ID from
`/v1/models`, and verification still checks `model=` and `max_tokens=` in the
server log.

## When a new model comes out

1. **Download** it into `~/.omlx/models` (oMLX's model manager or HF). Prefer a
   build that keeps MTP heads so the Lightning MTP toggle can speed decode ~1.5×;
   mlx-community conversions strip `mtp.*` tensors.
   - **First choice: `Jundot/<model>-oQ<level>e-mtp`** — oMLX's author publishes
     oQ builds with imatrix (`e`) and MTP preserved, which is exactly what
     quantizing the BF16 yourself would produce, without the ~2 bytes/param
     download. The model card benchmarks each level against the original.
   - Quantize yourself (oQ, "Preserve MTP", oQe) only when no such build
     exists, or for a fine-tune (graft its base model's MTP head with
     "Combine other model's MTP head").
   - **Check the repo before downloading, not oMLX's list.** The admin search's
     SIZE column and "High OOM risk" badge were wrong for these repos (showed
     133 GB for a 21.6 GB repo). Real size and MTP presence:
     ```bash
     r=<org/repo>
     curl -s "https://huggingface.co/api/models/$r/tree/main?recursive=true" | python3 -c "import json,sys;print(sum(f.get('size',0) for f in json.load(sys.stdin))/1e9,'GB')"
     curl -sL "https://huggingface.co/$r/resolve/main/model.safetensors.index.json" | grep -c '\.mtp\.'
     ```
   - A repo of ~0.5 GB named `…-MTP-4bit` is only the MTP head (a drafter or
     side-car), not a model to serve.
2. **Measure** against the incumbent, with other models unloaded
   (`POST /admin/api/models/<m>/unload`): `scripts/bench_decode.py <real file> <old> <new>`
   for decode speed (prefill excluded, median of 3), `scripts/eval_decide.py`
   for decide. Enable MTP on the new model and bench again. Record both in
   "How the choices were derived".
3. **Check memory** with the KV formula above for the tier's context.
4. **Log in to the admin API** (the main API key grants admin; sub-keys don't):
   ```bash
   KEY=$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.omlx/settings.json')))['auth']['api_key'])")
   B=http://127.0.0.1:8000/admin; J=$(mktemp)
   curl -s -c $J -H 'Content-Type: application/json' -d "{\"api_key\":\"$KEY\"}" $B/api/login
   curl -s -b $J $B/api/profile-templates            # the tier definitions
   ```
5. **Create the tier profile on the new model**: the template's settings plus
   the new model's recommended sampling from its model card:
   ```bash
   curl -s -b $J -H 'Content-Type: application/json' "$B/api/models/<NewModel>/profiles" -d '{
     "name":"code","display_name":"code","api_name":"code","source_template":"code","expose_as_model":true,
     "settings":{ <template settings>, <model-card sampling> }}'
   ```
   The API does not merge the template in; copy its settings explicitly.
6. **Repoint Pi** (fast/code/deep only — decide finds its model by the `:decide` suffix; keep exactly one exposed profile named `decide`): in `~/.pi/agent/models.json` change that tier's `id` to
   `<NewModel>:<tier>` and the model part of its `name` (keep the `<tier> — `
   prefix); set `contextWindow`/`maxTokens` to the profile's values and
   `reasoning` to the profile's `enable_thinking`.
7. **Verify** — both must pass:
   ```bash
   pi --offline --list-models omlx
   pi -p --no-session -nc -ns --model omlx/<tier> --tools read "Reply with exactly: PONG" </dev/null
   grep 'Chat completion' ~/.omlx/logs/server.log | tail -1   # model= and max_tokens= match the tier
   ```
8. **Retire** the old profile (`DELETE $B/api/models/<OldModel>/profiles/<tier>`)
   — for decide, immediately: `decide.py` fails while two `:decide` IDs exist.
   Repoint oMLX's `omlx launch` defaults (see Current mapping). Once nothing
   names the old model (`grep -rl <OldModel> ~/.omlx/*.json ~/.pi/agent`),
   delete it from disk with `DELETE $B/api/hf/models/<OldModel>` — it removes
   the first folder of that name across all `model_dirs`, so `find` them first
   to be sure there is one. Update the mapping table above with the date.

Changing a tier's *task* definition (e.g. a bigger thinking budget) means
updating the template **and** every profile made from it (`PUT
$B/api/models/<model>/profiles/<tier>`), then this file.
