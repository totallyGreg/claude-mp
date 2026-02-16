---
title: "feat: Vault-Curator CLI Intelligence Workflows"
type: feat
date: 2026-02-15
brainstorm: docs/brainstorms/2026-02-15-pkm-plugin-cli-integration-brainstorm.md
---

# feat: Vault-Curator CLI Intelligence Workflows

## Overview

Enhance vault-curator with four new workflow families (Consolidation, Discovery, Visualization, Metadata) powered by the now-installed obsidian-skills plugins (`obsidian-cli`, `obsidian-markdown`, `obsidian-bases`, `json-canvas`, `defuddle`) and safety layer (`obsidian-official-cli-skills`). Build opinionated workflows on top of these low-level tools while keeping the existing dual-skill architecture.

## Problem Statement / Motivation

The pkm-plugin has vault-architect (creating structures) and vault-curator (evolving content), but vault-curator currently only handles meeting extraction, migrations, and basic pattern detection via Python scripts. With 7162+ notes, the vault needs:

- **Intelligence**: Find duplicates, suggest consolidations, surface related notes
- **Visibility**: Generate canvas maps for "big picture" understanding
- **Metadata hygiene**: Detect missing properties, suggest improvements
- **Safety**: All operations scoped to subdirectories with dry-run and rollback

The official obsidian-skills plugins are now installed as separate plugins, eliminating the need to fork or adopt them into pkm-plugin. The focus is purely on building workflows.

## Proposed Solution

### Architecture: Agent-Orchestrated CLI Commands

**Key architectural decision**: The pkm-manager agent already has `Bash` in its tools. It can invoke `obsidian` CLI commands directly. The installed obsidian-cli skills (kepano's + jackal's safety layer) provide guidance on safe CLI usage. No cross-plugin import mechanism is needed -- Claude Code loads all installed skills and the agent can reference them naturally.

**Script strategy**: Stay with Python/PEP 723 for custom logic that CLI commands can't handle (similarity scoring, merge operations). Defer TypeScript migration -- the CLI handles most data gathering, and Python handles the processing. Only add TypeScript if a workflow genuinely requires it.

**Invocation pattern**:
```
User request → pkm-manager agent
  → Loads vault-curator SKILL.md (workflows)
  → Uses obsidian-cli skill guidance (safe CLI usage)
  → Runs CLI commands via Bash (search, properties, tags)
  → Runs Python scripts via uv for complex logic
  → Uses obsidian-bases/json-canvas knowledge for file creation
  → Presents results, gets confirmation, executes
```

### Scope Selection Pattern (Cross-Cutting)

All new workflows start with scope selection:

```
1. Agent runs: obsidian search --vault $VAULT_PATH --format json (or tree -L 2 -d $VAULT_PATH)
2. Agent presents top-level directories via AskUserQuestion
3. User selects scope (or types a path)
4. Agent scopes all subsequent operations to selected path
5. Session remembers last scope for follow-up operations
```

**Edge cases**:
- Empty scope (no markdown files) → inform user, suggest broadening
- User says "whole vault" → warn about 7K+ files, require explicit confirmation
- Quick path: if user mentions specific topic ("my Docker notes"), agent can pre-filter

### Workflow Organization in SKILL.md

Reorganize vault-curator SKILL.md by workflow type:

```markdown
# Vault Curator

## Scope Selection (first 30 lines - all workflows use this)

## Core Principles (existing, moved up)

## Migration Workflows (existing content, reorganized)

## Metadata Workflows (new - least destructive, implement first)

## Consolidation Workflows (new - most complex)

## Discovery Workflows (new - builds on consolidation)

## Visualization Workflows (new - generates canvas maps)
```

## Technical Approach

### Phase 1: Foundation + Metadata Workflows (v1.1.0 → v1.2.0)

Metadata workflows are the **least destructive** entry point -- they read vault state and suggest changes (frontmatter only). This validates the CLI integration and scope selection patterns.

#### 1a. Add Scope Selection to vault-curator SKILL.md

- [ ] Add "Scope Selection" section at top of SKILL.md (lines 11-40)
- [ ] Document the `obsidian search` and `tree` patterns
- [ ] Include AskUserQuestion interaction model
- [ ] Handle edge cases (empty scope, whole vault warning)

**Files**: `plugins/pkm-plugin/skills/vault-curator/SKILL.md`

#### 1b. Implement Metadata Workflows

**Capabilities**:
- **Property Suggestions**: Scan sibling notes (same fileClass/folder), find common properties this note is missing
- **Schema Validation**: Use `detect_schema_drift.py` (existing, needs implementation) enhanced with CLI property queries
- **Property Gap Report**: "Meeting notes typically have scope, attendees, type -- this note is missing scope"

**Implementation**:
- Use CLI: `obsidian properties get --vault $VAULT_PATH --format json` to gather property data
- Use Python script `suggest_properties.py` for gap analysis logic
- Present suggestions via agent, apply with confirmation

**Files**:
- `plugins/pkm-plugin/skills/vault-curator/SKILL.md` (add Metadata Workflows section)
- `plugins/pkm-plugin/skills/vault-curator/scripts/suggest_properties.py` (new)
- `plugins/pkm-plugin/skills/vault-curator/scripts/detect_schema_drift.py` (implement, was placeholder)

#### 1c. Update pkm-manager Agent

- [ ] Add references to obsidian-cli safe usage patterns
- [ ] Add Metadata workflow routing
- [ ] Add scope selection as initial step for new workflows
- [ ] Update trigger phrases in vault-curator description

**Files**: `plugins/pkm-plugin/agents/pkm-manager.md`

### Phase 2: Consolidation Workflows (v1.2.0 → v1.3.0)

The most complex and destructive workflow. Requires a documented merge protocol.

#### 2a. Create Consolidation Protocol Reference

Before writing code, document the merge specification:

- **Duplicate detection**: Tiered approach
  - Tier 1: Identical titles (after normalization) → "likely duplicates"
  - Tier 2: >80% title similarity OR identical tags + same folder → "possible duplicates"
  - Tier 3: Agent reads top candidates and judges similarity (LLM-powered)
- **Merge actions**: Per-group selection
  - **Merge content**: Surviving note gets union of frontmatter, concatenated body with separator
  - **Create MOC**: New note linking both, placed in same directory
  - **Mark aliases**: Add to Obsidian `aliases` field on both notes
  - **Skip**: Leave as-is
- **Link redirect**: Vault-wide search for `[[deleted-note]]` → `[[surviving-note]]` with confirmation
- **Rollback**: Git commit before operation, reverse script available

**Files**: `plugins/pkm-plugin/skills/vault-curator/references/consolidation-protocol.md` (new)

#### 2b. Implement Duplicate Detection

- [ ] Script `find_similar_notes.py`: Takes scope path, returns groups with similarity scores
- [ ] Uses CLI search + property queries for data gathering
- [ ] Tiered detection (title similarity → metadata overlap → LLM judgment)
- [ ] Performance: O(n) title scan, O(n) property scan, O(k) LLM reads (top-k candidates only)
- [ ] Cap results at 20 groups per run to avoid overwhelming user

**Files**:
- `plugins/pkm-plugin/skills/vault-curator/scripts/find_similar_notes.py` (new)

#### 2c. Implement Merge Operations

- [ ] Script `merge_notes.py`: Takes two note paths + merge strategy, produces merged note
- [ ] Frontmatter merge: union of properties, user-prompted for conflicts
- [ ] Content merge: concatenate with `---` separator and source headers
- [ ] Link redirect: separate script `redirect_links.py` for vault-wide wikilink replacement
- [ ] All operations have `--dry-run` mode

**Files**:
- `plugins/pkm-plugin/skills/vault-curator/scripts/merge_notes.py` (new)
- `plugins/pkm-plugin/skills/vault-curator/scripts/redirect_links.py` (new)

#### 2d. Add Consolidation Workflows to SKILL.md

- [ ] Document the full consolidation workflow
- [ ] Reference the protocol document
- [ ] Include safety checks and confirmation steps
- [ ] Add trigger phrases to description

**Files**: `plugins/pkm-plugin/skills/vault-curator/SKILL.md`

### Phase 3: Discovery Workflows (v1.3.0 → v1.4.0)

Builds on the analysis capabilities from Phase 2.

#### 3a. Related Note Finding

- Use CLI search + property queries to find notes sharing tags, properties, or links with a given note
- Rank by connection strength (shared properties weighted > shared tags > folder proximity)
- Present top 10 with explanations
- Offer to add wikilinks to related notes

**Implementation**: Primarily agent-orchestrated CLI commands. Python script `find_related.py` only if ranking logic is complex enough to warrant it.

**Files**:
- `plugins/pkm-plugin/skills/vault-curator/SKILL.md` (add Discovery Workflows section)
- `plugins/pkm-plugin/skills/vault-curator/scripts/find_related.py` (new, if needed)

#### 3b. Progressive Discovery Views

- Generate Bases views that show notes organized by depth/type
- Entry points (MOCs, overviews) → Detailed notes → Raw captures
- Use property-based hierarchy: `noteType` or `fileClass` determines tier
- Create Bases `.base` files using obsidian-bases skill knowledge

**Files**:
- `plugins/pkm-plugin/skills/vault-curator/SKILL.md`
- Generated `.base` files in user's vault (not committed)

### Phase 4: Visualization Workflows (v1.4.0 → v1.5.0)

#### 4a. Canvas Map Generation

- Generate JSON Canvas files showing note relationships within a scope
- Use json-canvas skill format knowledge for correct file structure
- Layout: Simple grid or tree layout (agent calculates positions)
- Cap at **50 nodes** per canvas; cluster into groups if more
- Naming: `_knowledge-map-YYYY-MM-DD.canvas` in scoped directory

**Edge cases**:
- Canvas already exists → append date suffix or offer to overwrite
- Zero relationships → inform user, suggest broadening scope
- >50 nodes → create hierarchical view (clusters as group nodes)

**Files**:
- `plugins/pkm-plugin/skills/vault-curator/SKILL.md` (add Visualization Workflows section)
- `plugins/pkm-plugin/skills/vault-curator/scripts/generate_canvas.py` (new)

## Acceptance Criteria

### Functional Requirements

- [ ] Scope selection works consistently across all four workflow types
- [ ] Metadata workflow: suggests missing properties based on peer note analysis
- [ ] Consolidation workflow: detects duplicates, presents merge options, executes with confirmation
- [ ] Discovery workflow: finds related notes and suggests links
- [ ] Visualization workflow: generates readable canvas maps within 50-node limit
- [ ] All destructive operations have dry-run mode
- [ ] All bulk operations create git commit before execution (if git repo)

### Non-Functional Requirements

- [ ] Operations on 500-file subdirectory complete in <30 seconds
- [ ] SKILL.md stays under 500 lines (detailed content in references/)
- [ ] Scope selection section appears in first 40 lines of SKILL.md
- [ ] All new scripts follow PEP 723 pattern with path validation

### Quality Gates

- [ ] Each phase has a separate GitHub Issue
- [ ] IMPROVEMENT_PLAN.md updated after each phase
- [ ] Post-commit verification: run affected scripts on test data
- [ ] pkm-manager agent correctly routes to new workflows

## Dependencies & Risks

### Dependencies

| Dependency | Status | Impact |
|-----------|--------|--------|
| obsidian-skills plugin (kepano) | Installed | Provides obsidian-markdown, obsidian-bases, json-canvas, defuddle, obsidian-cli skills |
| obsidian-official-cli-skills (jackal) | Installed | Provides CLI safety gotchas |
| Obsidian CLI 1.12+ | Required on user machine | Check version at workflow start |
| Python 3.11+ / uv | Required | Existing dependency |

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| CLI commands insufficient for workflows | Medium | Would need more Python scripts | Start with CLI, add scripts as needed |
| Merge operations cause data loss | Low (with safeguards) | High | Dry-run + git commit + confirmation |
| SKILL.md exceeds 500 lines | Medium | Reduced agent performance | Move details to references/ |
| Scope selection UX is clunky | Medium | Poor user experience | Test with real vault early |

## Open Questions Resolved

From the brainstorm's 10 open questions, resolved for this plan:

| # | Question | Resolution |
|---|----------|------------|
| 1 | Obsidian API access outside plugin? | Not needed. CLI commands handle data gathering. |
| 2 | Canvas generation approach? | Hybrid: CLI for analysis, json-canvas skill knowledge for file creation, Python for layout. |
| 3 | Duplicate detection algorithm? | Tiered: title similarity → metadata overlap → LLM judgment. See Phase 2a. |
| 4 | Script distribution? | Python/PEP 723. No TypeScript build system. Deferred. |
| 5 | Progressive discovery hierarchy? | Property-based (`noteType`/`fileClass` determines tier). |
| 6 | Automatic linking rules? | Shared properties (most precise), user defines additional via Bases formulas. |
| 7 | Consolidation actions? | Four options per group: merge, MOC, alias, skip. See Phase 2a. |
| 8 | Python → TypeScript migration? | Deferred. Stay Python. CLI handles most data gathering. |
| 9 | Backwards compatibility? | Yes, existing Python scripts remain. New scripts added alongside. |
| 10 | Testing strategy? | Dry-run mode on real vault + fixture-based pytest for scripts. |

## Success Metrics

1. Can consolidate a 200-file subdirectory in one session (scope → detect → merge → verify)
2. Metadata suggestions surface genuinely missing properties (not noise)
3. Canvas maps are readable and useful (not walls of unconnected nodes)
4. Zero data loss incidents (dry-run + git commit + confirmation)

## References & Research

### Internal References
- Brainstorm: `docs/brainstorms/2026-02-15-pkm-plugin-cli-integration-brainstorm.md`
- Current vault-curator: `plugins/pkm-plugin/skills/vault-curator/SKILL.md`
- Agent: `plugins/pkm-plugin/agents/pkm-manager.md`
- Architecture lessons: `docs/lessons/plugin-integration-and-architecture.md`
- Skill refinement lessons: `docs/lessons/omnifocus-manager-refinement-2026-01-18.md`
- IMPROVEMENT_PLAN conventions: `docs/lessons/improvement-plan-migration.md`

### External References
- Obsidian CLI docs: Obsidian 1.12+ CLI reference
- kepano/obsidian-skills: Installed at `~/.claude/plugins/cache/obsidian-skills/`
- jackal092927/obsidian-official-cli-skills: Installed at `~/.claude/plugins/cache/obsidian-official-cli-skills/`

### Installed Obsidian Skills (Available to Agent)
- `obsidian:obsidian-cli` - CLI commands for search, properties, tags, tasks
- `obsidian:obsidian-markdown` - Obsidian-flavored markdown (wikilinks, callouts, embeds)
- `obsidian:obsidian-bases` - Database-like views with filters and formulas
- `obsidian:json-canvas` - JSON Canvas file format for visual maps
- `obsidian:defuddle` - Clean markdown extraction from web pages
- `obsidian-cli:obsidian-cli` - 13 documented silent failure gotchas for safe CLI usage
