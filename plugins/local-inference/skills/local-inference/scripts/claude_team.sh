#!/bin/zsh
# claude_team.sh [tier] [dir] [extra-tools] — Claude Code on oMLX as a cross-session teammate, in a tmux
# pane beside this one. Prints the pane id; find the session's name with ListAgents (its
# tmux pane is shown there) and talk to it with SendMessage.
#
# Tiers match Pi's: oMLX's claude_code settings map haiku→:fast, sonnet→:code, opus→:deep,
# so /model inside the teammate switches tier. tier = haiku|sonnet|opus (default sonnet =
# code; the user's Claude default tier is opus, which would start it on deep).
# extra-tools (e.g. Edit or Edit,Write) are added to the read-only set and pre-approved:
# auto mode's classifier is unreachable through oMLX, so anything not allowlisted is blocked.
#
# "Slim" config, each flag earned in references/pi-vs-claude.md: a short brief instead of
# the default system prompt (52K→6–10K tokens per request), read-only tools plus messaging,
# no MCP servers, no skills, user settings only (a project SessionStart hook hijacked
# turns), and reply_guard.py as a Stop hook (the model forgot to SendMessage its answers).
set -u
tier=${1:-sonnet} dir=${2:-$PWD} extra=${3:-}
dir=${dir:A}
here=${0:A:h}
# Write tools are pre-approved only inside $dir (`//` = absolute path). An unscoped
# `--allowedTools Edit` let a teammate edit the user's main checkout from a worktree
# (09-30): outside $dir the edit falls to the unreachable classifier and is blocked.
tools=Read,Grep,Glob,SendMessage allowed=SendMessage
for t in ${(s:,:)extra}; do
  tools+=",$t"
  case $t in
    Edit|Write|NotebookEdit) allowed+=",$t(/$dir/**)" ;;
    *) allowed+=",$t" ;;
  esac
done
# The brief plus this session's directory, so it stops guessing absolute paths.
prompt=$(mktemp "${TMPDIR:-/tmp}/claude-team-prompt.XXXXXX")
{ cat "$here/claude_teammate_brief.txt"; print "\nYour working directory is $dir. Work only inside it and use paths relative to it; never read or change files outside it, even if another path looks like the same project."; } > $prompt
settings=$(printf '{"hooks":{"Stop":[{"hooks":[{"type":"command","command":"%s"}]}]}}' "$here/reply_guard.py")
pane=$(tmux split-window -h -d -t "${TMUX_PANE:-}" -l 45% -c "$dir" -P -F '#{pane_id}' \
  "omlx launch claude --model Qwen3.6-35B-A3B-oQ4e-mtp:code --cross-session -- \
     --model $tier \
     --system-prompt \"\$(cat '$prompt')\" \
     --tools '$tools' --allowedTools '$allowed' \
     --strict-mcp-config --disable-slash-commands --setting-sources user \
     --settings '$settings'; \
   echo \"[claude exited with status \$?]\"")
tmux set -p -t "$pane" remain-on-exit on   # keep the pane to see why it exited
tmux set -p -t "$pane" @alias omlx-claude
echo "$pane"
