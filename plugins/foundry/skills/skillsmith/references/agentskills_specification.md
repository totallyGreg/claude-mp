---
last_verified: 2026-04-29
sources:
  - type: github
    repo: "agentskills/agentskills"
    paths: ["docs/specification.mdx"]
    description: "Official AgentSkills specification source"
  - type: web
    url: "https://agentskills.io/specification"
    description: "AgentSkills specification web page"
---

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
- Examples: `Requires python3 and PyPDF2 package`, `Requires Python 3.14+ and uv`

**`metadata`**:
- A map from string keys to string values for additional properties
- Key names should be reasonably unique to avoid accidental conflicts
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
- Space-separated string of pre-approved tools the skill may use
- Support may vary between agent implementations
- Example: `allowed-tools: Bash(git:*) Bash(jq:*) Read`
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

**Recommended sections (spec-compliant six-section format):**
1. **Purpose** - What the skill does
2. **When to use** - Triggering conditions
3. **Step-by-step instructions** - Procedural workflow
4. **Input/output examples** - Concrete usage examples
5. **Edge case handling** - Error conditions and fallbacks
6. **Resource references** - How to use bundled scripts, references, and assets

**Alternatively, the Anthropic guide's four-section format** (optimized for Claude consumption):
1. **Instructions** - Overview + when to use
2. **Steps** - Numbered workflow
3. **Examples** - Concrete input/output pairs
4. **Troubleshooting** - Common failures and fixes

Both formats are valid. The six-section format maps more directly to spec compliance checks. The four-section format is more compact and easier for Claude to follow at runtime. See `skill_creation_detailed_guide.md` for guidance on choosing between them.

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

## Reference Provenance (Optional)

Reference files can optionally declare where their content originates using YAML frontmatter. This enables automated freshness detection — tools can check whether upstream sources have changed since the reference was last verified.

Provenance is **opt-in**. References without provenance frontmatter are valid and not penalized by evaluation tools.

### Frontmatter Schema

```yaml
---
last_verified: 2026-04-28
sources:
  - type: web
    url: "https://docs.example.com/api"
    description: "Official API documentation"
  - type: github
    repo: "org/repo-name"
    paths: ["src/constants.ts", "docs/"]
    description: "Source code definitions"
  - type: gitlab
    project_id: 12345
    paths: ["apps/api/routers/v1/"]
    description: "Engineering API routers"
  - type: slack
    channel_id: "C0EXAMPLE"
    description: "Release announcements channel"
  - type: plugin
    name: "obsidian"
    known_version: "2.1.0"
    description: "Obsidian CLI plugin capabilities"
---
```

### Field Reference

**`last_verified`** (date, required for provenance):
- ISO 8601 date (`YYYY-MM-DD`) when the reference content was last confirmed accurate against its sources
- Updated only through the `/ss-refresh` workflow, not manually
- References older than 90 days (default threshold) are flagged as stale

**`sources`** (list, required for provenance):
- Each entry has a `type` discriminator and type-specific fields
- Multiple sources per reference are supported (e.g., a reference summarizing content from both a GitHub repo and a web page)

### Source Types

| Type | Required Fields | Optional Fields | What It Checks |
|------|----------------|-----------------|----------------|
| `web` | `url` | `description` | HTTP HEAD status code; URL still reachable |
| `github` | `repo` | `paths`, `description` | Commits since `last_verified` via `gh api` |
| `gitlab` | `project_id` | `paths`, `description` | Commits since `last_verified` via `glab api` |
| `slack` | `channel_id` | `description` | Messages since `last_verified` via Slack API |
| `plugin` | `name` | `known_version`, `description` | Installed plugin version vs `known_version`; CHANGELOG for new entries |

**`paths`** (for `github` and `gitlab`):
- List of repository paths to monitor for commits
- Enables path-level tracking for structured data repos (e.g., tracking `risk-map/schemas/` in a large monorepo)
- When omitted, checks repo-level commit activity

**`known_version`** (for `plugin`):
- The plugin version at the time the reference was last verified
- When the installed plugin version exceeds `known_version`, drift is reported

### Examples

**Web documentation source:**
```yaml
---
last_verified: 2026-04-28
sources:
  - type: web
    url: "https://docs.paloaltonetworks.com/ai-runtime-security"
    description: "AIRS product documentation"
---
```

**GitHub structured data repo:**
```yaml
---
last_verified: 2026-04-28
sources:
  - type: github
    repo: "cosai-oasis/secure-ai-tooling"
    paths: ["risk-map/schemas/", "risk-map/personas.yaml"]
    description: "CoSAI Risk Map framework schemas and data"
---
```

**Cross-plugin dependency:**
```yaml
---
last_verified: 2026-04-28
sources:
  - type: plugin
    name: "obsidian"
    known_version: "2.1.0"
    description: "Obsidian CLI and vault management capabilities"
---
```

**Multiple sources on one reference:**
```yaml
---
last_verified: 2026-04-28
sources:
  - type: github
    repo: "cdot65/prisma-airs-sdk"
    paths: ["src/constants.ts"]
    description: "SDK API path definitions"
  - type: web
    url: "https://docs.paloaltonetworks.com/ai-runtime-security"
    description: "Product documentation"
  - type: gitlab
    project_id: 22949
    paths: ["apps/data-plane/src/data_plane/api/routers/v1/"]
    description: "Engineering API routers"
---
```

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

---

## Specification Validation Checklist

Ensure skills comply with the AgentSkills specification before distribution or after major updates.

### 1. Frontmatter Compliance

- [ ] `name` field present (1-64 chars, lowercase alphanumeric + hyphens)
- [ ] `name` matches directory name
- [ ] `description` field present (max 1024 chars, non-empty)
- [ ] `description` uses third-person and includes triggering keywords
- [ ] Optional fields properly formatted: `license`, `compatibility`, `metadata`

### 2. Structure Compliance

- [ ] SKILL.md exists at skill root
- [ ] Directory follows naming conventions (lowercase, hyphens only)
- [ ] Supporting directories use correct names: `scripts/`, `references/`, `assets/`
- [ ] File references use relative paths
- [ ] Reference chains remain one-level deep

### 3. Progressive Disclosure

- [ ] SKILL.md body under 500 lines
- [ ] Detailed content moved to references/
- [ ] Metadata (~100 tokens) provides clear skill purpose
- [ ] Instructions (<5000 tokens) provide actionable guidance

### 4. Content Quality

- [ ] Writing uses imperative/infinitive form
- [ ] Instructions are clear and actionable
- [ ] Examples demonstrate concrete usage
- [ ] Bundled resources are properly referenced

### 5. Reference Organization

- [ ] references/ directory uses one-level depth (no nested subdirectories)
- [ ] References are mentioned contextually in SKILL.md
- [ ] No duplicate or overlapping reference content detected
- [ ] FORMS.md included if skill uses structured data collection

### Validation Tools

Use these tools to validate specification compliance:

```bash
# Comprehensive evaluation with metrics and spec validation (recommended)
python3 scripts/evaluate_skill.py <skill-path>

# Quick validation for pre-commit hooks and CI/CD
python3 scripts/evaluate_skill.py <skill-path> --quick

# Deep multi-phase research analysis for improvement planning
python3 scripts/research_skill.py <skill-path>
```

For detailed tool documentation, see `validation_tools_guide.md`.

---

## Version History

- **v1.0** - Initial AgentSkills specification release
- **Latest** - Current specification at https://agentskills.io/specification
