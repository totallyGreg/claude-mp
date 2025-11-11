#!/usr/bin/env bash
#
# Install a Zsh autoload function to the appropriate fpath directory
#
# Usage: install_autoload.sh <function-name> <function-file>
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

error() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

info() {
    echo -e "${GREEN}$1${NC}"
}

warn() {
    echo -e "${YELLOW}Warning: $1${NC}"
}

# Check if running in Zsh context
if [ -z "${ZSH_VERSION:-}" ]; then
    warn "Not running in Zsh. Attempting to detect Zsh configuration..."
    if ! command -v zsh &> /dev/null; then
        error "Zsh is not installed"
    fi
fi

# Parse arguments
if [ $# -ne 2 ]; then
    echo "Usage: $0 <function-name> <function-file>"
    echo ""
    echo "Installs a Zsh autoload function to the appropriate fpath directory."
    echo ""
    echo "Arguments:"
    echo "  function-name   Name of the function (without path)"
    echo "  function-file   Path to the function file to install"
    exit 1
fi

FUNCTION_NAME="$1"
FUNCTION_FILE="$2"

# Validate function file exists
if [ ! -f "$FUNCTION_FILE" ]; then
    error "Function file not found: $FUNCTION_FILE"
fi

# Determine the best fpath directory to use
# Priority:
# 1. User's custom fpath directory (if exists): ~/.zsh/functions
# 2. ZDOTDIR/functions (if ZDOTDIR is set)
# 3. ~/.zsh/functions (create if needed)

TARGET_DIR=""

# Check for user's custom functions directory
if [ -d "$HOME/.zsh/functions" ]; then
    TARGET_DIR="$HOME/.zsh/functions"
    info "Using existing user functions directory: $TARGET_DIR"
elif [ -n "${ZDOTDIR:-}" ] && [ -d "$ZDOTDIR" ]; then
    TARGET_DIR="$ZDOTDIR/functions"
    if [ ! -d "$TARGET_DIR" ]; then
        info "Creating functions directory: $TARGET_DIR"
        mkdir -p "$TARGET_DIR"
    fi
else
    TARGET_DIR="$HOME/.zsh/functions"
    if [ ! -d "$TARGET_DIR" ]; then
        info "Creating user functions directory: $TARGET_DIR"
        mkdir -p "$TARGET_DIR"
    fi
fi

# Install the function
TARGET_FILE="$TARGET_DIR/$FUNCTION_NAME"

if [ -f "$TARGET_FILE" ]; then
    warn "Function already exists: $TARGET_FILE"
    read -p "Overwrite? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
fi

cp "$FUNCTION_FILE" "$TARGET_FILE"
info "Installed function to: $TARGET_FILE"

# Check if fpath includes this directory
FPATH_CHECK=""
if [ -n "${ZSH_VERSION:-}" ]; then
    # We're in Zsh, can check fpath directly
    if [[ ":${FPATH}:" == *":${TARGET_DIR}:"* ]]; then
        FPATH_CHECK="yes"
    fi
fi

if [ "$FPATH_CHECK" != "yes" ]; then
    warn "The directory $TARGET_DIR may not be in your fpath."
    echo ""
    echo "Add this to your ~/.zshrc (before compinit):"
    echo ""
    echo "    fpath=($TARGET_DIR \$fpath)"
    echo "    autoload -Uz $FUNCTION_NAME"
    echo ""
else
    info "Directory is in fpath. Add this to your ~/.zshrc if not already present:"
    echo ""
    echo "    autoload -Uz $FUNCTION_NAME"
    echo ""
fi

# Remind about reloading
echo ""
info "To use the function in your current shell, run:"
echo ""
echo "    autoload -Uz $FUNCTION_NAME"
echo ""
echo "Or reload your shell configuration:"
echo ""
echo "    source ~/.zshrc"
echo ""

info "Installation complete!"
