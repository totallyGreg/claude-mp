#!/bin/zsh
# pi_build_broker.sh — builds a sandboxed Pi can ask for, run outside the sandbox.
#
#   pi_build_broker.sh start --dir <worktree> --cmd <name>=<command> [--cmd ...]
#                            [--base <ref, default main>] [--guard <glob>]...   orchestrator, outside
#   pi_build_broker.sh request <name>                                Pi, inside the sandbox
#   pi_build_broker.sh status --dir <worktree>
#   pi_build_broker.sh stop   --dir <worktree>
#
# Why: some builds can't run in the sandbox (xcodebuild needs LaunchServices, which
# also launches apps outside it). The broker runs them for Pi and hands back the log,
# so Pi still gets compiler errors in its own loop.
#
# Safe by construction, not by trusting Pi:
#   - Only the named commands the orchestrator gave at start; a request is a name.
#   - Each request builds a snapshot of Pi's tree (commits, edits and new files) in a
#     detached worktree only the broker can write — so Pi can't change a file
#     between the check and the build.
#   - A build runs the project's own scripts, which Pi could edit to run code out
#     here. So the broker refuses when the snapshot differs from --base in any build-
#     defining file (--guard globs; defaults below), and never runs tests: a test
#     runs code Pi wrote. Give it builds only.
#
# Default guards: *.xcodeproj/**, *.xcworkspace/**, *.xcconfig, Package.swift,
#   Package.resolved, Plugins/**, mise.toml, .mise.toml, mise/**, Scripts/**,
#   scripts/**, .githooks/**, Makefile, *.mk, .swiftpm/**
set -u
cmd=${1:-}; shift 2>/dev/null
SELF=${0:A}
HOME_DIR=${PI_BROKER_HOME:-$HOME/Library/Application Support/pi-build-broker}
DEFAULT_GUARDS=('*.xcodeproj/*' '*.xcworkspace/*' '*.xcconfig' Package.swift Package.resolved 'Plugins/*'
  mise.toml .mise.toml 'mise/*' 'Scripts/*' 'scripts/*' '.githooks/*' Makefile '*.mk' '.swiftpm/*')

die() { print -u2 "pi_build_broker: $*"; exit 2 }
key_for() { print -rn -- "$1" | shasum | cut -c1-12 }

case $cmd in
start)
  dir=$PWD base=main cmds=() guards=()
  while (( $# )); do
    case $1 in
      --dir) dir=$2; shift 2 ;; --base) base=$2; shift 2 ;;
      --cmd) cmds+=("$2"); shift 2 ;; --guard) guards+=("$2"); shift 2 ;;
      *) die "unknown option $1" ;;
    esac
  done
  (( $#cmds )) || die "give at least one --cmd <name>=<command>"
  (( $#guards )) || guards=($DEFAULT_GUARDS)
  dir=${dir:A}
  # Compare with where Pi's branch left $base, so later merges to it aren't Pi's changes.
  base=$(git -C "$dir" merge-base HEAD "$base" 2>/dev/null) || die "--base: no merge base with HEAD"
  st=$HOME_DIR/$(key_for "$dir")
  [[ -f $st/pid ]] && kill -0 $(<$st/pid) 2>/dev/null && die "a broker already serves $dir (stop it first)"
  mkdir -p "$st" "$dir/.pi-build"
  exclude=$(git -C "$dir" rev-parse --path-format=absolute --git-path info/exclude)
  grep -qx '/.pi-build/' "$exclude" 2>/dev/null || print '/.pi-build/' >> "$exclude"
  { print -r -- "dir=${(q)dir}"; print -r -- "base=${(q)base}"
    print -r -- "cmds=(${(q)cmds[@]})"; print -r -- "guards=(${(q)guards[@]})"; } > "$st/config"
  [[ -d $st/src ]] || git -C "$dir" worktree add -q --detach "$st/src" HEAD
  nohup zsh "$SELF" serve "$st" >"$st/broker.log" 2>&1 &
  print $! > "$st/pid"
  print "pi_build_broker: serving $dir — Pi runs: $SELF request <name>   (names: ${(j:, :)${cmds%%=*}})"
  ;;

serve)  # the loop (internal)
  st=$1; source "$st/config"
  req=$dir/.pi-build
  while [[ -d $dir ]]; do
    if [[ -f $req/request ]]; then
      read -r name id < "$req/request"; rm -f "$req/request"
      result() { print -r -- "$id $1" > "$req/result.tmp" && mv "$req/result.tmp" "$req/result" }
      line=${(M)cmds:#$name=*}
      if [[ -z $name || -z $line ]]; then
        print -r -- "refused: no build named '$name' (have: ${(j:, :)${cmds%%=*}})" > "$req/$id.log"; result 2; continue
      fi
      # Snapshot Pi's tree, new files included, without touching its index.
      idx=$(mktemp "$st/index.XXXXXX")
      GIT_INDEX_FILE=$idx git -C "$dir" read-tree HEAD
      GIT_INDEX_FILE=$idx git -C "$dir" add -A
      tree=$(GIT_INDEX_FILE=$idx git -C "$dir" write-tree); rm -f "$idx"
      changed=(${(f)"$(git -C "$dir" diff-tree -r --name-only "$base" "$tree")"})
      hits=()
      for f in $changed; do for g in $guards; do [[ $f == ${~g} ]] && { hits+=($f); break } done; done
      if (( $#hits )); then
        { print "refused: this tree changes build-defining files, which run outside the sandbox:"
          print -l -- "  "$^hits; print "Revert them (git checkout $base -- <file>), or ask the orchestrator."; } > "$req/$id.log"
        result 3; continue
      fi
      commit=$(git -C "$dir" -c commit.gpgsign=false -c user.name=pi-build-broker -c user.email=broker@localhost \
        commit-tree "$tree" -p HEAD -m "pi-build-broker snapshot")
      git -C "$st/src" checkout -q --detach --force "$commit"
      (cd "$st/src" && eval "${line#*=}") > "$req/$id.log" 2>&1
      rc=$?
      sed -i '' "s|${st//|/\\|}/src|$dir|g" "$req/$id.log"   # paths point at Pi's worktree
      result $rc
    fi
    sleep 1
  done
  ;;

request)  # Pi, inside the sandbox
  name=${1:-}; [[ -n $name ]] || die "usage: request <name>"
  dir=${PI_SANDBOX_DIR:-$PWD}; req=$dir/.pi-build
  [[ -d $req ]] || die "no broker serves $dir (the orchestrator starts one)"
  id=$$$RANDOM
  print -r -- "$name $id" > "$req/request.tmp" && mv "$req/request.tmp" "$req/request"
  for i in {1..1800}; do
    if [[ -f $req/result ]] && read -r rid rc < "$req/result" && [[ $rid == $id ]]; then
      tail -n 200 "$req/$id.log"
      print "— build '$name' exited $rc (full log: $req/$id.log)"
      exit $rc
    fi
    sleep 1
  done
  die "no result after 30 minutes — is the broker running? (pi_build_broker.sh status)"
  ;;

status|stop)
  dir=$PWD; [[ ${1:-} == --dir ]] && dir=$2; dir=${dir:A}
  st=$HOME_DIR/$(key_for "$dir")
  [[ -f $st/config ]] || die "no broker for $dir"
  pid=$(<$st/pid)
  if [[ $cmd == status ]]; then
    kill -0 $pid 2>/dev/null && print "serving $dir (pid $pid)" || print "stopped (pid $pid gone)"
    exit
  fi
  kill $pid 2>/dev/null
  git -C "$dir" worktree remove --force "$st/src" 2>/dev/null
  rm -f -- "$st/config" "$st/pid" "$st/broker.log"; rmdir -- "$st" 2>/dev/null
  rm -rf -- "$dir/.pi-build"
  print "stopped the broker for $dir"
  ;;

*) sed -n '2,8p' "$SELF" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
