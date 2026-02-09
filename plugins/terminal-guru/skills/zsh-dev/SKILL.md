---
name: zsh-dev
description: This skill should be used when working with Zsh shell configuration, autoload functions, fpath management, completions, function generation using established patterns, and comprehensive testing with isolated environments for performance optimization and plugin compatibility validation. Use for creating zsh functions, configuring fpath, testing config changes safely, optimizing shell startup, and Plugin Standard compliance.
metadata:
  version: "3.0.0"
---

# Zsh Development

## Overview

Create, test, and optimize Zsh shell configurations: autoload functions, fpath management, completions, function generation from established patterns, and a Python-based testing framework for safe experimentation in isolated environments. Measure performance, validate plugin compatibility, and iteratively optimize configurations without affecting your working shell.

## When to Use This Skill

- Zsh shell configuration (startup files, ZDOTDIR)
- Autoload function creation and management
- fpath configuration and troubleshooting
- Completion system setup (compinit)
- Function generation using established patterns
- Performance optimization (slow startup, plugin overhead)
- Plugin configuration and compatibility testing
- Safe testing of configuration changes
- Comparing different plugin managers or configurations

### Zsh Function Generation

Use this skill to **generate, create, or write zsh functions** using established patterns:
- "Generate a zsh function that..." - Direct function generation
- "Create an autoload function with completions" - With completion support
- "Write a modular zsh function using xargs" - Specific pattern (xargs modularity)
- "Implement a secure function with keychain integration" - Credential security pattern
- "Create a subcommand function" - Subcommand dispatcher pattern
- "Write a zsh function following the Plugin Standard" - Standards compliance
- "Create a zsh function with async operations" - Advanced patterns

See `references/zsh_function_patterns.md` for comprehensive pattern documentation and `references/zsh_completion_guide.md` for completion implementation patterns.

## Core Capabilities

### 1. Zsh Configuration and Autoload Functions

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
bash scripts/install_autoload.sh mkcd ~/.zsh/functions/mkcd

# Or manually:
fpath=(~/.zsh/functions $fpath)
autoload -Uz mkcd
```

3. Add to ~/.zshrc for persistence:
```bash
fpath=(~/.zsh/functions $fpath)
typeset -U fpath
autoload -Uz mkcd
```

### 2. Testing and Optimization Framework

Create isolated test environments where you can test changes without affecting the user's working shell. All test logic is in Python, eliminating the circular dependency of "shell testing shell."

#### Creating Isolated Test Environments

```bash
# Create isolated environment
python3 scripts/environment_builder.py --create my-test

# List all test environments
python3 scripts/environment_builder.py --list

# Remove test environment
python3 scripts/environment_builder.py --cleanup /path/to/env
```

#### Running Comprehensive Tests

```bash
# Run all test suites
python3 scripts/terminal_test_runner.py --name my-test --suite all

# Run specific test suite
python3 scripts/terminal_test_runner.py --name perf-test --suite performance

# Preserve environment for inspection
python3 scripts/terminal_test_runner.py --name debug --preserve
```

**Test Suites:**
- **Performance Tests** - Startup time, command execution latency, profiling
- **Plugin Tests** - Plugin detection, FPATH configuration, autoload mechanism

#### Comparing Configurations

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

**Reference:** See `references/isolated_environments.md` for detailed guide on ZDOTDIR isolation and testing workflows.

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

extract "$@"
```

### Step 2: Install the Function

```bash
bash scripts/install_autoload.sh extract ~/.zsh/functions/extract
```

### Step 3: Configure Shell

Add to ~/.zshrc (before compinit if used):

```bash
fpath=(~/.zsh/functions $fpath)
typeset -U fpath
autoload -Uz extract
# Or autoload all: autoload -Uz ~/.zsh/functions/*(.:t)
```

### Step 4: Test and Reload

```bash
extract archive.tar.gz

# If making changes, reload:
unfunction extract
autoload -Uz extract

# Or reload shell
exec zsh
```

## Advanced Scenarios

### Lazy Loading for Performance

For expensive operations (like NVM, pyenv), use lazy loading:

```bash
# File: ~/.zsh/functions/nvm
nvm() {
    unfunction nvm
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    nvm "$@"
}

nvm "$@"
```

### Debugging Shell Startup

```bash
# Profile startup time
zmodload zsh/zprof
# ... rest of config ...
zprof

# Trace execution
zsh -x
```

## Common Use Cases

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

### "My zsh startup is slow"
1. Run performance tests: `python3 scripts/terminal_test_runner.py --name perf --suite performance`
2. Check results in `~/.terminal-guru/test-environments/perf-*/results/performance_results.json`
3. Identify slow components from startup time measurements
4. Apply optimizations (lazy loading, defer plugins, cache compinit)
5. Re-test to verify improvements

### "I want to test a config change safely"
1. Create test environment: `python3 scripts/environment_builder.py --create test`
2. Edit isolated config: `vim ~/.terminal-guru/test-environments/test-*/zdotdir/.zshrc`
3. Run tests: `python3 scripts/terminal_test_runner.py --name test --suite all`
4. If successful, apply changes to real ~/.zshrc
5. If failed, just delete the test environment

### "Compare oh-my-zsh vs zinit"
1. Run baseline with oh-my-zsh: `python3 scripts/terminal_test_runner.py --name omz`
2. Create test environment and convert to zinit
3. Run tests with zinit: `python3 scripts/terminal_test_runner.py --name zinit`
4. Compare: `python3 scripts/terminal_test_runner.py --compare omz.json zinit.json`
5. Choose based on performance and compatibility results

## Resources

### scripts/
- **`environment_builder.py`** - Create and manage isolated ZDOTDIR test environments
- **`terminal_test_runner.py`** - Run automated test suites in isolated environments
- **`install_autoload.sh`** - Install Zsh autoload functions to correct fpath location
- **`tests/performance_tests.py`** - Performance profiling and benchmarking
- **`tests/plugin_tests.py`** - Plugin compatibility testing
- **`tests/base.py`** - Shared test infrastructure
- **`analysis/output_analyzer.py`** - Analyze test results and generate recommendations

### references/
- **`zsh_configuration.md`** - Comprehensive Zsh configuration including autoload and fpath
- **`zsh_function_patterns.md`** - Zsh function generation patterns and templates
- **`zsh_completion_guide.md`** - Completion implementation patterns
- **`isolated_environments.md`** - Guide to ZDOTDIR isolation and testing workflows
