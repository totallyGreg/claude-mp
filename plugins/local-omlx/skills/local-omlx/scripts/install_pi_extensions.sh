#!/bin/zsh
# install_pi_extensions.sh [--check] — copy this skill's Pi extensions into Pi's own
# extensions directory, where Pi discovers them by itself.
#
# Target: ${PI_CODING_AGENT_DIR:-~/.pi/agent}/extensions. Pi does not follow XDG; to keep
# Pi's config under $XDG_CONFIG_HOME, set PI_CODING_AGENT_DIR=$XDG_CONFIG_HOME/pi/agent
# and this script follows it.
#
# Per file: missing → copied; identical → left alone; different → diff shown, the
# installed copy saved as <name>.ts.bak, then replaced. --check reports without changing
# anything. Updates are deliberate: run this after the plugin updates, then /reload in
# open Pi sessions.
set -u
check=0
[[ ${1:-} == --check ]] && check=1
src=${0:A:h:h}/assets/pi-extensions
agent=${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}
agent=${~agent}
dest=$agent/extensions
(( check )) || mkdir -p "$dest"

changed=0
for f in $src/*.ts; do
  name=${f:t} target=$dest/${f:t}
  if [[ ! -e $target ]]; then
    print "new        $name"
    (( check )) || cp "$f" "$target"
    changed=1
  elif cmp -s "$f" "$target"; then
    print "up to date $name"
  else
    print "changed    $name"
    diff -u "$target" "$f" | sed 's/^/    /'
    if (( ! check )); then
      cp "$target" "$target.bak" && cp "$f" "$target"
      print "    (previous copy saved as $name.bak)"
    fi
    changed=1
  fi
done

# The plugin's 1.0.0 setup pointed Pi's `extensions` setting at the marketplace copy;
# with the files installed here too, Pi would load every extension twice.
settings=$agent/settings.json
if [[ -f $settings ]] && grep -q 'local-omlx/pi/extensions' "$settings"; then
  print "\nwarning: $settings still lists the old local-omlx/pi/extensions path under"
  print "\"extensions\" — remove that entry, or Pi loads these extensions twice."
fi

(( check )) && { print "\n(check only — nothing changed; target $dest)"; exit $changed; }
(( changed )) && print "\nInstalled into $dest. Run /reload in any open Pi session."
exit 0
