# Zsh Configuration Guide

## Overview

This guide covers Zsh configuration, with particular focus on autoload functions, fpath management, and shell initialization. Mastering these concepts is essential for creating maintainable, modular Zsh configurations.

## Zsh Startup Files

Zsh reads configuration files in a specific order. Understanding this order is crucial for proper configuration.

### File Loading Order

For **login shells**:
1. `/etc/zshenv` (always)
2. `~/.zshenv` or `$ZDOTDIR/.zshenv` (always)
3. `/etc/zprofile` (login)
4. `~/.zprofile` or `$ZDOTDIR/.zprofile` (login)
5. `/etc/zshrc` (interactive)
6. `~/.zshrc` or `$ZDOTDIR/.zshrc` (interactive)
7. `/etc/zlogin` (login)
8. `~/.zlogin` or `$ZDOTDIR/.zlogin` (login)

On logout:
- `~/.zlogout` or `$ZDOTDIR/.zlogout`
- `/etc/zlogout`

For **interactive non-login shells** (most common):
1. `/etc/zshenv`
2. `~/.zshenv` or `$ZDOTDIR/.zshenv`
3. `/etc/zshrc`
4. `~/.zshrc` or `$ZDOTDIR/.zshrc`

### File Purposes

| File | Purpose | When to Use |
|------|---------|-------------|
| `.zshenv` | Environment variables | PATH, EDITOR, essential vars (sourced for all shells) |
| `.zprofile` | Login commands | Similar to `.zlogin`, runs before `.zshrc` |
| `.zshrc` | Interactive config | Aliases, functions, prompts, keybindings |
| `.zlogin` | Login commands | Commands to run after `.zshrc` for login shells |
| `.zlogout` | Cleanup | Commands to run on logout |

### ZDOTDIR

The `ZDOTDIR` variable specifies where Zsh looks for configuration files:

```bash
# Set in /etc/zshenv or before Zsh starts
export ZDOTDIR="$HOME/.config/zsh"

# Zsh will now look for:
# $ZDOTDIR/.zshenv
# $ZDOTDIR/.zshrc
# etc.
```

**Best Practice:** Set `ZDOTDIR` in `/etc/zshenv` or `~/.zshenv` to keep configs organized.

## Autoload Functions

Autoload is Zsh's mechanism for lazy-loading functions. Functions are loaded only when first called, improving startup time.

### Basic Autoload Syntax

```bash
# Mark function for autoloading
autoload function_name

# Load multiple functions
autoload function1 function2 function3

# Load with options
autoload -U function_name  # Ignore aliases
autoload -z function_name  # Use zsh style (default)
autoload -k function_name  # Use ksh style
autoload -w function_name  # Enable in current shell only

# Most common: -U and -z together
autoload -Uz function_name
```

### Common Autoload Flags

- `-U` - Suppress alias expansion (recommended)
- `-z` - Use Zsh-style loading (default, explicit)
- `-k` - Use Ksh-style loading
- `-w` - Mark for loading but don't make available yet
- `-X` - Load immediately
- `-d` - Mark function for delayed loading

**Best Practice:** Always use `autoload -Uz` for Zsh functions.

### Creating Autoload Functions

#### Method 1: File-based functions (recommended)

1. Create a directory for functions:
```bash
mkdir -p ~/.zsh/functions
```

2. Create a function file `~/.zsh/functions/hello`:
```bash
# File: ~/.zsh/functions/hello
# Function name must match filename

hello() {
    echo "Hello, ${1:-World}!"
}

# Execute the function if this is run directly
hello "$@"
```

3. Add to fpath and autoload in `~/.zshrc`:
```bash
# Add functions directory to fpath
fpath=(~/.zsh/functions $fpath)

# Autoload the function
autoload -Uz hello
```

#### Method 2: Inline definition

```bash
# Define and mark for autoload
autoload -Uz hello
hello() {
    echo "Hello, ${1:-World}!"
}
```

This is less common for autoload; usually functions are in files.

### Autoload Function Best Practices

1. **One function per file**: File name must match function name
2. **Call the function at end of file**: Ensures it runs when autoloaded
3. **Use `autoload -Uz`**: Most compatible and safe
4. **Add to fpath before autoload**: Functions must be findable
5. **No file extension**: Function files should have no `.zsh` extension

### Example: Advanced Autoload Function

```bash
# File: ~/.zsh/functions/mkcd
# Creates a directory and changes into it

mkcd() {
    # Ensure we have an argument
    if [[ $# -eq 0 ]]; then
        echo "Usage: mkcd <directory>" >&2
        return 1
    fi

    # Create directory with parents
    mkdir -p "$1" || return 1
    
    # Change into it
    cd "$1" || return 1
    
    echo "Created and entered: $1"
}

# Execute if called directly
mkcd "$@"
```

Add to `~/.zshrc`:
```bash
fpath=(~/.zsh/functions $fpath)
autoload -Uz mkcd
```

## FPATH Management

The `fpath` array determines where Zsh looks for autoload functions.

### Understanding fpath

```bash
# Display current fpath
echo $fpath
# or
print -l $fpath  # One per line

# Typical fpath includes:
# /usr/share/zsh/site-functions
# /usr/share/zsh/5.9/functions
# /usr/local/share/zsh/site-functions
```

### Modifying fpath

```bash
# Prepend to fpath (highest priority)
fpath=(~/.zsh/functions $fpath)

# Append to fpath (lowest priority)
fpath=($fpath ~/.zsh/functions)

# Add multiple directories
fpath=(
    ~/.zsh/functions
    ~/.zsh/completions
    $fpath
)

# Remove duplicates
typeset -U fpath
```

### fpath Best Practices

1. **Prepend custom directories**: Ensures your functions override system ones
2. **Use typeset -U**: Removes duplicates automatically
3. **Add before autoload**: Functions must be in fpath before loading
4. **Group related functions**: Use subdirectories for organization

### Example: Organized fpath Structure

```bash
# Directory structure
~/.zsh/
├── functions/       # General functions
│   ├── mkcd
│   ├── extract
│   └── backup
├── completions/     # Custom completions
│   └── _mycmd
└── prompts/         # Custom prompts
    └── prompt_custom_setup

# In ~/.zshrc
fpath=(
    ~/.zsh/functions
    ~/.zsh/completions
    ~/.zsh/prompts
    $fpath
)
typeset -U fpath

# Autoload all functions in directory
autoload -Uz ~/.zsh/functions/*(.:t)
```

The `*(.:t)` glob:
- `*` - All files
- `(.)` - Only regular files (not directories)
- `:t` - Tail (basename only)

## Completion System

The completion system is a critical part of Zsh and relies heavily on autoload.

### Initializing Completions

```bash
# In ~/.zshrc, after setting fpath

# Initialize completion system
autoload -Uz compinit

# Run compinit
compinit

# For security, check cache once per day
autoload -Uz compinit
if [[ -n ${ZDOTDIR}/.zcompdump(#qN.mh+24) ]]; then
    compinit
else
    compinit -C
fi
```

### Custom Completions

Create completion functions starting with underscore:

```bash
# File: ~/.zsh/completions/_mycmd

#compdef mycmd

_mycmd() {
    local -a subcommands
    subcommands=(
        'start:Start the service'
        'stop:Stop the service'
        'restart:Restart the service'
        'status:Show status'
    )
    
    _describe 'command' subcommands
}

_mycmd "$@"
```

Add to fpath before compinit:
```bash
fpath=(~/.zsh/completions $fpath)
autoload -Uz compinit
compinit
```

## Common Patterns and Idioms

### Loading All Functions from Directory

```bash
# Load all functions in ~/.zsh/functions
for func in ~/.zsh/functions/*(.:t); do
    autoload -Uz $func
done

# More concise using glob
autoload -Uz ~/.zsh/functions/*(.:t)
```

### Conditional Loading

```bash
# Load function only if file exists
[[ -f ~/.zsh/functions/myfunction ]] && autoload -Uz myfunction

# Load function only on macOS
[[ "$OSTYPE" == "darwin"* ]] && autoload -Uz mac_specific_func
```

### Lazy Loading for Speed

```bash
# Define placeholder that loads real function on first use
nvm() {
    unfunction nvm
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    nvm "$@"
}
```

### Reloading Functions

```bash
# Reload a function (useful during development)
unfunction myfunction
autoload -Uz myfunction

# Reload all functions in directory
for func in ~/.zsh/functions/*(.:t); do
    unfunction $func 2>/dev/null
    autoload -Uz $func
done
```

## Debugging Zsh Configuration

### Trace Startup

```bash
# Start Zsh with execution trace
zsh -x

# Or add to config file temporarily
set -x  # Enable tracing
# ... config code ...
set +x  # Disable tracing
```

### Profile Startup Time

```bash
# Add to top of ~/.zshrc
zmodload zsh/zprof

# Add to bottom of ~/.zshrc
zprof
```

### Check Function Locations

```bash
# Show where function is loaded from
whence -v function_name

# Show function definition
whence -f function_name

# Show all functions
print -l ${(ok)functions}
```

### Verify fpath

```bash
# Show fpath directories that exist
print -l $fpath | while read dir; do
    [[ -d $dir ]] && echo "✓ $dir" || echo "✗ $dir"
done

# List all autoloadable functions
print -l $^fpath/*(.:t)
```

## Advanced Topics

### Function Autoloading Internals

When you call an autoloaded function:
1. Zsh searches fpath for a file matching the function name
2. The file is sourced
3. The function definition is cached in memory
4. The function is executed with provided arguments

### Anonymous Functions

```bash
# Execute code in isolated scope
() {
    local temp_var="value"
    echo $temp_var
}
# temp_var is not accessible here
```

Useful for initialization blocks in config files.

### Autoloading with Parameters

```bash
# Pass parameters to autoloaded function
autoload -Uz colors && colors

# This loads colors function and executes it
```

## Common Issues and Solutions

### Issue: Function not found

**Diagnosis:**
```bash
# Check if function is in fpath
print -l $^fpath/myfunction

# Check fpath includes directory
echo $fpath | grep -q "my/functions/dir" || echo "Not in fpath"
```

**Solution:**
```bash
# Add directory to fpath
fpath=(~/.zsh/functions $fpath)
autoload -Uz myfunction
```

### Issue: Function not updating

**Diagnosis:**
Function is cached in memory after first load.

**Solution:**
```bash
# Unload and reload
unfunction myfunction
autoload -Uz myfunction

# Or restart shell
exec zsh
```

### Issue: Completion not working

**Diagnosis:**
```bash
# Check if compinit was called
whence -v compinit

# Check completion cache
ls -la ~/.zcompdump*
```

**Solution:**
```bash
# Rebuild completion cache
rm -f ~/.zcompdump*
autoload -Uz compinit
compinit
```

### Issue: Slow startup

**Diagnosis:**
```bash
# Profile with zprof
zmodload zsh/zprof
# ... source config ...
zprof
```

**Solution:**
- Use lazy loading for expensive operations
- Avoid synchronous network calls in config
- Use autoload instead of sourcing large files
- Consider compinit -C to skip security check

## Example: Complete Configuration

```bash
# ~/.zshrc

# Set ZDOTDIR if not already set
export ZDOTDIR="${ZDOTDIR:-$HOME}"

# Add custom function directories to fpath
fpath=(
    $ZDOTDIR/.zsh/functions
    $ZDOTDIR/.zsh/completions
    $fpath
)

# Remove duplicates from fpath
typeset -U fpath

# Autoload all functions
autoload -Uz $ZDOTDIR/.zsh/functions/*(.:t)

# Initialize completion system
autoload -Uz compinit
compinit

# Load colors
autoload -Uz colors && colors

# Common functions
autoload -Uz zmv  # Advanced file renaming

# Set up prompt
autoload -Uz promptinit
promptinit
# prompt adam2
```

## Resources

- `man zshall` - Complete Zsh documentation
- `man zshmisc` - Shell grammar and features
- `man zshbuiltins` - Built-in commands
- `man zshcompsys` - Completion system
- `man zshmodules` - Loadable modules
