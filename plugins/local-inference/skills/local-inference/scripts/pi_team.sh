#!/bin/zsh
# pi_team.sh — a Pi teammate in its own tmux pane, driven from Claude Code.
#
#   pi_team.sh spawn [tier] [dir] [name]   split a pane beside this one running `pi --model omlx/<tier>`
#                                           (default tier code, dir $PWD, name pi-<tier>); prints the pane id
#   pi_team.sh ask <pane> <task...>        type the task into that pane, wait, print Pi's final answer
#                                           (exit 1: no answer in PI_ASK_TIMEOUT s, default 1200;
#                                            exit 3: Pi's last 3 tool calls were all Auto Mode blocks)
#   pi_team.sh close <pane>                kill the pane and delete its session files
#
# Answers are read from Pi's session JSONL (complete and structured), not scraped
# from the screen. The session dir is stored on the pane as @pi_session_dir.
# Run `ask` with </dev/null under run_in_background, like any pi call.
set -u
cmd=${1:-}; shift 2>/dev/null
source ${0:A:h}/pi_env.sh

case $cmd in
spawn)
  tier=${1:-code} dir=${2:-$PWD} name=${3:-pi-${1:-code}}
  sd=$(mktemp -d "${TMPDIR:-/tmp}/pi-team.XXXXXX")
  pi_env
  # --approve: trust project files for this run, or a repo with .pi/settings.json
  # stops at a trust prompt nobody is watching.
  pane=$(tmux split-window -h -d -t "${TMUX_PANE:-}" -l 45% -c "$dir" -P -F '#{pane_id}' \
    "env ${(j: :)${(@q)reply}} pi --approve --session-dir '$sd' --model omlx/$tier")
  # pi_env's variables must be in the pane's command: typed into the pane, they
  # would be a message to the model.
  tmux set -p -t "$pane" @alias "$name"
  tmux set -p -t "$pane" @pi_session_dir "$sd"
  sleep 6
  echo "$pane"
  ;;
ask)
  pane=$1; shift
  sd=$(tmux show -pqv -t "$pane" @pi_session_dir)
  [[ -n $sd ]] || { echo "pi_team: $pane has no @pi_session_dir — not spawned by pi_team.sh" >&2; exit 2; }
  count_users() {
    local files=($sd/**/*.jsonl(N))
    (( $#files )) && cat $files | grep -c '"role":"user"' || echo 0
  }
  before=$(count_users)
  task="$*"
  # A long or multi-line task typed into Pi's editor can open its completion menu,
  # and the Enter then accepts a suggestion instead of submitting (2026-10-15: a
  # 3,000-character brief gained ".claude/" and sat unsent). Hand it over as a file.
  if [[ $task == *$'\n'* || ${#task} -gt 300 ]]; then
    tf=$(mktemp "$sd/task.XXXXXX") && print -r -- "$task" > "$tf"
    task="Read the file $tf with the read tool and carry out the task it describes, exactly."
  fi
  tmux send-keys -t "$pane" -l -- "$task"
  sleep 1
  tmux send-keys -t "$pane" Enter
  timeout=${PI_ASK_TIMEOUT:-1200}
  for i in {1..$(( (timeout + 2) / 3 ))}; do
    sleep 3
    python3 - "$sd" "$before" <<'PY'
import glob, json, sys
rows = [json.loads(l) for f in glob.glob(sys.argv[1] + "/**/*.jsonl", recursive=True) for l in open(f)]
msgs = [r["message"] for r in rows if r.get("type") == "message"]
users = [i for i, m in enumerate(msgs) if m["role"] == "user"]
if len(users) <= int(sys.argv[2]):
    sys.exit(1)
tail = msgs[users[-1] + 1:]
done = [m for m in tail if m["role"] == "assistant" and m.get("stopReason") in ("stop", "length", "error", "aborted")]
if not done:
    # A blocked call reads "[auto-mode <tag> block] BLOCKED — …" (pi-verdict). Three
    # in a row with no answer is a stall, not progress (2026-10-16: ~2 h of this).
    results = [m for m in tail if m["role"] == "toolResult"][-3:]
    text = lambda m: "".join(b.get("text", "") for b in m.get("content", []) if b.get("type") == "text")
    if len(results) == 3 and all(text(m).startswith("[auto-mode ") and "] BLOCKED" in text(m)[:40] for m in results):
        print("pi_team: Pi's last 3 tool calls were blocked by Auto Mode — check the pane:", file=sys.stderr)
        for m in results:
            print(f"  {m.get('toolName')}: {text(m)[:200]}", file=sys.stderr)
        sys.exit(3)
    sys.exit(1)
tools = [m["toolName"] for m in tail if m["role"] == "toolResult"]
m = done[-1]
print(f"[{m.get('model')} · tools: {', '.join(tools) or 'none'} · stop: {m['stopReason']}]")
print("".join(b.get("text", "") for b in m["content"] if b.get("type") == "text").strip())
PY
    rc=$?; (( rc == 1 )) || exit $rc
  done
  echo "pi_team: no answer after $timeout s (PI_ASK_TIMEOUT) — check the pane" >&2; exit 1
  ;;
close)
  pane=$1
  sd=$(tmux show -pqv -t "$pane" @pi_session_dir)
  tmux kill-pane -t "$pane"
  [[ -n $sd && $sd == */pi-team.* ]] && rm -r -- "$sd"
  ;;
*)
  sed -n '2,14p' "$0"; exit 2
  ;;
esac
