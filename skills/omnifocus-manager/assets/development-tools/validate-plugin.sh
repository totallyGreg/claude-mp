#!/bin/bash

# Plugin Structure Validation Script
# Validates OmniFocus plugin structure and manifest before installation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if plugin path provided
if [ -z "$1" ]; then
    echo "Usage: $0 <path-to-plugin.omnifocusjs>"
    echo "Example: $0 MyPlugin.omnifocusjs"
    exit 1
fi

PLUGIN_PATH="$1"

# Check if plugin exists
if [ ! -d "$PLUGIN_PATH" ]; then
    echo -e "${RED}❌ Error: Plugin directory not found: $PLUGIN_PATH${NC}"
    exit 1
fi

echo "=== OmniFocus Plugin Structure Validation ==="
echo ""
echo "Plugin: $PLUGIN_PATH"
echo ""

# Check manifest.json exists
echo "✓ Checking manifest.json..."
if [ ! -f "$PLUGIN_PATH/manifest.json" ]; then
    echo -e "${RED}  ❌ manifest.json not found${NC}"
    exit 1
fi

# Validate JSON syntax
if ! jq -e '.' "$PLUGIN_PATH/manifest.json" > /dev/null 2>&1; then
    echo -e "${RED}  ❌ manifest.json is invalid JSON${NC}"
    exit 1
fi
echo -e "${GREEN}  ✅ manifest.json is valid JSON${NC}"

# Check required manifest fields
IDENTIFIER=$(jq -r '.identifier // empty' "$PLUGIN_PATH/manifest.json")
VERSION=$(jq -r '.version // empty' "$PLUGIN_PATH/manifest.json")
AUTHOR=$(jq -r '.author // empty' "$PLUGIN_PATH/manifest.json")
DESCRIPTION=$(jq -r '.description // empty' "$PLUGIN_PATH/manifest.json")

if [ -z "$IDENTIFIER" ]; then
    echo -e "${RED}  ❌ Missing required field: identifier${NC}"
    exit 1
fi

if [ -z "$VERSION" ]; then
    echo -e "${RED}  ❌ Missing required field: version${NC}"
    exit 1
fi

if [ -z "$AUTHOR" ]; then
    echo -e "${YELLOW}  ⚠️  Missing recommended field: author${NC}"
fi

if [ -z "$DESCRIPTION" ]; then
    echo -e "${YELLOW}  ⚠️  Missing recommended field: description${NC}"
fi

echo -e "${GREEN}  ✅ Plugin identifier: $IDENTIFIER${NC}"
echo -e "${GREEN}  ✅ Plugin version: $VERSION${NC}"

# Check Resources directory
echo ""
echo "✓ Checking Resources directory..."
if [ ! -d "$PLUGIN_PATH/Resources" ]; then
    echo -e "${RED}  ❌ Resources/ directory not found${NC}"
    exit 1
fi
echo -e "${GREEN}  ✅ Resources/ directory exists${NC}"

# Check action files
echo ""
echo "✓ Checking action files..."
ACTIONS=$(jq -r '.actions[]?.identifier // empty' "$PLUGIN_PATH/manifest.json")

if [ -z "$ACTIONS" ]; then
    echo -e "${YELLOW}  ⚠️  No actions declared in manifest${NC}"
else
    ACTION_COUNT=0
    MISSING_ACTIONS=""

    for action in $ACTIONS; do
        ACTION_COUNT=$((ACTION_COUNT + 1))
        ACTION_FILE="$PLUGIN_PATH/Resources/${action}.js"

        if [ -f "$ACTION_FILE" ]; then
            echo -e "${GREEN}  ✅ ${action}.js exists${NC}"
        else
            echo -e "${RED}  ❌ ${action}.js missing${NC}"
            MISSING_ACTIONS="${MISSING_ACTIONS}${action} "
        fi
    done

    if [ -n "$MISSING_ACTIONS" ]; then
        echo -e "${RED}  ❌ Missing action files: ${MISSING_ACTIONS}${NC}"
        exit 1
    fi

    echo -e "${GREEN}  ✅ All $ACTION_COUNT action files exist${NC}"
fi

# Check library files (if declared)
echo ""
echo "✓ Checking library files..."
LIBRARIES=$(jq -r '.libraries[]?.identifier // empty' "$PLUGIN_PATH/manifest.json")

if [ -z "$LIBRARIES" ]; then
    echo -e "  ℹ️  No libraries declared in manifest"
else
    LIBRARY_COUNT=0
    MISSING_LIBRARIES=""

    for library in $LIBRARIES; do
        LIBRARY_COUNT=$((LIBRARY_COUNT + 1))
        LIBRARY_FILE="$PLUGIN_PATH/Resources/${library}.js"

        if [ -f "$LIBRARY_FILE" ]; then
            echo -e "${GREEN}  ✅ ${library}.js exists${NC}"
        else
            echo -e "${RED}  ❌ ${library}.js missing${NC}"
            MISSING_LIBRARIES="${MISSING_LIBRARIES}${library} "
        fi
    done

    if [ -n "$MISSING_LIBRARIES" ]; then
        echo -e "${RED}  ❌ Missing library files: ${MISSING_LIBRARIES}${NC}"
        exit 1
    fi

    echo -e "${GREEN}  ✅ All $LIBRARY_COUNT library files exist${NC}"
fi

# Check for common development artifacts that shouldn't be in distribution
echo ""
echo "✓ Checking for development artifacts..."
ARTIFACTS_FOUND=0

if [ -f "$PLUGIN_PATH/TESTING.md" ]; then
    echo -e "${YELLOW}  ⚠️  TESTING.md found (should be removed for distribution)${NC}"
    ARTIFACTS_FOUND=1
fi

if [ -f "$PLUGIN_PATH/TROUBLESHOOTING.md" ]; then
    echo -e "${YELLOW}  ⚠️  TROUBLESHOOTING.md found (should be removed for distribution)${NC}"
    ARTIFACTS_FOUND=1
fi

if [ -f "$PLUGIN_PATH/validate-structure.sh" ]; then
    echo -e "${YELLOW}  ⚠️  validate-structure.sh found (should be removed for distribution)${NC}"
    ARTIFACTS_FOUND=1
fi

if [ -f "$PLUGIN_PATH/test-libraries.js" ]; then
    echo -e "${YELLOW}  ⚠️  test-libraries.js found (should be removed for distribution)${NC}"
    ARTIFACTS_FOUND=1
fi

if [ -f "$PLUGIN_PATH/.DS_Store" ]; then
    echo -e "${YELLOW}  ⚠️  .DS_Store found (should be removed)${NC}"
    ARTIFACTS_FOUND=1
fi

if [ -d "$PLUGIN_PATH/.git" ]; then
    echo -e "${YELLOW}  ⚠️  .git directory found (should be removed for distribution)${NC}"
    ARTIFACTS_FOUND=1
fi

if [ $ARTIFACTS_FOUND -eq 0 ]; then
    echo -e "${GREEN}  ✅ No development artifacts found${NC}"
fi

# Check JavaScript files with eslint_d (if available)
echo ""
echo "✓ Checking JavaScript files with linter..."

# Check if eslint_d is available
if command -v eslint_d &> /dev/null; then
    JS_ERRORS=0

    for jsfile in "$PLUGIN_PATH/Resources"/*.js; do
        if [ -f "$jsfile" ]; then
            filename=$(basename "$jsfile")

            # Lint with eslint_d
            if eslint_d "$jsfile" > /dev/null 2>&1; then
                echo -e "${GREEN}  ✅ ${filename} - no linting errors${NC}"
            else
                echo -e "${RED}  ❌ ${filename} - linting errors detected${NC}"
                eslint_d "$jsfile"
                JS_ERRORS=1
            fi
        fi
    done

    if [ $JS_ERRORS -eq 1 ]; then
        echo -e "${RED}  ❌ JavaScript linting errors found${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}  ⚠️  eslint_d not found - skipping lint check${NC}"
    echo -e "  ℹ️  Install with: npm install -g eslint_d"
    echo -e "  ℹ️  Falling back to basic syntax check..."

    # Fallback to osascript for basic syntax check
    JS_ERRORS=0
    for jsfile in "$PLUGIN_PATH/Resources"/*.js; do
        if [ -f "$jsfile" ]; then
            filename=$(basename "$jsfile")

            if osascript -l JavaScript -e "$(cat "$jsfile")" > /dev/null 2>&1; then
                echo -e "${GREEN}  ✅ ${filename} - no syntax errors${NC}"
            else
                echo -e "${RED}  ❌ ${filename} - syntax errors detected${NC}"
                JS_ERRORS=1
            fi
        fi
    done

    if [ $JS_ERRORS -eq 1 ]; then
        echo -e "${RED}  ❌ JavaScript syntax errors found${NC}"
        exit 1
    fi
fi

# Check for API anti-patterns
echo ""
echo "✓ Checking for API anti-patterns..."
API_ERRORS=0

for jsfile in "$PLUGIN_PATH/Resources"/*.js; do
    if [ -f "$jsfile" ]; then
        filename=$(basename "$jsfile")

        # Check for Document.defaultDocument (should use global variables instead)
        if grep -q "Document\.defaultDocument" "$jsfile"; then
            echo -e "${RED}  ❌ ${filename} - uses Document.defaultDocument (use global variables: flattenedTasks, flattenedProjects, etc.)${NC}"
            API_ERRORS=1
        fi

        # Check for hallucinated Progress class
        if grep -q "new Progress" "$jsfile"; then
            echo -e "${RED}  ❌ ${filename} - uses non-existent Progress class${NC}"
            API_ERRORS=1
        fi

        # Check for FileType.fromExtension (doesn't exist)
        if grep -q "FileType\.fromExtension" "$jsfile"; then
            echo -e "${RED}  ❌ ${filename} - uses non-existent FileType.fromExtension()${NC}"
            API_ERRORS=1
        fi

        # Check for wrong LanguageModel.Schema constructor
        if grep -q "new LanguageModel\.Schema" "$jsfile"; then
            echo -e "${RED}  ❌ ${filename} - uses wrong LanguageModel.Schema constructor (use LanguageModel.Schema.fromJSON())${NC}"
            API_ERRORS=1
        fi
    fi
done

if [ $API_ERRORS -eq 0 ]; then
    echo -e "${GREEN}  ✅ No API anti-patterns detected${NC}"
else
    echo -e "${RED}  ❌ API anti-patterns found - see errors above${NC}"
    echo ""
    echo "Common fixes:"
    echo "  • Document.defaultDocument → use global variables (flattenedTasks, flattenedProjects, etc.)"
    echo "  • Progress → class doesn't exist, remove"
    echo "  • FileType.fromExtension() → doesn't exist, use url.write() instead"
    echo "  • new LanguageModel.Schema() → use LanguageModel.Schema.fromJSON()"
    echo ""
    echo "See: references/api_quick_reference.md for correct API patterns"
    exit 1
fi

# Summary
echo ""
echo "=== Validation Summary ==="
echo ""
echo -e "${GREEN}✅ Plugin structure is valid!${NC}"
echo ""
echo "Next steps:"
echo "1. Review any warnings above"
echo "2. Test plugin: open $PLUGIN_PATH"
echo "3. Verify in OmniFocus Automation Console"
echo ""

exit 0
