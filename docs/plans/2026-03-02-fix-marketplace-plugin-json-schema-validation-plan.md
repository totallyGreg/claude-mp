---
title: "fix: Add plugin.json schema validation to marketplace-manager"
type: fix
status: active
date: 2026-03-02
issue: 75
---

# fix: Add plugin.json schema validation to marketplace-manager

Unknown fields in plugin.json cause **silent installation failure** in Claude Code. The marketplace-manager currently validates marketplace.json thoroughly but never inspects plugin.json files. This fix adds plugin.json schema validation to the existing `validate_marketplace()` flow so unknown fields are caught before they reach users.

## Acceptance Criteria

- [ ] `validate_marketplace()` in `add_to_marketplace.py` loads and validates each plugin's `.claude-plugin/plugin.json` during the per-plugin loop (after line 502)
- [ ] Known fields allowlist: `name`, `version`, `description`, `author`, `license`, `keywords`, `mcpServers`
- [ ] Unknown fields flagged as **errors** (not warnings) with message: `"Unknown field '{field}' in plugin.json — this will cause silent installation failure"`
- [ ] Required plugin.json fields checked: `name`, `version`, `description`
- [ ] `/mp-validate` command documentation updated to list plugin.json validation
- [ ] Existing tests (if any) updated; at minimum, manual validation passes on all 7 current plugins

## Context

**Root cause (issue #75):** The omnifocus-manager plugin.json had a `"components"` field that is not part of the schema. Claude Code's plugin loader silently rejects plugins with unknown fields — no error message, just "Failed: omnifocus-manager". The immediate fix (commit `b926f0b`) removed the field, but no validation prevents this from recurring.

**Where to add validation:** The `validate_marketplace()` function in `add_to_marketplace.py:280` already iterates over all plugins and resolves their source paths. Adding a `validate_plugin_json()` call inside the per-plugin loop (around line 434 where `source_dir` is already computed) is a clean extension.

**Integration point:** The existing pre-commit hook runs `detect_version_changes.py` and `sync_marketplace_versions.py`. The `/mp-validate` command runs `add_to_marketplace.py validate`. Both paths will automatically pick up the new validation since they call `validate_marketplace()`.

## MVP

### add_to_marketplace.py — new helper function

```python
# Known valid fields for .claude-plugin/plugin.json
PLUGIN_JSON_KNOWN_FIELDS = {
    'name', 'version', 'description', 'author',
    'license', 'keywords', 'mcpServers'
}

PLUGIN_JSON_REQUIRED_FIELDS = {'name', 'version', 'description'}


def validate_plugin_json(plugin_json_path, plugin_name):
    """Validate plugin.json against known schema.

    Returns list of issue dicts.
    """
    issues = []
    try:
        with open(plugin_json_path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        issues.append({
            'type': 'error',
            'category': 'plugin_json',
            'field': f'{plugin_name}/plugin.json',
            'message': f"Failed to read plugin.json: {e}"
        })
        return issues

    # Check for unknown fields
    unknown = set(data.keys()) - PLUGIN_JSON_KNOWN_FIELDS
    for field in sorted(unknown):
        issues.append({
            'type': 'error',
            'category': 'plugin_json',
            'field': f'{plugin_name}/plugin.json.{field}',
            'message': (
                f"Unknown field '{field}' in plugin.json "
                f"— this will cause silent installation failure"
            )
        })

    # Check required fields
    for field in PLUGIN_JSON_REQUIRED_FIELDS:
        if field not in data or not data[field]:
            issues.append({
                'type': 'error',
                'category': 'plugin_json',
                'field': f'{plugin_name}/plugin.json.{field}',
                'message': f"Required field '{field}' missing from plugin.json"
            })

    return issues
```

### add_to_marketplace.py — call site in validate_marketplace()

Insert after the author email validation block (~line 502), inside the per-plugin loop:

```python
            # Validate plugin.json schema
            source_path = plugin.get('source', './')
            source_path_clean = source_path.lstrip('./')
            source_dir = repo_root / source_path_clean if source_path_clean else repo_root
            plugin_json_path = source_dir / '.claude-plugin' / 'plugin.json'
            if plugin_json_path.exists():
                issues.extend(validate_plugin_json(
                    plugin_json_path, plugin.get('name', f'plugins[{idx}]')
                ))
            else:
                issues.append({
                    'type': 'warning',
                    'category': 'plugin_json',
                    'field': f'{plugin_prefix}',
                    'message': f"No .claude-plugin/plugin.json found at {source_dir}"
                })
```

Note: `source_dir` is already computed at line 436 — reuse it rather than recomputing.

## Sources

- Issue: #75
- Fix commit: `b926f0b` (removed invalid `"components"` field)
- Validation function: `plugins/marketplace-manager/skills/marketplace-manager/scripts/add_to_marketplace.py:280`
- Lesson: `docs/lessons/plugin-integration-and-architecture.md`
