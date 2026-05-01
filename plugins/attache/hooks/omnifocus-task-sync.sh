#!/bin/bash
# omnifocus-task-sync.sh — PostToolUse hook for TaskUpdate
#
# When Claude Code marks a task complete via TaskUpdate, this hook
# searches for a matching OmniFocus task in AI Agent-tagged projects
# and marks it complete.
#
# Matching strategy:
#   1. Check .claude/omnifocus-maps/*.json for ID-based match (deterministic)
#   2. Fall back to name search within AI Agent-tagged projects (fuzzy)
#
# Exit codes:
#   0 — Always (never block Claude Code)
#
# Logs to: stderr (captured by Claude Code) and /tmp/claude-omnifocus-hook.log

set -uo pipefail

LOG_FILE="/tmp/claude-omnifocus-hook.log"

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg" >> "$LOG_FILE" 2>/dev/null || true
}

# Read JSON from stdin
input=$(cat)

# Extract status and subject from tool_input
status=$(echo "$input" | jq -r '.tool_input.status // empty' 2>/dev/null)
subject=$(echo "$input" | jq -r '.tool_input.subject // empty' 2>/dev/null)

# Only process completions
if [ "$status" != "completed" ]; then
    exit 0
fi

if [ -z "$subject" ]; then
    exit 0
fi

# Check if OmniFocus is running
if ! pgrep -x OmniFocus > /dev/null 2>&1; then
    log "SKIP: OmniFocus not running (task: $subject)"
    exit 0
fi

log "Processing completion: $subject"

# Strategy 1: Check mapping files for ID-based match
MAPS_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude/omnifocus-maps"
task_id=""

if [ -d "$MAPS_DIR" ]; then
    for mapfile in "$MAPS_DIR"/*.json; do
        [ -f "$mapfile" ] || continue
        # Look for the subject in the tasks mapping
        found_id=$(jq -r --arg name "$subject" '.tasks[$name] // empty' "$mapfile" 2>/dev/null)
        if [ -n "$found_id" ]; then
            task_id="$found_id"
            log "MATCH: Found ID $task_id via mapping file $(basename "$mapfile")"
            break
        fi
    done
fi

# ofo CLI path
OFO="${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core/scripts/ofo"

# Strategy 2: Fall back to name search (if no mapping match)
if [ -z "$task_id" ]; then
    search_result=$("$OFO" search "$subject" 2>/dev/null) || true

    if [ -n "$search_result" ]; then
        match_count=$(echo "$search_result" | jq -r '.count // 0' 2>/dev/null)
        if [ "$match_count" = "1" ]; then
            task_id=$(echo "$search_result" | jq -r '.tasks[0].id // empty' 2>/dev/null)
            log "MATCH: Found ID $task_id via name search"
        elif [ "$match_count" -gt 1 ] 2>/dev/null; then
            log "WARN: Multiple matches ($match_count) for '$subject', skipping"
            exit 0
        else
            log "WARN: No matches for '$subject'"
            exit 0
        fi
    else
        log "WARN: Search failed for '$subject'"
        exit 0
    fi
fi

# Mark the task complete in OmniFocus
if [ -n "$task_id" ]; then
    complete_result=$("$OFO" complete "$task_id" 2>/dev/null) || true

    success=$(echo "$complete_result" | jq -r '.success // false' 2>/dev/null)
    if [ "$success" = "true" ]; then
        log "DONE: Completed task $task_id ($subject)"
    else
        log "ERROR: Failed to complete task $task_id: $complete_result"
    fi
fi

exit 0
