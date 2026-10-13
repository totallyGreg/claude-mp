#!/usr/bin/env bash
set -euo pipefail

# Finder Surface — put a command-line script behind a Finder droplet or a Folder Action.
# The script receives file paths as arguments; it must not need a terminal.
#
#   finder_surface.sh droplet <Name.app> <script>        # drop files on the app icon
#   finder_surface.sh folder-action <folder> <script>    # files added to the folder
#   finder_surface.sh detach <folder>                    # remove that folder's actions
#
# AppleScript's `do shell script` runs /bin/sh with PATH=/usr/bin:/bin:/usr/sbin:/sbin
# and no login profile — use absolute paths inside <script>.

FA_DIR="$HOME/Library/Scripts/Folder Action Scripts"

usage() { sed -n '4,12p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }

abs() { (cd "$(dirname "$1")" && printf '%s/%s' "$PWD" "$(basename "$1")"); }

# AppleScript string literal: escape backslashes and double quotes.
as_string() { local s=${1//\\/\\\\}; printf '"%s"' "${s//\"/\\\"}"; }

# Handler body shared by both surfaces: run the script once with every item as an argument.
run_body() {
  local items=$1 label=$2
  cat <<EOF
	set cmd to quoted form of $(as_string "$script")
	repeat with f in $items
		set cmd to cmd & " " & quoted form of POSIX path of f
	end repeat
	try
		do shell script cmd
		display notification ((count of $items) as text) & " item(s) processed" with title $(as_string "$label")
	on error errMsg
		display notification errMsg with title $(as_string "$label failed")
	end try
EOF
}

need_script() {
  [[ -x "$1" ]] || { echo "not an executable file: $1" >&2; exit 1; }
  script=$(abs "$1")
}

cmd=${1:-}; shift || true
case "$cmd" in
  droplet)
    [[ $# -eq 2 ]] || usage
    app=$1; need_script "$2"
    [[ "$app" == *.app ]] || app="$app.app"
    name=$(basename "$app" .app)
    src=$(mktemp -t droplet).applescript
    {
      echo "on open droppedItems"; run_body droppedItems "$name"; echo "end open"
      echo "on run"
      echo "	display dialog $(as_string "Drop files on the $name icon.") buttons {\"OK\"} default button 1"
      echo "end run"
    } > "$src"
    osacompile -o "$app" "$src"; rm -f "$src"
    echo "droplet: $app → $script"
    ;;
  folder-action)
    [[ $# -eq 2 ]] || usage
    [[ -d "$1" ]] || { echo "not a folder: $1" >&2; exit 1; }
    folder=$(cd "$1" && pwd); need_script "$2"
    name="$(basename "$folder")-$(basename "$script").scpt"
    mkdir -p "$FA_DIR"
    src=$(mktemp -t folderaction).applescript
    {
      echo "on adding folder items to thisFolder after receiving addedItems"
      run_body addedItems "$(basename "$script")"
      echo "end adding folder items to"
    } > "$src"
    osacompile -o "$FA_DIR/$name" "$src"; rm -f "$src"
    osascript - "$folder" "$name" <<'EOF'
on run {folderPath, scriptName}
	tell application "System Events"
		set folder actions enabled to true
		if exists (folder action 1 whose path is folderPath) then
			set fa to folder action 1 whose path is folderPath
		else
			set fa to make new folder action at end of folder actions with properties {path:folderPath}
		end if
		if not (exists (script 1 of fa whose name is scriptName)) then
			tell fa to make new script at end of scripts with properties {name:scriptName}
		end if
	end tell
end run
EOF
    echo "folder action: $folder → $script (script: $FA_DIR/$name)"
    ;;
  detach)
    [[ $# -eq 1 ]] || usage
    folder=$(cd "$1" && pwd)
    names=$(osascript - "$folder" <<'EOF'
on run {folderPath}
	set out to {}
	tell application "System Events"
		-- a `whose` list re-evaluates after each delete, so take the first match until none is left
		repeat while (exists (folder action 1 whose path is folderPath))
			set fa to folder action 1 whose path is folderPath
			set out to out & (name of every script of fa)
			delete fa
		end repeat
	end tell
	set AppleScript's text item delimiters to linefeed
	return out as text
end run
EOF
)
    while IFS= read -r n; do
      [[ -n "$n" ]] && rm -f "$FA_DIR/$n" && echo "removed: $FA_DIR/$n"
    done <<< "$names"
    echo "detached: $folder (Folder Actions stay enabled for other folders)"
    ;;
  *) usage ;;
esac
