# Scope Management (advanced)

`scripts/scope_manager.py` is a **standalone** helper for changing the Slack app's OAuth scopes
via its manifest, with automatic backup and one-command revert. It is intentionally separate
from `slacker.py` because it uses a different, more powerful credential and can rewrite the
app's own configuration.

> **What it cannot do:** editing the manifest only changes what the app *requests*. The
> installed token keeps its old scopes until the app is **reinstalled** through the browser
> OAuth consent screen — a step that requires user (and possibly admin) approval and cannot be
> done headlessly. The helper prints where to reinstall and gives you a clean `revert` for when
> approval is not available.

## Credentials

Unlike the rest of the toolkit (which uses `$SLACK_USER_TOKEN`), scope management needs an
**app configuration token** (`xoxe.xoxp-…`). Resolution is env var first, then `keychainctl`.

| Variable | Purpose |
|----------|---------|
| `SLACK_CONFIG_TOKEN` | Config **access** token (`xoxe.xoxp-…`) — required for status/add/remove/revert |
| `SLACK_CONFIG_REFRESH_TOKEN` | Config **refresh** token (`xoxe-…`) — required for `rotate` |
| `SLACK_APP_ID` | Default app ID (or pass `--app-id A0123ABCD`) |
| `SLACK_USER_TOKEN` | Optional — lets `status` compute the installed-vs-configured delta |

Generate config tokens at `https://api.slack.com/apps` → your app → App Manifest / configuration
tokens. They are short-lived (~12h) and self-rotating — refresh with `rotate` (below).

## Commands

```bash
# See configured scopes and whether a reinstall is pending (needs SLACK_USER_TOKEN too)
uv run scope_manager.py status --app-id A0123

# Add scopes (backs up current scopes first, then updates the manifest)
uv run scope_manager.py add --user search:read im:read --bot chat:write --app-id A0123
uv run scope_manager.py add --user search:read --dry-run     # preview only, no write

# Remove scopes (also auto-backs up)
uv run scope_manager.py remove --user im:read --app-id A0123

# Undo the last add/remove using the auto-backup
uv run scope_manager.py revert --app-id A0123
uv run scope_manager.py revert --app-id A0123 --dry-run

# Rotate an expired config token (prints a new access + refresh pair)
uv run scope_manager.py rotate
```

## The safe add → reinstall → revert loop

1. `add --user <scopes>` — the helper writes `~/.slack-toolkit/scope-backup-<app_id>.json`
   (the *prior* scopes) **before** updating the manifest.
2. Reinstall in the browser: `https://api.slack.com/apps/<app_id>` → Install App → Reinstall.
3. `slacker.py auth-check` — confirms the new scopes reached your token.
4. **If the reinstall is blocked** (e.g. "requires admin approval" and you can't get it):
   run `scope_manager.py revert --app-id <app_id>`. The manifest returns to the backed-up
   scopes, so the app is not left requesting scopes it cannot be granted.

`status` reports `reinstall_pending_user_scopes` — configured scopes not yet present in the
installed token. A non-empty list means step 2 has not completed (or was approval-blocked).

## Backups

- One backup file per app: `~/.slack-toolkit/scope-backup-<app_id>.json`, holding the scopes
  captured **before** the most recent mutating change, plus a timestamp.
- `revert` restores **only** `oauth_config.scopes` onto the current manifest, preserving any
  other manifest changes made in between.
- Each `add`/`remove` overwrites the backup with the pre-change state, so `revert` always undoes
  the most recent mutation. Keep your own copy if you need a longer history.

## Notes & limits

- **No per-scope approval preflight.** Whether a scope needs admin approval is a workspace/Grid
  policy applied at the app level and is not queryable per scope. Discover it reactively at
  reinstall, then `revert` if blocked. Org admins can inspect requests via `admin.apps.requests.list`.
- Tokens are never echoed except by `rotate` (which must return the new pair) — store them
  immediately; the old pair is invalidated on rotation.
