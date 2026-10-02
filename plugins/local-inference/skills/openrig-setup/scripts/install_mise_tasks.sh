#!/bin/zsh
# install_mise_tasks.sh [--check] — copy this skill's openrig mise file tasks into the
# global mise tasks directory, so `mise run openrig:new|check|convert` works in every
# project.
#
# Target: ${MISE_CONFIG_DIR:-${XDG_CONFIG_HOME:-~/.config}/mise}/tasks/openrig. Files are
# copied, not linked: the plugin cache path changes with every plugin version.
#
# Per file: missing → copied; identical → left alone; different → diff shown, the
# installed copy saved as <name>.bak, then replaced. --check reports without changing
# anything. Run it again after the plugin updates.
set -u
check=0
[[ ${1:-} == --check ]] && check=1
src=${0:A:h:h}/mise-tasks/openrig
dest=${MISE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/mise}/tasks/openrig
(( check )) || mkdir -p "$dest"

changed=0
for f in $src/*; do
  name=${f:t} target=$dest/${f:t}
  if [[ ! -e $target ]]; then
    print "new        $name"
    (( check )) || cp -p "$f" "$target"
    changed=1
  elif cmp -s "$f" "$target"; then
    print "up to date $name"
  else
    print "changed    $name"
    diff -u "$target" "$f" | sed 's/^/    /'
    if (( ! check )); then
      # Not executable, or mise would list the backup as a task.
      cp -p "$target" "$target.bak" && chmod -x "$target.bak" && cp -p "$f" "$target"
      print "    (previous copy saved as $name.bak)"
    fi
    changed=1
  fi
done

(( check )) && { print "\n(check only — nothing changed; target $dest)"; exit $changed; }
(( changed )) && print "\nInstalled into $dest. List them with: mise tasks --global | grep openrig"
exit 0
