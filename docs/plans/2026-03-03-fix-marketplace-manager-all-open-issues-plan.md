---
title: "fix: Resolve all open marketplace-manager issues"
type: fix
status: completed
date: 2026-03-03
issues: [25, 30, 75, 78]
---

# fix: Resolve all open marketplace-manager issues

Consolidates four open marketplace-manager issues into a single implementation pass. Issues #75 and #78 both modify the pre-commit hook template and share a single hook version bump.

## Issues

| Issue | Title | Type | Complexity |
|-------|-------|------|------------|
| #25 | Clarify relationship with plugin-dev | docs | Trivial |
| #30 | Fix migrate_to_plugin.py repo root detection | bug | Low |
| #75 | Add plugin.json schema validation | enhancement | Medium |
| #78 | Pre-commit hook: handle skill drift separately | bug | Medium |

## Key Decisions

These resolve the critical questions from SpecFlow analysis:

1. **When both `mismatches` AND `skill_drift` exist:** Auto-sync mismatches first, then block on drift. User fixes plugin.json and re-commits cleanly.

2. **Skill drift blocks the commit (`exit 1`)** with a clear actionable message: "plugin.json needs a version bump to match SKILL.md".

3. **JSON parsing in hook uses `python3 -c`** — Python is already a dependency, avoids adding `jq`.

4. **plugin.json allowlist:** `name`, `version`, `description`, `author`, `license`, `keywords`, `mcpServers`. Conservative — only fields confirmed in the Anthropic plugin spec. If a new field is added upstream, the validation will flag it and the allowlist can be expanded.

5. **plugin.json required fields:** `name`, `version`, `description`.

6. **`utils.py.template` gets the same fix** as `utils.py` to prevent propagating the bug.

7. **`plugin-dev` is an official Anthropic plugin** (installed separately, not in this repo). The See Also reference should say: "For creating plugin components (skills, commands, agents, hooks), see the official `plugin-dev` plugin."

8. **Plugins without plugin.json:** Skip silently — single-skill plugins with `skills: ["./"]` don't use plugin.json.

9. **`--check-staged` step stays as-is** — warning-only, exit code is sufficient.

10. **`errors` array in hook:** Warn but don't block — version source detection errors are informational.

## Version Bumps

| File | Current | New |
|------|---------|-----|
| `SKILL.md` metadata.version | 2.4.0 | 2.5.0 |
| `plugin.json` version | 2.4.0 | 2.5.0 |
| `pre-commit.template` HOOK_VERSION | 4.0.0 | 5.0.0 |
| `marketplace.json` (auto-synced) | 2.4.0 | 2.5.0 |

---

## Phase 1: Documentation (#25)

**Files:**
- `plugins/marketplace-manager/skills/marketplace-manager/SKILL.md` (See Also section, ~line 200)

**Change:** Add plugin-dev reference:

```markdown
## See Also

- **skillsmith** - Creates and improves skills
- **plugin-dev** - Official Anthropic plugin for creating plugin components (skills, commands, agents, hooks)
- Workflow: `plugin-dev` (build) -> `skillsmith` (improve) -> `marketplace-manager` (publish)
```

**Acceptance:**
- [x] plugin-dev reference added to See Also
- [x] Workflow chain documented

---

## Phase 2: Fix `find_repo_root()` (#30)

**Files:**
- `plugins/marketplace-manager/skills/marketplace-manager/scripts/utils.py` (lines 11-43)
- `plugins/marketplace-manager/skills/marketplace-manager/scripts/templates/utils.py.template`

**Change:** Two-pass search — `.git` first across all parents, then `.claude-plugin` fallback:

```python
def find_repo_root(start_path=None):
    """Find repository root by traversing up from start_path.

    Two-pass search:
    1. Look for .git directory (most reliable, avoids stopping at plugin-level .claude-plugin)
    2. Fall back to .claude-plugin directory (for standalone plugin repos without .git)
    """
    start = Path(start_path).resolve() if start_path else Path.cwd()

    # Pass 1: Look for .git
    current = start
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    if (current / ".git").exists():
        return current

    # Pass 2: Fall back to .claude-plugin
    current = start
    while current != current.parent:
        if (current / ".claude-plugin").exists():
            return current
        current = current.parent
    if (current / ".claude-plugin").exists():
        return current

    return None
```

**Regression check:** Verify these scripts still work after the change:
- `detect_version_changes.py`
- `sync_marketplace_versions.py`
- `add_to_marketplace.py`
- `migrate_to_plugin.py`

**Acceptance:**
- [x] `find_repo_root()` returns repo root when CWD is inside a plugin directory
- [x] `find_repo_root()` still works from repo root
- [x] `find_repo_root()` works in standalone plugin repos (no `.git`, has `.claude-plugin`)
- [x] `utils.py.template` updated with same fix

---

## Phase 3: plugin.json Schema Validation (#75)

**Files:**
- `plugins/marketplace-manager/skills/marketplace-manager/scripts/add_to_marketplace.py`

**Changes:**

1. Add constants and `validate_plugin_json()` helper (as defined in existing plan `docs/plans/2026-03-02-fix-marketplace-plugin-json-schema-validation-plan.md`)

2. Move `source_dir` computation outside the `if 'skills' in plugin` block in `validate_marketplace()` so it's available unconditionally:

```python
        # Resolve source directory (needed for both skill and plugin.json validation)
        source_path = plugin.get('source', './')
        source_path_clean = source_path.lstrip('./')
        source_dir = repo_root / source_path_clean if source_path_clean else repo_root

        # Validate plugin.json schema
        plugin_json_path = source_dir / '.claude-plugin' / 'plugin.json'
        if plugin_json_path.exists():
            issues.extend(validate_plugin_json(plugin_json_path, plugin_name))

        # Existing skills validation block follows...
        if 'skills' in plugin and isinstance(plugin['skills'], list):
            # ... (uses source_dir, already computed above)
```

3. Update `/mp-validate` command docs if needed.

**Acceptance:**
- [x] `validate_plugin_json()` detects unknown fields with actionable error message
- [x] Required fields (`name`, `version`, `description`) checked
- [x] All 7 current plugins pass validation
- [x] Plugins without plugin.json skipped silently
- [x] `/mp-validate` reports plugin.json issues

---

## Phase 4: Pre-commit Hook Drift Handling (#78)

**Files:**
- `plugins/marketplace-manager/skills/marketplace-manager/scripts/pre-commit.template`

**Change:** Replace step 2 (lines 79-102) to parse JSON and handle drift vs mismatches separately:

```bash
# Step 2: Detect version mismatches and skill drift
echo -e "${BLUE}🔍 Checking marketplace version sync...${NC}"
DETECT_OUTPUT=$(python3 "$DETECT_SCRIPT" --format json 2>/dev/null)
DETECT_EXIT=$?

if [ $DETECT_EXIT -ne 0 ]; then
    # Parse JSON to determine what kind of issues exist
    HAS_MISMATCHES=$(python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
sys.exit(0 if data.get('mismatches') else 1)
" <<< "$DETECT_OUTPUT" 2>/dev/null && echo "yes" || echo "no")

    HAS_DRIFT=$(python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
sys.exit(0 if data.get('skill_drift') else 1)
" <<< "$DETECT_OUTPUT" 2>/dev/null && echo "yes" || echo "no")

    HAS_ERRORS=$(python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
sys.exit(0 if data.get('errors') else 1)
" <<< "$DETECT_OUTPUT" 2>/dev/null && echo "yes" || echo "no")

    # Handle sync mismatches (auto-fixable)
    if [ "$HAS_MISMATCHES" = "yes" ]; then
        echo -e "${BLUE}🔄 Auto-syncing marketplace.json...${NC}"
        if python3 "$SYNC_SCRIPT" --mode=auto 2>&1 | grep -q "Updated"; then
            git add "$MARKETPLACE_JSON"
            README_PATH="$REPO_ROOT/README.md"
            if [ -f "$README_PATH" ] && ! git diff --quiet "$README_PATH" 2>/dev/null; then
                git add "$README_PATH"
            fi
            echo -e "${GREEN}✅ marketplace.json updated and staged${NC}"
        else
            echo -e "${RED}❌ Failed to sync marketplace.json${NC}"
            echo -e "${YELLOW}   Please run: uv run scripts/sync_marketplace_versions.py${NC}"
            echo -e "${YELLOW}   Or bypass with: git commit --no-verify${NC}"
            exit 1
        fi
    fi

    # Handle skill version drift (requires manual fix)
    if [ "$HAS_DRIFT" = "yes" ]; then
        echo -e "${RED}❌ Skill version drift detected${NC}"
        python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
for d in data.get('skill_drift', []):
    print(f\"  {d['plugin']}: skill {d['skill_path']} at {d['skill_version']} exceeds plugin.json at {d['plugin_json_version']}\")
    print(f\"  → Bump plugin.json version to >= {d['skill_version']}\")
" <<< "$DETECT_OUTPUT"
        echo -e "${YELLOW}   Fix plugin.json version(s) and re-commit.${NC}"
        echo -e "${YELLOW}   Or bypass with: git commit --no-verify${NC}"
        exit 1
    fi

    # Handle errors (warn only, don't block)
    if [ "$HAS_ERRORS" = "yes" ]; then
        echo -e "${YELLOW}⚠️  Version detection errors (non-blocking):${NC}"
        python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
for e in data.get('errors', []):
    print(f\"  {e['plugin']}: {e['error']}\")
" <<< "$DETECT_OUTPUT"
    fi
else
    echo -e "${GREEN}✅ All marketplace versions up to date${NC}"
fi
```

**Key behaviors:**
- Mismatches only: auto-sync and stage (existing behavior)
- Drift only: warn and block (`exit 1`)
- Both: sync mismatches first, then block on drift
- Errors only: warn, don't block
- Clean: pass through

**Acceptance:**
- [x] Mismatches auto-synced as before
- [x] Drift produces clear error message with fix instructions
- [x] Both drift + mismatches handled: sync first, then block on drift
- [x] Errors produce warnings without blocking
- [x] Hook template version bumped to 5.0.0
- [x] Existing hook users warned about outdated version

---

## Phase 5: Version Bump & Validation

1. Bump `SKILL.md` metadata.version to 2.5.0
2. Bump `plugin.json` version to 2.5.0
3. Run `uv run .../sync_marketplace_versions.py` to sync marketplace.json
4. Run `uv run .../evaluate_skill.py` (skillsmith eval) and record score
5. Update IMPROVEMENT_PLAN.md version history
6. Re-install hook: `bash .../install_hook.sh`
7. Verify: commit something and confirm new hook behavior

**Acceptance:**
- [x] All versions consistent (SKILL.md = plugin.json = marketplace.json = 2.5.0)
- [ ] Hook v5.0.0 installed and working
- [x] Skillsmith eval score recorded (89/100)
- [x] IMPROVEMENT_PLAN.md updated
- [x] All 4 issues closeable

## Implementation Order

```
Phase 1 (#25) ──┐
                 ├──→ Phase 5 (version bump, validation)
Phase 2 (#30) ──┤
                 │
Phase 3 (#75) ──┤
                 │
Phase 4 (#78) ──┘
```

Phases 1-4 are independent and can be implemented in any order, but the recommended sequence is 1 → 2 → 3 → 4 → 5 because:
- Phase 2 fixes `find_repo_root()` which phases 3-4 depend on indirectly
- Phase 3 adds validation that phase 4's hook could optionally invoke
- Phase 5 must be last (version bump after all changes)

## Sources

- Existing plan for #75: `docs/plans/2026-03-02-fix-marketplace-plugin-json-schema-validation-plan.md`
- Lesson: `docs/solutions/logic-errors/multi-skill-plugin-version-sync.md`
- Lesson: `docs/lessons/plugin-integration-and-architecture.md`
- Lesson: `docs/lessons/skill-to-plugin-migration.md`
