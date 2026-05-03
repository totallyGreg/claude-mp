#!/usr/bin/env bash
set -euo pipefail

# Workflow Discovery Script
# Scans multiple signal sources to build a picture of tool usage and workflow patterns.
# Outputs a structured report. Metrics and patterns only — never secrets.

HISTORY_LINES="${1:-1000}"
SECRET_PATTERN='(token|password|secret|key=|apikey|bearer|authorization|credential|passphrase)'

section() { printf "\n## %s\n\n" "$1"; }

# --- Tool Landscape ---
section "Tool Landscape"

brew_count=$(brew list --formula 2>/dev/null | wc -l | tr -d ' ')
cask_count=$(brew list --cask 2>/dev/null | wc -l | tr -d ' ')
echo "Installed: ${brew_count} brew formulae, ${cask_count} casks"

xdg_dir="${XDG_CONFIG_HOME:-$HOME/.config}"
if [[ -d "$xdg_dir" ]]; then
  configured=$(ls "$xdg_dir" 2>/dev/null | head -20 | tr '\n' ', ' | sed 's/,$//')
  echo "Actively configured (XDG): ${configured}"
fi

echo ""
echo "### Recently Installed (brew, last 14 days)"
brew list --formula 2>/dev/null | while read -r pkg; do
  cellar_path="$(brew --prefix 2>/dev/null)/Cellar/$pkg"
  if [[ -d "$cellar_path" ]]; then
    install_date=$(stat -f %Sm -t %Y-%m-%d "$cellar_path" 2>/dev/null || echo "unknown")
    echo "$install_date $pkg"
  fi
done | sort -r | head -10

# --- Command History ---
section "Top Command Patterns"

histfile="${HISTFILE:-$HOME/.zsh_history}"
if [[ -f "$histfile" ]]; then
  echo "Source: $histfile (last $HISTORY_LINES entries)"
  echo ""

  # Extract commands, strip timestamps (zsh extended history format: : epoch:0;command)
  # Filter out secrets
  tail -n "$HISTORY_LINES" "$histfile" 2>/dev/null \
    | sed 's/^: [0-9]*:[0-9]*;//' \
    | grep -ivE "$SECRET_PATTERN" \
    | awk '{print $1}' \
    | sort | uniq -c | sort -rn \
    | head -20 \
    | while read -r count cmd; do
        printf "%4d  %s\n" "$count" "$cmd"
      done
else
  echo "(No history file found at $histfile)"
fi

# --- Zoxide Frecency ---
section "Directory Frecency (zoxide)"

if command -v zoxide &>/dev/null; then
  zoxide query -ls 2>/dev/null | head -15 | while read -r score path; do
    printf "%8.1f  %s\n" "$score" "$path"
  done
else
  echo "(zoxide not installed)"
fi

# --- Git Log (current repo) ---
section "Recent Git Workflow (current repo)"

if git rev-parse --is-inside-work-tree &>/dev/null 2>&1; then
  echo "### Commit frequency by hour"
  git log --format='%H %ai' -50 2>/dev/null \
    | awk '{split($2,t,":"); print t[1]":00"}' \
    | sort | uniq -c | sort -rn | head -5

  echo ""
  echo "### Most-changed files (last 50 commits)"
  git log --pretty=format: --name-only -50 2>/dev/null \
    | grep -v '^$' | sort | uniq -c | sort -rn | head -10
else
  echo "(Not in a git repository)"
fi

# --- Tool Preferences Summary ---
section "Tool Preference Signals"

echo "| Tool | Installed | XDG Config | History Uses |"
echo "|------|-----------|------------|--------------|"

for tool in fzf rg bat fd mise tmux sesh zoxide gum tv; do
  installed="no"
  has_config="no"
  hist_count=0

  command -v "$tool" &>/dev/null && installed="yes"
  [[ -d "$xdg_dir/$tool" || -f "$xdg_dir/$tool" ]] && has_config="yes"

  if [[ -f "$histfile" ]]; then
    hist_count=$(tail -n "$HISTORY_LINES" "$histfile" 2>/dev/null \
      | sed 's/^: [0-9]*:[0-9]*;//' \
      | grep -icE "^$tool " 2>/dev/null || echo 0)
  fi

  echo "| $tool | $installed | $has_config | $hist_count |"
done

echo ""
echo "---"
echo "Security: commands matching /${SECRET_PATTERN}/ were excluded."
