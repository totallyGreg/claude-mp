# Zsh Function Patterns Reference

Comprehensive guide to zsh function development patterns, combining user's preferred practices with Zsh Plugin Standard conventions.

## Table of Contents

1. [User's Established Patterns](#users-established-patterns)
2. [Zsh Plugin Standard Conventions](#zsh-plugin-standard-conventions)
3. [Completion Patterns](#completion-patterns)
4. [macOS Keychain Security](#macos-keychain-security)
5. [Structured Documentation Standard](#structured-documentation-standard)

---

## User's Established Patterns

Proven patterns from existing `$ZDOTDIR/functions/` implementations.

### Pattern 1: xargs Modularity

Dispatch work to subcommands using xargs for parallelization and modularity.

**Use case:** Functions that need to process multiple items, optionally in parallel

```bash
#autoload
#!/usr/bin/env zsh

do_one() {
   echo "Do something with $1"
   cp -v "$1" /tmp
}

do_all() {
  tasks=(test1 test2 test3)
  echo $tasks | tr '\n' '\0' | xargs -n 1 -0 -- ${(%):-%x} do_one
}

do_all_parallel() {
  cat tasks.txt | tr '\n' '\0' | xargs -n 1 -0 -P 2 -- "$0" do_one
}

"$@"  # dispatch on $0
```

**Key features:**
- `do_one()`: Single-item worker function
- `do_all()`: Sequential processing
- `do_all_parallel()`: Parallel processing with `-P 2`
- Dispatch mechanism: `"$@"` allows function to act as both standalone and worker
- Null termination: Handles filenames with spaces/special chars

**When to use:**
- Batch operations on multiple files or items
- Need for parallel execution
- Want clear separation between worker and orchestrator logic

---

### Pattern 2: Inline Completions

Self-contained functions with completion logic included.

**Use case:** Simple commands with predictable option sets

```bash
#autoload

function music() {
  local opt=$1
  case "$opt" in
    play|pause|stop) ;;
    ""|--help|-h) echo "Usage: $0 <option>"; return 0 ;;
    *) print "Unknown option: $opt"; return 1 ;;
  esac
  osascript -e "tell application \"Music\" to $opt"
}

function _music() {
  local -a cmds
  cmds=(
    "play:Play Music"
    "pause:Pause Music"
    "stop:Stop Music"
    {-h,--help}":Show usage"
  )
  if (( CURRENT == 2 )); then
    _describe 'command' cmds
  fi
}

compdef _music music
```

**Key features:**
- Function logic and completion in same file
- `_describe` for command list with descriptions
- `CURRENT` to determine position in command line
- `compdef` to register completion function

**When to use:**
- Simple commands with fixed options
- Options don't need complex logic to complete
- Want everything in one file

---

### Pattern 3: Credential Security

Manage secrets safely using macOS Keychain.

**Use case:** Functions that need to store/retrieve sensitive data

```bash
#autoload
#!/usr/bin/env zsh

main() {
  local verb=$1
  case "$verb" in
    list|ls) list_secrets ;;
    get) shift; get_secret "$@" ;;
    set) shift; set_secret "$@" ;;
    delete|rm) shift; delete_secret "$@" ;;
    *) print_usage ;;
  esac
}

print_usage() {
  NAME=$(basename "${(%):-%x}")
  cat << EOF
Usage:
  $NAME set <name> <value>
  $NAME get <name>
  $NAME rm <name>
  $NAME ls
EOF
}

get_secret() {
  local service=${1}
  security find-generic-password -a "$USER" -s "$service" -w
}

set_secret() {
  local service=$1 secret=$2
  # Idempotent: delete first if exists
  security delete-generic-password -a "$USER" -s "$service" 2>/dev/null
  security add-generic-password -a "$USER" -s "$service" -w "$secret"
}

"${@:-main}"
```

**Key features:**
- `main()` function acts as dispatcher
- Helper functions for each operation
- Keychain commands wrapped for consistency
- Idempotent set operation (delete then add)
- Usage function for documentation

**When to use:**
- Need to store API keys, tokens, or passwords
- Want secure credential management
- Need to share credentials with other scripts

---

## Zsh Plugin Standard Conventions

Best practices from [Zsh Plugin Standard v1.1.5](https://zdharma-continuum.github.io/Zsh-100-Commits-Club/Zsh-Plugin-Standard.html).

### Standard $0 Handling

Reliable way to get the function's own path:

```bash
0="${ZERO:-${${0:#$ZSH_ARGZERO}:-${(%):-%N}}}"
0="${${(M)0:#/*}:-$PWD/$0}"
# Then ${0:h} to get function's directory
```

Use this in functions that need to reference files in their own directory.

### Standard Recommended Options

Set at function start for consistent behavior:

```bash
emulate -L zsh
setopt extended_glob warn_create_global typeset_silent \
       no_short_loops rc_quotes no_auto_pushd
```

**Explanation:**
- `emulate -L zsh`: Emulate zsh in local scope
- `extended_glob`: Enable extended glob patterns
- `warn_create_global`: Warn when creating global variables
- `typeset_silent`: Suppress output from typeset
- `no_short_loops`: Disable short loop syntax
- `rc_quotes`: Enable rc-style quote escaping
- `no_auto_pushd`: Don't auto-pushd with cd

### Standard Recommended Variables

Reserve these for standard purposes:

```bash
local MATCH REPLY; integer MBEGIN MEND
local -a match mbegin mend reply
```

These are used by regex operations and completion system.

### Function Naming Prefixes

Adopt prefixes to signal function purpose:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `.` | Private/internal functions | `.myapp_get_value` |
| `→` | Hook functions (precmd, zle) | `→myapp_precmd` |
| `+` | Output/logging functions | `+myapp_log` |
| `/` | Debug functions | `/myapp_debug` |
| `@` | API-like functions | `@myapp_run_callback` |
| (none) | Public functions | `myapp_run`, `myapp_status` |

### Parameter Naming Conventions

Follow consistent naming by type:

| Type | Case | Example | Scope |
|------|------|---------|-------|
| Arrays | lowercase | `reply`, `match`, `items` | Local or global |
| Scalars (global) | UPPERCASE | `REPLY`, `MATCH`, `CONFIG` | Global only |
| Scalars (local) | lowercase | `local name`, `local count` | Local only |
| Hashes | Capitalized | `Plugins`, `Config`, `MyHash` | Global |

### Standard Plugins Hash

For plugin metadata:

```bash
typeset -gA Plugins
Plugins[MY_PLUGIN_REPO_DIR]="${0:h}"
Plugins[MY_PLUGIN_STATE]="initialized"
```

### Directory Structure for Plugin Functions

Standard plugin layout:

```
my-plugin/
├── my-plugin.plugin.zsh    # Main plugin file
├── functions/              # Autoload functions
│   ├── my_function         # Executable function (no extension)
│   └── _my_function        # Completion function
└── bin/                    # Executables
    └── my-script
```

### Preventing Function Pollution

Clean up temporary functions on exit:

```bash
typeset -g prjef
prjef=( ${(k)functions} )
trap "unset -f -- \"${(k)functions[@]:|prjef}\" &>/dev/null; unset prjef" EXIT
trap "unset -f -- \"${(k)functions[@]:|prjef}\" &>/dev/null; unset prjef; return 1" INT
```

This saves initial function list, then cleans up any added functions on exit.

---

## Completion Patterns

Reference: [zsh-completions-howto](https://github.com/zsh-users/zsh-completions/blob/master/zsh-completions-howto.org) and [A Guide to Zsh Completion](https://thevaluable.dev/zsh-completion-guide-examples/)

### Basic `_describe` Pattern

Simplest completion for command lists:

```bash
_mycommand() {
  local -a commands
  commands=(
    'start:Start the service'
    'stop:Stop the service'
    'status:Show status'
  )
  _describe 'command' commands
}
compdef _mycommand mycommand
```

**When to use:** Simple commands with fixed subcommands

### `_arguments` Pattern

For complex option parsing:

```bash
_mycommand() {
  _arguments \
    '-h[Show help]' \
    '-v[Verbose output]' \
    '-f[Force operation]' \
    '1:command:(start stop status)' \
    '*:file:_files'
}
```

**Features:**
- `-h`, `-v`, `-f`: Options with descriptions
- `1:command:(start stop status)`: First positional arg is command
- `*:file:_files`: Any remaining args are files

### Subcommand with State

Handle different completions based on subcommand:

```bash
_mycommand() {
  local -a cmds
  cmds=(
    'start:Start service'
    'stop:Stop service'
  )

  if (( CURRENT == 2 )); then
    _describe 'command' cmds
  elif (( CURRENT == 3 )); then
    case "$words[2]" in
      start) _describe 'option' '(--daemon --foreground)' ;;
      stop) _describe 'option' '(--force --graceful)' ;;
    esac
  fi
}
```

**Variables available in completion functions:**
- `CURRENT`: Current word position (1-indexed)
- `words`: Array of all words in command line
- Use these to provide context-aware completions

---

## macOS Keychain Security

Safe credential storage for shell scripts and functions.

### Basic Operations

```bash
# Store secret
security add-generic-password -s 'service-name' -a "$USER" -w 'secret-value'

# Retrieve secret
security find-generic-password -s 'service-name' -a "$USER" -w

# Delete secret
security delete-generic-password -s 'service-name' -a "$USER"

# Check if exists (via return code)
security find-generic-password -s 'service-name' -a "$USER" &>/dev/null
```

### Wrapper Function Pattern

For cleaner, reusable operations:

```bash
keychain_get() {
  local service="$1"
  local account="${2:-$USER}"
  security find-generic-password -s "$service" -a "$account" -w 2>/dev/null
}

keychain_set() {
  local service="$1"
  local secret="$2"
  local account="${3:-$USER}"
  # Delete existing first (idempotent)
  security delete-generic-password -s "$service" -a "$account" 2>/dev/null
  security add-generic-password -s "$service" -a "$account" -w "$secret"
}

keychain_exists() {
  local service="$1"
  local account="${2:-$USER}"
  security find-generic-password -s "$service" -a "$account" &>/dev/null
}
```

### Security Best Practices

- Never hardcode secrets in function files
- Use keychain for all credential storage
- Prompt interactively for secrets when needed
- Consider screen recording detection before printing secrets
- Use service names with consistent prefixes (e.g., `myapp:api-key`)
- Always use `-w` flag to extract just the password (not the full output)

---

## Structured Documentation Standard

Enable self-documentation and potential tooling:

```bash
#autoload
#!/usr/bin/env zsh
# @name: myfunction
# @version: 1.0.0
# @description: Brief description of what this function does
# @usage: myfunction [options] <command> [args...]
# @option: -h|--help: Show this help message
# @option: -v|--verbose: Enable verbose output
# @subcommand: start: Start the service
# @subcommand: stop: Stop the service
# @subcommand: status: Show current status
# @example: myfunction start --verbose
# @example: myfunction stop
# @requires: jq, fzf
# @author: Your Name
```

### Help Generator Pattern

Extract and display structured comments:

```bash
print_help() {
  # Extract from structured comments
  local script="${(%):-%x}"
  grep '^# @' "$script" | sed 's/^# @//' | while read -r line; do
    case "$line" in
      name:*) echo "Name: ${line#name: }" ;;
      description:*) echo "${line#description: }" ;;
      usage:*) echo "Usage: ${line#usage: }" ;;
      option:*) echo "  ${line#option: }" ;;
      subcommand:*) echo "  ${line#subcommand: }" ;;
      example:*) echo "Example: ${line#example: }" ;;
    esac
  done
}
```

**Benefits:**
- Single source of truth for documentation
- Self-documenting code
- Can generate help automatically
- Machine-parseable for tooling

---

## Quick Reference: Pattern Selection

Choose your pattern based on needs:

| Need | Pattern | Complexity |
|------|---------|-----------|
| Simple command with few options | Inline Completions | Low |
| Batch processing, parallelization | xargs Modularity | Medium |
| Store/retrieve secrets | Credential Security | Medium |
| Complex argument parsing | `_arguments` | Medium |
| Multiple subcommands | Subcommand with State | Medium |

---

## Resources

- [Zsh Plugin Standard](https://wiki.zshell.dev/community/zsh_plugin_standard)
- [Zsh Official Functions Documentation](https://zsh.sourceforge.io/Doc/Release/Functions.html)
- [zsh-async](https://github.com/mafredri/zsh-async) - Async operations
- [zsh-osx-keychain plugin](https://github.com/onyxraven/zsh-osx-keychain) - Real-world keychain integration
- [Scripting OS X - Keychain Passwords](https://scriptingosx.com/2021/04/get-password-from-keychain-in-shell-scripts/) - macOS security patterns
