---
title: "feat: Align marketplace-manager with official Anthropic plugin guidance + consolidate CI scripts"
type: feat
status: completed
date: 2026-03-24
issue: 143
---

# Align marketplace-manager with Official Anthropic Plugin Guidance + Consolidate CI Scripts

## Overview

The marketplace-manager plugin exists to codify Anthropic's official Claude Code plugin guidance into validated, enforceable tooling. Its scripts, hooks, and CI examples are the implementation layer for the schemas defined by Anthropic — both in the `plugin-dev` skills (claude-plugins-official) and on https://code.claude.com. When the official guidance says a field is valid, marketplace-manager must accept it. When it says a field is required, marketplace-manager must enforce it. The plugin is only as useful as its alignment with the upstream spec.

**Standing principle: When in doubt, defer to official Anthropic guidance.** The plugin-dev skills from claude-plugins-official are the primary upstream authority. When guidance isn't covered there, consult the official documentation at https://code.claude.com. When changes in upstream guidance are detected (new fields, changed requirements, deprecated patterns), invoke skillsmith's improvement workflow (`/ss-improve`) on marketplace-manager to incorporate the corrections. This is not a one-time fix — it's the ongoing operating model for keeping marketplace-manager aligned.

This plan addresses two problems: the validation logic has drifted significantly from the official spec, and the CI-facing scripts have accumulated overlap and dead code. The fix is to re-anchor validation to the official schemas, consolidate CI functionality into a single vendorable `marketplace_ci.py`, DRY up shared functions, and clean up dead scripts.

**Scope note:** Issue #143 originally focused on CI script consolidation. The scope expanded because consolidating scripts that enforce the wrong schema just spreads incorrect validation to more places. Schema alignment (Phase 1) must come first — correct the rules, then consolidate the tooling that enforces them.

## Problem Statement

### Schema drift from official guidance

1. **marketplace.json schema is wrong** — The current validation requires `version`, `description`, and `$schema` at root level, but Anthropic's official schema (https://code.claude.com/docs/en/plugin-marketplaces#marketplace-schema) only requires `name`, `owner`, and `plugins`. Optional metadata is nested under `metadata` (`metadata.description`, `metadata.version`, `metadata.pluginRoot`), not at root level.
2. **marketplace.json plugin entries are too strict** — The official schema requires only `name` and `source` per plugin entry. marketplace-manager requires `version`, `description`, and `skills`. The `source` field supports 5 types (relative path string, github object, url object, git-subdir object, npm object) but marketplace-manager only handles relative path strings.
3. **Missing marketplace.json fields** — The official schema defines `tags`, `strict`, `lspServers`, `category` on plugin entries. marketplace-manager doesn't recognize these.
4. **plugin.json validation rejects valid fields** — The `PLUGIN_JSON_KNOWN_FIELDS` allowlist errors on `homepage`, `repository`, and component path overrides (`commands`, `agents`, `hooks`) that plugin-dev's manifest-reference.md documents as valid.
5. **plugin.json validation is stricter than the spec** — `PLUGIN_JSON_REQUIRED_FIELDS` requires `version` and `description`, but plugin-dev's minimal example shows `name` as the only required field.
6. **Missing type flexibility** — `author` and `repository` can be strings or objects per the spec. `hooks` and `mcpServers` can be paths or inline objects. The validator only handles one form.
7. **Missing name format validation** — The spec defines a regex (`/^[a-z][a-z0-9]*(-[a-z0-9]+)*$/`) but marketplace-manager doesn't enforce it.
8. **Pre-release versions rejected** — The spec supports `1.0.0-alpha.1` but the validator uses strict `^\d+\.\d+\.\d+$`.
9. **Unknown field severity wrong** — The plugin-validator agent says "warn but don't fail" for unknown fields. marketplace-manager errors, claiming "silent installation failure."
10. **`skills` field not in official schema** — The current marketplace.json uses a `skills` array in 7 of 10 plugin entries (e.g., `"skills": ["./skills/terminal-emulation"]`). This field does NOT appear in Anthropic's official marketplace.json plugin entry schema. Skills are defined within the plugin directory itself and discovered automatically by Claude Code — they should not be declared in marketplace.json. Remove `skills` from all plugin entries in marketplace.json during Phase 1 migration.

### Script consolidation

11. **CI scripts overlap significantly** — `add_to_marketplace.py validate`, `detect_version_changes.py`, and `sync_marketplace_versions.py` cover overlapping validation concerns. External repos must figure out which to call and in what order.
12. **No MR/PR diff mode** — `detect_version_changes.py --check-staged` only supports `git diff --cached` (pre-commit hook context). CI MR pipelines need `git diff origin/$TARGET...HEAD`.
13. **pyyaml dependency** — `add_to_marketplace.py` requires pyyaml for one function (`extract_skill_version`), but CI images have Python 3.12+ with no `uv`. All other scripts are stdlib-only.
14. **Vendoring friction** — Consuming repos must copy multiple files (`utils.py` + main script). A single-file solution eliminates this.
15. **Dead scripts** — 2 scripts are broken (`package_skill.py`, `generate_utils_template.py`).
16. **Duplicated functions** — `load_marketplace()` is copied 5x, `extract_frontmatter_version()` exists in 2 incompatible versions (different signatures AND return types), `parse_semver()`/`parse_version()` duplicated with divergent failure defaults.

## Proposed Solution

Five phases:

1. **Align all validation with official Anthropic guidance** — Re-derive marketplace.json, plugin.json, and SKILL.md validation from the upstream sources. Fix `add_to_marketplace.py` and all skill scripts first.
2. **Consolidate shared functions into `utils.py`** — DRY up the remaining lifecycle scripts using the corrected validation logic.
3. **Create `marketplace_ci.py`** — Build a single, self-contained, stdlib-only CI script based on the corrected skill scripts logic, designed for minimal environments.
4. **Delete dead scripts** — Remove 2 broken files + orphaned templates directory.
5. **Update documentation, references, SKILL.md, and run skillsmith evaluation** — Update all references to match corrected schemas. Run skillsmith to validate changes and improve on baseline.

## Technical Approach

### Phase 1: Align Validation with Official Anthropic Guidance

All validation must be derived from and stay synchronized with the upstream sources. Skill scripts run via `uv` with PEP 723 headers and should use proper yaml modules (pyyaml via `yaml.safe_load()`) — not regex — for parsing YAML frontmatter.

#### Phase 1a: Resolve structural prerequisites before schema changes

Before correcting schema validation, fix three structural issues that would otherwise complicate Phase 1 and block Phase 2:

1. **Break circular import:** `add_to_marketplace.py` imports `extract_frontmatter_version` from `sync_marketplace_versions.py` (line 589). Move `extract_frontmatter_version` to `utils.py` immediately, before any schema changes. Update imports in both scripts.

2. **Reconcile `extract_frontmatter_version()` signatures:** Two incompatible versions exist:
   - `sync_marketplace_versions.py`: Takes `Path` parameter, returns `(version, is_nonstandard)` tuple
   - `detect_version_changes.py`: Takes `str` content parameter, returns `version` string only

   The canonical version in `utils.py` should take a file `Path`, return `(version, is_nonstandard)` tuple, and use `yaml.safe_load()` for parsing. Update all callers to use the canonical signature.

3. **Add test cases for `parse_semver()` failure default change:** The consolidated `parse_semver()` will use `(0, 0, 0)` as failure default (currently `(1, 0, 0)` in `add_to_marketplace.py`). Before changing, add test cases that document the behavioral impact — verify no existing version comparisons silently change outcome. At minimum, test:
   - Unparseable version strings return `(0, 0, 0)`
   - `1.0.0-alpha.1` parses correctly (base `(1, 0, 0)`)
   - Version comparison ordering: `0.0.0 < 0.1.0 < 1.0.0`

**Upstream schema authorities (in priority order):**
1. **Official Anthropic documentation** — https://code.claude.com/docs/en/plugin-marketplaces#marketplace-schema and https://code.claude.com/docs/en/plugins-reference#plugin-manifest-schema
2. **plugin-dev skills** (claude-plugins-official) — `plugin-dev:plugin-structure` SKILL.md + `references/manifest-reference.md`
3. **plugin-dev:plugin-validator agent** — for validation severity guidance
4. **AgentSkills Specification** (skillsmith references) — for SKILL.md frontmatter schema

#### marketplace.json Schema (per https://code.claude.com/docs/en/plugin-marketplaces#marketplace-schema)

**Root-level required fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Marketplace identifier (kebab-case, no spaces) |
| `owner` | object | `{name (required), email (optional)}` |
| `plugins` | array | List of plugin entries |

**Root-level optional metadata (nested under `metadata`):**

| Field | Type | Description |
|-------|------|-------------|
| `metadata.description` | string | Brief marketplace description |
| `metadata.version` | string | Marketplace version |
| `metadata.pluginRoot` | string | Base directory prepended to relative plugin source paths |

**Migration:** The current marketplace.json has `version`, `description`, and `$schema` at root level. Per the official schema, optional metadata belongs under `metadata`. Migrate the existing file during Phase 1: move `version` → `metadata.version`, `description` → `metadata.description`. The `$schema` field is accepted at root level (common JSON convention) but not required. The validator should reject root-level `version`/`description` as unknown fields (with a helpful message suggesting migration to `metadata`).

#### marketplace.json Plugin Entry Schema (per official docs)

**Required fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Plugin identifier (kebab-case) |
| `source` | string or object | Where to fetch the plugin (see source types below) |

**Optional standard metadata (any plugin.json field is valid here):**

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Brief plugin description |
| `version` | string | Plugin version |
| `author` | object | `{name (required), email (optional)}` |
| `homepage` | string | Plugin documentation URL |
| `repository` | string | Source code repository URL |
| `license` | string | SPDX license identifier |
| `keywords` | array | Tags for discovery |
| `category` | string | Plugin category |
| `tags` | array | Tags for searchability |
| `strict` | boolean | Controls whether plugin.json is authority for components (default: true) |

**Optional component configuration:**

| Field | Type | Description |
|-------|------|-------------|
| `commands` | string or array | Custom paths to command files/directories |
| `agents` | string or array | Custom paths to agent files |
| `hooks` | string or object | Hooks configuration or path to hooks file |
| `mcpServers` | string or object | MCP server configurations or path |
| `lspServers` | string or object | LSP server configurations or path |

**Source types:**

| Source | Type | Required Fields |
|--------|------|-----------------|
| Relative path | string (e.g., `"./my-plugin"`) | Must start with `./` |
| GitHub | object | `source: "github"`, `repo` (required), `ref?`, `sha?` |
| Git URL | object | `source: "url"`, `url` (required), `ref?`, `sha?` |
| Git subdirectory | object | `source: "git-subdir"`, `url`, `path` (required), `ref?`, `sha?` |
| npm | object | `source: "npm"`, `package` (required), `version?`, `registry?` |

#### plugin.json Field Schema (per plugin-dev manifest-reference.md)

| Field | Status | Type | Notes |
|-------|--------|------|-------|
| `name` | **Required** | string | Kebab-case: `/^[a-z][a-z0-9]*(-[a-z0-9]+)*$/`, must start with letter, end with letter/number |
| `version` | Recommended | string | Semver (X.Y.Z), pre-release supported (`1.0.0-alpha.1`). Default `0.1.0` if absent |
| `description` | Recommended | string | 50-200 chars recommended |
| `author` | Optional | string or object | Object: `{name, email?, url?}`. String: `"Name <email> (url)"` |
| `license` | Optional | string | SPDX identifier |
| `keywords` | Optional | array[string] | Tags for discovery |
| `homepage` | Optional | string (URL) | Plugin documentation (not source code) |
| `repository` | Optional | string or object | String: URL. Object: `{type, url, directory?}` |
| `commands` | Optional | string or array[string] | Custom command paths, supplements default `commands/` |
| `agents` | Optional | string or array[string] | Custom agent paths, supplements default `agents/` |
| `hooks` | Optional | string or object | String: path to hooks.json. Object: inline hook config |
| `mcpServers` | Optional | string or object | String: path to `.mcp.json`. Object: inline MCP config |
| `lspServers` | Optional | string or object | LSP server configurations |

**Changes to `add_to_marketplace.py`:**

```python
# BEFORE (too restrictive, drifted from upstream):
PLUGIN_JSON_KNOWN_FIELDS = {
    'name', 'version', 'description', 'author',
    'license', 'keywords', 'mcpServers'
}
PLUGIN_JSON_REQUIRED_FIELDS = {'name', 'version', 'description'}

# AFTER (aligned with plugin-dev manifest-reference.md + official docs):
PLUGIN_JSON_KNOWN_FIELDS = {
    # Required
    'name',
    # Recommended metadata
    'version', 'description', 'author', 'license', 'keywords',
    'homepage', 'repository',
    # Component path overrides (supplement defaults, don't replace)
    'commands', 'agents', 'hooks',
    # Server definitions
    'mcpServers', 'lspServers',
}
PLUGIN_JSON_REQUIRED_FIELDS = {'name'}
```

**Validation behavior changes:**
- `version` and `description` downgraded from error to warning when missing
- Version validation accepts pre-release suffixes — what Anthropic defines as valid is valid
- `name` format validated per manifest-reference.md (research whether string validation or regex is appropriate for this — regex may be acceptable for plugin naming since it's not YAML parsing)
- `author` accepted as string or object, `repository` accepted as string or object
- Component path overrides validated: must start with `./`, no `../`, forward slashes only
- Unknown fields downgraded from error to warning (per plugin-validator agent)
- marketplace.json validation updated to match official schema (required: `name`, `owner`, `plugins` only)
- marketplace.json plugin entries: required `name` and `source` only
- Plugin `source` field: validate relative paths thoroughly (must start with `./`, path exists on disk, no `../`). For object source types (github, url, git-subdir, npm), accept without detailed field validation — this repo only uses relative paths and detailed validation for unused types is YAGNI. Do not reject object sources; just don't validate their internal structure

**Skill scripts use pyyaml for YAML parsing** — all scripts running via `uv` should use `yaml.safe_load()` for frontmatter parsing, not regex. The PEP 723 `# /// script` header declares the pyyaml dependency.

#### SKILL.md Frontmatter Schema (per AgentSkills Specification)

| Field | Status | Notes |
|-------|--------|-------|
| `name` | Required | 1-64 chars, lowercase alphanumeric + hyphens, must match directory name |
| `description` | Required | Max 1024 chars, third-person voice, include trigger phrases |
| `version` | Not in spec | The AgentSkills Specification does not define a root-level `version` field. Some existing skills use it by convention, but `metadata.version` is the only spec-defined location. Warn if found at root level; prefer `metadata.version`. |
| `license` | Optional | Brief license reference |
| `compatibility` | Optional | Max 500 chars, environment requirements |
| `metadata` | Optional | Object with arbitrary key-value pairs |
| `metadata.version` | **Preferred** | Semantic version — preferred over root-level `version` |
| `metadata.author` | Optional | Skill creator name |
| `metadata.tags` | Optional | Categories/keywords |
| `allowed-tools` | Optional | Space-delimited string (experimental) |

### Phase 2: Consolidate Shared Functions into `utils.py`

Move duplicated functions into `utils.py` so the remaining lifecycle scripts (`add_to_marketplace.py`, `sync_marketplace_versions.py`, `sync_readme.py`, `deprecate_skill.py`, `create_plugin.py`) stay DRY. All functions use the corrected validation logic from Phase 1.

**Functions to add to `utils.py`:**

```python
# Already in utils.py:
find_repo_root()
get_repo_root()
print_verbose_info()
validate_repo_structure()

# NEW — consolidate from duplicated copies:
load_marketplace(marketplace_path)       # from 5 scripts
save_marketplace(marketplace_path, data) # from 3 scripts
find_plugin(marketplace_data, name)      # from 2 scripts
extract_frontmatter_version(path)        # file-path version, returns (version, is_nonstandard)
parse_semver(version_str)                # from detect_version_changes.py + add_to_marketplace.py
validate_semantic_version(version_str)   # from add_to_marketplace.py — updated for pre-release

# Schema constants (shared between utils.py and marketplace_ci.py):
PLUGIN_JSON_KNOWN_FIELDS                 # aligned with upstream
PLUGIN_JSON_REQUIRED_FIELDS              # {'name'} only
MARKETPLACE_REQUIRED_FIELDS              # {'name', 'owner', 'plugins'}
PLUGIN_ENTRY_REQUIRED_FIELDS             # {'name', 'source'}
```

**Impact on existing scripts:**

| Script | Change |
|--------|--------|
| `add_to_marketplace.py` | Remove inline duplicated functions and schema constants. Import from `utils`. Keep pyyaml dependency (PEP 723 header). Remove `from sync_marketplace_versions import extract_frontmatter_version` circular import. Update all validation to match Phase 1 corrected schemas. |
| `sync_marketplace_versions.py` | Remove inline `load_marketplace`, `save_marketplace`, `extract_frontmatter_version`. Import from `utils`. |
| `sync_readme.py` | Remove inline `load_marketplace`. Import from `utils`. |
| `deprecate_skill.py` | Remove inline `load_marketplace`, `save_marketplace`, `find_plugin`. Import from `utils`. |
| `create_plugin.py` | No change needed (only imports `find_repo_root`, already in utils). |

### Phase 3: Create `marketplace_ci.py` (New File)

Build the CI script **after** the skill scripts are corrected and consolidated. `marketplace_ci.py` is based on the corrected logic from Phases 1-2 but built for minimal environments (stdlib-only, no uv, no pyyaml).

A single entry point for CI pipelines with these subcommands:

```
marketplace_ci.py validate          # Structural linting (corrected schema from Phase 1)
marketplace_ci.py version-check     # Version mismatch detection
marketplace_ci.py version-check --mr  # MR/PR diff mode (NEW)
marketplace_ci.py structure-check   # Anti-pattern detection
```

**Design constraints:**
- **Zero local imports** — all functions inlined (no `from utils import`)
- **Stdlib-only** — no pyyaml, no third-party packages
- **Single-file vendorable** — copy one file to any repo, run with `python3`
- **CI-native output** — `--format json` on all subcommands, exit 0/1
- **`--ci` flag** — superset of `--format json`: forces JSON output + exit 1 on any issue
- **No regex for YAML frontmatter** — use the split+state machine pattern (see below). Regex may be acceptable for plugin name format validation (research during implementation).

**Key functions to inline:**
- `find_repo_root()` — from `utils.py`
- `load_marketplace()` — from `utils.py`
- `extract_frontmatter_version()` — split+state machine parser, returns `(version, is_nonstandard)` tuple
- `extract_plugin_json_version()` — from `detect_version_changes.py`
- `parse_semver()` — failure default `(0,0,0)` (see "Implementation Notes")
- `validate_marketplace()` — based on corrected Phase 1 logic, stdlib-only reimplementation

**MR diff mode (`--mr`):**

```python
def get_mr_diff_files(repo_root):
    """Get files changed in MR/PR vs target branch.

    Auto-detects target branch from CI environment variables:
    - GitLab: CI_MERGE_REQUEST_TARGET_BRANCH_NAME
    - GitHub: GITHUB_BASE_REF
    - Manual: --target-branch flag

    Exits with error if git diff fails (e.g., target branch not fetched).
    """
    target = (
        os.environ.get('CI_MERGE_REQUEST_TARGET_BRANCH_NAME')
        or os.environ.get('GITHUB_BASE_REF')
        or 'main'
    )
    result = subprocess.run(
        ['git', 'diff', '--name-only', f'origin/{target}...HEAD'],
        cwd=repo_root, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ERROR: git diff against origin/{target} failed.", file=sys.stderr)
        print(f"Ensure target branch is fetched (e.g., fetch-depth: 0 or git fetch origin {target}).", file=sys.stderr)
        sys.exit(1)
    return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
```

**Frontmatter Parsing (stdlib, no regex):**

```python
def extract_frontmatter_version(content):
    """Extract version from SKILL.md frontmatter. Stdlib only, no regex.

    Returns (version, is_nonstandard) tuple:
    - version: the version string (metadata.version preferred)
    - is_nonstandard: True if version came from root-level 'version:' field (not in AgentSkills spec)
    """
    if not content or not content.startswith('---'):
        return (None, False)

    parts = content.split('---', 2)
    if len(parts) < 3:
        return (None, False)

    metadata_version = None
    version = None
    in_metadata = False

    for line in parts[1].strip().splitlines():
        stripped = line.strip()
        indented = line.startswith(' ') or line.startswith('\t')

        if stripped == 'metadata:':
            in_metadata = True
        elif in_metadata and indented and stripped.startswith('version:'):
            metadata_version = stripped.split(':', 1)[1].strip().strip('"').strip("'")
        elif not indented and stripped.startswith('version:'):
            version = stripped.split(':', 1)[1].strip().strip('"').strip("'")
            in_metadata = False
        elif not indented and stripped and ':' in stripped:
            in_metadata = False

    if metadata_version:
        return (metadata_version, False)
    elif version:
        return (version, True)
    return (None, False)
```

**Note:** Skill scripts (`utils.py`, `add_to_marketplace.py`, etc.) should use `yaml.safe_load()` for frontmatter parsing — the stdlib state machine is only for the vendorable CI script.

**A comment block at the top of `marketplace_ci.py`** lists the canonical source for each inlined function so maintainers know to check both when making changes.

**Consistency tests for dual YAML parsers:**

The stdlib state-machine parser in `marketplace_ci.py` and the `yaml.safe_load()` parser in `utils.py` must produce identical results for `extract_frontmatter_version()`. Add test cases that run both implementations on identical inputs and assert identical `(version, is_nonstandard)` output. Test cases must cover:
- Standard frontmatter: `metadata:\n  version: 1.0.0`
- Root-level version (not in spec): `version: 2.0.0`
- Quoted values: `version: "1.0.0"`
- Inline comments: `version: 1.0.0 # current`
- No frontmatter / empty content
- Both `metadata.version` and root-level `version` present (metadata wins)

Document any edge cases where the stdlib parser intentionally diverges from `yaml.safe_load()` (e.g., multi-line scalars, folded blocks). These are known limitations of the vendorable CI script.

### Phase 4: Delete Dead Scripts

| Script | Reason for Removal |
|--------|-------------------|
| `package_skill.py` | **Broken** — imports `from quick_validate import validate_skill` but `quick_validate.py` doesn't exist. Skill packaging owned by skillsmith. |
| `generate_utils_template.py` | **Broken** — hardcodes pre-migration path `repo_root / 'skills' / 'marketplace-manager' / 'scripts' / 'templates' / 'utils.py.template'` (line 140). Template exists at post-migration path but script's reference is broken. |
**Also delete:** `templates/` directory and `utils.py.template` — orphaned after `generate_utils_template.py` removal, no remaining consumers.

**Retained:** `analyze_bundling.py` — provides useful guidance when asked about bundling analysis.

**Retained:** `migrate_to_plugin.py` stays — repos commonly start as flat skill layouts and need to convert to plugin structure as they mature.

### Phase 5: Update Documentation, References, SKILL.md, and Run Skillsmith

This phase happens after all script fixes and consolidations are complete.

1. **Update `references/plugin_marketplace_guide.md`** — Update the plugin.json field reference and marketplace.json schema to match the corrected official schemas from Phase 1.

2. **Update `references/marketplace_distribution_guide.md`** — Correct the marketplace.json schema documentation to match the official Anthropic schema. Update plugin entry required/optional fields.

3. **Update `references/troubleshooting.md`** — Replace references to running `detect_version_changes.py --check-structure` diagnostically with `marketplace_ci.py structure-check`.

4. **Add deprecation notice to `detect_version_changes.py`** — Comment header noting `marketplace_ci.py` is canonical for CI. Pre-commit hooks continue using this script. Future hook template version (v6.0.0) should migrate callers.

5. **Add CI example snippets to `references/`** — Two new files:

#### `references/ci-example-github-actions.yml`

```yaml
# .github/workflows/plugin-validation.yml
# Validates Claude Code plugin structure and version enforcement on PRs.
# Requires: marketplace_ci.py vendored at scripts/marketplace_ci.py

name: Plugin Validation

on:
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Validate plugin structure
        run: python3 scripts/marketplace_ci.py validate --ci

      - name: Check version bumps
        run: python3 scripts/marketplace_ci.py version-check --mr --ci

      - name: Check structure (advisory)
        run: python3 scripts/marketplace_ci.py structure-check --ci || true
```

#### `references/ci-example-gitlab-ci.yml`

```yaml
# Validates Claude Code plugin structure and version enforcement on MRs.
# Requires: marketplace_ci.py vendored at scripts/marketplace_ci.py

stages:
  - validate

validate:plugin:
  stage: validate
  image: python:3.12-slim
  script:
    - python3 scripts/marketplace_ci.py validate --ci
  rules:
    - if: $CI_MERGE_REQUEST_IID

version:check:
  stage: validate
  image: python:3.12-slim
  before_script:
    - git fetch origin $CI_MERGE_REQUEST_TARGET_BRANCH_NAME --depth=1
  script:
    - python3 scripts/marketplace_ci.py version-check --mr --ci
  rules:
    - if: $CI_MERGE_REQUEST_IID

structure:check:
  stage: validate
  image: python:3.12-slim
  script:
    - python3 scripts/marketplace_ci.py structure-check --ci
  allow_failure: true
  rules:
    - if: $CI_MERGE_REQUEST_IID
```

6. **Update SKILL.md** — Add `marketplace_ci.py` to documented capabilities. Remove references to deleted scripts. Reference the corrected schemas and CI examples.

7. **Run skillsmith evaluation** — After all changes are complete:
   ```bash
   uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py plugins/marketplace-manager/skills/marketplace-manager
   ```
   Record eval score in README.md. The evaluation validates that SKILL.md accurately reflects the script inventory, removed scripts are no longer referenced, and new references are properly linked. If the eval score doesn't improve on baseline, use `/ss-improve` to iterate until it does. This improvement loop should become part of marketplace-manager's operating model for future changes.


## Acceptance Criteria

### Structural Prerequisites (Phase 1a)
- [ ] Circular import broken: `extract_frontmatter_version` moved from `sync_marketplace_versions.py` to `utils.py`
- [ ] `extract_frontmatter_version()` has canonical signature: takes `Path`, returns `(version, is_nonstandard)`, uses `yaml.safe_load()`
- [ ] All callers updated to use canonical signature
- [ ] Test cases added for `parse_semver()` failure default change (`(1, 0, 0)` → `(0, 0, 0)`) — no silent behavioral regressions

### Schema Alignment (Phase 1)
- [ ] marketplace.json root validation: only `name`, `owner`, `plugins` required
- [ ] marketplace.json optional metadata nested under `metadata` (not root level)
- [ ] marketplace.json plugin entries: only `name` and `source` required
- [ ] Plugin `source` field: relative paths validated thoroughly (starts with `./`, exists on disk, no `../`). Object source types (github, url, git-subdir, npm) accepted without rejection but no detailed field validation (YAGNI — only relative paths are used)
- [ ] Plugin entries accept all optional fields: `description`, `version`, `author`, `homepage`, `repository`, `license`, `keywords`, `category`, `tags`, `strict`, `commands`, `agents`, `hooks`, `mcpServers`, `lspServers`
- [ ] `PLUGIN_JSON_KNOWN_FIELDS` updated to include: `homepage`, `repository`, `commands`, `agents`, `hooks`, `lspServers`
- [ ] `PLUGIN_JSON_REQUIRED_FIELDS` reduced to `{'name'}` only
- [ ] `name` format validated per manifest-reference.md
- [ ] Missing `version` or `description` in plugin.json emits warning, not error
- [ ] Version validation accepts pre-release suffixes
- [ ] `author` accepted as string or object
- [ ] `repository` accepted as string or object
- [ ] Component path overrides validated: must start with `./`, no `../`
- [ ] Unknown fields downgraded from error to warning
- [ ] SKILL.md `name` validated: 1-64 chars, lowercase alphanumeric + hyphens, matches directory
- [ ] Skill scripts use `yaml.safe_load()` for frontmatter parsing (not regex)
- [ ] Existing `marketplace.json` migrated to official schema structure (`version`/`description` moved under `metadata`)
- [ ] `skills` field removed from all plugin entries in marketplace.json (skills are defined in the plugin, not marketplace.json)
- [ ] Validator rejects `skills` as an unknown field with helpful message explaining skills are discovered from the plugin directory

### Utils Consolidation (Phase 2)
- [ ] `utils.py` contains consolidated `load_marketplace`, `save_marketplace`, `find_plugin`, `extract_frontmatter_version`, `parse_semver`, `validate_semantic_version`
- [ ] `utils.py` exports schema constants aligned with official guidance
- [ ] `parse_semver()` uses `(0, 0, 0)` as failure default

### CI Script (Phase 3)
- [ ] `marketplace_ci.py validate` performs all checks using corrected schema
- [ ] `marketplace_ci.py validate` detects non-standard root-level `version:` in SKILL.md (not in AgentSkills spec)
- [ ] `marketplace_ci.py validate` detects undeclared skills
- [ ] `marketplace_ci.py version-check` detects version mismatches
- [ ] `marketplace_ci.py version-check --mr` supports MR/PR diff mode
- [ ] `marketplace_ci.py version-check --mr` exits 1 with descriptive error on git failure
- [ ] `marketplace_ci.py version-check --mr --target-branch <branch>` supports explicit target
- [ ] `marketplace_ci.py version-check --staged` replaces `detect_version_changes.py --check-staged`
- [ ] `marketplace_ci.py structure-check` detects structural anti-patterns
- [ ] All subcommands support `--format json` and `--ci` flags
- [ ] Zero local imports, stdlib-only, vendorable
- [ ] No regex for YAML frontmatter parsing
- [ ] `extract_frontmatter_version()` returns `(version, is_nonstandard)` tuple
- [ ] Comment block lists canonical sources for all inlined functions
- [ ] Consistency tests verify stdlib parser and `yaml.safe_load()` parser produce identical `(version, is_nonstandard)` output for canonical SKILL.md frontmatter patterns
- [ ] Known limitations of stdlib parser documented (multi-line scalars, folded blocks)

### Cleanup (Phase 4)
- [ ] `package_skill.py` deleted
- [ ] `generate_utils_template.py` deleted
- [ ] `analyze_bundling.py` retained (provides bundling analysis guidance)
- [ ] `templates/` directory and `utils.py.template` deleted
- [ ] `migrate_to_plugin.py` retained

### Documentation & Skillsmith (Phase 5)
- [ ] Reference docs updated with corrected schemas from official Anthropic sources
- [ ] CI example files added for GitHub Actions and GitLab CI
- [ ] `detect_version_changes.py` has deprecation notice header
- [ ] Pre-commit hook continues to work unchanged
- [ ] SKILL.md updated to reflect new capabilities and removed scripts
- [ ] Skillsmith evaluation run — score improves on baseline
- [ ] No stale file references in SKILL.md or references/ docs

## File Inventory: Before and After

### Before (13 files + template + templates/)

```
scripts/
  utils.py                      # shared utilities
  detect_version_changes.py     # version detection (3 modes)
  add_to_marketplace.py         # marketplace CRUD + validation
  sync_marketplace_versions.py  # version sync engine
  sync_readme.py                # README table sync
  validate_hook.py              # hook health check
  install_hook.sh               # hook installer
  pre-commit.template           # hook template
  create_plugin.py              # plugin scaffolding
  migrate_to_plugin.py          # skill-to-plugin migration
  deprecate_skill.py            # skill deprecation
  package_skill.py              # BROKEN (quick_validate missing)
  generate_utils_template.py    # BROKEN (hardcoded pre-migration path)
  analyze_bundling.py           # bundling analysis guidance
  templates/
    utils.py.template           # ORPHANED
```

### After (12 files + template)

```
scripts/
  marketplace_ci.py             # NEW — single CI entry point (self-contained, corrected schema)
  utils.py                      # EXPANDED — consolidated shared functions + schema constants
  detect_version_changes.py     # RETAINED — pre-commit hook backward compat (deprecation notice)
  add_to_marketplace.py         # SIMPLIFIED — imports from utils, corrected validation
  sync_marketplace_versions.py  # SIMPLIFIED — imports from utils
  sync_readme.py                # SIMPLIFIED — imports from utils
  deprecate_skill.py            # SIMPLIFIED — imports from utils
  create_plugin.py              # UNCHANGED
  migrate_to_plugin.py          # RETAINED — recurring workflow
  analyze_bundling.py           # RETAINED — bundling analysis guidance
  validate_hook.py              # UNCHANGED
  install_hook.sh               # UNCHANGED
  pre-commit.template           # UNCHANGED
```

Net: -2 deleted, -1 directory, +1 created = **-2 files/dirs**.

## Implementation Notes

### On `detect_version_changes.py` retention

The pre-commit hook (`pre-commit.template` v5.2.0) calls `detect_version_changes.py` by name in 6+ places. Removing it would break installed hooks. It stays with a deprecation notice. Future hook template v6.0.0 should migrate callers to `marketplace_ci.py`.

### On `parse_semver` failure default

`detect_version_changes.py` uses `(0, 0, 0)`, `add_to_marketplace.py` uses `(1, 0, 0)`. The consolidated version uses `(0, 0, 0)` — more conservative, makes parse failures visible, avoids false "already at 1.0.0" signals.

### On YAML parsing: skill scripts vs CI script

Skill scripts run via `uv` with PEP 723 headers declaring pyyaml. They should use `yaml.safe_load()` — the right tool for YAML. Only `marketplace_ci.py` uses the stdlib split+state machine because it must run in minimal CI environments with just `python3`.

### On function duplication between `marketplace_ci.py` and `utils.py`

Intentional duplication for vendorability. Both must be updated when fixing bugs. A comment block at the top of `marketplace_ci.py` lists canonical sources.

### On `validate_hook.py` exclusion

Checks hook health (installation, permissions, template version). Orthogonal to CI validation and schema — different lifecycle concern. Correctly left unchanged.

### On marketplace.json migration

The existing `marketplace.json` in this repo has several fields that don't match the official Anthropic schema:
- `version` and `description` at root level → official schema nests these under `metadata`
- `$schema` at root level → not mentioned in official schema (keep as optional, don't require)
- `skills` arrays in plugin entries → not in official schema (skills are discovered from the plugin directory)

Migration happens during Phase 1:
1. Move `version` → `metadata.version`, `description` → `metadata.description`
2. Remove `skills` from all 10 plugin entries
3. Keep `$schema` at root level (accepted but not required)
4. Validator rejects root-level `version`/`description` with migration guidance
5. Validator rejects `skills` with explanation that skills are defined in the plugin

## Scope Boundaries

- **In scope:** Schema correction, script consolidation, dead code cleanup, CI examples, skillsmith evaluation
- **Out of scope:** Auto-fetching the official schema URL at validation time
- **Out of scope:** Detailed field validation for object source types (github, npm, git-subdir, url) — accept without rejection but only validate relative path sources thoroughly (this repo only uses relative paths)
- **Research during implementation:** Whether regex is appropriate for plugin name format validation vs string operations

## Sources

### Upstream Schema Authorities (marketplace-manager derives from these)

- **Official Anthropic documentation** — https://code.claude.com/docs/en/plugin-marketplaces#marketplace-schema — **canonical marketplace.json schema**
- **Official Anthropic documentation** — https://code.claude.com/docs/en/plugins-reference#plugin-manifest-schema — **canonical plugin.json schema**
- **`plugin-dev:plugin-structure` SKILL.md** (claude-plugins-official) — plugin.json field definitions, directory structure, auto-discovery rules
- **`plugin-dev:plugin-structure` `references/manifest-reference.md`** (claude-plugins-official) — complete plugin.json field reference with types, formats, validation rules
- **`plugin-dev:plugin-validator` agent** (claude-plugins-official) — validation severity (unknown fields warn, don't fail)
- **`plugin-dev:skill-development` SKILL.md** (claude-plugins-official) — SKILL.md structure and frontmatter requirements
- **AgentSkills Specification** (`skillsmith/references/agentskills_specification.md`) — SKILL.md frontmatter schema

### Project References

- GitHub Issue: #143
- Institutional learning: `docs/solutions/logic-errors/multi-skill-plugin-version-sync.md` — version comparison must use `max()` with `parse_semver` for multi-skill plugins
- Institutional learning: `docs/lessons/plugin-integration-and-architecture.md` — plugin self-containment is intentional; code duplication accepted for marketplace distribution
- Institutional learning: `docs/plans/2026-03-03-fix-marketplace-manager-all-open-issues-plan.md` — plugin.json validation uses conservative allowlist, skill drift should block commits
- Related plan: `docs/plans/2026-01-18-extension-evolution.md` — previously proposed shared utility extraction
