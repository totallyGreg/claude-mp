# AgentSkills Specification

This document contains the official AgentSkills specification that defines the structure, requirements, and best practices for creating skills.

**Official sources:**
- https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx
- https://agentskills.io/specification

## Directory Structure

Skills require a minimal structure with a `SKILL.md` file at the skill root. Optional supporting directories include:

- `scripts/` - Executable code (Python, Bash, etc.)
- `references/` - Documentation and reference material
- `assets/` - Static resources (templates, images, data files)

**Minimal valid skill structure:**
```
skill-name/
└── SKILL.md
```

**Complete skill structure:**
```
skill-name/
├── SKILL.md (required)
├── scripts/ (optional)
│   └── *.py, *.sh, etc.
├── references/ (optional)
│   └── *.md
└── assets/ (optional)
    └── templates, images, etc.
```

## SKILL.md Format Requirements

### Required Frontmatter Fields

Every SKILL.md must begin with YAML frontmatter containing two required fields:

**`name`** (required):
- Must be 1-64 characters
- Lowercase alphanumeric characters and hyphens only
- Cannot start or end with hyphens
- Cannot contain consecutive hyphens
- Must match the parent directory name

**Valid examples:**
- `pdf-processing`
- `data-analysis`
- `code-review`
- `api-client`

**Invalid examples:**
- `PDF-Processing` (uppercase)
- `-pdf` (starts with hyphen)
- `pdf-` (ends with hyphen)
- `pdf--processing` (consecutive hyphens)

**`description`** (required):
- Maximum 1024 characters
- Must be non-empty
- Describes what the skill does and when to use it
- Should include keywords that help agents identify when the skill is relevant
- Should be written in third-person (e.g., "This skill should be used when...")

### Optional Frontmatter Fields

**`license`**:
- Brief reference to licensing terms
- Can reference a separate LICENSE file
- Example: `MIT`, `Apache-2.0`, `Complete terms in LICENSE.txt`

**`compatibility`**:
- Maximum 500 characters
- Indicates environment requirements
- Examples: intended product, system packages, network access, Python version, etc.
- Example: `Requires python3 and PyPDF2 package`

**`metadata`**:
- Arbitrary key-value pairs for custom properties
- Commonly used fields:
  - `author`: Skill creator name
  - `version`: Semantic version (e.g., "1.0.0")
  - `tags`: Categories or keywords
- Example:
  ```yaml
  metadata:
    author: John Doe
    version: "1.2.0"
    tags: ["pdf", "document-processing"]
  ```

**`allowed-tools`** (experimental):
- Space-delimited list of pre-approved tools
- Allows skills to specify which tools agents can use
- Example: `allowed-tools: read write bash grep`
- Status: Experimental feature, may change

### Complete Frontmatter Example

```yaml
---
name: pdf-processor
description: This skill should be used when working with PDF files, including rotation, merging, splitting, and extracting text. Handles both simple and complex PDF operations with error handling.
metadata:
  author: Jane Smith
  version: "2.1.0"
  tags: ["pdf", "document", "processing"]
compatibility: Requires python3, PyPDF2>=3.0.0, and PIL for image operations
license: MIT
---
```

## Body Content

The Markdown section following frontmatter contains skill instructions with no format restrictions beyond standard Markdown.

**Recommended sections:**
1. **Purpose** - What the skill does
2. **When to use** - Triggering conditions
3. **Step-by-step instructions** - Procedural workflow
4. **Input/output examples** - Concrete usage examples
5. **Edge case handling** - Error conditions and fallbacks
6. **Resource references** - How to use bundled scripts, references, and assets

**Best practices:**
- Keep SKILL.md under 500 lines (move detailed content to references/)
- Use imperative/infinitive verb form for instructions
- Include concrete examples
- Reference supporting resources clearly
- Avoid deeply nested file reference chains

## Progressive Disclosure Architecture

The AgentSkills framework optimizes context usage across three loading levels:

### Level 1: Metadata (~100 tokens)
- Loaded for all skills at startup
- Consists of `name` and `description` fields
- Determines skill discoverability
- Always in context

### Level 2: Instructions (<5000 tokens recommended)
- Full SKILL.md body loaded when skill activates
- Should be concise and focused
- Keep under 500 lines when possible
- Move detailed content to references/

### Level 3: Supporting Resources (on-demand)
- Scripts, references, and assets loaded only when needed
- Scripts may execute without loading into context
- References loaded when Claude determines necessity
- Assets used in output without context loading
- Effectively unlimited size

**Design principle:** Information density decreases at each level. Most specific and actionable content stays in SKILL.md, while supporting details move to references.

## Supporting Directories

### scripts/

Self-contained executable code that handles tasks requiring deterministic reliability.

**When to include:**
- Same code is rewritten repeatedly
- Deterministic behavior required
- Complex algorithms or data processing
- Integration with external tools or APIs

**Requirements:**
- Must be self-contained and executable
- Should handle dependencies gracefully
- Must include error handling
- Should accept command-line arguments when appropriate

**Examples:**
- `scripts/rotate_pdf.py` - PDF rotation utility
- `scripts/analyze_data.py` - Data analysis pipeline
- `scripts/deploy.sh` - Deployment automation

**Benefits:**
- Token efficient (may execute without reading)
- Deterministic and reliable
- Reusable across skill invocations
- Testable independently

### references/

Additional documentation files loaded when needed to inform Claude's process.

**When to include:**
- Detailed domain knowledge
- Database schemas or API documentation
- Company policies or templates
- Detailed workflow guides
- Large examples or reference material

**Common file types:**
- `REFERENCE.md` - General reference material
- `FORMS.md` - Form templates or structures
- `schema.md` - Database or API schemas
- `policies.md` - Guidelines and rules
- Domain-specific guides

**Examples:**
- `references/finance.md` - Financial schemas and calculations
- `references/mnda.md` - Company NDA template
- `references/api_docs.md` - API endpoint specifications

**Best practices:**
- Use descriptive filenames
- Keep files focused on specific topics
- Include grep search patterns in SKILL.md for large files (>10k words)
- Avoid duplication with SKILL.md content
- Prefer references/ for detailed information to keep SKILL.md lean

### assets/

Static resources not intended for context loading, but used in skill output.

**When to include:**
- Templates for generated content
- Images, logos, or icons
- Boilerplate code or project structures
- Fonts or styling resources
- Sample documents

**Examples:**
- `assets/logo.png` - Brand assets
- `assets/slides.pptx` - PowerPoint templates
- `assets/frontend-template/` - HTML/React boilerplate
- `assets/font.ttf` - Typography resources

**Use cases:**
- Templates that get copied or modified
- Images embedded in output
- Boilerplate code for new projects
- Reference designs or mockups

**Benefits:**
- Separates output resources from documentation
- Enables reuse without context overhead
- Supports complex multi-file templates
- Maintains consistency across skill usage

## File References and Best Practices

**Reference depth:**
- Keep reference chains one-level deep from SKILL.md
- Avoid deeply nested file references
- Use relative paths from skill root

**Path conventions:**
```markdown
<!-- Good: One-level reference -->
See `references/schema.md` for database structure.
Run `scripts/process.py` to execute workflow.
Use template from `assets/template.html`.

<!-- Avoid: Deep nesting -->
See `references/advanced/subsystem/details.md`
```

**Context optimization:**
- Keep SKILL.md under 500 lines
- Move detailed material to references/
- Use progressive disclosure principles
- Let Claude load references on-demand

**Naming conventions:**
- Use descriptive, lowercase names with hyphens
- Match directory structure to purpose
- Keep filenames concise but clear

## Validation

**Specification compliance:**
- Use `skills-ref` reference library to validate structure
- Verify naming conventions (lowercase, alphanumeric, hyphens only)
- Check frontmatter completeness
- Ensure description quality and relevance

**Common validation points:**
- `name` matches directory name
- `name` follows naming rules (1-64 chars, lowercase, no leading/trailing hyphens)
- `description` is non-empty and under 1024 characters
- SKILL.md exists at skill root
- Directory structure follows conventions
- File paths use relative references

## Design Principles Summary

1. **Progressive Disclosure** - Load information only when needed
2. **Context Efficiency** - Keep frequently loaded content lean
3. **Self-Contained** - Skills should include all necessary resources
4. **Discoverable** - Clear naming and descriptions enable proper triggering
5. **Maintainable** - Organized structure supports long-term evolution
6. **Reusable** - Bundled resources eliminate redundant work

## Migration from Non-Compliant Skills

When updating existing skills to meet specification:

1. **Verify frontmatter:**
   - Ensure `name` and `description` are present
   - Check `name` follows naming conventions
   - Validate `description` length and clarity

2. **Restructure content:**
   - Move detailed content from SKILL.md to references/
   - Extract reusable code to scripts/
   - Move templates and assets to assets/

3. **Update references:**
   - Change absolute paths to relative paths
   - Flatten nested reference chains
   - Update documentation to reference new locations

4. **Test progressive disclosure:**
   - Verify skill triggers with metadata alone
   - Ensure SKILL.md provides sufficient context
   - Confirm resources load on-demand

5. **Validate compliance:**
   - Use validation tools
   - Check all requirements met
   - Test skill functionality

## Version History

- **v1.0** - Initial AgentSkills specification release
- **Latest** - Current specification at https://agentskills.io/specification
