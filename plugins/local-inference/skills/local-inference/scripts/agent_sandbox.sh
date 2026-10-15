#!/bin/zsh
# agent_sandbox.sh — run a coding agent (or any command) with a shell under a macOS
# sandbox that confines it to one git worktree branch. Harness-agnostic: Pi's
# launcher is pi_sandboxed.sh, built on this.
#
#   agent_sandbox.sh exec    [opts] -- <cmd...>   run a command under the sandbox
#   agent_sandbox.sh profile [opts]               print the sandbox profile
#
#   opts:  --dir <worktree>   where the agent works (default: $PWD)
#          --write <path>     another writable path, e.g. a build dir; repeatable
#          --state <path>     the agent's own state dir it must write; repeatable
#          --locks <dir>      a dir where only *.lock entries may be created; repeatable
#          --port <n>         a localhost port it may reach, e.g. its model; repeatable
#
# What the sandbox allows
#   - Reading anything except ~/.ssh, ~/.gnupg, ~/.aws and the keychains.
#   - Running anything except launchctl, ssh and screen. Nothing can start a process
#     outside the sandbox: LaunchServices and AppleEvents are closed to every program
#     (so open, osascript or an NSWorkspace call fail), and so are unix sockets.
#   - Writing only: the worktree, each --write and --state path, *.lock in each --locks
#     dir, $TMPDIR, the per-user cache dir, /dev/tty* and /dev/null — and in the repo's
#     shared .git only objects/, this worktree's private git dir, and the ref, reflog
#     and parent dirs of the worktree's own branch. So the agent commits on its branch
#     and can't move main, rewrite other branches, change .git/config or install hooks.
#     (Git takes packed-refs.lock on every ref update; the lock is allowed, but
#     installing a new packed-refs is not, so a packed main can't be rewritten.)
#   - Network only to the given localhost ports. Unix sockets only for DNS and syslog
#     (so not tmux's socket, the Docker socket or ssh-agent).
#
# Drops secrets from the environment it passes on (*TOKEN*, *SECRET*, *API_KEY*,
# cloud and forge credentials, CLAUDE*, ssh-agent and tmux variables).
#
# Refuses to start unless --dir is a linked worktree on a branch other than the
# default branch. Sets AGENT_SANDBOX=1 and AGENT_SANDBOX_DIR for project hooks and
# tools; turns off git's automatic gc/maintenance, which would rewrite packed-refs;
# and commits unsigned — the agent can't read ~/.gnupg, and shouldn't sign as you.
set -u
cmd=${1:-}; shift 2>/dev/null
SELF=${0:A}

die() { print -u2 "agent_sandbox: $*"; exit 2 }
real() { [[ -e $1 ]] || mkdir -p -- "$1"; print -r -- ${1:A} }   # absolute, symlinks resolved
sbquote() { print -r -- "\"${1//\"/\\\"}\"" }                    # a string literal for the profile
rx() { print -r -- "$1" | sed 's/[][\\.*^$+?(){}|]/\\&/g' }      # escape for a profile regex

parse_opts() {
  dir=$PWD writes=() states=() lockdirs=() ports=() rest=()
  while (( $# )); do
    case $1 in
      --dir) dir=$2; shift 2 ;;
      --write) writes+=("$2"); shift 2 ;;
      --state) states+=("$2"); shift 2 ;;
      --locks) lockdirs+=("$2"); shift 2 ;;
      --port) ports+=("$2"); shift 2 ;;
      --) shift; rest+=("$@"); break ;;
      *) rest+=("$1"); shift ;;
    esac
  done
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
  [[ $gitdir != $common ]] || die "$dir is the main checkout; use a linked worktree (git worktree add -b <branch> ...)"
  branch=$(git -C "$dir" symbolic-ref --quiet --short HEAD) || die "$dir has a detached HEAD; check out a branch"
  local default=$(git -C "$dir" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)
  default=${default#origin/}
  [[ $branch != (main|master) && $branch != ${default:-main} ]] || die "$dir is on the default branch ($branch)"
}

profile() {
  check_worktree
  local tmp=$(real "${TMPDIR:-/tmp}") cache=$(real "$(getconf DARWIN_USER_CACHE_DIR)")
  local ref=$common/refs/heads/$branch log=$common/logs/refs/heads/$branch
  local p w lines=() nets=()
  for w in $writes $states; do lines+=("  (subpath $(sbquote "$(real "$w")"))"); done
  for w in $lockdirs; do lines+=("  (regex $(sbquote "^$(rx "$(real "$w")")/[^/]+\\.lock(/|\$)"))"); done
  # A packed branch has no loose directory left: allow re-creating just its parents.
  local part prefix=
  if [[ $branch == */* ]]; then
    for part in ${(s:/:)branch%/*}; do
      prefix=${prefix:+$prefix/}$part
      lines+=("  (literal $(sbquote "$common/refs/heads/$prefix")) (literal $(sbquote "$common/logs/refs/heads/$prefix"))")
    done
  fi
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

;; open, osascript and tmux may run — agents run open themselves, and a blocked exec
;; crashes them — but they fail at the LaunchServices, AppleEvents and socket rules.
(deny process-exec
  (literal "/bin/launchctl") (literal "/usr/bin/ssh") (literal "/usr/bin/screen"))
;; LaunchServices starts apps outside the sandbox (NSWorkspace from any Swift or
;; Python script, not only open), and AppleEvents drive apps that do.
(deny mach-lookup (global-name-regex #"^com\\.apple\\.(lsd\\.|coreservices\\.)"))

;; Network: the given localhost ports only. Unix sockets: DNS and syslog only.
(deny network-outbound)
(allow network-outbound
${(F)nets}
  (literal "/private/var/run/mDNSResponder")
  (literal "/private/var/run/syslog"))
EOF
}

# Runs "$@" under the profile, with the environment the agent's tools should see.
sandboxed() {
  local sb=$(mktemp "${TMPDIR:-/tmp}/agent-sandbox.XXXXXX")
  profile > "$sb" || { rm -f "$sb"; exit 2 }
  # The caller's environment minus anything the agent shouldn't hold: tokens, keys,
  # its parent session's channels (Claude Code's messaging token, ssh-agent, tmux).
  local name drop=()
  for name in ${(k)parameters[(R)*export*]}; do
    [[ $name == (CLAUDE*|ANTHROPIC*|OPENAI*|AWS_*|GH_*|GITHUB_*|GITLAB_*|SSH_AUTH_SOCK|SSH_AGENT_PID|TMUX|TMUX_PANE|GPG_AGENT_INFO|*TOKEN*|*SECRET*|*PASSWORD*|*PASSWD*|*API_KEY*|*APIKEY*|*CREDENTIAL*) ]] \
      && drop+=(-u "$name")
  done
  env "${drop[@]}" AGENT_SANDBOX=1 AGENT_SANDBOX_DIR="$dir" \
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
*) sed -n '2,13p' "$SELF" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
