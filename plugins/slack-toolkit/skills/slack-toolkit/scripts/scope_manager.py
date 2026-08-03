#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = ["slack_sdk", "pip-system-certs"]
# ///
"""
Slack app scope manager — safely change a manifest's OAuth scopes, with auto-backup + revert.

Standalone helper (separate from slacker.py) because it uses a DIFFERENT credential:
an app **configuration token** (xoxe.xoxp-…), NOT your SLACK_USER_TOKEN. It edits the app's
manifest via apps.manifest.export/update, always backing up the prior scopes first so you can
`revert` if a manual reinstall turns out to require admin approval you can't get.

    uv run scope_manager.py status  [--app-id A123]
    uv run scope_manager.py add     --user search:read im:read [--bot chat:write] [--app-id A123]
    uv run scope_manager.py remove  --user search:read [--app-id A123]
    uv run scope_manager.py revert  [--app-id A123] [--backup PATH]
    uv run scope_manager.py rotate  # refresh the config token

Credentials (env var first, then `keychainctl get <NAME>`):
    SLACK_CONFIG_TOKEN          config ACCESS token (xoxe.xoxp-…) — required for all but rotate
    SLACK_CONFIG_REFRESH_TOKEN  config REFRESH token (xoxe-…)     — required for rotate
    SLACK_APP_ID                default app ID (or pass --app-id)
    SLACK_USER_TOKEN            optional — enables the live-vs-configured delta in `status`

Exit codes: 0 ok · 1 usage · 2 auth · 3 API error.

IMPORTANT: editing the manifest only changes what the app *requests*. Your installed token
keeps its old scopes until the app is reinstalled through the browser OAuth consent screen.
This helper cannot perform that consent step; it prints where to do it.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

EXIT_OK, EXIT_USAGE, EXIT_AUTH, EXIT_API = 0, 1, 2, 3

BACKUP_DIR = Path.home() / ".slack-toolkit"


# ---------------------------------------------------------------------------
# Credential + app-id resolution
# ---------------------------------------------------------------------------
def _resolve(name):
    """env var first, then `keychainctl get <name>`."""
    val = os.environ.get(name)
    if val:
        return val.strip()
    try:
        r = subprocess.run(["keychainctl", "get", name], capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def config_client():
    token = _resolve("SLACK_CONFIG_TOKEN")
    if not token:
        print("Error: No config token. Set $SLACK_CONFIG_TOKEN (xoxe.xoxp-…) or store via "
              "keychainctl. Generate one at https://api.slack.com/apps → your app → "
              "'App Manifest' / configuration tokens, or run `scope_manager.py rotate`.",
              file=sys.stderr)
        sys.exit(EXIT_AUTH)
    if not token.startswith("xoxe."):
        print("Warning: config token does not start with 'xoxe.' — apps.manifest.* may reject it.",
              file=sys.stderr)
    return WebClient(token=token)


def resolve_app_id(args):
    app_id = getattr(args, "app_id", None) or _resolve("SLACK_APP_ID")
    if not app_id:
        print("Error: No app ID. Pass --app-id or set $SLACK_APP_ID (e.g. A0123ABCD).",
              file=sys.stderr)
        sys.exit(EXIT_USAGE)
    return app_id


def _call(method, **kwargs):
    try:
        return method(**kwargs)
    except SlackApiError as e:
        err = "unknown"
        try:
            err = e.response.get("error", "unknown")
        except Exception:
            err = str(e)
        if err in ("not_authed", "invalid_auth", "token_expired", "token_revoked"):
            print(f"Error: config-token auth failed — {err}. Try `scope_manager.py rotate`.",
                  file=sys.stderr)
            sys.exit(EXIT_AUTH)
        print(f"Error: {method.__name__} failed — {err}", file=sys.stderr)
        sys.exit(EXIT_API)


# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------
def export_manifest(client, app_id):
    resp = _call(client.apps_manifest_export, app_id=app_id)
    manifest = resp.get("manifest")
    if not manifest:
        print("Error: apps.manifest.export returned no manifest.", file=sys.stderr)
        sys.exit(EXIT_API)
    return manifest


def get_scopes(manifest):
    scopes = ((manifest.get("oauth_config") or {}).get("scopes") or {})
    return {
        "bot": list(scopes.get("bot", []) or []),
        "user": list(scopes.get("user", []) or []),
    }


def set_scopes(manifest, bot, user):
    manifest.setdefault("oauth_config", {}).setdefault("scopes", {})
    manifest["oauth_config"]["scopes"]["bot"] = sorted(set(bot))
    manifest["oauth_config"]["scopes"]["user"] = sorted(set(user))
    return manifest


def backup_path(app_id):
    return BACKUP_DIR / f"scope-backup-{app_id}.json"


def write_backup(app_id, manifest):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    path = backup_path(app_id)
    payload = {
        "app_id": app_id,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "scopes": get_scopes(manifest),
    }
    path.write_text(json.dumps(payload, indent=2))
    return path


def reinstall_hint(app_id):
    return (
        f"\nNext: reinstall the app to grant the new scopes (browser consent required):\n"
        f"  https://api.slack.com/apps/{app_id}  →  'Install App'  →  Reinstall to Workspace\n"
        f"Then run: slacker.py auth-check  (confirms the new scopes reached your token).\n"
        f"If reinstall is blocked by admin approval you can't get, run:\n"
        f"  scope_manager.py revert --app-id {app_id}\n"
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_status(args):
    client = config_client()
    app_id = resolve_app_id(args)
    configured = get_scopes(export_manifest(client, app_id))
    out = {"app_id": app_id, "configured": configured}

    live = None
    user_token = _resolve("SLACK_USER_TOKEN")
    if user_token:
        try:
            resp = WebClient(token=user_token).auth_test()
            hdr = ""
            for k, v in (resp.headers or {}).items():
                if k.lower() == "x-oauth-scopes":
                    hdr = v
                    break
            live = sorted({s.strip() for s in hdr.split(",") if s.strip()})
        except SlackApiError:
            live = None

    if live is not None:
        out["installed_user_scopes"] = live
        # Configured user scopes not yet present in the installed token => reinstall pending.
        pending = sorted(set(configured["user"]) - set(live))
        out["reinstall_pending_user_scopes"] = pending
        out["reinstall_pending"] = bool(pending)

    bp = backup_path(app_id)
    out["backup_exists"] = bp.exists()
    if bp.exists():
        out["backup_path"] = str(bp)
    print(json.dumps(out, indent=2))


def _mutate(args, adding):
    client = config_client()
    app_id = resolve_app_id(args)
    add_bot, add_user = args.bot or [], args.user or []
    if not add_bot and not add_user:
        print("Error: provide --user and/or --bot scopes.", file=sys.stderr)
        sys.exit(EXIT_USAGE)

    manifest = export_manifest(client, app_id)
    before = get_scopes(manifest)
    bot, user = set(before["bot"]), set(before["user"])
    if adding:
        bot |= set(add_bot)
        user |= set(add_user)
    else:
        bot -= set(add_bot)
        user -= set(add_user)
    after = {"bot": sorted(bot), "user": sorted(user)}

    if after == before:
        print(json.dumps({"ok": True, "changed": False, "scopes": before}))
        return

    bp = write_backup(app_id, manifest)
    set_scopes(manifest, bot, user)

    if args.dry_run:
        print(json.dumps({"ok": True, "dry_run": True, "app_id": app_id,
                          "before": before, "after": after, "backup": str(bp)}, indent=2))
        return

    _call(client.apps_manifest_update, app_id=app_id, manifest=manifest)
    print(json.dumps({"ok": True, "app_id": app_id, "before": before, "after": after,
                      "backup": str(bp)}, indent=2))
    print(reinstall_hint(app_id), file=sys.stderr)


def cmd_add(args):
    _mutate(args, adding=True)


def cmd_remove(args):
    _mutate(args, adding=False)


def cmd_revert(args):
    client = config_client()
    app_id = resolve_app_id(args)
    bp = Path(args.backup) if args.backup else backup_path(app_id)
    if not bp.exists():
        print(f"Error: no backup at {bp}. Nothing to revert to.", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    saved = json.loads(bp.read_text())
    target = saved.get("scopes") or {}
    manifest = export_manifest(client, app_id)
    current = get_scopes(manifest)
    set_scopes(manifest, target.get("bot", []), target.get("user", []))

    if args.dry_run:
        print(json.dumps({"ok": True, "dry_run": True, "app_id": app_id,
                          "current": current, "revert_to": target,
                          "backup_saved_at": saved.get("saved_at")}, indent=2))
        return

    _call(client.apps_manifest_update, app_id=app_id, manifest=manifest)
    print(json.dumps({"ok": True, "app_id": app_id, "reverted_from": current,
                      "reverted_to": target, "backup_saved_at": saved.get("saved_at")}, indent=2))


def cmd_rotate(_args):
    refresh = _resolve("SLACK_CONFIG_REFRESH_TOKEN")
    if not refresh:
        print("Error: set $SLACK_CONFIG_REFRESH_TOKEN (xoxe-…) to rotate.", file=sys.stderr)
        sys.exit(EXIT_AUTH)
    resp = _call(WebClient().tooling_tokens_rotate, refresh_token=refresh)
    print(json.dumps({"ok": True, "token": resp.get("token"),
                      "refresh_token": resp.get("refresh_token"),
                      "exp": resp.get("exp")}, indent=2))
    print("Store the new token as $SLACK_CONFIG_TOKEN and the new refresh_token as "
          "$SLACK_CONFIG_REFRESH_TOKEN — the old pair is now invalid.", file=sys.stderr)


# ---------------------------------------------------------------------------
def build_parser():
    p = argparse.ArgumentParser(prog="scope_manager",
                                description="Manage a Slack app's manifest OAuth scopes (config token)")
    sub = p.add_subparsers(dest="command", required=True)

    st = sub.add_parser("status", help="Show configured scopes + live-token delta (reinstall pending?)")
    st.add_argument("--app-id")
    st.set_defaults(func=cmd_status)

    for name, fn, verb in (("add", cmd_add, "add"), ("remove", cmd_remove, "remove")):
        sp = sub.add_parser(name, help=f"{verb.capitalize()} scopes in the manifest (auto-backs up first)")
        sp.add_argument("--user", nargs="+", metavar="SCOPE", help="User-token scopes")
        sp.add_argument("--bot", nargs="+", metavar="SCOPE", help="Bot-token scopes")
        sp.add_argument("--app-id")
        sp.add_argument("--dry-run", action="store_true", help="Show the change without writing")
        sp.set_defaults(func=fn)

    rv = sub.add_parser("revert", help="Restore scopes from the auto-backup (undo add/remove)")
    rv.add_argument("--app-id")
    rv.add_argument("--backup", help="Backup file (default ~/.slack-toolkit/scope-backup-<app_id>.json)")
    rv.add_argument("--dry-run", action="store_true", help="Show what would be restored")
    rv.set_defaults(func=cmd_revert)

    ro = sub.add_parser("rotate", help="Rotate the config token via tooling.tokens.rotate")
    ro.set_defaults(func=cmd_rotate)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
