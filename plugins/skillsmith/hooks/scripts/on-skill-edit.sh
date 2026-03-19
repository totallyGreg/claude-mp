#!/bin/bash
# on-skill-edit.sh — PostToolUse hook for Write|Edit
#
# Fires a quick skill evaluation when a SKILL.md file is edited in the
# repo source (not installed marketplace copies). Outputs a one-line score
# summary to stderr with exit 2 so Claude sees it in context.
#
# Exit codes:
#   0  — Not a SKILL.md edit or marketplace copy; silent
#   2  — SKILL.md eval complete; output passed to Claude's context

set -uo pipefail

# Read JSON from stdin
input=$(cat)

# Extract file_path using python3 (more portable than jq)
file_path=$(python3 -c "
import json, sys
try:
    data = json.loads(sys.stdin.read())
    print(data.get('tool_input', {}).get('file_path', ''))
except Exception:
    print('')
" <<< "$input" 2>/dev/null) || file_path=""

# Only process SKILL.md edits
if [[ "$file_path" != */SKILL.md ]]; then
    exit 0
fi

# Skip installed marketplace copies (~/.claude/plugins/)
home_plugins="${HOME}/.claude/plugins"
if [[ "$file_path" == "${home_plugins}"* ]]; then
    exit 0
fi

# Get the skill directory
skill_dir=$(dirname "$file_path")

# Find evaluate_skill.py
EVALUATE_SCRIPT="${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/evaluate_skill.py"

if [[ ! -f "$EVALUATE_SCRIPT" ]]; then
    exit 0
fi

# Run full evaluation with JSON output (quiet mode suppresses status messages)
eval_json=$(uv run "$EVALUATE_SCRIPT" "$skill_dir" --format json 2>/dev/null) || {
    echo "[skillsmith] Eval failed for ${skill_dir}" >&2
    exit 2
}

# Parse scores and format summary line
summary=$(python3 -c "
import json, sys
try:
    data = json.loads(sys.stdin.read())
    m = data.get('metrics', {})
    conc = m.get('conciseness', {}).get('score', '-')
    comp = m.get('complexity', {}).get('score', '-')
    spec = m.get('spec_compliance', {}).get('score', '-')
    disc = m.get('progressive_disclosure', {}).get('score', '-')
    desc = m.get('description_quality', {}).get('score', '-')
    overall = m.get('overall_score', '-')
    print(f'[skillsmith] Quick eval: Overall {overall}/100 (Conc:{conc} Comp:{comp} Spec:{spec} Disc:{disc} Desc:{desc}). Run /ss-evaluate for full report.')
except Exception as e:
    print(f'[skillsmith] Eval parse error: {e}')
" <<< "$eval_json" 2>/dev/null) || summary="[skillsmith] Eval parse failed"

echo "$summary" >&2
exit 2
