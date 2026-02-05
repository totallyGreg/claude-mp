#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Skill Initializer - Creates a new skill from template

Usage:
    uv run scripts/init_skill.py <skill-name> [--template TYPE] [--path <path>] [--verbose]

Template Types:
    minimal   - Simple skill with SKILL.md only (~50-100 lines)
    standard  - Skill with references and optional scripts (~150-300 lines) [default]
    complete  - Full skill with all resource types (~250-400 lines)

Examples:
    uv run scripts/init_skill.py my-new-skill
    uv run scripts/init_skill.py my-api-helper --template minimal
    uv run scripts/init_skill.py complex-tool --template complete --path /custom/location
    uv run scripts/init_skill.py custom-skill --verbose
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from utils import get_repo_root

# Template types
TEMPLATE_MINIMAL = "minimal"
TEMPLATE_STANDARD = "standard"
TEMPLATE_COMPLETE = "complete"

MINIMAL_SKILL_TEMPLATE = """---
name: {skill_name}
description: This skill should be used when users ask to "[TODO: trigger phrase 1]", "[TODO: trigger phrase 2]". [TODO: Brief description of what the skill does.]
metadata:
  version: "1.0.0"
---

# {skill_title}

[TODO: 1-2 sentences explaining what this skill enables]

## Usage

[TODO: Explain how to use this skill. Include key commands, patterns, or workflows.]

## Key Concepts

[TODO: List 3-5 core concepts with brief explanations]

---

*This is a minimal skill template. For more complex skills, consider adding references/, scripts/, or assets/ directories.*
"""

COMPLETE_SKILL_TEMPLATE = """---
name: {skill_name}
description: This skill should be used when users ask to "[TODO: trigger phrase 1]", "[TODO: trigger phrase 2]", "[TODO: trigger phrase 3]", or "[TODO: trigger phrase 4]". [TODO: Comprehensive description of skill capabilities.]
metadata:
  version: "1.0.0"
  author: [TODO: Author name]
compatibility: Requires python3 and uv for script execution
license: See LICENSE.txt
---

# {skill_title}

This skill provides [TODO: comprehensive description of what this skill enables].

## About This Skill

### What This Skill Provides

1. [TODO: Primary capability]
2. [TODO: Secondary capability]
3. [TODO: Tertiary capability]
4. [TODO: Additional capability]

### When to Use This Skill

[TODO: Describe specific scenarios when this skill should be triggered]

## Workflow

### Step 1: [TODO: First major step]

[TODO: Description and guidance for step 1]

### Step 2: [TODO: Second major step]

[TODO: Description and guidance for step 2]

### Step 3: [TODO: Third major step]

[TODO: Description and guidance for step 3]

## Common Patterns

### Pattern 1: [TODO: Pattern name]

[TODO: Description of common pattern]

### Pattern 2: [TODO: Pattern name]

[TODO: Description of common pattern]

## Bundled Resources

### scripts/

Executable utilities for this skill:
- `scripts/main_tool.py` - [TODO: Primary tool description]
- `scripts/helper.py` - [TODO: Helper utility description]

### references/

Detailed documentation:
- `references/detailed_guide.md` - Comprehensive guide
- `references/patterns.md` - Common patterns and examples
- `references/advanced.md` - Advanced techniques

### assets/

Templates and files used in output:
- `assets/templates/` - Template files

## Advanced Topics

For detailed guidance, see reference files:
- **`references/detailed_guide.md`** - Comprehensive implementation details
- **`references/patterns.md`** - Common patterns and best practices
- **`references/advanced.md`** - Advanced techniques and edge cases
"""

SKILL_TEMPLATE = """---
name: {skill_name}
description: [TODO: Complete and informative explanation of what the skill does and when to use it. Include WHEN to use this skill - specific scenarios, file types, or tasks that trigger it.]
metadata:
  version: 1.0.0
---

# {skill_title}

## Overview

[TODO: 1-2 sentences explaining what this skill enables]

## Structuring This Skill

[TODO: Choose the structure that best fits this skill's purpose. Common patterns:

**1. Workflow-Based** (best for sequential processes)
- Works well when there are clear step-by-step procedures
- Example: DOCX skill with "Workflow Decision Tree" → "Reading" → "Creating" → "Editing"
- Structure: ## Overview → ## Workflow Decision Tree → ## Step 1 → ## Step 2...

**2. Task-Based** (best for tool collections)
- Works well when the skill offers different operations/capabilities
- Example: PDF skill with "Quick Start" → "Merge PDFs" → "Split PDFs" → "Extract Text"
- Structure: ## Overview → ## Quick Start → ## Task Category 1 → ## Task Category 2...

**3. Reference/Guidelines** (best for standards or specifications)
- Works well for brand guidelines, coding standards, or requirements
- Example: Brand styling with "Brand Guidelines" → "Colors" → "Typography" → "Features"
- Structure: ## Overview → ## Guidelines → ## Specifications → ## Usage...

**4. Capabilities-Based** (best for integrated systems)
- Works well when the skill provides multiple interrelated features
- Example: Product Management with "Core Capabilities" → numbered capability list
- Structure: ## Overview → ## Core Capabilities → ### 1. Feature → ### 2. Feature...

Patterns can be mixed and matched as needed. Most skills combine patterns (e.g., start with task-based, add workflow for complex operations).

Delete this entire "Structuring This Skill" section when done - it's just guidance.]

## [TODO: Replace with the first main section based on chosen structure]

[TODO: Add content here. See examples in existing skills:
- Code samples for technical skills
- Decision trees for complex workflows
- Concrete examples with realistic user requests
- References to scripts/templates/references as needed]

## Resources

This skill includes example resource directories that demonstrate how to organize different types of bundled resources:

### scripts/
Executable code (Python/Bash/etc.) that can be run directly to perform specific operations.

**Examples from other skills:**
- PDF skill: `fill_fillable_fields.py`, `extract_form_field_info.py` - utilities for PDF manipulation
- DOCX skill: `document.py`, `utilities.py` - Python modules for document processing

**Appropriate for:** Python scripts, shell scripts, or any executable code that performs automation, data processing, or specific operations.

**Note:** Scripts may be executed without loading into context, but can still be read by Claude for patching or environment adjustments.

### references/
Documentation and reference material intended to be loaded into context to inform Claude's process and thinking.

**Examples from other skills:**
- Product management: `communication.md`, `context_building.md` - detailed workflow guides
- BigQuery: API reference documentation and query examples
- Finance: Schema documentation, company policies

**Appropriate for:** In-depth documentation, API references, database schemas, comprehensive guides, or any detailed information that Claude should reference while working.

### assets/
Files not intended to be loaded into context, but rather used within the output Claude produces.

**Examples from other skills:**
- Brand styling: PowerPoint template files (.pptx), logo files
- Frontend builder: HTML/React boilerplate project directories
- Typography: Font files (.ttf, .woff2)

**Appropriate for:** Templates, boilerplate code, document templates, images, icons, fonts, or any files meant to be copied or used in the final output.

---

**Any unneeded directories can be deleted.** Not every skill requires all three types of resources.
"""

EXAMPLE_SCRIPT = '''#!/usr/bin/env python3
# /// script
# dependencies = [
#   # Add dependencies here with version constraints:
#   # "requests>=2.31.0,<3.0.0",
#   # "pyyaml>=6.0.1",
# ]
# ///
"""
Example helper script for {skill_name}

This script uses PEP 723 inline metadata for dependency management.

Usage:
    uv run scripts/example.py

Dependencies are declared in the # /// script block above.
Uncomment and add dependencies as needed.

Example real scripts from other skills:
- pdf/scripts/fill_fillable_fields.py - Fills PDF form fields
- pdf/scripts/convert_pdf_to_images.py - Converts PDF pages to images

For comprehensive guidance on Python scripts in skills, see:
references/python_uv_guide.md in the skillsmith skill.
"""

def main():
    """Main entry point for the script."""
    print("This is an example script for {skill_name}")
    # TODO: Add actual script logic here
    # This could be data processing, file conversion, API calls, etc.

if __name__ == "__main__":
    main()
'''

EXAMPLE_REFERENCE = """# Reference Documentation for {skill_title}

This is a placeholder for detailed reference documentation.
Replace with actual reference content or delete if not needed.

Example real reference docs from other skills:
- product-management/references/communication.md - Comprehensive guide for status updates
- product-management/references/context_building.md - Deep-dive on gathering context
- bigquery/references/ - API references and query examples

## When Reference Docs Are Useful

Reference docs are ideal for:
- Comprehensive API documentation
- Detailed workflow guides
- Complex multi-step processes
- Information too lengthy for main SKILL.md
- Content that's only needed for specific use cases

## Structure Suggestions

### API Reference Example
- Overview
- Authentication
- Endpoints with examples
- Error codes
- Rate limits

### Workflow Guide Example
- Prerequisites
- Step-by-step instructions
- Common patterns
- Troubleshooting
- Best practices
"""
FORMS_TEMPLATE = """# Form Templates

This file contains structured templates for this skill's workflows.

## Example Form

Replace this with actual form templates relevant to your skill's domain.

**Field 1:** [description]
**Field 2:** [description]
**Field 3:** [description]
"""

EXAMPLE_ASSET = """# Example Asset File

This placeholder represents where asset files would be stored.
Replace with actual asset files (templates, images, fonts, etc.) or delete if not needed.

Asset files are NOT intended to be loaded into context, but rather used within
the output Claude produces.

Example asset files from other skills:
- Brand guidelines: logo.png, slides_template.pptx
- Frontend builder: hello-world/ directory with HTML/React boilerplate
- Typography: custom-font.ttf, font-family.woff2
- Data: sample_data.csv, test_dataset.json

## Common Asset Types

- Templates: .pptx, .docx, boilerplate directories
- Images: .png, .jpg, .svg, .gif
- Fonts: .ttf, .otf, .woff, .woff2
- Boilerplate code: Project directories, starter files
- Icons: .ico, .svg
- Data files: .csv, .json, .xml, .yaml

Note: This is a text placeholder. Actual assets can be any file type.
"""

IMPROVEMENT_PLAN_TEMPLATE = """# {skill_title} - Improvement Plan

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
| 1.0.0 | {date} | - | Initial release | - | - | - | - | - |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure (0-100 scale)

## Active Work

No active improvements yet. Create GitHub Issues for planned work.

See GitHub Issues for detailed plans and task checklists.

## Known Issues

None yet. Report issues at https://github.com/{{{{repo}}}}/issues

## Archive

For complete development history:
- Git commit history: `git log --grep="{skill_name}"`
- Closed issues: https://github.com/{{{{repo}}}}/issues?q=label:enhancement+is:closed
- Cross-skill learnings: docs/lessons/

---

**Development Workflow:**

See repository `/WORKFLOW.md` for complete documentation on:
- GitHub Issues as source of truth for ALL planning
- IMPROVEMENT_PLAN.md format (this lightweight release notes + metrics)
- Two-commit release strategy
- Using `uv run scripts/evaluate_skill.py --export-table-row` to capture metrics
"""


def title_case_skill_name(skill_name):
    """Convert hyphenated skill name to Title Case for display."""
    return " ".join(word.capitalize() for word in skill_name.split("-"))


def init_skill(skill_name, skills_dir, template_type=TEMPLATE_STANDARD):
    """
    Initialize a new skill directory with template SKILL.md.

    Args:
        skill_name: Name of the skill
        skills_dir: Path to skills directory where skill will be created
        template_type: Type of template to use (minimal, standard, complete)

    Returns:
        Path to created skill directory, or None if error
    """
    # Determine skill directory path
    skill_dir = skills_dir / skill_name

    # Check if directory already exists
    if skill_dir.exists():
        print(f"❌ Error: Skill directory already exists: {skill_dir}")
        return None

    # Create skill directory
    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        print(f"✅ Created skill directory: {skill_dir}")
    except Exception as e:
        print(f"❌ Error creating directory: {e}")
        return None

    # Select template based on template_type
    skill_title = title_case_skill_name(skill_name)
    if template_type == TEMPLATE_MINIMAL:
        skill_content = MINIMAL_SKILL_TEMPLATE.format(
            skill_name=skill_name, skill_title=skill_title
        )
        print(f"📋 Using minimal template")
    elif template_type == TEMPLATE_COMPLETE:
        skill_content = COMPLETE_SKILL_TEMPLATE.format(
            skill_name=skill_name, skill_title=skill_title
        )
        print(f"📋 Using complete template")
    else:  # TEMPLATE_STANDARD (default)
        skill_content = SKILL_TEMPLATE.format(
            skill_name=skill_name, skill_title=skill_title
        )
        print(f"📋 Using standard template")

    skill_md_path = skill_dir / "SKILL.md"
    try:
        skill_md_path.write_text(skill_content)
        print("✅ Created SKILL.md")
    except Exception as e:
        print(f"❌ Error creating SKILL.md: {e}")
        return None

    # Create IMPROVEMENT_PLAN.md from template (skip for minimal)
    if template_type != TEMPLATE_MINIMAL:
        today = datetime.now().strftime("%Y-%m-%d")
        improvement_plan_content = IMPROVEMENT_PLAN_TEMPLATE.format(
            skill_name=skill_name, skill_title=skill_title, date=today
        )

        improvement_plan_path = skill_dir / "IMPROVEMENT_PLAN.md"
        try:
            improvement_plan_path.write_text(improvement_plan_content)
            print("✅ Created IMPROVEMENT_PLAN.md")
        except Exception as e:
            print(f"❌ Error creating IMPROVEMENT_PLAN.md: {e}")
            return None

    # Create resource directories based on template type
    try:
        if template_type == TEMPLATE_MINIMAL:
            # Minimal: No resource directories
            pass

        elif template_type == TEMPLATE_STANDARD:
            # Standard: references/ and optional scripts/
            references_dir = skill_dir / "references"
            references_dir.mkdir(exist_ok=True)
            example_reference = references_dir / "detailed_guide.md"
            example_reference.write_text(EXAMPLE_REFERENCE.format(skill_title=skill_title))
            print("✅ Created references/detailed_guide.md")

            scripts_dir = skill_dir / "scripts"
            scripts_dir.mkdir(exist_ok=True)
            example_script = scripts_dir / "helper.py"
            example_script.write_text(EXAMPLE_SCRIPT.format(skill_name=skill_name))
            example_script.chmod(0o755)
            print("✅ Created scripts/helper.py")

        else:  # TEMPLATE_COMPLETE
            # Complete: All resource directories
            # Create scripts/ directory
            scripts_dir = skill_dir / "scripts"
            scripts_dir.mkdir(exist_ok=True)
            main_script = scripts_dir / "main_tool.py"
            main_script.write_text(EXAMPLE_SCRIPT.format(skill_name=skill_name))
            main_script.chmod(0o755)
            print("✅ Created scripts/main_tool.py")

            helper_script = scripts_dir / "helper.py"
            helper_script.write_text(EXAMPLE_SCRIPT.format(skill_name=skill_name))
            helper_script.chmod(0o755)
            print("✅ Created scripts/helper.py")

            # Create references/ directory with multiple files
            references_dir = skill_dir / "references"
            references_dir.mkdir(exist_ok=True)

            for ref_name in ["detailed_guide.md", "patterns.md", "advanced.md"]:
                ref_file = references_dir / ref_name
                ref_file.write_text(EXAMPLE_REFERENCE.format(skill_title=skill_title))
                print(f"✅ Created references/{ref_name}")

            # Create assets/ directory
            assets_dir = skill_dir / "assets"
            assets_dir.mkdir(exist_ok=True)
            templates_dir = assets_dir / "templates"
            templates_dir.mkdir(exist_ok=True)
            example_asset = templates_dir / "example_template.txt"
            example_asset.write_text(EXAMPLE_ASSET)
            print("✅ Created assets/templates/example_template.txt")

    except Exception as e:
        print(f"❌ Error creating resource directories: {e}")
        return None

    # Print next steps based on template type
    print(f"\n✅ Skill '{skill_name}' initialized successfully at {skill_dir}")
    print("\nNext steps:")
    print("1. Edit SKILL.md to complete the TODO items and update the description")
    if template_type == TEMPLATE_MINIMAL:
        print("2. Run the validator when ready: uv run scripts/evaluate_skill.py <path> --quick")
    else:
        print("2. Customize or delete the example files in resource directories")
        print("3. Run the validator when ready: uv run scripts/evaluate_skill.py <path> --quick")

    return skill_dir


def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new skill with template structure. Auto-detects repository root.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Skill name requirements:
  - Hyphen-case identifier (e.g., 'data-analyzer')
  - Lowercase letters, digits, and hyphens only
  - Max 40 characters
  - Must match directory name exactly

Template types:
  minimal   - Simple skill with SKILL.md only (~50-100 lines)
  standard  - Skill with references and scripts (~150-300 lines) [default]
  complete  - Full skill with all resource types (~250-400 lines)

Examples:
  # Auto-detect repo root, create skill in <repo>/skills/<skill-name>
  %(prog)s my-new-skill

  # Create minimal skill (no resource directories)
  %(prog)s simple-helper --template minimal

  # Create complete skill (all resource directories)
  %(prog)s complex-tool --template complete

  # With explicit repository ROOT path (script appends /skills automatically)
  %(prog)s my-api-helper --path /path/to/repo

  # With verbose output to see path resolution
  %(prog)s custom-skill --verbose
""",
    )

    parser.add_argument("skill_name", help="Name of the skill to create")

    parser.add_argument(
        "--template",
        "-t",
        choices=["minimal", "standard", "complete"],
        default="standard",
        help="Template type: minimal, standard (default), or complete",
    )

    parser.add_argument(
        "--path",
        default=".",
        help="Repository root path - NOT the skills directory (default: auto-detect). Script appends /skills automatically.",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed path resolution information",
    )

    args = parser.parse_args()

    # Determine repository root with auto-detection
    repo_root = get_repo_root(args.path, verbose=args.verbose)

    # Warn if path ends with /skills (common mistake)
    if args.path != "." and args.path.rstrip("/").endswith("/skills"):
        print("⚠️  Warning: --path appears to end with '/skills'")
        print(f"   The script automatically appends '/skills' to the repository root.")
        print(f"   You provided: {args.path}")
        print(f"   This will create: {repo_root / 'skills' / args.skill_name}")
        print(f"   Did you mean to provide the repository root instead?")
        print()
        response = input("   Continue anyway? [y/N]: ").strip().lower()
        if response not in ["y", "yes"]:
            print("❌ Cancelled by user")
            sys.exit(1)
        print()

    skills_dir = repo_root / "skills"

    # Ensure skills directory exists
    if not skills_dir.exists():
        print(f"⚠️  Creating skills directory at: {skills_dir}")
        try:
            skills_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"❌ Error creating skills directory: {e}")
            sys.exit(1)

    if args.verbose:
        print(f"🔍 Skill Creation:")
        print(f"   Repository root: {repo_root}")
        print(f"   Skills directory: {skills_dir}")
        print(f"   Target skill directory: {skills_dir / args.skill_name}")
        print(f"   Template type: {args.template}")
        print()

    print(f"🚀 Initializing skill: {args.skill_name}")
    print(f"   Location: {skills_dir}")
    print()

    result = init_skill(args.skill_name, skills_dir, args.template)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
