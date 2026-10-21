# macOS Finder Surfaces — Droplets, Folder Actions, Quick Actions

Put a command-line script behind something a person does in Finder: drop files
on an icon, drop them into a folder, or right-click them. The script stays the
product; the surface is a thin AppleScript wrapper that hands it file paths.

## The Pattern: Core Script First

```
core script (args = file paths)  →  test by hand  →  wrap in a surface
```

Write and test the script from the terminal before wrapping it. A surface adds
nothing but a trigger, so every bug left in the script turns into a silent
failure that's harder to debug.

**Core-script contract** — what a surface needs:

| Rule | Why |
|------|-----|
| Takes file paths as arguments, many at once | Every surface passes the whole selection in one call |
| Absolute paths for every tool (`/usr/bin/fm`, `/opt/homebrew/bin/jq`) | `do shell script` runs `/bin/sh` with `PATH=/usr/bin:/bin:/usr/sbin:/sbin`, no profile, no mise/direnv |
| No stdin, no TTY, no prompts | Nothing is attached |
| Skips files it doesn't handle (match on extension) | Folders receive everything, including the script's own output |
| Writes output atomically (`out.tmp` → validate → `mv`) | A half-written file in a watched folder triggers the next run |
| Idempotent; reports failure on stderr with a non-zero exit | The generated wrapper turns a failure into a dialog |
| Sets up its own environment (`PATH`, `SSH_AUTH_SOCK`, …) | Finder apps get launchd's environment, not your shell's (see Hurdles) |
| Optional: writes progress to `$DROPLET_PROGRESS_FILE` | The droplet shows a real progress bar instead of "Working…" |
| Optional: exits 3 after showing its own outcome | The wrapper then stays silent (see Exit Contract) |

## Choosing a Surface

| Surface | Trigger | Best for | Verified here |
|---------|---------|----------|---------------|
| **Droplet** (`.app`) | Drag files onto the icon (Dock, Desktop, sidebar) | On-demand batches the user picks | yes |
| **Folder Action** | A file lands in a folder | Hands-off inbox: scans, downloads, screenshots | yes |
| **Quick Action** | Finder right-click → Quick Actions, or Services | On-demand without a visible app | registers and runs; Finder menu to confirm |
| **launchd `WatchPaths`** | Path changes, no login session needed in Finder | Headless, survives Finder being quit | no |
| **fswatch / entr** | Terminal-run watcher | Dev loops while a terminal is open — see signals-monitoring | — |

Graduation: a script run by hand on files 3+ times → droplet. Same script run
on every new file in one place → Folder Action.

## Generator Script

`scripts/finder_surface.sh` builds the verified surfaces from any executable:

```bash
S=${CLAUDE_PLUGIN_ROOT}/skills/environment-composition/scripts/finder_surface.sh
$S droplet ~/Applications/"Receipt to JSON.app" ~/bin/receipt2json   # drop files on the app
$S droplet --link --self-reporting ~/Applications/X.app ~/dev/x.sh    # options: see below
$S folder-action ~/Receipts ~/bin/receipt2json                        # files added to ~/Receipts
$S detach ~/Receipts                                                  # remove that folder's actions
```

**Droplet** (re-run the same command to update an app; it replaces only an
existing AppleScript app):

- **Embedded by default.** The script is copied into `Contents/Resources` and the
  app is re-signed, so it survives moving or deleting the project and raises no
  Documents/Desktop privacy prompt. Re-run the generator after editing the
  script. `--link` runs the script from its path instead (edits apply at once;
  the app breaks if the script moves). An embedded script must be self-contained:
  no sibling files found relative to `$0`.
- **Progress window with Stop.** The script runs in the background; the app shows
  the standard applet progress window ("Working…" by default) and Stop sends
  SIGTERM to the script and its children. See Progress Protocol.
- **Double-click = settings.** A dialog shows "Finder right-click menu: On/Off";
  the toggle installs or removes `~/Library/Services/<Name>.workflow`, a Quick
  Action that runs `open -a <the app> "$@"`, so right-click → Quick Actions →
  *Name* behaves exactly like a drop (same progress window and reporting).
- `--self-reporting`: the script shows its own outcome (see Exit Contract).

Each Folder Action passes all items to the script in one call, posts a
notification with the item count, and posts the error text when the script
fails. Re-running `folder-action` on the same folder is a no-op; `detach`
removes the folder's actions and their `.scpt` files but leaves Folder Actions
enabled globally. Test a droplet without Finder: `open -a "Receipt to JSON.app"
file.png` sends the same open event a drop does (it shows real UI).

### Exit Contract (droplet)

| Exit | Default | `--self-reporting` |
|------|---------|--------------------|
| 0 | Notification "Finished N item(s)." | Silent: the script notified |
| 3 | Silent: the script already showed the outcome | Silent |
| other | Dialog with the exit status and stderr's last line | Dialog with the exit status only (stderr may hold file names) |

A script that reports for itself: success → `display notification`, failure →
`display dialog` (a notification disappears; a failure must stay on screen),
then `exit 3`. Pass the text as an argument so quotes in it can't break the
AppleScript: `osascript -e 'on run argv' -e 'display dialog (item 1 of argv)'
-e 'end run' "$msg"`. Keep file names out of notifications if the files are
private: Notification Center keeps a history and shows them on the lock screen.

### Progress Protocol (droplet)

The app sets `DROPLET_PROGRESS_FILE` and polls it every 0.5 s. The script writes
one line, replaced atomically: `<percent or -1>\t<phase>\t<detail>` (-1 =
indeterminate). Phase is the window's main line, detail the second. Draw a bar
too when stderr is a terminal, so the same script reports in both places
(bash 3.2-safe):

```bash
progress() {  # progress PCT PHASE [DETAIL]
    if [[ -t 2 ]]; then printf '\r\033[K%s%% %s %s' "$1" "$2" "${3:-}" >&2; fi
    if [[ -n ${DROPLET_PROGRESS_FILE:-} ]]; then
        printf '%s\t%s\t%s\n' "$1" "$2" "${3:-}" >"$DROPLET_PROGRESS_FILE.tmp" &&
            mv -f "$DROPLET_PROGRESS_FILE.tmp" "$DROPLET_PROGRESS_FILE"
    fi
}
```

For a long copy, measure progress from the destination (remote: `du -sk` or
`stat -f %z` every few seconds over an existing SSH connection) in a background
loop, and show bytes, rate and time left. Stop must leave nothing half-done:
trap TERM/INT, kill your children (`pkill -TERM -P $$`), remove the partial
output, undo temporary changes (unmount, re-lock), then report what finished.

## Droplet

An AppleScript app with an `on open` handler:

```applescript
on open droppedItems
	set cmd to quoted form of "/Users/me/bin/receipt2json"
	repeat with f in droppedItems
		set cmd to cmd & " " & quoted form of POSIX path of f
	end repeat
	do shell script cmd
end open
on run -- double-clicked instead of dropped
	display dialog "Drop files on this icon." buttons {"OK"} default button 1
end run
```

Build: `osacompile -o "Name.app" droplet.applescript`. Always use
`quoted form of` — filenames with spaces and quotes are normal in Finder.
Replace the icon via Finder's Get Info (paste an image onto the icon well).

## Folder Action

An AppleScript in `~/Library/Scripts/Folder Action Scripts/` with
`on adding folder items to thisFolder after receiving addedItems`, attached to
a folder, with Folder Actions turned on globally:

```applescript
tell application "System Events"
	set folder actions enabled to true                -- global switch, off by default
	set fa to make new folder action at end of folder actions with properties {path:"/Users/me/Receipts"}
	tell fa to make new script at end of scripts with properties {name:"receipt2json.scpt"}
end tell
```

GUI equivalent: right-click the folder → Services → Folder Actions Setup.

Gotchas:
- **Output re-triggers the action.** Writing `x.json` next to `x.png` fires the
  handler again with `x.json`; the core script must skip it (extension
  filter), or write output to a sibling folder.
- **Partial files.** Downloads and slow copies may fire before the file is
  complete (browsers write `.download`/`.crdownload` first). Filter those
  extensions; for large files, wait until the size is stable.
- **Only additions fire** (`adding folder items`); there are also `removing
  folder items`, `opening folder`, `closing folder window`, `moving folder
  window` handlers.
- **In a `whose` loop, deleting re-evaluates the filter** — loop with
  `repeat while exists (folder action 1 whose path is p)` (see the generator).
- **Privacy prompts.** The first run against `~/Desktop`, `~/Documents` or
  `~/Downloads`, or the first System Events call, can raise a macOS
  permission prompt; until approved the action fails silently. Check System
  Settings → Privacy & Security → Files and Folders / Automation.
- Debug by running the core script with the same paths by hand, then
  `osascript` the handler logic; the generator's notification shows the error.

## Quick Action

A `.workflow` bundle in `~/Library/Services/`: `Contents/Info.plist` declares
the service (`NSServices`: menu name, `NSMessage = runWorkflowAsService`,
`NSRequiredContext` → `com.apple.finder`, `NSSendFileTypes = public.item`), and
`Contents/document.wflow` holds one **Run Shell Script** action (`inputMethod`
1 = pass input as arguments). The droplet generator embeds this template
(`quick_action_template` in `finder_surface.sh`) and its toggle fills in
`COMMAND_STRING` with `plutil -replace`. Hand-written bundles register fine.
After adding or removing one, run `/System/Library/CoreServices/pbs -flush` to
refresh the Services menu.

Verified 2026-10-20: a generated bundle shows up in `pbs -dump_pboard`,
`automator -i <file> <bundle>` runs it with the file path (spaces included) as
`$1`. Not yet confirmed: that it appears under Finder right-click → Quick Actions.

GUI alternatives: Automator → New → Quick Action ("Workflow receives current
*files or folders* in *Finder*", **Run Shell Script**, "Pass input: as
arguments"); or Shortcuts with "Use as Quick Action" → Finder.

## launchd `WatchPaths` (unverified here)

For a watcher that doesn't depend on Folder Actions, a LaunchAgent with
`WatchPaths` (fires on any change; the script finds new files itself) or
`QueueDirectories` (fires while the directory is non-empty; the script must
move files out or it loops). Load with `launchctl bootstrap gui/$(id -u)
~/Library/LaunchAgents/<label>.plist`. Declarative alternative:
mise-tooling's `[bootstrap.macos.launchd.agents]`.

## Worked Example — Receipt Image → JSON with Apple's On-Device Model

macOS 27's `/usr/bin/fm` gives any script local inference with a JSON-schema
output, so a surface can wrap a model call like any other command. Flags,
schema dialect and failure modes: local-inference skill,
`references/apple-fm.md`.

```zsh
#!/bin/zsh -f
# receipt2json IMAGE... — write IMAGE.json next to each receipt image.
emulate -L zsh; setopt pipe_fail
schema=${RECEIPT_SCHEMA:-${0:A:h}/receipt.schema.json}
for img in "$@"; do
  [[ $img == *.(png|jpg|jpeg|heic|tiff|PNG|JPG|JPEG|HEIC|TIFF) ]] || continue  # skips its own .json
  out=${img:r}.json
  /usr/bin/fm respond --no-stream --greedy --tool ocr --schema $schema --image $img \
      'Extract this receipt.' > $out.tmp \
    && /usr/bin/jq -e . $out.tmp >/dev/null && mv $out.tmp $out \
    || { rm -f $out.tmp; print -u2 "receipt2json: failed on $img"; exit 1 }
done
```

Then `finder_surface.sh droplet … receipt2json` and/or `folder-action
~/Receipts receipt2json`. Verified 2026-10-13: both surfaces wrote the correct
JSON for a test receipt in ~3 s per image (first OCR call after idle is slower).
Totals the model reads are not checked arithmetic — verify sums with `jq`.

## Hurdles Seen Building a Real Droplet

From building a remote-transfer droplet (drop files → SSH to another Mac → mount
an encrypted disk image → copy, verify, unmount), 2026-10-19/20. Each cost a
debugging round; check them up front.

**Environment**
- Finder apps don't inherit the shell's environment. `SSH_AUTH_SOCK` points at
  macOS's own ssh-agent, not gpg-agent or 1Password; `PATH` lacks Homebrew. Set
  them in the script (`gpgconf --launch gpg-agent`; export the agent socket).
- A cancelled or failed SSH login and an unreachable host need different
  messages: grep stderr for `Permission denied` before blaming the network.

**macOS's `/bin/bash` 3.2** (what `#!/usr/bin/env bash` gets under Finder's PATH)
- `"$name…"` reads the non-ASCII `…` as part of the variable name: with `set -u`
  the script dies on its first status message. Write `${name}…`. Find them:
  `LC_ALL=C grep -nE '\$[A-Za-z_][A-Za-z0-9_]*[^ -~]' script.sh`.
- The EXIT trap's last command sets the exit status: a crash can exit 0 and the
  wrapper shows nothing. Start the trap with `local rc=$?` and end with `exit "$rc"`.
- A trap waits for the foreground child to finish, so Stop during a long `scp`
  does nothing until the copy ends. Run the child with `&` and `wait "$!"`;
  `wait` returns as soon as a trapped signal arrives.
- No associative arrays or `mapfile`; `"${arr[@]}"` on an empty array fails under
  `set -u` (guard with a count check).

**Changing and testing**
- Never overwrite a script that may be running: bash reads it as it goes. Write
  `x.tmp`, then `mv -f x.tmp x` (a running copy keeps the old file).
- Test without pop-ups: put a stub `osascript` first on `PATH` that answers
  `display dialog … default answer` with a test value and logs everything else.
- Terminal progress bars need a TTY. `script(1)` fails without one (sandboxed
  agents, CI); run the script under Python's `pty.openpty()` and capture stderr.
- Some commands open GUI prompts even when scripted: `diskutil image info` on an
  encrypted image asks for its password on the Mac's screen. Prefer commands that
  take secrets on stdin (`diskutil image attach --stdinpass`).
- Tools drift between macOS versions: on 26, `diskutil image attach --mountPoint`
  needs the folder to exist (27 creates it) and fails with a usage error. Prefer
  the current tool and fall back to the deprecated one on any error that isn't a
  wrong password, rather than probing for support with `--help`.

**Remote work over SSH**
- One `ControlMaster` connection for the whole run: `ssh -fNM -o
  ControlPath=<private dir>/ctl`, then every `ssh`/`scp` with the same
  `ControlPath` reuses it (`-v` shows `mux_client_request_session`). Close it with
  `ssh -O exit`.
- Networks may silently drop new SSH connections after a few in a few minutes
  (here: blocked for ~5–10 min; ping still worked). Space test runs out, and
  check the VPN tunnel before assuming a block.
- Secrets go over stdin (`printf '%s' "$pw" | ssh host 'cmd --stdinpass'`), never
  in a command line (`ps` shows it on both machines). Quote every value placed
  in a remote command with `printf %q`.
- `BatchMode=yes` (no prompts; a droplet can't answer), `StrictHostKeyChecking=yes`
  (never `no`: that hands the secret to whoever intercepts the connection),
  `ForwardAgent=no`.
- Finder-locked files (`chflags uchg`, Get Info ▸ Locked) refuse writes; a locked
  disk image mounts read-only. Unlock for the run and re-lock in the cleanup trap.

**Review agent-written scripts.** The first version of this droplet (from a local
model) passed the password in the command line, disabled host-key checking,
staged the plaintext in `/tmp` and had a copy step that could never work. Read the
whole thing and test each step by hand before wrapping it.
