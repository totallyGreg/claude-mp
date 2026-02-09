# Zsh Completion Guide

Comprehensive guide to writing zsh completion functions. Completions make commands discoverable and reduce typing by providing context-aware suggestions.

## Table of Contents

1. [Completion Basics](#completion-basics)
2. [Core Completion Functions](#core-completion-functions)
3. [Practical Patterns](#practical-patterns)
4. [Advanced Techniques](#advanced-techniques)
5. [Testing and Debugging](#testing-and-debugging)

---

## Completion Basics

### How Zsh Completions Work

When a user presses TAB:

1. Zsh identifies the command being completed
2. Loads the completion function (if it exists)
3. Completion function analyzes context (position, previous words, etc.)
4. Suggests completions based on context

### Completion Function Naming

Completion functions start with underscore followed by command name:

```bash
_mycommand      # Completion for 'mycommand'
_mycmd          # Completion for 'mycmd'
_git            # Completion for 'git'
```

### Registering Completions

Link a completion function to a command:

```bash
compdef _mycommand mycommand
```

Place this line in:
- The completion function file itself (after the function definition)
- `.zshrc` or a completion file loaded at startup

### Completion Context Variables

Available inside completion functions:

| Variable | Purpose | Example |
|----------|---------|---------|
| `CURRENT` | Position of cursor word (1-indexed) | In `cmd opt file`, if on `file`: `CURRENT=3` |
| `words` | Array of all words in command line | `words[1]` = command, `words[2]` = first arg |
| `LBUFFER` | Text to left of cursor | `"cmd opt "` |
| `RBUFFER` | Text to right of cursor | `"ile"` |
| `PREFIX` | Word being completed (from start) | `"fi"` when completing `"file"` |
| `SUFFIX` | Word being completed (to end) | `"le"` when completing `"file"` |
| `compstate` | Hash with completion state | `compstate[list]`, `compstate[insert]` |

---

## Core Completion Functions

### `_describe` - Simple Option Lists

**Use case:** Commands with a fixed set of subcommands or options

Simplest and most common completion function:

```bash
_mycommand() {
  local -a commands
  commands=(
    'start:Start the service'
    'stop:Stop the service'
    'restart:Restart the service'
    'status:Show current status'
    'logs:Display logs'
  )
  _describe 'command' commands
}
compdef _mycommand mycommand
```

**How to run it:**
```bash
# In zsh shell
mycommand [TAB]  # Shows: start  stop  restart  status  logs
mycommand st[TAB]  # Shows: start  status
```

**Syntax:** `'option:description'`
- Everything before the colon is what gets completed
- Everything after is shown to the user

#### Advanced `_describe`

Organize commands by group:

```bash
_mycommand() {
  local -a commands
  commands=(
    'service-management:Service operations'
    'start:Start the service'
    'stop:Stop the service'
    'restart:Restart the service'
    'monitoring:Status and logs'
    'status:Show current status'
    'logs:Display logs'
  )
  _describe 'command' commands
}
```

---

### `_arguments` - Complex Option Parsing

**Use case:** Commands with many options, flags, and different argument types

```bash
_mycommand() {
  _arguments \
    '-h[Show help message]' \
    '-v[Verbose output]' \
    '-f[Force operation]' \
    '-o[Output file]:output file:_files' \
    '1:command:(start stop status)' \
    '*:file:_files'
}
```

**Syntax:**
- `-option[description]` - Flag option
- `-option[description]:argument description:completion function` - Option with argument
- `position:description:(choices)` - Positional argument with choices
- `position:description:completion_function` - Positional argument with function
- `*:description:completion_function` - Remaining arguments

**Examples:**

```bash
_mycommand() {
  _arguments \
    '-h[Show help]' \
    '-c[Config file]:config:_files -g "*.conf"' \
    '-t[Timeout]:seconds:(10 30 60 120)' \
    '1:action:(build test deploy)' \
    '2:environment:(dev staging prod)'
}
```

**Common completion functions to use:**
- `_files` - File completion
- `_files -g "*.txt"` - Filter to specific extension
- `_directories` - Directory completion
- `_command_names` - Available commands
- `_users` - System users
- `_groups` - System groups
- `_hosts` - Network hosts (from ~/.ssh/config, /etc/hosts)

---

### `_values` - Simple Values

**Use case:** Options that take specific value choices

```bash
_mycommand() {
  _values 'logging level' \
    'debug' \
    'info' \
    'warning' \
    'error' \
    'critical'
}
```

---

## Practical Patterns

### Pattern 1: Subcommand-Based Completion

Different completions based on first argument:

```bash
_mycmd() {
  local -a subcommands
  subcommands=(
    'start:Start the service'
    'stop:Stop the service'
    'restart:Restart the service'
    'status:Show status'
    'logs:Show logs'
  )

  # Position 1: Show subcommands
  if (( CURRENT == 2 )); then
    _describe 'command' subcommands
  # Positions 2+: Depend on the subcommand
  elif (( CURRENT >= 3 )); then
    case "$words[2]" in
      logs)
        _arguments '::log file:_files -g "*.log"'
        ;;
      start|restart)
        _arguments \
          '--daemon[Run in background]' \
          '--config[Config file]:config:_files'
        ;;
      *)
        ;;
    esac
  fi
}
compdef _mycmd mycmd
```

**How it works:**
- `CURRENT == 2` - User typing first argument (the subcommand)
- `CURRENT >= 3` - User typing arguments after subcommand
- `words[2]` - The subcommand that was chosen
- Use `case` to provide different completions per subcommand

### Pattern 2: State-Aware Completion

Track state as user completes:

```bash
_mycmd() {
  local -a hosts users
  hosts=(server1 server2 server3)
  users=(admin user guest)

  # First argument: choose host
  # Second argument: choose user (based on host)
  # Third argument: choose action

  if (( CURRENT == 2 )); then
    _describe 'host' hosts
  elif (( CURRENT == 3 )); then
    _describe 'user' users
  elif (( CURRENT == 4 )); then
    local -a actions
    actions=(
      'login:Log in to server'
      'logout:Log out'
      'restart:Restart service'
    )
    _describe 'action' actions
  fi
}
```

### Pattern 3: Dynamic Completions

Get completions from external source:

```bash
_deploy() {
  # Position 1: Available environments
  if (( CURRENT == 2 )); then
    local -a envs
    # Read from config file or API
    envs=$(grep "^\[" ~/.deploy/config | sed 's/\[//g; s/\]//g')
    _describe 'environment' envs

  # Position 2: Versions for that environment
  elif (( CURRENT == 3 )); then
    local env="$words[2]"
    local -a versions
    # Query external source for versions
    versions=$(curl -s "http://api.example.com/versions?env=$env" | jq -r '.[]')
    _describe 'version' versions
  fi
}
```

### Pattern 4: Combined `_arguments` and `_describe`

Mix different completion types:

```bash
_package_manager() {
  _arguments \
    '(-h --help)'{-h,--help}'[Show help]' \
    '(-v --version)'{-v,--version}'[Show version]' \
    '(-s --silent)'{-s,--silent}'[Silent mode]' \
    '1:action:->action' \
    '2:package:->package' && return 0

  case $state in
    action)
      local -a actions
      actions=(
        'install:Install package'
        'remove:Remove package'
        'search:Search packages'
        'update:Update package list'
        'upgrade:Upgrade packages'
      )
      _describe 'action' actions
      ;;
    package)
      # Get available packages from system
      _describe 'package' $(dpkg -l | awk '{print $2}')
      ;;
  esac
}
```

---

## Advanced Techniques

### Using `compstate` for Control

Control how completions are displayed:

```bash
_mycmd() {
  # ... completion logic ...

  # Show list of completions
  compstate[list]="list"

  # Insert only common prefix, don't complete
  compstate[insert]="unambiguous"

  # Insert first match
  compstate[insert]="menu"
}
```

### Custom Message

Add instructional messages:

```bash
_mycmd() {
  local -a commands
  commands=(
    'start:Start the service'
    'stop:Stop the service'
  )

  _describe 'command' commands

  # Add a note at the end
  _message 'use "help" for more information'
}
```

### Caching Completions

Cache expensive completions:

```bash
_mycmd() {
  local -a hosts

  # Check cache
  if [[ -z "$_mycmd_hosts_cache" ]]; then
    _mycmd_hosts_cache=( $(cat ~/.hosts) )
  fi

  _describe 'host' $_mycmd_hosts_cache
}
```

### Completion Conditions

Only complete in certain situations:

```bash
_mycmd() {
  # Only show help option if command unknown
  if [[ "$words[1]" == "mycmd" && ! "$words[2]" =~ ^(start|stop|status)$ ]]; then
    _arguments '(-h --help)'{-h,--help}'[Show help]'
  fi
}
```

---

## Testing and Debugging

### Reload Completions

After editing a completion function:

```bash
# Method 1: Restart shell
exec zsh

# Method 2: Re-source .zshrc
source ~/.zshrc

# Method 3: Delete completion cache
rm ~/.zcompdump
# Then restart shell or run:
compinit
```

### Debug Completion Functions

Print debug info:

```bash
_mycmd_debug() {
  print "DEBUG: CURRENT=$CURRENT" >> /tmp/completion.log
  print "DEBUG: words=($words)" >> /tmp/completion.log
  print "DEBUG: PREFIX=$PREFIX" >> /tmp/completion.log
}

# Add debugging to your function
_mycmd() {
  _mycmd_debug
  # ... rest of function ...
}
```

### View What's Being Completed

Set `ZSHCOMPDEBUG`:

```bash
# In shell
export ZSHCOMPDEBUG=1

# Now completions will print debug info as they run
mycmd [TAB]

# Turn off
unset ZSHCOMPDEBUG
```

### Common Issues

**Issue: Completion not appearing**
- Check: Is completion file in `fpath`?
- Check: Is `compdef` registered correctly?
- Check: Did you reload completions (`rm ~/.zcompdump && compinit`)?

**Issue: Wrong completions showing**
- Check: Is `CURRENT` logic correct?
- Check: Are you checking the right `words` array position?
- Add debug output to see what's happening

**Issue: Completion is slow**
- Cache expensive results
- Use completion callbacks instead of running commands inline
- Profile with `_compstate`

---

## Complete Example: Multi-Level Completion

Real-world completion with multiple levels:

```bash
#compdef mydeploy

_mydeploy() {
  local -a envs apps

  # Get environments from config
  envs=(dev staging prod)
  apps=(web api worker)

  case $((CURRENT - 1)) in
    1)
      # First arg: choose environment
      _describe 'environment' envs
      ;;
    2)
      # Second arg: choose app
      _describe 'app' apps
      ;;
    3)
      # Third arg: choose action for that app
      local app="${words[3]}"
      case "$app" in
        web)
          _describe 'action' \
            '(start stop restart logs scale)' \
            '(restart:Restart the web server)'
          ;;
        api)
          _describe 'action' \
            '(start stop restart logs migrate)' \
            '(migrate:Run migrations)'
          ;;
        worker)
          _describe 'action' \
            '(start stop restart logs scale)' \
            '(scale:Scale worker processes)'
          ;;
      esac
      ;;
  esac
}
```

---

## Resources

- [Zsh Completion System](https://zsh.sourceforge.io/Doc/Release/Completion-System.html) - Official documentation
- [zsh-completions-howto](https://github.com/zsh-users/zsh-completions/blob/master/zsh-completions-howto.org) - Community guide
- [A Guide to Zsh Completion](https://thevaluable.dev/zsh-completion-guide-examples/) - Practical examples
- [Oh-My-Zsh Completions](https://github.com/ohmyzsh/ohmyzsh/tree/master/completions) - Real-world examples
