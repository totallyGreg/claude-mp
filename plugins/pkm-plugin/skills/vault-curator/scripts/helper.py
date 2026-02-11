#!/usr/bin/env python3
# /// script
# dependencies = [
#   # Add dependencies here with version constraints:
#   # "requests>=2.31.0,<3.0.0",
#   # "pyyaml>=6.0.1",
# ]
# ///
"""
Example helper script for vault-curator

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
    print("This is an example script for vault-curator")
    # TODO: Add actual script logic here
    # This could be data processing, file conversion, API calls, etc.

if __name__ == "__main__":
    main()
