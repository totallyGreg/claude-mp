---
name: skillsmith
description: Guide for forging effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Claude's capabilities with specialized knowledge, workflows, or tool integrations.
metadata:
  author: J. Greg Williams
  version: "1.8.0"
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

To distribute skills via Claude Code plugin marketplace, use **marketplace-manager**:

```bash
# Add skill to marketplace
See marketplace-manager skill for complete workflow

# marketplace-manager handles:
- Adding skills to marketplace.json
- Version syncing
- Git integration
- Validation
```

For comprehensive marketplace documentation, see the **marketplace-manager** skill.

### Step 6: Iterate

After testing the skill, users may request improvements. Often this happens right after using the skill, with fresh context of how the skill performed.

**Iteration workflow:**
1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Use **skill-planner** for systematic improvements:
   - Research current state
   - Create improvement plan
   - Refine and approve plan
   - Implement approved changes
4. Update `metadata.version` in SKILL.md frontmatter (follow semantic versioning)
5. If published in marketplace, use **marketplace-manager** to sync versions

**Version Guidelines:**
- **MAJOR** (1.0.0 → 2.0.0): Breaking changes, major rewrites, changed workflow
- **MINOR** (1.0.0 → 1.1.0): New features, new bundled resources, backward-compatible changes
- **PATCH** (1.0.0 → 1.0.1): Bug fixes, documentation updates, minor improvements

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

**Validation tools:**
```bash
# Comprehensive evaluation with metrics and spec validation (recommended)
python3 scripts/evaluate_skill.py <skill-path>

# Deep multi-phase research analysis for improvement planning
python3 scripts/research_skill.py <skill-path>
```

For complete specification details, naming rules, and validation requirements, see `references/agentskills_specification.md`.

---

## Skill Evaluation & Analysis

skillsmith provides comprehensive evaluation and research capabilities to assess skills, verify improvements, and identify enhancement opportunities:

### evaluate_skill.py

Comprehensive skill evaluation combining metrics, spec validation, comparison, and functionality testing.

**Features:**
- **Baseline metrics** - Calculates all quality scores (conciseness, complexity, spec compliance, progressive disclosure)
- **Comparison mode** - Compare improved skill against original to verify improvements
- **Spec validation** - Complete AgentSkills specification compliance checking
- **Functionality testing** - Validates skill can be loaded, scripts are executable, references are readable
- **Metadata storage** - Optionally store metrics in SKILL.md frontmatter

**Usage:**
```bash
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

**When to use:**
- Before and after skill improvements to verify enhancements
- To validate AgentSkills specification compliance
- To get comprehensive quality assessment
- To compare different versions of a skill
- To test skill functionality and resource accessibility
- For quick quality checks or detailed analysis

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
