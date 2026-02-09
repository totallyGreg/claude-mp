# Terminal-Guru: Zsh Function Patterns Reference Enhancement

## Objective

Enhance terminal-guru's reference documentation with comprehensive zsh function development patterns, incorporating:
- User's preferred patterns from existing `$ZDOTDIR/functions/`
- Zsh Plugin Standard (zdharma-continuum) conventions
- Completion system best practices
- macOS keychain security patterns

**Approach:** Reference documentation only (no new scripts). Claude will use these patterns when generating functions.

**Related Issue:** [#12 - Migrate and triage planned improvements](https://github.com/totallyGreg/claude-mp/issues/12)
- Supports Issue #12's goal: reduce SKILL.md complexity (currently 588 lines) by moving detailed patterns to dedicated references
- Establishes reference documentation strategy enabling terminal-guru to generate functions using established patterns
- Part of broader effort to maintain SKILL.md as quick reference + pointers to external documentation

## Research Sources

### Primary Standards
- [Zsh Plugin Standard v1.1.5](https://zdharma-continuum.github.io/Zsh-100-Commits-Club/Zsh-Plugin-Standard.html) - zdharma-continuum
- [Z-Shell Wiki Plugin Standard](https://wiki.zshell.dev/community/zsh_plugin_standard)
- [Zsh Official Functions Documentation](https://zsh.sourceforge.io/Doc/Release/Functions.html)

### Completion Resources
- [zsh-completions-howto](https://github.com/zsh-users/zsh-completions/blob/master/zsh-completions-howto.org)
- [A Guide to Zsh Completion](https://thevaluable.dev/zsh-completion-guide-examples/)

### Async Operations
- [zsh-async](https://github.com/mafredri/zsh-async) - Asynchronous task execution framework

### Security Resources
- [zsh-osx-keychain plugin](https://github.com/onyxraven/zsh-osx-keychain)
- [Scripting OS X - Keychain Passwords](https://scriptingosx.com/2021/04/get-password-from-keychain-in-shell-scripts/)

---

## User's Existing Patterns

Based on examination of functions in `$ZDOTDIR/functions/`:

### Pattern 1: xargs Modularity (`test_copy`)
```bash
#autoload
#!/usr/bin/env zsh

do_one() {
   echo "Do something with $1"
   cp -v $1 /tmp
}

do_all() {
  tasks=(test1 test2 test3)
  echo $tasks | tr '\n' '\0' | xargs -n 1 -0 -- ${(%):-%x} do_one
}

do_all_parallel() {
  cat tasks.txt | tr '\n' '\0' | xargs -n 1 -0 -P 2 -- $0 do_one
}

"$@"  # dispatch on $0
```

### Pattern 2: Inline Completions (`music`)
```bash
#autoload

function music() {
  local opt=$1
  case "$opt" in
    play|pause|stop) ;;
    ""|-h|--help) echo "Usage: $0 <option>"; return 0 ;;
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

### Pattern 3: Credential Security (`passwords`)
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

"${@:-main}"
```

---

## Zsh Plugin Standard Conventions

### Standard `$0` Handling
```bash
0="${ZERO:-${${0:#$ZSH_ARGZERO}:-${(%):-%N}}}"
0="${${(M)0:#/*}:-$PWD/$0}"
# Then ${0:h} to get function's directory
```

### Standard Recommended Options
```bash
emulate -L zsh
setopt extended_glob warn_create_global typeset_silent \
       no_short_loops rc_quotes no_auto_pushd
```

### Standard Recommended Variables
```bash
local MATCH REPLY; integer MBEGIN MEND
local -a match mbegin mend reply
```

### Function Naming Prefixes

| Prefix | Purpose | Example |
|--------|---------|---------|
| `.` | Private functions | `.myapp_get_value` |
| `→` | Hook functions (precmd, zle) | `→myapp_precmd` |
| `+` | Output/logging functions | `+myapp_log` |
| `/` | Debug functions | `/myapp_debug` |
| `@` | API-like functions | `@myapp_run_callback` |

### Parameter Naming Convention

| Type | Case | Example |
|------|------|---------|
| Arrays | lowercase | `reply`, `match`, `items` |
| Scalars (global) | UPPERCASE | `REPLY`, `MATCH`, `CONFIG` |
| Scalars (local) | lowercase ok | `local name`, `local count` |
| Hashes | Capitalized | `Plugins`, `Config`, `MyHash` |

### Standard Plugins Hash
```bash
typeset -gA Plugins
Plugins[MY_PLUGIN_REPO_DIR]="${0:h}"
Plugins[MY_PLUGIN_STATE]="initialized"
```

### Directory Structure
```
my-plugin/
├── my-plugin.plugin.zsh    # Main plugin file
├── functions/              # Autoload functions (added to fpath)
│   ├── my_function
│   └── _my_function        # Completion
└── bin/                    # Executables (added to PATH)
    └── my-script
```

### Preventing Function Pollution
```bash
typeset -g prjef
prjef=( ${(k)functions} )
trap "unset -f -- \"\${(k)functions[@]:|prjef}\" &>/dev/null; unset prjef" EXIT
trap "unset -f -- \"\${(k)functions[@]:|prjef}\" &>/dev/null; unset prjef; return 1" INT
```

---

## Completion Patterns

### Basic `_describe` Pattern
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

### `_arguments` Pattern
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

### Subcommand with State
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

---

## macOS Keychain Security Patterns

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

---

## Structured Comment Standard (Proposed)

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

---

## Implementation Tasks

| Priority | Task | Description | Issue #12 Impact |
|----------|------|-------------|------------------|
| P1 | Create `references/zsh_function_patterns.md` | Consolidate all patterns above | Moves content from SKILL.md |
| P1 | Update `references/zsh_configuration.md` | Add Plugin Standard conventions | Enriches existing reference |
| P2 | Extract `references/zshguide/` | Extract from zshguide_html.tar.gz | Reduces SKILL.md load |
| P2 | Add `references/zsh_completion_guide.md` | Completion-specific patterns | Progressive disclosure strategy |
| P3 | Update SKILL.md description | Add function generation trigger phrases | Clarifies skill capability |
| P3 | Add examples to `examples/` | Sample functions using patterns | Demonstrates reference usage |

## File Structure After Implementation

```
skills/terminal-guru/
├── SKILL.md (minor updates to description)
├── IMPROVEMENT_PLAN.md
├── scripts/                        # Existing (no changes)
│   ├── install_autoload.sh
│   └── ...
├── references/
│   ├── zsh_function_patterns.md    # NEW: Comprehensive patterns guide
│   ├── zsh_completion_guide.md     # NEW: Completion-specific guide
│   ├── zsh_configuration.md        # UPDATED: Add Plugin Standard
│   ├── zshguide/                   # NEW: Extracted official guide
│   ├── terminfo_guide.md           # Existing
│   ├── unicode_troubleshooting.md  # Existing
│   └── isolated_environments.md    # Existing
└── examples/
    ├── simple_function             # NEW: Example using patterns
    ├── subcommand_function         # NEW: With completions
    └── secure_function             # NEW: Keychain integration
```

## Success Criteria

1. **Pattern Coverage:** All user patterns documented with Plugin Standard alignment
2. **Completion Guidance:** Clear examples for `_describe` and `_arguments`
3. **Security Patterns:** Keychain wrappers documented with best practices
4. **Self-Documentation:** Structured comment standard defined
5. **Reference Organization:** Logical split between configuration and patterns

## P3: SKILL.md Trigger Phrases

For the SKILL.md description update, use these trigger phrases to clarify when to invoke terminal-guru for function generation:

### Direct Triggers (High Priority)
- "generate a zsh function"
- "create an autoload function with completions"
- "write a zsh function that..."
- "make a zsh function following best practices"

### Pattern-Based Triggers (Medium Priority)
- "create a subcommand function" (Pattern 2: Inline Completions)
- "write a modular zsh function using xargs" (Pattern 1: xargs Modularity)
- "implement a secure function with keychain integration" (Pattern 3: Credential Security)
- "create a zsh function with async operations"

### Context Triggers (User Intent)
- "I need a zsh function that handles secrets/passwords"
- "create a function with command completions"
- "write a dispatcher function for multiple subcommands"
- "implement a function following the Zsh Plugin Standard"

### Proposed SKILL.md Description Enhancement

**Current:** "Zsh function creation and installation"

**Enhanced to:**
- Zsh autoload function generation with completions
- Pattern-based function creation (modular dispatch, subcommands, security)
- Generating functions following Zsh Plugin Standard conventions
- Implementing secure functions with keychain integration
- Creating async-capable zsh functions

### Proposed Frontmatter Update

Add to the YAML description to explicitly mention function generation:

```yaml
description: This skill should be used when configuring, diagnosing, fixing, or understanding Unix terminals, including terminfo database issues, shell configuration (especially Zsh autoload functions and fpath), Unicode/UTF-8 character rendering problems, TUI applications, terminal emulator settings, **generating zsh functions using established patterns**, and comprehensive zsh testing with isolated environments for performance optimization and plugin compatibility validation.
```

Key additions: "**generating zsh functions using established patterns**"

## Metrics Impact

| Metric | Current | Target | Rationale |
|--------|---------|--------|-----------|
| Conciseness | 36 | 40-45 | Reference-only approach keeps SKILL.md lean |
| Complexity | 66 | 68-70 | Minimal increase from reference additions |
| Spec Compliance | 80 | 85-90 | Fix trigger phrases in description |
| Progressive Disclosure | 100 | 100 | Patterns in references, not SKILL.md |
| Description | 60 | 80-85 | Add function generation triggers |

## Version

**Target version:** 2.1.0 (MINOR - new reference documentation)

---

## How This Plan Addresses Issue #12

[#12 - Migrate and triage planned improvements](https://github.com/totallyGreg/claude-mp/issues/12) identified that terminal-guru's IMPROVEMENT_PLAN.md needed triage and that SKILL.md (588 lines) had grown too large. This plan directly addresses those concerns:

### Reducing SKILL.md Complexity

**Current state:** SKILL.md contains detailed pattern documentation inline, contributing to high line count.

**This plan's solution:**
- Move comprehensive pattern examples → `references/zsh_function_patterns.md` (P1)
- Move completion details → `references/zsh_completion_guide.md` (P2)
- Keep SKILL.md focused on "what" and "when to use" with pointers to references
- Estimated SKILL.md reduction: 50-80 lines through externalization

### Supporting Issue #12's Triaging Strategy

Issue #12 poses three options for planned improvements. This plan implements **Option B (partial) + Option C**:
- **Option B**: Archive comprehensive designs to docs/plans/ ✓ (this document)
- **Option C**: Create focused improvements with clear scope ✓ (reference documentation is well-scoped)
- Avoids **Option A** (large implementation projects) by keeping work to documentation only

### Workflow Integration

This plan follows the Issue #12 recommendation that IMPROVEMENT_PLAN.md be kept minimal (~100-300 lines) with GitHub Issues as source of truth. Upon completion, the updated IMPROVEMENT_PLAN.md will show:
- New reference files in Version History
- Link to this planning document in Archive section
- Metric improvements reflecting SKILL.md reduction
