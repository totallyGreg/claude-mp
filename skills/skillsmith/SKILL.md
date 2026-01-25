---
name: skillsmith
description: Guide for creating and improving effective skills. This skill should be used when users want to create, update, or improve skills that extend Claude's capabilities with specialized knowledge, workflows, or tool integrations.
metadata:
  author: J. Greg Williams
  version: "3.4.0"
compatibility: Requires python3 and uv for script execution and validation
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
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation intended to be loaded into context as needed
    └── assets/           - Files used in output (templates, icons, fonts, etc.)
```

**Specification Compliance:** Skills must follow the AgentSkills specification for structure, naming conventions, and metadata requirements. See `references/agentskills_specification.md` for complete specification details.

#### SKILL.md (required)

**Metadata Quality:** The `name` and `description` in YAML frontmatter determine when Claude will use the skill. Be specific about what the skill does and when to use it. Use the third-person (e.g. "This skill should be used when..." instead of "Use this skill when...").

**Specification Requirements:**
- `name`: 1-64 characters, lowercase alphanumeric and hyphens only, must match directory name
- `description`: Max 1024 characters, non-empty, describes what the skill does and when to use it
- Optional fields: `license`, `compatibility`, `metadata`, `allowed-tools`

For complete frontmatter requirements and examples, see `references/agentskills_specification.md`.

#### Bundled Resources (optional)

##### Scripts (`scripts/`)

Executable code (Python/Bash/etc.) for tasks that require deterministic reliability or are repeatedly rewritten.

- **When to include**: When the same code is being rewritten repeatedly or deterministic reliability is needed
- **Example**: `scripts/rotate_pdf.py` for PDF rotation tasks
- **Benefits**: Token efficient, deterministic, may be executed without loading into context
- **Note**: Scripts may still need to be read by Claude for patching or environment-specific adjustments
- **Python scripts**: MUST use PEP 723 inline metadata for uv execution. See `references/python_uv_guide.md` for details.

##### References (`references/`)

Documentation and reference material intended to be loaded as needed into context to inform Claude's process and thinking.

- **When to include**: For documentation that Claude should reference while working
- **Examples**: Example reference files might include financial schemas, NDA templates, company policies, API specifications, or database documentation (see `references/` for skillsmith's actual reference files)
- **Use cases**: Database schemas, API documentation, domain knowledge, company policies, detailed workflow guides
- **Benefits**: Keeps SKILL.md lean, loaded only when Claude determines it's needed
- **Best practice**: If files are large (>10k words), include grep search patterns in SKILL.md
- **Avoid duplication**: Information should live in either SKILL.md or references files, not both. Prefer references files for detailed information unless it's truly core to the skill—this keeps SKILL.md lean while making information discoverable without hogging the context window.
- **Reference Discovery**: Reference files should be mentioned contextually in SKILL.md where they're relevant (e.g., "See references for API documentation" or "See validation guide for detailed metrics")
- **Forms and Templates**: Skills that involve structured data collection should include `references/form_templates.md` with form templates

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

### Validation as a Core Workflow

Quality validation is embedded throughout the skill creation process:

- **During development**: Quick validation catches structural issues early
- **Before release**: Strict mode ensures no quality regressions
- **In CI/CD**: Automated gates prevent bad skills from being published

The validation workflow prevents issues from accumulating and ensures each skill meets AgentSkills specification.

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

**Examples:**

- `pdf-editor` skill: A script to eliminate re-writing rotation code for every query
- `frontend-webapp-builder` skill: An assets template to store boilerplate HTML/React for "Build me a todo app" type queries
- `big-query` skill: A reference file documenting schemas and table relationships instead of re-discovering them

(For detailed analysis patterns, see `references/improvement_workflow_guide.md`)

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

**Progressive Disclosure:** Keep SKILL.md lean (<500 lines). See `references/progressive_disclosure_discipline.md` before adding detailed content.

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

### Step 5: Validate the Skill

Once the skill is ready, validate it to ensure it meets all requirements:

```bash
uv run scripts/evaluate_skill.py <skill-path> --quick
```

The validation evaluates:
- YAML frontmatter format and required fields
- Character limits (name ≤64 chars, description ≤1024 chars)
- Naming conventions (lowercase-with-hyphens)
- Line/token budgets (SKILL.md <500 lines recommended)
- Description completeness and quality
- File organization and resource references
- AgentSkills specification compliance

If validation fails, the tool will report the errors. Fix any validation errors and run validation again.

#### Validation Gate: Strict vs Standard Mode

Validation provides two enforcement levels:

**Standard Mode (default):**
- Errors block skill completion (required fixes)
- Warnings are informational (recommended improvements)
- Developers can proceed despite warnings
- Use in: Development iterations

**Strict Mode (--strict flag):**
- Both errors AND warnings block skill completion
- Prevents quality regressions before release
- Designed for: Pre-release quality gates
- Prevents: Accidentally shipping low-quality documentation

Use strict mode when:
- Preparing release versions
- Running in CI/CD validation gates
- Quality expectations are high
- Before submission to marketplace

Example:
```bash
# Standard validation (warnings are OK)
uv run scripts/evaluate_skill.py skills/my-skill --quick

# Strict validation (warnings block completion)
uv run scripts/evaluate_skill.py skills/my-skill --quick --strict
```

For advanced validation options, see `references/validation_tools_guide.md`.

**Post-Validation Checklist:**

After validation passes:
- [ ] Test skill functionality end-to-end
- [ ] Verify bundled resources work correctly
- [ ] Update root README.md with skill version and changelog
- [ ] Optionally invoke marketplace-manager to publish skill

### Step 6: Iterate

After testing the skill, users may request improvements. Often this happens right after using the skill, with fresh context of how the skill performed.

**Iteration workflow:**
1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Identify how SKILL.md or bundled resources should be updated
4. Make improvements directly for simple changes
5. Run quick validation to verify no regressions: `uv run scripts/evaluate_skill.py <skill> --quick`
6. Before committing:
   - Run strict validation: `uv run scripts/evaluate_skill.py <skill> --quick --strict`
   - Fix any issues (errors or warnings in strict mode)
   - Re-run validation until all issues are resolved
7. Update the `metadata.version` field in YAML frontmatter:
   - **PATCH** (1.0.0 → 1.0.1): Bug fixes, documentation updates, minor improvements
   - **MINOR** (1.0.0 → 1.1.0): New features, new bundled resources, backward-compatible changes
   - **MAJOR** (1.0.0 → 2.0.0): Breaking changes, major rewrites, changed workflow
8. Test again and commit changes
9. Optionally sync to marketplace

**For complex improvements:**
- Use WORKFLOW.md pattern: Create GitHub Issue → Add to IMPROVEMENT_PLAN.md → Plan in docs/plans/
- See `references/improvement_workflow_guide.md` for detailed improvement workflows
- Research skill opportunities with `scripts/research_skill.py`

---

## Advanced Topics

For detailed guidance on specific topics, see these reference files:

- **`references/agentskills_specification.md`** - Complete AgentSkills specification, validation checklist, naming rules
- **`references/progressive_disclosure_discipline.md`** - Avoiding documentation bloat and maintaining lean SKILL.md
- **`references/python_uv_guide.md`** - Python scripts best practices with uv and PEP 723 inline metadata
- **`references/validation_tools_guide.md`** - Comprehensive documentation for evaluate_skill.py and research_skill.py
- **`references/improvement_workflow_guide.md`** - Detailed improvement routing logic and workflows
- **`references/reference_management_guide.md`** - Managing reference files and documentation
- **`references/improvement_plan_best_practices.md`** - Version history and planning documentation
- **`references/research_guide.md`** - Research phases, metrics interpretation, evaluation workflows
- **`references/integration_guide.md`** - Integration patterns with marketplace-manager
- **`references/FORMS.md`** - Form templates for structured data collection

For marketplace distribution, see the **marketplace-manager** skill.
