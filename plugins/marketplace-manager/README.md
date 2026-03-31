# marketplace-manager

Plugin marketplace operations: version syncing, skill publishing, and marketplace.json maintenance.

## Components

### Skill: marketplace-manager
Self-sufficient marketplace repo model with two-tier script architecture:
- Repo-level scripts (validate.py, sync.py) installed into marketplace repos for standalone operation
- Skill-level scripts (setup.py, scaffold.py) for repo initialization and plugin scaffolding
- Official Anthropic schema validation with reverse scan and auto-fix
- Pre-commit hook using repo-local scripts

### Commands (5)

| Command | Purpose |
|---------|---------|
| `/mp-sync` | Sync plugin versions to marketplace.json |
| `/mp-validate` | Validate marketplace.json against official schema |
| `/mp-add` | Scaffold a new plugin or migrate a legacy skill |
| `/mp-list` | List all marketplace plugins |
| `/mp-status` | Show version mismatches and validation summary |

### Scripts

| Script | Tier | Purpose |
|--------|------|---------|
| `scripts/setup.py` | Skill | Initialize marketplace repo, copy scripts, install hook |
| `scripts/scaffold.py` | Skill | Scaffold new plugin or migrate legacy skill |
| `scripts/repo/validate.py` | Repo | Schema validation, forward/reverse scan, auto-fix, CI output |
| `scripts/repo/sync.py` | Repo | Sync versions from plugin.json/SKILL.md to marketplace.json |

### References

| Reference | Content |
|-----------|---------|
| `references/official_docs_index.md` | Official Anthropic documentation links |
| `references/plugin_marketplace_guide.md` | Plugin structure and marketplace schema |
| `references/marketplace_distribution_guide.md` | Distribution workflow and best practices |
| `references/troubleshooting.md` | Common issues and solutions |
| `references/ci-example-github-actions.yml` | GitHub Actions CI example |
| `references/ci-example-gitlab-ci.yml` | GitLab CI example |

### Key Concepts

- **Two-tier model**: After `setup.py all`, repos own their own validation and sync with no runtime dependency on marketplace-manager
- **Version source priority**: plugin.json > SKILL.md metadata.version > SKILL.md root version (non-standard)
- **Pre-commit hook**: runs `validate.py --staged` then `sync.py` -- blocks on version issues, auto-syncs otherwise
- **Repo-level scripts are stdlib-only** -- no external dependencies, vendorable into any repo
- **Workflow**: `plugin-dev` (build) > `skillsmith` (improve) > `marketplace-manager` (publish)

## Two-Tier Architecture

```mermaid
flowchart TD
    subgraph skill["Skill-Level Scripts (marketplace-manager)"]
        direction TB
        S1["setup.py"] --> S1a["init -- create marketplace.json"]
        S1 --> S1b["install-scripts -- copy validate.py + sync.py into repo"]
        S1 --> S1c["install-hook -- install pre-commit hook"]
        S1 --> S1d["all -- init + install-scripts + install-hook"]
        S2["scaffold.py"] --> S2a["create -- scaffold new plugin directory"]
        S2 --> S2b["migrate -- convert legacy skill to plugin structure"]
    end

    subgraph repo["Repo-Level Scripts (installed into marketplace repo)"]
        direction TB
        R1["scripts/validate.py"] --> R1a["Schema validation"]
        R1 --> R1b["Forward validation -- source paths exist"]
        R1 --> R1c["Reverse scan -- unregistered plugins on disk"]
        R1 --> R1d["--fix -- auto-add missing plugins"]
        R1 --> R1e["--staged -- pre-commit version check"]
        R1 --> R1f["--check-structure -- anti-pattern detection"]
        R1 --> R1g["--format json -- CI/CD output"]
        R2["scripts/sync.py"] --> R2a["Sync versions to marketplace.json"]
        R2 --> R2b["--dry-run -- preview changes"]
    end

    S1b -->|copies| R1
    S1b -->|copies| R2

    style skill fill:#e8f5e9,stroke:#4caf50
    style repo fill:#e3f2fd,stroke:#2196f3
```

## Component Lifecycle Flow

```mermaid
flowchart TD
    subgraph dev["Developer Actions"]
        A["Edit skill
(SKILL.md, scripts, references)"] --> B{"Component type?"}
        B -->|Skill| C["Bump metadata.version
in SKILL.md"]
        B -->|Plugin manifest| D["Bump version
in plugin.json"]
        B -->|Command| E["Edit command .md
in commands/"]
        B -->|Hook| F["Edit hook config
in hooks/"]
        B -->|Agent| G["Edit agent .md
in agents/"]
    end

    subgraph version["Version Sources"]
        C --> H["SKILL.md
metadata.version: X.Y.Z"]
        D --> I["plugin.json
version: X.Y.Z"]
        E --> J["No version
(commands are unversioned)"]
        F --> K["No version
(hooks are unversioned)"]
        G --> L["No version
(agents are unversioned)"]
    end

    subgraph discovery["Plugin Structure & Discovery"]
        direction TB
        M["Plugin directory"] --> N{"Has
plugin.json?"}
        N -->|Yes| O["Version from plugin.json
(single source of truth)"]
        N -->|No| P{"Has
SKILL.md at root?"}
        P -->|Yes| Q["Single-skill plugin
Version from SKILL.md"]
        P -->|No| R["Scan skills/ subdirs
auto-discover SKILL.md files"]
        R --> S["Multi-skill plugin
Max version from skills"]
    end

    subgraph precommit["Pre-commit Hook (installed by setup.py)"]
        direction TB
        T["git commit"] --> U["validate.py --staged"]
        U --> V{"Version
mismatches?"}
        V -->|Yes| W["Block commit"]
        V -->|No| X["sync.py"]
        X --> Y["Sync marketplace.json
if needed"]
        Y --> Z["Commit proceeds"]
    end

    subgraph marketplace["marketplace.json (Official Anthropic Schema)"]
        direction TB
        AF["Root fields:
name, owner, plugins
metadata: version, description"]
        AG["Plugin entry:
name (kebab-case, required)
source (required)
version, description, author
category, keywords, etc."]
        AF --> AG
    end

    subgraph validation["Validation (validate.py)"]
        direction TB
        AH["Schema check -- required fields,
known fields, naming"] --> AI["Forward validation --
source paths exist on disk"]
        AI --> AJ["Reverse scan --
plugins on disk not in manifest"]
        AJ --> AK["Auto-discover skills
from plugin directories"]
        AK --> AL["SKILL.md frontmatter check
(metadata.version preferred)"]
        AL --> AM["Name format: kebab-case regex"]
        AM --> AN["Unknown fields -- warning
(not error)"]
    end

    subgraph sync["Version Sync Flow (sync.py)"]
        direction TB
        AS["For each plugin in marketplace.json"] --> AT{"plugin.json
exists?"}
        AT -->|Yes| AU["Read version from plugin.json"]
        AT -->|No| AV{"Single skill
(skills/*/SKILL.md)?"}
        AV -->|Yes| AW["Read version from SKILL.md
frontmatter"]
        AV -->|No| AX["Skip (no version source)"]
        AU --> AY{"Version !=
marketplace?"}
        AW --> AY
        AY -->|Yes| AZ["Update marketplace.json
plugin version"]
        AY -->|No| BA["Already in sync"]
    end

    subgraph ci["CI Pipeline (uses repo-level scripts)"]
        direction TB
        AP["validate.py
Schema + structure"] --> AQ["validate.py --format json
Machine-readable output"]
        AQ --> AR["validate.py --check-structure
Anti-pattern detection"]
    end

    H --> O
    I --> O
    O --> AS
    Q --> AS
    S --> AS
    T --> U
    AF --> AH
    AF --> AP

    style dev fill:#e8f5e9,stroke:#4caf50
    style version fill:#fff3e0,stroke:#ff9800
    style discovery fill:#e3f2fd,stroke:#2196f3
    style precommit fill:#fce4ec,stroke:#e91e63
    style marketplace fill:#f3e5f5,stroke:#9c27b0
    style validation fill:#e0f7fa,stroke:#00bcd4
    style ci fill:#fff9c4,stroke:#ffc107
    style sync fill:#e8eaf6,stroke:#3f51b5
```

## Changelog

| Version | Changes |
|---------|---------|
| 4.0.0 | Official Anthropic schema alignment, self-sufficient repo model, 12 scripts replaced by 4, reverse scan + auto-fix |
| 2.9.0 | Multi-plugin structure detection (`--check-structure`), CI mode (`--ci`), advisory hook warning, docs |
| 2.8.0 | Undeclared skill detection in validate; uv guard; license frontmatter fix |
| 2.7.0 | Add trigger phrases to description |
| 2.5.0 | plugin-dev docs, two-pass find_repo_root(), plugin.json schema validation, pre-commit hook v5.0.0 |
| 2.0.0 | Migrated to plugin structure |

## Skill: marketplace-manager

### Current Metrics

**Score: 100/100** (Excellent) — 2026-03-26

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 100 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 4.0.0 | 2026-03-26 | [#145](https://github.com/totallyGreg/claude-mp/issues/145) | Official schema alignment, self-sufficient repo model, 12 scripts replaced by 4, reverse scan + auto-fix | 100 | 100 | 100 | 100 | 100 | 100 |
| 3.1.0 | 2026-03-25 | - | Fix validator schema guidance: remove metadata from known fields, correct version/description migration advice, merge SKILL.md sections (10→4 H2s), add negative trigger clause | 100 | 100 | 100 | 100 | 100 | 100 |
| 2.9.0 | 2026-03-23 | [#139](https://github.com/totallyGreg/claude-mp/issues/139) | Multi-plugin structure detection (`--check-structure`), CI mode (`--ci`), advisory hook warning, docs | 100 | 87 | 100 | 100 | 100 | 97 |
| 2.8.0 | 2026-03-21 | - | Undeclared skill detection in validate; uv guard on add_to_marketplace.py; license field fix | 100 | 90 | 100 | 100 | 100 | 98 |
| 2.5.1 | 2026-03-03 | - | Add trigger phrases to description | 100 | 83 | 90 | 100 | - | 93 |
| 2.5.0 | 2026-03-03 | [#25](https://github.com/totallyGreg/claude-mp/issues/25), [#30](https://github.com/totallyGreg/claude-mp/issues/30), [#75](https://github.com/totallyGreg/claude-mp/issues/75), [#78](https://github.com/totallyGreg/claude-mp/issues/78) | plugin-dev docs, two-pass find_repo_root(), plugin.json schema validation, pre-commit hook v5.0.0 with drift/mismatch separation | 100 | 83 | 90 | 100 | - | 89 |
| 2.4.0 | 2026-03-03 | [#78](https://github.com/totallyGreg/claude-mp/issues/78) | Detect skill version drift from plugin.json in multi-skill plugins | - | - | - | - | - | - |
| 2.3.0 | 2026-02-16 | - | Plugin versioning strategy: plugin.json as version source, detect refactor, hook stages README.md | 100 | 83 | 90 | 100 | - | 89 |
| 2.0.0 | 2026-02-03 | - | Standalone plugin migration: Moved to plugins/, added commands, improved SKILL.md conciseness | - | - | - | - | - | - |
| 1.5.0 | 2026-01-23 | - | Deprecate skill-planner skill: Removed from marketplace, updated workflow documentation | - | - | - | - | - | - |
| 1.4.0 | 2026-01-22 | [#4](https://github.com/totallyGreg/claude-mp/issues/4), [#5](https://github.com/totallyGreg/claude-mp/issues/5) | Core marketplace operations automation: source path fixes, deprecation, bundling, templates | - | - | - | - | - | 75 |
| 1.3.0 | 2026-01-07 | - | Critical bug fixes: utils.py dependency, schema compliance, metadata.version parsing | - | - | - | - | - | - |
| 1.1.0 | 2025-12-22 | - | Added plugin versioning strategies, validation command, pre-commit hook | - | - | - | - | - | - |
| 1.0.0 | 2025-12-21 | - | Initial release | - | - | - | - | - | - |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

