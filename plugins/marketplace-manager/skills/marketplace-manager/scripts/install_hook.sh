#!/bin/bash
#
# install_hook.sh - Idempotent pre-commit hook installer for marketplace-manager
#
# Usage:
#   bash scripts/install_hook.sh [--force] [--dry-run]
#
# Options:
#   --force    Force reinstall even if up-to-date
#   --dry-run  Preview changes without installing
#

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
FORCE=false
DRY_RUN=false

for arg in "$@"; do
    case $arg in
        --force)
            FORCE=true
            ;;
        --dry-run)
            DRY_RUN=true
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            echo "Usage: $0 [--force] [--dry-run]"
            exit 1
            ;;
    esac
done

# Find repository root
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_ROOT" ]; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_PATH="$SCRIPT_DIR/pre-commit.template"
HOOK_PATH="$REPO_ROOT/.git/hooks/pre-commit"

echo -e "${BLUE}🔧 marketplace-manager pre-commit hook installer${NC}"
echo ""

# Check if marketplace.json exists in target repo
MARKETPLACE_JSON="$REPO_ROOT/.claude-plugin/marketplace.json"
if [ ! -f "$MARKETPLACE_JSON" ]; then
    echo -e "${YELLOW}⚠️  No marketplace.json found in target repo${NC}"
    echo -e "${YELLOW}   The hook requires .claude-plugin/marketplace.json to function.${NC}"
    echo -e "${YELLOW}   Initialize with: uv run $SCRIPT_DIR/add_to_marketplace.py init${NC}"
    echo ""
fi

# Check if template exists
if [ ! -f "$TEMPLATE_PATH" ]; then
    echo -e "${RED}❌ Error: Template not found at $TEMPLATE_PATH${NC}"
    exit 1
fi

# Extract template version
TEMPLATE_VERSION=$(grep -m 1 "^# marketplace-manager pre-commit hook v" "$TEMPLATE_PATH" | sed 's/.*v\([0-9.]*\).*/\1/')
if [ -z "$TEMPLATE_VERSION" ]; then
    echo -e "${YELLOW}⚠️  Warning: Could not detect template version${NC}"
    TEMPLATE_VERSION="unknown"
fi

echo -e "Template: ${GREEN}v$TEMPLATE_VERSION${NC} at $TEMPLATE_PATH"

# Check if hook is already installed
if [ -f "$HOOK_PATH" ]; then
    # Extract installed version
    INSTALLED_VERSION=$(grep -m 1 "^HOOK_VERSION=" "$HOOK_PATH" | sed 's/.*"\([^"]*\)".*/\1/')
    if [ -z "$INSTALLED_VERSION" ]; then
        INSTALLED_VERSION="unknown"
    fi
    
    echo -e "Installed: ${YELLOW}v$INSTALLED_VERSION${NC} at $HOOK_PATH"
    
    # Compare versions
    if [ "$INSTALLED_VERSION" = "$TEMPLATE_VERSION" ] && [ "$FORCE" = false ]; then
        echo ""
        echo -e "${GREEN}✅ Hook is up-to-date (v$INSTALLED_VERSION)${NC}"
        echo -e "   Use --force to reinstall anyway"
        exit 0
    fi
    
    # Check if hook content matches template (ignoring embedded path lines)
    HOOK_NORMALIZED=$(grep -v "^EMBEDDED_SCRIPTS_DIR=" "$HOOK_PATH" | grep -v "^EMBEDDED_INSTALL_CMD=")
    TEMPLATE_NORMALIZED=$(grep -v "^EMBEDDED_SCRIPTS_DIR=" "$TEMPLATE_PATH" | grep -v "^EMBEDDED_INSTALL_CMD=")
    if [ "$HOOK_NORMALIZED" = "$TEMPLATE_NORMALIZED" ] && [ "$FORCE" = false ]; then
        echo ""
        echo -e "${GREEN}✅ Hook is up-to-date (identical to template)${NC}"
        echo -e "   Use --force to reinstall anyway"
        exit 0
    fi
    
    if [ "$INSTALLED_VERSION" != "$TEMPLATE_VERSION" ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Hook needs update: v$INSTALLED_VERSION → v$TEMPLATE_VERSION${NC}"
        ACTION="Updating"
    else
        echo ""
        echo -e "${BLUE}🔄 Reinstalling hook${NC}"
        ACTION="Reinstalling"
    fi
else
    echo -e "Installed: ${YELLOW}Not installed${NC}"
    echo ""
    echo -e "${BLUE}📦 Installing hook for the first time${NC}"
    ACTION="Installing"
fi

# Dry run mode
if [ "$DRY_RUN" = true ]; then
    echo ""
    echo -e "${BLUE}[DRY RUN] Would perform:${NC}"
    echo -e "  1. Copy $TEMPLATE_PATH"
    echo -e "     to   $HOOK_PATH"
    echo -e "  2. Embed script path: $SCRIPT_DIR"
    echo -e "  3. Set executable permissions (chmod +x)"
    echo ""
    echo -e "${GREEN}✅ Dry run complete${NC}"
    exit 0
fi

# Perform installation
echo ""
echo -e "${BLUE}$ACTION hook...${NC}"

# Create hooks directory if it doesn't exist
mkdir -p "$(dirname "$HOOK_PATH")"

# Copy template to hook location
cp "$TEMPLATE_PATH" "$HOOK_PATH"

# Embed the resolved script directory and install command into the hook
# Portable sed -i across macOS (BSD) and Linux (GNU)
sed_inplace() { if [[ "$OSTYPE" == "darwin"* ]]; then sed -i '' "$@"; else sed -i "$@"; fi; }
sed_inplace "s|^EMBEDDED_SCRIPTS_DIR=.*|EMBEDDED_SCRIPTS_DIR=\"$SCRIPT_DIR\"|" "$HOOK_PATH"
INSTALL_CMD="bash $SCRIPT_DIR/install_hook.sh"
sed_inplace "s|^EMBEDDED_INSTALL_CMD=.*|EMBEDDED_INSTALL_CMD=\"$INSTALL_CMD\"|" "$HOOK_PATH"

# Set executable permissions
chmod +x "$HOOK_PATH"

echo -e "${GREEN}✅ Hook installed successfully (v$TEMPLATE_VERSION)${NC}"
echo ""
echo -e "Location:    $HOOK_PATH"
echo -e "Version:     v$TEMPLATE_VERSION"
echo -e "Scripts at:  $SCRIPT_DIR"
echo ""
echo -e "${GREEN}The hook will now automatically sync marketplace.json on commits${NC}"
echo -e "To bypass temporarily: ${YELLOW}git commit --no-verify${NC}"

exit 0
