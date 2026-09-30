---
title: "refactor: plugin.json as single source of truth + enforced version bumps"
type: refactor
date: 2026-09-29
issue: "#193"
supersedes: docs/plans/2026-02-16-refactor-plugin-versioning-strategy-plan.md (sync model)
---

# refactor: plugin.json as single source of truth + enforced version bumps

## Goal

Keep releases in this repo simple and automatic:

1. A plugin's metadata (version, description, author) lives only in its `plugin.json`.
2. Any change to a plugin must raise that plugin's version, and any change to a skill must raise
   that skill's version. Otherwise marketplace subscribers never receive the change, because
   Claude Code updates a plugin only when its version string changes.
3. Use Anthropic's own tooling (`claude plugin validate`, `claude plugin tag`) wherever it covers
   the job. Keep custom code only for what it doesn't cover.

## Why the current model fails

- `marketplace.json` repeats each plugin's `version`, `description` and `author`. `sync.py` copies
  versions into it on every commit, so every release of any plugin edits one shared file. Parallel
  branches conflict there (PR #192).
- The existing "version bump" check only warns, and it passes if SKILL.md or plugin.json is merely
  *staged*, even when the version didn't change.
- Two hook copies and two copies of the scripts (`.git/hooks/pre-commit` → `scripts/*.py`, and
  `.githooks/pre-commit` → foundry scripts) have drifted apart.
- Anthropic's docs: *"Don't set `version` in both `plugin.json` and the marketplace entry."* For
  relative-path plugins, `plugin.json` wins, and display fields the entry omits are read from
  `plugin.json`.

## Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Marketplace entries hold only `name`, `source` and `category` | `category` is a catalog field; everything else is manifest data |
| D2 | Move the curated entry `description` into `plugin.json`; add `author` to the 3 manifests missing it | Users keep seeing exactly the same listing text |
| D3 | **Bump-first, enforced locally.** Base = `git merge-base HEAD origin/<default>`. The pre-commit hook blocks the commit if a plugin changed since base and its `plugin.json` version is not semver-greater than at base | One rule on main and on branches; no CI to maintain; merging main into a branch moves the base forward |
| D4 | **Skill rule, same mechanism.** If any file under `skills/<s>/` changed since base, `SKILL.md` `metadata.version` must be semver-greater than at base | Skill version identifies the skill change; the skill change is a plugin change, so the plugin must bump too |
| D5 | New plugin or skill (absent at base) passes if it declares a version; deleted skills are ignored | |
| D6 | Schema validation → `claude plugin validate`: strict for the marketplace, normal for each changed plugin (errors block, warnings print) | Existing plugin warnings (commands missing frontmatter, unquoted `${CLAUDE_PLUGIN_ROOT}`) shouldn't block unrelated work. Follow-up issue to clean them up |
| D7 | `validate.py` keeps only what Anthropic's tooling doesn't do: the version-bump check, the reverse scan (`--fix`, which adds `{name, source}`), and the structure check. It drops its duplicate schema checks and warns when an entry repeats `version` | Less code to maintain; matches Anthropic's official schema by construction |
| D8 | Retire `sync.py` (foundry and repo copies) and `/mp-sync`. `/mp-status` reports which plugins and skills still need a bump | Nothing left to sync |
| D9 | One tracked hook: `.githooks/pre-commit`, activated with `git config core.hooksPath .githooks`. The hook checks only; it never rewrites or stages files | Removes the copied `scripts/` and the auto-`git add` |
| D10 | `setup.py` for external repos: copy `validate.py` only and install the checks-only hook | External marketplaces get the same model |
| D11 | `scaffold.py`: write JSON with `ensure_ascii=False`; SKILL.md template uses `metadata.version` (Agent Skills spec) | Formatting stability and spec compliance |
| D12 | Release tagging: document `claude plugin tag <plugin-dir> --push` after merge (optional, gives `<name>--v<version>` tags for dependency ranges) | Anthropic tooling, no custom code |

## Enforcement details (D3/D4)

- The pre-commit hook reads versions from the **index** (`git show :path`); `/mp-status` reads the
  working tree. Both compare against `git show <base>:path`.
- Changed paths: `git diff --cached --name-only <base>` in the hook; `git diff --name-only <base>`
  otherwise.
- Default branch: `git symbolic-ref refs/remotes/origin/HEAD`, falling back to `origin/main`. If no
  base can be resolved (no remote), the check is skipped with a warning, never a false block.
- Versions compare as semver `(major, minor, patch)`.
- A stale `origin/main` can let a check pass locally; the plugin.json version line then conflicts
  at merge and forces a re-bump. Acceptable. The hook doesn't fetch (no network in hooks).
- Escape hatch: `git commit --no-verify` (standard git).

## Work breakdown

1. **foundry / marketplace-manager** (bump first: skill 4.0.0 → 5.0.0, foundry 1.7.0 → 2.0.0,
   breaking because `/mp-sync` and `sync.py` are removed)
   - `validate.py`: version check (`--check-versions`, `--staged`, `--base`), drop duplicate
     schema checks, warn on entry `version`
   - Delete `scripts/repo/sync.py` and `commands/mp-sync.md`; rewrite `mp-status`, `mp-validate`
     and `mp-add`
   - `setup.py`, `scaffold.py` per D10/D11
   - Tests for the version check (temporary git repo fixtures)
   - SKILL.md and references; `ss-improve`, `ss-refresh` and `as-improve` release steps
   - Fix foundry's own strict warnings (command frontmatter, hook quoting)
2. **Repo**
   - Slim `marketplace.json`; move descriptions/authors into `plugin.json` with patch bumps
     (dogfoods D3)
   - `.githooks/pre-commit` per D6/D9; delete `scripts/`; set `core.hooksPath`
   - `WORKFLOW.md`, `.claude/CLAUDE.md`, root `README.md`
3. **Verify**
   - Unit tests pass; hook blocks an unbumped change and passes a bumped one
   - `claude plugin validate . --strict` passes
   - skillsmith eval for marketplace-manager (and any other skill touched), with `--verify`
4. **Follow-up issue**: strict-validator warnings in ai-risk-mapper, gateway-manager and attache

## Acceptance criteria

- [ ] `marketplace.json` entries contain only `name`, `source`, `category`
- [ ] Committing a change under `plugins/<p>/` without raising `<p>`'s plugin.json version fails
- [ ] Committing a change under `plugins/<p>/skills/<s>/` without raising `<s>`'s SKILL.md version fails
- [ ] Bumped commits pass; later commits on the same branch pass without re-bumping
- [ ] No script writes `marketplace.json` during commit; the hook never stages files
- [ ] `claude plugin validate . --strict` passes
- [ ] No references to `sync.py` / `/mp-sync` remain outside historical plans
