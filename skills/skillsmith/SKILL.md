---
name: skillsmith
description: Main actor for all skill-related operations including creation, improvement, and management. Intelligently routes requests - handling quick updates directly and delegating complex improvements to skill-planner. This skill should be used when users want to create, update, improve, or manage skills that extend Claude's capabilities with specialized knowledge, workflows, or tool integrations.
metadata:
  author: J. Greg Williams
  version: "2.1.1"
compatibility: Requires python3 for research and metrics scripts
license: Complete terms in LICENSE.txt
---

# Skillsmith

This skill provides guidance for forging effective skills.

## About Skills

Skills are modular, self-contained packages that extend Claude's capabilities by providing
specialized knowledge, workflows, and tools. Think of them as "onboarding guides" for specific
domains or tasks—they transform Claude from a general-purpose agent into a specialized agent
equipped with procedural knowledge that no model can fully possess.

### What Skills Provide

1. Specialized workflows - Multi-step procedures for specific domains
2. Tool integrations - Instructions for working with specific file formats or APIs
3. Domain expertise - Company-specific knowledge, schemas, business logic
4. Bundled resources - Scripts, references, and assets for complex and repetitive tasks

### Anatomy of a Skill

Every skill consists of a required SKILL.md file and optional bundled resources:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
├── IMPROVEMENT_PLAN.md (recommended)
│   └── Version history, planned improvements, and design decisions
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation intended to be loaded into context as needed
    └── assets/           - Files used in output (templates, icons, fonts, etc.)
```

**Specification Compliance:** Skills must follow the AgentSkills specification for structure, naming conventions, and metadata requirements. See `references/agentskills_specification.md` for complete specification details including validation requirements, naming rules, and progressive disclosure architecture.

#### SKILL.md (required)

**Metadata Quality:** The `name` and `description` in YAML frontmatter determine when Claude will use the skill. Be specific about what the skill does and when to use it. Use the third-person (e.g. "This skill should be used when..." instead of "Use this skill when...").

**Specification Requirements:**
- `name`: 1-64 characters, lowercase alphanumeric and hyphens only, must match directory name
- `description`: Max 1024 characters, non-empty, describes what the skill does and when to use it
- Optional fields: `license`, `compatibility`, `metadata`, `allowed-tools`

For complete frontmatter requirements and examples, see `references/agentskills_specification.md`.

#### IMPROVEMENT_PLAN.md (recommended)

Living document tracking skill evolution, version history, and future improvements.

- **When to include**: For all skills, especially those expected to evolve over time
- **Purpose**: Historical context, planning documentation, design decision rationale
- **Structure**:
  - Version history with dates and descriptions
  - Completed improvements with implementation details
  - Planned improvements organized by priority
  - Technical debt tracking
  - Enhancement requests from users
- **Benefits**:
  - Provides context for why changes were made
  - Helps future maintainers understand evolution
  - Central place for planning and tracking improvements
  - Captures institutional knowledge
- **Note**: Should be excluded from skill packaging (add to .skillignore) but committed to version control

#### Bundled Resources (optional)

##### Scripts (`scripts/`)

Executable code (Python/Bash/etc.) for tasks that require deterministic reliability or are repeatedly rewritten.

- **When to include**: When the same code is being rewritten repeatedly or deterministic reliability is needed
- **Example**: `scripts/rotate_pdf.py` for PDF rotation tasks
- **Benefits**: Token efficient, deterministic, may be executed without loading into context
- **Note**: Scripts may still need to be read by Claude for patching or environment-specific adjustments

##### References (`references/`)

Documentation and reference material intended to be loaded as needed into context to inform Claude's process and thinking.

- **When to include**: For documentation that Claude should reference while working
- **Examples**: `references/finance.md` for financial schemas, `references/mnda.md` for company NDA template, `references/policies.md` for company policies, `references/api_docs.md` for API specifications
- **Use cases**: Database schemas, API documentation, domain knowledge, company policies, detailed workflow guides
- **Benefits**: Keeps SKILL.md lean, loaded only when Claude determines it's needed
- **Best practice**: If files are large (>10k words), include grep search patterns in SKILL.md
- **Avoid duplication**: Information should live in either SKILL.md or references files, not both. Prefer references files for detailed information unless it's truly core to the skill—this keeps SKILL.md lean while making information discoverable without hogging the context window. Keep only essential procedural instructions and workflow guidance in SKILL.md; move detailed reference material, schemas, and examples to references files.
- **Reference Catalog**: Skills with 3+ reference files should include `references/REFERENCE.md` to index all references with metadata. This catalog is automatically maintained by skillsmith during quick update workflows.
- **Forms and Templates**: Skills that involve structured data collection should include `references/FORMS.md` with form templates.

##### Assets (`assets/`)

Files not intended to be loaded into context, but rather used within the output Claude produces.

- **When to include**: When the skill needs files that will be used in the final output
- **Examples**: `assets/logo.png` for brand assets, `assets/slides.pptx` for PowerPoint templates, `assets/frontend-template/` for HTML/React boilerplate, `assets/font.ttf` for typography
- **Use cases**: Templates, images, icons, boilerplate code, fonts, sample documents that get copied or modified
- **Benefits**: Separates output resources from documentation, enables Claude to use files without loading them into context

### Progressive Disclosure Design Principle

Skills use a three-level loading system to manage context efficiently:

1. **Metadata (name + description)** - Always in context (~100 words)
2. **SKILL.md body** - When skill triggers (<5k words)
3. **Bundled resources** - As needed by Claude (Unlimited*)

*Unlimited because scripts can be executed without reading into context window.

## Skill Improvement Routing

Skillsmith is the main entry point for all skill-related work and intelligently routes improvement requests based on complexity:

**Quick Updates** (Handled directly by Skillsmith):
- Adding reference files to `references/`
  - Automatically regenerates `references/REFERENCE.md` catalog
  - Validates reference structure and detects consolidation opportunities
  - Both reference file and updated catalog included in commit
- Updating SKILL.md documentation (< 50 line changes)
- Adding examples, clarifications, or fixing typos
- Minor script fixes (< 20 lines)
- Single file, single concern, low risk changes
- **Version**: Automatic PATCH bump (1.0.0 → 1.0.1)

**Complex Improvements** (Delegated to skill-planner):
- Restructuring SKILL.md sections (> 50 lines)
- Adding new scripts or significant script modifications
- Changing workflow procedures or processes
- Multi-file coordinated changes
- Breaking changes or major refactors
- **Version**: User selects MINOR (1.0.0 → 1.1.0) or MAJOR (1.0.0 → 2.0.0)

**Automatic Detection**:
Skillsmith analyzes requests based on:
- **File count**: 1 file = quick, 2+ files = likely complex
- **Line changes**: < 50 lines = quick, ≥ 50 lines = complex
- **Scope**: Documentation/references = quick, structure/workflow = complex
- **Impact**: Additive = quick, modifications = complex

**User Override**:
- Say "handle this quickly" or "quick update" to skip planning
- Say "use planning" or "create a plan" to force systematic planning

For detailed complexity classification criteria and integration patterns, see `references/integration_guide.md`.

## Skill Creation Process

To create a skill, follow the "Skill Creation Process" in order, skipping steps only if there is a clear reason why they are not applicable.

### Step 1: Understanding the Skill with Concrete Examples

Skip this step only when the skill's usage patterns are already clearly understood. It remains valuable even when working with an existing skill.

To create an effective skill, clearly understand concrete examples of how the skill will be used. This understanding can come from either direct user examples or generated examples that are validated with user feedback.

For example, when building an image-editor skill, relevant questions include:

- "What functionality should the image-editor skill support? Editing, rotating, anything else?"
- "Can you give some examples of how this skill would be used?"
- "I can imagine users asking for things like 'Remove the red-eye from this image' or 'Rotate this image'. Are there other ways you imagine this skill being used?"
- "What would a user say that should trigger this skill?"

To avoid overwhelming users, avoid asking too many questions in a single message. Start with the most important questions and follow up as needed for better effectiveness.

Conclude this step when there is a clear sense of the functionality the skill should support.

### Step 2: Planning the Reusable Skill Contents

To turn concrete examples into an effective skill, analyze each example by:

1. Considering how to execute on the example from scratch
2. Identifying what scripts, references, and assets would be helpful when executing these workflows repeatedly

Example: When building a `pdf-editor` skill to handle queries like "Help me rotate this PDF," the analysis shows:

1. Rotating a PDF requires re-writing the same code each time
2. A `scripts/rotate_pdf.py` script would be helpful to store in the skill

Example: When designing a `frontend-webapp-builder` skill for queries like "Build me a todo app" or "Build me a dashboard to track my steps," the analysis shows:

1. Writing a frontend webapp requires the same boilerplate HTML/React each time
2. An `assets/hello-world/` template containing the boilerplate HTML/React project files would be helpful to store in the skill

Example: When building a `big-query` skill to handle queries like "How many users have logged in today?" the analysis shows:

1. Querying BigQuery requires re-discovering the table schemas and relationships each time
2. A `references/schema.md` file documenting the table schemas would be helpful to store in the skill

To establish the skill's contents, analyze each concrete example to create a list of the reusable resources to include: scripts, references, and assets.

### Step 3: Initializing the Skill

At this point, it is time to actually create the skill.

Skip this step only if the skill being developed already exists, and iteration or packaging is needed. In this case, continue to the next step.

When creating a new skill from scratch, always run the `init_skill.py` script. The script conveniently generates a new template skill directory that automatically includes everything a skill requires, making the skill creation process much more efficient and reliable.

Usage:

```bash
scripts/init_skill.py <skill-name> --path <output-directory>
```

The script:

- Creates the skill directory at the specified path
- Generates a SKILL.md template with proper frontmatter and TODO placeholders
- Creates IMPROVEMENT_PLAN.md template for tracking skill evolution
- Creates example resource directories: `scripts/`, `references/`, and `assets/`
- Adds example files in each directory that can be customized or deleted

The initialization script also creates reference management files:

- `references/REFERENCE.md` - Catalog template (regenerate after adding references)
- `references/FORMS.md` - Form templates for structured data (customize for your domain)

After creating your skill and adding actual reference content, regenerate the catalog:

```bash
cd skills/your-skill
python3 ../skillsmith/scripts/update_references.py .
```

After initialization, customize or remove the generated SKILL.md and example files as needed.

### Step 4: Edit the Skill

When editing the (newly-generated or existing) skill, remember that the skill is being created for another instance of Claude to use. Focus on including information that would be beneficial and non-obvious to Claude. Consider what procedural knowledge, domain-specific details, or reusable assets would help another Claude instance execute these tasks more effectively.

#### Start with Reusable Skill Contents

To begin implementation, start with the reusable resources identified above: `scripts/`, `references/`, and `assets/` files. Note that this step may require user input. For example, when implementing a `brand-guidelines` skill, the user may need to provide brand assets or templates to store in `assets/`, or documentation to store in `references/`.

Also, delete any example files and directories not needed for the skill. The initialization script creates example files in `scripts/`, `references/`, and `assets/` to demonstrate structure, but most skills won't need all of them.

#### Update SKILL.md

**Writing Style:** Write the entire skill using **imperative/infinitive form** (verb-first instructions), not second person. Use objective, instructional language (e.g., "To accomplish X, do Y" rather than "You should do X" or "If you need to do X"). This maintains consistency and clarity for AI consumption.

**Specification Compliance:** Ensure the skill follows AgentSkills specification requirements:
- Verify frontmatter contains required `name` and `description` fields
- Confirm `name` follows naming conventions (lowercase, alphanumeric, hyphens only)
- Keep `description` under 1024 characters with clear triggering keywords
- Keep SKILL.md body under 500 lines (move detailed content to references/)
- Use relative paths for all file references
- Maintain one-level-deep reference chains

See `references/agentskills_specification.md` for complete validation requirements.

To complete SKILL.md, answer the following questions:

1. What is the purpose of the skill, in a few sentences?
2. When should the skill be used?
3. In practice, how should Claude use the skill? All reusable skill contents developed above should be referenced so that Claude knows how to use them.

### Step 5: Distribute via Marketplace (Optional)

To distribute skills via Claude Code plugin marketplace, Skillsmith delegates to **marketplace-manager**:

**Distribution workflow:**
1. Create or improve skill using Steps 1-4
2. Ready to distribute? Skillsmith calls marketplace-manager
3. marketplace-manager adds skill to marketplace.json (if new)
4. marketplace-manager syncs skill version to marketplace.json
5. marketplace-manager validates marketplace structure
6. Asks user: "Commit to marketplace?"
7. On approval, commits skill + marketplace.json together
8. Optionally pushes to remote repository

**marketplace-manager handles:**
- Adding skills to marketplace.json
- Automatic version syncing between SKILL.md and marketplace.json
- Git integration (commit and push operations)
- Marketplace validation
- Multi-component plugin versioning

For comprehensive marketplace documentation and manual operations, see the **marketplace-manager** skill.

### Step 6: Iterate

After testing the skill, users may request improvements. Skillsmith coordinates all improvement workflows, automatically routing based on complexity.

**Quick Update Workflow:**

For simple changes (adding references, documentation updates, minor fixes):

1. Skillsmith analyzes the request and determines it's quick
2. Reads current skill state to understand context
3. Makes the requested changes directly
4. Runs `evaluate_skill.py` to verify no regressions
5. Automatically bumps `metadata.version` to next PATCH (e.g., 1.0.0 → 1.0.1)
6. Calls **marketplace-manager** to sync marketplace.json
7. Asks user: "Commit these changes?"
8. On approval, marketplace-manager commits SKILL.md + marketplace.json
9. Asks user: "Push to remote?"

**Complex Improvement Workflow:**

For substantial changes (restructuring, new scripts, multi-file changes):

1. Skillsmith analyzes the request and determines it's complex
2. Informs user: "This requires systematic planning. Invoking skill-planner..."
3. Invokes **skill-planner** with improvement context
4. skill-planner executes complete workflow:
   - Research current state (using research_skill.py)
   - Create improvement plan (PLAN.md in git branch)
   - Refinement loop (user can iterate)
   - User approval (explicit approval gate)
   - Implementation (in plan branch)
5. skill-planner returns results to Skillsmith
6. Skillsmith asks user: "Version bump? MINOR (new feature) or MAJOR (breaking)?"
7. Updates `metadata.version` based on user selection
8. Calls **marketplace-manager** to sync and commit to plan branch
9. User manually tests and merges plan branch to main
10. skill-planner detects merge and archives completed plan

**Explicit Planning Request:**

If user says "create a plan for..." or "use planning", Skillsmith immediately invokes skill-planner regardless of complexity.

**Version Guidelines:**
- **MAJOR** (1.0.0 → 2.0.0): Breaking changes, major rewrites, changed workflow
- **MINOR** (1.0.0 → 1.1.0): New features, new bundled resources, backward-compatible changes
- **PATCH** (1.0.0 → 1.0.1): Bug fixes, documentation updates, minor improvements (auto-applied for quick updates)

---

## Specification Validation

Ensure skills comply with the AgentSkills specification before distribution or after major updates.

**Validation checklist:**

1. **Frontmatter compliance:**
   - `name` field present (1-64 chars, lowercase alphanumeric + hyphens)
   - `name` matches directory name
   - `description` field present (max 1024 chars, non-empty)
   - `description` uses third-person and includes triggering keywords
   - Optional fields properly formatted: `license`, `compatibility`, `metadata`

2. **Structure compliance:**
   - SKILL.md exists at skill root
   - Directory follows naming conventions (lowercase, hyphens only)
   - Supporting directories use correct names: `scripts/`, `references/`, `assets/`
   - File references use relative paths
   - Reference chains remain one-level deep

3. **Progressive disclosure:**
   - SKILL.md body under 500 lines
   - Detailed content moved to references/
   - Metadata (~100 tokens) provides clear skill purpose
   - Instructions (<5000 tokens) provide actionable guidance

4. **Content quality:**
   - Writing uses imperative/infinitive form
   - Instructions are clear and actionable
   - Examples demonstrate concrete usage
   - Bundled resources are properly referenced

5. **Reference organization:**
   - references/ directory uses one-level depth (no nested subdirectories)
   - REFERENCE.md catalog exists if skill has 3+ references
   - Catalog is up-to-date (includes all reference files)
   - No duplicate or overlapping reference content detected
   - FORMS.md included if skill uses structured data collection

**Validation tools:**
```bash
# Comprehensive evaluation with metrics and spec validation (recommended)
python3 scripts/evaluate_skill.py <skill-path>

# Deep multi-phase research analysis for improvement planning
python3 scripts/research_skill.py <skill-path>
```

For complete specification details, naming rules, and validation requirements, see `references/agentskills_specification.md`.

---

## Reference Management

Skillsmith provides automated reference catalog management for skills with multiple reference documents.

**Quick Start:**
```bash
# Generate or update catalog
python3 scripts/update_references.py .

# Detect consolidation opportunities
python3 scripts/update_references.py . --detect-duplicates

# Validate reference structure
python3 scripts/update_references.py . --validate-structure
```

**Key Features:**
- Automatic `REFERENCE.md` catalog generation with metadata
- Consolidation detection for duplicate/overlapping references
- Structure validation against AgentSkills spec
- Automatic catalog updates during quick update workflows

For detailed documentation on catalog structure, usage patterns, command reference, and advanced features, see `references/reference_management_guide.md`.

---

## Skill Evaluation & Analysis

skillsmith provides comprehensive evaluation and research capabilities to assess skills, verify improvements, and identify enhancement opportunities:

### evaluate_skill.py

Unified skill validation and evaluation tool with two modes: **quick validation** (fast, structure-only) and **comprehensive evaluation** (metrics, spec validation, comparison, functionality testing).

**Features:**
- **Quick validation mode** - Fast structural validation for pre-commit hooks and CI/CD (replaces quick_validate.py)
- **Baseline metrics** - Calculates all quality scores (conciseness, complexity, spec compliance, progressive disclosure)
- **Comparison mode** - Compare improved skill against original to verify improvements
- **Spec validation** - Complete AgentSkills specification compliance checking
- **Functionality testing** - Validates skill can be loaded, scripts are executable, references are readable
- **Metadata storage** - Optionally store metrics in SKILL.md frontmatter

**Usage:**
```bash
# Quick validation (fast, structure-only - for pre-commit hooks, CI/CD)
python3 scripts/evaluate_skill.py <skill-path> --quick
python3 scripts/evaluate_skill.py <skill-path> --quick --check-improvement-plan

# Basic evaluation with metrics and spec validation
python3 scripts/evaluate_skill.py <skill-path>

# Compare improved vs original skill
python3 scripts/evaluate_skill.py <skill-path> --compare <original-path>

# With functionality validation
python3 scripts/evaluate_skill.py <skill-path> --validate-functionality

# Store metrics in SKILL.md metadata
python3 scripts/evaluate_skill.py <skill-path> --store-metrics

# Full evaluation with all options and JSON output
python3 scripts/evaluate_skill.py <skill-path> --compare <original-path> --validate-functionality --format json

# Save results to file
python3 scripts/evaluate_skill.py <skill-path> --output results.json
```

**When to use quick mode (`--quick`):**
- Pre-commit hooks and CI/CD validation gates
- Quick sanity checks during development
- Validating IMPROVEMENT_PLAN.md completeness before release
- Fast structural validation only (no metrics calculation)

**When to use comprehensive mode (default):**
- Before and after skill improvements to verify enhancements
- To validate AgentSkills specification compliance
- To get comprehensive quality assessment
- To compare different versions of a skill
- To test skill functionality and resource accessibility
- For detailed quality analysis and metrics

**Note:** `scripts/quick_validate.py` provides basic SKILL.md validation only (upstream compatible with Anthropic skill-creator). For enhanced validation including IMPROVEMENT_PLAN checking, use `evaluate_skill.py --quick --check-improvement-plan`.

### research_skill.py

Deep multi-phase research analysis to understand skills and identify improvement opportunities.

**Features:**
- 7-phase research workflow (intent, domain, best practices, similar skills, implementation, compliance, recommendations)
- Identifies strengths, weaknesses, and opportunities
- Domain classification and complexity assessment
- Integration with skill-planner for systematic improvements

**Usage:**
```bash
# Full research analysis
python3 scripts/research_skill.py <skill-path>

# Save research to file
python3 scripts/research_skill.py <skill-path> --output research.json
```

**When to use:**
- Planning major skill improvements
- Understanding unfamiliar skills
- Identifying refactoring opportunities
- Preparing for skill-planner workflow

For comprehensive documentation on research phases, metrics interpretation, evaluation workflows, and best practices, see `references/research_guide.md`.
