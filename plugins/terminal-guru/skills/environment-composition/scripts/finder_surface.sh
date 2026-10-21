#!/usr/bin/env bash
set -euo pipefail

# Finder Surface — put a command-line script behind a Finder droplet or a Folder Action.
# The script receives file paths as arguments; it must not need a terminal.
#
#   finder_surface.sh droplet [--link] [--self-reporting] <Name.app> <script>
#                                                        # drop files on the app icon
#   finder_surface.sh folder-action <folder> <script>    # files added to the folder
#   finder_surface.sh detach <folder>                    # remove that folder's actions
#
# droplet: the script is copied into the app (re-run to update it; --link runs it
# from its path instead). The app shows a progress window with a Stop button
# (SIGTERM); a script that writes "<percent or -1>\t<phase>\t<detail>" lines to
# $DROPLET_PROGRESS_FILE gets a real bar. Exit 0 = done (notification), 3 = the
# script already showed the outcome, other = failure dialog with stderr's last line.
# --self-reporting: the script reports its own success, and failure dialogs omit
# stderr. Double-clicking the app toggles a Finder Quick Action for the same script.
#
# AppleScript's `do shell script` runs /bin/sh with PATH=/usr/bin:/bin:/usr/sbin:/sbin
# and no login profile — use absolute paths inside <script>.

FA_DIR="$HOME/Library/Scripts/Folder Action Scripts"

usage() { sed -n '4,21p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }

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

# Droplet applet: runs the script in the background, shows its progress, handles
# Stop, reports by exit status; double-click toggles the Quick Action.
droplet_source() {
  local name=$1 ref=$2 embedded=$3 self=$4
  cat <<EOF
property appName : $(as_string "$name")
property scriptRef : $(as_string "$ref") -- resource name when embedded, else absolute path
property embedded : $embedded
property selfReporting : $self

on open droppedItems
	if embedded then
		set scriptPath to POSIX path of (path to resource scriptRef)
	else
		set scriptPath to scriptRef
	end if
	set args to ""
	repeat with f in droppedItems
		set args to args & " " & quoted form of POSIX path of f
	end repeat
	set work to do shell script "mktemp -d \"\${TMPDIR:-/tmp}/droplet.XXXXXX\""
	set progressFile to work & "/progress"
	set exitFile to work & "/exit"
	set errFile to work & "/stderr"
	-- Background run; the subshell records the exit status.
	set runner to do shell script "(DROPLET_PROGRESS_FILE=" & quoted form of progressFile & " " & quoted form of scriptPath & args & " >/dev/null 2>" & quoted form of errFile & "; echo \$? > " & quoted form of exitFile & ") >/dev/null 2>&1 & echo \$!"
	set progress description to appName
	set progress additional description to "Working…"
	set progress total steps to -1
	set exitCode to ""
	set stopping to false
	repeat while exitCode is ""
		try
			delay 0.5
			if not stopping then my showProgress(my firstLine(progressFile))
			set exitCode to my firstLine(exitFile)
		on error number -128 -- Stop button
			if not stopping then
				set stopping to true
				set progress total steps to -1
				set progress description to "Stopping…"
				set progress additional description to ""
				-- TERM the script and its children (so a long copy or open dialog ends now).
				do shell script "s=\$(pgrep -P " & runner & "); [ -n \"\$s\" ] && { pkill -TERM -P \$s; kill -TERM \$s; }; true"
			end if
		end try
	end repeat
	set lastErr to do shell script "tail -n 1 " & quoted form of errFile & " 2>/dev/null || true"
	do shell script "rm -f " & quoted form of progressFile & " " & quoted form of exitFile & " " & quoted form of errFile & "; rmdir " & quoted form of work
	if exitCode is "0" then
		if not selfReporting then display notification "Finished " & (count of droppedItems) & " item(s)." with title appName
	else if exitCode is not "3" then
		set msg to appName & " failed (exit " & exitCode & ")."
		if selfReporting then
			set msg to msg & " Run the script in Terminal to see details."
		else if lastErr is not "" then
			set msg to msg & return & return & lastErr
		end if
		display dialog msg with title appName buttons {"OK"} default button 1 with icon stop
	end if
end open

-- Double-click: settings window with the Quick Action toggle.
on run
	set qa to POSIX path of (path to home folder) & "Library/Services/" & appName & ".workflow"
	repeat
		set isOn to (do shell script "test -d " & quoted form of qa & " && echo yes || echo no") is "yes"
		if isOn then
			set {state, toggle} to {"On", "Turn Off"}
		else
			set {state, toggle} to {"Off", "Turn On"}
		end if
		set answer to button returned of (display dialog appName & return & return & "Drop files or folders on this icon to run it." & return & return & "Finder right-click menu (Quick Actions ▸ " & appName & "): " & state buttons {toggle, "Done"} default button "Done" with title appName)
		if answer is "Done" then exit repeat
		if isOn then
			do shell script "rm -r " & quoted form of qa & "; /System/Library/CoreServices/pbs -flush"
		else
			set template to POSIX path of (path to resource "QuickAction.workflow")
			set cmd to "open -a " & quoted form of (POSIX path of (path to me)) & " \"\$@\""
			do shell script "mkdir -p ~/Library/Services && ditto " & quoted form of template & " " & quoted form of qa & " && plutil -replace actions.0.action.ActionParameters.COMMAND_STRING -string " & quoted form of cmd & " " & quoted form of (qa & "/Contents/document.wflow") & " && /System/Library/CoreServices/pbs -flush"
		end if
	end repeat
end run

on firstLine(p)
	try
		return paragraph 1 of (read (POSIX file p) as «class utf8»)
	on error
		return ""
	end try
end firstLine

-- "<percent or -1><tab><phase><tab><detail>" from the script
on showProgress(ln)
	if ln is "" then return
	set AppleScript's text item delimiters to tab
	set parts to text items of ln
	set AppleScript's text item delimiters to ""
	if (count of parts) < 3 then return
	set pct to (item 1 of parts) as integer
	if pct < 0 then
		set progress total steps to -1
	else
		set progress total steps to 100
		set progress completed steps to pct
	end if
	set progress description to item 2 of parts
	set progress additional description to item 3 of parts
end showProgress
EOF
}

# Quick Action template (Finder, files as arguments). The app fills in
# COMMAND_STRING with its own path when the toggle installs it.
quick_action_template() {
  local dir=$1 name=$2 xname
  xname=$(printf '%s' "$name" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')
  mkdir -p "$dir/Contents"
  cat > "$dir/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
	<key>NSServices</key><array><dict>
		<key>NSMenuItem</key><dict><key>default</key><string>$xname</string></dict>
		<key>NSMessage</key><string>runWorkflowAsService</string>
		<key>NSRequiredContext</key><dict><key>NSApplicationIdentifier</key><string>com.apple.finder</string></dict>
		<key>NSSendFileTypes</key><array><string>public.item</string></array>
	</dict></array>
</dict></plist>
EOF
  cat > "$dir/Contents/document.wflow" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
	<key>AMApplicationBuild</key><string>534</string>
	<key>AMApplicationVersion</key><string>2.10</string>
	<key>AMDocumentVersion</key><string>2</string>
	<key>actions</key><array><dict>
		<key>action</key><dict>
			<key>AMAccepts</key><dict><key>Container</key><string>List</string><key>Optional</key><true/><key>Types</key><array><string>com.apple.cocoa.string</string></array></dict>
			<key>AMActionVersion</key><string>2.0.3</string>
			<key>AMApplication</key><array><string>Automator</string></array>
			<key>AMParameterProperties</key><dict><key>COMMAND_STRING</key><dict/><key>CheckedForUserDefaultShell</key><dict/><key>inputMethod</key><dict/><key>shell</key><dict/><key>source</key><dict/></dict>
			<key>AMProvides</key><dict><key>Container</key><string>List</string><key>Types</key><array><string>com.apple.cocoa.string</string></array></dict>
			<key>ActionBundlePath</key><string>/System/Library/Automator/Run Shell Script.action</string>
			<key>ActionName</key><string>Run Shell Script</string>
			<key>ActionParameters</key><dict>
				<key>COMMAND_STRING</key><string>true</string>
				<key>CheckedForUserDefaultShell</key><true/>
				<key>inputMethod</key><integer>1</integer>
				<key>shell</key><string>/bin/bash</string>
				<key>source</key><string></string>
			</dict>
			<key>BundleIdentifier</key><string>com.apple.RunShellScript</string>
			<key>CFBundleVersion</key><string>2.0.3</string>
			<key>CanShowSelectedItemsWhenRun</key><false/>
			<key>CanShowWhenRun</key><true/>
			<key>Category</key><array><string>AMCategoryUtilities</string></array>
			<key>Class Name</key><string>RunShellScriptAction</string>
			<key>InputUUID</key><string>$(uuidgen)</string>
			<key>Keywords</key><array><string>Shell</string><string>Script</string><string>Command</string><string>Run</string><string>Unix</string></array>
			<key>OutputUUID</key><string>$(uuidgen)</string>
			<key>UUID</key><string>$(uuidgen)</string>
			<key>UnlocalizedApplications</key><array><string>Automator</string></array>
			<key>arguments</key><dict>
				<key>0</key><dict><key>default value</key><integer>0</integer><key>name</key><string>inputMethod</string><key>required</key><string>0</string><key>type</key><string>0</string><key>uuid</key><string>0</string></dict>
				<key>1</key><dict><key>default value</key><false/><key>name</key><string>CheckedForUserDefaultShell</string><key>required</key><string>0</string><key>type</key><string>0</string><key>uuid</key><string>1</string></dict>
				<key>2</key><dict><key>default value</key><string></string><key>name</key><string>source</string><key>required</key><string>0</string><key>type</key><string>0</string><key>uuid</key><string>2</string></dict>
				<key>3</key><dict><key>default value</key><string></string><key>name</key><string>COMMAND_STRING</string><key>required</key><string>0</string><key>type</key><string>0</string><key>uuid</key><string>3</string></dict>
				<key>4</key><dict><key>default value</key><string>/bin/sh</string><key>name</key><string>shell</string><key>required</key><string>0</string><key>type</key><string>0</string><key>uuid</key><string>4</string></dict>
			</dict>
			<key>conversionLabel</key><integer>0</integer>
			<key>isViewVisible</key><integer>1</integer>
			<key>location</key><string>309.000000:305.000000</string>
			<key>nibPath</key><string>/System/Library/Automator/Run Shell Script.action/Contents/Resources/Base.lproj/main.nib</string>
		</dict>
		<key>isViewVisible</key><integer>1</integer>
	</dict></array>
	<key>connectors</key><dict/>
	<key>workflowMetaData</key><dict>
		<key>applicationBundleIDsByPath</key><dict/>
		<key>applicationPaths</key><array/>
		<key>inputTypeIdentifier</key><string>com.apple.Automator.fileSystemObject</string>
		<key>outputTypeIdentifier</key><string>com.apple.Automator.nothing</string>
		<key>presentationMode</key><integer>15</integer>
		<key>processesInput</key><false/>
		<key>serviceApplicationBundleID</key><string>com.apple.finder</string>
		<key>serviceInputTypeIdentifier</key><string>com.apple.Automator.fileSystemObject</string>
		<key>serviceOutputTypeIdentifier</key><string>com.apple.Automator.nothing</string>
		<key>serviceProcessesInput</key><false/>
		<key>systemImageName</key><string>NSActionTemplate</string>
		<key>useAutomaticInputType</key><false/>
		<key>workflowTypeIdentifier</key><string>com.apple.Automator.servicesMenu</string>
	</dict>
</dict></plist>
EOF
  plutil -lint -s "$dir/Contents/Info.plist" "$dir/Contents/document.wflow"
}

need_script() {
  [[ -x "$1" ]] || { echo "not an executable file: $1" >&2; exit 1; }
  script=$(abs "$1")
}

cmd=${1:-}; shift || true
case "$cmd" in
  droplet)
    embedded=true self=false
    while [[ ${1:-} == --* ]]; do
      case $1 in
        --link) embedded=false ;;
        --self-reporting) self=true ;;
        *) usage ;;
      esac
      shift
    done
    [[ $# -eq 2 ]] || usage
    app=$1; need_script "$2"
    [[ "$app" == *.app ]] || app="$app.app"
    name=$(basename "$app" .app)
    if [[ -e "$app" && ! -f "$app/Contents/Resources/Scripts/main.scpt" ]]; then
      echo "exists and is not an AppleScript app, not replacing: $app" >&2; exit 1
    fi
    ref=$script; $embedded && ref=$(basename "$script")
    build=$(mktemp -d -t droplet)
    droplet_source "$name" "$ref" "$embedded" "$self" > "$build/main.applescript"
    osacompile -o "$build/$name.app" "$build/main.applescript" 2>"$build/osacompile.err" \
      || { cat "$build/osacompile.err" >&2; exit 1; }   # quiet unless it fails (it chats about signing)
    res="$build/$name.app/Contents/Resources"
    $embedded && cp -p "$script" "$res/$ref"
    quick_action_template "$res/QuickAction.workflow" "$name"
    codesign -f -s - "$build/$name.app" 2>/dev/null   # resources changed after osacompile signed it
    [[ -e "$app" ]] && rm -r "$app"
    mv "$build/$name.app" "$app"; rm -r "$build"
    if $embedded; then echo "droplet: $app (embedded copy of $script)"; else echo "droplet: $app → $script"; fi
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
