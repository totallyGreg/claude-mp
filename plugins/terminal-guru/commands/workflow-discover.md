---
name: workflow-discover
description: Scan command history, brew inventory, XDG configs, and git log to discover workflow patterns, tool preferences, and graduation candidates.
---

Run the workflow discovery script and present findings.

1. Load the user's terminal profile (check `$TERMINAL_GURU_PROFILE`, then `${XDG_CONFIG_HOME:-~/.config}/terminal-guru/profile.md`, then `${CLAUDE_PLUGIN_ROOT}/.terminal-guru-profile.local.md`)
2. Run the discovery script: `bash ${CLAUDE_PLUGIN_ROOT}/skills/environment-composition/scripts/workflow-discover.sh`
3. Load `${CLAUDE_PLUGIN_ROOT}/skills/environment-composition/references/composition_philosophy.md` for the Pattern Graduation Pipeline
4. Present findings organized as:
   - **Tool Landscape**: what's installed, configured, and recently added
   - **Top Command Patterns**: repeated sequences with graduation suggestions
   - **Tool Preferences**: frecency data for key tools
   - **Recommendations**: specific graduation actions using the Pipeline
5. Offer to update the profile's `workflow_patterns` and `tool_preferences` sections with the findings
6. If the profile has empty `versions:` fields, run version detection (`mise --version`, `tmux -V`, `sesh --version`, `zsh --version`) and offer to update
