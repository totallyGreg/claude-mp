# Obsidian CLI Patterns for Curator Workflows

The installed obsidian-cli skills provide safe CLI usage patterns for vault curation.

## Property Commands

```bash
obsidian properties path=<path> format=tsv           # list all properties
obsidian property:read name=<key> path=<path>        # read one property
obsidian property:set name=<key> value=<val> path=<path>  # set property
```

## Search Commands

```bash
obsidian search query="<text>" path=<folder> format=json matches  # scoped search with context
```

## Structure Commands

```bash
obsidian folders                                      # list all folders
obsidian files folder=<path> ext=md                   # list files in folder
obsidian orphans                                      # files with no incoming links
obsidian backlinks path=<path> counts                 # incoming links with counts
```

## Tag Commands

```bash
obsidian tags all counts sort=count                   # vault-wide tags by frequency
obsidian tag name=<tag>                               # files with specific tag
```

## Safety Rules

- Always use `silent` flag with `create` (prevents opening files in UI)
- Always use `format=json` for programmatic output
- Use `tasks all todo` not `tasks todo` (latter defaults to active file)
- Use `tags all counts` not `tags counts` (latter defaults to active file)
- CLI requires Obsidian desktop app to be running

See installed `obsidian-cli` skills for the full gotcha list.

## Fallback

If CLI is unavailable (Obsidian not running), use Grep/Glob/Read for file operations.
