---
title: Migrate obsidian-pkm-manager to pkm-plugin with Agent
type: feat
date: 2026-02-10
status: planning
---

# Migrate obsidian-pkm-manager to pkm-plugin with Agent

## Overview

Transform the standalone `obsidian-pkm-manager` skill into a full-featured `pkm-plugin` following the Stage 3 evolution pattern (plugin with skills + commands + agents). The agent will orchestrate multi-step workflows for vault analysis, template creation, and PKM system optimization.

This is a two-phase approach:
- **Phase 1** (this plan): Migrate to plugin structure with agent and commands
- **Phase 2** (future): Split into organizational principles vs technical Obsidian interaction skills

## Enhancement Summary

**Deepened on:** 2026-02-10
**Research Agents Used:** 10 parallel agents (architecture, simplicity, patterns, Python, security, agent-native, best practices, Obsidian docs, plugin validation)

### Key Improvements Identified

1. **Python Dependency Management** - Add PEP 723 headers to all scripts for uv execution
2. **Security Hardening** - Implement path validation to prevent directory traversal
3. **Context Injection** - Add vault path configuration for agent awareness
4. **Simplification Opportunities** - Reduce plan complexity by 48% (focus on minimal v1.0.0)
5. **Pattern Alignment** - Fix command namespace and reference architecture discrepancies

### Critical Fixes Required Before Implementation

| Priority | Issue | Impact | Solution |
|----------|-------|--------|----------|
| **P0** | Python dependencies undefined | Scripts fail without PyYAML | Add PEP 723 headers + pyproject.toml |
| **P0** | Path traversal vulnerability | Security risk in vault analysis | Add path validation function |
| **P0** | Context starvation | Agent blind to user's vault | Add .local.md vault path config |
| **P1** | Over-engineering (3 commands) | Unnecessary complexity | Start with 1 command or agent-only |
| **P1** | Missing type hints | Maintenance burden | Add types to all Python functions |

### New Research Insights

**Agent Orchestration (2026 Best Practices):**
- Bounded autonomy pattern: Pause and confirm before destructive operations
- Plan-and-execute can reduce costs by 90% with model tiering
- Progressive skill loading: Metadata → SKILL.md → References

**Python Script Integration:**
- PEP 723 inline metadata standardized in 2024 for standalone scripts
- uv adoption eliminates need for requirements.txt
- Portable paths via `${CLAUDE_PLUGIN_ROOT}` essential

**Security Findings:**
- Path validation critical for user-provided vault paths
- YAML size limits prevent bomb attacks
- Agent tool access needs documented permission model

**Obsidian PKM Patterns:**
- Bases query performance: 50,000+ notes with instant rendering
- Templater best practices: Focus editor, validate input, move files last
- PKM frameworks: Zettelkasten, PARA, LYT (skill already follows best practices)

---

## Problem Statement / Motivation

**Current State:**
- `obsidian-pkm-manager` is a standalone skill (Stage 1)
- Contains comprehensive PKM methodology (~481 lines)
- Has Python scripts in `scripts/` directory
- Lacks user-discoverable commands
- No orchestration for complex multi-step workflows

**Desired State:**
- Full plugin with discoverable slash commands
- Agent for orchestrating complex vault improvements
- Maintainable structure following repository patterns
- Foundation for future skill decomposition

**Why This Matters:**
1. **Discoverability**: Users can invoke `/pkm:analyze-vault` instead of asking "analyze my vault"
2. **Autonomy**: Agent can orchestrate vault analysis → recommendations → implementation
3. **Maintainability**: Follows established plugin architecture patterns
4. **Extensibility**: Clean foundation for splitting organizational vs technical skills later

## Proposed Solution

### High-Level Approach

Follow the **terminal-guru** plugin pattern as the reference architecture:

```
pkm-plugin/
├── .claude-plugin/
│   └── plugin.json                    # Plugin manifest
├── README.md                           # Plugin documentation
├── agents/
│   └── pkm-manager.md                 # Orchestration agent
├── commands/
│   ├── pkm-analyze-vault.md           # /pkm:analyze-vault
│   ├── pkm-validate-templates.md      # /pkm:validate-templates
│   └── pkm-create-template.md         # /pkm:create-template
└── skills/
    └── obsidian-pkm-manager/          # Migrated skill (unchanged)
        ├── SKILL.md
        ├── IMPROVEMENT_PLAN.md
        ├── references/
        ├── scripts/
        └── assets/
```

### Agent Responsibilities

The `pkm-manager` agent will orchestrate multi-step workflows:

1. **Vault Analysis Workflow**
   - Run analysis scripts
   - Interpret results
   - Generate recommendations
   - Present prioritized action plan

2. **Template Creation Workflow**
   - Understand user requirements
   - Design frontmatter schema
   - Write Templater logic
   - Create/update Bases queries
   - Test template functionality

3. **System Optimization Workflow**
   - Analyze current structure
   - Identify pain points
   - Propose improvements
   - Implement changes incrementally
   - Validate results

The agent **references** the obsidian-pkm-manager skill for domain knowledge but **orchestrates** the application of that knowledge.

## Technical Approach

### Phase 1: Directory Structure Setup

**Tasks:**
- Create `plugins/pkm-plugin/` directory structure
- Initialize `.claude-plugin/plugin.json` manifest
- Create `agents/`, `commands/`, `skills/` subdirectories
- Move `skills/obsidian-pkm-manager/` into `plugins/pkm-plugin/skills/`
- Preserve all existing content (SKILL.md, references/, scripts/, assets/)

**Key Files to Create:**

#### `plugins/pkm-plugin/.claude-plugin/plugin.json`
```json
{
  "name": "pkm-plugin",
  "version": "1.0.0",
  "description": "Personal Knowledge Management expert for Obsidian vaults with autonomous orchestration",
  "author": {
    "name": "J. Greg Williams",
    "email": "283704+totallyGreg@users.noreply.github.com"
  },
  "license": "MIT",
  "keywords": ["obsidian", "pkm", "knowledge-management", "templater", "bases", "vault"]
}
```

**Validation:**
- Use `plugin-dev:plugin-validator` to check structure
- Ensure directory follows conventions from `docs/lessons/skill-to-plugin-migration.md`

---

### Phase 2: Agent Development

**Tasks:**
- Create `plugins/pkm-plugin/agents/pkm-manager.md`
- Write agent frontmatter (YAML)
- Design system prompt for workflow orchestration
- Define agent tool access
- Add usage examples with `<example>` tags

**Agent Specification:**

#### `plugins/pkm-plugin/agents/pkm-manager.md` (Frontmatter)
```yaml
---
name: pkm-manager
description: |
  Use this agent when orchestrating multi-step Personal Knowledge Management workflows
  in Obsidian vaults, including vault analysis, template creation, and system optimization.

  <example>
  Context: User wants to improve their vault organization
  user: "Analyze my vault and help me improve organization"
  assistant: "I'll use the pkm-manager agent to analyze your vault and orchestrate improvements."
  <commentary>
  Multi-step workflow: run analysis scripts → interpret results → generate recommendations
  → prioritize actions → guide implementation. Agent orchestrates the full process.
  </commentary>
  </example>

  <example>
  Context: User needs a new Templater template
  user: "Create a customer meeting note template"
  assistant: "I'll use the pkm-manager agent to design and implement the template."
  <commentary>
  Template creation workflow: understand requirements → design frontmatter → write Templater
  logic → create Bases queries → test functionality. Agent coordinates all steps.
  </commentary>
  </example>

model: inherit
color: purple
tools: ["Read", "Bash", "Grep", "Glob", "Edit", "Write"]
---
```

#### Agent System Prompt (Markdown content)

The agent should:

1. **Load Domain Knowledge**
   - Reference `${CLAUDE_PLUGIN_ROOT}/skills/obsidian-pkm-manager/SKILL.md`
   - Load relevant references from `references/` as needed
   - Follow PKM principles from skill documentation

2. **Workflow Orchestration Patterns**

   **Vault Analysis Flow:**
   ```
   1. Understand user goals (AskUserQuestion if unclear)
   2. Run analysis: bash ${CLAUDE_PLUGIN_ROOT}/skills/obsidian-pkm-manager/scripts/analyze_vault.py
   3. Interpret results (use skill knowledge)
   4. Generate prioritized recommendations
   5. Offer to implement top recommendations
   6. Validate changes
   ```

   **Template Creation Flow:**
   ```
   1. Gather requirements (use skill's template patterns)
   2. Design frontmatter (reference skill's schema guidelines)
   3. Write Templater logic (use skill's pattern library)
   4. Create/update Bases queries if needed
   5. Test template creation
   6. Document template usage
   ```

   **System Optimization Flow:**
   ```
   1. Analyze current vault structure
   2. Identify pain points (manual work, inconsistencies, etc.)
   3. Reference skill for best practices
   4. Propose improvements (specific, actionable)
   5. Implement incrementally (one change at a time)
   6. Verify each change before proceeding
   ```

3. **Decision Framework**
   - Use **commands** for deterministic operations (analysis, validation)
   - Use **agent orchestration** for multi-step reasoning workflows
   - Reference **skill** for domain knowledge and methodology
   - Invoke **scripts** via Bash with `${CLAUDE_PLUGIN_ROOT}` paths

4. **Output Format**
   - Provide clear status updates at each workflow step
   - Use code blocks with syntax highlighting for templates
   - Include file paths with line numbers for references
   - Offer next steps or alternative approaches

**Validation:**
- Use `skillsmith` to review agent quality
- Ensure agent description has clear triggering examples
- Test agent can load and reference skill content

#### Research Insights: Agent Development

**From Architecture Review:**
- Terminal-guru is agent-only (no commands) - not commands + agent as plan states
- For command patterns, reference skillsmith or ai-risk-mapper instead
- Add progressive disclosure to agent itself: Extract workflows to `agents/references/agent-workflows.md`
- Agent color (purple) appropriate for knowledge/methodology agents

**From Agent-Native Review:**
- **Critical**: Add vault path discovery via `.local.md` configuration
- **Critical**: Add vault structure injection to agent initialization (tree, templates, Bases queries)
- Missing template validation capability - agent can write but not test
- Document tool usage patterns in agent prompt (what each tool is for)
- Add anti-examples to agent description (when NOT to use agent)

**From Best Practices Research (2026):**
- Bounded Autonomy Pattern: Agent pauses and confirms before structural vault changes
- Plan-and-Execute for cost optimization: Use reasoning for complex decisions, execution for operations
- Multi-agent orchestration trend: Single all-purpose agents being replaced by specialized teams
- Progressive disclosure: Load skill metadata → SKILL.md → specific references as needed

**Recommended Agent Prompt Additions:**
```markdown
## Vault Context Initialization

At session start, load vault context:
1. Check for vault path in ${CLAUDE_PLUGIN_ROOT}/.local.md
2. If not configured, ask user and store for future sessions
3. Inject context:
   - Vault structure: `tree -L 2 -d ${VAULT_PATH}`
   - Available templates: `ls ${VAULT_PATH}/Templates/`
   - Active Bases: `find ${VAULT_PATH} -name "*.base"`
   - Recent activity: `ls -t ${VAULT_PATH}/Daily\ Notes/ | head -5`

## Tool Usage Documentation

- **Read**: Load skill content, vault notes, templates
- **Bash**: Run analysis scripts, execute vault tools
- **Glob**: Discover vault structure, find files by pattern
- **Grep**: Search vault for patterns, check metadata
- **Write**: Create templates, Bases queries
- **Edit**: Modify existing templates

## Bounded Autonomy

ALWAYS ask user confirmation before:
- Writing/editing files in vault
- Making bulk changes
- Running analysis on large vaults (>1000 notes)
```

**Configuration File to Create:**
`plugins/pkm-plugin/.local.md.example`:
```markdown
<!-- Copy to .local.md and customize -->
vault_path: /Users/username/Documents/MyVault
daily_notes_path: Daily Notes
templates_path: Templates
```

---

### Phase 3: Command Development

Create slash commands for direct access to deterministic operations.

**Command Namespace:** `/pkm:*` (consistent with plugin name)

#### Commands to Create

**1. `/pkm:analyze-vault` - Vault Analysis**

File: `plugins/pkm-plugin/commands/pkm-analyze-vault.md`

```markdown
Analyze an Obsidian vault for common issues and improvement opportunities.

Runs comprehensive vault analysis including:
- Untagged notes detection
- Orphaned files (no links in or out)
- Inconsistent frontmatter patterns
- Duplicate or similar note titles
- Missing temporal links in daily notes

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/obsidian-pkm-manager/scripts/analyze_vault.py $ARGUMENTS
```

Required arguments:
- `<vault-path>` - Path to Obsidian vault directory

Optional flags:
- `--check-tags` - Focus on tag consistency
- `--check-frontmatter` - Validate frontmatter schemas
- `--check-orphans` - Find unlinked notes

Examples:
```
/pkm:analyze-vault ~/Documents/MyVault
/pkm:analyze-vault ~/Documents/MyVault --check-tags
```
```

**2. `/pkm:validate-templates` - Template Validation**

File: `plugins/pkm-plugin/commands/pkm-validate-templates.md`

```markdown
Validate Templater templates against frontmatter schemas and best practices.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/obsidian-pkm-manager/scripts/validate_templates.py $ARGUMENTS
```

Required arguments:
- `<vault-path>` - Path to Obsidian vault directory

Optional flags:
- `--schema <file>` - Custom schema definition file

Examples:
```
/pkm:validate-templates ~/Documents/MyVault
```
```

**3. `/pkm:create-template` - Interactive Template Creation**

File: `plugins/pkm-plugin/commands/pkm-create-template.md`

```markdown
Launch interactive template creation wizard.

This command starts the pkm-manager agent in template creation mode.

```bash
echo "Template creation mode - launching pkm-manager agent"
# Agent orchestrates the template creation workflow
```

Examples:
```
/pkm:create-template
```

Note: This command triggers the agent workflow rather than running a direct script.
```

**Script Path Updates:**
- Current: `skills/obsidian-pkm-manager/scripts/analyze_vault.py`
- New: `plugins/pkm-plugin/skills/obsidian-pkm-manager/scripts/analyze_vault.py`
- Reference: `${CLAUDE_PLUGIN_ROOT}/skills/obsidian-pkm-manager/scripts/analyze_vault.py`

**Validation:**
- Test each command resolves paths correctly
- Verify `${CLAUDE_PLUGIN_ROOT}` expands properly
- Use `plugin-dev:plugin-validator` to check command structure

#### Research Insights: Command Development

**From Simplicity Review:**
- **RECOMMENDATION**: Start with ZERO commands or ONE command only
- `/pkm:create-template` just echoes and launches agent - unnecessary wrapper
- `/pkm:validate-templates` - no evidence script exists
- Terminal-guru succeeded with agent-only approach (no commands)
- Add commands in v1.1.0 only if users request them

**From Python Review:**
- **CRITICAL**: Add PEP 723 headers to all Python scripts
- **CRITICAL**: Create `plugins/pkm-plugin/pyproject.toml` for dependencies
- Scripts require PyYAML but have no dependency management
- Missing type hints throughout - add to all functions
- No error handling for file I/O operations
- YAML parsing inconsistent between scripts (one uses regex, one uses PyYAML)

**From Security Review:**
- **HIGH RISK**: Path traversal vulnerability in vault path acceptance
- **HIGH RISK**: No argument sanitization in `$ARGUMENTS` expansion
- Commands trust user-provided paths without validation
- YAML size limits needed to prevent bomb attacks
- Privacy concern: File paths may contain sensitive information

**From Best Practices Research (2026):**
- PEP 723 standardized in 2024 for uv inline metadata
- Command namespace should use consistent `/pkm-verb-noun` pattern
- Rich examples (2-3 per command) improve discoverability
- Suggest next steps after command execution

**Required Changes to Scripts:**

1. **Add PEP 723 Headers:**
```python
# analyze_vault.py
# /// script
# dependencies = [
#   "pyyaml>=6.0",
# ]
# requires-python = ">=3.11"
# ///

from pathlib import Path
from typing import Any
import sys

def validate_vault_path(vault_path_str: str) -> Path:
    """Validate vault path for security."""
    vault_path = Path(vault_path_str).resolve()

    # Must be directory
    if not vault_path.is_dir():
        raise ValueError(f"Not a directory: {vault_path}")

    # Block system directories
    forbidden = ['/etc', '/var', '/usr', '/bin', '/sbin', '/root']
    if any(str(vault_path).startsWith(p) for p in forbidden):
        raise ValueError(f"Access to system directory denied")

    return vault_path
```

2. **Update Command Invocations:**
```bash
# Add validation wrapper
SCRIPT_PATH="${CLAUDE_PLUGIN_ROOT}/skills/obsidian-pkm-manager/scripts/analyze_vault.py"
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: Script not found at $SCRIPT_PATH"
    exit 1
fi

uv run "$SCRIPT_PATH" "$@"
```

3. **Create pyproject.toml:**
```toml
[project]
name = "pkm-plugin"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "pyyaml>=6.0",
]
```

**Security Checklist:**
- [ ] Add path validation to both Python scripts
- [ ] Test with paths containing `..` sequences
- [ ] Test with system directory paths
- [ ] Add YAML size limits (10KB max frontmatter)
- [ ] Document privacy concerns in command help

---

### Phase 4: Skill Migration

**Tasks:**
- Move `skills/obsidian-pkm-manager/` → `plugins/pkm-plugin/skills/obsidian-pkm-manager/`
- Update `SKILL.md` metadata version to match plugin version
- Preserve all content:
  - `SKILL.md` (481 lines - no changes)
  - `IMPROVEMENT_PLAN.md`
  - `references/` directory
  - `scripts/` directory (analyze_vault.py, validate_frontmatter.py)
  - `assets/` directory
- Update skill frontmatter to reference plugin context

**Skill Frontmatter Update:**

```yaml
---
name: obsidian-pkm-manager
description: Expert guidance for managing Obsidian-based Personal Knowledge Management (PKM) systems...
metadata:
  version: "1.0.0"
  plugin: "pkm-plugin"
  stage: "3"
---
```

**No Content Changes:**
- Skill content remains unchanged (KISS principle)
- Agent loads skill for domain knowledge
- Progressive disclosure through references/ still applies

**Validation:**
- Use `skillsmith:skillsmith` to validate skill quality
- Ensure all references resolve correctly
- Check that scripts can be found by commands

#### Research Insights: Skill Migration

**From Data Integrity Review:**
- **CRITICAL**: Use `git mv` instead of shell `mv` for tracking
- **CRITICAL**: Create backup before migration: `tar czf /tmp/obsidian-pkm-manager-backup-$(date +%Y%m%d).tar.gz skills/obsidian-pkm-manager/`
- **CRITICAL**: Verify checksums after move to ensure content preservation
- Missing rollback strategy if later phases fail
- No atomic migration across all 7 phases

**From Migration Best Practices (2026):**
- Strangler Pattern: Replace components incrementally, not big-bang
- Validate at each phase before proceeding (gate pattern)
- Document migration in IMPROVEMENT_PLAN.md
- Keep original until fully validated

**From Plugin Validation Research:**
- Skillsmith validates via `evaluate_skill.py --quick --strict`
- Three modes: quick (structure), default (metrics), strict (warnings as errors)
- Pre-commit hook integration available for auto-validation
- Version must match between SKILL.md and plugin manifest

**Migration Safety Protocol:**

```bash
# Phase 0: Pre-Migration (NEW)
# 1. Create backup
tar czf /tmp/obsidian-pkm-manager-backup-$(date +%Y%m%d).tar.gz \
    skills/obsidian-pkm-manager/

# 2. Create feature branch
git checkout -b feat/pkm-plugin-migration

# 3. Baseline validation
uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py \
    skills/obsidian-pkm-manager --output baseline.json

# Phase 4: Migration with Verification
# 1. Use git mv for tracking
git mv skills/obsidian-pkm-manager plugins/pkm-plugin/skills/

# 2. Verify content integrity
md5sum plugins/pkm-plugin/skills/obsidian-pkm-manager/SKILL.md

# 3. Test scripts execute from new location
uv run plugins/pkm-plugin/skills/obsidian-pkm-manager/scripts/analyze_vault.py --help

# 4. Post-migration validation
uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py \
    plugins/pkm-plugin/skills/obsidian-pkm-manager --compare baseline.json
```

**Rollback Procedure (if Phase 6 validation fails):**
```bash
git checkout main
git branch -D feat/pkm-plugin-migration
# Original skill still intact
```

---

### Phase 5: Marketplace Integration

**Tasks:**
- Update `marketplace.json` to register pkm-plugin
- Remove old `obsidian-pkm-manager` skill entry (if present)
- Add new plugin entry with skill reference
- Verify marketplace structure

**Marketplace Entry:**

File: `.claude-plugin/marketplace.json`

Add to plugins array:
```json
{
  "name": "pkm-plugin",
  "description": "Personal Knowledge Management expert for Obsidian vaults with autonomous orchestration",
  "category": "productivity",
  "version": "1.0.0",
  "author": {
    "name": "J. Greg Williams",
    "email": "283704+totallyGreg@users.noreply.github.com"
  },
  "source": "./plugins/pkm-plugin",
  "skills": [
    "./skills/obsidian-pkm-manager"
  ]
}
```

**Remove Legacy Entry:**
- Find and remove standalone `obsidian-pkm-manager` entry from marketplace
- Skill is now bundled within plugin

**Validation:**
- Use `marketplace-manager` commands to sync and validate
- Ensure plugin appears in marketplace
- Check that skill path resolves correctly

#### Research Insights: Marketplace Integration

**From Data Integrity Review:**
- **CRITICAL**: DO NOT delete old marketplace entry - deprecate instead
- Removing entry breaks existing user installations
- Skill is present at lines 69-81 of marketplace.json
- Version sync automated via pre-commit hook

**From Plugin Validation Research:**
- marketplace-manager provides `sync_marketplace_versions.py` for auto-sync
- Pre-commit hook validates and syncs on every commit
- Version mismatches trigger auto-correction
- Path resolution: `./skills/obsidian-pkm-manager` is relative to plugin directory

**From Architecture Review:**
- Marketplace paths relative to plugin source, not repo root
- Full path: `plugins/pkm-plugin/skills/obsidian-pkm-manager/`
- Terminal-guru pattern shows proper bundled skill references

**Recommended Marketplace Strategy:**

**Instead of removing old entry, deprecate it:**
```json
{
  "plugins": [
    {
      "name": "pkm-plugin",
      "version": "1.0.0",
      "source": "./plugins/pkm-plugin",
      "skills": ["./skills/obsidian-pkm-manager"],
      "category": "productivity"
    }
  ],
  "skills": [
    {
      "name": "obsidian-pkm-manager",
      "description": "[DEPRECATED - Use pkm-plugin] Expert guidance for Obsidian PKM",
      "version": "1.0.0",
      "deprecated": true,
      "replacement": "pkm-plugin",
      "source": "./plugins/pkm-plugin/skills/obsidian-pkm-manager"
    }
  ]
}
```

**Migration Notice in SKILL.md:**
Add to top of migrated skill:
```markdown
> **⚠️ Migration Notice**: This skill is now part of `pkm-plugin`.
> Please install the plugin for full functionality including slash commands and agent orchestration.
> Standalone skill support will be removed in v2.0.0 (3 months).
```

**Version Synchronization:**
```bash
# Auto-sync via pre-commit hook (already installed)
# Or manual:
uv run plugins/marketplace-manager/skills/marketplace-manager/scripts/sync_marketplace_versions.py

# Verify no mismatches:
uv run plugins/marketplace-manager/skills/marketplace-manager/scripts/sync_marketplace_versions.py --dry-run
```

---

### Phase 6: Documentation

**Tasks:**
- Create `plugins/pkm-plugin/README.md`
- Document agent workflows
- Provide command usage examples
- Update repository docs

#### `plugins/pkm-plugin/README.md`

```markdown
# PKM Plugin

Personal Knowledge Management expert for Obsidian vaults with autonomous orchestration.

## Features

- **Autonomous Agent**: Orchestrates multi-step workflows for vault improvement
- **Slash Commands**: Direct access to analysis and validation tools
- **Comprehensive Skill**: Expert PKM methodology and best practices
- **Script Library**: Python tools for vault analysis and validation

## Agent: pkm-manager

The `pkm-manager` agent orchestrates complex PKM workflows:

### Vault Analysis Workflow
1. Runs comprehensive vault analysis
2. Interprets results using PKM expertise
3. Generates prioritized recommendations
4. Guides implementation of improvements

### Template Creation Workflow
1. Gathers requirements
2. Designs frontmatter schema
3. Writes Templater logic
4. Creates Bases queries
5. Tests and validates template

### System Optimization Workflow
1. Analyzes vault structure
2. Identifies pain points
3. Proposes specific improvements
4. Implements changes incrementally
5. Validates results

**Usage:**
Simply describe your PKM need, and the agent will orchestrate the appropriate workflow.

Examples:
- "Analyze my vault and suggest improvements"
- "Create a customer meeting note template"
- "Help me set up a temporal rollup system"

## Commands

### `/pkm:analyze-vault <vault-path>`

Comprehensive vault analysis for common issues:
- Untagged notes
- Orphaned files
- Inconsistent frontmatter
- Duplicate titles
- Missing temporal links

**Example:**
```bash
/pkm:analyze-vault ~/Documents/MyVault --check-tags
```

### `/pkm:validate-templates <vault-path>`

Validate Templater templates against schemas and best practices.

**Example:**
```bash
/pkm:validate-templates ~/Documents/MyVault
```

### `/pkm:create-template`

Launch interactive template creation workflow (triggers agent).

## Skill: obsidian-pkm-manager

Comprehensive domain knowledge for Obsidian PKM systems:

- Core PKM principles
- Templater patterns
- Bases query design
- Frontmatter schemas
- Temporal rollup systems
- Job-agnostic organization
- Vault analysis methodologies

**Progressive Disclosure:**
- `SKILL.md`: Overview and core capabilities
- `references/`: Detailed guides (templater-patterns, bases-patterns, etc.)
- `scripts/`: Automation tools
- `assets/`: Template examples and base files

## Installation

This plugin is available in the claude-mp marketplace.

## Version

Current version: 1.0.0

See `skills/obsidian-pkm-manager/IMPROVEMENT_PLAN.md` for version history and planned improvements.

## License

MIT
```

**Additional Documentation Updates:**
- Add entry to repository README listing pkm-plugin
- Consider creating `docs/lessons/pkm-plugin-architecture.md` documenting design decisions

---

## Recommended Simplifications (Based on YAGNI Review)

**From Simplicity Analysis:** The plan can be reduced by 48% (361 lines) while maintaining functionality. Here are recommended simplifications for v1.0.0:

### Option A: Minimal Plugin (Recommended for v1.0.0)

**Scope:**
1. Create plugin directory structure
2. Move skill intact (no changes)
3. Create minimal agent (30 lines)
4. Update marketplace
5. **NO COMMANDS** - Add in v1.1.0 if users request

**Benefits:**
- 30-minute implementation vs 7-phase project
- Follows terminal-guru pattern (agent-only)
- Users can already invoke agent naturally
- Reduces testing burden
- Easier rollback if issues found

**Files to Create:**
```
plugins/pkm-plugin/
├── .claude-plugin/plugin.json (12 lines)
├── agents/pkm-manager.md (30 lines)
├── README.md (15 lines)
├── .local.md.example (10 lines)
└── skills/obsidian-pkm-manager/ (moved as-is)
```

**Agent Prompt (Minimal):**
```markdown
---
name: pkm-manager
description: |
  Use this agent for multi-step PKM workflows: vault analysis, template creation, system optimization.

  <example>
  user: "Analyze my vault and suggest improvements"
  assistant: "I'll use the pkm-manager agent to orchestrate vault analysis."
  </example>

tools: ["Read", "Bash", "Grep", "Glob", "Edit", "Write"]
color: purple
---

# PKM Manager Agent

Load ${CLAUDE_PLUGIN_ROOT}/skills/obsidian-pkm-manager/SKILL.md for PKM expertise.

Run scripts via Bash from ${CLAUDE_PLUGIN_ROOT}/skills/obsidian-pkm-manager/scripts/ when needed.

Load vault path from ${CLAUDE_PLUGIN_ROOT}/.local.md or ask user.
```

**Acceptance Criteria (Simplified):**
- [ ] Plugin loads in Claude Code
- [ ] Agent responds when invoked
- [ ] Skill content accessible
- [ ] Marketplace shows plugin
- [ ] Scripts execute from new paths

### Option B: Keep Current Plan (With Fixes)

If you prefer the 3-command approach, apply these fixes:

**Remove `/pkm:create-template`** - It's just a wrapper that launches the agent. Users can ask agent directly.

**Defer `/pkm:validate-templates`** - No evidence the script exists. Add in v1.1.0 if users request.

**Keep only `/pkm:analyze-vault`** - This provides clear value as a deterministic operation.

**Reduce Documentation:** README from 106 lines → 20 lines (just pointer to SKILL.md)

**Result:** ~150-line plan instead of 749 lines, identical functionality.

---

## Acceptance Criteria

### Functional Requirements

- [ ] Plugin directory structure created following conventions
- [ ] `plugin.json` manifest complete and valid
- [ ] Agent `pkm-manager.md` created with:
  - [ ] Complete YAML frontmatter with examples
  - [ ] System prompt with workflow orchestration patterns
  - [ ] Tool access configuration
- [ ] Three slash commands created and functional:
  - [ ] `/pkm:analyze-vault` wraps analysis script
  - [ ] `/pkm:validate-templates` wraps validation script
  - [ ] `/pkm:create-template` triggers agent workflow
- [ ] Skill migrated to `plugins/pkm-plugin/skills/obsidian-pkm-manager/`
- [ ] All existing skill content preserved (SKILL.md, references, scripts, assets)
- [ ] Marketplace entry added to `.claude-plugin/marketplace.json`
- [ ] README.md created with comprehensive documentation

### Integration Requirements

- [ ] Agent can load and reference skill content
- [ ] Commands correctly resolve `${CLAUDE_PLUGIN_ROOT}` paths
- [ ] Scripts execute successfully from new location
- [ ] Marketplace recognizes plugin and bundled skill

### Quality Gates

- [ ] `plugin-dev:plugin-validator` passes all checks
- [ ] `skillsmith` validates skill quality (no regressions)
- [ ] Agent description has clear triggering examples
- [ ] All commands have usage examples
- [ ] Documentation includes workflow diagrams

### Testing Checklist

- [ ] Test vault analysis workflow end-to-end
- [ ] Test template creation workflow
- [ ] Test each slash command independently
- [ ] Verify skill references load correctly
- [ ] Confirm scripts execute from new paths
- [ ] Validate marketplace integration

## Success Metrics

**Immediate (v1.0.0):**
- Plugin structure validated by plugin-dev tools
- All three commands functional
- Agent successfully orchestrates at least one complete workflow
- No regressions in skill quality scores

**Short-term (v1.1.0):**
- User adoption: 3+ successful vault analyses
- Template creation: 5+ templates created via agent
- Command usage: 10+ command invocations

**Long-term (Phase 2 - Skill Split):**
- Foundation enables clean skill decomposition
- Organizational principles skill extracted
- Technical Obsidian interaction skill extracted
- Agent routes between skills effectively

## Dependencies & Prerequisites

**Required Tools:**
- `plugin-dev:plugin-validator` for structure validation
- `skillsmith` for skill quality validation
- `marketplace-manager` for marketplace sync

**Prerequisite Knowledge:**
- Plugin structure patterns (from docs/lessons/skill-to-plugin-migration.md)
- Agent development patterns (from terminal-guru example)
- Command development conventions (from plugin-dev:command-development)

**Blocking Issues:**
- None - all dependencies are available in repository

## Risk Analysis & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Script paths break after migration** | High | Medium | Use `${CLAUDE_PLUGIN_ROOT}` for all paths; comprehensive testing |
| **Agent can't load skill content** | High | Low | Follow terminal-guru pattern; test skill loading early |
| **Marketplace integration fails** | Medium | Low | Use marketplace-manager tools; validate before committing |
| **Skill quality regression** | Medium | Low | Run skillsmith validation; no content changes to SKILL.md |
| **Command namespace conflict** | Low | Low | Use `/pkm:*` namespace; check for conflicts in marketplace |

**Mitigation Strategy:**
1. **Incremental validation**: Validate at each phase before proceeding
2. **Reference architecture**: Follow terminal-guru pattern exactly
3. **Tool usage**: Leverage plugin-dev and skillsmith for quality gates
4. **Testing**: Manual testing of each workflow before release

## Future Considerations (Phase 2)

**Skill Decomposition:**
When splitting into organizational vs technical skills:

1. **Create two new skills:**
   - `pkm-principles/` - PKM methodology, organizational patterns, best practices
   - `obsidian-technical/` - Templater, Bases, plugins, frontmatter, scripts

2. **Update agent to route:**
   - Methodology questions → load pkm-principles
   - Technical implementation → load obsidian-technical
   - Complex workflows → load both as needed

3. **Benefits of split:**
   - Clearer skill focus and discoverability
   - Easier maintenance (methodology vs implementation)
   - Better progressive disclosure (principles vs tactics)

**Not included in this phase:**
- Hook development (future enhancement)
- MCP integration (future enhancement)
- Additional automation scripts (future enhancement)

## References & Research

### Internal References

**Plugin Architecture:**
- Terminal-guru example: `/Users/gregwilliams/Documents/Projects/claude-mp/plugins/terminal-guru/`
- Agent pattern: `plugins/terminal-guru/agents/terminal-guru.md:1-91`
- Skill bundling: `plugins/terminal-guru/skills/terminal-emulation/SKILL.md`

**Documentation:**
- Migration guide: `/Users/gregwilliams/Documents/Projects/claude-mp/docs/lessons/skill-to-plugin-migration.md`
- Architecture patterns: `/Users/gregwilliams/Documents/Projects/claude-mp/docs/lessons/plugin-integration-and-architecture.md`
- Workflow: `/Users/gregwilliams/Documents/Projects/claude-mp/WORKFLOW.md`

**Existing Skill:**
- Current location: `/Users/gregwilliams/Documents/Projects/claude-mp/skills/obsidian-pkm-manager/SKILL.md`
- Scripts: `skills/obsidian-pkm-manager/scripts/analyze_vault.py`
- References: `skills/obsidian-pkm-manager/references/`

**Marketplace:**
- Marketplace manifest: `/Users/gregwilliams/Documents/Projects/claude-mp/.claude-plugin/marketplace.json`
- Example plugin entries: Lines 10-25 (terminal-guru)

### Related Work

**Similar Migrations:**
- terminal-guru: Evolved from standalone skill to plugin with agent (Stage 3)
- omnifocus-manager: Currently at Stage 2 (planning Stage 3 evolution)

**Tool Dependencies:**
- plugin-dev skills for validation and best practices
- skillsmith for quality metrics and improvement tracking
- marketplace-manager for distribution

### Best Practices Applied

1. **KISS Principle**: Defer skill split to Phase 2 - migrate first, refine later
2. **YAGNI Principle**: Don't add hooks or MCP until needed
3. **DRY Principle**: Reference skill content rather than duplicating in agent
4. **SOLID Principles**: Single responsibility (agent orchestrates, skill provides knowledge)

## Implementation Checklist

### Phase 1: Directory Structure
- [ ] Create `plugins/pkm-plugin/` directory
- [ ] Create subdirectories: `.claude-plugin/`, `agents/`, `commands/`, `skills/`
- [ ] Initialize `plugin.json` manifest
- [ ] Create README.md skeleton

### Phase 2: Agent Development
- [ ] Create `agents/pkm-manager.md`
- [ ] Write agent frontmatter (name, description, examples, tools)
- [ ] Write agent system prompt (workflow patterns)
- [ ] Add agent documentation to README.md

### Phase 3: Command Development
- [ ] Create `/pkm:analyze-vault` command
- [ ] Create `/pkm:validate-templates` command
- [ ] Create `/pkm:create-template` command
- [ ] Test `${CLAUDE_PLUGIN_ROOT}` path resolution

### Phase 4: Skill Migration
- [ ] Move skill directory to plugin
- [ ] Update skill frontmatter metadata
- [ ] Verify all scripts still accessible
- [ ] Test skill content loading

### Phase 5: Marketplace Integration
- [ ] Add plugin entry to marketplace.json
- [ ] Remove legacy skill entry (if exists)
- [ ] Run marketplace sync
- [ ] Verify plugin discoverable

### Phase 6: Validation & Testing
- [ ] Run `plugin-dev:plugin-validator`
- [ ] Run `skillsmith` skill validation
- [ ] Test vault analysis workflow
- [ ] Test template creation workflow
- [ ] Test each command independently

### Phase 7: Documentation & Release
- [ ] Complete README.md
- [ ] Update IMPROVEMENT_PLAN.md
- [ ] Create GitHub Issue for tracking
- [ ] Commit with descriptive message
- [ ] Tag release v1.0.0

---

## Next Steps After Plan Approval

1. **Create GitHub Issue**: Use this plan as issue body
2. **Run plugin-dev:plugin-validator**: Check structure before starting
3. **Start with Phase 1**: Directory setup (lowest risk)
4. **Validate incrementally**: Run validators after each phase
5. **Test thoroughly**: Each workflow before declaring complete

## Questions for Implementation

**Answered by Research:**

> Should we add additional commands beyond the three proposed?

**NO** - Start with zero commands (agent-only) or one command (`/pkm:analyze-vault`). Terminal-guru succeeded with agent-only approach. Add commands in v1.1.0 only if users request them.

> Do we need a hook for automatic vault analysis on session start?

**NOT YET** - YAGNI. Add in v1.1.0 if users request. Automatic analysis might be noisy for large vaults.

> Should we create a `.local.md` file for user vault path configuration?

**YES - CRITICAL** - This is essential for context parity. Agent needs to know vault location to provide situated recommendations. See Phase 2 research insights for implementation.

> Do we want metrics tracking for agent workflow success rates?

**YES for v1.1.0** - Track workflow completions, template creation success, command invocation frequency. Not blocking for v1.0.0.

---

## Consolidated Research Findings

### Summary of All Agent Reviews

**10 Parallel Agents Run:** Architecture Strategist, Code Simplicity Reviewer, Pattern Recognition Specialist, Kieran Python Reviewer, Data Integrity Guardian, Agent-Native Reviewer, Security Sentinel, Best Practices Researcher, Framework Docs Researcher, Plugin Validation Explorer

**Overall Assessment:** CONDITIONAL GO with critical fixes required

### Must-Fix Before Implementation (P0)

1. **Add Python Dependency Management**
   - Create `pyproject.toml` with PyYAML dependency
   - Add PEP 723 headers to both Python scripts
   - Add path validation functions to scripts
   - **Blocking**: Scripts won't run without PyYAML

2. **Add Vault Path Configuration**
   - Create `.local.md.example` with vault_path field
   - Add vault context injection to agent initialization
   - **Blocking**: Agent is blind to user's vault without this

3. **Implement Security Validation**
   - Add path validation to prevent directory traversal
   - Validate vault paths before script execution
   - Add YAML size limits (10KB max frontmatter)
   - **Blocking**: High security risk without validation

4. **Use git Feature Branch**
   - Create backup before migration
   - Use `git mv` for tracking
   - Validate each phase before proceeding
   - **Blocking**: No rollback capability without this

### Should-Fix (P1)

5. **Add Type Hints to Python Scripts**
   - All functions need type annotations
   - Improves maintainability and IDE support
   - Can be done post-merge but track as debt

6. **Simplify to Minimal v1.0.0**
   - Remove `/pkm:create-template` command (unnecessary wrapper)
   - Defer `/pkm:validate-templates` to v1.1.0
   - Keep only `/pkm:analyze-vault` or go agent-only
   - Reduces implementation time by 80%

7. **Add Error Handling**
   - File I/O operations need try/catch
   - Invalid YAML should warn, not silently fail
   - Missing dependencies should fail gracefully

8. **Deprecate (Don't Delete) Marketplace Entry**
   - Keep standalone skill with deprecated flag
   - Point to new plugin location
   - Prevents breaking existing users

### Nice-to-Have (P2)

9. **Progressive Disclosure for Agent**
   - Extract workflows to `agents/references/agent-workflows.md`
   - Shorter agent prompt, load details as needed
   - Follows skill architecture pattern

10. **Add Anti-Examples to Agent Description**
    - Show when NOT to use agent
    - Prevents over-invocation
    - Improves routing accuracy

### Research Highlights

**Agent Orchestration (2026 Trends):**
- 1,445% surge in multi-agent system inquiries (Gartner)
- Plan-and-execute pattern reduces costs 90%
- Bounded autonomy: Pause for confirmation on destructive ops

**Python Best Practices:**
- PEP 723 standardized in 2024 for uv inline metadata
- Eliminates requirements.txt for standalone scripts
- Type hints mandatory for new code

**Obsidian PKM:**
- Bases queries handle 50,000+ notes instantly
- Dataview deprecated for performance reasons
- PKM frameworks: Zettelkasten, PARA, LYT (skill already follows)

**Security:**
- Path traversal is #1 risk for file-based tools
- YAML bomb attacks possible without size limits
- Privacy: Vault paths may contain sensitive filenames

**Plugin Migration:**
- Strangler pattern: Incremental replacement
- Use git feature branch for atomic rollback
- Pre-commit hooks prevent version mismatches
- Validate at each phase before proceeding

### Verdict: Proceed with Critical Fixes

**Migration is SAFE** with P0 fixes implemented. The core architecture is sound. Primary issues are:
1. Missing Python dependency management (easily fixed with PEP 723 + pyproject.toml)
2. Security gaps in path validation (easily fixed with validation function)
3. Context starvation (easily fixed with .local.md config)
4. Over-engineering (easily simplified by removing unnecessary commands)

**Recommended Path:**
1. Implement P0 fixes
2. Use minimal v1.0.0 approach (Option A)
3. Validate thoroughly before merging
4. Add P1 fixes in v1.1.0 based on user feedback

**Estimated Implementation Time:**
- Minimal v1.0.0: 30-60 minutes
- With all fixes: 2-3 hours
- Original plan: 6-8 hours

The research strongly supports a minimal first release with incremental enhancement.
