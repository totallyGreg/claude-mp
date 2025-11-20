---
name: terminal-guru
description: This skill should be used when configuring, diagnosing, fixing, or understanding Unix terminals, including terminfo database issues, shell configuration (especially Zsh autoload functions and fpath), Unicode/UTF-8 character rendering problems, TUI applications, and terminal emulator settings.
---

# Terminal Guru

## Overview

Configure, diagnose, and fix all aspects of Unix terminals, from low-level terminfo capabilities to high-level shell configurations. Handle Unicode/UTF-8 rendering issues, create and install Zsh autoload functions, troubleshoot terminal emulator problems, and optimize TUI (Text User Interface) applications.

## When to Use This Skill

Use terminal-guru when users encounter:
- Terminal display issues (garbled characters, wrong colors, broken box drawing)
- Shell configuration problems (Zsh autoload functions, fpath management)
- Unicode/UTF-8 rendering issues (emoji, CJK characters, combining characters)
- Zsh function creation and installation
- Terminal capability diagnostics
- TUI application configuration
- Locale and encoding problems
- Terminal emulator configuration
- Character width and alignment issues

## Core Capabilities

### 1. Terminal Diagnostics

Run comprehensive diagnostics to identify terminal, locale, and environment issues:

```bash
# Use the diagnostic script
python3 scripts/terminal_diagnostics.py
```

The diagnostic script checks:
- Environment variables (TERM, LANG, LC_*, SHELL, FPATH)
- Locale settings and UTF-8 support
- Terminal capabilities via terminfo/tput
- Unicode rendering (emoji, CJK, box drawing)
- Shell configuration files
- Installed TUI tools

**When to use**: Start with diagnostics when users report any terminal-related issues to gather comprehensive information about their environment.

### 2. Terminfo Database Management

For detailed terminfo troubleshooting, refer to `references/terminfo_guide.md` which covers:
- Terminal type (TERM) selection and configuration
- Terminfo database locations and structure
- Using infocmp, tic, tput, and toe commands
- Terminal capabilities (colors, cursor movement, text attributes)
- Creating custom terminfo entries
- Fixing common terminfo issues (wrong TERM, missing entries, broken capabilities)

**Common operations**:

```bash
# Check current terminal's capabilities
infocmp

# Test color support
tput colors

# Verify terminfo entry exists
infocmp $TERM >/dev/null 2>&1 && echo "OK" || echo "Missing"

# Compare terminal types
infocmp -d xterm-256color tmux-256color

# Create custom entry
infocmp xterm-256color > custom.ti
# Edit custom.ti
tic -o ~/.terminfo custom.ti
```

**When to diagnose**: Users report wrong colors, function keys not working, box drawing broken, or "unknown terminal type" errors.

### 3. Zsh Configuration and Autoload Functions

For comprehensive Zsh guidance, refer to `references/zsh_configuration.md` which covers:
- Zsh startup file order (.zshenv, .zprofile, .zshrc, .zlogin)
- ZDOTDIR configuration
- Autoload function syntax and best practices
- fpath management and organization
- Completion system (compinit)
- Function debugging and reloading
- Performance optimization

**Creating autoload functions**:

1. Create function file (no extension, name matches function):
```bash
# File: ~/.zsh/functions/mkcd
mkcd() {
    if [[ $# -eq 0 ]]; then
        echo "Usage: mkcd <directory>" >&2
        return 1
    fi
    mkdir -p "$1" && cd "$1"
}

# Execute if called directly
mkcd "$@"
```

2. Install the function:
```bash
# Use the installation script
bash scripts/install_autoload.sh mkcd ~/.zsh/functions/mkcd

# Or manually:
fpath=(~/.zsh/functions $fpath)
autoload -Uz mkcd
```

3. Add to ~/.zshrc for persistence:
```bash
fpath=(~/.zsh/functions $fpath)
autoload -Uz mkcd
```

**When to use**: Users want to create Zsh functions, configure fpath, set up completions, or troubleshoot function loading.

### 4. Unicode and UTF-8 Troubleshooting

For detailed Unicode guidance, refer to `references/unicode_troubleshooting.md` which covers:
- Locale configuration for UTF-8
- Character width issues (narrow, wide, ambiguous, zero-width)
- Combining characters and normalization (NFC, NFD, NFKC, NFKD)
- Emoji rendering (simple, modifiers, ZWJ sequences)
- Box drawing and line characters
- Zero-width characters (ZWSP, ZWJ, ZWNJ)
- Byte Order Mark (BOM) detection and removal
- Terminal emulator configuration
- Font selection for Unicode coverage

**Common fixes**:

```bash
# Fix locale for UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Test Unicode rendering
echo "ASCII: Hello"
echo "CJK: 你好世界"
echo "Emoji: 😀 🎉 ✨"
echo "Box: ┌─┐│└┘"

# Fix box drawing (if showing as q, x, m, j)
export NCURSES_NO_UTF8_ACS=0

# Remove BOM from file
sed -i '1s/^\xEF\xBB\xBF//' file.txt

# Normalize Unicode
echo "café" | iconv -f UTF-8 -t UTF-8
```

**When to use**: Users report garbled characters, emoji not rendering, box drawing broken, incorrect string lengths, or cursor misalignment.

## Diagnostic Workflow

When troubleshooting terminal issues, follow this systematic approach:

### Step 1: Gather Information

Run diagnostics to collect comprehensive environment information:
```bash
python3 scripts/terminal_diagnostics.py
```

Key information to verify:
- TERM value (should be xterm-256color, tmux-256color, etc.)
- Locale settings (should include UTF-8)
- Shell type and config files
- Terminal emulator being used

### Step 2: Identify the Problem Domain

Categorize the issue:

| Symptoms | Domain | Reference |
|----------|--------|-----------|
| Wrong colors, broken function keys | Terminfo | `references/terminfo_guide.md` |
| Function not found, fpath issues | Zsh config | `references/zsh_configuration.md` |
| Garbled text, emoji broken, box drawing issues | Unicode/UTF-8 | `references/unicode_troubleshooting.md` |
| Slow startup, functions not loading | Zsh performance | `references/zsh_configuration.md` |

### Step 3: Apply Targeted Fixes

Use the appropriate reference guide to diagnose and fix:

**Terminfo issues**:
```bash
# Verify and fix TERM
echo $TERM
export TERM=xterm-256color
tput colors  # Should show 256
```

**Zsh issues**:
```bash
# Check fpath
print -l $fpath
# Add custom directory
fpath=(~/.zsh/functions $fpath)
# Reload function
unfunction myfunction; autoload -Uz myfunction
```

**Unicode issues**:
```bash
# Fix locale
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
# Test
locale | grep UTF-8
```

### Step 4: Persist Configuration

Add fixes to appropriate shell config file:
- `.zshenv` - Environment variables (LANG, PATH, EDITOR)
- `.zshrc` - Interactive config (aliases, functions, fpath, prompts)

```bash
# Add to ~/.zshrc
cat >> ~/.zshrc << 'EOF'
# Terminal configuration
export TERM=xterm-256color
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Zsh functions
fpath=(~/.zsh/functions $fpath)
typeset -U fpath
autoload -Uz ~/.zsh/functions/*(.:t)
EOF

# Reload
source ~/.zshrc
```

## Creating Zsh Autoload Functions

Complete workflow for creating and installing Zsh autoload functions:

### Step 1: Create the Function

Best practices:
- One function per file
- File name must match function name exactly
- No file extension
- Call the function at end of file (enables direct execution when autoloaded)
- Use local variables to avoid polluting global scope

```bash
# Example: ~/.zsh/functions/extract
# Universal archive extractor

extract() {
    if [[ $# -eq 0 ]]; then
        echo "Usage: extract <archive-file>" >&2
        return 1
    fi

    if [[ ! -f "$1" ]]; then
        echo "Error: '$1' is not a file" >&2
        return 1
    fi

    case "$1" in
        *.tar.gz|*.tgz)   tar xzf "$1"   ;;
        *.tar.bz2|*.tbz2) tar xjf "$1"   ;;
        *.tar.xz|*.txz)   tar xJf "$1"   ;;
        *.tar)            tar xf "$1"    ;;
        *.gz)             gunzip "$1"    ;;
        *.bz2)            bunzip2 "$1"   ;;
        *.zip)            unzip "$1"     ;;
        *.rar)            unrar x "$1"   ;;
        *.7z)             7z x "$1"      ;;
        *)
            echo "Error: Unknown archive format" >&2
            return 1
            ;;
    esac
}

# Execute if called directly
extract "$@"
```

### Step 2: Install the Function

Use the installation script to properly place the function:

```bash
# Install to correct fpath location
bash scripts/install_autoload.sh extract ~/.zsh/functions/extract
```

The script:
- Determines the appropriate fpath directory (priority: ~/.zsh/functions, $ZDOTDIR/functions)
- Creates the directory if needed
- Copies the function file
- Provides instructions for adding to fpath and autoloading

### Step 3: Configure Shell

Add to ~/.zshrc (before compinit if used):

```bash
# Add functions directory to fpath
fpath=(~/.zsh/functions $fpath)

# Remove duplicates
typeset -U fpath

# Autoload specific function
autoload -Uz extract

# Or autoload all functions in directory
autoload -Uz ~/.zsh/functions/*(.:t)
```

### Step 4: Test and Reload

```bash
# Test the function
extract archive.tar.gz

# If making changes, reload:
unfunction extract
autoload -Uz extract

# Or reload shell
exec zsh
```

## Advanced Scenarios

### Custom Terminal Configuration for SSH

When SSH'ing to remote systems with different terminal databases:

```bash
# In ~/.zshrc or ~/.bashrc
if [[ -n "$SSH_CONNECTION" ]]; then
    # Use widely-compatible TERM
    export TERM=xterm-256color
    
    # Ensure UTF-8
    export LANG=en_US.UTF-8
    export LC_ALL=en_US.UTF-8
fi
```

### Tmux/Screen Terminal Setup

```bash
# For tmux - add to ~/.tmux.conf
set -g default-terminal "tmux-256color"
set -ga terminal-overrides ",*256col*:Tc"

# For screen - add to ~/.screenrc
term screen-256color
```

Then in shell config:
```bash
if [[ -n "$TMUX" ]]; then
    export TERM=tmux-256color
elif [[ -n "$STY" ]]; then
    export TERM=screen-256color
fi
```

### Lazy Loading for Performance

For expensive operations (like NVM, pyenv), use lazy loading:

```bash
# File: ~/.zsh/functions/nvm
# Lazy-load NVM on first use

nvm() {
    # Remove this placeholder function
    unfunction nvm
    
    # Load the real NVM
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    
    # Call the real nvm with original arguments
    nvm "$@"
}

nvm "$@"
```

### Debugging Shell Startup

Profile shell startup time:

```bash
# Add to top of ~/.zshrc
zmodload zsh/zprof

# ... rest of config ...

# Add to bottom of ~/.zshrc
zprof
```

Trace execution:
```bash
# Start shell with trace
zsh -x

# Or trace section of config
set -x
# ... code to trace ...
set +x
```

## Reference Documentation

This skill includes three comprehensive reference guides. Load these into context when needed for detailed information:

1. **`references/terminfo_guide.md`** - Load when diagnosing terminal capabilities, TERM issues, color problems, or creating custom terminfo entries

2. **`references/zsh_configuration.md`** - Load when working with Zsh startup files, autoload functions, fpath, completions, or shell performance

3. **`references/unicode_troubleshooting.md`** - Load when handling character encoding, emoji, CJK characters, character width, or font issues

## Common Use Cases

### "My terminal colors are wrong"
1. Run diagnostics: `python3 scripts/terminal_diagnostics.py`
2. Check TERM: `echo $TERM`
3. Set correct TERM: `export TERM=xterm-256color`
4. Test: `tput colors` (should show 256)
5. Add to shell config to persist

### "Box drawing characters show as letters"
1. Verify UTF-8 locale: `locale | grep UTF-8`
2. Set if missing: `export LANG=en_US.UTF-8`
3. Try: `export NCURSES_NO_UTF8_ACS=0`
4. Check font supports Unicode
5. Refer to `references/unicode_troubleshooting.md`

### "I want to create a Zsh function"
1. Create function file in ~/.zsh/functions/
2. Install: `bash scripts/install_autoload.sh <name> <file>`
3. Add to ~/.zshrc: `fpath=(~/.zsh/functions $fpath); autoload -Uz <name>`
4. Refer to `references/zsh_configuration.md` for advanced patterns

### "My custom function isn't found"
1. Check fpath: `print -l $fpath`
2. Verify function file exists: `ls ~/.zsh/functions/<name>`
3. Ensure in fpath: `fpath=(~/.zsh/functions $fpath)`
4. Reload: `unfunction <name>; autoload -Uz <name>`
5. Check function location: `whence -v <name>`

### "Emoji aren't rendering correctly"
1. Verify UTF-8 locale: `locale | grep UTF-8`
2. Check terminal supports emoji
3. Verify font has emoji glyphs
4. Test: `echo "😀 🎉 ✨"`
5. Refer to `references/unicode_troubleshooting.md` for emoji-specific issues

## Resources

### scripts/
- **`terminal_diagnostics.py`** - Comprehensive diagnostic tool for terminal, locale, and environment
- **`install_autoload.sh`** - Install Zsh autoload functions to correct fpath location

### references/
- **`terminfo_guide.md`** - Complete terminfo database reference and troubleshooting
- **`zsh_configuration.md`** - Comprehensive Zsh configuration including autoload and fpath
- **`unicode_troubleshooting.md`** - Unicode/UTF-8 character rendering and encoding issues
