---
name: skillsmith
description: Guide for forging effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Claude's capabilities with specialized knowledge, workflows, or tool integrations.
metadata:
  version: "1.6.0"
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

#### SKILL.md (required)

**Metadata Quality:** The `name` and `description` in YAML frontmatter determine when Claude will use the skill. Be specific about what the skill does and when to use it. Use the third-person (e.g. "This skill should be used when..." instead of "Use this skill when...").

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

## Skill Research & Analysis

skillsmith provides deep research capabilities to understand skills and identify improvement opportunities. This research integrates with skill-planner for systematic skill improvement workflows.

### Research Capabilities

The research system conducts a multi-phase analysis to understand what a skill does, how well it's implemented, and how it can be improved.

**Available Research Phases:**

1. **Understand Intent** - Extract skill purpose, description, and usage patterns
2. **Identify Domain & Complexity** - Classify domain and assess complexity level
3. **Research Best Practices** - Identify domain-specific patterns (future enhancement)
4. **Find Similar Skills** - Learn from examples in repository (future enhancement)
5. **Analyze Implementation** - Calculate quality metrics and identify issues
6. **Check Spec Compliance** - Validate against Agent Skills specification
7. **Synthesize Findings** - Consolidate into prioritized recommendations (future enhancement)

### Quality Metrics

skillsmith calculates objective quality metrics for any skill:

**Conciseness Score (0-100)**
- Evaluates line count vs guidelines (500 max, 300 recommended)
- Evaluates token count vs guidelines (2000 max)
- Higher score = more concise

**Complexity Score (0-100)**
- Analyzes heading structure and nesting depth
- Counts sections and code blocks
- Higher score = simpler, clearer structure

**Spec Compliance Score (0-100)**
- Validates required frontmatter fields (name, description)
- Checks recommended fields (metadata, compatibility, license)
- Identifies violations and warnings
- Higher score = better adherence to Agent Skills spec

**Progressive Disclosure Score (0-100)**
- Evaluates proper use of bundled resources (scripts, references, assets)
- Checks for appropriate content separation
- Higher score = better information architecture

**Overall Score (0-100)**
- Weighted average of all metrics
- Provides single quality indicator

### Running Research

To analyze a skill:

```bash
python3 scripts/research_skill.py <skill-path> [--output research.json]
```

**Example:**
```bash
# Analyze skillsmith itself
python3 scripts/research_skill.py skills/skillsmith

# Save findings to JSON
python3 scripts/research_skill.py skills/omnifocus-manager --output research.json
```

**Output includes:**
- Domain classification and complexity assessment
- Current quality metrics with visual score bars
- Strengths, weaknesses, and opportunities
- Spec compliance violations and warnings
- Full metrics data in JSON format (if --output specified)

### Calculate Metrics Only

To calculate quality metrics without full research:

```bash
python3 scripts/calculate_metrics.py <skill-path> [--format json|text]
```

**Example output:**
```
Quality Metrics: skillsmith
Basic Metrics:
  SKILL.md: 491 lines, ~5290 tokens
  Scripts: 9 files, 2696 lines
  References: 2 files, 783 lines

Quality Scores:
  Conciseness:     [██░░░░░░░░] 26/100
  Complexity:      [████████░░] 80/100
  Spec Compliance: [███████░░░] 75/100
  Progressive:     [██████████] 100/100
  Overall:         [██████░░░░] 68/100
```

### Integration with skill-planner

Research findings integrate seamlessly with skill-planner for improvement workflows:

**Workflow:**
1. User: "I want to improve skillsmith"
2. skill-planner invokes skillsmith research
3. Research analyzes skill and identifies issues
4. skill-planner creates improvement plan with research findings
5. Plan includes baseline metrics and specific opportunities
6. User refines and approves plan
7. Implementation guided by objective metrics

**Benefits:**
- Data-driven improvement decisions
- Objective baseline for measuring progress
- Specific, actionable recommendations
- Before/after metrics comparison

### Research Output Format

Research generates structured JSON with all findings:

```json
{
  "timestamp": "2025-12-21T...",
  "skill_path": "skills/skillsmith",
  "phase1_intent": {
    "name": "skillsmith",
    "description": "...",
    "purpose": "...",
    "triggers": [...]
  },
  "phase2_domain": {
    "domain": "meta",
    "complexity": "Meta",
    "special_considerations": [...]
  },
  "phase5_implementation": {
    "metrics": { ... },
    "strengths": [...],
    "weaknesses": [...],
    "opportunities": [...]
  },
  "phase6_compliance": {
    "score": 75,
    "violations": [],
    "warnings": [...]
  }
}
```

This structured format enables programmatic consumption by skill-planner and other tools.

### Best Practices for Research

**When to research:**
- Before planning skill improvements
- After significant changes to validate quality
- Periodically to track skill health
- When skill feels bloated or unclear

**Interpreting metrics:**
- Overall < 60: Significant improvements needed
- Overall 60-79: Good quality, room for improvement
- Overall 80+: Excellent quality

**Focus areas by score:**
- Low conciseness: Move content to references/, simplify language
- Low complexity: Reduce nesting, simplify structure
- Low spec compliance: Fix frontmatter, follow guidelines
- Low progressive disclosure: Better separation of concerns

**Acting on findings:**
- Use skill-planner for systematic improvements
- Address violations before warnings
- Prioritize opportunities with highest impact
- Measure before/after to validate improvements
