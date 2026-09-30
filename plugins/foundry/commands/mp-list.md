---
name: mp-list
description: List marketplace plugins with version, description, and source read from each plugin.json
argument-hint: [marketplace-path]
---

List the plugins in the marketplace at `${1:-.claude-plugin/marketplace.json}`.

`plugin.json` is the source of truth, so read each entry's `source`, then its `<source>/.claude-plugin/plugin.json`:

```bash
mp="${1:-.claude-plugin/marketplace.json}"
root="$(dirname "$(dirname "$mp")")"
jq -r '.plugins[] | [.name, .source, (.category // "")] | @tsv' "$mp" |
while IFS=$'\t' read -r name source category; do
  jq -r --arg n "$name" --arg s "$source" --arg c "$category" \
    '[$n, (.version // "-"), $c, $s, (.description // "" | .[0:80])] | @tsv' \
    "$root/$source/.claude-plugin/plugin.json"
done
```

Display a table with columns: Plugin, Version, Category, Source, Description.
