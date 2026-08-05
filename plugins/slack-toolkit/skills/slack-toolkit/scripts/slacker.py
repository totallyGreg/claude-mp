#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = ["slack_sdk", "pip-system-certs"]
# ///
"""
Slack Web API CLI — readable extraction + Canvas authoring.

Built on slack_sdk.WebClient. Pulls large threads/history into readable markdown
(user names resolved), runs multi-channel catch-up digests, verifies token scopes,
and provides full Canvas CRUD + publishing (markdown file -> shared Canvas).

Run with uv (auto-installs slack_sdk + pip-system-certs):
    uv run slacker.py <command> [args]

Exit codes:
    0 = success
    1 = usage error
    2 = auth error
    3 = API error
    4 = rate limited (after retry failed)
"""

import argparse
import html.parser
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------
EXIT_OK = 0
EXIT_USAGE = 1
EXIT_AUTH = 2
EXIT_API = 3
EXIT_RATE = 4


# ---------------------------------------------------------------------------
# Required scopes (checked by auth-check)
# ---------------------------------------------------------------------------
REQUIRED_SCOPES = {
    # reading conversations
    "channels:history", "channels:read",
    "groups:history", "groups:read",
    "im:history", "im:read",
    "mpim:history", "mpim:read",
    "users:read",
    # cross-channel search (user token only)
    "search:read",
    # canvases + files
    "files:read", "canvases:read", "canvases:write",
    # reactions
    "reactions:write",
}


# ---------------------------------------------------------------------------
# Per-operation scope requirements (checked by the preflight before the call)
# ---------------------------------------------------------------------------
# Maps a command to the scope(s) it needs. require_scopes() verifies these BEFORE
# hitting the API so a missing scope fails loudly with a fix, instead of a bare
# `missing_scope` surfacing mid-operation. Only the always-needed scope per op is
# listed; DM/group variants (groups/im/mpim:*) are surfaced by Slack's own
# `needed` field via slack_call's missing_scope handler when a specific conv type
# is actually hit.
PER_OP_SCOPES = {
    "search": {"search:read"},          # user token only
    "history": {"channels:history"},
    "thread": {"channels:history"},
    "catchup": {"channels:history"},
    "mine": {"channels:history"},      # from:@me reconstruction, no search:read
    "channels": {"channels:read"},
    "react": {"reactions:write"},
    "unreact": {"reactions:write"},
}

# Actionable guidance printed whenever a scope is missing (preflight or mid-call).
SCOPE_FIX_HINT = (
    "\nTo grant a missing scope:\n"
    "  1. Add it to the app manifest (needs an app config token, xoxe.xoxp-…):\n"
    "       uv run {here}/scope_manager.py add --user <scope> --app-id <APP_ID>\n"
    "     …or add it manually at https://api.slack.com/apps/<APP_ID> → OAuth & Permissions.\n"
    "  2. Reinstall the app via the browser OAuth consent screen\n"
    "     (Enterprise Grid may require org-admin approval — this cannot be done headlessly).\n"
    "  3. Update the stored token, then re-run: slacker.py auth-check\n"
    "  See references/scope-management.md for the full add → reinstall → revert loop."
)


# ---------------------------------------------------------------------------
# Token resolution + client factory
# ---------------------------------------------------------------------------
def resolve_token(token_type="user"):
    """Resolve Slack token: env var -> keychainctl fallback -> prefix validation."""
    env_var = "SLACK_BOT_TOKEN" if token_type == "bot" else "SLACK_USER_TOKEN"
    token = os.environ.get(env_var)

    if not token:
        try:
            result = subprocess.run(
                ["keychainctl", "get", env_var],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                token = result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    if not token:
        print(f"Error: No Slack token found. Set ${env_var} or store via keychainctl.", file=sys.stderr)
        sys.exit(EXIT_AUTH)

    if not token.startswith(("xoxp-", "xoxb-")):
        print("Error: Token has invalid prefix (expected xoxp- or xoxb-).", file=sys.stderr)
        sys.exit(EXIT_AUTH)

    return token


def get_client(token_type="user"):
    """Return a slack_sdk WebClient. Access the raw token via client.token when needed."""
    return WebClient(token=resolve_token(token_type))


def slack_call(method, strict=True, **kwargs):
    """Invoke a bound WebClient method with one 429 retry; map errors to exit codes.

    Slack's {"ok": true} is authoritative — slack_sdk raises SlackApiError on ok:false,
    so a returned response is always a success.

    With strict=False, generic API errors (e.g. channel_not_found, not_in_channel) are
    re-raised for the caller to handle instead of exiting — auth, scope, and rate-limit
    failures still exit loudly. Used by sweeps that must skip unreadable channels.
    """
    for attempt in range(2):
        try:
            return method(**kwargs)
        except SlackApiError as e:
            resp = e.response
            status = getattr(resp, "status_code", None)
            if status == 429 and attempt == 0:
                retry_after = int(resp.headers.get("Retry-After", "5"))
                print(f"Rate limited, retrying in {retry_after}s...", file=sys.stderr)
                time.sleep(retry_after)
                continue
            if status == 429:
                print("Error: Rate limited after retry.", file=sys.stderr)
                sys.exit(EXIT_RATE)
            err = "unknown"
            try:
                err = resp.get("error", "unknown")
            except Exception:
                err = str(e)
            if err in ("not_authed", "invalid_auth", "token_revoked", "account_inactive"):
                print(f"Error: Auth failed — {err}", file=sys.stderr)
                sys.exit(EXIT_AUTH)
            if err == "missing_scope":
                # Slack returns the exact scope in `needed` — surface it with a fix so
                # this fails loudly with guidance instead of a bare `missing_scope`.
                needed = provided = ""
                try:
                    needed = resp.get("needed", "") or ""
                    provided = resp.get("provided", "") or ""
                except Exception:
                    pass
                detail = f" — needs '{needed}'" if needed else ""
                print(f"Error: {method.__name__} failed — missing_scope{detail}", file=sys.stderr)
                if provided:
                    print(f"Token currently has: {provided}", file=sys.stderr)
                print(SCOPE_FIX_HINT.format(here=SCRIPT_DIR), file=sys.stderr)
                sys.exit(EXIT_AUTH)
            if err == "not_allowed_token_type":
                print(f"Error: {method.__name__} rejected this token type. "
                      "search.* and several methods require the USER token (xoxp-) — "
                      "drop --bot and set $SLACK_USER_TOKEN.", file=sys.stderr)
                sys.exit(EXIT_AUTH)
            if not strict:
                raise  # caller handles data errors (e.g. channel_not_found) itself
            print(f"Error: {method.__name__} failed — {err}", file=sys.stderr)
            sys.exit(EXIT_API)
    sys.exit(EXIT_RATE)


# ---------------------------------------------------------------------------
# Scope preflight
# ---------------------------------------------------------------------------
def scopes_from_response(resp):
    """Extract the set of OAuth scopes from an auth.test response (X-OAuth-Scopes header)."""
    for k, v in (resp.headers or {}).items():
        if k.lower() == "x-oauth-scopes":
            return {s.strip() for s in v.split(",") if s.strip()}
    return set()


def require_scopes(client, command):
    """Preflight: verify the token carries the scope(s) `command` needs.

    Runs auth.test (reads X-OAuth-Scopes) BEFORE the operation, so a missing scope
    fails loudly with actionable guidance instead of a bare `missing_scope` mid-call.
    No-op for commands with no fixed scope requirement.
    """
    required = PER_OP_SCOPES.get(command)
    if not required:
        return
    granted = scopes_from_response(slack_call(client.auth_test))
    missing = sorted(required - granted)
    if missing:
        print(f"Error: '{command}' needs scope(s) not on this token: {', '.join(missing)}",
              file=sys.stderr)
        print(SCOPE_FIX_HINT.format(here=SCRIPT_DIR), file=sys.stderr)
        sys.exit(EXIT_AUTH)


def slack_download(url, token):
    """Authenticated GET for url_private content. Returns decoded string.

    slack_sdk does not fetch arbitrary file bodies, so this stays a raw urllib GET.
    """
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"Error: Failed to download — HTTP {e.code}", file=sys.stderr)
        sys.exit(EXIT_API)


def _paginate(method, key, cap, per_page, strict=True, **params):
    """Cursor-paginate a WebClient list method up to `cap` items.

    strict=False re-raises generic API errors (see slack_call) so a caller sweeping
    many channels can skip unreadable ones instead of aborting.
    """
    items = []
    cursor = None
    while len(items) < cap:
        page_params = dict(params)
        page_params["limit"] = min(per_page, cap - len(items))
        if cursor:
            page_params["cursor"] = cursor
        resp = slack_call(method, strict=strict, **page_params)
        items.extend(resp.get(key, []) or [])
        cursor = (resp.get("response_metadata") or {}).get("next_cursor")
        if not cursor:
            break
    return items[:cap]


# ---------------------------------------------------------------------------
# HTML -> Markdown converter (for quip-type canvases)
# ---------------------------------------------------------------------------
class HtmlToMarkdown(html.parser.HTMLParser):
    """Convert Slack quip canvas HTML to markdown using stdlib only."""

    def __init__(self):
        super().__init__()
        self._output = []
        self._stack = []
        self._list_stack = []
        self._href = None
        self._link_text = []
        self._in_code_block = False
        self._table_rows = []
        self._current_row = []
        self._cell_text = []
        self._in_table = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self._stack.append(tag)

        if tag in ("h1", "h2", "h3"):
            level = int(tag[1])
            self._output.append("\n" + "#" * level + " ")
        elif tag in ("b", "strong"):
            self._output.append("**")
        elif tag in ("i", "em"):
            self._output.append("_")
        elif tag == "code":
            if self._in_code_block:
                return
            self._output.append("`")
        elif tag == "pre":
            self._in_code_block = True
            self._output.append("\n```\n")
        elif tag == "a":
            self._href = attrs_dict.get("href")
            self._link_text = []
        elif tag == "ul":
            self._list_stack.append(("ul", 0))
        elif tag == "ol":
            self._list_stack.append(("ol", 0))
        elif tag == "li":
            if self._list_stack:
                list_type, count = self._list_stack[-1]
                indent = "  " * (len(self._list_stack) - 1)
                if list_type == "ol":
                    count += 1
                    self._list_stack[-1] = (list_type, count)
                    self._output.append(f"\n{indent}{count}. ")
                else:
                    self._output.append(f"\n{indent}- ")
        elif tag == "hr":
            self._output.append("\n---\n")
        elif tag == "br":
            self._output.append("\n")
        elif tag == "p":
            self._output.append("\n\n")
        elif tag == "table":
            self._in_table = True
            self._table_rows = []
        elif tag == "tr":
            self._current_row = []
        elif tag in ("td", "th"):
            self._cell_text = []
        elif tag == "img":
            alt = attrs_dict.get("alt", "")
            src = attrs_dict.get("src", "")
            self._output.append(f"![{alt}]({src})")

    def handle_endtag(self, tag):
        if self._stack and self._stack[-1] == tag:
            self._stack.pop()

        if tag in ("h1", "h2", "h3"):
            self._output.append("\n")
        elif tag in ("b", "strong"):
            self._output.append("**")
        elif tag in ("i", "em"):
            self._output.append("_")
        elif tag == "code":
            if self._in_code_block:
                return
            self._output.append("`")
        elif tag == "pre":
            self._in_code_block = False
            self._output.append("\n```\n")
        elif tag == "a":
            text = "".join(self._link_text)
            if self._href:
                self._output.append(f"[{text}]({self._href})")
            else:
                self._output.append(text)
            self._href = None
            self._link_text = []
        elif tag in ("ul", "ol"):
            if self._list_stack:
                self._list_stack.pop()
            self._output.append("\n")
        elif tag in ("td", "th"):
            self._current_row.append("".join(self._cell_text).strip())
            self._cell_text = []
        elif tag == "tr":
            self._table_rows.append(self._current_row)
            self._current_row = []
        elif tag == "table":
            self._in_table = False
            self._flush_table()

    def handle_data(self, data):
        if self._href is not None:
            self._link_text.append(data)
        elif self._in_table and (self._cell_text is not None):
            self._cell_text.append(data)
        else:
            self._output.append(data)

    def handle_entityref(self, name):
        entities = {"amp": "&", "lt": "<", "gt": ">", "quot": '"', "apos": "'"}
        self.handle_data(entities.get(name, f"&{name};"))

    def handle_charref(self, name):
        try:
            char = chr(int(name[1:], 16)) if name.startswith("x") else chr(int(name))
        except (ValueError, OverflowError):
            char = f"&#{name};"
        self.handle_data(char)

    def _flush_table(self):
        if not self._table_rows:
            return
        cols = max(len(row) for row in self._table_rows)
        for row in self._table_rows:
            while len(row) < cols:
                row.append("")
        self._output.append("\n\n")
        header = self._table_rows[0]
        self._output.append("| " + " | ".join(header) + " |\n")
        self._output.append("| " + " | ".join("---" for _ in header) + " |\n")
        for row in self._table_rows[1:]:
            self._output.append("| " + " | ".join(row) + " |\n")

    def get_markdown(self):
        text = "".join(self._output)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"


def html_to_markdown(html_content):
    converter = HtmlToMarkdown()
    converter.feed(html_content)
    return converter.get_markdown()


# ---------------------------------------------------------------------------
# URL parsing
# ---------------------------------------------------------------------------
def parse_slack_url(url):
    """Parse a Slack message URL into channel + timestamp components."""
    match = re.match(
        r"https?://[^/]+\.slack\.com/archives/([A-Z0-9]+)/p(\d+)(?:\?.*)?$",
        url,
    )
    if not match:
        print(f"Error: Could not parse Slack URL: {url}", file=sys.stderr)
        sys.exit(EXIT_USAGE)

    channel = match.group(1)
    raw_ts = match.group(2)
    ts = raw_ts[:-6] + "." + raw_ts[-6:]

    import urllib.parse
    qs = urllib.parse.urlparse(url).query
    params = urllib.parse.parse_qs(qs)
    thread_ts = params.get("thread_ts", [None])[0]
    cid = params.get("cid", [None])[0]

    result = {"channel": cid or channel, "ts": ts}
    if thread_ts:
        result["thread_ts"] = thread_ts
    return result


# ---------------------------------------------------------------------------
# Time range parsing
# ---------------------------------------------------------------------------
def parse_since(value):
    """Convert a --since value to a Unix timestamp string for the `oldest` param.

    Accepts Nh / Nd / Nw (relative) or an ISO date (YYYY-MM-DD).
    """
    s = value.strip().lower()
    m = re.fullmatch(r"(\d+)([hdw])", s)
    if m:
        n = int(m.group(1))
        secs = {"h": 3600, "d": 86400, "w": 604800}[m.group(2)]
        return f"{time.time() - n * secs:.6f}"
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
        return f"{dt.timestamp():.6f}"
    except ValueError:
        print(f"Error: Cannot parse --since '{value}'. Use Nh/Nd/Nw or YYYY-MM-DD.", file=sys.stderr)
        sys.exit(EXIT_USAGE)


# ---------------------------------------------------------------------------
# User resolution + message rendering
# ---------------------------------------------------------------------------
_USER_CACHE = {}


def resolve_users(client, user_ids):
    """Return {user_id: display_name} for the given IDs, caching across calls."""
    for uid in user_ids:
        if not uid or uid in _USER_CACHE:
            continue
        try:
            resp = client.users_info(user=uid)
            profile = resp.get("user", {}) or {}
            prof = profile.get("profile", {}) or {}
            _USER_CACHE[uid] = (
                prof.get("display_name") or profile.get("real_name") or profile.get("name") or uid
            )
        except SlackApiError:
            _USER_CACHE[uid] = uid
    return {uid: _USER_CACHE.get(uid, uid) for uid in user_ids if uid}


def collect_user_ids(messages):
    """Gather author IDs and in-text @-mention IDs from a list of messages."""
    ids = set()
    for m in messages:
        if m.get("user"):
            ids.add(m["user"])
        for uid in re.findall(r"<@([UW][A-Z0-9]+)", m.get("text", "") or ""):
            ids.add(uid)
    return ids


def format_text(text, user_map):
    """Resolve Slack mrkdwn entities to readable markdown."""
    if not text:
        return ""
    text = re.sub(
        r"<@([UW][A-Z0-9]+)(?:\|([^>]+))?>",
        lambda m: "@" + (user_map.get(m.group(1)) or m.group(2) or m.group(1)),
        text,
    )
    text = re.sub(r"<#(C[A-Z0-9]+)\|([^>]+)>", r"#\2", text)
    text = re.sub(r"<#(C[A-Z0-9]+)>", r"#\1", text)
    text = re.sub(r"<!(here|channel|everyone)>", r"@\1", text)
    text = re.sub(r"<!subteam\^[A-Z0-9]+\|(@[^>]+)>", r"\1", text)
    text = re.sub(r"<((?:https?|mailto):[^|>]+)\|([^>]+)>", r"[\2](\1)", text)
    text = re.sub(r"<((?:https?|mailto):[^>]+)>", r"\1", text)
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    return text


def fmt_ts(ts):
    try:
        return datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError, OverflowError):
        return str(ts)


def render_message(msg, user_map):
    """Render a single message to a markdown block."""
    uid = msg.get("user") or msg.get("bot_id", "")
    name = user_map.get(uid) or msg.get("username") or uid or "unknown"
    lines = [f"**{name}** · {fmt_ts(msg.get('ts', '0'))}"]
    body = format_text(msg.get("text", ""), user_map)
    if body:
        lines += ["", body]
    for f in msg.get("files", []) or []:
        title = f.get("title") or f.get("name") or "file"
        link = f.get("permalink") or f.get("url_private") or ""
        lines.append(f"📎 [{title}]({link})")
    return "\n".join(lines).rstrip()


def _blockquote(block):
    return "\n".join(("> " + ln) if ln else ">" for ln in block.split("\n"))


def render_thread_md(messages, user_map, label):
    out = [f"# Thread in {label}", ""]
    if not messages:
        out.append("_No messages._")
        return "\n".join(out)
    out.append(render_message(messages[0], user_map))
    replies = messages[1:]
    if replies:
        out += ["", f"## Replies ({len(replies)})"]
        for r in replies:
            out += ["", _blockquote(render_message(r, user_map))]
    return "\n".join(out).rstrip() + "\n"


def render_history_md(messages, user_map, label):
    out = [f"# {label}", ""]
    if not messages:
        out.append("_No messages in range._")
        return "\n".join(out) + "\n"
    for m in messages:
        out.append(render_message(m, user_map))
        for r in m.get("_replies", []) or []:
            out.append(_blockquote(render_message(r, user_map)))
        rc = m.get("reply_count", 0)
        if rc and not m.get("_replies"):
            out.append(f"_↳ {rc} repl{'y' if rc == 1 else 'ies'} — thread ts {m.get('ts')}_")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def enrich_messages(messages, user_map):
    """Attach resolved author_name to each message for --json output."""
    for m in messages:
        uid = m.get("user") or m.get("bot_id", "")
        m["author_name"] = user_map.get(uid) or m.get("username") or uid
        for r in m.get("_replies", []) or []:
            ruid = r.get("user") or r.get("bot_id", "")
            r["author_name"] = user_map.get(ruid) or r.get("username") or ruid
    return messages


def channel_label(client, channel):
    """Best-effort '#name' for a channel ID; falls back to the ID."""
    try:
        resp = client.conversations_info(channel=channel)
        name = (resp.get("channel", {}) or {}).get("name")
        return f"#{name}" if name else channel
    except SlackApiError:
        return channel


def read_content(inline, path):
    """Resolve content from --content or --content-file/--file."""
    if path:
        try:
            with open(path, "r") as f:
                return f.read()
        except OSError as e:
            print(f"Error: Cannot read file — {e}", file=sys.stderr)
            sys.exit(EXIT_USAGE)
    return inline


def load_channels_file(path):
    """Extract channel IDs (C...) from a markdown channel-list table."""
    ids = []
    try:
        with open(path, "r") as f:
            for line in f:
                m = re.match(r"\|\s*(C[A-Z0-9]+)\s*\|", line)
                if m:
                    ids.append(m.group(1))
    except OSError as e:
        print(f"Error: Cannot read channels file — {e}", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    if not ids:
        print(f"Error: No channel IDs (C...) found in {path}.", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    return ids


# ---------------------------------------------------------------------------
# Canvas helpers
# ---------------------------------------------------------------------------
def _downgrade_headings(content):
    """Downgrade H4+ headings to H3. Slack Canvas rejects H4+ (canvas_creation_failed)."""
    if re.search(r"^#{4,}\s", content, flags=re.MULTILINE):
        print(
            "Warning: Markdown contains H4+ headings (####) unsupported by Slack Canvas. "
            "Downgrading H4+ to H3.",
            file=sys.stderr,
        )
        content = re.sub(r"^#{4,}(\s)", r"###\1", content, flags=re.MULTILINE)
    return content


def _test_canvas_api_availability(client):
    """Silently verify canvases.create produces editable (non-quip) canvases."""
    try:
        resp = client.canvases_create(
            title="__api_test__",
            document_content={"type": "markdown", "markdown": "test"},
        )
        canvas_id = resp.get("canvas_id")
        if not canvas_id:
            return False
        info = client.files_info(file=canvas_id)
        is_quip = (info.get("file", {}) or {}).get("filetype", "") == "quip"
        try:
            client.files_delete(file=canvas_id)
        except SlackApiError:
            pass
        return not is_quip
    except SlackApiError:
        return False


def _canvas_append_chunked(client, canvas_id, content, chunk_size=3000):
    """Append content, auto-chunking on paragraph boundaries to stay under ~4KB/op."""
    if len(content.encode("utf-8")) <= chunk_size:
        slack_call(client.canvases_edit, canvas_id=canvas_id, changes=[
            {"operation": "insert_at_end", "document_content": {"type": "markdown", "markdown": content}}
        ])
        return 1

    chunks, current, current_size = [], [], 0
    for paragraph in content.split("\n\n"):
        para_size = len((paragraph + "\n\n").encode("utf-8"))
        if current_size + para_size > chunk_size and current:
            chunks.append("\n\n".join(current))
            current, current_size = [paragraph], para_size
        else:
            current.append(paragraph)
            current_size += para_size
    if current:
        chunks.append("\n\n".join(current))

    for i, chunk in enumerate(chunks):
        slack_call(client.canvases_edit, canvas_id=canvas_id, changes=[
            {"operation": "insert_at_end", "document_content": {"type": "markdown", "markdown": chunk}}
        ])
        if i < len(chunks) - 1:
            time.sleep(1)
    return len(chunks)


# ---------------------------------------------------------------------------
# Commands: extraction
# ---------------------------------------------------------------------------
def cmd_thread(args):
    client = get_client("bot" if args.bot else "user")
    if args.target.startswith("http"):
        parsed = parse_slack_url(args.target)
        channel = parsed["channel"]
        ts = parsed.get("thread_ts") or parsed["ts"]
    else:
        if not args.ts:
            print("Error: Provide a thread ts when target is a channel ID.", file=sys.stderr)
            sys.exit(EXIT_USAGE)
        channel, ts = args.target, args.ts

    limit = min(args.limit, 1000)
    messages = _paginate(client.conversations_replies, "messages", cap=limit, per_page=200,
                         channel=channel, ts=ts)
    user_map = resolve_users(client, collect_user_ids(messages))
    if args.json:
        print(json.dumps(enrich_messages(messages, user_map), indent=2))
    else:
        print(render_thread_md(messages, user_map, channel_label(client, channel)))


def cmd_history(args):
    client = get_client("bot" if args.bot else "user")
    limit = min(args.limit, 1000)
    params = {"channel": args.channel}
    if args.since:
        params["oldest"] = parse_since(args.since)
    messages = _paginate(client.conversations_history, "messages", cap=limit, per_page=100, **params)
    user_map = resolve_users(client, collect_user_ids(messages))
    if args.json:
        print(json.dumps(enrich_messages(messages, user_map), indent=2))
    else:
        label = f"History: {channel_label(client, args.channel)}"
        print(render_history_md(messages, user_map, label))


def cmd_catchup(args):
    client = get_client("bot" if args.bot else "user")
    channels = args.channels or (load_channels_file(args.channels_file) if args.channels_file else None)
    if not channels:
        print("Error: Provide --channels or --channels-file.", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    oldest = parse_since(args.since)
    per_channel_cap = min(args.limit, 1000)

    sections = []
    for ch in channels:
        msgs = _paginate(client.conversations_history, "messages", cap=per_channel_cap,
                         per_page=100, channel=ch, oldest=oldest)
        if not msgs:
            continue
        for m in msgs:
            if m.get("reply_count", 0) > 0:
                replies = _paginate(client.conversations_replies, "messages", cap=200,
                                    per_page=200, channel=ch, ts=m["ts"])
                m["_replies"] = replies[1:]  # drop the parent (already shown)
        sections.append((ch, msgs))

    all_ids = set()
    for _, msgs in sections:
        for m in msgs:
            all_ids |= collect_user_ids([m] + (m.get("_replies") or []))
    user_map = resolve_users(client, all_ids)

    if args.json:
        out = {ch: enrich_messages(msgs, user_map) for ch, msgs in sections}
        print(json.dumps(out, indent=2))
        return

    if not sections:
        print(f"# Catch-up\n\n_No activity since {args.since}._")
        return
    blocks = [f"# Catch-up — since {args.since}", ""]
    for ch, msgs in sections:
        blocks.append(render_history_md(msgs, user_map, channel_label(client, ch)))
    print("\n".join(blocks))


def cmd_channels(args):
    client = get_client("bot" if args.bot else "user")
    chans = _paginate(client.users_conversations, "channels", cap=min(args.limit, 1000),
                      per_page=200, types=args.types, exclude_archived=True)
    if args.resolve:
        needle = args.resolve.lower()
        matches = [{"id": c["id"], "name": c.get("name", "")} for c in chans
                   if needle in (c.get("name", "") or "").lower()]
        print(json.dumps(matches, indent=2))
        return
    if args.json:
        print(json.dumps(chans, indent=2))
        return
    lines = ["| ID | Name | Topic |", "|----|------|-------|"]
    for c in sorted(chans, key=lambda c: c.get("name", "")):
        topic = ((c.get("topic", {}) or {}).get("value", "") or "").replace("|", "\\|")[:60]
        lines.append(f"| {c['id']} | {c.get('name', '')} | {topic} |")
    print("\n".join(lines))


def cmd_mine(args):
    """Rank the authenticated user's own message counts per channel over a window.

    Reconstructs a `from:@me` view WITHOUT search:read — lists the user's channel
    memberships (users.conversations), tallies messages the user authored in each
    over --since, and reports channels ranked by participation (most active first).
    Reusable: vary --since to re-run the same evidence pull for any period.
    """
    client = get_client("bot" if args.bot else "user")
    require_scopes(client, "mine")  # preflight: channels:history before the sweep
    me = slack_call(client.auth_test).get("user_id")
    oldest = parse_since(args.since)
    per_channel_cap = min(args.msg_limit, 1000)

    chans = _paginate(client.users_conversations, "channels", cap=min(args.limit, 1000),
                      per_page=200, types=args.types, exclude_archived=True)

    rows = []
    skipped = 0
    total_chans = len(chans)
    for idx, c in enumerate(chans, 1):
        if sys.stderr.isatty():
            sys.stderr.write(f"\r[{idx}/{total_chans}] scanning #{c.get('name', '')[:40]}\033[K")
            sys.stderr.flush()
        try:
            msgs = _paginate(client.conversations_history, "messages", cap=per_channel_cap,
                             per_page=200, strict=False, channel=c["id"], oldest=oldest)
            capped = len(msgs) >= per_channel_cap  # hit the fetch cap — may undercount
            mine = [m for m in msgs if m.get("user") == me]
            if args.threads:
                for m in msgs:
                    if not m.get("reply_count", 0):
                        continue
                    # conversations.history already carries reply_users (distinct repliers).
                    # Only pay for a replies call when I might be among them: when the replier
                    # list is complete (count == len) and excludes me, skip it — accuracy-safe.
                    ru = m.get("reply_users") or []
                    ruc = m.get("reply_users_count", len(ru))
                    if me not in ru and ruc <= len(ru) and m.get("user") != me:
                        continue
                    replies = _paginate(client.conversations_replies, "messages", cap=1000,
                                        per_page=200, strict=False, channel=c["id"], ts=m["ts"])
                    mine += [r for r in replies[1:] if r.get("user") == me]
        except SlackApiError:
            skipped += 1  # channel_not_found / not_in_channel / etc. — unreadable, skip
            continue
        if mine:
            rows.append({"id": c["id"], "name": c.get("name", "") or c["id"],
                         "count": len(mine), "capped": capped, "messages": mine})
    if sys.stderr.isatty():
        sys.stderr.write("\r\033[K")  # clear the progress line
        sys.stderr.flush()

    rows.sort(key=lambda r: r["count"], reverse=True)
    total = sum(r["count"] for r in rows)

    if args.json:
        user_map = resolve_users(client, {me})
        print(json.dumps({
            "since": args.since,
            "user_id": me,
            "total_messages": total,
            "channels_with_activity": len(rows),
            "channels_skipped_unreadable": skipped,
            "threads_scanned": bool(args.threads),
            "channels": [
                {"id": r["id"], "name": r["name"], "count": r["count"], "capped": r["capped"],
                 "messages": enrich_messages(r["messages"], user_map)}
                for r in rows
            ],
        }, indent=2))
        return

    lines = [f"# My participation — since {args.since}", "",
             f"_{total} message(s) across {len(rows)} channel(s); ranked by my message count._", ""]
    if not rows:
        print("\n".join(lines) + "_No messages authored in range._\n")
        return
    lines += ["| Rank | Channel | My msgs | Note |", "|------|---------|---------|------|"]
    for i, r in enumerate(rows, 1):
        note = "⚠ capped — may undercount" if r["capped"] else ""
        lines.append(f"| {i} | #{r['name']} | {r['count']} | {note} |")
    lines.append("")
    lines.append(f"> Scope: channels you belong to in `{args.types}`. "
                 "1:1 DMs excluded unless `im` is added to --types and granted.")
    if not args.threads:
        lines.append("> Thread replies NOT counted — add `--threads` for reply-inclusive "
                     "counts (slower).")
    if any(r["capped"] for r in rows):
        lines.append(f"> ⚠ Capped channels hit the {per_channel_cap}-message fetch cap; "
                     "raise `--msg-limit` or narrow `--since` for exact counts.")
    if skipped:
        lines.append(f"> {skipped} channel(s) skipped (history not readable by this token).")
    print("\n".join(lines) + "\n")


def cmd_auth_check(args):
    client = get_client("bot" if args.bot else "user")
    resp = slack_call(client.auth_test)
    granted = scopes_from_response(resp)
    missing = sorted(REQUIRED_SCOPES - granted)
    print(json.dumps({
        "ok": True,
        "user": resp.get("user"),
        "team": resp.get("team"),
        "granted": sorted(granted),
        "missing": missing,
    }, indent=2))
    if missing:
        print(f"Warning: {len(missing)} required scope(s) missing — some commands will fail.",
              file=sys.stderr)


def render_search_md(matches, user_map, query):
    out = [f"# Search: {query}", "", f"_{len(matches)} match(es)_", ""]
    if not matches:
        out.append("_No matches._")
        return "\n".join(out) + "\n"
    for m in matches:
        ch = m.get("channel") or {}
        chname = ch.get("name") or ch.get("id", "")
        uid = m.get("user") or ""
        name = user_map.get(uid) or m.get("username") or uid or "unknown"
        out.append(f"**{name}** in #{chname} · {fmt_ts(m.get('ts', '0'))}")
        body = format_text(m.get("text", ""), user_map)
        if body:
            out += ["", body]
        if m.get("permalink"):
            out.append(f"[↗ view]({m['permalink']})")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def cmd_search(args):
    """Search messages across all channels/DMs the user can access (search.messages).

    User-token only — Slack does not allow bot tokens to call search.*.
    Query supports modifiers: in:#channel, from:@user, after:YYYY-MM-DD, before:, during:.
    """
    client = get_client("bot" if args.bot else "user")
    require_scopes(client, "search")  # preflight: fail loudly if search:read is absent
    cap = min(args.count, 1000)
    matches, page = [], 1
    while len(matches) < cap:
        resp = slack_call(client.search_messages, query=args.query,
                          count=min(100, cap - len(matches)), page=page,
                          sort=args.sort, sort_dir="desc")
        msgs = resp.get("messages") or {}
        batch = msgs.get("matches", []) or []
        matches.extend(batch)
        paging = msgs.get("paging", {}) or {}
        if not batch or page >= paging.get("pages", 1):
            break
        page += 1
    matches = matches[:cap]

    user_map = resolve_users(client, {m.get("user") for m in matches if m.get("user")})
    if args.json:
        for m in matches:
            m["author_name"] = user_map.get(m.get("user")) or m.get("username") or m.get("user")
        print(json.dumps(matches, indent=2))
    else:
        print(render_search_md(matches, user_map, args.query))


# ---------------------------------------------------------------------------
# Commands: canvas
# ---------------------------------------------------------------------------
def cmd_canvas_read(args):
    client = get_client("bot" if args.bot else "user")
    info = slack_call(client.files_info, file=args.canvas_id)
    file_data = info.get("file", {}) or {}
    filetype = file_data.get("filetype", "unknown")
    url_private = file_data.get("url_private")

    if not url_private:
        print(
            f"Error: No url_private for this canvas (filetype: {filetype}). "
            f"Canvas read is only reliably supported for quip-type canvases.",
            file=sys.stderr,
        )
        print(json.dumps({
            "canvas_id": args.canvas_id,
            "title": file_data.get("title", ""),
            "filetype": filetype,
            "permalink": file_data.get("permalink", ""),
        }))
        sys.exit(EXIT_API)

    raw = slack_download(url_private, client.token)
    if raw.lstrip().startswith("<"):
        print(html_to_markdown(raw))
    else:
        if filetype != "quip":
            print(f"Note: Canvas filetype '{filetype}' returned non-HTML content. Emitting raw.",
                  file=sys.stderr)
        print(raw)


def cmd_canvas_create(args):
    client = get_client("bot" if args.bot else "user")
    content = read_content(args.content, args.content_file)
    if not content:
        print("Error: Provide --content or --content-file.", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    if not _test_canvas_api_availability(client):
        print("Warning: Canvas API test failed or workspace produces quip canvases. "
              "Run 'canvas probe' to diagnose. Proceeding anyway.", file=sys.stderr)
    content = _downgrade_headings(content)
    resp = slack_call(client.canvases_create, title=args.title,
                      document_content={"type": "markdown", "markdown": content})
    print(json.dumps({"canvas_id": resp.get("canvas_id", "unknown")}))


def cmd_canvas_publish(args):
    """Aggregate: create a canvas from a markdown file, then optionally share it."""
    client = get_client("bot" if args.bot else "user")
    content = read_content(None, args.file)
    if not content:
        print("Error: --file is required and must be non-empty.", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    content = _downgrade_headings(content)

    if args.channel_tab:
        resp = slack_call(client.conversations_canvases_create, channel_id=args.channel_tab,
                          title=args.title, document_content={"type": "markdown", "markdown": content})
    else:
        if not _test_canvas_api_availability(client):
            print("Warning: workspace may produce non-editable (quip) canvases. Run 'canvas probe'.",
                  file=sys.stderr)
        resp = slack_call(client.canvases_create, title=args.title,
                          document_content={"type": "markdown", "markdown": content})
    canvas_id = resp.get("canvas_id", "unknown")

    shared = {}
    if args.share_channels:
        slack_call(client.canvases_access_set, canvas_id=canvas_id,
                   access_level=args.access, channel_ids=args.share_channels)
        shared["channels"] = args.share_channels
    if args.share_users:
        slack_call(client.canvases_access_set, canvas_id=canvas_id,
                   access_level=args.access, user_ids=args.share_users)
        shared["users"] = args.share_users

    print(json.dumps({"canvas_id": canvas_id, "channel_tab": args.channel_tab, "shared": shared}))


def cmd_canvas_update(args):
    client = get_client("bot" if args.bot else "user")
    info = slack_call(client.files_info, file=args.canvas_id)
    if (info.get("file", {}) or {}).get("filetype") == "quip":
        print("Warning: quip-type canvas — canvases.edit may not work. Consider 'canvas rewrite'.",
              file=sys.stderr)

    content = read_content(args.append or args.content, args.append_file or args.content_file)
    if args.append or args.append_file:
        chunks = _canvas_append_chunked(client, args.canvas_id, content)
        print(json.dumps({"ok": True, "chunks": chunks}))
    elif args.replace and content:
        slack_call(client.canvases_edit, canvas_id=args.canvas_id, changes=[
            {"operation": "replace", "section_id": args.replace,
             "document_content": {"type": "markdown", "markdown": content}}
        ])
        print(json.dumps({"ok": True}))
    else:
        print("Error: Provide --append[-file] or --replace <section_id> --content[-file].",
              file=sys.stderr)
        sys.exit(EXIT_USAGE)


def cmd_canvas_probe(args):
    client = get_client("bot" if args.bot else "user")
    resp = slack_call(client.canvases_create, title="__canvas_probe_test__",
                      document_content={"type": "markdown", "markdown": "probe"})
    canvas_id = resp.get("canvas_id", "unknown")
    info = slack_call(client.files_info, file=canvas_id)
    is_quip = (info.get("file", {}) or {}).get("filetype", "unknown") == "quip"
    try:
        del_resp = client.files_delete(file=canvas_id)
        cleaned_up = del_resp.get("ok", False)
    except SlackApiError:
        cleaned_up = False

    result = {
        "workspace_canvas_type": "quip" if is_quip else "new",
        "canvases_edit_supported": not is_quip,
        "chunked_create_supported": not is_quip,
        "probe_cleaned_up": cleaned_up,
    }
    if not cleaned_up:
        result["probe_canvas_id"] = canvas_id
    if is_quip:
        result["warning"] = (
            "This workspace routes canvases.create through legacy Quip backend. "
            "canvases.edit (append/replace) will not work reliably; create must fit ~4KB."
        )
    print(json.dumps(result, indent=2))


def cmd_canvas_rewrite(args):
    client = get_client("bot" if args.bot else "user")
    info = slack_call(client.files_info, file=args.canvas_id)
    file_data = info.get("file", {}) or {}
    if file_data.get("filetype", "") != "quip":
        print("Error: Canvas is not quip-type. No rewrite needed.", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    url_private = file_data.get("url_private")
    if not url_private:
        print("Error: No url_private in file info.", file=sys.stderr)
        sys.exit(EXIT_API)
    markdown = html_to_markdown(slack_download(url_private, client.token))
    title = file_data.get("title", "Rewritten Canvas")
    resp = slack_call(client.canvases_create, title=title,
                      document_content={"type": "markdown", "markdown": markdown})
    print(json.dumps({"old_canvas_id": args.canvas_id,
                      "new_canvas_id": resp.get("canvas_id", "unknown"), "title": title}))


def cmd_canvas_sections_lookup(args):
    client = get_client("bot" if args.bot else "user")
    criteria = {}
    if args.section_types:
        criteria["section_types"] = args.section_types
    if args.contains_text:
        criteria["contains_text"] = args.contains_text
    resp = slack_call(client.canvases_sections_lookup, canvas_id=args.canvas_id, criteria=criteria)
    print(json.dumps({"sections": resp.get("sections", [])}))


def cmd_canvas_delete(args):
    client = get_client("bot" if args.bot else "user")
    slack_call(client.canvases_delete, canvas_id=args.canvas_id)
    print(json.dumps({"ok": True, "canvas_id": args.canvas_id}))


def cmd_canvas_channel_create(args):
    client = get_client("bot" if args.bot else "user")
    content = read_content(args.content, args.content_file)
    payload = {"channel_id": args.channel_id}
    if content:
        payload["document_content"] = {"type": "markdown", "markdown": _downgrade_headings(content)}
    if args.title:
        payload["title"] = args.title
    resp = slack_call(client.conversations_canvases_create, **payload)
    print(json.dumps({"canvas_id": resp.get("canvas_id", "unknown"), "channel_id": args.channel_id}))


def _canvas_access_payload(args):
    if not args.channel_ids and not args.user_ids:
        print("Error: Provide --channel-ids or --user-ids.", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    if args.channel_ids and args.user_ids:
        print("Error: --channel-ids and --user-ids are mutually exclusive.", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    return ({"channel_ids": args.channel_ids} if args.channel_ids else {"user_ids": args.user_ids})


def cmd_canvas_access_set(args):
    client = get_client("bot" if args.bot else "user")
    payload = {"canvas_id": args.canvas_id, "access_level": args.access_level}
    payload.update(_canvas_access_payload(args))
    slack_call(client.canvases_access_set, **payload)
    print(json.dumps({"ok": True}))


def cmd_canvas_access_delete(args):
    client = get_client("bot" if args.bot else "user")
    payload = {"canvas_id": args.canvas_id}
    payload.update(_canvas_access_payload(args))
    slack_call(client.canvases_access_delete, **payload)
    print(json.dumps({"ok": True}))


# ---------------------------------------------------------------------------
# Commands: reactions + url
# ---------------------------------------------------------------------------
def cmd_react(args):
    client = get_client("bot" if args.bot else "user")
    slack_call(client.reactions_add, channel=args.channel, timestamp=args.timestamp,
               name=args.emoji.strip(":"))
    print(json.dumps({"ok": True}))


def cmd_unreact(args):
    client = get_client("bot" if args.bot else "user")
    slack_call(client.reactions_remove, channel=args.channel, timestamp=args.timestamp,
               name=args.emoji.strip(":"))
    print(json.dumps({"ok": True}))


def cmd_parse_url(args):
    print(json.dumps(parse_slack_url(args.url), indent=2))


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        prog="slacker",
        description="Slack Web API CLI — extraction (thread/history/catchup) + Canvas authoring",
    )
    parser.add_argument("--bot", action="store_true", help="Use bot token instead of user token")
    sub = parser.add_subparsers(dest="command", required=True)

    # --- thread ---
    t = sub.add_parser("thread", help="Pull a thread as readable markdown (or --json)")
    t.add_argument("target", help="Slack thread URL, or channel ID (with ts)")
    t.add_argument("ts", nargs="?", help="Thread parent ts (when target is a channel ID)")
    t.add_argument("--limit", type=int, default=500, help="Max messages (default 500, cap 1000)")
    t.add_argument("--json", action="store_true", help="Emit enriched JSON instead of markdown")
    t.set_defaults(func=cmd_thread)

    # --- history ---
    h = sub.add_parser("history", help="Channel history as readable markdown (or --json)")
    h.add_argument("channel", help="Channel ID")
    h.add_argument("--since", help="Time range: Nh/Nd/Nw or YYYY-MM-DD")
    h.add_argument("--limit", type=int, default=100, help="Max messages (default 100, cap 1000)")
    h.add_argument("--json", action="store_true", help="Emit enriched JSON instead of markdown")
    h.set_defaults(func=cmd_history)

    # --- catchup ---
    c = sub.add_parser("catchup", help="Multi-channel digest over a time range")
    c.add_argument("--channels", nargs="+", metavar="CHANNEL_ID", help="Channel IDs to scan")
    c.add_argument("--channels-file", help="Markdown file with a channel-list table (C... IDs)")
    c.add_argument("--since", required=True, help="Time range: Nh/Nd/Nw or YYYY-MM-DD")
    c.add_argument("--limit", type=int, default=100, help="Max messages per channel (default 100)")
    c.add_argument("--json", action="store_true", help="Emit enriched JSON instead of markdown")
    c.set_defaults(func=cmd_catchup)

    # --- channels ---
    ch = sub.add_parser("channels", help="List/resolve your channels")
    ch.add_argument("--types", default="public_channel,private_channel",
                    help="Comma list: public_channel,private_channel,im,mpim")
    ch.add_argument("--resolve", metavar="NAME", help="Return IDs for channels matching this name")
    ch.add_argument("--limit", type=int, default=1000, help="Max channels (default 1000)")
    ch.add_argument("--json", action="store_true", help="Emit raw JSON instead of a table")
    ch.set_defaults(func=cmd_channels)

    # --- mine ---
    mn = sub.add_parser("mine",
                        help="Rank your own message counts per channel (from:@me, no search:read)")
    mn.add_argument("--since", required=True, help="Time range: Nh/Nd/Nw or YYYY-MM-DD")
    mn.add_argument("--types", default="public_channel,private_channel",
                    help="Comma list: public_channel,private_channel,mpim,im")
    mn.add_argument("--limit", type=int, default=1000, help="Max channels to scan (default 1000)")
    mn.add_argument("--msg-limit", type=int, default=1000, dest="msg_limit",
                    help="Max messages fetched per channel (default 1000, cap 1000)")
    mn.add_argument("--threads", action="store_true", help="Also count your thread replies (slower)")
    mn.add_argument("--json", action="store_true", help="Emit structured JSON incl. your messages")
    mn.set_defaults(func=cmd_mine)

    # --- search ---
    s = sub.add_parser("search", help="Search messages across all channels/DMs you can access")
    s.add_argument("query", help="Query; supports in:#channel, from:@user, after:YYYY-MM-DD, before:, during:")
    s.add_argument("--count", type=int, default=100, help="Max matches (default 100, cap 1000)")
    s.add_argument("--sort", choices=["score", "timestamp"], default="score", help="Ranking (default score)")
    s.add_argument("--json", action="store_true", help="Emit enriched JSON instead of markdown")
    s.set_defaults(func=cmd_search)

    # --- auth-check ---
    a = sub.add_parser("auth-check", help="Verify token validity and required scopes")
    a.set_defaults(func=cmd_auth_check)

    # --- canvas ---
    canvas = sub.add_parser("canvas", help="Canvas operations")
    cs = canvas.add_subparsers(dest="canvas_command", required=True)

    cr = cs.add_parser("read", help="Read canvas as markdown")
    cr.add_argument("canvas_id", help="Canvas file ID (F-prefixed)")
    cr.set_defaults(func=cmd_canvas_read)

    cc = cs.add_parser("create", help="Create a new canvas (primitive)")
    cc.add_argument("title", help="Canvas title")
    cc.add_argument("--content", help="Markdown content")
    cc.add_argument("--content-file", help="Path to markdown file")
    cc.set_defaults(func=cmd_canvas_create)

    cpub = cs.add_parser("publish", help="Publish a canvas from a markdown file + optionally share")
    cpub.add_argument("title", help="Canvas title")
    cpub.add_argument("--file", required=True, help="Path to markdown file")
    cpub.add_argument("--channel-tab", metavar="CHANNEL_ID",
                      help="Create as a channel-pinned tab instead of standalone")
    cpub.add_argument("--share-channels", nargs="+", metavar="CHANNEL_ID", help="Grant access to channels")
    cpub.add_argument("--share-users", nargs="+", metavar="USER_ID", help="Grant access to users")
    cpub.add_argument("--access", choices=["read", "write"], default="read", help="Access level to grant")
    cpub.set_defaults(func=cmd_canvas_publish)

    cu = cs.add_parser("update", help="Update an existing canvas")
    cu.add_argument("canvas_id", help="Canvas file ID (F-prefixed)")
    cu.add_argument("--append", help="Markdown to append (inline)")
    cu.add_argument("--append-file", help="Path to markdown file to append")
    cu.add_argument("--replace", metavar="SECTION_ID", help="Section ID to replace")
    cu.add_argument("--content", help="Replacement content (inline, with --replace)")
    cu.add_argument("--content-file", help="Replacement content file (with --replace)")
    cu.set_defaults(func=cmd_canvas_update)

    cw = cs.add_parser("rewrite", help="Rewrite quip canvas as new-type canvas")
    cw.add_argument("canvas_id", help="Quip canvas file ID")
    cw.set_defaults(func=cmd_canvas_rewrite)

    cp = cs.add_parser("probe", help="Detect quip vs new-type canvas workspace")
    cp.set_defaults(func=cmd_canvas_probe)

    csec = cs.add_parser("sections", help="Canvas section operations")
    ssub = csec.add_subparsers(dest="sections_command", required=True)
    csl = ssub.add_parser("lookup", help="Find section IDs by type/text (for targeted edits)")
    csl.add_argument("canvas_id", help="Canvas file ID (F-prefixed)")
    csl.add_argument("--section-types", nargs="+", choices=["h1", "h2", "h3", "any_header"],
                     metavar="TYPE", help="Filter by section type")
    csl.add_argument("--contains-text", metavar="TEXT", help="Filter sections containing this text")
    csl.set_defaults(func=cmd_canvas_sections_lookup)

    cd = cs.add_parser("delete", help="Permanently delete a canvas")
    cd.add_argument("canvas_id", help="Canvas file ID (F-prefixed)")
    cd.set_defaults(func=cmd_canvas_delete)

    ccc = cs.add_parser("channel-create", help="Create a channel-pinned canvas tab")
    ccc.add_argument("channel_id", help="Channel ID to attach canvas to")
    ccc.add_argument("--title", help="Canvas title")
    ccc.add_argument("--content", help="Markdown content")
    ccc.add_argument("--content-file", help="Path to markdown file")
    ccc.set_defaults(func=cmd_canvas_channel_create)

    ca = cs.add_parser("access", help="Canvas access management")
    asub = ca.add_subparsers(dest="access_command", required=True)
    cas = asub.add_parser("set", help="Grant or change canvas access")
    cas.add_argument("canvas_id", help="Canvas file ID (F-prefixed)")
    cas.add_argument("access_level", choices=["read", "write", "owner"], help="Access level")
    cas.add_argument("--channel-ids", nargs="+", metavar="CHANNEL_ID",
                     help="Channel IDs (mutually exclusive with --user-ids)")
    cas.add_argument("--user-ids", nargs="+", metavar="USER_ID",
                     help="User IDs (mutually exclusive with --channel-ids)")
    cas.set_defaults(func=cmd_canvas_access_set)
    cad = asub.add_parser("delete", help="Revoke canvas access")
    cad.add_argument("canvas_id", help="Canvas file ID (F-prefixed)")
    cad.add_argument("--channel-ids", nargs="+", metavar="CHANNEL_ID", help="Channel IDs to revoke")
    cad.add_argument("--user-ids", nargs="+", metavar="USER_ID", help="User IDs to revoke")
    cad.set_defaults(func=cmd_canvas_access_delete)

    # --- react / unreact ---
    rp = sub.add_parser("react", help="Add reaction to message")
    rp.add_argument("channel", help="Channel ID")
    rp.add_argument("timestamp", help="Message timestamp")
    rp.add_argument("emoji", help="Emoji name (without colons)")
    rp.set_defaults(func=cmd_react)

    up = sub.add_parser("unreact", help="Remove reaction from message")
    up.add_argument("channel", help="Channel ID")
    up.add_argument("timestamp", help="Message timestamp")
    up.add_argument("emoji", help="Emoji name (without colons)")
    up.set_defaults(func=cmd_unreact)

    # --- parse-url ---
    pp = sub.add_parser("parse-url", help="Parse Slack URL to components")
    pp.add_argument("url", help="Slack message URL")
    pp.set_defaults(func=cmd_parse_url)

    return parser


def main():
    args = build_parser().parse_args()
    if not hasattr(args, "bot"):
        args.bot = False
    args.func(args)


if __name__ == "__main__":
    main()
