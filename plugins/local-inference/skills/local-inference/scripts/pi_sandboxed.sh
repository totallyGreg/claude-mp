#!/bin/zsh
# pi_sandboxed.sh — run Pi with bash under macOS sandbox-exec, allowing writes
# only to its launch directory (worktree), a build scratch dir, $TMPDIR, and Pi's
# session dir. Reads are unrestricted.
#
#   pi_sandboxed.sh spawn [tier] [dir] [name] [scratch-dir]
#     split a pane beside this one running `pi --model omlx/<tier>` with bash
#     sandboxed.  scratch-dir defaults to <dir>/build-scratch.
#     Prints the pane id (alias pi-sandbox-<tier>).
#
#   pi_sandboxed.sh self-test
#     runs a quick self-test: touch inside (allowed) and touch ~/outside-test
#     (refused).  Exits 0 on pass, 1 on failure.
#
# How the sandbox works
#
#   sandbox-exec(1) on macOS applies a sandbox profile.  We build a profile
#   at runtime that allows read/write to specific paths:
#
#     - The launch directory (and everything under it) — Pi's worktree
#     - $TMPDIR — temporary files
#     - Pi's session dir (~/.pi/agent sessions, if running as a teammate)
#     - A build scratch directory (default: <dir>/build-scratch)
#     - The project's .git directory — git commit on a worktree branch writes
#       objects, refs, and worktree metadata to the main repo's .git
#
#   Refused paths:
#     - Anything outside the above set, including ~/ outside the worktree
#
#   This does NOT parse bash commands for writes (unreliable).  It relies on
#   the OS-level sandbox.  The permission-gate extension is still useful for
#   catching rm -rf / sudo / chmod 777 before they reach the sandbox.
#
#   The project's pre-commit hook (if any) still runs inside the sandbox and
#   can see the changes.  Pi should commit on its own branch, never merge, push,
#   release, or modify the default branch.  The orchestrator reviews the diff,
#   runs the full gate, and merges.
#
#   For extra safety, export PI_AGENT=1 in the spawned pane so the project's
#   hooks can refuse commits/merges on the default branch when this flag is set.
#
# Usage in the SKILL.md gated-edit recipe:
#
#   T=${CLAUDE_PLUGIN_ROOT}/skills/local-inference/scripts/pi_sandboxed.sh
#   P=$($T spawn code "$PWD" "$PWD/build-scratch")
#   $T ask $P "Run the project's fast check: mise run check:fast. If it fails,
#     fix the cause and retry. Loop until green. Then commit on your branch."
#
#   Brief-template line: "Commit only on your branch. Never merge, push, release,
#     or modify the default branch, whatever the project's AGENTS.md says."

set -u
cmd=${1:-}; shift 2>/dev/null

build_sandbox_policy() {
  local launch_dir=$1 scratch_dir=$2 session_dir=$3 caller_cwd=$4
  cat <<EOF
;; Sandbox profile for pi_sandboxed.sh
;; Auto-generated — do not edit.

(version 1)
(deny default)

(import "system.sb")

;; Allow execution of common shells
(allow process-exec
  (literal "/bin/bash")
  (literal "/bin/zsh")
  (literal "/usr/bin/env"))

;; Allow read/write to launch directory (Pi's worktree)
(allow file-read*
  (subpath "${launch_dir}"))
(allow file-write*
  (subpath "${launch_dir}"))

;; Allow read/write to scratch directory
(allow file-read*
  (subpath "${scratch_dir}"))
(allow file-write*
  (subpath "${scratch_dir}"))

;; Allow read/write to TMPDIR
(allow file-read*
  (subpath "${TMPDIR}"))
(allow file-write*
  (subpath "${TMPDIR}"))

;; Allow read access to caller's cwd (needed for getcwd)
(allow file-read*
  (subpath "${caller_cwd}"))
EOF

  # Allow read/write to session dir (if provided)
  if [[ -n "$session_dir" ]]; then
    cat <<EOF2

;; Allow read/write to session dir
(allow file-read*
  (subpath "${session_dir}"))
(allow file-write*
  (subpath "${session_dir}"))
EOF2
  fi

  # Allow read/write to .git directory (git commit on worktree branch)
  local git_dir
  git_dir=$(git -C "$launch_dir" rev-parse --git-dir 2>/dev/null || echo "")
  if [[ -n "$git_dir" ]]; then
    # Resolve to absolute path
    local abs_git_dir
    if [[ "$git_dir" == /* ]]; then
      abs_git_dir="$git_dir"
    else
      abs_git_dir=$(cd "$launch_dir" && cd "$(dirname "$git_dir")" && pwd)/$(basename "$git_dir")
    fi
    cat <<EOF3

;; Allow read/write to .git directory (git commit on worktree branch)
(allow file-read*
  (subpath "${abs_git_dir}"))
(allow file-write*
  (subpath "${abs_git_dir}"))
EOF3
  fi
}

case $cmd in
spawn)
  tier=${1:-code}
  dir=${2:-$PWD}
  name=${3:-pi-sandbox-${1:-code}}
  scratch=${4:-${dir}/build-scratch}
  sd=$(mktemp -d "${TMPDIR:-/tmp}/pi-sandbox.XXXXXX")

  # Create scratch dir if it doesn't exist
  mkdir -p "$scratch"

  # Build the sandbox policy (.sb format)
  policy_file=$(mktemp /tmp/pi-sandbox-policy.XXXXXX.sb)
  build_sandbox_policy "$dir" "$scratch" "$sd" "$PWD" > "$policy_file"

  # Split pane and run Pi under sandbox-exec
  pane=$(tmux split-window -h -d -t "${TMUX_PANE:-}" -l 45% -c "$dir" -P -F '#{pane_id}' \
    "sandbox-exec -f '$policy_file' pi --approve --session-dir '$sd' --model omlx/$tier; rm -f '$policy_file'")

  tmux set -p -t "$pane" @alias "$name"
  tmux set -p -t "$pane" @pi_session_dir "$sd"
  tmux set -p -t "$pane" @pi_scratch_dir "$scratch"
  tmux set -p -t "$pane" @pi_launch_dir "$dir"

  # Export PI_AGENT=1 so project hooks can refuse default-branch commits/merges
  tmux send-keys -t "$pane" "export PI_AGENT=1" Enter

  sleep 6
  echo "$pane"
  ;;
self-test)
  # Self-test: touch inside (allowed) and touch ~/outside-test (refused)
  test_dir=$(mktemp -d "${TMPDIR:-/tmp}/pi-sandbox-test.XXXXXX")
  policy_file=$(mktemp /tmp/pi-sandbox-test-policy.XXXXXX.sb)
  build_sandbox_policy "$test_dir" "$test_dir" "" "$PWD" > "$policy_file"

  pass=1

  # Test 1: touch inside should work (use a subshell to avoid getcwd issues)
  if /bin/bash -c "cd $test_dir && sandbox-exec -f $policy_file /bin/bash -c 'touch inside-test && echo inside:OK'"; then
    echo "PASS: touch inside sandbox works"
  else
    echo "FAIL: touch inside sandbox should work"
    pass=0
  fi

  # Test 2: touch ~/outside-test should be refused
  if sandbox-exec -f "$policy_file" /bin/bash -c "touch ~/outside-test 2>/dev/null"; then
    echo "FAIL: touch ~/outside-test should be refused"
    pass=0
  else
    echo "PASS: touch ~/outside-test is refused"
  fi

  # Cleanup
  rm -f "$policy_file"
  rm -rf "$test_dir"
  rm -f ~/outside-test 2>/dev/null

  exit $((1 - pass))
  ;;
*)
  sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 2
  ;;
esac
