#!/usr/bin/env bash
# Weekly Review Parallel Data Collector
#
# Runs all five GTD diagnostic queries simultaneously and outputs a single
# combined JSON object. Replaces sequential agent queries with one parallel
# shell execution — 5x faster than running each query in series.
#
# Usage:
#   bash weekly-review-collect.sh
#
# Output:
#   JSON to stdout with keys: collectedAt, inbox, overdue, waitingFor,
#   recentlyCompleted, stalledProjects

set -uo pipefail

# cd to scripts dir so JXA library loading (relative to CWD) works correctly
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPTS_DIR"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Run all queries in parallel — background each osascript call
osascript -l JavaScript gtd-queries.js --action inbox-count      > "$TMP/inbox.json"     2>&1 &
osascript -l JavaScript gtd-queries.js --action overdue          > "$TMP/overdue.json"   2>&1 &
osascript -l JavaScript gtd-queries.js --action waiting-for      > "$TMP/waiting.json"   2>&1 &
osascript -l JavaScript gtd-queries.js --action stalled-projects > "$TMP/stalled.json"   2>&1 &
osascript -l JavaScript gtd-queries.js --action recently-completed --days 7 \
                                                                 > "$TMP/completed.json" 2>&1 &
wait

# Combine into a single JSON envelope
python3 - "$TMP" << 'PYEOF'
import json, os, sys, datetime

tmp = sys.argv[1]

def load(filename):
    path = os.path.join(tmp, filename)
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        raw = ''
        try:
            with open(path) as f:
                raw = f.read()
        except Exception:
            raw = 'file missing'
        return {'error': str(e), 'raw': raw}

print(json.dumps({
    'collectedAt': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    'inbox': load('inbox.json'),
    'overdue': load('overdue.json'),
    'waitingFor': load('waiting.json'),
    'recentlyCompleted': load('completed.json'),
    'stalledProjects': load('stalled.json'),
}, indent=2))
PYEOF
