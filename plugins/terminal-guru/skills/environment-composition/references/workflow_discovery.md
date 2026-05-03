# Workflow Discovery

## Overview

Workflow discovery identifies patterns in how the user works — repeated commands, tool preferences, directory habits — and suggests graduating them into reusable automation. Discovery operates in two modes:

- **Passive**: agent records patterns it observes during sessions into the profile's `workflow_patterns` section
- **Active**: the `/workflow-discover` command scans multiple signal sources for a comprehensive analysis

---

## Signal Sources

### 1. Command History

Parse `$HISTFILE` (typically `~/.zsh_history`) for frequently repeated commands and multi-command sequences.

```bash
# Top 20 commands by frequency
fc -l -1000 | awk '{$1=""; print}' | sort | uniq -c | sort -rn | head -20

# Find repeated sequences (commands run in succession)
# Look for patterns like: git pull → mise run lint → mise run test
```

**What to extract**: individual command frequency, multi-command sequences, tool-specific usage counts.

**Security boundary**: skip lines containing `token`, `password`, `secret`, `key=`, `apikey`, `bearer`, `Authorization`. Report command names and flags only, never argument values that could contain secrets.

### 2. Zoxide Frecency

Zoxide tracks directory visit frequency and recency (frecency). High-frecency directories indicate active projects.

```bash
# Top directories by frecency score
zoxide query -ls | head -20
```

**What to extract**: most-visited project directories, mapping between directories and the commands used in them.

### 3. Homebrew Inventory

Homebrew reveals the tool landscape — what's installed, what's actively maintained, what's stale.

```bash
# All installed formulae with versions
brew list --versions

# Recently installed (last 7 days)
brew list --formula | while read pkg; do
  install_date=$(stat -f %Sm -t %Y-%m-%d $(brew --prefix)/Cellar/$pkg 2>/dev/null)
  echo "$install_date $pkg"
done | sort -r | head -20

# Cask apps
brew list --cask --versions
```

**Adoption signals**:
- Installed in last 7 days → exploring (don't build workflows around it yet)
- Updated in last 30 days → active use (safe to compose with)
- Not updated in 6+ months → check if still in use

### 4. XDG_CONFIG_HOME

Tools with config directories in `~/.config/` are actively configured — a stronger signal than mere installation.

```bash
# List actively configured tools
ls ${XDG_CONFIG_HOME:-~/.config}/

# Compare against brew list to find "installed but unconfigured" tools
comm -23 <(brew list --formula | sort) <(ls ~/.config/ | sort)
```

**What to extract**: which tools the user has customized, potential for discovering tools with config but unused or vice versa.

### 5. Git Log

Repository-specific workflow patterns — what the user does in this project.

```bash
# Recent commit patterns
git log --oneline -50

# Files changed most frequently (workflow hotspots)
git log --pretty=format: --name-only -50 | sort | uniq -c | sort -rn | head -20
```

---

## Discovery Output Format

The discovery script produces a structured report:

```
## Tool Landscape
Installed: 47 brew formulae, 12 casks
Actively configured (XDG): mise, sesh, ghostty, bat, fzf, ...
Recently added: television (2 days ago), jnv (5 days ago)

## Top Command Patterns
1. git pull → mise run lint → mise run test (seen 12 times)
   → Suggested graduation: mise task with depends_post
2. fd --type f | fzf --preview 'bat {}' | xargs vim (seen 8 times)
   → Suggested graduation: zsh function (shell context needed)
3. brew update && brew upgrade (seen 6 times)
   → Suggested graduation: mise task (no shell context needed)

## Tool Preferences
| Tool | Uses (30d) | Preferred For |
|------|-----------|---------------|
| fzf | 87 | branch selection, file search |
| rg | 63 | code search |
| bat | 45 | file preview |
| fd | 38 | file finding |
| mise | 34 | task running, env management |

## Recommendations
- Consider graduating pattern #1 to a mise task
- Your fzf usage is high — check fzf_composition.md for advanced patterns
- television was recently installed — explore tv channels for file search
```

---

## Profile Integration

After discovery, the agent offers to update the profile:

### workflow_patterns section

```yaml
workflow_patterns:
  morning_routine:
    commands: ["git pull", "mise run lint", "mise run test"]
    frequency: 12
    suggested_graduation: "mise_task"
    status: observed        # observed → suggested → graduated
  file_edit:
    commands: ["fd --type f", "fzf --preview 'bat {}'", "xargs vim"]
    frequency: 8
    suggested_graduation: "function"
    status: suggested
```

### tool_preferences section

```yaml
tool_preferences:
  fzf:
    use_count: 87
    last_used: "2026-05-03"
    preferred_for: ["branch selection", "file search"]
  rg:
    use_count: 63
    last_used: "2026-05-03"
    preferred_for: ["code search"]
```

---

## Version Auto-Detection

When the profile has empty `versions:` fields, the agent runs version detection:

```bash
mise --version 2>/dev/null | head -1
tmux -V 2>/dev/null
sesh --version 2>/dev/null
zsh --version 2>/dev/null
```

The agent suggests updating the profile with discovered versions. This helps tailor advice to version-specific features.
