# Unix Composition Primer

Foundation reference for composing terminal tools to achieve a stated goal. Covers the three core operations — **piping** (moving data), **filtering** (selecting subsets), and **transforming** (reshaping content) — plus an explicit tool preference matrix so the right tool gets picked for each job.

This primer is loaded by the agent when answering "how do I combine X and Y?" or "what's the best way to do Z in the shell?" questions.

---

## Why a Preference Matrix

POSIX has had `grep`, `find`, `sed`, and `awk` for decades. Modern alternatives (`rg`, `fd`, `sd`, `jq`, `yq`) are faster, have saner defaults, and respect `.gitignore`. The trade-off is portability: POSIX tools exist everywhere; modern tools require installation.

**Default rule:** Prefer the modern tool on user machines (where it's likely installed); use POSIX in scripts that need to run anywhere (CI runners without brew, minimal containers, remote servers).

---

## Piping (Moving Data)

### Streams

| Stream | FD | Default destination | Redirect to file | Pipe through         |
| ------ | -- | ------------------- | ---------------- | -------------------- |
| stdout | 1  | terminal            | `> file`         | `\| cmd`             |
| stderr | 2  | terminal            | `2> file`        | `2>&1 \| cmd` (merge first) |
| stdin  | 0  | keyboard            | `< file`         | (received from upstream pipe) |

### Common redirection patterns

```bash
cmd > out.log                # stdout to file (overwrite)
cmd >> out.log               # stdout to file (append)
cmd 2> err.log               # stderr to file
cmd > out.log 2>&1           # merge stderr into stdout, both to file
cmd &> out.log               # bash/zsh shortcut for above
cmd < input.txt              # feed file as stdin
cmd | other                  # stdout of cmd → stdin of other
cmd |& other                 # bash/zsh shortcut for: 2>&1 | other
```

### Process substitution `<(...)` and `>(...)`

When a command wants a *file path* but you have a *stream*:

```bash
# diff the output of two commands
diff <(ls dir_a) <(ls dir_b)

# pass curl output to a command that wants a file
vim <(curl -s https://example.com/data.json)

# tee to multiple consumers
some_cmd > >(tee primary.log) 2> >(tee errors.log >&2)
```

### `tee` — fan-out

```bash
cmd | tee output.log          # write to file AND continue piping
cmd | tee -a output.log       # append mode
cmd | tee >(grep ERROR > errors.log) | downstream    # parallel branches
```

### `pv` — pipe viewer (progress)

```bash
cat big.tar.gz | pv | tar xz                  # show throughput
pv -L 1m big.iso > /dev/sda                   # rate-limit a write to 1MB/s
```

---

## Filtering (Selecting Subsets)

### Find files by name/attribute

| Goal                          | Preferred         | POSIX fallback       | Why                                          |
| ----------------------------- | ----------------- | -------------------- | -------------------------------------------- |
| Find files matching a pattern | `fd PATTERN`      | `find . -name PATTERN` | fd: ripgrep-style, parallel, respects .gitignore, hidden files excluded by default |
| All files of a type           | `fd -e py`        | `find . -name '*.py'` | fd: `-e` flag is the obvious form            |
| Include hidden                | `fd -H`           | `find . -name PATTERN` | fd: explicit `-H` (sane default)             |
| Don't respect .gitignore      | `fd -I`           | `find . -name PATTERN` | fd: explicit `-I`                            |
| Find + exec command           | `fd PATTERN -x cmd` | `find . -name PATTERN -exec cmd {} \;` | fd: cleaner, parallel by default |
| Find directories only         | `fd -t d PATTERN` | `find . -type d -name PATTERN` | fd: shorter                       |
| Find by size                  | `fd -S +10M`      | `find . -size +10M`  | Either works                                  |

```bash
# fd basics
fd 'config'                   # find files/dirs matching config
fd -e ts -e tsx               # multiple extensions
fd -t f -e py -x black {}     # parallel exec — format all Python files
fd --changed-within 1d        # files modified in last day
```

### Search inside files (content)

| Goal                          | Preferred         | POSIX fallback       | Why                                          |
| ----------------------------- | ----------------- | -------------------- | -------------------------------------------- |
| Search for a pattern          | `rg PATTERN`      | `grep -r PATTERN .`  | rg: 10–100× faster, respects .gitignore, color, smart-case |
| Only file names that match    | `rg -l PATTERN`   | `grep -rl PATTERN .` | rg: `-l` works the same                      |
| Show N lines of context       | `rg -A 5 PATTERN` | `grep -A 5 PATTERN`  | Same flags                                   |
| Whole-word match              | `rg -w PATTERN`   | `grep -w PATTERN`    | Same                                         |
| File type filter              | `rg --type py PATTERN` | `find ... -exec grep` | rg: built-in type filters             |
| Multiline regex               | `rg -U PATTERN`   | `grep -P` (perl mode) | rg: cross-line by default with `-U`         |
| Replace inline (preview)      | `rg PATTERN -r REPL` | `sed -i 's/PATTERN/REPL/'` | rg: previews changes without applying  |

```bash
# rg basics
rg 'TODO'                                    # search all (respects .gitignore)
rg -t md 'TODO'                              # markdown only
rg -g '*.{ts,tsx}' -g '!*.test.*' 'export'   # include/exclude globs
rg --files-with-matches 'pattern'            # just file names
rg --count 'pattern'                         # match counts per file
rg 'foo' -r 'bar' --replace-only             # preview replacement
```

### Filter structured data

| Format     | Preferred              | Fallback                       |
| ---------- | ---------------------- | ------------------------------ |
| JSON       | `jq`                   | `python -c 'import json...'`   |
| YAML       | `yq` (Go version)      | `python -c 'import yaml...'`   |
| TOML       | `yq -p toml` or `dasel` | `python -c 'import tomllib...'`|
| CSV / TSV  | `xsv` or `mlr`         | `awk -F,`                      |
| HTML       | `pup` or `htmlq`       | `python -c 'from bs4...'`      |
| XML        | `xmlstarlet`           | `xmllint --xpath`              |

```bash
# jq idioms
echo '{"a":1,"b":2}' | jq '.a'                                # → 1
jq '.users[] | select(.active) | .email' users.json           # filter + project
jq '.[] | {name, total: (.items | map(.price) | add)}' data.json   # transform
jq -r '.users[].email' users.json                             # raw output (no quotes)

# yq (kislyuk/Go fork)
yq '.services.api.image' docker-compose.yml
yq -p toml -o json '.' Cargo.toml                             # toml → json
yq '.spec.containers[].image' deploy.yaml

# xsv (CSV)
xsv headers data.csv                                          # show columns
xsv select name,email data.csv
xsv search -s email '@example.com' data.csv
xsv stats data.csv | xsv table                                # summary stats
```

---

## Transforming (Reshaping Content)

### String substitution

| Goal                          | Preferred         | POSIX fallback           | Why                                       |
| ----------------------------- | ----------------- | ------------------------ | ----------------------------------------- |
| Replace a string in a file    | `sd 'find' 'repl' file` | `sed -i '' 's/find/repl/g' file` | sd: no regex by default, no fragile escaping |
| Regex replace                 | `sd -r 'find' 'repl'` | `sed -i '' -E 's/find/repl/g'` | sd: regex via flag, not escapes        |
| Multi-file replace            | `fd -t f -x sd 'old' 'new' {}` | `find . -type f -exec sed -i '' 's/old/new/g' {} +` | fd + sd: parallel, sane |
| Preview without writing       | `sd 'find' 'repl'` (no `-i`)   | `sed 's/find/repl/' file` | Both work                       |

```bash
# sd: dead-simple find/replace
sd 'oldFunction' 'newFunction' src/**/*.ts
sd -p 'oldFunction' 'newFunction' src/**/*.ts                # preview (-p)
sd -r 'logger\.(info|debug)' 'logger.$1' app.py              # regex with capture
```

### awk — column-oriented text streams

`awk` is still the right tool for column-aligned text and field-based aggregations:

```bash
# Print column 5
ps aux | awk '{print $5}'

# Sum a column
df | awk 'NR>1 {sum+=$2} END {print sum}'

# Filter then format
who | awk '$2 ~ /^tty/ {printf "%-15s %s\n", $1, $4}'

# Use a different field separator
awk -F: '{print $1}' /etc/passwd
```

### `cut` — quick column extraction

```bash
echo 'a,b,c,d' | cut -d, -f2,4         # → b,d
cut -c1-10 file.txt                    # first 10 chars per line
ls -l | cut -d' ' -f1                  # first space-separated field
```

### `sort` / `uniq` / `wc`

```bash
# Most common patterns
sort file.txt | uniq                         # dedupe
sort file.txt | uniq -c | sort -rn           # frequency, descending
wc -l file.txt                               # line count

# Sort by numeric column
sort -k2 -n data.txt

# Reverse sort
sort -r file.txt
```

---

## Glue Patterns

### fzf — interactive selection

`fzf` is the universal glue for turning any list into an interactive picker. The pattern: `source | fzf --preview 'cmd {}' | downstream`.

```bash
# Pick a file, open in editor
fd -t f | fzf | xargs $EDITOR

# Pick a git branch
git branch | fzf | xargs git checkout

# Pick from process list
ps aux | fzf | awk '{print $2}' | xargs kill

# With preview
fd -e md | fzf --preview 'glow -s dark {}'

# Multi-select (Tab to mark, Enter to confirm)
fd | fzf -m | xargs rm -i
```

See `fzf_composition.md` for the full preview recipes and the `source | fzf --preview | action` pattern catalog.

### xargs — bridge stdin to argv

When the downstream command needs **arguments** rather than **stdin**:

```bash
# Simple — substitute {} for each item
fd -e log | xargs -I{} rm {}

# Parallel
fd -e py | xargs -n 1 -P 8 -I{} python {} --validate

# Null-delimited (filenames with spaces / newlines)
fd -e log -0 | xargs -0 rm

# Limit batch size
echo {1..100} | xargs -n 10 echo                  # 10 items per invocation
```

### `tee` — duplicate the stream

```bash
cmd | tee output.txt | downstream                 # save AND continue
cmd | tee >(consumer1) >(consumer2) > final.txt   # multi-fan-out
```

---

## Tool Preference Matrix (Quick Reference)

| Situation                            | Preferred           | POSIX fallback             | Why prefer                                       |
| ------------------------------------ | ------------------- | -------------------------- | ------------------------------------------------ |
| Search text inside files             | `rg`                | `grep -r`                  | Speed, .gitignore-aware, sane defaults           |
| Find files by name                   | `fd`                | `find`                     | Speed, .gitignore-aware, cleaner syntax          |
| Substitute in a file                 | `sd`                | `sed`                      | No regex escaping nightmares                     |
| JSON manipulation                    | `jq`                | `python -c`                | DSL designed for it; ubiquitous on dev machines  |
| YAML manipulation                    | `yq`                | `python -c`                | Same syntax as jq                                |
| TOML manipulation                    | `yq -p toml` / `dasel` | `python -c 'import tomllib'` | Pipeline-friendly                          |
| Interactive selection                | `fzf` / `television` | `select` (POSIX)          | Vastly better UX                                 |
| Markdown rendering                   | `glow`              | `cat` + scrolling           | Syntax highlighting                              |
| CSV manipulation                     | `xsv` / `mlr`        | `awk -F,`                  | Column-aware; handles quotes                     |
| HTTP fetching                        | `curl`              | (no alternative)           | Universal                                        |
| HTTP for humans                      | `httpie` (`http`)   | `curl`                     | Saner defaults for interactive use               |
| Process column-oriented text         | `awk`               | (still the right tool)     | Awk wins for field aggregations                  |
| Compress                             | `zstd` / `gzip`     | `gzip`                     | zstd: faster + better ratio when available       |
| Hex dump                             | `xxd`               | `od -x`                    | Cleaner output                                   |
| diff files                           | `delta` or `difft`  | `diff` / `git diff`        | Syntax-aware, side-by-side                       |

---

## Choosing a Compositional Approach

Three modes of composition, in increasing order of formality:

1. **Inline pipeline** — `source | filter | transform | sink`. Use for one-off operations. Throw away after.
2. **Shell history → function** — when you've typed the same pipeline 3+ times, lift it into a zsh function (see `zsh-dev/references/zsh_function_patterns.md`).
3. **Function → mise task** — when the workflow needs to be shareable, repeatable, or include multiple steps with dependencies, graduate to a mise task (see `mise-tooling/references/mise_task_patterns.md`).

See `composition_philosophy.md` for the full Pattern Graduation Pipeline.

---

## When NOT to Compose

- **Critical correctness paths.** A bug in a hand-rolled `awk` script that processes payroll data costs more than writing a real program.
- **State management.** Pipelines are stateless. If you need state across iterations, you need a real script (Python, Ruby), not a pipeline.
- **Concurrency beyond `xargs -P`.** For fan-out with actual coordination, a real script.
- **Error recovery.** Pipelines fail silently on broken pipes. If you need retry logic, you need a real script.
