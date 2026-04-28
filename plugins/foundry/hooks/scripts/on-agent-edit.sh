#!/bin/bash
# on-agent-edit.sh — PostToolUse hook for Write|Edit
#
# Fires a quick agent evaluation when an agent .md file is edited in the
# repo source (not installed marketplace copies). Outputs a one-line score
# summary to stderr with exit 2 so Claude sees it in context.
#
# Exit codes:
#   0  — Not an agent edit or marketplace copy; silent
#   2  — Agent eval complete; output passed to Claude's context

set -uo pipefail

input=$(cat)

file_path=$(python3 -c "
import json, sys
try:
    data = json.loads(sys.stdin.read())
    print(data.get('tool_input', {}).get('file_path', ''))
except Exception:
    print('')
" <<< "$input" 2>/dev/null) || file_path=""

# Only process .md files under an agents/ directory
if [[ "$file_path" != */agents/*.md && "$file_path" != */agents/*/AGENT.md ]]; then
    exit 0
fi

# Skip installed marketplace copies (~/.claude/plugins/)
home_plugins="${HOME}/.claude/plugins"
if [[ "$file_path" == "${home_plugins}"* ]]; then
    exit 0
fi

if [[ ! -f "$file_path" ]]; then
    exit 0
fi

EVALUATE_SCRIPT="${CLAUDE_PLUGIN_ROOT}/skills/agentsmith/scripts/evaluate_agent.py"

if [[ ! -f "$EVALUATE_SCRIPT" ]]; then
    exit 0
fi

summary=$(uv run "$EVALUATE_SCRIPT" "$file_path" --quick 2>/dev/null) || {
    exit 0
}

echo "$summary" >&2
exit 2
