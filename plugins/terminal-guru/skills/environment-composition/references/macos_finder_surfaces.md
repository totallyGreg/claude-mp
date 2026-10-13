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
| Idempotent; reports failure on stderr with a non-zero exit | The generated wrapper turns a failure into a notification |

## Choosing a Surface

| Surface | Trigger | Best for | Verified here |
|---------|---------|----------|---------------|
| **Droplet** (`.app`) | Drag files onto the icon (Dock, Desktop, sidebar) | On-demand batches the user picks | yes |
| **Folder Action** | A file lands in a folder | Hands-off inbox: scans, downloads, screenshots | yes |
| **Quick Action** | Finder right-click → Quick Actions, or Services | On-demand without a visible app | no |
| **launchd `WatchPaths`** | Path changes, no login session needed in Finder | Headless, survives Finder being quit | no |
| **fswatch / entr** | Terminal-run watcher | Dev loops while a terminal is open — see signals-monitoring | — |

Graduation: a script run by hand on files 3+ times → droplet. Same script run
on every new file in one place → Folder Action.

## Generator Script

`scripts/finder_surface.sh` builds both verified surfaces from any executable:

```bash
S=${CLAUDE_PLUGIN_ROOT}/skills/environment-composition/scripts/finder_surface.sh
$S droplet ~/Applications/"Receipt to JSON.app" ~/bin/receipt2json   # drop files on the app
$S folder-action ~/Receipts ~/bin/receipt2json                        # files added to ~/Receipts
$S detach ~/Receipts                                                  # remove that folder's actions
```

Each wrapper passes all items to the script in one call, posts a notification
with the item count, and posts the error text instead when the script fails.
Re-running `folder-action` on the same folder is a no-op; `detach` removes the
folder's actions and their `.scpt` files but leaves Folder Actions enabled
globally. Test a droplet without Finder: `open -a "Receipt to JSON.app" file.png`
sends the same open event a drop does.

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

## Quick Action (unverified here)

Automator → New → Quick Action: "Workflow receives current *files or folders*
in *Finder*", add **Run Shell Script** with "Pass input: as arguments", body
`/Users/me/bin/receipt2json "$@"`. Saved to `~/Library/Services/`; appears
under right-click → Quick Actions. Shortcuts can do the same: enable "Use as
Quick Action" → Finder, receive Files, then a **Run Shell Script** action with
input as arguments.

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
