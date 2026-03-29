#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
#   "python-frontmatter>=1.0.0",
#   "python-dateutil>=2.8.2",
# ]
# ///

"""
Extract meeting note from daily/company note section.

Parses selected text from daily notes or company notes to extract meeting
metadata, infers missing information from context, and generates meeting
note metadata for template creation.

Usage:
    uv run extract_section_to_meeting.py <vault-path> <note-path> <selection>

Arguments:
    vault-path: Absolute path to Obsidian vault
    note-path: Path to note containing selection (relative to vault)
    selection: Selected text to parse

Returns:
    JSON with meeting metadata:
    {
        "status": "success",
        "metadata": {
            "title": "Meeting title",
            "start": "2026-02-10T14:30:00",
            "scope": ["[[Company]]", "[[Project]]"],
            "attendees": ["[[Person1]]", "[[Person2]]"],
            "type": "customer-meeting",
            "inferred_company": "Company",
            "inferred_folder": "path/to/folder"
        },
        "missing": ["field1", "field2"]
    }

Example:
    $ uv run extract_section_to_meeting.py \\
        /Users/me/vault \\
        "Work/PAN/Daily Notes/2026-02-10.md" \\
        "### (log::⏱ 14:30 -0500: Customer sync)\\n\\nscope:: [[Acme]]"
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

def validate_vault_path(vault_path_str: str) -> Path:
    """
    Validate vault path for security.

    Prevents access to system directories to ensure scripts only
    operate on user vaults.

    Args:
        vault_path_str: Path to validate

    Returns:
        Resolved Path object

    Raises:
        ValueError: If path is in forbidden directory
    """
    vault_path = Path(vault_path_str).resolve()
    forbidden = ['/etc', '/var', '/usr', '/bin', '/sbin', '/root', '/System']

    if any(str(vault_path).startswith(p) for p in forbidden):
        raise ValueError(f"Access denied: {vault_path}")

    if not vault_path.exists():
        raise ValueError(f"Vault path does not exist: {vault_path}")

    return vault_path

def parse_log_syntax(selection: str) -> Dict[str, Any]:
    """
    Parse Quickadd log syntax for meeting metadata.

    Patterns:
        ### (log::⏱ HH:MM ZONE: Title)
        ### (log::⏱ HH:MM -0500: Meeting with Customer)

    Args:
        selection: Selected text to parse

    Returns:
        Dict with extracted metadata
    """
    metadata = {}

    # Pattern: ### (log::⏱ HH:MM ZONE: Title)
    log_pattern = r'###\s*\(log::⏱\s*(\d{1,2}:\d{2})\s*([-+]\d{4})?:\s*(.+?)\)'
    match = re.search(log_pattern, selection)

    if match:
        time = match.group(1)
        timezone = match.group(2) or ""
        title = match.group(3).strip()

        metadata['time'] = time
        metadata['timezone'] = timezone
        metadata['title'] = title

    return metadata

def parse_inline_fields(selection: str) -> Dict[str, List[str]]:
    """
    Parse Dataview-style inline fields.

    Patterns:
        scope:: [[Company]], [[Project]]
        attendees:: [[Person1]], [[Person2]]
        start:: 2026-02-10T14:30:00

    Args:
        selection: Selected text to parse

    Returns:
        Dict of field names to values
    """
    fields = {}

    # Pattern: field:: value
    field_pattern = r'(\w+)::\s*(.+?)(?:\n|$)'
    matches = re.finditer(field_pattern, selection)

    for match in matches:
        field_name = match.group(1)
        field_value = match.group(2).strip()

        # Parse wikilinks [[Note]]
        if '[[' in field_value:
            wikilinks = re.findall(r'\[\[([^\]]+)\]\]', field_value)
            fields[field_name] = [f"[[{link}]]" for link in wikilinks]
        else:
            fields[field_name] = [field_value]

    return fields

def parse_heading_date(selection: str) -> Optional[str]:
    """
    Parse date from markdown heading.

    Patterns:
        ## 2026-02-05
        ## Meeting on 2026-02-05
        ### 2026-02-05 Notes

    Args:
        selection: Selected text to parse

    Returns:
        ISO date string or None
    """
    # Pattern: ## ...YYYY-MM-DD...
    date_pattern = r'##\s*.*?(\d{4}-\d{2}-\d{2})'
    match = re.search(date_pattern, selection)

    if match:
        return match.group(1)

    return None

def infer_company_from_path(note_path: str) -> Optional[str]:
    """
    Infer company/organization from note path.

    Example:
        "Work/Palo Alto Networks/Daily Notes/2026-02-10.md" → "Palo Alto Networks"
        "Notes/Solo.io/Meetings/..." → "Solo.io"

    Args:
        note_path: Path to note (relative to vault)

    Returns:
        Company name or None
    """
    parts = Path(note_path).parts

    # Skip common folder names
    skip = ['Work', 'Notes', 'Daily Notes', 'Meetings', '700 Notes', '800 Work']

    for part in parts:
        if part not in skip and not part.endswith('.md'):
            return part

    return None

def infer_folder_from_context(note_path: str, company: Optional[str]) -> str:
    """
    Infer meeting note folder from current context.

    Args:
        note_path: Path to note containing selection
        company: Inferred company name

    Returns:
        Folder path for new meeting note
    """
    parts = Path(note_path).parts

    # If in company folder structure, use company's Meetings folder
    if company:
        # Find company in path
        for i, part in enumerate(parts):
            if part == company:
                # Build path up to company, add Meetings
                base_path = Path(*parts[:i+1])
                return str(base_path / "Meetings")

    # Fallback to generic Meetings folder
    return "Meetings"

def extract_meeting_metadata(
    vault_path: Path,
    note_path: str,
    selection: str
) -> Dict[str, Any]:
    """
    Extract meeting metadata from selection.

    Args:
        vault_path: Path to vault
        note_path: Path to note containing selection
        selection: Selected text

    Returns:
        Dict with extracted and inferred metadata
    """
    metadata = {
        "status": "success",
        "metadata": {},
        "missing": []
    }

    # Parse log syntax
    log_data = parse_log_syntax(selection)
    if log_data:
        if 'title' in log_data:
            metadata['metadata']['title'] = log_data['title']
        if 'time' in log_data:
            # TODO: Combine with date to create full start datetime
            metadata['metadata']['time'] = log_data['time']

    # Parse inline fields
    inline_fields = parse_inline_fields(selection)
    if 'scope' in inline_fields:
        metadata['metadata']['scope'] = inline_fields['scope']
    if 'attendees' in inline_fields:
        metadata['metadata']['attendees'] = inline_fields['attendees']
    if 'start' in inline_fields:
        metadata['metadata']['start'] = inline_fields['start'][0]

    # Parse heading date
    date = parse_heading_date(selection)
    if date:
        metadata['metadata']['date'] = date

    # Infer company from path
    company = infer_company_from_path(note_path)
    if company:
        metadata['metadata']['inferred_company'] = company
        # Add to scope if not already present
        if 'scope' not in metadata['metadata']:
            metadata['metadata']['scope'] = [f"[[{company}]]"]

    # Infer folder
    folder = infer_folder_from_context(note_path, company)
    metadata['metadata']['inferred_folder'] = folder

    # Identify missing fields
    required = ['title', 'start']
    for field in required:
        if field not in metadata['metadata']:
            metadata['missing'].append(field)

    return metadata

def main():
    """Main entry point."""
    if len(sys.argv) < 4:
        print(json.dumps({
            "status": "error",
            "error": "Usage: extract_section_to_meeting.py <vault-path> <note-path> <selection>"
        }))
        sys.exit(1)

    try:
        vault_path = validate_vault_path(sys.argv[1])
        note_path = sys.argv[2]
        selection = sys.argv[3]

        result = extract_meeting_metadata(vault_path, note_path, selection)
        print(json.dumps(result, indent=2))

    except ValueError as e:
        print(json.dumps({
            "status": "error",
            "error": str(e)
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "error": f"Unexpected error: {str(e)}"
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
