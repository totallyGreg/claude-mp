# fzf Composition Patterns

## The Universal Pattern

fzf transforms any list into an interactive selection workflow:

```
source | fzf [options] | action
```

Three stages: **source** produces lines, **fzf** filters and selects, **action** consumes the selection. Each stage is independently replaceable — that's the composition power.

---

## Core Options Reference

### Display & Layout

```bash
fzf --height 40%              # Inline (don't take full screen)
fzf --layout reverse           # Top-down instead of bottom-up
fzf --border rounded           # Add a border
fzf --header 'Select a branch' # Context header
fzf --prompt 'branch> '        # Custom prompt
```

### Preview

Preview shows context for the highlighted item without selecting it:

```bash
fzf --preview 'bat --color=always {}'          # File content
fzf --preview 'brew info {}'                    # Package info
fzf --preview 'git log --oneline -10 {}'        # Branch history
fzf --preview 'mise run --dry-run {}'           # Task dry-run
fzf --preview-window 'right:60%:wrap'           # Position and wrap
```

### Selection

```bash
fzf --multi                    # Allow multiple selections (Tab to toggle)
fzf --select-1                 # Auto-select if only one match
fzf --exit-0                   # Exit immediately if no matches
fzf --no-sort                  # Preserve input order
```

### Keybindings

```bash
fzf --bind 'ctrl-r:reload(source_cmd)'         # Refresh the source
fzf --bind 'ctrl-y:execute-silent(echo {} | pbcopy)'  # Copy to clipboard
fzf --bind 'ctrl-o:execute(open {})'           # Open in default app
fzf --bind 'enter:become(vim {})'              # Replace fzf with action
```

---

## Composition Recipes

### Git Workflows

```bash
# Checkout branch (sorted by recent)
git branch --sort=-committerdate | sed 's/^[* ]*//' | fzf --preview 'git log --oneline -10 {}' | xargs git checkout

# Interactive rebase target selection
git log --oneline -20 | fzf | awk '{print $1}' | xargs -I{} git rebase -i {}^

# Stage files selectively
git diff --name-only | fzf --multi --preview 'git diff --color=always {}' | xargs git add

# Browse stashes
git stash list | fzf --preview 'git stash show -p {+1}' | awk -F: '{print $1}' | xargs git stash pop
```

### Package Management

```bash
# Browse installed brew packages with info
brew list --formula | fzf --preview 'brew info {}' --multi | xargs brew upgrade

# Search and install brew packages
brew search '' | fzf --multi --preview 'brew info {}' | xargs brew install

# Inspect brew cask apps
brew list --cask | fzf --preview 'brew info --cask {}'
```

### Process Management

```bash
# Kill a process interactively
ps aux | fzf --header-lines=1 --preview 'echo {}' | awk '{print $2}' | xargs kill

# Select a port to investigate
lsof -i -P | fzf --header-lines=1 | awk '{print $2}' | xargs -I{} lsof -p {}
```

### Mise Task Selection

```bash
# Pick and run a mise task
mise tasks | awk '{print $1}' | fzf --preview 'mise tasks info {}' | xargs mise run

# Select tools to install
mise ls-remote node | fzf | xargs mise use node@
```

### File Operations

```bash
# Find and edit a file (fd + bat preview)
fd --type f | fzf --preview 'bat --color=always --line-range=:50 {}' | xargs $EDITOR

# Find and cd into a directory
fd --type d | fzf --preview 'ls -la {}' | { read dir && cd "$dir"; }

# Search file contents (rg + fzf)
rg --line-number '' | fzf --delimiter : --preview 'bat --color=always --highlight-line {2} {1}' | awk -F: '{print "+"$2, $1}' | xargs $EDITOR
```

---

## Building Reusable fzf Functions

When an fzf composition proves useful, graduate it to a zsh function:

```zsh
# ~/.zsh/functions/fbr — interactive branch checkout
function fbr() {
  local branch
  branch=$(git branch --sort=-committerdate | sed 's/^[* ]*//' | fzf --preview 'git log --oneline -10 {}')
  [[ -n "$branch" ]] && git checkout "$branch"
}
```

For team-shared compositions, graduate to a mise task with the `usage` field for argument parsing.

---

## Alternatives Comparison

| Tool | Model | Best For |
|------|-------|----------|
| **fzf** | Pipe-based filter | Any list → interactive selection |
| **tv** (television) | Standalone with built-in sources | File search, code grep, git files |
| **gum** | Structured prompts | Confirmations, forms, multi-step input |

### When to Prefer tv

tv (television) has built-in "channels" for common sources (files, git files, grep). Use it when the source is already built-in — no piping needed:

```bash
tv                      # Default file search
tv --channel git-files  # Search git-tracked files
tv --channel grep       # Search file contents
```

### When to Prefer gum

gum provides structured interaction widgets. Use it for confirmation flows and multi-step input — not list filtering:

```bash
gum confirm "Deploy to production?"
gum choose "staging" "production" "development"
gum input --placeholder "Enter version..."
TYPE=$(gum choose "feat" "fix" "docs") && gum input --placeholder "description" | xargs -I{} echo "$TYPE: {}"
```
