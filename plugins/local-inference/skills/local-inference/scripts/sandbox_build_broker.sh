#!/bin/zsh
# sandbox_build_broker.sh — builds a sandboxed agent asks for, run outside the sandbox.
# Harness- and toolchain-agnostic: any agent that can run a shell command in its
# worktree can request; any build command can be named.
#
#   sandbox_build_broker.sh start --dir <worktree> --cmd <name>=<command> [--cmd ...]
#                           [--preset <ecosystem>]... [--guard <glob>]... [--base <ref>]
#                                                        orchestrator, outside
#   sandbox_build_broker.sh request <name>               the agent, inside the sandbox
#   sandbox_build_broker.sh status|stop --dir <worktree>
#
# Why: some builds can't run in the sandbox (xcodebuild needs LaunchServices, which
# also launches apps outside it). The broker runs them and hands back the log, so the
# agent still gets compiler errors in its own loop.
#
# Safe by construction, not by trusting the agent:
#   - Only the named commands the orchestrator gave at start; a request is a name.
#   - Each request builds a snapshot of the agent's tree (commits, edits and new files)
#     in a detached worktree only the broker can write — nothing changes between the
#     check and the build. Paths in the log are rewritten to the agent's worktree.
#   - A build runs project code — build scripts, plugins, macros — which the agent
#     could edit to run code out here. So the broker refuses when the snapshot differs
#     from where the branch left --base (default main) in a build-defining file, by the
#     guards of each --preset plus --guard globs. A glob without "/" matches that file
#     name anywhere, as in .gitignore. Swift and Rust also refuse changed macro code
#     (a compiler plugin runs during the build), found by content.
#   - Without --preset or --guard it detects the ecosystems from the tree, and refuses
#     to start when it recognises none: unknown build files can't be guarded.
#   - It never runs tests: a test runs code the agent wrote. Name builds only.
#
# Presets: swift xcode node rust python gradle cmake make. Always guarded: mise and
# asdf config, Scripts/ and scripts/, .githooks/, .envrc, justfile, Taskfile.
set -u
cmd=${1:-}; shift 2>/dev/null
SELF=${0:A}
HOME_DIR=${SANDBOX_BROKER_HOME:-$HOME/Library/Application Support/sandbox-build-broker}

typeset -A PRESET
PRESET[base]='mise.toml .mise.toml mise/* .tool-versions Scripts/* scripts/* .githooks/* .envrc justfile Justfile Taskfile.yml Taskfile.yaml'
PRESET[swift]='Package.swift Package@swift-*.swift Package.resolved Plugins/* .swiftpm/*'
PRESET[xcode]='*.xcodeproj/* *.xcworkspace/* *.xcconfig .xcode-version'
PRESET[node]='package.json package-lock.json npm-shrinkwrap.json yarn.lock pnpm-lock.yaml pnpm-workspace.yaml bun.lockb .npmrc .yarnrc .yarnrc.yml .pnpmfile.cjs *.config.js *.config.cjs *.config.mjs *.config.ts .babelrc .babelrc.js gulpfile.* Gruntfile.*'
PRESET[rust]='Cargo.toml Cargo.lock build.rs .cargo/* rust-toolchain rust-toolchain.toml'
PRESET[python]='setup.py setup.cfg pyproject.toml Pipfile Pipfile.lock poetry.lock uv.lock requirements*.txt noxfile.py tox.ini hatch_build.py MANIFEST.in'
PRESET[gradle]='*.gradle *.gradle.kts gradle/* gradlew gradlew.bat gradle.properties buildSrc/*'
PRESET[cmake]='CMakeLists.txt *.cmake CMakePresets.json CMakeUserPresets.json'
PRESET[make]='Makefile makefile GNUmakefile *.mk'

die() { print -u2 "sandbox_build_broker: $*"; exit 2 }
key_for() { print -rn -- "$1" | shasum | cut -c1-12 }

# The ecosystems a tree's build files say it uses.
detect() {
  local d=$1 found=()
  setopt local_options null_glob
  [[ -f $d/Package.swift ]] && found+=(swift)
  [[ -n $(print -l $d/*.xcodeproj $d/*.xcworkspace) ]] && found+=(xcode)
  [[ -f $d/package.json ]] && found+=(node)
  [[ -f $d/Cargo.toml ]] && found+=(rust)
  [[ -f $d/pyproject.toml || -f $d/setup.py || -f $d/setup.cfg ]] && found+=(python)
  [[ -n $(print -l $d/*.gradle $d/*.gradle.kts) ]] && found+=(gradle)
  [[ -f $d/CMakeLists.txt ]] && found+=(cmake)
  [[ -f $d/Makefile || -f $d/makefile || -f $d/GNUmakefile ]] && found+=(make)
  print -r -- $found
}

case $cmd in
start)
  dir=$PWD base=main cmds=() guards=() presets=()
  while (( $# )); do
    case $1 in
      --dir) dir=$2; shift 2 ;; --base) base=$2; shift 2 ;;
      --cmd) cmds+=("$2"); shift 2 ;; --guard) guards+=("$2"); shift 2 ;;
      --preset) presets+=("$2"); shift 2 ;;
      *) die "unknown option $1" ;;
    esac
  done
  (( $#cmds )) || die "give at least one --cmd <name>=<command>"
  dir=${dir:A}
  if (( ! $#presets && ! $#guards )); then
    presets=($(detect "$dir"))
    (( $#presets )) || die "no build system recognised in $dir — name one with --preset (${(j:, :)${(k)PRESET:#base}}) or list its build files with --guard"
  fi
  for p in $presets; do [[ -n ${PRESET[$p]:-} && $p != base ]] || die "unknown preset '$p' (have: ${(j:, :)${(k)PRESET:#base}})"; done
  guards+=(${=PRESET[base]}); for p in $presets; do guards+=(${=PRESET[$p]}); done
  # Compare with where the branch left $base, so later merges to it aren't the agent's.
  base=$(git -C "$dir" merge-base HEAD "$base" 2>/dev/null) || die "--base: no merge base with HEAD"
  st=$HOME_DIR/$(key_for "$dir")
  [[ -f $st/pid ]] && kill -0 $(<$st/pid) 2>/dev/null && die "a broker already serves $dir (stop it first)"
  mkdir -p "$st" "$dir/.agent-build"
  exclude=$(git -C "$dir" rev-parse --path-format=absolute --git-path info/exclude)
  grep -qx '/.agent-build/' "$exclude" 2>/dev/null || print '/.agent-build/' >> "$exclude"
  { print -r -- "dir=${(q)dir}"; print -r -- "base=${(q)base}"; print -r -- "presets=(${(q)presets[@]})"
    print -r -- "cmds=(${(q)cmds[@]})"; print -r -- "guards=(${(q)guards[@]})"; } > "$st/config"
  [[ -d $st/src ]] || git -C "$dir" worktree add -q --detach "$st/src" HEAD
  nohup zsh "$SELF" serve "$st" >"$st/broker.log" 2>&1 &
  print $! > "$st/pid"
  print "sandbox_build_broker: serving $dir (guards: ${(j:, :)presets:-custom}) — the agent runs: $SELF request <name>   (names: ${(j:, :)${cmds%%=*}})"
  ;;

serve)  # the loop (internal)
  st=$1; source "$st/config"
  req=$dir/.agent-build
  while [[ -d $dir ]]; do
    if [[ -f $req/request ]]; then
      read -r name id < "$req/request"; rm -f "$req/request"
      result() { print -r -- "$id $1" > "$req/result.tmp" && mv "$req/result.tmp" "$req/result" }
      line=${(M)cmds:#$name=*}
      if [[ -z $name || -z $line ]]; then
        print -r -- "refused: no build named '$name' (have: ${(j:, :)${cmds%%=*}})" > "$req/$id.log"; result 2; continue
      fi
      # Snapshot the agent's tree, new files included, without touching its index.
      idx=$(mktemp "$st/index.XXXXXX")
      GIT_INDEX_FILE=$idx git -C "$dir" read-tree HEAD
      GIT_INDEX_FILE=$idx git -C "$dir" add -A
      tree=$(GIT_INDEX_FILE=$idx git -C "$dir" write-tree); rm -f "$idx"
      changed=(${(f)"$(git -C "$dir" diff-tree -r --name-only "$base" "$tree")"})
      hits=()
      for f in $changed; do
        for g in $guards; do
          if [[ $g == */* ]]; then [[ $f == ${~g} ]] && { hits+=($f); break }
          else [[ ${f:t} == ${~g} ]] && { hits+=($f); break }; fi
        done
      done
      # Macros run inside the compiler: changed macro code is build code.
      for f in $changed; do
        case $f in
          *.swift) (( ${presets[(I)swift]} )) && git -C "$dir" cat-file -p "$tree:$f" 2>/dev/null \
                     | grep -qE '^[[:space:]]*import (SwiftSyntaxMacros|SwiftCompilerPlugin)\b' && hits+=("$f (a Swift macro)") ;;
          *.rs) (( ${presets[(I)rust]} )) && git -C "$dir" cat-file -p "$tree:$f" 2>/dev/null \
                     | grep -qE '\bproc_macro\b' && hits+=("$f (a Rust proc-macro)") ;;
        esac
      done
      if (( $#hits )); then
        { print "refused: this tree changes build-defining files, which run outside the sandbox:"
          print -l -- "  "${(u)^hits}; print "Revert them (git checkout $base -- <file>), or ask the orchestrator."; } > "$req/$id.log"
        result 3; continue
      fi
      commit=$(git -C "$dir" -c commit.gpgsign=false -c user.name=sandbox-build-broker -c user.email=broker@localhost \
        commit-tree "$tree" -p HEAD -m "sandbox-build-broker snapshot")
      git -C "$st/src" checkout -q --detach --force "$commit"
      (cd "$st/src" && eval "${line#*=}") > "$req/$id.log" 2>&1
      rc=$?
      sed -i '' "s|${st//|/\\|}/src|$dir|g" "$req/$id.log"   # paths point at the agent's worktree
      result $rc
    fi
    sleep 1
  done
  ;;

request)  # the agent, inside the sandbox
  name=${1:-}; [[ -n $name ]] || die "usage: request <name>"
  dir=${AGENT_SANDBOX_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || print -r -- $PWD)}; req=$dir/.agent-build
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
  die "no result after 30 minutes — is the broker running? (sandbox_build_broker.sh status)"
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
  rm -rf -- "$dir/.agent-build"
  print "stopped the broker for $dir"
  ;;

*) sed -n '2,11p' "$SELF" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
