# Extraction Guide — Threads, History, Catch-up

The `thread`, `history`, and `catchup` commands turn Slack conversations into readable,
parseable output. All three share one user-name cache and one markdown renderer.

## Output modes

| Mode | Flag | Shape |
|------|------|-------|
| Markdown (default) | — | Headers `**Name** · YYYY-MM-DD HH:MM`, body with resolved mentions/links, 📎 files, thread replies as blockquotes |
| Enriched JSON | `--json` | Raw API message objects **plus** an `author_name` field on each; thread replies nested under `_replies` (catchup/history) |

Markdown is best for reading and for feeding to a model for summarization. `--json` is best
when a downstream script needs structured fields (reactions, ts, files) with names already resolved.

### mrkdwn resolution

The renderer rewrites Slack's `mrkdwn` entities so output is portable markdown:

- `<@U123>` / `<@U123|name>` → `@DisplayName`
- `<#C123|general>` → `#general`
- `<!here>` / `<!channel>` → `@here` / `@channel`; `<!subteam^S1|@team>` → `@team`
- `<https://x|Label>` → `[Label](https://x)`; bare `<https://x>` → `https://x`
- HTML entities `&lt; &gt; &amp;` are unescaped

## Time ranges (`--since`)

`history` and `catchup` accept `--since`. `catchup` **requires** it; `history` defaults to no
lower bound (most recent `--limit` messages).

| Format | Meaning |
|--------|---------|
| `Nh` | last N hours (e.g. `24h`) |
| `Nd` | last N days (e.g. `7d`) |
| `Nw` | last N weeks (e.g. `2w`) |
| `YYYY-MM-DD` | since that date (local midnight) |

Internally converted to a Unix timestamp for the API `oldest` parameter.

## Pagination & limits

- `thread`: `--limit` default 500, hard cap 1000 (paginates `conversations.replies` at 200/page).
- `history`: `--limit` default 100, hard cap 1000 (100/page).
- `catchup`: `--limit` is **per channel** (default 100). For each message with `reply_count > 0`
  it fetches up to 200 replies and nests them.
- `channels`: `--limit` default 1000 (200/page via `users.conversations`).

Empty channels are skipped in `catchup` (no `conversations.history` results in range).

## User-name cache

`resolve_users()` calls `users.info` once per unique ID and caches for the process lifetime.
Author IDs and in-text `<@…>` mention IDs are both resolved. Unknown/failed lookups fall back
to the raw ID rather than erroring, so a single bad ID never breaks a render.

## Channel discovery & the channel-list file

Resolve names to IDs with `channels --resolve <name>`, or dump the full table with `channels`.

`catchup --channels-file <path>` reads channel IDs from a markdown table. Any table row whose
**first cell** is a channel ID (`C…`) is used; other columns are ignored, so a categorized list
is fine:

```markdown
# Default Channels

## Team
| ID | Channel | Category |
|----|---------|----------|
| C09849LMMDH | team-eng | internal |
| C0123ABCD   | company-news | announcements |
```

Save a reusable list once, then run `catchup --channels-file channels.md --since 7d` for
repeatable digests without re-entering IDs.

## Cross-channel search

`search` queries `search.messages` across **every channel and DM you can access or have
contributed to** — not just channels you name. It is **user-token only** (`--bot` will fail;
Slack forbids bot tokens on `search.*`) and requires the `search:read` scope.

```bash
slacker.py search "quarterly planning"                 # markdown, ranked by relevance
slacker.py search "from:@me in:#team-eng" --count 200  # scoped with modifiers
slacker.py search "incident after:2026-03-01" --sort timestamp --json
```

Output shows each match's author, `#channel`, timestamp, text, and a permalink. `--count`
defaults to 100 (cap 1000, paginated 100/page); `--sort` is `score` (default) or `timestamp`.

**Query modifiers** (combine freely): `in:#channel` / `in:@dm`, `from:@user` (or `from:@me`),
`after:YYYY-MM-DD`, `before:YYYY-MM-DD`, `during:July`, `has:link`, `has:star`. Quote the whole
query string. Narrow with modifiers when a bare term returns too many matches.

Use `search` to find *where* something was discussed, then `thread` to pull the full
conversation, or `catchup` to digest the surrounding channels.

## Typical workflows

**Catch me up across my team's channels**
1. `channels` (or load a saved channel-list file) to get IDs.
2. `catchup --channels-file channels.md --since 7d` → grouped digest with threads.
3. Summarize decisions/questions/action items per channel from the markdown.

**Pull one big thread for analysis**
1. `parse-url "<url>"` if you only have a link and want the components, or pass the URL directly.
2. `thread "<url>" --limit 1000` → readable markdown; add `--json` if a script will parse it.

**Extract a channel's recent history to a file**
- `history C0123 --since 2w > history.md` — then edit and, if useful, publish as a Canvas via
  `canvas publish "History" --file history.md`.
