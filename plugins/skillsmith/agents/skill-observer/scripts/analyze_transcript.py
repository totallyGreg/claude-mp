#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
analyze_transcript.py — Skill gap detector for Claude Code session transcripts.

Reads a session JSONL file, extracts Skill tool call invocations, groups subsequent
tool calls by active skill, resolves skill name → source SKILL.md via marketplace.json,
and reports structural gaps (tool patterns not covered by the skill's SKILL.md).

Usage:
    uv run analyze_transcript.py --session <session-id-or-path> [--skill <name>] [--format json|markdown]

Examples:
    # Analyze by session ID (searches ~/.claude/projects/)
    uv run analyze_transcript.py --session 6c22a82a-be4e-4256-8641-99d1d0b78969

    # Analyze by path
    uv run analyze_transcript.py --session ~/.claude/projects/my-project/abc123.jsonl

    # Filter to a specific skill
    uv run analyze_transcript.py --session abc123 --skill skillsmith

    # JSON output
    uv run analyze_transcript.py --session abc123 --format json
"""

import json
import sys
import os
import glob
from pathlib import Path
from collections import defaultdict


# ============================================================================
# Session File Resolution
# ============================================================================

def find_session_file(session_id_or_path: str) -> Path | None:
    """Find session JSONL file by ID or direct path."""
    p = Path(session_id_or_path).expanduser()

    # Direct path
    if p.exists() and p.suffix == '.jsonl':
        return p

    # Search across project directories
    search_id = session_id_or_path.removesuffix('.jsonl')
    pattern = os.path.expanduser(f'~/.claude/projects/**/{search_id}.jsonl')
    matches = glob.glob(pattern, recursive=True)
    if matches:
        return Path(matches[0])

    return None


def list_recent_sessions(project_slug: str | None = None, limit: int = 10) -> list[Path]:
    """List recent session files, optionally filtered by project slug."""
    if project_slug:
        pattern = os.path.expanduser(f'~/.claude/projects/{project_slug}/*.jsonl')
    else:
        pattern = os.path.expanduser('~/.claude/projects/**/*.jsonl')

    files = glob.glob(pattern, recursive=True)
    return sorted([Path(f) for f in files], key=lambda p: p.stat().st_mtime, reverse=True)[:limit]


# ============================================================================
# Session Parsing
# ============================================================================

def parse_session(session_path: Path) -> list[dict]:
    """Parse JSONL session file into list of message dicts."""
    messages = []
    with open(session_path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                messages.append(msg)
            except json.JSONDecodeError as e:
                print(f"Warning: skipping malformed line {line_num}: {e}", file=sys.stderr)
    return messages


def extract_skill_invocations(messages: list[dict]) -> list[dict]:
    """
    Extract all Skill tool calls from assistant messages.
    Returns list of {skill: str, message_idx: int, timestamp: str, tool_call_id: str}
    """
    invocations = []
    for idx, msg in enumerate(messages):
        if msg.get('type') != 'assistant':
            continue
        content = msg.get('message', {}).get('content', [])
        if not isinstance(content, list):
            continue
        for block in content:
            if (isinstance(block, dict)
                    and block.get('type') == 'tool_use'
                    and block.get('name') == 'Skill'):
                skill_input = block.get('input', {})
                skill_name = skill_input.get('skill', '')
                invocations.append({
                    'skill': skill_name,
                    'message_idx': idx,
                    'timestamp': msg.get('timestamp', ''),
                    'tool_call_id': block.get('id', ''),
                })
    return invocations


def extract_tool_calls(messages: list[dict]) -> list[dict]:
    """
    Extract all tool_use blocks from assistant messages.
    Returns list of {name: str, input: dict, message_idx: int, timestamp: str}
    """
    tool_calls = []
    for idx, msg in enumerate(messages):
        if msg.get('type') != 'assistant':
            continue
        content = msg.get('message', {}).get('content', [])
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'tool_use':
                tool_calls.append({
                    'name': block.get('name', ''),
                    'input': block.get('input', {}),
                    'message_idx': idx,
                    'timestamp': msg.get('timestamp', ''),
                })
    return tool_calls


def group_tool_calls_by_skill(
    skill_invocations: list[dict],
    all_tool_calls: list[dict]
) -> dict[str, list[dict]]:
    """
    Group tool calls by the skill that was active when they were made.

    A skill is "active" from its invocation message until the next Skill invocation
    or end of session. Tool calls within the invocation message itself are included.

    Returns: {skill_name: [tool_call, ...]}
    """
    if not skill_invocations:
        return {}

    groups: dict[str, list[dict]] = defaultdict(list)

    # Build intervals: (start_msg_idx, end_msg_idx_exclusive, skill_name)
    intervals = []
    for i, inv in enumerate(skill_invocations):
        start = inv['message_idx']
        end = skill_invocations[i + 1]['message_idx'] if i + 1 < len(skill_invocations) else float('inf')
        intervals.append((start, end, inv['skill']))

    for tc in all_tool_calls:
        # Skip the Skill tool calls themselves
        if tc['name'] == 'Skill':
            continue
        for start, end, skill_name in intervals:
            if start <= tc['message_idx'] < end:
                groups[skill_name].append(tc)
                break

    return dict(groups)


# ============================================================================
# Marketplace Resolution
# ============================================================================

def find_marketplace_json(repo_root: Path) -> Path | None:
    """Find marketplace.json relative to repo root."""
    candidates = [
        repo_root / '.claude-plugin' / 'marketplace.json',
        repo_root / 'marketplace.json',
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def load_marketplace(marketplace_path: Path) -> dict:
    """Load and index marketplace.json by plugin name."""
    with open(marketplace_path) as f:
        data = json.load(f)

    index: dict[str, dict] = {}
    for plugin in data.get('plugins', []):
        name = plugin.get('name', '')
        if name:
            index[name] = plugin
    return index


def resolve_skill_to_source(skill_name: str, marketplace: dict, repo_root: Path) -> Path | None:
    """
    Resolve a skill name (e.g., "skillsmith:skillsmith" or "skillsmith") to
    its source SKILL.md path in the repo.

    Skill name formats:
    - "plugin-name:skill-name"  (plugin qualified)
    - "skill-name"              (unqualified — search all plugins)
    """
    if ':' in skill_name:
        plugin_part, skill_part = skill_name.split(':', 1)
    else:
        plugin_part = None
        skill_part = skill_name

    # If plugin qualified, look up directly
    if plugin_part and plugin_part in marketplace:
        plugin = marketplace[plugin_part]
        source_dir = (repo_root / plugin['source']).resolve()
        # Try skills subdirectory
        candidate = source_dir / 'skills' / skill_part / 'SKILL.md'
        if candidate.exists():
            return candidate.parent
        # Some plugins have skill in source root
        candidate = source_dir / 'SKILL.md'
        if candidate.exists():
            return source_dir

    # Unqualified — search all plugins
    for _, plugin in marketplace.items():
        source_dir = (repo_root / plugin['source']).resolve()
        candidate = source_dir / 'skills' / skill_part / 'SKILL.md'
        if candidate.exists():
            return candidate.parent

    return None


# ============================================================================
# Gap Analysis
# ============================================================================

def read_skill_content(skill_dir: Path) -> str:
    """Read SKILL.md and all reference files into a single text blob for gap checking."""
    parts = []

    skill_md = skill_dir / 'SKILL.md'
    if skill_md.exists():
        parts.append(skill_md.read_text())

    refs_dir = skill_dir / 'references'
    if refs_dir.exists():
        for ref_file in refs_dir.glob('*.md'):
            try:
                parts.append(ref_file.read_text())
            except Exception:
                pass

    return '\n'.join(parts)


def analyze_tool_call_gaps(
    tool_calls: list[dict],
    skill_content: str,
    skill_name: str,  # noqa: ARG001
) -> list[dict]:
    """
    Identify tool calls whose patterns are not covered in the skill's content.

    Gap detection heuristics:
    1. Files read/written that aren't mentioned in the skill docs
    2. Bash command topics (tools used) not referenced in the skill docs
    3. Tools used significantly that the skill doesn't mention at all
    """
    gaps = []
    skill_lower = skill_content.lower()

    # Count tool usage
    tool_counts: dict[str, int] = defaultdict(int)
    for tc in tool_calls:
        tool_counts[tc['name']] += 1

    # Gap 1: Tools used but never mentioned in skill docs
    tool_coverage_map = {
        'Bash': ['bash', '```bash', 'shell', 'command', 'run '],
        'Read': ['read', 'file_path', 'references/', 'skill.md'],
        'Write': ['write', 'create', 'generate', 'output'],
        'Edit': ['edit', 'modify', 'update', 'change'],
        'Grep': ['grep', 'search', 'find pattern', 'rg '],
        'Glob': ['glob', 'find files', 'pattern match'],
        'WebFetch': ['webfetch', 'url', 'http', 'documentation'],
        'WebSearch': ['websearch', 'search the web', 'look up'],
        'Agent': ['agent', 'subagent', 'spawn'],
    }

    for tool_name, count in tool_counts.items():
        if tool_name == 'Skill':
            continue
        coverage_terms = tool_coverage_map.get(tool_name, [tool_name.lower()])
        covered = any(term in skill_lower for term in coverage_terms)
        if not covered and count >= 2:
            gaps.append({
                'type': 'uncovered_tool',
                'tool': tool_name,
                'count': count,
                'description': f'{tool_name} used {count}x but not mentioned in skill docs',
                'suggestion': f'Add {tool_name} usage guidance or examples to SKILL.md or references/',
            })

    # Gap 2: Files accessed that skill doesn't mention
    accessed_files = set()
    for tc in tool_calls:
        if tc['name'] in ('Read', 'Write', 'Edit'):
            fp = tc['input'].get('file_path', '')
            if fp:
                # Normalize to filename only for checking
                filename = Path(fp).name
                accessed_files.add((fp, filename))

    uncovered_files = []
    for full_path, filename in accessed_files:
        if filename.lower() not in skill_lower and full_path not in skill_lower:
            # Only flag if it's not a very generic name
            if filename not in ('SKILL.md', 'README.md', 'plugin.json') and len(filename) > 4:
                uncovered_files.append(full_path)

    if len(uncovered_files) >= 2:
        sample = uncovered_files[:3]
        gaps.append({
            'type': 'uncovered_files',
            'tool': 'Read/Write/Edit',
            'count': len(uncovered_files),
            'description': f'{len(uncovered_files)} files accessed not mentioned in skill docs',
            'examples': sample,
            'suggestion': 'Add these file paths or patterns to the skill\'s reference documentation',
        })

    # Gap 3: Bash commands using patterns not in skill docs
    bash_patterns = defaultdict(int)
    for tc in tool_calls:
        if tc['name'] == 'Bash':
            cmd = tc['input'].get('command', '')
            # Identify the primary command
            first_word = cmd.strip().split()[0] if cmd.strip() else ''
            if first_word and first_word not in ('cd', 'echo', 'cat', 'ls'):
                bash_patterns[first_word] += 1

    for cmd, count in bash_patterns.items():
        if count >= 2 and cmd.lower() not in skill_lower:
            gaps.append({
                'type': 'uncovered_bash',
                'tool': 'Bash',
                'count': count,
                'description': f'`{cmd}` command used {count}x but not referenced in skill docs',
                'suggestion': f'Add `{cmd}` usage pattern to a reference file or SKILL.md examples',
            })

    return gaps


# ============================================================================
# Main Analysis
# ============================================================================

def analyze(
    session_path: Path,
    skill_filter: str | None,
    repo_root: Path,
    marketplace: dict,
) -> dict:
    """Run full transcript analysis. Returns structured result dict."""
    messages = parse_session(session_path)
    skill_invocations = extract_skill_invocations(messages)
    all_tool_calls = extract_tool_calls(messages)

    session_id = session_path.stem

    if not skill_invocations:
        return {
            'session_id': session_id,
            'session_path': str(session_path),
            'status': 'no_skills_detected',
            'message': 'No Skill tool calls found in this session. Skills must be invoked via the Skill tool to be tracked.',
            'skills': [],
            'gaps': [],
        }

    # Apply filter
    if skill_filter:
        skill_invocations = [s for s in skill_invocations if skill_filter in s['skill']]
        if not skill_invocations:
            return {
                'session_id': session_id,
                'session_path': str(session_path),
                'status': 'skill_not_found',
                'message': f'Skill "{skill_filter}" was not invoked in this session.',
                'skills': [],
                'gaps': [],
            }

    grouped = group_tool_calls_by_skill(skill_invocations, all_tool_calls)

    # Count invocations per skill
    invocation_counts: dict[str, int] = defaultdict(int)
    for inv in skill_invocations:
        invocation_counts[inv['skill']] += 1

    skills_report = []
    all_gaps = []

    seen_skills: set[str] = set()
    for inv in skill_invocations:
        skill_name: str = inv['skill']
        if skill_name in seen_skills:
            continue
        seen_skills.add(skill_name)

        tool_calls_for_skill = grouped.get(skill_name, [])
        tool_count_by_type: dict[str, int] = defaultdict(int)
        for tc in tool_calls_for_skill:
            tool_count_by_type[tc['name']] += 1

        # Resolve source
        source_dir = resolve_skill_to_source(skill_name, marketplace, repo_root)
        is_local = source_dir is not None

        skill_entry = {
            'skill': skill_name,
            'invocations': invocation_counts[skill_name],
            'tool_calls': len(tool_calls_for_skill),
            'tool_breakdown': dict(tool_count_by_type),
            'source_path': str(source_dir) if source_dir else None,
            'is_local': is_local,
        }
        skills_report.append(skill_entry)

        if is_local and tool_calls_for_skill:
            skill_content = read_skill_content(source_dir)
            gaps = analyze_tool_call_gaps(tool_calls_for_skill, skill_content, skill_name)
            for g in gaps:
                g['skill'] = skill_name
                g['source_path'] = str(source_dir)
            all_gaps.extend(gaps)
        elif not is_local:
            all_gaps.append({
                'skill': skill_name,
                'type': 'third_party',
                'tool': '-',
                'count': 0,
                'description': 'No local source found — this skill is third-party and cannot be improved here.',
                'suggestion': '-',
                'source_path': None,
            })

    return {
        'session_id': session_id,
        'session_path': str(session_path),
        'status': 'ok',
        'message': '',
        'total_messages': len(messages),
        'total_tool_calls': len(all_tool_calls),
        'skills': skills_report,
        'gaps': sorted(all_gaps, key=lambda g: g.get('count', 0), reverse=True),
    }


# ============================================================================
# Output Formatting
# ============================================================================

def format_markdown(result: dict) -> str:
    lines = []
    lines.append(f"## Skill Observer Report — {result['session_id']}")
    lines.append('')

    if result['status'] != 'ok':
        lines.append(f"**Status:** {result['message']}")
        return '\n'.join(lines)

    lines.append(f"**Session:** `{result['session_path']}`  ")
    lines.append(f"**Messages:** {result['total_messages']}  **Tool Calls:** {result['total_tool_calls']}")
    lines.append('')

    lines.append('### Skills Active in Session')
    lines.append('')
    lines.append('| Skill | Invocations | Tool Calls While Active | Source |')
    lines.append('|-------|-------------|------------------------|--------|')
    for s in result['skills']:
        source = f"`{Path(s['source_path']).relative_to(Path.cwd()) if s['source_path'] else 'third-party'}`"
        lines.append(f"| {s['skill']} | {s['invocations']} | {s['tool_calls']} | {source} |")
    lines.append('')

    if not result['gaps']:
        lines.append('### Structural Gaps')
        lines.append('')
        lines.append('No structural gaps detected.')
        return '\n'.join(lines)

    lines.append('### Structural Gaps')
    lines.append('')

    by_skill: dict[str, list] = defaultdict(list)
    for gap in result['gaps']:
        by_skill[gap['skill']].append(gap)

    for skill_name, gaps in by_skill.items():
        source = next((s['source_path'] for s in result['skills'] if s['skill'] == skill_name), None)
        source_label = f" → `{source}`" if source else ' (third-party)'
        lines.append(f"#### {skill_name}{source_label}")
        lines.append('')
        lines.append('| Gap | Tool | Occurrences | Suggested Fix |')
        lines.append('|-----|------|-------------|---------------|')
        for g in gaps:
            desc = g['description'].replace('|', '\\|')
            suggestion = g['suggestion'].replace('|', '\\|')
            lines.append(f"| {desc} | {g['tool']} | {g.get('count', '-')} | {suggestion} |")
        lines.append('')

    lines.append('### Recommended Improvements')
    lines.append('')
    seen = set()
    rank = 1
    for gap in result['gaps']:
        if gap['type'] == 'third_party':
            continue
        key = (gap['skill'], gap['type'], gap.get('tool', ''))
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"{rank}. **{gap['skill']}**: {gap['suggestion']}")
        rank += 1

    return '\n'.join(lines)


# ============================================================================
# CLI
# ============================================================================

def main():
    args = sys.argv[1:]
    session_arg = None
    skill_filter = None
    output_format = 'markdown'

    i = 0
    while i < len(args):
        if args[i] == '--session' and i + 1 < len(args):
            session_arg = args[i + 1]
            i += 2
        elif args[i] == '--skill' and i + 1 < len(args):
            skill_filter = args[i + 1]
            i += 2
        elif args[i] == '--format' and i + 1 < len(args):
            output_format = args[i + 1]
            i += 2
        elif args[i] in ('--help', '-h'):
            print(__doc__)
            sys.exit(0)
        else:
            i += 1

    if not session_arg:
        print('Error: --session <id|path> is required', file=sys.stderr)
        print('Usage: uv run analyze_transcript.py --session <id|path> [--skill <name>]', file=sys.stderr)
        sys.exit(1)

    # Find session file
    session_path = find_session_file(session_arg)
    if not session_path:
        print(f'Error: session not found: {session_arg}', file=sys.stderr)
        print('Search locations: ~/.claude/projects/**/<session-id>.jsonl', file=sys.stderr)
        sys.exit(1)

    # Find repo root and marketplace.json
    # Walk up from the script's location to find marketplace.json
    script_dir = Path(__file__).parent
    repo_root: Path | None = None
    marketplace_path: Path | None = None
    search = script_dir
    for _ in range(8):
        candidate = find_marketplace_json(search)
        if candidate:
            repo_root = search
            marketplace_path = candidate
            break
        search = search.parent

    if repo_root is None or marketplace_path is None:
        print('Warning: marketplace.json not found; installed→source resolution disabled', file=sys.stderr)
        marketplace = {}
        repo_root = Path.cwd()
    else:
        marketplace = load_marketplace(marketplace_path)

    # Run analysis
    result = analyze(session_path, skill_filter, repo_root, marketplace)

    if output_format == 'json':
        print(json.dumps(result, indent=2, default=str))
    else:
        print(format_markdown(result))


if __name__ == '__main__':
    main()
