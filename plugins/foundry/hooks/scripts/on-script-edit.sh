#!/bin/bash
# on-script-edit.sh — PostToolUse hook for Write|Edit
#
# Fires when a Python file inside a scripts/ directory is written or edited.
# Enforces two mechanical rules:
#   1. PEP 723 inline metadata block must be present (entry points only)
#   2. Banned CLI libraries (click, typer) must not be imported
#
# Exit codes:
#   0  — Not a scripts/*.py file, or no violations found; silent
#   2  — Violation found; message fed back to Claude's context

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

# Only process Python files inside a scripts/ directory
if [[ "$file_path" != */scripts/*.py ]]; then
    exit 0
fi

# Skip installed marketplace copies
home_plugins="${HOME}/.claude/plugins"
if [[ "$file_path" == "${home_plugins}"* ]]; then
    exit 0
fi

if [[ ! -f "$file_path" ]]; then
    exit 0
fi

violations=()

# Check 1: PEP 723 inline metadata block — entry points only. Package modules
# (no __main__ guard, __init__.py, conftest.py) are imported, never run by uv.
base=$(basename "$file_path")
is_entrypoint=false
if [[ "$base" != "__init__.py" && "$base" != "conftest.py" ]] \
    && grep -qE "^if __name__ == ['\"]__main__['\"]" "$file_path"; then
    is_entrypoint=true
fi
if $is_entrypoint && ! grep -q "# /// script" "$file_path"; then
    violations+=("missing PEP 723 header (# /// script ... # ///)")
fi

# Check 2: Banned CLI libraries
for lib in click typer; do
    if grep -qE "^(import ${lib}|from ${lib})" "$file_path"; then
        violations+=("banned CLI library '${lib}' imported — use argparse (stdlib) instead")
    fi
done

if [[ ${#violations[@]} -eq 0 ]]; then
    exit 0
fi

echo "[skillsmith] Script policy violation in $(basename "$file_path"):" >&2
for v in "${violations[@]}"; do
    echo "  ✗ ${v}" >&2
done
echo "  See references/python_uv_guide.md for the standards." >&2
exit 2
