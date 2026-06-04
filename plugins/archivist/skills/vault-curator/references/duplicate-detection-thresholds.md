---
name: Detection & Visualization Thresholds
description: Documents the policy thresholds used by find_similar_notes.py, check_collection_health.py, and generate_canvas.py — what each default means, when to override, and recommended ranges.
load_when: Tuning duplicate detection, collection health thresholds, canvas layouts; or when a script's default output looks too noisy or too sparse.
---

# Detection & Visualization Thresholds

Policy reference for the three scripts that have user-tunable thresholds. **Defaults are calibrated for vaults of 1k–10k notes** with typical taxonomies. Override when the defaults produce too much (noisy) or too little (missed) output.

## Duplicate Similarity — `find_similar_notes.py`

| Param | Default | Range | Effect |
|---|---|---|---|
| `--min-similarity` | **80** (%) | 60–95 | Title-similarity floor for Tier 2 (similar titles + matching tags). Tier 1 (identical titles) is unaffected. |
| `--max-groups` | (no default cap) | 5–50 | Limits how many duplicate groups are returned; pair with progressive review on large vaults. |

**Tuning guide:**
- **Lower to ~70** when surfacing variants ("Meeting Notes — Q1", "Meeting Notes Q1") and the default misses obvious pairs.
- **Raise to ~90** when the default returns false positives (notes that share a prefix but aren't really duplicates).
- **Never drop below 60** — the algorithm uses normalized Levenshtein; below 60% you're matching unrelated notes.

## Collection Health — `check_collection_health.py`

| Param | Default | Range | Effect |
|---|---|---|---|
| `--coverage-threshold` | **60** (%) | 40–80 | Minimum share of notes that must agree on a `fileClass` value for density-based collection candidacy. |

**Tuning guide:**
- The 60% default assumes a mature collection where some legacy/edge notes legitimately lack `fileClass`.
- **Lower to ~40** to surface emerging collections (folders just starting to organize around a fileClass).
- **Raise to ~80** during strictness audits — only fully-typed collections will register as candidates.

**Health bucket definitions** are in `collection-health-criteria.md` — this doc covers *thresholds*, that doc covers *what each bucket means*.

## Canvas Layout — `generate_canvas.py`

| Param | Default | Range | Effect |
|---|---|---|---|
| `--max-nodes` | **50** | 20–200 | Above this count, the script clusters notes by folder rather than rendering each as a node. Beyond ~200 canvases become unreadable in Obsidian. |
| `--node-width` | **300** (px) | 200–500 | Card width. Wider nodes wrap less but consume more canvas real estate. |
| `--node-height` | **120** (px) | 80–200 | Card height. Match to typical title + frontmatter-preview length. |

**Tuning guide:**
- **Default (50/300/120)** produces a readable 7×7 grid that fits Obsidian's default zoom.
- **Lower max-nodes (20–30)** for executive-summary canvases — a few key entry points only.
- **Raise max-nodes (100+)** only when the canvas is intended for desktop review, not handheld.
- Pair tighter (`--node-width 200`) with larger counts to keep the canvas square; pair wider (`--node-width 400`) with cluster nodes for readability.

## When to override vs. when to live with defaults

Override at the **invocation site** (CLI args) for one-off tuning. If you're consistently overriding the same value across many invocations, raise the floor in the script itself rather than putting the value in user prompts — the agent should not have to remember per-vault thresholds.

For per-vault threshold customization (e.g., "this vault always uses 70% similarity"), the right place is `_vault-profile.md` under a `## Tunings` section — the agent reads it at init and applies the overrides automatically.
