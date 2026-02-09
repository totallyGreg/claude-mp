---
name: terminal-guru
description: This skill should be used when configuring, diagnosing, fixing, or understanding Unix terminals, including terminfo database issues, shell configuration (especially Zsh autoload functions and fpath), Unicode/UTF-8 character rendering problems, TUI applications, terminal emulator settings, **generating zsh functions using established patterns**, and comprehensive zsh testing with isolated environments for performance optimization and plugin compatibility validation.
metadata:
  version: "2.1.0"
---

# Terminal Guru

## Overview

Configure, diagnose, test, and optimize all aspects of Unix terminals and zsh configurations. Provides comprehensive terminal diagnostics (terminfo, Unicode/UTF-8, locale), zsh configuration management (autoload functions, fpath), and Python-based testing framework for safe experimentation in isolated environments. Test display consistency, measure performance, validate plugin compatibility, and iteratively optimize configurations without affecting your working shell.

## When to Use This Skill

Use terminal-guru when users encounter:
- Terminal display issues (garbled characters, wrong colors, broken box drawing)
- Shell configuration problems (Zsh autoload functions, fpath management)
- Unicode/UTF-8 rendering issues (emoji, CJK characters, combining characters)
- Terminal capability diagnostics
- TUI application configuration
- Locale and encoding problems
- Terminal emulator configuration
- Character width and alignment issues
- **Performance optimization needs (slow startup, plugin overhead)**
- **Plugin configuration and compatibility testing**
- **Safe testing of configuration changes before applying**
- **Comparing different plugin managers or configurations**

### Zsh Function Generation

Use terminal-guru to **generate, create, or write zsh functions** using established patterns. Examples:
- "Generate a zsh function that..." - Direct function generation
- "Create an autoload function with completions" - With completion support
- "Write a modular zsh function using xargs" - Specific pattern (xargs modularity)
- "Implement a secure function with keychain integration" - Credential security pattern
- "Create a subcommand function" - Subcommand dispatcher pattern
- "Write a zsh function following the Plugin Standard" - Standards compliance
- "Create a zsh function with async operations" - Advanced patterns

See `references/zsh_function_patterns.md` for comprehensive pattern documentation and `references/zsh_completion_guide.md` for completion implementation patterns.

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

### 5. Testing and Optimization Framework (NEW in v2.0)

For comprehensive testing, performance optimization, and safe configuration experimentation, use the Python-based testing framework. This framework creates isolated test environments where you can test changes without affecting the user's working shell.

**Key innovation:** All test logic is implemented in Python rather than shell scripts, eliminating the circular dependency problem of "shell testing shell." Python observes zsh externally via subprocess/PTY, ensuring test infrastructure bugs cannot contaminate results.

#### Creating Isolated Test Environments

Create safe, isolated environments using ZDOTDIR for testing:

```bash
# Create isolated environment
python3 scripts/environment_builder.py --create my-test

# List all test environments
python3 scripts/environment_builder.py --list

# Remove test environment
python3 scripts/environment_builder.py --cleanup /path/to/env
```

#### Running Comprehensive Tests

Execute automated test suites in isolated environments:

```bash
# Run all test suites
python3 scripts/terminal_test_runner.py --name my-test --suite all

# Run specific test suite
python3 scripts/terminal_test_runner.py --name perf-test --suite performance

# Preserve environment for inspection
python3 scripts/terminal_test_runner.py --name debug --preserve
```

**Test Suites:**
- **Display Tests** - Line length accuracy, Unicode rendering, color support
- **Performance Tests** - Startup time, command execution latency, profiling
- **Plugin Tests** - Plugin detection, FPATH configuration, autoload mechanism

#### Comparing Configurations

Compare test results from different configurations:

```bash
# Run baseline
python3 scripts/terminal_test_runner.py --name baseline

# Modify config in test environment and re-run
python3 scripts/terminal_test_runner.py --name optimized

# Compare results
python3 scripts/terminal_test_runner.py --compare \
    ~/.terminal-guru/test-environments/baseline-*/results/all_results.json \
    ~/.terminal-guru/test-environments/optimized-*/results/all_results.json
```

#### Testing Workflow

1. **Create Environment** - Isolated ZDOTDIR with copy of user's config
2. **Run Baseline Tests** - Identify current issues and performance
3. **Apply Changes** - Modify config in isolated environment
4. **Re-test** - Validate improvements
5. **Compare Results** - Analyze before/after differences
6. **Apply to Production** - Once validated, apply changes to real config

**When to use**: Users want to optimize performance, test plugin changes, compare configurations, or safely experiment with config modifications.

**Reference:** See `references/isolated_environments.md` for detailed guide on ZDOTDIR isolation and testing workflows.

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

### "My zsh startup is slow" (NEW in v2.0)
1. Run performance tests: `python3 scripts/terminal_test_runner.py --name perf --suite performance`
2. Check results: View `~/.terminal-guru/test-environments/perf-*/results/performance_results.json`
3. Identify slow components from startup time measurements
4. Apply optimizations (lazy loading, defer plugins, cache compinit)
5. Re-test to verify improvements

### "I want to test a config change safely" (NEW in v2.0)
1. Create test environment: `python3 scripts/environment_builder.py --create test`
2. Edit isolated config: `vim ~/.terminal-guru/test-environments/test-*/zdotdir/.zshrc`
3. Run tests: `python3 scripts/terminal_test_runner.py --name test --suite all`
4. If successful, apply changes to real ~/.zshrc
5. If failed, just delete the test environment

### "Compare oh-my-zsh vs zinit" (NEW in v2.0)
1. Run baseline with oh-my-zsh: `python3 scripts/terminal_test_runner.py --name omz`
2. Create test environment and convert to zinit
3. Run tests with zinit: `python3 scripts/terminal_test_runner.py --name zinit`
4. Compare: `python3 scripts/terminal_test_runner.py --compare omz.json zinit.json`
5. Choose based on performance and compatibility results

## Resources

### scripts/
- **`terminal_diagnostics.py`** - Comprehensive diagnostic tool for terminal, locale, and environment (supports --json mode)
- **`install_autoload.sh`** - Install Zsh autoload functions to correct fpath location
- **`environment_builder.py`** - Create and manage isolated ZDOTDIR test environments (NEW v2.0)
- **`terminal_test_runner.py`** - Run automated test suites in isolated environments (NEW v2.0)
- **`tests/display_tests.py`** - Display consistency tests (Python-based) (NEW v2.0)
- **`tests/performance_tests.py`** - Performance profiling and benchmarking (NEW v2.0)
- **`tests/plugin_tests.py`** - Plugin compatibility testing (NEW v2.0)
- **`analysis/output_analyzer.py`** - Analyze test results and generate recommendations (NEW v2.0)

### references/
- **`terminfo_guide.md`** - Complete terminfo database reference and troubleshooting
- **`zsh_configuration.md`** - Comprehensive Zsh configuration including autoload and fpath
- **`unicode_troubleshooting.md`** - Unicode/UTF-8 character rendering and encoding issues
- **`isolated_environments.md`** - Guide to ZDOTDIR isolation and testing workflows (NEW v2.0)
