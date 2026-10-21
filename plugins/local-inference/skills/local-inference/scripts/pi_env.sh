# pi_env.sh — sourced by pi_sandboxed.sh and pi_team.sh: the environment every local Pi run gets.
#
# PI_AGENT=1 lets project hooks refuse default-branch commits.
# PI_AUTO_MODE_MODEL points pi-verdict's judge (when that package is installed) at the fast
# tier: thinking off, so its short verdicts don't run out of tokens and fail closed, and runs
# ~3× faster than judging with the session model (references/tiers.md derivation 17). Pi's
# `omlx/fast` name doesn't resolve there, so the full id comes from ~/.pi/agent/models.json.
# A value already set wins; nothing is set when there is no fast entry.
pi_env() {
  local fast
  fast=$(/usr/bin/jq -r '[.providers.omlx.models[]? | select(.name | startswith("fast")) | .id][0] // empty' \
    ~/.pi/agent/models.json 2>/dev/null)
  reply=(PI_AGENT=1)
  if [[ -n ${PI_AUTO_MODE_MODEL:-} ]]; then reply+=(PI_AUTO_MODE_MODEL=$PI_AUTO_MODE_MODEL)
  elif [[ -n $fast ]]; then reply+=(PI_AUTO_MODE_MODEL=omlx/$fast)
  fi
}
