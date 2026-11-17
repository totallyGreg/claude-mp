# Model storage — one shared, iCloud-synced folder

Model weights live once, in `~/Documents/LLMs/<org>/<model>/` (iCloud Drive),
so every Mac signed in to the account and every engine (oMLX, Splash through
oMLX, LM Studio) reads the same copy. Set up 2026-11-16.

## Layout

| Folder | Role |
|--------|------|
| `~/.omlx/models` | oMLX's **first** model folder: where oMLX downloads land. Local, not synced. Normally empty |
| `~/Documents/LLMs` | The shared store, added as an oMLX model folder. Complete models only |
| `~/.cache/huggingface/hub` | HF cache: Splash's DFlash2 drafts and helper models. Local, per Mac |

oMLX names a model by its folder (`Qwen3.6-35B-A3B-oQ4e-mtp`), not its path,
so moving a model between folders keeps its id, its profiles (`:fast`, `:code`,
`:deep`), its `model_settings.json` entry (e.g. `external_engine: splash`) and
every Pi and Claude Code tier reference.

## Rules

1. **Pin before relying on it.** Finder → right-click `LLMs` → **Keep
   Downloaded** (sets `com.apple.fileprovider.pinned#PX` on the folder). With
   *Optimize Mac Storage* on, unpinned files get evicted to iCloud.
2. **Check nothing is evicted before a rescan** (oMLX restart, model-folder
   change, `POST /admin/api/reload`):
   ```bash
   find ~/Documents/LLMs -type f -exec ls -lO {} + | grep -c dataless   # must be 0
   ```
3. **Download locally, then move.** A model downloads into `~/.omlx/models`;
   move `<org>/<model>` into `~/Documents/LLMs/` only when it's complete, so
   no partial model syncs to every Mac. Same disk → `mv` is a rename.
4. **Unload before moving** a model oMLX has loaded, then
   `POST /admin/api/reload` (admin key from `~/.omlx/settings.json`).

## Why the rules — what happened

- **Eviction stalls the whole server, not one model.** Adding the folder while
  it was evicted: oMLX's scan opened `gpt-oss-20b-MXFP4.gguf` to read its
  header, and that read blocked until iCloud fetched all 12.1 GB. `/v1/models`
  stopped answering (HTTP 000) and the settings change didn't save until the
  download finished. MLX weights aren't read during a scan, but a load of an
  evicted model blocks the same way.
- **Evicted folders hide incomplete copies.** Five of nine old models there had
  metadata but no weights; deleted.

## Measured after the move

`Qwen3.6-35B-A3B-oQ4e-mtp` from `~/Documents/LLMs/Jundot/`: same id, Splash
1.6.1 started in 17 s, and `bench_decode.py` gave 3,428 / 141.2 tok/s
(prefill / decode) against 3,445 / 143.4 from `~/.omlx/models`
(tiers.md derivation 18) — no change.

## Costs

| Cost | Handling |
|------|----------|
| Every Mac downloads every model (45 GB on 2026-11-16) | Fine for Macs that run them; a Mac that doesn't can leave the folder unpinned and never point oMLX at it |
| Per-Mac config isn't shared: `~/.omlx` settings, profiles, `model_settings.json`, Splash drafts in the HF cache | Set up each Mac per tiers.md; the admin API's `external_engines[].reason` names a missing draft |
| iCloud ` 2` conflict copies if two Macs write the same model | Download a model on one Mac only; look for ` 2` files after a sync |
| Splash re-hashes weights when file times change | One full read on the next load; seen as a slower first start |
| Not verified: whether Keep Downloaded on the folder covers files moved in later | Rule 2's check catches it |
