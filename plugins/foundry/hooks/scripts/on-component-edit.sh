#!/bin/bash
# on-component-edit.sh — PostToolUse hook for Write|Edit
#
# Warns (does not write) when a plugin component is added or changed so the
# plugin README's autogen Components inventory can be refreshed. Fires on
# SKILL.md, agent .md/AGENT.md, and command .md edits in the repo source
# (not installed marketplace copies).
#
# Warn-only by design: it never rewrites the README. It prints the exact
# --update-components command to run.
#
# Exit codes:
#   0  — Not a component edit or marketplace copy; silent
#   2  — Component edit detected; advisory passed to Claude's context

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

# Only process plugin component files
case "$file_path" in
    */SKILL.md|*/agents/*.md|*/agents/*/AGENT.md|*/commands/*.md) ;;
    *) exit 0 ;;
esac

# Skip installed marketplace copies (~/.claude/plugins/)
home_plugins="${HOME}/.claude/plugins"
if [[ "$file_path" == "${home_plugins}"* ]]; then
    exit 0
fi

EVALUATE_SCRIPT="${CLAUDE_PLUGIN_ROOT:-}/skills/skillsmith/scripts/evaluate_skill.py"
if [[ ! -f "$EVALUATE_SCRIPT" ]]; then
    exit 0
fi

dir=$(dirname "$file_path")

echo "[skillsmith] Component changed — plugin README Components inventory may be stale. Refresh with: uv run \"$EVALUATE_SCRIPT\" \"$dir\" --update-components" >&2
exit 2
