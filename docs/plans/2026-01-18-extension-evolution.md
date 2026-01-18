# Claude-MP Extension Evolution Plan

## Executive Summary

The claude-mp repository currently focuses exclusively on **skills** (9 published), but contains repeatable patterns that could benefit from Claude Code's full extension ecosystem: **commands**, **agents**, **MCP servers**, and **hooks**.

This plan identifies:
1. **Repeatable patterns** that could be extracted into shared tooling
2. **Functionality better suited** to different extension types
3. **Evolution pathways** for existing skills
4. **Decision framework** for choosing extension types

## Current State Analysis

### Repository Structure
```
claude-mp/
├── skills/              (9 published skills - ONLY active extension type)
│   ├── omnifocus-manager    (most complex: 22 scripts, TypeScript validation)
│   ├── skillsmith           (meta-skill: creates/improves skills)
│   ├── marketplace-manager  (meta-skill: marketplace operations)
│   ├── skill-planner        (meta-skill: planning workflow)
│   └── [6 domain skills]    (terminal-guru, swift-dev, helm-chart-developer, etc.)
├── agents/              (placeholder - not implemented)
├── commands/            (placeholder - not implemented)
├── mcp-servers/         (placeholder - not implemented)
├── hooks/               (placeholder - not implemented)
└── docs/
    ├── lessons/         (post-work retrospectives)
    └── plans/           (pre-work planning)
```

### Identified Repeatable Patterns

#### 1. **Repository Detection** (High-value extraction candidate)
- **Used by**: skillsmith, marketplace-manager, skill-planner (3+ skills)
- **Pattern**: `find_repo_root()` - searches for `.git` or `.claude-plugin` directory
- **Current duplication**: Each skill has own `utils.py` with identical logic
- **Location**: `skills/*/scripts/utils.py`
- **Opportunity**: Extract to shared library/command

#### 2. **Validation Framework** (High-value extraction candidate)
- **Used by**: skillsmith, marketplace-manager, omnifocus-manager
- **Pattern**: YAML parsing, regex validation, error aggregation
- **Examples**:
  - `evaluate_skill.py` - comprehensive skill validation
  - `validate-plugin.sh` - plugin structure validation
  - `sync_marketplace_versions.py` - version consistency checking
- **Opportunity**: Create base validation classes or shared validation command

#### 3. **PEP 723 Script Pattern** (Template candidate)
- **Used by**: All Python scripts (100% adoption)
- **Pattern**: Inline dependency metadata for `uv` execution
  ```python
  # /// script
  # dependencies = ["pyyaml>=6.0.1"]
  # ///
  ```
- **Opportunity**: Script template generator (enhance skillsmith)

#### 4. **TypeScript Validation** (Specialized, reusable module)
- **Used by**: omnifocus-manager only (but pattern is valuable)
- **Pattern**: Parse TypeScript, validate against `.d.ts` type definitions
- **Tools**: TypeScript compiler API for syntax/type checking
- **Opportunity**: Reusable TypeScript validation module for other JS-based skills

#### 5. **Version Synchronization** (Automation candidate)
- **Used by**: marketplace-manager
- **Pattern**: Read SKILL.md versions → sync to marketplace.json
- **Current**: Manual script execution
- **Opportunity**: Pre-commit hook for automatic version sync

#### 6. **IMPROVEMENT_PLAN.md Format** (Automation candidate)
- **Pattern**: Standardized table format (as of v3.2.0+)
  ```markdown
  | Issue | Priority | Title | Status |
  |-------|----------|-------|--------|
  | #123  | High     | Feature | Open |
  ```
- **Opportunity**: Auto-generate from GitHub Issues API

## Recommendations by Extension Type

### 1. **COMMANDS** - Quick-Access Wrappers

**What should become commands:**
- Repeatable validation and utility operations
- Project-wide tooling that benefits all skills
- Quick shortcuts for common workflows

**Specific Recommendations:**

#### A. `/validate-skill <path>` Command
```bash
# Wraps evaluate_skill.py with cleaner interface
claude code /validate-skill skills/omnifocus-manager
```
**Why command over skill:**
- Explicit invocation preferred (not auto-triggered)
- Quick validation workflow
- No domain knowledge needed, just execution

**Implementation:**
```bash
.claude/commands/validate-skill.md
# Defines command interface
# Executes: uv run [shared-scripts]/evaluate_skill.py $1
```

#### B. `/sync-versions` Command
```bash
# Syncs all skill versions to marketplace.json
claude code /sync-versions
```
**Why command:**
- Clear, explicit action
- Pre-release checklist item
- Simple wrapper around existing script

#### C. `/init-skill <name>` Command
```bash
# Quick scaffold for new skills
claude code /init-skill my-new-skill
```
**Why command:**
- Explicit creation workflow
- Could replace/supplement skillsmith for simple cases
- Clear command-palette discoverability

### 2. **SHARED UTILITIES** - Common Library

**Recommendation: Create `claude-mp-utils` package**

**Structure:**
```
utils/
├── __init__.py
├── repo.py           # Repository detection (extract from skills/*/scripts/utils.py)
├── validation.py     # Base validation classes and utilities
├── templates.py      # PEP 723 templates, script scaffolding
└── marketplace.py    # Marketplace operations (version sync, etc.)
```

**How skills would use it:**
```python
# /// script
# dependencies = [
#   "../../utils",  # Relative import to shared utils
# ]
# ///
from claude_mp_utils.repo import find_repo_root
from claude_mp_utils.validation import SkillValidator
```

**Benefits:**
- DRY principle adherence
- Single source of truth for common patterns
- Easier maintenance and testing
- Consistent behavior across skills

### 3. **MCP SERVERS** - External Tool Integration

**Recommendation: Extract OmniFocus query operations to MCP server**

#### A. `omnifocus-mcp-server` (High Priority)

**Why MCP server over skill:**
- **Query operations** are tool calls, not knowledge transfer
  - "Show me tasks due today" → Tool call, not workflow guidance
  - "What's in my inbox?" → Data retrieval, not GTD expertise
- **Separation of concerns**:
  - MCP Server = OmniFocus data access (queries, task CRUD)
  - Skill = GTD methodology, workflow guidance, plugin generation
- **Reusability**: Other Claude instances could use same MCP server
- **Real-time data**: Direct OmniFocus database/JXA access

**Proposed Split:**

**MCP Server (`omnifocus-mcp-server`):**
```typescript
// Tools exposed via MCP
- omnifocus.getTasks(filter)       // Query tasks
- omnifocus.createTask(params)     // Create task
- omnifocus.updateTask(id, params) // Update task
- omnifocus.search(query)          // Search tasks
- omnifocus.getProjects()          // List projects
```

**Skill (`omnifocus-manager`):**
- GTD methodology guidance
- Plugin generation workflow (keep existing scripts)
- Workflow recommendations
- Best practices and patterns
- References to GTD, automation guides

**Benefits:**
- Clean separation: data access (MCP) vs knowledge (skill)
- MCP server handles authentication, error handling, data formatting
- Skill focuses on guiding users through GTD workflows
- Other skills could leverage OmniFocus data without duplicating JXA code

**Migration Path:**
1. Create `mcp-servers/omnifocus/` with core query/CRUD tools
2. Update `omnifocus-manager` skill to reference MCP tools
3. Keep plugin generation in skill (it's guidance, not data access)
4. Eventually: Extract plugin generation scripts to `/commands/` for explicit access

### 4. **AGENTS** - Autonomous Multi-Step Work

**Recommendation: Evolve meta-skills into agents when available**

#### A. `skillsmith` → Agent

**Why agent over skill:**
- Shows agent-like behavior: routing between quick updates vs complex planning
- Multi-phase autonomous workflow (research → design → implement)
- Decision-making based on improvement complexity
- Coordinates with skill-planner for complex work

**Current pattern (skill-based):**
```
User request → skillsmith analyzes → routes to:
  - Direct update (simple changes)
  - Delegate to skill-planner (complex changes)
```

**As agent:**
```
User request → skillsmith agent autonomously:
  1. Analyzes improvement request
  2. Decides approach (quick vs planned)
  3. Executes or coordinates with skill-planner
  4. Validates and reports results
```

#### B. `skill-planner` → Agent

**Why agent:**
- Multi-phase workflow: research → plan → approve → implement
- Git branch management (create, switch, merge)
- Autonomous decision-making about planning approach
- Background processing of complex improvements

#### C. `marketplace-manager` → Agent (Lower priority)

**Current behavior is already semi-autonomous:**
- Detects version changes
- Updates marketplace.json
- Validates consistency
- Can be invoked programmatically by other skills

**As agent:**
- Could run as background process monitoring for version changes
- Autonomous marketplace submission/publishing
- Dependency resolution across plugin ecosystem

### 5. **HOOKS** - Event Automation

**Recommendation: Extract validation into pre-commit hooks**

#### A. Pre-Commit Hook: Version Sync
```bash
.claude/hooks/pre-commit/sync-marketplace-versions.sh
# Automatically runs sync_marketplace_versions.py before commits
# Ensures marketplace.json always reflects SKILL.md versions
```

**Why hook:**
- Automatic enforcement (no manual step)
- Prevents version drift
- Current workflow has this pattern (mentioned in docs)

#### B. Pre-Commit Hook: IMPROVEMENT_PLAN.md Validation
```bash
.claude/hooks/pre-commit/validate-improvement-plan.sh
# Validates IMPROVEMENT_PLAN.md table format
# Ensures Issue references are valid
# Checks for required columns
```

**Why hook:**
- Enforces standardized format
- Catches errors before commit
- Aligns with WORKFLOW.md principles

#### C. Post-Commit Hook: Auto-Update Issues
```bash
.claude/hooks/post-commit/update-github-issues.sh
# Parses commit message for issue references
# Updates GitHub issue checkboxes via gh CLI
# Keeps issue task lists in sync
```

**Why hook:**
- Automates GitHub Issues ↔ commits sync
- Reduces manual issue management
- Aligns with "GitHub Issues as source of truth"

## Decision Framework

**Use this framework to choose extension types for future patterns:**

| **If the pattern...**                          | **Use**        | **Example**                          |
|------------------------------------------------|----------------|--------------------------------------|
| Provides domain knowledge/workflows            | **Skill**      | helm-chart-developer, swift-dev      |
| Wraps external system data access              | **MCP Server** | omnifocus-mcp-server                 |
| Quick explicit action/shortcut                 | **Command**    | /validate-skill, /sync-versions      |
| Multi-step autonomous orchestration            | **Agent**      | skillsmith, skill-planner            |
| Automatic enforcement on events                | **Hook**       | pre-commit version sync              |
| Shared utility across multiple extensions      | **Library**    | claude-mp-utils (repo detection)     |

**Key Questions:**

1. **Does it need to coordinate multiple steps autonomously?** → Agent
2. **Does it access external system data?** → MCP Server
3. **Should it trigger automatically on events?** → Hook
4. **Is it an explicit one-off action?** → Command
5. **Does it provide knowledge/guidance?** → Skill
6. **Is it reusable logic across extensions?** → Shared Library

## Specific Implementation Priorities (UPDATED)

### Phase 1: Foundation (PRIORITY - Start Here)
**Goal**: Extract common patterns, enable automation, design for future agents
**Timeline**: 3-4 days total
**GitHub Issue**: Create comprehensive issue for Phase 1 work

#### 1.1 Create `utils/` Python Package (2 days)
**Directory structure:**
```
utils/
├── __init__.py              # Package initialization
├── pyproject.toml           # Package metadata (optional, for uv)
├── repo.py                  # Repository detection
├── validation.py            # Base validation classes
├── templates.py             # PEP 723 script templates
└── marketplace.py           # Marketplace operations
```

**Implementation details:**
- **`repo.py`**: Extract `find_repo_root()`, `get_repo_root()` from skills/*/scripts/utils.py
- **`validation.py`**: Base classes for YAML parsing, regex validation, error aggregation
- **`templates.py`**: PEP 723 script templates, skill scaffolding helpers
- **`marketplace.py`**: Version sync logic, marketplace.json operations

**Skills to update** (use new package):
- skillsmith, marketplace-manager, skill-planner (primary users)
- Remove duplicated utils.py files after migration

**Design consideration**: Structure for easy agent consumption
- Agent-friendly interfaces (return structured data, not just print)
- Clear error types and messages for autonomous handling

#### 1.2 Create Commands (1 day)
**Commands to create:**

```markdown
.claude/commands/
├── validate-skill.md        # Validate skill structure/compliance
├── sync-versions.md         # Sync SKILL.md versions → marketplace.json
└── init-skill.md            # Scaffold new skill (uses utils package)
```

**Command implementations:**
- `/validate-skill <path>` → `uv run utils/scripts/validate_skill_cli.py $1`
- `/sync-versions` → `uv run utils/scripts/sync_versions_cli.py`
- `/init-skill <name>` → `uv run utils/scripts/init_skill_cli.py $1`

**Note**: Commands wrap utils package for CLI interface
- Provides explicit, discoverable access
- Useful during development and debugging
- Complements automatic hooks

#### 1.3 Add Hooks (1 day)
**Hooks to create:**

```bash
.claude/hooks/
├── pre-commit/
│   ├── sync-marketplace-versions.sh    # Auto-sync versions
│   └── validate-improvement-plan.sh    # Validate table format
└── post-commit/
    └── update-github-issues.sh         # Sync commit → issue checkboxes
```

**Hook behavior:**
- **Pre-commit**: Automatic enforcement (can be bypassed with --no-verify)
- Hooks use utils package for consistency
- Same validation logic as commands (DRY)

**Configuration:**
```json
// .claude/settings.json (if needed)
{
  "hooks": {
    "pre-commit": [
      ".claude/hooks/pre-commit/sync-marketplace-versions.sh",
      ".claude/hooks/pre-commit/validate-improvement-plan.sh"
    ]
  }
}
```

#### 1.4 Documentation (half day)
- Update README.md with new utils package usage
- Document command usage in `.claude/commands/README.md`
- Add migration guide: `docs/lessons/shared-utils-migration.md`
- Update WORKFLOW.md with hook references

**Phase 1 Success Criteria:**
- [ ] All common patterns extracted to utils package
- [ ] Skills updated to use shared utils (no duplicated code)
- [ ] Commands working and documented
- [ ] Hooks running automatically on commit
- [ ] Tests for utils package (basic validation)

---

### Phase 2: OmniFocus MCP Server (AFTER Phase 1)
**Goal**: Proper separation of data access vs knowledge
**Timeline**: 4-5 days
**GitHub Issue**: Create separate issue after Phase 1 completion

#### 2.1 Design MCP Server Interface (1 day)
**Research and design:**
- Review MCP SDK documentation
- Design tool interface (getTasks, createTask, etc.)
- Plan authentication and error handling
- Decide on OmniFocus access method (JXA vs direct DB)

#### 2.2 Implement `omnifocus-mcp-server` (2-3 days)
**Directory structure:**
```
mcp-servers/omnifocus/
├── src/
│   ├── index.ts             # MCP server entry point
│   ├── tools/               # Tool implementations
│   │   ├── getTasks.ts
│   │   ├── createTask.ts
│   │   ├── updateTask.ts
│   │   └── search.ts
│   └── omnifocus/           # OmniFocus integration layer
│       ├── jxa.ts           # JXA wrapper
│       └── types.ts         # TypeScript types
├── package.json
├── tsconfig.json
└── README.md
```

**Tools to implement:**
- `omnifocus.getTasks(filter)` - Query tasks with filtering
- `omnifocus.createTask(params)` - Create new task
- `omnifocus.updateTask(id, params)` - Update existing task
- `omnifocus.deleteTask(id)` - Delete task
- `omnifocus.search(query)` - Full-text search
- `omnifocus.getProjects()` - List all projects
- `omnifocus.getTags()` - List all tags

#### 2.3 Update `omnifocus-manager` Skill (1 day)
**Refactor skill to focus on knowledge:**
- Remove query/CRUD examples (now in MCP server)
- Add references to MCP server tools
- Keep plugin generation workflow (guidance, not data access)
- Update documentation to explain MCP + skill split
- Add "How to use MCP tools" section

**Skill becomes:**
- GTD methodology guidance
- Plugin generation workflow (deterministic, TypeScript-validated)
- Automation patterns and best practices
- References to GTD principles, OmniFocus features

#### 2.4 Create Optional Command (1 day)
```markdown
.claude/commands/generate-omnifocus-plugin.md
# Quick access to plugin generation
# Wraps: node skills/omnifocus-manager/scripts/generate_plugin.js
```

**Phase 2 Success Criteria:**
- [ ] MCP server running and tools working
- [ ] omnifocus-manager skill updated (no query examples)
- [ ] Documentation clear on MCP vs skill separation
- [ ] Tests for MCP server tools
- [ ] Performance acceptable (JXA response times)

---

### Phase 3: Agent Migration (FUTURE - When Available)
**Goal**: Autonomous multi-step orchestration
**Timeline**: 2-3 days per agent (depends on SDK)
**Prerequisites**: Agent functionality available in Claude Code

#### 3.1 Skillsmith → Agent
**Design considerations:**
- Autonomous routing: quick update vs complex planning
- Background processing of improvements
- Coordination with skill-planner agent
- State management across multiple phases

**Migration approach:**
- Extract core logic to utils package (Phase 1 makes this easier)
- Create agent wrapper around existing logic
- Maintain skill as fallback or simple interface
- Agent handles complex orchestration autonomously

#### 3.2 Skill-Planner → Agent
**Design considerations:**
- Git branch workflow automation
- Multi-phase autonomous workflow (research → plan → implement)
- Background processing while user continues work
- State persistence across sessions

#### 3.3 Marketplace-Manager → Agent (Lower Priority)
**Design considerations:**
- Background monitoring of version changes
- Autonomous marketplace operations
- Dependency resolution

**Phase 3 Success Criteria:**
- [ ] Agents running autonomously
- [ ] Clear handoff from skills to agents
- [ ] State management working
- [ ] Performance acceptable
- [ ] Fallback to skills if agent fails

## Example: OmniFocus Split

**Current (All-in-One Skill):**
```
omnifocus-manager skill:
  - GTD methodology ✓ (keep)
  - Query tasks       ✗ (move to MCP)
  - Create tasks      ✗ (move to MCP)
  - Plugin generation ✓ (keep)
  - Automation guide  ✓ (keep)
```

**Proposed (Split Architecture):**
```
omnifocus-mcp-server:
  - Tools: getTasks(), createTask(), updateTask(), search()
  - Direct OmniFocus database/JXA access
  - Authentication and error handling

omnifocus-manager skill:
  - When to use: GTD workflows, plugin creation
  - How to use: Workflow guidance, best practices
  - References: GTD methodology, automation guides
  - Scripts: generate_plugin.js, validate-plugin.sh

/generate-omnifocus-plugin command (optional):
  - Quick access to plugin generation
  - Wraps: node scripts/generate_plugin.js
```

## Migration Path for Existing Patterns

### Extract Shared Utilities

**Step 1**: Create shared utils package
```bash
mkdir -p utils
touch utils/__init__.py
```

**Step 2**: Extract common code
```python
# utils/repo.py
def find_repo_root(start_path=None):
    # Extract from skills/skillsmith/scripts/utils.py
    ...
```

**Step 3**: Update skills to use shared utils
```python
# skills/skillsmith/scripts/evaluate_skill.py
# /// script
# dependencies = ["../../utils"]
# ///
from claude_mp_utils.repo import find_repo_root  # Use shared
```

**Step 4**: Remove duplicated utils.py files
```bash
# Keep as reference, but remove from active skills
git mv skills/skillsmith/scripts/utils.py skills/skillsmith/scripts/utils.py.old
```

### Create Commands

**Step 1**: Create command directory
```bash
mkdir -p .claude/commands
```

**Step 2**: Define command
```markdown
# .claude/commands/validate-skill.md
---
name: validate-skill
description: Validate a skill's structure and compliance
---

Validates skill structure, frontmatter, and AgentSkills spec compliance.

Usage: /validate-skill <skill-path>

This command wraps skillsmith's evaluate_skill.py with better UX.
```

**Step 3**: Create command script
```bash
# .claude/commands/validate-skill.sh
#!/bin/bash
uv run skills/skillsmith/scripts/evaluate_skill.py "$@"
```

### Create Hooks

**Step 1**: Create hooks directory
```bash
mkdir -p .claude/hooks/pre-commit
```

**Step 2**: Create hook script
```bash
# .claude/hooks/pre-commit/sync-versions.sh
#!/bin/bash
python3 skills/marketplace-manager/scripts/sync_marketplace_versions.py
git add .claude-plugin/marketplace.json
```

**Step 3**: Configure Claude Code to run hooks
```json
// .claude/settings.json
{
  "hooks": {
    "pre-commit": [
      ".claude/hooks/pre-commit/sync-versions.sh"
    ]
  }
}
```

## Benefits Summary

### For Users
- **Better UX**: Explicit commands vs. implicit skill triggering for utilities
- **Consistency**: Shared validation logic across all skills
- **Automation**: Hooks prevent errors before they happen
- **Clarity**: Right tool for the job (data access = MCP, knowledge = skill)

### For Developers
- **DRY**: No duplicated repo detection, validation logic
- **Maintainability**: Single source of truth for shared patterns
- **Extensibility**: Easy to add new skills using shared utilities
- **Standards**: Enforced via hooks and validation commands

### For Repository
- **Architecture**: Clear separation of concerns (data, knowledge, automation)
- **Scalability**: Shared utils make adding new skills easier
- **Quality**: Automated validation and version sync
- **Flexibility**: Users can choose extension type that fits their needs

## User Decisions (Captured)

Based on clarification questions, the following approach is confirmed:

1. **Shared utilities**: ✅ Python package in `utils/` directory
   - Use PEP 723 relative imports for skill scripts
   - Single source of truth for common patterns
   - Clean architecture, DRY principles

2. **OmniFocus MCP server**: ✅ Medium priority - Phase 2
   - Focus on foundation (shared utils, commands, hooks) first
   - OmniFocus MCP extraction after foundation is stable
   - More cautious, phased approach

3. **Automation approach**: ✅ Both hooks AND commands
   - Pre-commit hooks for automatic enforcement
   - Manual commands for development/debugging
   - Maximum flexibility, best of both worlds

4. **Agent migration**: ✅ High interest - design for future
   - Plan shared utils and commands to facilitate agent migration
   - Design with agent patterns in mind (autonomous, orchestration-ready)
   - When agents become available, smooth transition path

5. **Scope**: Multiple GitHub Issues (one per phase)
   - Phase 1: Shared utilities + commands + hooks (Foundation)
   - Phase 2: OmniFocus MCP server (Architecture evolution)
   - Phase 3: Agent migration when available (Future evolution)

## Implementation Plan Summary

### Immediate Next Steps (After Plan Approval)

#### 1. Create GitHub Issue for Phase 1
```bash
gh issue create \
  --title "claude-mp: Extract shared utilities and create foundation" \
  --body "**Goal**: Create shared Python package, commands, and hooks

**Plan**: See docs/plans/2026-01-18-extension-evolution.md (this plan)

**Phase**: 1 of 3 (Foundation)

**Tasks**:
- [ ] Create utils/ Python package with repo, validation, templates, marketplace modules
- [ ] Update skills to use shared utils (skillsmith, marketplace-manager, skill-planner)
- [ ] Create commands: /validate-skill, /sync-versions, /init-skill
- [ ] Add pre-commit hooks: version sync, IMPROVEMENT_PLAN.md validation
- [ ] Add post-commit hook: GitHub issue checkbox sync
- [ ] Write documentation: migration guide, command usage
- [ ] Update README.md and WORKFLOW.md

**Related Skills**: skillsmith, marketplace-manager, skill-planner
**Estimated Effort**: 3-4 days
" \
  --assignee @me
```

#### 2. Update IMPROVEMENT_PLAN.md
Add to Planned table (repository-level or create one):
```markdown
| Issue | Priority | Title | Status |
|-------|----------|-------|--------|
| #XXX  | High     | Extract shared utilities and create foundation | Open |
```

#### 3. Implement Phase 1
Follow the detailed Phase 1 plan above:
- Create utils package
- Update skills
- Create commands
- Add hooks
- Document

#### 4. Create Lesson Document
After Phase 1 completion:
```markdown
docs/lessons/shared-utils-extraction.md
- What patterns were extracted
- Migration challenges and solutions
- Performance impact
- Agent-readiness design decisions
```

#### 5. Create Phase 2 Issue
After Phase 1 success, create OmniFocus MCP server issue following same pattern.

### Long-Term Roadmap

**Q1 2026**: Phase 1 complete (shared utils, commands, hooks)
**Q2 2026**: Phase 2 complete (OmniFocus MCP server)
**Future**: Phase 3 when agents available (skillsmith, skill-planner migration)

### Success Metrics

**Phase 1:**
- Zero duplicated utils code across skills
- All validation uses shared framework
- Pre-commit hooks prevent version drift
- Commands provide explicit access to utilities

**Phase 2:**
- OmniFocus data access cleanly separated from knowledge
- MCP server performs well (JXA response times acceptable)
- omnifocus-manager skill focuses purely on GTD guidance

**Phase 3:**
- Agents handle complex multi-step workflows autonomously
- Skills provide fallback for simple cases
- State management works reliably

## Files Reviewed

- `/WORKFLOW.md` - GitHub Issues workflow, IMPROVEMENT_PLAN.md format
- `skills/skillsmith/scripts/evaluate_skill.py` - Validation framework
- `skills/skillsmith/scripts/utils.py` - Shared utility patterns
- `skills/marketplace-manager/scripts/sync_marketplace_versions.py` - Version sync
- `skills/omnifocus-manager/SKILL.md` - Complex skill example
- `.claude-plugin/marketplace.json` - Plugin distribution format

## Conclusion

The claude-mp repository has matured to the point where:
- **Repeatable patterns** justify extraction (repo detection, validation, templates)
- **Functionality mismatch** suggests evolution (OmniFocus queries → MCP server)
- **Meta-patterns** indicate agent-like behavior (skillsmith, skill-planner)
- **Automation opportunities** exist (hooks for version sync, validation)

The recommendations balance:
- **DRY principles** (shared utilities)
- **Separation of concerns** (data access vs knowledge)
- **User experience** (explicit commands, automatic hooks)
- **Future evolution** (skills → agents when available)

This is a natural evolution, not a rewrite. Each phase builds on existing patterns while improving architecture.
