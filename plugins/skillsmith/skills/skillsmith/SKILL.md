---
name: skillsmith
description: This skill should be used when users ask to "create a skill", "validate a skill for quality", "evaluate skill improvements", "research skill opportunities", "analyze skill metrics", "improve skill quality", "init a new skill", "check skill compliance", or "sync skill to marketplace". Provides comprehensive skill development with automated validation, metrics tracking, and improvement workflows.
metadata:
  author: J. Greg Williams
  version: "5.0.0"
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

Create the skill by editing reusable resources (scripts, references, assets) and updating SKILL.md. Focus on information that would help another Claude instance execute tasks effectively. Use imperative form, keep SKILL.md lean (<500 lines), and follow AgentSkills specification requirements.

See `references/skill_creation_detailed_guide.md` for comprehensive editing guidance including writing style, progressive disclosure, and specification compliance.

### Step 5: Validate the Skill

Validate the completed skill using `evaluate_skill.py`:

```bash
# Quick validation (fast, structure-only) - use during development
uv run scripts/evaluate_skill.py <skill-path> --quick

# Strict validation (warnings as errors) - use before release
uv run scripts/evaluate_skill.py <skill-path> --quick --strict

# Full evaluation with metrics - use to assess quality
uv run scripts/evaluate_skill.py <skill-path>
```

**Validation modes:**
- **Quick** (`--quick`): Fast structural checks (frontmatter, naming, PEP 723)
- **Strict** (`--strict`): Treat warnings as errors (for pre-release gates)
- **Comprehensive** (no flags): Full metrics (conciseness, complexity, spec compliance)

See `references/validation_tools_guide.md` for complete command reference and workflow examples.

### Step 6: Iterate

After testing, improve the skill based on real-world usage. Follow the iteration workflow:
1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Identify improvements to SKILL.md or bundled resources
4. Run quick validation: `uv run scripts/evaluate_skill.py <skill> --quick`
5. Run strict validation before committing
6. Update version in SKILL.md metadata (PATCH/MINOR/MAJOR)
7. Test and commit

For complex improvements (>50 lines or architectural changes), follow WORKFLOW.md pattern with GitHub Issues.

See `references/skill_creation_detailed_guide.md` for detailed iteration workflow and complexity decision criteria.

---

## Common Mistakes to Avoid

### Mistake 1: Weak Trigger Description

❌ **Bad:**
```yaml
description: Provides guidance for creating skills.
```

**Why bad:** Vague, no specific trigger phrases, not third-person format

✅ **Good:**
```yaml
description: This skill should be used when users ask to "create a skill", "validate a skill for quality", "evaluate skill improvements". Provides comprehensive skill development guidance.
```

**Why good:** Third-person format, specific trigger phrases, concrete scenarios

### Mistake 2: Bloated SKILL.md

❌ **Bad:** SKILL.md with 800+ lines containing all documentation

**Why bad:** Consumes context window every time skill triggers, detailed content always loaded

✅ **Good:** SKILL.md with 200-400 lines, detailed content in `references/`

**Why good:** Progressive disclosure - core essentials load immediately, details load as needed

### Mistake 3: Second-Person Writing

❌ **Bad:**
```markdown
You should start by understanding the skill requirements.
You need to validate your skill before release.
```

**Why bad:** Second-person style, not imperative form

✅ **Good:**
```markdown
Start by understanding the skill requirements.
Validate the skill before release.
```

**Why good:** Imperative form, direct instructions

### Mistake 4: Missing or Orphaned References

❌ **Bad:** Reference files exist in `references/` but aren't mentioned in SKILL.md

**Why bad:** Claude doesn't know the references exist or when to use them

✅ **Good:** Each reference file mentioned contextually where relevant in SKILL.md

**Why good:** Claude knows what references exist and when to load them

---

## Quick Reference: Skill Templates

### Minimal Skill (~50-100 lines)

```
skill-name/
├── SKILL.md
└── (no bundled resources)
```

**Frontmatter:**
```yaml
---
name: skill-name
description: This skill should be used when users ask to "do X", "perform Y".
metadata:
  version: "1.0.0"
---
```

**Use for:** Simple knowledge transfer, single-topic guidance, no complex workflows

### Standard Skill (~150-300 lines)

```
skill-name/
├── SKILL.md
├── references/
│   ├── detailed_guide.md
│   └── patterns.md
└── scripts/
    └── helper_script.py
```

**Frontmatter:**
```yaml
---
name: skill-name
description: This skill should be used when users ask to "create X", "configure Y", "validate Z".
metadata:
  version: "1.0.0"
compatibility: Requires python3 and uv for script execution
---
```

**Use for:** Most skills - workflows with 2-3 references and optional scripts

### Complete Skill (~250-400 lines)

```
skill-name/
├── SKILL.md
├── IMPROVEMENT_PLAN.md
├── references/
│   ├── specification.md
│   ├── detailed_guide.md
│   ├── patterns.md
│   └── advanced_topics.md
├── scripts/
│   ├── main_tool.py
│   └── helper.py
└── assets/
    └── templates/
```

**Frontmatter:**
```yaml
---
name: skill-name
description: This skill should be used when users ask to "create X", "validate Y", "improve Z", "analyze A", "export B".
metadata:
  version: "1.0.0"
  author: Author Name
compatibility: Requires python3 and uv for script execution
license: See LICENSE.txt
---
```

**Use for:** Complex domains with extensive documentation, tooling, and templates

---

## Advanced Topics

For detailed guidance on specific topics, see these reference files:

- **`references/agentskills_specification.md`** - Complete AgentSkills specification, validation checklist, naming rules
- **`references/skill_creation_detailed_guide.md`** - Detailed guidance for Steps 4-6 (editing, validation, iteration)
- **`references/progressive_disclosure_discipline.md`** - Avoiding documentation bloat and maintaining lean SKILL.md
- **`references/python_uv_guide.md`** - Python scripts best practices with uv and PEP 723 inline metadata
- **`references/validation_tools_guide.md`** - Comprehensive documentation for evaluate_skill.py and research_skill.py
- **`references/improvement_workflow_guide.md`** - Detailed improvement routing logic and workflows
- **`references/reference_management_guide.md`** - Managing reference files and documentation
- **`references/improvement_plan_best_practices.md`** - Version history and planning documentation
- **`references/research_guide.md`** - Research phases, metrics interpretation, evaluation workflows
- **`references/integration_guide.md`** - Integration patterns with marketplace-manager
- **`references/form_templates.md`** - Form templates for structured data collection

For marketplace distribution, see the **marketplace-manager** skill.

---

## Learn from Official Examples

Study these skills from the official **plugin-dev** toolkit as examples of best practices:

| Skill | Best Practice Example |
|-------|----------------------|
| **hook-development** | Excellent progressive disclosure - lean SKILL.md with 3 reference files, 3 examples, 3 scripts |
| **agent-development** | Strong trigger phrases, focused content (~1,438 words), complete agent examples |
| **plugin-settings** | Clear reference organization with real-world implementation examples |
| **command-development** | Specific trigger phrases demonstrating proper frontmatter patterns |
| **skill-development** | Comprehensive validation checklist and common mistakes documentation |

These official skills demonstrate the AgentSkills specification patterns that skillsmith automates and extends with metrics tracking.
