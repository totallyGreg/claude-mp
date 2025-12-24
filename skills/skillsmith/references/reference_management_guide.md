# Reference Management Guide

## Introduction

For skills with multiple reference documents, skillsmith provides automated reference catalog management. This guide covers how to use the reference management system to maintain organized, discoverable, and consolidated reference documentation.

**Why Reference Management Matters:**
- Enables faster reference discovery for agents through structured metadata
- Ensures all references are properly documented and cataloged
- Prevents reference bloat through consolidation detection
- Validates compliance with AgentSkills specification

**When to Use Reference Management:**
- Skills with 3+ reference files should include a REFERENCE.md catalog
- When adding new reference documentation
- When reviewing skills for consolidation opportunities
- During skill validation and quality checks

## Reference Catalog (REFERENCE.md)

### Purpose and Structure

Skills with 3+ reference files should include a `references/REFERENCE.md` catalog that indexes all references with metadata. This enables faster reference discovery and ensures all references are properly documented.

**Catalog Structure:**
- **Quick Reference**: Concise list of all references with one-line descriptions
- **Detailed Index**: Full metadata including size, topics, purpose, usage scenarios, key sections
- **Consolidation Status**: Warnings about similar references that may need consolidation

**Metadata Included:**
- File name and size (KB)
- Line count
- Topic tags (extracted from headings and content)
- Purpose statement (first paragraph)
- Key sections (H2 headings)
- When to use (usage scenarios)

**Benefits:**
- Faster reference discovery for agents
- Ensures all references are documented
- Standardized format across skills
- Automated maintenance via update_references.py

### How Agents Use Catalogs

Instead of reading SKILL.md to discover which references exist, agents can:
1. Read the compact REFERENCE.md catalog
2. Quickly identify relevant references by topics and purpose
3. Load only the specific references needed for the task
4. Understand when to use each reference through usage scenarios

This follows the progressive disclosure principle: metadata in REFERENCE.md (level 2), full reference content loaded on-demand (level 3).

## Generating and Updating Catalogs

### Automatic Workflow

The reference catalog is automatically maintained during skillsmith quick update workflows:

1. When adding a reference file through skillsmith
2. Skillsmith automatically runs update_references.py
3. REFERENCE.md is regenerated with the new file included
4. Both the reference file and updated catalog are committed together

### Manual Workflow

You can also manually generate or update the catalog:

```bash
# Generate or update catalog for current skill
python3 scripts/update_references.py .

# For other skills (from skillsmith directory)
python3 scripts/update_references.py ../other-skill
```

### Output Formats

The catalog can be generated in different formats:

```bash
# Markdown format (default)
python3 scripts/update_references.py .

# JSON format for programmatic access
python3 scripts/update_references.py . --format json
```

**JSON output includes:**
- last_updated timestamp
- references array with full metadata
- Total reference count

## Adding New References

### Quick Update Workflow (Automatic)

When adding a new reference file during skill improvements handled by skillsmith:

1. Create new reference file: `references/new_topic.md`
2. Skillsmith automatically runs update_references.py
3. REFERENCE.md regenerated with new file included
4. Both files committed together

**No manual catalog updates needed!**

### Manual Workflow

For manual reference additions:

1. Create `references/new_topic.md` with proper structure:
   - H1 heading with descriptive title
   - Clear introductory paragraph explaining purpose
   - H2 sections for major topics
   - Well-organized content

2. Run the catalog update script:
   ```bash
   python3 scripts/update_references.py .
   ```

3. Review the updated REFERENCE.md to verify:
   - New reference appears in Quick Reference section
   - Detailed index entry has accurate metadata
   - Topics were correctly extracted

4. Commit both files together:
   ```bash
   git add references/new_topic.md references/REFERENCE.md
   git commit -m "Add new_topic reference documentation"
   ```

### Best Practices

- **Use descriptive filenames**: `api_authentication.md` not `auth.md`
- **Start with clear H1**: First heading becomes the title in catalog
- **Write clear purpose**: First paragraph is extracted as purpose statement
- **Use H2 for sections**: These become "Key sections" in catalog
- **Keep focused**: One topic per reference file
- **Update catalog**: Always regenerate REFERENCE.md after adding references

## Detecting Consolidation Opportunities

### Why Consolidation Matters

As skills evolve, references may become redundant or overlapping. Multiple references covering similar topics:
- Fragment information unnecessarily
- Create maintenance burden
- Confuse agents about which reference to load
- Violate the principle of keeping references focused

### Running Consolidation Detection

Detect similar references using the duplicate detection mode:

```bash
python3 scripts/update_references.py . --detect-duplicates
```

### Output Example

```
Consolidation Opportunities Detected:

Cluster 1 (85% similar):
  - references/api_guide.md
  - references/api_reference.md
  Recommendation: Consolidate into single API documentation file

Cluster 2 (72% similar):
  - references/workflow_a.md
  - references/process_guide.md
  Recommendation: Review for overlapping content
```

### Similarity Thresholds

The detection algorithm uses Jaccard similarity on reference descriptions and topics:

- **>90% similar**: High priority consolidation (likely duplicates)
  - Action: Merge into single reference file
  - These are probably covering the exact same content

- **70-90% similar**: Medium priority review (overlapping content)
  - Action: Review both files for overlap
  - May need restructuring or partial consolidation

- **<70%**: No consolidation needed
  - Files are sufficiently distinct
  - Keep as separate references

### How Similarity is Calculated

1. **Tokenization**: Extract significant words from purpose and topics
2. **Similarity Metric**: Calculate Jaccard similarity (intersection / union)
3. **Clustering**: Group references with >70% similarity
4. **Recommendations**: Provide action items based on similarity level

### Interpreting Results

**When consolidation is recommended:**
- Read both references to understand overlap
- Determine if they can be merged
- Consider if they serve different use cases despite similarity
- Consolidate if truly redundant

**False positives may occur when:**
- References use similar terminology but serve different purposes
- Topic overlap is high but content depth differs
- References target different skill levels (beginner vs advanced)

Use judgment when deciding whether to consolidate.

## Validating Reference Structure

### Running Structure Validation

Ensure references/ directory follows AgentSkills specification:

```bash
python3 scripts/update_references.py . --validate-structure
```

### Validation Checks

The validator checks for:

1. **Directory exists**: `references/` directory is present
2. **One-level depth**: No nested subdirectories (per AgentSkills spec)
3. **File readability**: All `.md` files can be read
4. **Catalog currency**: REFERENCE.md is up-to-date (if exists)
5. **Large file warnings**: Files >100KB get warnings (use grep patterns in SKILL.md)

### Example Output

```
✓ references/ directory exists
✓ All references are readable
✓ No nested subdirectories (spec compliant)
✓ REFERENCE.md is up-to-date
⚠ Large file detected: references/api_docs.md (124 KB)
  Recommendation: Consider including grep patterns in SKILL.md
```

### Common Issues and Fixes

**Issue: Nested subdirectories**
- Problem: `references/api/authentication.md`
- Fix: Flatten structure to `references/api_authentication.md`
- Why: AgentSkills spec requires one-level depth

**Issue: REFERENCE.md out of date**
- Problem: Added references but didn't regenerate catalog
- Fix: Run `python3 scripts/update_references.py .`
- Prevention: Use automatic workflow via skillsmith

**Issue: Large reference files**
- Problem: Reference >100KB makes context window inefficient
- Fix: Include grep search patterns in SKILL.md for selective loading
- Example: `grep -A 20 "^## Authentication" references/api_docs.md`

**Issue: Unreadable files**
- Problem: File encoding issues or permission problems
- Fix: Ensure UTF-8 encoding and readable permissions
- Command: `chmod 644 references/*.md`

## FORMS.md Template File

### Purpose and Usage

The `references/FORMS.md` file (optional) contains structured templates for workflows that involve data collection.

**Purpose:**
- Provide consistent templates for common skill workflows
- Standardize data capture across skill usage
- Reduce back-and-forth for missing information
- Serve as quick reference for required fields

### When to Include FORMS.md

Include a FORMS.md file when your skill:
- Involves structured data collection
- Uses repeatable forms or templates frequently
- Requires standardized request/proposal formats
- Has workflows with specific field requirements

### Examples of Form Templates

**Skill-specific examples:**
- **Skill proposal forms**: Template for proposing new skills
- **Improvement request templates**: Standardized improvement requests
- **Research analysis templates**: Structured skill research findings
- **Domain-specific structured data**: Expense reports, status updates, bug reports, etc.

### Benefits

- **Consistency**: All users/agents follow same data structure
- **Completeness**: Templates ensure all required fields are included
- **Efficiency**: Reduces back-and-forth asking for missing information
- **Clarity**: Makes expectations clear upfront

### FORMS.md Structure

Typically organized by form type:

```markdown
# Form Templates

## [Form Type 1]

**Field 1:** [description/requirements]
**Field 2:** [description/requirements]
[...]

## [Form Type 2]

**Field 1:** [description/requirements]
[...]
```

See `references/FORMS.md` in skillsmith for examples of skill proposal, improvement request, and research analysis templates.

## Command Reference

### update_references.py

Complete command-line reference for the reference management script.

**Basic Usage:**
```bash
python3 scripts/update_references.py <skill-path> [options]
```

**Options:**

- `<skill-path>`: Path to skill directory (required)
- `--output FILENAME`: Output filename (default: REFERENCE.md)
- `--format {markdown|json}`: Output format (default: markdown)
- `--detect-duplicates`: Detect and report consolidation opportunities only
- `--validate-structure`: Validate references/ directory structure only
- `--force`: Force regeneration even if catalog is up-to-date

**Examples:**

```bash
# Generate catalog for current skill
python3 scripts/update_references.py .

# Generate for another skill
python3 scripts/update_references.py ../other-skill

# Detect consolidation opportunities
python3 scripts/update_references.py . --detect-duplicates

# Validate structure
python3 scripts/update_references.py . --validate-structure

# Output as JSON
python3 scripts/update_references.py . --format json

# Custom output filename
python3 scripts/update_references.py . --output MY_CATALOG.md
```

**Exit Codes:**
- `0`: Success
- `1`: Validation failure or error

**Output:**
- Markdown: Human-readable catalog with Quick Reference, Detailed Index, and Consolidation Status
- JSON: Machine-readable format with full metadata array

For specification details on references/ directory structure, see `references/agentskills_specification.md` (lines 188-217).
