#!/bin/bash
# submit-issue.sh — Write a friction report to .local/agent-issues/reports/
#
# Usage:
#   submit-issue.sh --type <type> --name <name> --category <category> \
#     --description <desc> [--project <path>] [--session <id>]
#
# Exit codes:
#   0 — Report filed successfully
#   1 — Error (missing args, not in a git repo, etc.)

set -uo pipefail

type=""
name=""
category=""
description=""
project=""
session=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --type)      type="$2"; shift 2 ;;
    --name)      name="$2"; shift 2 ;;
    --category)  category="$2"; shift 2 ;;
    --description) description="$2"; shift 2 ;;
    --project)   project="$2"; shift 2 ;;
    --session)   session="$2"; shift 2 ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$description" ]]; then
  echo "Error: --description is required" >&2
  exit 1
fi

if [[ -z "$type" ]]; then
  type="unknown"
fi

if [[ -z "$category" ]]; then
  category="other"
fi

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "Error: not inside a git repository" >&2
  exit 1
}

reports_dir="$repo_root/.local/agent-issues/reports"
mkdir -p "$reports_dir"

gitignore="$repo_root/.gitignore"
if ! grep -qx '\.local/' "$gitignore" 2>/dev/null; then
  printf '\n# WTF friction reports (local only, never commit)\n.local/\n' >> "$gitignore"
fi

timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
filename_ts=$(date -u +"%Y-%m-%d-%H%M%S")
filename="${filename_ts}-$$.md"

cat > "$reports_dir/$filename" <<REPORT
---
type: ${type}
name: "${name}"
category: ${category}
project: "${project}"
session: "${session}"
date: ${timestamp}
---

${description}
REPORT

echo "Friction report filed: .local/agent-issues/reports/$filename"
