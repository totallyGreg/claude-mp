---
title: "feat: Marketplace manager external repo support"
type: feat
status: active
date: 2026-03-19
origin: 800 Generated/820 Brainstorms/2026-03-19-marketplace-manager-external-repo-support-requirements.md
---

# feat: Marketplace Manager External Repo Support

## Overview

Make marketplace-manager's pre-commit hook work when installed as an external plugin from the Claude plugin cache, not just when its source code lives inside the consuming repo. This enables any repo with a `marketplace.json` to get automatic version sync protection.

## Problem Statement

The pre-commit hook template (`pre-commit.template:36-49`) searches only within `$REPO_ROOT` for Python scripts. When marketplace-manager is installed from the plugin cache (`~/.claude/plugins/cache/...`), the scripts don't exist in the consuming repo — the hook silently skips all checks, providing no value.

(see origin: 800 Generated/820 Brainstorms/2026-03-19-marketplace-manager-external-repo-support-requirements.md)

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Script discovery mechanism | Embed path at install time via `sed` substitution | Simplest approach; no runtime discovery or config files needed |
| Discovery priority order | Repo-local first, then embedded path | Prevents stale-cache bugs in source repo; embedded path is fallback for external repos |
| Template substitution marker | `EMBEDDED_SCRIPTS_DIR=""` variable at top of template | Clean, readable; `sed` replaces the empty string with actual path |
| Hook update message | Also embedded at install time | External users need correct reinstall path, not repo-relative path |
| validate_hook.py changes | Normalize embedded path before template comparison | Prevents false "does not match template" warnings |

## Technical Approach

### Phase 1: Pre-commit template changes

**File:** `plugins/marketplace-manager/skills/marketplace-manager/scripts/pre-commit.template`

Add two new variables near the top (after `HOOK_VERSION`):

```bash
# Embedded at install time by install_hook.sh
# If empty, falls back to repo-local discovery
EMBEDDED_SCRIPTS_DIR=""
EMBEDDED_INSTALL_CMD=""
```

Restructure script discovery (lines 36-56) with new priority order:

1. **Repo-local discovery** (existing logic, lines 38-48) — try `$REPO_ROOT/plugins/marketplace-manager/...`, then `$REPO_ROOT/skills/marketplace-manager/...`, then `find` fallback
2. **Embedded path** (new) — if repo-local failed and `EMBEDDED_SCRIPTS_DIR` is non-empty and the directory exists, use it
3. **Give up gracefully** — warn user, suggest reinstall using `EMBEDDED_INSTALL_CMD` if available

Also update the "hook outdated" message (line 64) to use `EMBEDDED_INSTALL_CMD` when set, instead of the hardcoded repo-relative path.

### Phase 2: install_hook.sh changes

**File:** `plugins/marketplace-manager/skills/marketplace-manager/scripts/install_hook.sh`

Replace the bare `cp` on line 134 with copy + `sed` substitution:

```bash
# Copy template
cp "$TEMPLATE_PATH" "$HOOK_PATH"

# Embed the resolved script directory path (portable sed -i across macOS and Linux)
sed_inplace() { if [[ "$OSTYPE" == "darwin"* ]]; then sed -i '' "$@"; else sed -i "$@"; fi; }
sed_inplace "s|^EMBEDDED_SCRIPTS_DIR=.*|EMBEDDED_SCRIPTS_DIR=\"$SCRIPT_DIR\"|" "$HOOK_PATH"

# Embed the install command for update messages
INSTALL_CMD="bash $SCRIPT_DIR/install_hook.sh"
sed_inplace "s|^EMBEDDED_INSTALL_CMD=.*|EMBEDDED_INSTALL_CMD=\"$INSTALL_CMD\"|" "$HOOK_PATH"
```

Note: `SCRIPT_DIR` is already resolved via `BASH_SOURCE` on line 50. When run from the plugin cache, this resolves to the cache path. When run from the source repo, it resolves to the repo-local path. Both are correct.

The `sed_inplace` helper handles the macOS vs Linux `sed -i` difference (macOS requires an empty string argument, Linux does not).

Update the dry-run output to mention the path embedding step.

### Phase 3: validate_hook.py changes

**File:** `plugins/marketplace-manager/skills/marketplace-manager/scripts/validate_hook.py`

The `matches_template` check (lines 122-128) compares hook content byte-for-byte against the template. After install-time `sed` substitution, the hook will differ from the template on the two embedded lines.

Fix: normalize both files before comparison by stripping the `EMBEDDED_SCRIPTS_DIR=` and `EMBEDDED_INSTALL_CMD=` lines, or by replacing their values with empty strings before diffing.

### Phase 4: Marketplace init for external repos

When an external repo doesn't yet have `.claude-plugin/marketplace.json`, the hook (and scripts) have nothing to manage. Add a lightweight init capability so external repos can bootstrap their marketplace:

**Option A (minimal):** `install_hook.sh` checks for `marketplace.json` and offers to create a minimal one:

```bash
if [ ! -f "$MARKETPLACE_JSON" ]; then
    echo "No marketplace.json found. Create one? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        mkdir -p "$REPO_ROOT/.claude-plugin"
        # Generate minimal marketplace.json with repo name
        REPO_NAME=$(basename "$REPO_ROOT")
        cat > "$MARKETPLACE_JSON" << EOF
{
  "name": "$REPO_NAME",
  "version": "1.0.0",
  "plugins": []
}
EOF
        echo "Created $MARKETPLACE_JSON"
    fi
fi
```

**Option B (use existing):** The `add_to_marketplace.py init` command already exists. Document it in the external usage section and have `install_hook.sh` print a suggestion when marketplace.json is missing.

Recommend **Option B** — reuse existing tooling, keep `install_hook.sh` focused on hook installation. The init prompt in the install script just prints the command to run.

### Phase 5: SKILL.md documentation

**File:** `plugins/marketplace-manager/skills/marketplace-manager/SKILL.md`

Add an "External Repo Usage" section after "Git Integration" explaining:

1. How to install the hook from the plugin cache:
   ```bash
   bash ${CLAUDE_PLUGIN_ROOT}/skills/marketplace-manager/scripts/install_hook.sh
   ```
2. That the consuming repo needs `.claude-plugin/marketplace.json`
3. That the hook auto-embeds the script path — no manual config needed
4. How to update the hook after plugin version changes (re-run install)

### Phase 6: Version bump

- Bump `SKILL.md` frontmatter `metadata.version` to `2.7.0`
- Bump `plugin.json` version to `2.7.0`
- Bump `HOOK_VERSION` in `pre-commit.template` to `5.1.0` (additive change — new variables, no breaking changes)
- Run skillsmith evaluation, record score

## Acceptance Criteria

- [ ] Hook works in external repo: install from cache path, commit triggers version sync
- [ ] Hook works in source repo: existing repo-local discovery still takes priority
- [ ] Stale cache path: hook falls back to repo-local discovery, then warns gracefully
- [ ] `validate_hook.py --json` reports correct status for hooks with embedded paths
- [ ] Hook update message shows correct reinstall path for external users
- [ ] SKILL.md documents external repo usage with install instructions
- [ ] `install_hook.sh` suggests marketplace init when `marketplace.json` is missing
- [ ] Skillsmith evaluation score >= 95/100

## Files Changed

| File | Change |
|------|--------|
| `scripts/pre-commit.template` | Add `EMBEDDED_SCRIPTS_DIR`/`EMBEDDED_INSTALL_CMD` variables; restructure discovery order |
| `scripts/install_hook.sh` | Replace `cp` with copy + `sed` substitution; add marketplace init hint; update dry-run output |
| `scripts/validate_hook.py` | Normalize embedded vars before template comparison |
| `SKILL.md` | Add "External Repo Usage" section; bump version to 2.7.0 |
| `.claude-plugin/plugin.json` | Bump version to 2.7.0 |

All paths relative to `plugins/marketplace-manager/skills/marketplace-manager/`.

## Test Scenarios

1. **Source repo install + commit** — regression test, verify repo-local scripts used
2. **External repo install from cache + commit** — core new flow
3. **Cache cleared after install + commit** — verify fallback + warning
4. **Plugin version updated in cache + commit** — verify stale path detection + fallback
5. **`validate_hook.py` on external hook** — verify no false warnings

## Sources

- **Origin document:** 800 Generated/820 Brainstorms/2026-03-19-marketplace-manager-external-repo-support-requirements.md — Key decisions: embed path at install time, fallback to repo-local, git-host agnostic
- GitLab issue: https://code.pan.run/airs/tme/claude-skills/-/issues/1
- Current pre-commit template: `plugins/marketplace-manager/skills/marketplace-manager/scripts/pre-commit.template`
- Current install script: `plugins/marketplace-manager/skills/marketplace-manager/scripts/install_hook.sh`
- Lesson: `docs/plans/2026-03-03-fix-marketplace-manager-all-open-issues-plan.md` — two-pass `find_repo_root()` design
- Lesson: `docs/plans/2025-12-31-marketplace-hooks-improvement.md` — dynamic path discovery design
