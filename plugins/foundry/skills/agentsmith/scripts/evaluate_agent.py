#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pyyaml>=6.0.1",
# ]
# ///
"""
Agent quality evaluation engine for Claude Code agents.

Evaluates agent .md files across three quality dimensions:
- Trigger Effectiveness (0.35): How well the description triggers the agent
- System Prompt Quality (0.35): Quality of the system prompt body
- Coherence (0.30): Consistency between description, body, and tools

Usage:
    # Default evaluation
    uv run scripts/evaluate_agent.py <agent-path>

    # Per-dimension coaching with top-3 improvements
    uv run scripts/evaluate_agent.py <agent-path> --explain

    # One-line score summary for hook use
    uv run scripts/evaluate_agent.py <agent-path> --quick

    # JSON output
    uv run scripts/evaluate_agent.py <agent-path> --format json

    # Export version history table row
    uv run scripts/evaluate_agent.py <agent-path> --export-table-row --version 1.0.0

    # Update plugin-level README.md metrics
    uv run scripts/evaluate_agent.py <agent-path> --update-readme

Options:
    <agent-path>           Path to agent .md file or directory containing AGENT.md
    --explain              Per-dimension coaching with sub-metric detail and top-3 improvements
    --format json|text     Output format (default: text)
    --quick                One-line score summary for hook use (fast mode)
    --export-table-row     Emit markdown table row for README changelog
    --version VERSION      Version for table row export
    --update-readme        Update plugin-level README.md metrics section
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml

from utils import find_agent_file, find_plugin_root, load_baselines, save_baselines


# ============================================================================
# Agent File Parsing
# ============================================================================

def parse_agent_file(agent_path: Path) -> dict:
    """Parse an agent .md file into frontmatter dict and body string.

    Returns:
        {
            'frontmatter': dict,
            'body': str,
            'raw_content': str,
            'pattern': 'flat' | 'directory',
            'name': str,
            'path': str,
        }

    Raises:
        ValueError: if frontmatter is missing or malformed
    """
    content = agent_path.read_text(encoding='utf-8')

    if not content.startswith('---'):
        raise ValueError(f"No YAML frontmatter found in {agent_path}")

    parts = content.split('---', 2)
    if len(parts) < 3:
        raise ValueError(f"Malformed frontmatter in {agent_path}")

    frontmatter_text = parts[1].strip()
    body = parts[2].strip()

    try:
        frontmatter = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter: {e}")

    # Determine pattern: directory-based if file is AGENT.md, flat otherwise
    pattern = 'directory' if agent_path.name == 'AGENT.md' else 'flat'

    name = frontmatter.get('name', agent_path.stem)

    return {
        'frontmatter': frontmatter,
        'body': body,
        'raw_content': content,
        'pattern': pattern,
        'name': name,
        'path': str(agent_path),
    }


def strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks from text to prevent false positives."""
    return re.sub(r'```.*?```', '', text, flags=re.DOTALL)


def extract_examples(description: str) -> list[dict]:
    """Extract <example> blocks from a description string.

    Returns list of dicts with keys:
        'raw': full example text
        'user': user message (if found)
        'assistant': assistant message (if found)
        'commentary': commentary text (if found)
        'context': context line (if found)
    """
    examples = []
    pattern = re.compile(r'<example>(.*?)</example>', re.DOTALL)

    for match in pattern.finditer(description):
        block = match.group(1).strip()
        example = {'raw': block}

        # Extract context
        ctx_match = re.search(r'Context:\s*(.+)', block)
        if ctx_match:
            example['context'] = ctx_match.group(1).strip()

        # Extract user message
        user_match = re.search(r'user:\s*"([^"]+)"', block)
        if not user_match:
            user_match = re.search(r'user:\s*(.+)', block)
        if user_match:
            example['user'] = user_match.group(1).strip().strip('"')

        # Extract assistant message
        asst_match = re.search(r'assistant:\s*"([^"]+)"', block)
        if not asst_match:
            asst_match = re.search(r'assistant:\s*(.+)', block)
        if asst_match:
            example['assistant'] = asst_match.group(1).strip().strip('"')

        # Extract commentary
        comment_match = re.search(
            r'<commentary>(.*?)</commentary>', block, re.DOTALL
        )
        if comment_match:
            example['commentary'] = comment_match.group(1).strip()

        examples.append(example)

    return examples


# ============================================================================
# Dimension 1: Trigger Effectiveness (weight: 0.35)
# ============================================================================

def score_trigger_effectiveness(frontmatter: dict, examples: list[dict]) -> dict:
    """Score trigger effectiveness dimension.

    Sub-metrics:
        example_count (25pts), example_variety (25pts), commentary_presence (15pts),
        negative_triggers (15pts), phrasing_variety (10pts), description_specificity (10pts)
    """
    description = frontmatter.get('description', '')

    # --- Example count (25pts) ---
    n = len(examples)
    if n == 0:
        example_count_score = 0
    elif n == 1:
        example_count_score = 10
    elif n == 2:
        example_count_score = 15
    elif n == 3:
        example_count_score = 20
    else:
        example_count_score = 25

    # --- Example variety (25pts) ---
    # Check for explicit triggers ("user asks to X"), proactive triggers
    # ("after user does X"), implicit/edge-case triggers
    has_explicit = False
    has_proactive = False
    has_implicit = False

    explicit_patterns = [
        r'user\s+asks', r'user\s+wants', r'user\s+reports',
        r'user\s+has', r'user\s+says',
    ]
    proactive_patterns = [
        r'after\s+', r'proactively', r'automatically',
        r'agent\s+triggers', r'when\s+.*completes',
    ]
    implicit_patterns = [
        r'ambiguous', r'vague', r'unclear', r'cross-domain',
        r'edge\s*case', r'novel', r'implicit',
    ]

    for ex in examples:
        context = ex.get('context', '') + ' ' + ex.get('commentary', '')
        context_lower = context.lower()
        user_msg = (ex.get('user', '') or '').lower()
        combined = context_lower + ' ' + user_msg

        if any(re.search(p, combined) for p in explicit_patterns):
            has_explicit = True
        if any(re.search(p, combined) for p in proactive_patterns):
            has_proactive = True
        if any(re.search(p, combined) for p in implicit_patterns):
            has_implicit = True

    variety_types = sum([has_explicit, has_proactive, has_implicit])
    if variety_types >= 3:
        example_variety_score = 25
    elif variety_types == 2:
        example_variety_score = 18
    elif variety_types == 1:
        example_variety_score = 10
    else:
        example_variety_score = 0 if n == 0 else 5

    # --- Commentary presence (15pts) ---
    examples_with_commentary = sum(1 for ex in examples if ex.get('commentary'))
    if n > 0:
        commentary_score = int((examples_with_commentary / n) * 15)
    else:
        commentary_score = 0

    # --- Negative triggers (15pts) ---
    negative_patterns = [
        r'do\s+not', r"don't", r'when\s+not\s+to',
        r'skip', r"don't\s+use", r'not\s+for',
        r'avoid', r'not\s+intended\s+for',
    ]
    # Check outside of example blocks
    desc_outside_examples = re.sub(
        r'<example>.*?</example>', '', description, flags=re.DOTALL
    )
    has_negative = any(
        re.search(p, desc_outside_examples, re.IGNORECASE)
        for p in negative_patterns
    )
    negative_score = 15 if has_negative else 0

    # --- Phrasing variety (10pts) ---
    user_messages = [ex.get('user', '') for ex in examples if ex.get('user')]
    if len(user_messages) >= 2:
        # Check that user messages use different wording
        # Tokenize and check overlap
        token_sets = []
        for msg in user_messages:
            tokens = set(re.findall(r'\b\w{3,}\b', msg.lower()))
            token_sets.append(tokens)

        # Calculate average pairwise Jaccard distance
        pairwise_distances = []
        for i in range(len(token_sets)):
            for j in range(i + 1, len(token_sets)):
                union = token_sets[i] | token_sets[j]
                if union:
                    jaccard = len(token_sets[i] & token_sets[j]) / len(union)
                    pairwise_distances.append(1 - jaccard)

        avg_distance = (
            sum(pairwise_distances) / len(pairwise_distances)
            if pairwise_distances else 0
        )

        if avg_distance >= 0.7:
            phrasing_score = 10
        elif avg_distance >= 0.4:
            phrasing_score = 7
        else:
            phrasing_score = 3
    elif len(user_messages) == 1:
        phrasing_score = 3
    else:
        phrasing_score = 0

    # --- Description specificity (10pts) ---
    generic_phrases = [
        'helps the user', 'assists with', 'provides guidance',
        'general purpose', 'multipurpose',
    ]
    desc_lower = description.lower()
    is_too_generic = (
        any(p in desc_lower for p in generic_phrases)
        and len(description) < 200
    )

    if is_too_generic:
        specificity_score = 2
    elif len(description) > 100 and n >= 1:
        specificity_score = 10
    elif len(description) > 50:
        specificity_score = 6
    else:
        specificity_score = 3

    total = (
        example_count_score + example_variety_score + commentary_score
        + negative_score + phrasing_score + specificity_score
    )

    return {
        'score': min(100, total),
        'sub_metrics': {
            'example_count': {'score': example_count_score, 'max': 25, 'count': n},
            'example_variety': {
                'score': example_variety_score, 'max': 25,
                'types': {
                    'explicit': has_explicit,
                    'proactive': has_proactive,
                    'implicit': has_implicit,
                },
            },
            'commentary_presence': {
                'score': commentary_score, 'max': 15,
                'with_commentary': examples_with_commentary,
                'total': n,
            },
            'negative_triggers': {
                'score': negative_score, 'max': 15,
                'present': has_negative,
            },
            'phrasing_variety': {
                'score': phrasing_score, 'max': 10,
                'label': (
                    'good' if phrasing_score >= 7
                    else 'limited' if phrasing_score >= 3
                    else 'none'
                ),
            },
            'description_specificity': {
                'score': specificity_score, 'max': 10,
                'is_generic': is_too_generic,
            },
        },
    }


# ============================================================================
# Dimension 2: System Prompt Quality (weight: 0.35)
# ============================================================================

def score_system_prompt_quality(body: str) -> dict:
    """Score system prompt quality dimension.

    Sub-metrics:
        role_specificity (15pts), concrete_responsibilities (15pts),
        step_by_step_process (15pts), quality_standards (10pts),
        output_format (10pts), edge_case_handling (10pts),
        length_sweet_spot (15pts), structural_organization (10pts)
    """
    # Strip code blocks to avoid false positives in heuristic checks
    clean_body = strip_code_blocks(body)
    words = body.split()
    word_count = len(words)

    # --- Role specificity (15pts) ---
    # First paragraph should define a specific role
    paragraphs = [p.strip() for p in body.split('\n\n') if p.strip()]
    first_para = paragraphs[0] if paragraphs else ''
    first_para_lower = first_para.lower()

    generic_role_phrases = [
        'help the user', 'assist the user', 'general assistant',
        'helpful assistant',
    ]
    has_specific_role = (
        ('you are' in first_para_lower or 'your job' in first_para_lower
         or 'your role' in first_para_lower)
        and not any(p in first_para_lower for p in generic_role_phrases)
    )
    # Check for domain-specific language (at least 2 domain words)
    domain_indicators = len(re.findall(
        r'\b(?:orchestrat|analyz|evaluat|diagnos|triage|rout|manag|generat|'
        r'validat|configur|migrat|scaffold|audit|consolid|transpil|compil|'
        r'PKM|vault|GTD|kubernetes|gateway|terminal|shell|OmniFocus)\w*\b',
        first_para, re.IGNORECASE
    ))

    if has_specific_role and domain_indicators >= 2:
        role_score = 15
    elif has_specific_role or domain_indicators >= 2:
        role_score = 10
    elif domain_indicators >= 1:
        role_score = 6
    else:
        role_score = 3

    # --- Concrete responsibilities (15pts) ---
    # Look for numbered or bulleted lists
    bullet_lines = re.findall(r'^[\s]*[-*]\s+.+', clean_body, re.MULTILINE)
    numbered_lines = re.findall(r'^[\s]*\d+\.\s+.+', clean_body, re.MULTILINE)
    responsibility_items = len(bullet_lines) + len(numbered_lines)

    if responsibility_items >= 10:
        responsibility_score = 15
    elif responsibility_items >= 5:
        responsibility_score = 12
    elif responsibility_items >= 2:
        responsibility_score = 8
    else:
        responsibility_score = 3

    # --- Step-by-step process (15pts) ---
    process_indicators = [
        r'(?:step|phase)\s+\d', r'\d+\.\s+\*\*',
        r'##\s+.*(?:workflow|process|procedure)',
        r'###\s+.*(?:step|phase)',
    ]
    process_hits = sum(
        1 for p in process_indicators
        if re.search(p, clean_body, re.IGNORECASE | re.MULTILINE)
    )
    # Also check for sequential numbered steps (1. ... 2. ... 3. ...)
    sequential_steps = len(re.findall(
        r'^\s*\d+\.\s+', clean_body, re.MULTILINE
    ))

    if process_hits >= 2 or sequential_steps >= 5:
        process_score = 15
    elif process_hits >= 1 or sequential_steps >= 3:
        process_score = 10
    elif sequential_steps >= 1:
        process_score = 5
    else:
        process_score = 0

    # --- Quality standards (10pts) ---
    quality_patterns = [
        r'must\b', r'always\b', r'never\b', r'require',
        r'standard', r'criteria', r'quality',
        r'IMPORTANT', r'CRITICAL', r'MUST',
    ]
    quality_hits = sum(
        1 for p in quality_patterns
        if re.search(p, clean_body, re.MULTILINE)
    )
    if quality_hits >= 4:
        quality_score = 10
    elif quality_hits >= 2:
        quality_score = 7
    elif quality_hits >= 1:
        quality_score = 4
    else:
        quality_score = 0

    # --- Output format (10pts) ---
    output_patterns = [
        r'##\s+.*(?:output|format|report)',
        r'```(?:markdown|json|yaml)',
        r'return.*(?:report|result|output)',
        r'present\s+.*(?:as|in|using)',
    ]
    output_hits = sum(
        1 for p in output_patterns
        if re.search(p, clean_body, re.IGNORECASE | re.MULTILINE)
    )
    if output_hits >= 2:
        output_score = 10
    elif output_hits >= 1:
        output_score = 6
    else:
        output_score = 0

    # --- Edge case handling (10pts) ---
    edge_patterns = [
        r'edge\s+case', r'error\s+handling', r'fallback',
        r'if\s+.*fail', r'if\s+.*not\s+found', r'if\s+.*missing',
        r'if\s+.*absent', r'if\s+.*unavailable',
        r'when\s+.*fail', r'limitation',
    ]
    edge_hits = sum(
        1 for p in edge_patterns
        if re.search(p, clean_body, re.IGNORECASE | re.MULTILINE)
    )
    if edge_hits >= 3:
        edge_score = 10
    elif edge_hits >= 2:
        edge_score = 7
    elif edge_hits >= 1:
        edge_score = 4
    else:
        edge_score = 0

    # --- Length sweet spot (15pts) ---
    if word_count < 200:
        length_score = 0
    elif word_count < 500:
        length_score = 8
    elif word_count <= 3000:
        length_score = 15
    elif word_count <= 10000:
        length_score = 10
    else:
        length_score = 5

    length_label = (
        'too short' if word_count < 200
        else 'short' if word_count < 500
        else 'sweet spot' if word_count <= 3000
        else 'long' if word_count <= 10000
        else 'too long'
    )

    # --- Structural organization (10pts) ---
    headings = re.findall(r'^#{1,4}\s+.+', body, re.MULTILINE)
    heading_count = len(headings)

    if heading_count >= 5:
        structure_score = 10
    elif heading_count >= 3:
        structure_score = 7
    elif heading_count >= 1:
        structure_score = 4
    else:
        structure_score = 0

    total = (
        role_score + responsibility_score + process_score + quality_score
        + output_score + edge_score + length_score + structure_score
    )

    return {
        'score': min(100, total),
        'sub_metrics': {
            'role_specificity': {
                'score': role_score, 'max': 15,
                'specific': has_specific_role,
                'domain_indicators': domain_indicators,
            },
            'concrete_responsibilities': {
                'score': responsibility_score, 'max': 15,
                'items': responsibility_items,
            },
            'step_by_step_process': {
                'score': process_score, 'max': 15,
                'present': process_hits >= 1 or sequential_steps >= 3,
            },
            'quality_standards': {
                'score': quality_score, 'max': 10,
                'hits': quality_hits,
            },
            'output_format': {
                'score': output_score, 'max': 10,
                'defined': output_hits >= 1,
            },
            'edge_case_handling': {
                'score': edge_score, 'max': 10,
                'hits': edge_hits,
            },
            'length_sweet_spot': {
                'score': length_score, 'max': 15,
                'word_count': word_count,
                'label': length_label,
            },
            'structural_organization': {
                'score': structure_score, 'max': 10,
                'headings': heading_count,
            },
        },
    }


# ============================================================================
# Dimension 3: Coherence (weight: 0.30)
# ============================================================================

def _extract_action_verbs(text: str) -> set[str]:
    """Extract key action verbs/phrases from text."""
    verbs = set()
    patterns = [
        r'\b(analyz\w*)\b', r'\b(evaluat\w*)\b', r'\b(generat\w*)\b',
        r'\b(creat\w*)\b', r'\b(validat\w*)\b', r'\b(configur\w*)\b',
        r'\b(diagnos\w*)\b', r'\b(rout\w*)\b', r'\b(migrat\w*)\b',
        r'\b(scaffold\w*)\b', r'\b(orchest\w*)\b', r'\b(search\w*)\b',
        r'\b(updat\w*)\b', r'\b(manag\w*)\b', r'\b(monitor\w*)\b',
        r'\b(check\w*)\b', r'\b(review\w*)\b', r'\b(deploy\w*)\b',
        r'\b(load\w*)\b', r'\b(run\w*)\b', r'\b(scan\w*)\b',
        r'\b(detect\w*)\b', r'\b(fix\w*)\b', r'\b(merge\w*)\b',
        r'\b(profile\w*)\b', r'\b(coach\w*)\b', r'\b(triage\w*)\b',
    ]
    for p in patterns:
        for m in re.finditer(p, text, re.IGNORECASE):
            verbs.add(m.group(1).lower())
    return verbs


def score_coherence(
    frontmatter: dict, body: str, examples: list[dict]
) -> dict:
    """Score coherence dimension.

    Sub-metrics:
        example_body_alignment (30pts), body_example_coverage (25pts),
        tool_scope_fitness (25pts), terminology_consistency (20pts)
    """
    description = frontmatter.get('description', '')
    tools_declared = frontmatter.get('tools', [])
    clean_body = strip_code_blocks(body)

    # --- Example-body alignment (30pts) ---
    # Extract verbs from examples and check they appear in body
    example_verbs = set()
    for ex in examples:
        text = ' '.join([
            ex.get('user', ''), ex.get('assistant', ''),
            ex.get('commentary', ''),
        ])
        example_verbs.update(_extract_action_verbs(text))

    body_verbs = _extract_action_verbs(body)

    if example_verbs:
        alignment_ratio = len(example_verbs & body_verbs) / len(example_verbs)
    else:
        alignment_ratio = 0.0

    if alignment_ratio >= 0.7:
        alignment_score = 30
    elif alignment_ratio >= 0.5:
        alignment_score = 22
    elif alignment_ratio >= 0.3:
        alignment_score = 15
    elif example_verbs:
        alignment_score = 5
    else:
        alignment_score = 0

    # Track unaligned verbs for coaching
    unaligned_verbs = example_verbs - body_verbs

    # --- Body-example coverage (25pts) ---
    # Extract headings from body as major sections
    body_headings = re.findall(r'^##\s+(.+)', body, re.MULTILINE)

    # Check if examples reference content from body sections
    example_text_combined = ' '.join(
        ex.get('user', '') + ' ' + ex.get('commentary', '')
        for ex in examples
    ).lower()

    covered_headings = 0
    uncovered_headings = []
    for heading in body_headings:
        heading_words = set(re.findall(r'\b\w{4,}\b', heading.lower()))
        # Check if any heading words appear in example text
        if heading_words and (heading_words & set(
            re.findall(r'\b\w{4,}\b', example_text_combined)
        )):
            covered_headings += 1
        else:
            uncovered_headings.append(heading)

    if not body_headings:
        coverage_score = 15  # No headings to check
    else:
        coverage_ratio = covered_headings / len(body_headings)
        if coverage_ratio >= 0.6:
            coverage_score = 25
        elif coverage_ratio >= 0.3:
            coverage_score = 18
        elif coverage_ratio > 0:
            coverage_score = 10
        else:
            coverage_score = 5

    # --- Tool scope fitness (25pts) ---
    # Check if declared tools are referenced in body
    if tools_declared:
        tools_in_body = sum(
            1 for tool in tools_declared
            if re.search(r'\b' + re.escape(tool) + r'\b', body)
        )
        tool_ratio = tools_in_body / len(tools_declared)

        # Check for tools referenced in body but NOT declared
        common_tools = [
            'Read', 'Write', 'Edit', 'Bash', 'Grep', 'Glob',
            'AskUserQuestion', 'WebFetch', 'WebSearch',
        ]
        body_referenced_tools = [
            t for t in common_tools
            if re.search(r'\b' + re.escape(t) + r'\b', body)
        ]
        undeclared_tools = [
            t for t in body_referenced_tools if t not in tools_declared
        ]

        if tool_ratio >= 0.8 and not undeclared_tools:
            tool_score = 25
        elif tool_ratio >= 0.5:
            tool_score = 18
        elif tool_ratio > 0:
            tool_score = 10
        else:
            tool_score = 5
    else:
        # No tools array — full access implied; check if body scope justifies it
        body_tool_refs = len(re.findall(
            r'\b(?:Read|Write|Edit|Bash|Grep|Glob|WebFetch)\b', body
        ))
        if body_tool_refs >= 3:
            tool_score = 20  # Body references tools but none declared
        else:
            tool_score = 15  # Ambiguous

        tools_in_body = 0
        undeclared_tools = []

    # --- Terminology consistency (20pts) ---
    # Extract key terms from description (outside examples)
    desc_outside = re.sub(
        r'<example>.*?</example>', '', description, flags=re.DOTALL
    )
    desc_terms = set(re.findall(r'\b[A-Za-z]{4,}\b', desc_outside.lower()))
    body_terms = set(re.findall(r'\b[A-Za-z]{4,}\b', clean_body.lower()))

    # Filter to meaningful terms (remove common words)
    stopwords = {
        'this', 'that', 'with', 'from', 'will', 'have', 'been', 'when',
        'what', 'where', 'which', 'should', 'would', 'could', 'does',
        'about', 'into', 'also', 'more', 'most', 'some', 'each',
        'than', 'them', 'then', 'they', 'their', 'there', 'these',
        'your', 'used', 'using', 'uses', 'user', 'agent', 'tool',
    }
    desc_terms -= stopwords
    body_terms -= stopwords

    if desc_terms:
        term_overlap = len(desc_terms & body_terms) / len(desc_terms)
    else:
        term_overlap = 0.0

    if term_overlap >= 0.6:
        term_score = 20
    elif term_overlap >= 0.4:
        term_score = 14
    elif term_overlap >= 0.2:
        term_score = 8
    else:
        term_score = 3

    total = alignment_score + coverage_score + tool_score + term_score

    return {
        'score': min(100, total),
        'sub_metrics': {
            'example_body_alignment': {
                'score': alignment_score, 'max': 30,
                'ratio': round(alignment_ratio, 2),
                'unaligned': sorted(unaligned_verbs)[:5],
                'label': 'good' if alignment_score >= 22 else 'gaps found',
            },
            'body_example_coverage': {
                'score': coverage_score, 'max': 25,
                'total_headings': len(body_headings),
                'covered': covered_headings,
                'uncovered': uncovered_headings[:5],
            },
            'tool_scope_fitness': {
                'score': tool_score, 'max': 25,
                'declared': len(tools_declared) if tools_declared else 0,
                'referenced_in_body': tools_in_body,
                'undeclared': undeclared_tools[:5] if tools_declared else [],
            },
            'terminology_consistency': {
                'score': term_score, 'max': 20,
                'overlap_ratio': round(term_overlap, 2),
            },
        },
    }


# ============================================================================
# Overall Score Calculation
# ============================================================================

DIMENSION_WEIGHTS = {
    'trigger_effectiveness': 0.35,
    'system_prompt_quality': 0.35,
    'coherence': 0.30,
}


def calculate_overall_score(
    trigger: dict, prompt: dict, coherence: dict
) -> int:
    """Calculate weighted overall score."""
    overall = (
        trigger['score'] * DIMENSION_WEIGHTS['trigger_effectiveness']
        + prompt['score'] * DIMENSION_WEIGHTS['system_prompt_quality']
        + coherence['score'] * DIMENSION_WEIGHTS['coherence']
    )
    return int(overall)


def evaluate_agent(agent_path: Path) -> dict:
    """Run full evaluation on an agent file.

    Returns complete metrics dict.
    """
    parsed = parse_agent_file(agent_path)
    frontmatter = parsed['frontmatter']
    body = parsed['body']
    description = frontmatter.get('description', '')
    examples = extract_examples(description)

    trigger = score_trigger_effectiveness(frontmatter, examples)
    prompt = score_system_prompt_quality(body)
    coherence = score_coherence(frontmatter, body, examples)
    overall = calculate_overall_score(trigger, prompt, coherence)

    return {
        'agent': parsed['name'],
        'path': parsed['path'],
        'pattern': parsed['pattern'],
        'metrics': {
            'trigger_effectiveness': trigger,
            'system_prompt_quality': prompt,
            'coherence': coherence,
            'overall_score': overall,
        },
        'baseline_delta': None,  # Populated by baseline comparison
    }


# ============================================================================
# Baseline Comparison
# ============================================================================

def compare_with_baseline(result: dict, agent_path: Path) -> dict:
    """Compare evaluation results against stored baseline.

    Updates result['baseline_delta'] in place and manages baseline file.
    """
    plugin_root = find_plugin_root(str(agent_path))
    if plugin_root is None:
        result['baseline_delta'] = None
        return result

    baselines = load_baselines(plugin_root)
    agent_name = result['agent']
    current_score = result['metrics']['overall_score']

    if agent_name in baselines:
        baseline_score = baselines[agent_name].get('overall_score', 0)
        result['baseline_delta'] = current_score - baseline_score
    else:
        result['baseline_delta'] = None  # First run

    # Update baseline
    baselines[agent_name] = {
        'overall_score': current_score,
        'trigger_effectiveness': result['metrics']['trigger_effectiveness']['score'],
        'system_prompt_quality': result['metrics']['system_prompt_quality']['score'],
        'coherence': result['metrics']['coherence']['score'],
        'last_evaluated': datetime.now().strftime('%Y-%m-%d'),
    }
    save_baselines(plugin_root, baselines)

    return result


# ============================================================================
# Output Formatting
# ============================================================================

def format_score_bar(score: int, width: int = 20) -> str:
    """Format score as visual bar."""
    filled = int((score / 100) * width)
    empty = width - filled
    return f"[{'█' * filled}{'░' * empty}] {score}/100"


def print_quick_output(result: dict) -> None:
    """Print one-line score summary for hook use."""
    m = result['metrics']
    trig = m['trigger_effectiveness']['score']
    prompt = m['system_prompt_quality']['score']
    coher = m['coherence']['score']
    overall = m['overall_score']
    print(
        f"[agentsmith] Quick eval: Overall {overall}/100 "
        f"(Trig:{trig} Prompt:{prompt} Coher:{coher})"
    )


def print_text_output(result: dict) -> None:
    """Print default text evaluation output."""
    m = result['metrics']
    trig = m['trigger_effectiveness']
    prompt = m['system_prompt_quality']
    coher = m['coherence']

    print(f"\nAgent: {result['agent']}")
    print(f"Path: {result['path']}")
    print(f"Pattern: {result['pattern']}")
    print()

    # Trigger Effectiveness
    trig_sub = trig['sub_metrics']
    print(f"Trigger Effectiveness:  {trig['score']}/100")
    ex_count = trig_sub['example_count']
    ex_var = trig_sub['example_variety']
    types_list = []
    if ex_var['types']['explicit']:
        types_list.append('explicit')
    if ex_var['types']['proactive']:
        types_list.append('proactive')
    if ex_var['types']['implicit']:
        types_list.append('implicit')
    types_str = ', '.join(types_list) if types_list else 'none'
    print(
        f"  Examples: {ex_count['count']} "
        f"(types: {types_str})"
    )
    comm = trig_sub['commentary_presence']
    print(f"  Commentary: {comm['with_commentary']}/{comm['total']} examples")
    neg = trig_sub['negative_triggers']
    print(f"  Negative triggers: {'yes' if neg['present'] else 'no'}")
    phr = trig_sub['phrasing_variety']
    print(f"  Phrasing variety: {phr['label']}")
    print()

    # System Prompt Quality
    prompt_sub = prompt['sub_metrics']
    print(f"System Prompt Quality:  {prompt['score']}/100")
    role = prompt_sub['role_specificity']
    print(f"  Role: {'specific' if role['specific'] else 'generic'}")
    proc = prompt_sub['step_by_step_process']
    print(f"  Process steps: {'yes' if proc['present'] else 'no'}")
    qual = prompt_sub['quality_standards']
    print(f"  Quality standards: {'yes' if qual['hits'] >= 2 else 'no'}")
    length = prompt_sub['length_sweet_spot']
    print(f"  Word count: {length['word_count']} ({length['label']})")
    print()

    # Coherence
    coher_sub = coher['sub_metrics']
    print(f"Coherence:              {coher['score']}/100")
    align = coher_sub['example_body_alignment']
    print(f"  Example-body alignment: {align['label']}")
    tool = coher_sub['tool_scope_fitness']
    print(f"  Tool scope: {tool['declared']} declared, {tool['referenced_in_body']} referenced")
    print()

    # Overall
    print(f"Overall:                {m['overall_score']}/100")
    print()

    # Baseline
    delta = result.get('baseline_delta')
    if delta is None:
        print("Baseline: first run")
    elif delta == 0:
        print("Baseline: no change from baseline")
    elif delta > 0:
        print(f"Baseline: +{delta} from baseline")
    else:
        print(f"Baseline: {delta} from baseline (REGRESSION)")
    print()


def print_explain_output(result: dict) -> None:
    """Print per-dimension coaching with top-3 improvements."""
    m = result['metrics']
    overall = m['overall_score']

    print(f"\n{'='*60}")
    print(f"Agent Evaluation: {result['agent']} — Explain Mode")
    print(f"{'='*60}\n")

    # Brief overview
    print("Quality Scores:")
    print(f"  Trigger:    {format_score_bar(m['trigger_effectiveness']['score'])}")
    print(f"  Prompt:     {format_score_bar(m['system_prompt_quality']['score'])}")
    print(f"  Coherence:  {format_score_bar(m['coherence']['score'])}")
    print(f"  Overall:    {format_score_bar(overall)}")
    print()

    improvements = []  # (delta, label)

    # ── TRIGGER EFFECTIVENESS ───────────────────────────────────────────────
    trig = m['trigger_effectiveness']
    trig_sub = trig['sub_metrics']
    trig_score = trig['score']

    print(f"Trigger Effectiveness Score: {trig_score}/100\n")
    print("  Sub-metrics:")
    for name, sub in trig_sub.items():
        label = name.replace('_', ' ').title()
        print(f"    {label}: {sub['score']}/{sub['max']}")
    print()

    trig_gap = 100 - trig_score
    if trig_gap > 0:
        print("  To improve:")
        ex_count = trig_sub['example_count']
        if ex_count['count'] < 4:
            print(f"    - Add more examples (currently {ex_count['count']}, need 4+ for full score)")
        ex_var = trig_sub['example_variety']
        missing_types = [
            t for t, present in ex_var['types'].items() if not present
        ]
        if missing_types:
            print(f"    - Add {', '.join(missing_types)} trigger examples")
        comm = trig_sub['commentary_presence']
        if comm['with_commentary'] < comm['total']:
            print(f"    - Add <commentary> blocks to all examples ({comm['with_commentary']}/{comm['total']})")
        neg = trig_sub['negative_triggers']
        if not neg['present']:
            print("    - Add negative trigger clause (\"Do NOT use this agent for...\")")
        phr = trig_sub['phrasing_variety']
        if phr['score'] < 7:
            print("    - Vary user message wording across examples")

        delta = int(trig_gap * DIMENSION_WEIGHTS['trigger_effectiveness'])
        if delta > 0:
            improvements.append((delta, f"Improve trigger effectiveness -> +{delta} overall"))
    else:
        print("  Nothing to improve -- already at 100")
    print()

    # ── SYSTEM PROMPT QUALITY ───────────────────────────────────────────────
    prompt = m['system_prompt_quality']
    prompt_sub = prompt['sub_metrics']
    prompt_score = prompt['score']

    print(f"System Prompt Quality Score: {prompt_score}/100\n")
    print("  Sub-metrics:")
    for name, sub in prompt_sub.items():
        label = name.replace('_', ' ').title()
        extra = ''
        if name == 'length_sweet_spot':
            extra = f" ({sub['word_count']} words, {sub['label']})"
        elif name == 'structural_organization':
            extra = f" ({sub['headings']} headings)"
        print(f"    {label}: {sub['score']}/{sub['max']}{extra}")
    print()

    prompt_gap = 100 - prompt_score
    if prompt_gap > 0:
        print("  To improve:")
        role = prompt_sub['role_specificity']
        if not role['specific']:
            print("    - Start body with a specific role definition (\"You are a ... that ...\")")
        resp = prompt_sub['concrete_responsibilities']
        if resp['items'] < 5:
            print(f"    - Add bulleted/numbered responsibilities ({resp['items']} found, need 5+)")
        proc = prompt_sub['step_by_step_process']
        if not proc['present']:
            print("    - Document a step-by-step workflow or process")
        qual = prompt_sub['quality_standards']
        if qual['hits'] < 2:
            print("    - Add measurable quality standards (MUST, ALWAYS, NEVER)")
        out = prompt_sub['output_format']
        if not out['defined']:
            print("    - Define expected output format (## Output Format section)")
        edge = prompt_sub['edge_case_handling']
        if edge['hits'] < 2:
            print("    - Document edge cases and error handling")
        length = prompt_sub['length_sweet_spot']
        if length['label'] in ('too short', 'short'):
            print(f"    - Expand body ({length['word_count']} words, aim for 500-3000)")
        elif length['label'] in ('long', 'too long'):
            print(f"    - Trim body ({length['word_count']} words, aim for 500-3000)")
        struct = prompt_sub['structural_organization']
        if struct['headings'] < 3:
            print(f"    - Add more markdown headings ({struct['headings']} found, need 3+)")

        delta = int(prompt_gap * DIMENSION_WEIGHTS['system_prompt_quality'])
        if delta > 0:
            improvements.append((delta, f"Improve system prompt quality -> +{delta} overall"))
    else:
        print("  Nothing to improve -- already at 100")
    print()

    # ── COHERENCE ───────────────────────────────────────────────────────────
    coher = m['coherence']
    coher_sub = coher['sub_metrics']
    coher_score = coher['score']

    print(f"Coherence Score: {coher_score}/100\n")
    print("  Sub-metrics:")
    for name, sub in coher_sub.items():
        label = name.replace('_', ' ').title()
        print(f"    {label}: {sub['score']}/{sub['max']}")
    print()

    coher_gap = 100 - coher_score
    if coher_gap > 0:
        print("  To improve:")
        align = coher_sub['example_body_alignment']
        if align['unaligned']:
            verbs = ', '.join(align['unaligned'][:3])
            print(f"    - Body missing actions from examples: {verbs}")
        cov = coher_sub['body_example_coverage']
        if cov['uncovered']:
            sections = ', '.join(cov['uncovered'][:3])
            print(f"    - Add examples covering body sections: {sections}")
        tool = coher_sub['tool_scope_fitness']
        if tool['undeclared']:
            tools_str = ', '.join(tool['undeclared'][:3])
            print(f"    - Add undeclared tools to frontmatter: {tools_str}")
        term = coher_sub['terminology_consistency']
        if term['overlap_ratio'] < 0.6:
            print(f"    - Align terminology between description and body (overlap: {term['overlap_ratio']:.0%})")

        delta = int(coher_gap * DIMENSION_WEIGHTS['coherence'])
        if delta > 0:
            improvements.append((delta, f"Improve coherence -> +{delta} overall"))
    else:
        print("  Nothing to improve -- already at 100")
    print()

    # ── TOP-3 SUMMARY ─────────────────────────────────────────────────────
    improvements.sort(reverse=True)
    print(f"{'='*60}")
    print("Top improvements:")
    if not improvements:
        print("  All dimensions at 100 -- no improvements needed")
    else:
        for i, (delta, label) in enumerate(improvements[:3], 1):
            print(f"  {i}. {label}")
        total_delta = sum(d for d, _ in improvements[:3])
        estimated = min(100, overall + total_delta)
        print(f"\n  Estimated overall: {overall} -> {estimated}")
    print()


def print_json_output(result: dict) -> None:
    """Print JSON evaluation output."""
    print(json.dumps(result, indent=2))


# ============================================================================
# README Update
# ============================================================================

def _generate_agent_metrics_content(metrics: dict, today: str) -> str:
    """Generate metrics section body for plugin README.

    Returns string starting with newline, suitable for section replacement.
    """
    trig = metrics['trigger_effectiveness']['score']
    prompt = metrics['system_prompt_quality']['score']
    coher = metrics['coherence']['score']
    overall = metrics['overall_score']

    def _interp(score):
        if score >= 95:
            return 'Excellent'
        elif score >= 80:
            return 'Good'
        elif score >= 60:
            return 'Fair'
        return 'Needs work'

    return (
        f'\n\n**Score: {overall}/100** ({_interp(overall)}) — {today}\n\n'
        '| Trigger | Prompt | Coherence |\n'
        '|---------|--------|-----------|\n'
        f'| {trig} | {prompt} | {coher} |\n'
    )


def _find_agent_section_range(content: str, agent_name: str):
    """Find start/end of ## Agent: <name> section in README."""
    pattern = rf'(?m)^## Agent: {re.escape(agent_name)}\s*$'
    match = re.search(pattern, content)
    if not match:
        return None, None

    start = match.start()
    rest = content[match.end():]
    next_h2 = re.search(r'(?m)^## (?!#)', rest)
    end = match.end() + next_h2.start() if next_h2 else len(content)

    return start, end


def update_plugin_readme_agent_metrics(agent_path: Path, result: dict) -> Path | None:
    """Update the plugin-level README.md with agent metrics.

    Returns path to updated README, or None if skipped.
    """
    plugin_root = find_plugin_root(str(agent_path))
    if plugin_root is None:
        print(f"No plugin root found for {agent_path} -- skipping README update",
              file=sys.stderr)
        return None

    plugin_readme = plugin_root / 'README.md'
    today = datetime.now().strftime('%Y-%m-%d')
    metrics_content = _generate_agent_metrics_content(
        result['metrics'], today
    )
    agent_name = result['agent']

    if plugin_readme.exists():
        content = plugin_readme.read_text(encoding='utf-8')
    else:
        content = f'# {plugin_root.name}\n'

    start, end = _find_agent_section_range(content, agent_name)

    if start is not None:
        # Section exists -- replace ### Current Metrics
        section = content[start:end]
        pattern = r'(?ms)^(### Current Metrics)(.*?)(?=\n### |\n## |\Z)'
        updated_section, n = re.subn(
            pattern,
            lambda m: m.group(1) + metrics_content,
            section,
        )
        if n == 0:
            heading_end = section.index('\n') + 1 if '\n' in section else len(section)
            updated_section = (
                section[:heading_end]
                + '\n### Current Metrics' + metrics_content
                + section[heading_end:]
            )
        content = content[:start] + updated_section + content[end:]
    else:
        # Append new section
        new_section = (
            f'\n## Agent: {agent_name}\n'
            f'\n### Current Metrics{metrics_content}'
            f'\n### Version History\n\n'
            f'| Version | Date | Issue | Summary | Trigger | Prompt | Coherence | Score |\n'
            f'|---------|------|-------|---------|---------|--------|-----------|-------|\n\n'
            f'**Metric Legend:** Trigger=Trigger Effectiveness, '
            f'Prompt=System Prompt Quality, Coherence=Coherence (0-100 scale)\n'
        )
        content = content.rstrip() + '\n' + new_section

    plugin_readme.write_text(content, encoding='utf-8')
    return plugin_readme


# ============================================================================
# Export Table Row
# ============================================================================

def export_table_row(result: dict, version: str) -> str:
    """Generate a markdown table row for README version history."""
    today = datetime.now().strftime('%Y-%m-%d')
    m = result['metrics']
    trig = m['trigger_effectiveness']['score']
    prompt = m['system_prompt_quality']['score']
    coher = m['coherence']['score']
    overall = m['overall_score']
    agent_name = result['agent']
    summary = f"{agent_name} v{version}"

    return (
        f"| {version} | {today} | - | {summary} "
        f"| {trig} | {prompt} | {coher} | {overall} |"
    )


# ============================================================================
# CLI
# ============================================================================

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Agent quality evaluation engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        'agent_path',
        help='Path to agent .md file or directory containing AGENT.md',
    )
    parser.add_argument(
        '--explain', action='store_true',
        help='Per-dimension coaching with sub-metric detail and top-3 improvements',
    )
    parser.add_argument(
        '--format', dest='output_format', choices=['json', 'text'],
        default='text', help='Output format (default: text)',
    )
    parser.add_argument(
        '--quick', action='store_true',
        help='One-line score summary for hook use',
    )
    parser.add_argument(
        '--export-table-row', action='store_true',
        help='Emit markdown table row for README changelog',
    )
    parser.add_argument(
        '--version', dest='version_number',
        help='Version for table row export',
    )
    parser.add_argument(
        '--update-readme', action='store_true',
        help='Update plugin-level README.md metrics section',
    )

    args = parser.parse_args()

    # Validate flag compatibility
    if args.explain and args.quick:
        print("Error: --explain is incompatible with --quick", file=sys.stderr)
        sys.exit(1)

    if args.export_table_row and not args.version_number:
        print("Error: --export-table-row requires --version", file=sys.stderr)
        sys.exit(1)

    try:
        # Resolve agent file
        agent_file = find_agent_file(args.agent_path)

        # Run evaluation
        result = evaluate_agent(agent_file)

        # Baseline comparison
        result = compare_with_baseline(result, agent_file)

        # Export table row mode
        if args.export_table_row:
            print(export_table_row(result, args.version_number))
            sys.exit(0)

        # Update README mode
        if args.update_readme:
            readme_path = update_plugin_readme_agent_metrics(agent_file, result)
            if readme_path:
                print(f"Plugin README updated: {readme_path}")
                print(f"  Agent: {result['agent']}")
                print(f"  Overall score: {result['metrics']['overall_score']}/100")
            sys.exit(0)

        # Output
        if args.quick:
            print_quick_output(result)
        elif args.output_format == 'json':
            print_json_output(result)
        elif args.explain:
            print_explain_output(result)
        else:
            print_text_output(result)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
