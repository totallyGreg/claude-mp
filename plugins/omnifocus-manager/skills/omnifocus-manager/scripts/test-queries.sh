#!/usr/bin/env bash
# Smoke test for omnifocus-manager JXA entry-point scripts.
#
# Runs one action from each script and asserts "success": true in the output.
# Run from any directory before bumping the plugin version.
#
# Usage:
#   bash skills/omnifocus-manager/scripts/test-queries.sh
#
# Requirements: OmniFocus must be running with Automation permission granted.

set -uo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(dirname "$SCRIPTS_DIR")"

PASS=0
FAIL=0

run_test() {
    local name="$1"
    local script="$2"
    shift 2
    local args=("$@")

    local output
    output=$(cd "$SKILL_ROOT" && osascript -l JavaScript "$script" "${args[@]}" 2>&1)

    if echo "$output" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('success') else 1)" 2>/dev/null; then
        echo "  PASS  $name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  $name"
        echo "        output: $(echo "$output" | head -3)"
        FAIL=$((FAIL + 1))
    fi
}

echo "omnifocus-manager smoke tests"
echo "────────────────────────────"

# Phase 1: Library load tests (no OmniFocus required)
# Verifies that loadLibrary() resolves paths correctly from the skill root.
echo "  Library load checks:"
for lib in taskQuery taskMutation argParser dateUtils; do
    result=$(osascript -l JavaScript - << JSEOF
ObjC.import('Foundation');
const cwd = $.NSFileManager.defaultManager.currentDirectoryPath.js;
const path = cwd + '/scripts/libraries/jxa/${lib}.js';
const content = $.NSString.alloc.initWithContentsOfFileEncodingError(path, $.NSUTF8StringEncoding, null);
content ? 'ok' : 'fail: ' + path;
JSEOF
)
    if [ "$result" = "ok" ]; then
        echo "    PASS  load ${lib}.js"
        PASS=$((PASS + 1))
    else
        echo "    FAIL  load ${lib}.js — $result"
        FAIL=$((FAIL + 1))
    fi
done

# Phase 2: Live OmniFocus queries (requires OmniFocus running with Automation permission)
echo "  Live OmniFocus queries:"
run_test "gtd-queries.js system-health"   scripts/gtd-queries.js    --action system-health
run_test "manage_omnifocus.js today"      scripts/manage_omnifocus.js today

echo "────────────────────────────"
echo "  ${PASS} passed, ${FAIL} failed"

[ "$FAIL" -eq 0 ]
