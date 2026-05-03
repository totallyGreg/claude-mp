# Composition Philosophy

## Unix Composition Principle

Compose existing tools before creating new ones. The terminal stack is rich — most automation needs can be met by piping known tools together. Before suggesting a new script or tool installation, check what the user already has (`brew list`, `ls ~/.config/`, command history) and compose from that.

However, recognize when multi-tasking tools simplify pipeline complexity. mise replaces separate env managers + task runners + version managers. sesh replaces manual tmux session scripting. When a single tool absorbs a pipeline, prefer it over the equivalent chain of small tools.

**Heuristic**: if a pipeline exceeds 3 stages or requires persistent state between invocations, look for a tool that absorbs the complexity. If the pipeline is 1-2 stages with no state, keep it simple.

---

## Tool Landscape Discovery

Before suggesting compositions, discover what the user actually uses. Don't assume tools — inventory them:

| Signal Source | What It Reveals | Command |
|--------------|----------------|---------|
| Homebrew inventory | Installed tools, update recency | `brew list --versions`, `brew info --installed --json` |
| XDG_CONFIG_HOME | Actively configured tools | `ls ${XDG_CONFIG_HOME:-~/.config}/` |
| Shell history | Frequently used commands, sequences | `fc -l -1000` or parse `$HISTFILE` |
| Zoxide frecency | Directory visit patterns | `zoxide query -ls` |
| Git log | Repo-specific workflow habits | `git log --oneline -50` |

**Adoption signals from brew**:
- Recently installed (< 7 days) — exploring, don't build workflows around it yet
- Frequently updated — active use, safe to compose with
- Installed but stale (no updates in 6+ months) — check if still in use before suggesting

**XDG config presence** = active configuration. A tool with config in `~/.config/` is more deeply integrated than one that's merely installed.

---

## Pattern Graduation Pipeline

Patterns move through stages. Each promotion has a trigger — don't skip levels unless the user's intent clearly requires it.

```
Ad-hoc Command  →  Shell History  →  Zsh Function  →  Mise Task
   (one-off)        (repeated)       (personal)       (team/project)
```

### Promotion Triggers

| Transition | Trigger | Action |
|-----------|---------|--------|
| Ad-hoc → History | Automatic (shell records it) | No action needed |
| History → Function | Same pipeline run 3+ times, or user asks to automate | Create autoload function in `~/.zsh/functions` |
| Function → Mise Task | Team needs it, has dependencies, needs isolated env, needs DAG ordering | Create `mise run` task with `usage` field for arg parsing |
| Function → Sesh Template | Involves session setup, multiple windows/panes, startup commands | Add `[[session]]` or `[[wildcard]]` to `sesh.toml` |
| Any → fzf Composition | User manually selects from a list before acting | Wrap with `source | fzf --preview | action` pattern |

### Decision Shortcuts

- "I need this in my shell right now" → zsh function
- "The team needs to run this" → mise task
- "This modifies my working directory or exports" → zsh function
- "This has build steps that depend on each other" → mise task (DAG model)
- "I want to pick from a list first" → fzf composition

---

## fzf as Composition Glue

fzf turns any list into an interactive selection. The universal pattern:

```
source | fzf [--preview 'command {}'] | action
```

### Common Compositions

```bash
# Select and checkout a git branch
git branch --sort=-committerdate | fzf --preview 'git log --oneline -10 {}' | xargs git checkout

# Browse and inspect brew packages
brew list | fzf --preview 'brew info {}' | xargs brew info

# Select and run a mise task
mise tasks | awk '{print $1}' | fzf --preview 'mise run --dry-run {}' | xargs mise run

# Find and edit a file
fd --type f | fzf --preview 'bat --color=always {}' | xargs $EDITOR

# Kill a process interactively
ps aux | fzf --header-lines=1 | awk '{print $2}' | xargs kill
```

### fzf Power Features

| Feature | Flag | Use Case |
|---------|------|----------|
| Preview | `--preview 'cmd {}'` | Show context before selecting |
| Multi-select | `--multi` | Act on multiple items |
| Keybindings | `--bind 'ctrl-r:reload(cmd)'` | Refresh source list |
| Header | `--header 'Select...'` | Describe what to pick |
| Prompt | `--prompt '> '` | Custom input prompt |

### When to Use Alternatives

| Tool | Best For | Pattern |
|------|----------|---------|
| **fzf** | List selection, filtering | `source \| fzf \| action` |
| **tv/television** | File-centric search, code grep | `tv` (standalone, built-in sources) |
| **gum** | Structured prompts, confirmations, forms | `gum choose`, `gum confirm`, `gum input` |

---

## Composition Heuristics

When composing tools:

1. **Diagnose bottom-up** — use the Terminal Stack order (zsh → tmux → sesh → git → mise). Lower layers must work before higher layers compose.
2. **Discover before composing** — check what tools exist (`brew list`, XDG configs) before suggesting combinations.
3. **Prefer existing tools** — compose from what's installed rather than suggesting new installations.
4. **Use the Lens framework** as a composition checklist: Selection (what's included), Arrangement (how it's presented), Purpose (why it exists), Activation (how to trigger it).
5. **Record what works** — when a composition proves useful, suggest recording it in the profile's `workflow_patterns` section.
