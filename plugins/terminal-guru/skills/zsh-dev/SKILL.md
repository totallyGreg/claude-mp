---
name: zsh-dev
description: This skill should be used when the user asks to "create a zsh function", "configure fpath", "add a keychain secret", "set up keychainctl", "check shell startup", or needs help with autoload functions, completions, zsh testing, Plugin Standard compliance, storing tokens, retrieving secrets, or macOS keychain management via keychainctl. Do NOT use for terminal display issues or signal handling (use terminal-emulation or signals-monitoring skills instead).
license: MIT
compatibility: claude-code, Requires uv for Python script execution
metadata:
  version: "3.2.1"
---

# Zsh Development

## Overview

Create, test, and optimize Zsh shell configurations: autoload functions, fpath management, completions, function generation from established patterns, and a Python-based testing framework for safe experimentation in isolated environments.

## When to Use This Skill

- Zsh shell configuration (startup files, ZDOTDIR)
- Autoload function creation and management
- fpath configuration and troubleshooting
- Completion system setup (compinit)
- Function generation using established patterns
- Performance optimization (slow startup, plugin overhead)
- Plugin configuration and compatibility testing
- Safe testing of configuration changes
- Storing and retrieving secrets via macOS keychain (`keychainctl`)

## Zsh Function Generation

Use this skill to **generate, create, or write zsh functions** using established patterns:
- Direct function generation, with or without completions
- Specific patterns: xargs modularity, credential security, subcommand dispatcher
- Plugin Standard compliance and async operations

See `references/zsh_function_patterns.md` for pattern documentation and `references/zsh_completion_guide.md` for completion patterns.

## Core Capabilities

### Zsh Configuration and Autoload Functions

Refer to `references/zsh_configuration.md` for comprehensive guidance on startup file order, ZDOTDIR, autoload syntax, fpath management, compinit, debugging, and performance.

**Autoload function workflow:**

```bash
# 1. Create file (no extension, name = function name)
# 2. Install and configure fpath
bash scripts/install_autoload.sh myfunction ~/.zsh/functions/myfunction
# 3. Add to ~/.zshrc
fpath=(~/.zsh/functions $fpath); autoload -Uz myfunction
# 4. Reload after changes
unfunction myfunction; autoload -Uz myfunction
```

### Testing and Optimization Framework

Isolated test environments for safe experimentation. All test logic is in Python, eliminating the circular dependency of "shell testing shell."

- **Create:** `python3 scripts/environment_builder.py --create <name>`
- **Test:** `python3 scripts/terminal_test_runner.py --name <name> --suite all|performance`
- **Compare:** `python3 scripts/terminal_test_runner.py --compare baseline.json optimized.json`
- **Cleanup:** `python3 scripts/environment_builder.py --cleanup <path>`

See `references/isolated_environments.md` for the full testing workflow.

### Keychain Secret Management

The `keychainctl` script (zsh; needs only macOS built-ins `security` + `plutil`) stores secrets in the macOS keychain. Each secret is one item whose **Kind** records its format: `secret` (one value) or `json` (a bundle of named fields).

```bash
keychainctl set API_KEY                    # one value, hidden prompt
TOKEN=$(keychainctl get API_KEY)           # stdout only — safe for capture
keychainctl import TENANT                  # paste a JSON bundle (hidden, Ctrl-D) — nothing in history
pbpaste | keychainctl import TENANT        # …or from stdin / a file
keychainctl get TENANT CLIENT_SECRET       # one field; `get TENANT` prints KEY=val lines
keychainctl set TENANT -f CLIENT_SECRET    # add/rotate one field, others untouched
keychainctl rm TENANT -f OLD_FIELD         # remove one field (omit -f to delete the secret)
keychainctl ls -k work                     # optional fzf browse; -k selects the keychain
```

Guards (override with `--force`): `set`/`import` refuse to drop a bundle's existing fields, and refuse values containing whitespace, `$(` or a backtick (usually a paste/quoting mistake). Field names can't contain `.` (plutil key paths). The old `pair get|set|update` commands remain as compatibility aliases.

## Common Use Cases

### "I want to create a Zsh function"
1. Create file in `$ZDOTDIR/functions/` — see `references/zsh_function_patterns.md` for patterns
2. Install and add to fpath (workflow above)

### "My custom function isn't found"
1. `print -l $fpath` — verify directory is listed
2. `whence -v <name>` — check function location
3. Reload: `unfunction <name>; autoload -Uz <name>`

### "My zsh startup is slow"
1. Run: `python3 scripts/terminal_test_runner.py --name perf --suite performance`
2. Apply optimizations (lazy loading, defer plugins, cache compinit)
3. Re-test to verify

## Resources

### scripts/
- **`keychainctl`** - macOS keychain secret management CLI
- **`environment_builder.py`** - Isolated ZDOTDIR test environments
- **`terminal_test_runner.py`** - Automated test suites
- **`install_autoload.sh`** - Install autoload functions to fpath

### references/
- **`zsh_configuration.md`** - Comprehensive Zsh configuration guide
- **`zsh_function_patterns.md`** - Function generation patterns and templates
- **`zsh_completion_guide.md`** - Completion implementation patterns
- **`isolated_environments.md`** - ZDOTDIR isolation and testing workflows
