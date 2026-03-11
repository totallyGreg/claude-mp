---
title: Rewrite keychainctl — consistent TUI for macOS keychain secrets
type: feat
status: completed
date: 2026-03-11
---

# Rewrite keychainctl — consistent TUI for macOS keychain secrets

A simpler, consistent CLI wrapper around macOS `security` for storing and retrieving environment variables without plaintext exposure. Primary use case: `ASANA_TOKEN=$(keychainctl get CLAUDE_ASANA)`.

## Current Problems

The existing `~/bin/keychainctl` has several issues:

1. **Security**: `set_secret` echoes the full command including password in plaintext to stdout
2. **Inconsistent args**: Each subcommand handles arguments differently (arg count, ordering, defaults)
3. **No error handling**: No `set -e`, no input validation, no friendly error messages
4. **Broken quoting**: `main $@` instead of `main "$@"` — breaks secret names with spaces
5. **Scope leaks**: `select_keychain` exports to global environment unnecessarily
6. **`-D kind` mismatch**: `set` tags entries with `-D "secret"` but `get`/`delete` don't filter by kind
7. **delete bug**: `$KEYCHAIN` not set correctly when `$2` is provided in `delete_secret`
8. **stdout/stderr mixing**: Informational output goes to stdout, breaking `$(...)` capture

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Format | Standalone bash script | Portable, no zsh dependency |
| Location | `plugins/terminal-guru/skills/zsh-dev/scripts/keychainctl` | Always available via terminal-guru plugin |
| fzf | Optional dependency | Used for `ls` and interactive `get` when available + TTY attached |
| Default keychain | `login.keychain` | Overridable via `KEYCHAINCTL_KEYCHAIN` env var |
| System keychain | Excluded from `ls` listing | Still accessible via explicit argument |
| `-D kind` | Drop entirely | Use default "application password" kind consistently across all operations |
| stdout contract | `get` → password only; `ls` → names only; everything else → stderr | Critical for `$(...)` scripting use case |
| `set` without value | Prompt via `/dev/tty` | More secure — avoids `ps` and shell history exposure |
| Keychain suffix | Auto-append `.keychain` if missing | Users can type `login` or `login.keychain` — both work |
| `pluginkit` | Not relevant | CryptoTokenKit hardware token management, not secret storage |

## Keychain Resolution Precedence

Single function `resolve_keychain()` with this priority:

1. Explicit argument (highest)
2. `KEYCHAINCTL_KEYCHAIN` env var
3. fzf interactive selection (if available AND stdin is a TTY)
4. `login.keychain` default (lowest)

All keychain names are normalized: if the value doesn't end in `.keychain` or `.keychain-db`, `.keychain` is appended automatically. Always filter out `System.keychain` from listings. Pass normalized names through to `security` as-is.

## Acceptance Criteria

- [x] `ASANA_TOKEN=$(keychainctl get CLAUDE_ASANA)` works — only password on stdout
- [x] `keychainctl set NAME VALUE [keychain]` stores secret silently (no plaintext echo)
- [x] `keychainctl set NAME` (no value) prompts for password via `/dev/tty`
- [x] `keychainctl rm NAME [keychain]` deletes secret
- [x] `keychainctl ls [keychain]` lists secret names (one per line, fzf when available + TTY)
- [x] `keychainctl` or `keychainctl --help` prints usage
- [x] Keychain names auto-suffixed: `login` → `login.keychain`
- [x] All informational/error output goes to stderr
- [x] Friendly error messages for common failures (not found, keychain doesn't exist)
- [x] `set -euo pipefail` with proper error trapping
- [x] Secret names with spaces work correctly (`keychainctl get 'acme API key'`)
- [x] No fzf invocation when stdin/stdout is not a TTY (safe in pipes/scripts)
- [x] Works without fzf installed (graceful degradation)
- [x] Follows repo shell script conventions (colored stderr output, `die()` function)

## MVP

### keychainctl

```bash
#!/usr/bin/env bash
set -euo pipefail

# Colors (stderr only)
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}$*${NC}" >&2; }
warn()  { echo -e "${YELLOW}$*${NC}" >&2; }
die()   { echo -e "${RED}error:${NC} $*" >&2; exit 1; }

KEYCHAINCTL_KEYCHAIN="${KEYCHAINCTL_KEYCHAIN:-login.keychain}"

has_fzf() { command -v fzf &>/dev/null; }
is_tty()  { [[ -t 0 ]] && [[ -t 1 ]]; }

# Normalize keychain name: auto-append .keychain if missing
normalize_keychain() {
  local kc="$1"
  if [[ "$kc" != *.keychain && "$kc" != *.keychain-db ]]; then
    echo "${kc}.keychain"
  else
    echo "$kc"
  fi
}

resolve_keychain() {
  local raw
  # 1. Explicit argument
  if [[ -n "${1:-}" ]]; then
    raw="$1"
  # 2. fzf interactive (if available + TTY)
  elif has_fzf && is_tty; then
    raw=$(security list-keychains | xargs -I{} basename {} '-db' \
      | grep -v '^System\.keychain$' | fzf --prompt="Keychain> ") || true
  fi
  # 3. Default (env var or login.keychain)
  normalize_keychain "${raw:-$KEYCHAINCTL_KEYCHAIN}"
}

cmd_get() {
  local name="${1:-}" keychain
  keychain=$(resolve_keychain "${2:-}")
  if [[ -z "$name" ]]; then
    # Interactive: browse secrets with fzf
    if has_fzf && is_tty; then
      name=$(security dump-keychain "$keychain" \
        | awk -F= '/0x00000007/ {print $2}' | tr -d '"' \
        | fzf --prompt="Secret> ") || die "No secret selected"
    else
      die "Usage: keychainctl get <name> [keychain]"
    fi
  fi
  security find-generic-password -a "$USER" -s "$name" -w "$keychain" 2>/dev/null \
    || die "Secret '$name' not found in $keychain"
}

cmd_set() {
  local name="${1:-}" value="${2:-}" keychain
  [[ -z "$name" ]] && die "Usage: keychainctl set <name> [value] [keychain]"
  if [[ -z "$value" ]]; then
    # Prompt for password securely
    read -rsp "Password for '$name': " value < /dev/tty
    echo >&2  # newline after hidden input
    [[ -z "$value" ]] && die "Password cannot be empty"
    keychain=$(resolve_keychain "${2:-}")
  else
    keychain=$(resolve_keychain "${3:-}")
  fi
  security add-generic-password -U -a "$USER" -s "$name" -w "$value" "$keychain" \
    || die "Failed to store secret '$name' in $keychain"
  info "Secret '$name' stored in $keychain"
}

cmd_rm() {
  local name="${1:-}" keychain
  [[ -z "$name" ]] && die "Usage: keychainctl rm <name> [keychain]"
  keychain=$(resolve_keychain "${2:-}")
  security delete-generic-password -a "$USER" -s "$name" "$keychain" &>/dev/null \
    || die "Secret '$name' not found in $keychain"
  info "Secret '$name' deleted from $keychain"
}

cmd_ls() {
  local keychain
  keychain=$(resolve_keychain "${1:-}")
  local secrets
  secrets=$(security dump-keychain "$keychain" \
    | awk -F= '/0x00000007/ {print $2}' | tr -d '"' | sort -u)
  if has_fzf && is_tty; then
    echo "$secrets" | fzf --prompt="Secrets in $keychain> "
  else
    echo "$secrets"
  fi
}

print_usage() {
  cat >&2 << EOF
Usage: $(basename "$0") <command> [args]

Commands:
  get <name> [keychain]    Retrieve a secret (password only to stdout)
  set <name> [value] [kc]  Store a secret (prompts if value omitted)
  rm  <name> [keychain]    Delete a secret
  ls  [keychain]           List secrets (interactive with fzf if available)

Environment:
  KEYCHAINCTL_KEYCHAIN     Default keychain (default: login.keychain)

Keychain names are auto-suffixed: 'login' becomes 'login.keychain'.

Examples:
  ASANA_TOKEN=\$(keychainctl get CLAUDE_ASANA)
  keychainctl set CLAUDE_ASANA              # prompts for password
  keychainctl set CLAUDE_ASANA sk-12345
  keychainctl ls work                       # lists secrets in work.keychain
EOF
  exit 0
}

case "${1:-}" in
  get)        shift; cmd_get "$@" ;;
  set)        shift; cmd_set "$@" ;;
  rm|delete)  shift; cmd_rm "$@" ;;
  ls|list)    shift; cmd_ls "$@" ;;
  -h|--help|"") print_usage ;;
  *)          die "Unknown command: $1. Run '$(basename "$0") --help' for usage." ;;
esac
```

## Sources

- Current script: `~/bin/keychainctl`
- Keychain patterns: `plugins/terminal-guru/skills/zsh-dev/references/zsh_function_patterns.md` (Pattern 3: Credential Security)
- CLI reference: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/ofo` (subcommand dispatch pattern)
- Shell conventions: `set -euo pipefail`, colored stderr, `die()` — consistent across repo scripts
- `security(1)` man page: `find-generic-password`, `add-generic-password`, `delete-generic-password`, `dump-keychain`, `list-keychains`
- `pluginkit(8)`: CryptoTokenKit hardware token management — not relevant to this use case
