#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Slack Web API CLI — Canvas read/create/update, reactions, threads, history.

Fills gaps in the official Slack MCP plugin (no Canvas read/update, no reactions)
and provides a full fallback when MCP is unavailable.

Usage:
    python3 slacker.py <command> [args]

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
import urllib.parse
import urllib.request


# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------
EXIT_OK = 0
EXIT_USAGE = 1
EXIT_AUTH = 2
EXIT_API = 3
EXIT_RATE = 4


# ---------------------------------------------------------------------------
# Token resolution
# ---------------------------------------------------------------------------
def resolve_token(token_type="user"):
    """Resolve Slack token: env var → keychainctl fallback → prefix validation."""
    env_var = "SLACK_BOT_TOKEN" if token_type == "bot" else "SLACK_USER_TOKEN"
    token = os.environ.get(env_var)

    if not token:
        keychain_key = env_var
        try:
            result = subprocess.run(
                ["keychainctl", "get", keychain_key],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                token = result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    if not token:
        print(f"Error: No Slack token found. Set ${env_var} or store via keychainctl.", file=sys.stderr)
        sys.exit(EXIT_AUTH)

    expected_prefix = "xoxb-" if token_type == "bot" else "xoxp-"
    if not token.startswith(expected_prefix):
        # Allow either prefix — bot commands can use user tokens too
        if not token.startswith(("xoxp-", "xoxb-")):
            print(f"Error: Token has invalid prefix (expected xoxp- or xoxb-).", file=sys.stderr)
            sys.exit(EXIT_AUTH)

    return token


# ---------------------------------------------------------------------------
# Slack API helpers
# ---------------------------------------------------------------------------
def slack_post(method, token, **params):
    """POST form-encoded request to Slack Web API. Returns parsed JSON.

    Handles 429 rate limiting with one retry using Retry-After header.
    """
    url = f"https://slack.com/api/{method}"
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    for attempt in range(2):
        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read().decode("utf-8")
                result = json.loads(body, strict=False)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt == 0:
                retry_after = int(e.headers.get("Retry-After", "5"))
                print(f"Rate limited, retrying in {retry_after}s...", file=sys.stderr)
                time.sleep(retry_after)
                continue
            if e.code == 429:
                print(f"Error: Rate limited after retry.", file=sys.stderr)
                sys.exit(EXIT_RATE)
            print(f"Error: HTTP {e.code} from {method}", file=sys.stderr)
            sys.exit(EXIT_API)

        if not result.get("ok"):
            error = result.get("error", "unknown")
            if error in ("not_authed", "invalid_auth", "token_revoked"):
                print(f"Error: Auth failed — {error}", file=sys.stderr)
                sys.exit(EXIT_AUTH)
            print(f"Error: {method} failed — {error}", file=sys.stderr)
            sys.exit(EXIT_API)

        return result

    # Should not reach here
    sys.exit(EXIT_RATE)


def slack_download(url, token):
    """Authenticated GET for url_private content. Returns decoded string."""
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"Error: Failed to download — HTTP {e.code}", file=sys.stderr)
        sys.exit(EXIT_API)


def slack_post_json(method, token, payload):
    """POST JSON body to Slack Web API. Used for endpoints requiring JSON (canvases.*)."""
    url = f"https://slack.com/api/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )

    for attempt in range(2):
        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read().decode("utf-8")
                result = json.loads(body, strict=False)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt == 0:
                retry_after = int(e.headers.get("Retry-After", "5"))
                print(f"Rate limited, retrying in {retry_after}s...", file=sys.stderr)
                time.sleep(retry_after)
                continue
            if e.code == 429:
                print(f"Error: Rate limited after retry.", file=sys.stderr)
                sys.exit(EXIT_RATE)
            print(f"Error: HTTP {e.code} from {method}", file=sys.stderr)
            sys.exit(EXIT_API)

        if not result.get("ok"):
            error = result.get("error", "unknown")
            if error in ("not_authed", "invalid_auth", "token_revoked"):
                print(f"Error: Auth failed — {error}", file=sys.stderr)
                sys.exit(EXIT_AUTH)
            print(f"Error: {method} failed — {error}", file=sys.stderr)
            sys.exit(EXIT_API)

        return result

    sys.exit(EXIT_RATE)


# ---------------------------------------------------------------------------
# HTML → Markdown converter (for quip-type canvases)
# ---------------------------------------------------------------------------
class HtmlToMarkdown(html.parser.HTMLParser):
    """Convert Slack quip canvas HTML to markdown using stdlib only."""

    def __init__(self):
        super().__init__()
        self._output = []
        self._stack = []  # element tag stack
        self._list_stack = []  # (tag, counter) for nested lists
        self._href = None
        self._link_text = []
        self._in_code_block = False
        self._table_rows = []
        self._current_row = []
        self._cell_text = []
        self._in_table = False
        self._suppress_data = False

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
        elif tag == "p":
            pass  # handled in starttag

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
            if name.startswith("x"):
                char = chr(int(name[1:], 16))
            else:
                char = chr(int(name))
        except (ValueError, OverflowError):
            char = f"&#{name};"
        self.handle_data(char)

    def _flush_table(self):
        if not self._table_rows:
            return
        # Determine column widths
        cols = max(len(row) for row in self._table_rows)
        # Pad rows to same length
        for row in self._table_rows:
            while len(row) < cols:
                row.append("")

        self._output.append("\n\n")
        # Header row
        header = self._table_rows[0]
        self._output.append("| " + " | ".join(header) + " |\n")
        self._output.append("| " + " | ".join("---" for _ in header) + " |\n")
        # Data rows
        for row in self._table_rows[1:]:
            self._output.append("| " + " | ".join(row) + " |\n")

    def get_markdown(self):
        text = "".join(self._output)
        # Clean up excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"


def html_to_markdown(html_content):
    """Convert HTML string to markdown."""
    converter = HtmlToMarkdown()
    converter.feed(html_content)
    return converter.get_markdown()


# ---------------------------------------------------------------------------
# URL parsing
# ---------------------------------------------------------------------------
def parse_slack_url(url):
    """Parse a Slack URL into channel and timestamp components."""
    # Pattern: https://<workspace>.slack.com/archives/<CHANNEL>/p<TS>
    match = re.match(
        r"https?://[^/]+\.slack\.com/archives/([A-Z0-9]+)/p(\d+)(?:\?.*)?$",
        url,
    )
    if not match:
        print(f"Error: Could not parse Slack URL: {url}", file=sys.stderr)
        sys.exit(EXIT_USAGE)

    channel = match.group(1)
    raw_ts = match.group(2)
    # Convert: strip p prefix already done by regex, insert . before last 6 digits
    ts = raw_ts[:-6] + "." + raw_ts[-6:]

    # Check for thread_ts in query params
    qs = urllib.parse.urlparse(url).query
    params = urllib.parse.parse_qs(qs)
    thread_ts = params.get("thread_ts", [None])[0]
    cid = params.get("cid", [None])[0]

    result = {"channel": cid or channel, "ts": ts}
    if thread_ts:
        result["thread_ts"] = thread_ts

    return result


# ---------------------------------------------------------------------------
# Commands: Canvas
# ---------------------------------------------------------------------------
def cmd_canvas_read(args):
    """Read a canvas and output as markdown."""
    token = resolve_token("bot" if args.bot else "user")

    # Get file info to determine canvas type
    info = slack_post("files.info", token, file=args.canvas_id)
    file_data = info.get("file", {})
    filetype = file_data.get("filetype", "")

    if filetype == "quip":
        # Quip-type canvas: download HTML and convert to markdown
        url_private = file_data.get("url_private")
        if not url_private:
            print("Error: No url_private in file info.", file=sys.stderr)
            sys.exit(EXIT_API)
        html_content = slack_download(url_private, token)
        markdown = html_to_markdown(html_content)
        print(markdown)
    else:
        # New Canvas API type: use canvases.sections.lookup
        try:
            result = slack_post_json("canvases.sections.lookup", token, {
                "canvas_id": args.canvas_id,
                "criteria": {},
            })
            sections = result.get("sections", [])
            if not sections:
                print("(empty canvas)")
                return
            for section in sections:
                content = section.get("markdown", section.get("content", ""))
                if content:
                    print(content)
        except SystemExit as e:
            if e.code == EXIT_API:
                # Fallback: try reading as file with url_private
                url_private = file_data.get("url_private")
                if url_private:
                    content = slack_download(url_private, token)
                    print(content)
                else:
                    raise


def cmd_canvas_create(args):
    """Create a new canvas."""
    token = resolve_token("bot" if args.bot else "user")

    if args.content_file:
        try:
            with open(args.content_file, "r") as f:
                content = f.read()
        except OSError as e:
            print(f"Error: Cannot read file — {e}", file=sys.stderr)
            sys.exit(EXIT_USAGE)
    elif args.content:
        content = args.content
    else:
        print("Error: Provide --content or --content-file.", file=sys.stderr)
        sys.exit(EXIT_USAGE)

    result = slack_post_json("canvases.create", token, {
        "title": args.title,
        "document_content": {"type": "markdown", "markdown": content},
    })

    canvas_id = result.get("canvas_id", "unknown")
    print(json.dumps({"canvas_id": canvas_id}))


def cmd_canvas_update(args):
    """Update an existing canvas."""
    token = resolve_token("bot" if args.bot else "user")

    # Check if this is a quip canvas
    info = slack_post("files.info", token, file=args.canvas_id)
    file_data = info.get("file", {})
    if file_data.get("filetype") == "quip":
        print("Warning: This is a quip-type canvas. Updates via canvases.edit may not work.", file=sys.stderr)
        print("Suggestion: Use 'canvas rewrite' to migrate to a new-type canvas first.", file=sys.stderr)

    if args.append:
        changes = [{"operation": "insert_at_end", "document_content": {"type": "markdown", "markdown": args.append}}]
    elif args.replace and args.content:
        changes = [{"operation": "replace", "section_id": args.replace, "document_content": {"type": "markdown", "markdown": args.content}}]
    else:
        print("Error: Provide --append or --replace <section_id> --content.", file=sys.stderr)
        sys.exit(EXIT_USAGE)

    slack_post_json("canvases.edit", token, {
        "canvas_id": args.canvas_id,
        "changes": changes,
    })
    print(json.dumps({"ok": True}))


def cmd_canvas_rewrite(args):
    """Rewrite a quip canvas as a new-type canvas."""
    token = resolve_token("bot" if args.bot else "user")

    # Read the original canvas
    info = slack_post("files.info", token, file=args.canvas_id)
    file_data = info.get("file", {})
    filetype = file_data.get("filetype", "")

    if filetype != "quip":
        print("Error: Canvas is not a quip-type. No rewrite needed.", file=sys.stderr)
        sys.exit(EXIT_USAGE)

    url_private = file_data.get("url_private")
    if not url_private:
        print("Error: No url_private in file info.", file=sys.stderr)
        sys.exit(EXIT_API)

    # Download and convert
    html_content = slack_download(url_private, token)
    markdown = html_to_markdown(html_content)

    # Create new canvas
    title = file_data.get("title", "Rewritten Canvas")
    result = slack_post_json("canvases.create", token, {
        "title": title,
        "document_content": {"type": "markdown", "markdown": markdown},
    })

    new_id = result.get("canvas_id", "unknown")
    old_id = args.canvas_id
    print(json.dumps({"old_canvas_id": old_id, "new_canvas_id": new_id, "title": title}))


# ---------------------------------------------------------------------------
# Commands: Reactions
# ---------------------------------------------------------------------------
def cmd_react(args):
    """Add a reaction to a message."""
    token = resolve_token("bot" if args.bot else "user")
    # Strip colons if user included them
    emoji = args.emoji.strip(":")
    slack_post("reactions.add", token, channel=args.channel, timestamp=args.timestamp, name=emoji)
    print(json.dumps({"ok": True}))


def cmd_unreact(args):
    """Remove a reaction from a message."""
    token = resolve_token("bot" if args.bot else "user")
    emoji = args.emoji.strip(":")
    slack_post("reactions.remove", token, channel=args.channel, timestamp=args.timestamp, name=emoji)
    print(json.dumps({"ok": True}))


# ---------------------------------------------------------------------------
# Commands: Thread / History
# ---------------------------------------------------------------------------
def cmd_thread(args):
    """Get all replies in a thread with pagination."""
    token = resolve_token("bot" if args.bot else "user")
    messages = []
    cursor = None
    limit = min(args.limit, 1000)
    per_page = min(limit, 200)

    while len(messages) < limit:
        params = {"channel": args.channel, "ts": args.thread_ts, "limit": per_page}
        if cursor:
            params["cursor"] = cursor
        result = slack_post("conversations.replies", token, **params)
        batch = result.get("messages", [])
        messages.extend(batch)

        cursor = result.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    messages = messages[:limit]
    print(json.dumps(messages, indent=2))


def cmd_history(args):
    """Get channel history with pagination."""
    token = resolve_token("bot" if args.bot else "user")
    messages = []
    cursor = None
    limit = min(args.limit, 1000)
    per_page = min(limit, 100)

    while len(messages) < limit:
        params = {"channel": args.channel, "limit": per_page}
        if cursor:
            params["cursor"] = cursor
        result = slack_post("conversations.history", token, **params)
        batch = result.get("messages", [])
        messages.extend(batch)

        cursor = result.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    messages = messages[:limit]
    print(json.dumps(messages, indent=2))


def cmd_parse_url(args):
    """Parse a Slack URL into components."""
    result = parse_slack_url(args.url)
    print(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        prog="slacker",
        description="Slack Web API CLI — Canvas, reactions, threads, history",
    )
    parser.add_argument("--bot", action="store_true", help="Use bot token instead of user token")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- canvas ---
    canvas_parser = subparsers.add_parser("canvas", help="Canvas operations")
    canvas_sub = canvas_parser.add_subparsers(dest="canvas_command", required=True)

    # canvas read
    cr = canvas_sub.add_parser("read", help="Read canvas as markdown")
    cr.add_argument("canvas_id", help="Canvas file ID (F-prefixed)")
    cr.set_defaults(func=cmd_canvas_read)

    # canvas create
    cc = canvas_sub.add_parser("create", help="Create a new canvas")
    cc.add_argument("title", help="Canvas title")
    cc.add_argument("--content", help="Markdown content")
    cc.add_argument("--content-file", help="Path to markdown file")
    cc.set_defaults(func=cmd_canvas_create)

    # canvas update
    cu = canvas_sub.add_parser("update", help="Update an existing canvas")
    cu.add_argument("canvas_id", help="Canvas file ID (F-prefixed)")
    cu.add_argument("--append", help="Markdown to append at end")
    cu.add_argument("--replace", metavar="SECTION_ID", help="Section ID to replace")
    cu.add_argument("--content", help="Replacement content (with --replace)")
    cu.set_defaults(func=cmd_canvas_update)

    # canvas rewrite
    cw = canvas_sub.add_parser("rewrite", help="Rewrite quip canvas as new-type canvas")
    cw.add_argument("canvas_id", help="Quip canvas file ID to rewrite")
    cw.set_defaults(func=cmd_canvas_rewrite)

    # --- react ---
    react_parser = subparsers.add_parser("react", help="Add reaction to message")
    react_parser.add_argument("channel", help="Channel ID")
    react_parser.add_argument("timestamp", help="Message timestamp")
    react_parser.add_argument("emoji", help="Emoji name (without colons)")
    react_parser.set_defaults(func=cmd_react)

    # --- unreact ---
    unreact_parser = subparsers.add_parser("unreact", help="Remove reaction from message")
    unreact_parser.add_argument("channel", help="Channel ID")
    unreact_parser.add_argument("timestamp", help="Message timestamp")
    unreact_parser.add_argument("emoji", help="Emoji name (without colons)")
    unreact_parser.set_defaults(func=cmd_unreact)

    # --- thread ---
    thread_parser = subparsers.add_parser("thread", help="Get thread replies")
    thread_parser.add_argument("channel", help="Channel ID")
    thread_parser.add_argument("thread_ts", help="Thread parent timestamp")
    thread_parser.add_argument("--limit", type=int, default=200, help="Max messages (default: 200, cap: 1000)")
    thread_parser.set_defaults(func=cmd_thread)

    # --- history ---
    history_parser = subparsers.add_parser("history", help="Get channel history")
    history_parser.add_argument("channel", help="Channel ID")
    history_parser.add_argument("--limit", type=int, default=100, help="Max messages (default: 100, cap: 1000)")
    history_parser.set_defaults(func=cmd_history)

    # --- parse-url ---
    parse_parser = subparsers.add_parser("parse-url", help="Parse Slack URL to components")
    parse_parser.add_argument("url", help="Slack message URL")
    parse_parser.set_defaults(func=cmd_parse_url)

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = build_parser()
    args = parser.parse_args()

    # Propagate --bot from top-level to subcommands
    if not hasattr(args, "bot"):
        args.bot = False

    args.func(args)


if __name__ == "__main__":
    main()
