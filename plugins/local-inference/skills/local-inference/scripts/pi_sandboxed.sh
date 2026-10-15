#!/bin/zsh
# pi_sandboxed.sh — run Pi (or any command) with bash under a macOS sandbox
# that confines it to one git worktree branch.
#
#   pi_sandboxed.sh run   [opts] -- <pi args...>    one-shot `pi` under the sandbox
#   pi_sandboxed.sh spawn [opts] [tier] [name]      a sandboxed Pi pane; prints the pane id.
#                                                   Drive it with pi_team.sh ask / close.
#   pi_sandboxed.sh exec  [opts] -- <cmd...>        any command under the same sandbox
#   pi_sandboxed.sh profile [opts]                  print the sandbox profile
#   pi_sandboxed.sh self-test [--live]              prove what is allowed and refused
#
#   opts:  --dir <worktree>   where Pi works (default: $PWD)
#          --write <path>     another writable path, e.g. a build scratch dir; repeatable
#          --port <n>         a localhost port Pi may reach (default: 8000, oMLX); repeatable
#
# What the sandbox allows
#   - Reading anything except ~/.ssh, ~/.gnupg, ~/.aws and the keychains.
#   - Running anything except launchctl, ssh and screen. Nothing can start a process
#     outside the sandbox: LaunchServices and AppleEvents are closed to every program
#     (so `open`, `osascript` or an NSWorkspace call fail), and so are unix sockets.
#   - Writing only: the worktree, each --write path, $TMPDIR, the per-user cache dir,
#     Pi's sessions and its lock files, /dev/tty* and /dev/null — and in the repo's
#     shared .git only objects/, this worktree's private git dir, and the ref and
#     reflog of the worktree's own branch. So Pi can commit on its branch, and cannot
#     move main, rewrite other branches, change .git/config or install hooks.
#     (Git takes packed-refs.lock on every ref update; the lock is allowed, but
#     installing a new packed-refs is not, so a packed main can't be rewritten.)
#   - Network only to the given localhost ports. Unix sockets only for DNS and syslog
#     (so not tmux's socket, the Docker socket or ssh-agent).
#
# Refuses to start unless --dir is a linked worktree on a branch other than the
# default branch. Sets PI_AGENT=1 for project hooks; turns off git's automatic
# gc/maintenance, which would rewrite packed-refs; and commits unsigned — Pi can't
# read ~/.gnupg, and shouldn't sign as you. Your reviewed merge carries the signature.
set -u
cmd=${1:-}; shift 2>/dev/null
SELF=${0:A}

die() { print -u2 "pi_sandboxed: $*"; exit 2 }
real() { [[ -e $1 ]] || mkdir -p -- "$1"; print -r -- ${1:A} }   # absolute, symlinks resolved
sbquote() { print -r -- "\"${1//\"/\\\"}\"" }                    # a string literal for the profile
rx() { print -r -- "$1" | sed 's/[][\\.*^$+?(){}|]/\\&/g' }      # escape for a profile regex

parse_opts() {
  dir=$PWD writes=() ports=() rest=()
  while (( $# )); do
    case $1 in
      --dir) dir=$2; shift 2 ;;
      --write) writes+=("$2"); shift 2 ;;
      --port) ports+=("$2"); shift 2 ;;
      --) shift; rest+=("$@"); break ;;
      *) rest+=("$1"); shift ;;
    esac
  done
  (( $#ports )) || ports=(8000)
  [[ -d $dir ]] || die "--dir $dir is not a directory"
  dir=${dir:A}
}

# Checks the worktree and sets: common, gitdir, branch.
check_worktree() {
  setopt local_options extended_glob
  common=$(git -C "$dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) \
    || die "$dir is not in a git repository"
  gitdir=$(git -C "$dir" rev-parse --path-format=absolute --git-dir)
  common=${common:A} gitdir=${gitdir:A}
  [[ $gitdir != $common ]] || die "$dir is the main checkout; give Pi a linked worktree (git worktree add -b <branch> ...)"
  branch=$(git -C "$dir" symbolic-ref --quiet --short HEAD) || die "$dir has a detached HEAD; check out a branch"
  local default=$(git -C "$dir" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)
  default=${default#origin/}
  [[ $branch != (main|master) && $branch != ${default:-main} ]] || die "$dir is on the default branch ($branch)"
}

profile() {
  check_worktree
  local tmp=$(real "${TMPDIR:-/tmp}") cache=$(real "$(getconf DARWIN_USER_CACHE_DIR)")
  local pi=$(real "$HOME/.pi/agent") ref=$common/refs/heads/$branch log=$common/logs/refs/heads/$branch
  local w lines=()
  for w in $writes; do lines+=("  (subpath $(sbquote "$(real "$w")"))"); done
  # A packed branch has no loose directory left: allow re-creating just its parents.
  local part prefix=
  for part in ${(s:/:)branch%/*}; do
    [[ $branch == */* ]] || break
    prefix=${prefix:+$prefix/}$part
    lines+=("  (literal $(sbquote "$common/refs/heads/$prefix")) (literal $(sbquote "$common/logs/refs/heads/$prefix"))")
  done
  local p nets=()
  for p in $ports; do [[ $p == <-> ]] || die "--port $p is not a number"; nets+=("  (remote ip \"localhost:$p\")"); done
  cat <<EOF
(version 1)
(allow default)

;; Writes: only the worktree, its branch and the scratch it needs.
(deny file-write*)
(allow file-write*
  (literal "/dev/null") (literal "/dev/zero") (literal "/dev/dtracehelper")
  (regex #"^/dev/(tty|ttys|fd/|ptmx)")
  (subpath $(sbquote "$dir"))
  (subpath $(sbquote "$tmp"))
  (subpath $(sbquote "$cache"))
  (subpath $(sbquote "$pi/sessions"))
  (regex $(sbquote "^$(rx "$pi")/[^/]+\\.lock(/|\$)"))
  (subpath $(sbquote "$gitdir"))
  (subpath $(sbquote "$common/objects"))
  (regex $(sbquote "^$(rx "$ref")(\\.lock)?\$"))
  (regex $(sbquote "^$(rx "$log")(\\.lock)?\$"))
  (literal $(sbquote "$common/packed-refs.lock"))
${(F)lines})

;; Secrets stay unreadable.
(deny file-read*
  (subpath $(sbquote "$HOME/.ssh")) (subpath $(sbquote "$HOME/.gnupg"))
  (subpath $(sbquote "$HOME/.aws")) (subpath $(sbquote "$HOME/Library/Keychains")))

;; No way to start a process outside the sandbox.
;; open, osascript and tmux may run — Pi itself runs `open`, and blocking an exec
;; crashes it — but they fail at the LaunchServices, AppleEvents and socket rules.
(deny process-exec
  (literal "/bin/launchctl") (literal "/usr/bin/ssh") (literal "/usr/bin/screen"))
;; LaunchServices starts apps outside the sandbox (NSWorkspace from any Swift or
;; Python script, not only `open`), and AppleEvents drive apps that do.
(deny mach-lookup (global-name-regex #"^com\.apple\.(lsd\.|coreservices\.)"))

;; Network: the model server only. Unix sockets: DNS and syslog only.
(deny network-outbound)
(allow network-outbound
${(F)nets}
  (literal "/private/var/run/mDNSResponder")
  (literal "/private/var/run/syslog"))
EOF
}

# Runs "$@" under the profile, with the environment Pi's tools should see.
sandboxed() {
  local sb=$(mktemp "${TMPDIR:-/tmp}/pi-sandbox.XXXXXX")
  profile > "$sb" || { rm -f "$sb"; exit 2 }
  env PI_AGENT=1 PI_SANDBOX_DIR="$dir" \
    GIT_CONFIG_COUNT=4 GIT_CONFIG_KEY_0=gc.auto GIT_CONFIG_VALUE_0=0 \
    GIT_CONFIG_KEY_1=maintenance.auto GIT_CONFIG_VALUE_1=false \
    GIT_CONFIG_KEY_2=commit.gpgsign GIT_CONFIG_VALUE_2=false \
    GIT_CONFIG_KEY_3=tag.gpgsign GIT_CONFIG_VALUE_3=false \
    sandbox-exec -f "$sb" "$@"
  local rc=$?
  rm -f "$sb"
  return $rc
}

case $cmd in
profile) parse_opts "$@"; profile ;;
exec) parse_opts "$@"; (( $#rest )) || die "exec needs a command after --"; cd "$dir" && sandboxed "${rest[@]}" ;;
run) parse_opts "$@"; cd "$dir" && sandboxed pi "${rest[@]}" ;;
spawn)
  parse_opts "$@"
  tier=${rest[1]:-code} name=${rest[2]:-pi-sandbox-${rest[1]:-code}}
  check_worktree
  sd=$(mktemp -d "${TMPDIR:-/tmp}/pi-team.XXXXXX")
  args=(--dir ${(q)dir}); for w in $writes; do args+=(--write ${(q)w}); done; for p in $ports; do args+=(--port $p); done
  # The pane runs this script's `run`, so the profile is built and applied the same way.
  pane=$(tmux split-window -h -d -t "${TMUX_PANE:-}" -l 45% -c "$dir" -P -F '#{pane_id}' \
    "${(q)SELF} run ${args[*]} -- --approve --session-dir ${(q)sd} --model omlx/$tier")
  tmux set -p -t "$pane" @alias "$name"
  tmux set -p -t "$pane" @pi_session_dir "$sd"
  tmux set -p -t "$pane" @pi_sandbox_dir "$dir"
  sleep 6
  print -r -- "$pane"
  ;;
self-test) exec zsh "${SELF:h}/pi_sandbox_selftest.sh" "$@" ;;
*) sed -n '2,13p' "$SELF" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
