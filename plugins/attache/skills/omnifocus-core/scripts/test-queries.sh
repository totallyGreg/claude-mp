#!/usr/bin/env bash
# Smoke test for omnifocus-core JXA entry-point scripts.
#
# Runs one action from each script and asserts "success": true in the output.
# Run from any directory before bumping the plugin version.
#
# Usage:
#   bash skills/omnifocus-core/scripts/test-queries.sh
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

echo "omnifocus-core smoke tests"
echo "────────────────────────────"

# Phase 0: JXA anti-pattern validation (no OmniFocus required)
echo "  Anti-pattern checks:"
if command -v node >/dev/null 2>&1; then
    if node "$SCRIPTS_DIR/validate-jxa-patterns.js" "$SCRIPTS_DIR/libraries/jxa/" >/dev/null 2>&1; then
        echo "    PASS  JXA libraries — no anti-patterns"
        PASS=$((PASS + 1))
    else
        echo "    FAIL  JXA libraries — anti-patterns detected"
        node "$SCRIPTS_DIR/validate-jxa-patterns.js" "$SCRIPTS_DIR/libraries/jxa/" 2>&1 | sed 's/^/    /'
        FAIL=$((FAIL + 1))
    fi
    if node "$SCRIPTS_DIR/validate-jxa-patterns.js" "$SCRIPTS_DIR/manage_omnifocus.js" >/dev/null 2>&1; then
        echo "    PASS  manage_omnifocus.js — no anti-patterns"
        PASS=$((PASS + 1))
    else
        echo "    FAIL  manage_omnifocus.js — anti-patterns detected"
        FAIL=$((FAIL + 1))
    fi
    if node "$SCRIPTS_DIR/validate-jxa-patterns.js" "$SCRIPTS_DIR/gtd-queries.js" >/dev/null 2>&1; then
        echo "    PASS  gtd-queries.js — no anti-patterns"
        PASS=$((PASS + 1))
    else
        echo "    FAIL  gtd-queries.js — anti-patterns detected"
        FAIL=$((FAIL + 1))
    fi
else
    echo "    SKIP  Node.js not available — skipping anti-pattern checks"
fi

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
run_test "gtd-queries.js system-health"     scripts/gtd-queries.js    --action system-health
run_test "gtd-queries.js ai-agent-tasks"    scripts/gtd-queries.js    --action ai-agent-tasks
run_test "manage_omnifocus.js today"        scripts/manage_omnifocus.js today

# Phase 3: Tag management lifecycle (requires OmniFocus running)
echo "  Tag management:"
run_test "manage_omnifocus.js list-tags"    scripts/manage_omnifocus.js list-tags

# Create a throwaway tag via a temp task, then test rename/move/delete
TEST_TAG="__smoke_test_tag_$$"
run_test "create task with test tag"        scripts/manage_omnifocus.js create --name "__smoke_test_task_$$" --tags "$TEST_TAG" --create-tags
run_test "rename-tag"                       scripts/manage_omnifocus.js rename-tag --name "$TEST_TAG" --new-name "${TEST_TAG}_renamed"
run_test "move-tag to root"                 scripts/manage_omnifocus.js move-tag --name "${TEST_TAG}_renamed" --root
run_test "delete test task"                 scripts/manage_omnifocus.js delete --name "__smoke_test_task_$$"
run_test "delete-tag"                       scripts/manage_omnifocus.js delete-tag --name "${TEST_TAG}_renamed"

echo "────────────────────────────"
echo "  ${PASS} passed, ${FAIL} failed"

[ "$FAIL" -eq 0 ]
