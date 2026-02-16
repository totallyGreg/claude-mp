---
date: 2026-02-15
topic: pkm-plugin-cli-integration
---

# PKM Plugin: Obsidian CLI Integration

## What We're Building

Enhance the pkm-plugin to leverage the official Obsidian CLI (1.12+) for intelligent vault operations while maintaining a clean separation between low-level tools and opinionated workflows.

**Core capabilities:**
- **Automatic linking**: Notes appear in relevant views based on shared metadata
- **Progressive discovery**: Visual hierarchy from entry points → detailed notes → raw captures
- **Consolidation prompts**: Detect similar/duplicate notes and suggest merging
- **Visual overviews**: Generate canvas maps for "big picture" understanding
- **Subdirectory-scoped operations**: Work on specific areas of a 7K+ note vault

## Why This Approach

### Separation of Concerns

Adopt official Obsidian skills as low-level tools:
- `obsidian-cli` (+ safety enhancements from jackal092927/obsidian-official-cli-skills)
- `obsidian-markdown`
- `obsidian-bases`
- `json-canvas`

Build opinionated workflows on top:
- **vault-architect**: Keep for Templater patterns and creating new structures
- **vault-curator**: Enhance with CLI-powered intelligence workflows
- **pkm-manager**: Orchestrate everything

### Why Not Create New Skills

The semantic mapping is clear:
- **Architect** = Creating new structure (templates, Bases, canvas)
- **Curator** = Evolving existing content (migrations, consolidation, discovery, visualization)

Adding intelligence/consolidation workflows to curator maintains this mental model while avoiding skill proliferation.

### Ecosystem Alignment

- **TypeScript scripts**: Align with Obsidian's JavaScript ecosystem
- **Obsidian API types**: Use official type definitions from obsidianmd/obsidian-api
- **Community tools**: Leverage kepano's maintained skills as foundation
- **Safety layer**: Encode jackal's CLI gotchas to avoid silent failures

## Key Decisions

### 1. Script Implementation: TypeScript

**Choice**: TypeScript with Obsidian API type definitions

**Rationale**:
- Full type safety catches errors at development time
- Better IDE support and autocomplete
- Aligns with Obsidian plugin development patterns
- Community familiarity (most plugins are TypeScript)

**Build approach**:
- Add `tsconfig.json` with Obsidian API types
- Compile to JavaScript for execution
- Scripts can be run via CLI or imported by plugins

### 2. Operation Scope: Interactive Selection

**Choice**: Show directory tree, user selects scope

**Workflow**:
```
User: "Help me consolidate my Docker notes"
Curator: Uses CLI to list vault directories
Curator: Presents interactive tree view
User: Selects /Areas/Technical/Docker/
Curator: Runs analysis/consolidation on just that subtree
```

**Rationale**:
- Large vault (7162 files) makes vault-wide operations risky
- User wants to work incrementally on subdirectories
- Interactive selection provides clarity and control
- Aligns with "behind confirmations" preference for bulk updates

**Implementation**:
- Use Obsidian CLI to traverse directory structure
- Present choices via AskUserQuestion tool
- Scope all subsequent operations to selected path
- Remember last selection for session continuity

### 3. Skill Organization: Workflow Sections

**Choice**: Organize vault-curator by workflow type

**Structure**:
```markdown
# Vault Curator

## Core Principles
(existing: evolution, validation, rollback, pattern recognition)

## Workflows

### Migration Workflows
(existing: frontmatter migrations, Dataview→Bases)

### Consolidation Workflows
(new: duplicate detection, similarity analysis, merge suggestions)

### Discovery Workflows
(new: progressive views, automatic linking, related note finding)

### Visualization Workflows
(new: canvas generation, knowledge graphs, MOC creation)

### Metadata Workflows
(new: property suggestions, formula insights, schema validation)
```

**Rationale**:
- Clear navigation: "I need to consolidate" → go to Consolidation section
- Workflow-oriented matches how users think about tasks
- Extensible: easy to add new workflow types
- Maintains existing Migration content while adding new capabilities

### 4. Official Skills Integration

**Adoption strategy**:
- Fork `obsidian-cli` skill from kepano/obsidian-skills
- Add safety enhancements from jackal092927/obsidian-official-cli-skills:
  - Warn about `tasks todo` → use `tasks all todo`
  - Warn about `tags counts` → use `tags all counts`
  - Always use `format=json` with validation
  - Add `silent` flag for non-interactive operations
- Adopt `obsidian-markdown`, `obsidian-bases`, `json-canvas` as-is
- Consider PRing safety improvements back to kepano

**vault-curator uses these tools via**:
- CLI commands for search, property queries, task management
- Markdown/Bases skills for file creation/editing
- Canvas skill for visualization generation

### 5. Vault-architect Preservation

**What stays in vault-architect**:
- Templater patterns and API reference
- Frontmatter schema design
- Bases query patterns (creation)
- Quick capture workflows
- New structure design

**What moves to vault-curator**:
- Analyzing existing structures
- Consolidating existing notes
- Improving existing metadata
- Visualizing existing relationships

**Clean boundary**: Architect = blank slate design, Curator = working with what exists

## Open Questions

### Technical Questions

1. **Obsidian API access**: Can TypeScript scripts access the full Obsidian API outside of a plugin context? Or do we need to wrap operations via CLI?

2. **Canvas generation**: What's the best approach?
   - Generate JSON directly (json-canvas skill)
   - Use Obsidian API to create canvas programmatically
   - Hybrid: analyze via CLI, generate via json-canvas skill

3. **Duplicate detection algorithm**: What makes notes "similar"?
   - Title similarity (Levenshtein distance?)
   - Content overlap (cosine similarity?)
   - Metadata matches (same tags/properties?)
   - Link graph proximity (connected to same notes?)
   - Combination heuristic?

4. **Script distribution**: Should TypeScript scripts be:
   - Compiled and committed (users run .js files)
   - Source-only (users must compile locally)
   - Both (committed .js with .ts sources for development)

### Workflow Questions

5. **Progressive discovery**: What does "entry point → detailed → raw" hierarchy look like in practice?
   - Is this folder-based? (MOCs/ → Notes/ → Captures/)
   - Property-based? (type=overview → type=detailed → type=capture)
   - Link-depth based? (0 hops → 1 hop → 2 hops from entry)

6. **Automatic linking**: When should notes automatically appear in views?
   - Shared tags only?
   - Shared properties (more precise)?
   - Content similarity (ML-based)?
   - User defines rules via Bases formulas?

7. **Consolidation workflow**: When duplicates are found, what actions are available?
   - Merge content (keep which version?)
   - Create parent MOC (link both)
   - Mark as aliases (same entity, different perspectives)
   - Delete one (move links to other)

### Migration Questions

8. **Python → TypeScript**: Which scripts to migrate first?
   - Start with most-used (analyze_vault.py?)
   - Start with simplest (validate_frontmatter.py?)
   - Migrate as workflows are added (on-demand)

9. **Backwards compatibility**: Should old Python scripts remain available during transition?

10. **Testing strategy**: How to test against user's 7K+ note vault safely?
    - Create test vault with similar structure?
    - Always run in --dry-run mode first?
    - Automated tests with fixture vaults?

## Next Steps

### Immediate (Foundation)

1. **Set up TypeScript build system**
   - Add tsconfig.json with Obsidian API types
   - Create build script (tsc)
   - Define output structure

2. **Fork and enhance obsidian-cli skill**
   - Clone from kepano/obsidian-skills
   - Integrate jackal's safety warnings
   - Test against CLI 1.12+
   - Document gotchas

3. **Adopt other official skills**
   - Add obsidian-markdown, obsidian-bases, json-canvas to plugin
   - Update pkm-manager agent to reference these skills
   - Test basic operations

### Phase 1 (Consolidation Workflows)

4. **Implement duplicate detection**
   - TypeScript script: find_duplicates.ts
   - Use CLI search + property queries
   - Interactive subdirectory selection
   - Present matches with similarity scores

5. **Add consolidation workflow to vault-curator**
   - Update SKILL.md with Consolidation Workflows section
   - Document merge strategies
   - Add confirmation prompts

6. **Create first canvas visualization**
   - Generate canvas showing duplicate clusters
   - Use json-canvas skill for file creation
   - Test with user's Docker notes subdirectory

### Phase 2 (Discovery Workflows)

7. **Implement progressive discovery**
   - Define hierarchy model (decide on Open Question #5)
   - Create discovery views using Bases
   - Generate "entry point" canvases

8. **Add automatic linking suggestions**
   - Analyze metadata patterns
   - Suggest tag/property additions
   - Create Bases formulas for automatic views

### Phase 3 (Migration & Polish)

9. **Migrate Python scripts to TypeScript**
   - Start with analyze_vault.py
   - Leverage Obsidian CLI for data gathering
   - Add type safety

10. **Update documentation**
    - Revise README with new capabilities
    - Update IMPROVEMENT_PLAN.md
    - Create user guide for new workflows

11. **Community contribution**
    - PR safety improvements to kepano/obsidian-skills
    - Share consolidation patterns
    - Document learnings

---

## Success Criteria

This enhancement succeeds when:

1. **Quick capture works** - Can write notes rapidly without organizational friction
2. **Everything is discoverable** - Any note is accessible through well-designed Bases views
3. **Mess becomes structure** - Consolidation workflows help organize 7K+ notes incrementally
4. **Big picture is visible** - Canvas visualizations provide overview of knowledge areas
5. **Patterns are simple** - Converged on ONE opinionated approach (metadata-driven, Bases-powered)
6. **CLI is safe** - No silent failures or gotchas due to encoded safety layer

---

## Implementation Philosophy

**Incremental & Scoped**
- Work on subdirectories, not entire vault
- Test on small areas first
- Always confirm before bulk operations

**TypeScript-Native**
- Align with Obsidian ecosystem
- Leverage official type definitions
- Type safety catches errors early

**Community-Aligned**
- Build on official skills (tools)
- Contribute improvements back
- Share opinionated workflows (but not as "the" way)

**Workflow-Oriented**
- Organize by user tasks, not technical capabilities
- Make common operations easy
- Progressive disclosure of complexity
