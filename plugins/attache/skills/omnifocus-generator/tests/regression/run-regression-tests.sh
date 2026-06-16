#!/bin/bash
# D8.8 — Regression suite for the post-emit validation pipeline.
# Confirms each fixture is caught (or passes) at the expected layer.
#
# Coverage:
#   - bundle-coherence-mismatch: D8.4 (manifest declares action; .js missing constructor)
#   - smoke-load-undefined-global: D8.6 (action references undefined global)
#   - smoke-load-passing: positive control (should pass both)
#
# Out of scope (would require setting up tsc/eslint test harnesses):
#   - Pre-emit TS errors (Layer 2a)
#   - Pre-emit lint errors (Layer 2b)
#   - Pre-emit antipattern errors (Layer 2c)
#   These are exercised indirectly when the generator runs against real specs.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Walk up twice: regression/ → tests/ → omnifocus-generator/
GENERATOR_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
VALIDATE="$GENERATOR_DIR/scripts/validate-plugin.sh"
SMOKE="$GENERATOR_DIR/scripts/smoke-load.js"
FIXTURES="$SCRIPT_DIR/fixtures"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

# Test helper: assert <description> <expected-result> <actual-exit-code>
#   expected-result: 0 (pass) or non-zero (fail)
assert() {
    local description="$1"
    local expected="$2"
    local actual="$3"

    if [ "$expected" = "$actual" ] || ( [ "$expected" != "0" ] && [ "$actual" != "0" ] ); then
        echo -e "${GREEN}  ✅ PASS${NC} — $description"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}  ❌ FAIL${NC} — $description (expected exit $expected, got $actual)"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== D8.8 Regression Suite ==="
echo ""

# ─── Test 1: bundle-coherence-mismatch should FAIL D8.4 ───
echo "Test 1: bundle-coherence-mismatch (D8.4)"
bash "$VALIDATE" "$FIXTURES/bundle-coherence-mismatch.omnifocusjs" > /tmp/test1.out 2>&1
EXIT=$?
if grep -q "Bundle coherence: 1 error" /tmp/test1.out && grep -q "does not contain 'new PlugIn.Action(' constructor" /tmp/test1.out; then
    assert "D8.4 rejects manifest/code mismatch with correct error message" 1 "$EXIT"
else
    echo -e "${RED}  ❌ FAIL${NC} — D8.4 did not produce expected error message"
    FAIL=$((FAIL + 1))
    echo "Output excerpt:"
    grep -E "❌|coherence" /tmp/test1.out | head -3 | sed 's/^/    /'
fi
rm -f /tmp/test1.out
echo ""

# ─── Test 2: smoke-load-undefined-global should FAIL D8.6 ───
echo "Test 2: smoke-load-undefined-global (D8.6)"
node "$SMOKE" "$FIXTURES/smoke-load-undefined-global.omnifocusjs" > /tmp/test2.out 2>&1
EXIT=$?
if grep -q "flattenedTaks" /tmp/test2.out; then
    assert "D8.6 smoke-load rejects undefined-global reference (flattenedTaks typo)" 1 "$EXIT"
else
    echo -e "${RED}  ❌ FAIL${NC} — D8.6 did not surface flattenedTaks reference error"
    FAIL=$((FAIL + 1))
    cat /tmp/test2.out | head -5 | sed 's/^/    /'
fi
rm -f /tmp/test2.out
echo ""

# ─── Test 3: smoke-load-passing should PASS D8.6 (positive control) ───
echo "Test 3: smoke-load-passing (positive control)"
node "$SMOKE" "$FIXTURES/smoke-load-passing.omnifocusjs" > /tmp/test3.out 2>&1
EXIT=$?
assert "D8.6 smoke-load accepts clean action (positive control)" 0 "$EXIT"
rm -f /tmp/test3.out
echo ""

# ─── Summary ───
echo "=== Results ==="
TOTAL=$((PASS + FAIL))
if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}✅ All $TOTAL tests passed${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAIL of $TOTAL tests failed${NC}"
    exit 1
fi
