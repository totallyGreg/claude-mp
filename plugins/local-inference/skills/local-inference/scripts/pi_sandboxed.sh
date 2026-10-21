#!/bin/zsh
# pi_sandboxed.sh — Pi with a shell under agent_sandbox.sh: one worktree branch, no
# other writes, no network but its oMLX model, nothing started outside.
#
#   pi_sandboxed.sh run   [opts] -- <pi args...>    one-shot `pi` under the sandbox
#   pi_sandboxed.sh spawn [opts] [tier] [name]      a sandboxed Pi pane; prints the pane id.
#                                                   Drive it with pi_team.sh ask / close.
#   pi_sandboxed.sh exec  [opts] -- <cmd...>        any command, with Pi's allowances
#   pi_sandboxed.sh profile [opts]                  print the profile
#   pi_sandboxed.sh self-test [--live]              prove what is allowed and refused
#
#   opts: those of agent_sandbox.sh (--dir, --write, --state, --locks, --port).
#
# What it adds to agent_sandbox.sh: Pi's sessions as --state, its config dir as
# --locks (Pi takes settings.json.lock and auth.json.lock), oMLX's port 8000 unless
# --port is given, and PI_AGENT=1 for project hooks.
set -u
cmd=${1:-}; shift 2>/dev/null
SELF=${0:A}
AS=${SELF:h}/agent_sandbox.sh
PI_DIR=$HOME/.pi/agent
source ${SELF:h}/pi_env.sh

# Pi's allowances, added to whatever options were given.
pi_opts() {
  local a has_port=0
  for a in "$@"; do [[ $a == --port ]] && has_port=1; done
  extra=(--state "$PI_DIR/sessions" --locks "$PI_DIR")
  (( has_port )) || extra+=(--port 8000)
}

# Splits "$@" at -- into opts and rest.
split() { opts=() rest=(); while (( $# )); do [[ $1 == -- ]] && { shift; rest=("$@"); break }; opts+=("$1"); shift; done }

case $cmd in
profile) pi_opts "$@"; zsh "$AS" profile "$@" "${extra[@]}" ;;
exec) split "$@"; pi_opts "${opts[@]}"; pi_env; zsh "$AS" exec "${opts[@]}" "${extra[@]}" -- env "${reply[@]}" "${rest[@]}" ;;
run) split "$@"; exec zsh "$SELF" exec "${opts[@]}" -- pi "${rest[@]}" ;;
spawn)
  # Leading options, then [tier] [name].
  opts=() pos=()
  while (( $# )); do
    case $1 in --dir|--write|--state|--locks|--port) opts+=("$1" "$2"); shift 2 ;; *) pos+=("$1"); shift ;; esac
  done
  tier=${pos[1]:-code} name=${pos[2]:-pi-sandbox-${pos[1]:-code}}
  dir=$PWD; for (( i = 1; i < $#opts; i++ )); do [[ ${opts[i]} == --dir ]] && dir=${opts[i+1]}; done
  zsh "$AS" profile "${opts[@]}" >/dev/null || exit 2   # refuse here, not in a pane that vanishes
  sd=$(mktemp -d "${TMPDIR:-/tmp}/pi-team.XXXXXX")
  # The pane runs this script's `run`, so the profile is built and applied the same way.
  pane=$(tmux split-window -h -d -t "${TMUX_PANE:-}" -l 45% -c "$dir" -P -F '#{pane_id}' \
    "${(q)SELF} run ${(j: :)${(q)opts[@]}} -- --approve --session-dir ${(q)sd} --model omlx/$tier")
  tmux set -p -t "$pane" @alias "$name"
  tmux set -p -t "$pane" @pi_session_dir "$sd"
  tmux set -p -t "$pane" @pi_sandbox_dir "${dir:A}"
  sleep 6
  print -r -- "$pane"
  ;;
self-test) exec zsh "${SELF:h}/agent_sandbox_selftest.sh" "$@" ;;
*) sed -n '2,13p' "$SELF" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
