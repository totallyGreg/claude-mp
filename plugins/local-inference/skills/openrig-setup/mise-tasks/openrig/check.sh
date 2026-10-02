#!/usr/bin/env bash
#MISE description="Read-only audit of OpenRig and a project's rig specs; exit 1 on any FAIL"
#USAGE arg "[project]" help="Project directory (default: where mise run was invoked)"
# Checks prerequisites, rig doctor, the daemon, rig workspace doctor, every
# rig.yaml under the project (version, codex seats, agent_ref and cwd
# resolution, terminal send_text, rig up --plan) and duplicate rig names.
# Changes nothing. Prints OK / WARN / FAIL lines, then a summary.
set -uo pipefail

PROJECT=$(cd "${usage_project:-${1:-${MISE_ORIGINAL_CWD:-$PWD}}}" && pwd)
fails=0 warns=0
ok()   { printf '  OK    %s\n' "$*"; }
warn() { printf '  WARN  %s\n' "$*"; warns=$((warns + 1)); }
fail() { printf '  FAIL  %s\n' "$*"; fails=$((fails + 1)); }

echo "== Prerequisites"
if command -v rig >/dev/null; then ok "rig $(rig --version 2>/dev/null | head -1)"; else fail "rig not on PATH (npm install -g @openrig/cli)"; fi
if command -v node >/dev/null; then
	major=$(node --version | sed 's/^v\([0-9]*\).*/\1/')
	case $major in 22|24) ok "node $(node --version)" ;; *) fail "node $(node --version): OpenRig needs Node 22 or 24 (22 on Apple silicon)" ;; esac
else fail "node not on PATH"; fi
command -v tmux >/dev/null && ok "$(tmux -V)" || fail "tmux not on PATH"
command -v claude >/dev/null && ok "claude $(claude --version 2>/dev/null | head -1)" || fail "claude not on PATH"
command -v codex >/dev/null && ok "codex present" || ok "codex absent (Claude-only setup; codex seats will not launch)"
command -v rig >/dev/null || { echo "rig missing; stopping."; exit 1; }

echo "== Install (rig doctor)"
doctor=$(rig doctor 2>&1)
grep -q '\[FAIL\]' <<<"$doctor" && fail "rig doctor reports failures:" && grep '\[FAIL\]' <<<"$doctor" | sed 's/^/        /'
grep -q '\[FAIL\]' <<<"$doctor" || ok "rig doctor: no failures"
grep '\[WARN\]' <<<"$doctor" | sed 's/^ *\[WARN\] /  note  /'

echo "== Daemon"
if rig daemon status 2>&1 | grep -q 'running'; then ok "$(rig daemon status 2>&1 | head -1)"; daemon=1
else fail "daemon not running (rig daemon start, or rig start --last)"; daemon=0; fi

echo "== Config (non-default values)"
rig config --with-source 2>/dev/null | grep -v 'source: default' | grep 'source:' | sed 's/^/  /' || true
echo "  workspace.root = $(rig config get workspace.root 2>/dev/null)"

if [ "$daemon" = 1 ]; then
	echo "== Workspace (rig workspace doctor)"
	wsd=$(rig workspace doctor 2>&1)
	sed 's/^/  /' <<<"$wsd" | tail -15
	n=$(grep -c '\[WARN\]' <<<"$wsd"); warns=$((warns + n))
	n=$(grep -c '\[FAIL\]' <<<"$wsd"); fails=$((fails + n))
	grep -q daemon_reload_needed <<<"$wsd" && echo "  (0.5.17 has no 'rig daemon restart': rig daemon stop && rig daemon start)"
fi

# All rigs, running or stopped, as "name<TAB>status<TAB>lifecycle<TAB>rigId".
rigs=$({ rig ps --json 2>/dev/null; echo; rig ps --json --filter status=stopped 2>/dev/null; } | python3 -c '
import sys, json
seen = set()
for line in sys.stdin.read().splitlines():
    if not line.strip(): continue
    data = json.loads(line)
    for r in (data["entries"] if isinstance(data, dict) else data):
        if r["rigId"] in seen: continue
        seen.add(r["rigId"])
        print("\t".join([r["name"], r["status"], r.get("lifecycleState") or "", r["rigId"]]))
' 2>/dev/null)
rig_names=$(cut -f1 <<<"$rigs" | sort -u)

echo "== Project specs under $PROJECT"
specs=$(find "$PROJECT" -maxdepth 4 -name rig.yaml -not -path '*/node_modules/*' -not -path '*/.git/*' 2>/dev/null)
[ -z "$specs" ] && warn "no rig.yaml found (rig create <name> for a one-seat rig, or mise run openrig:new for a templated rig)"
for spec in $specs; do
	dir=$(dirname "$spec")
	name=$(sed -n 's/^name: *"\{0,1\}\([^"]*\)"\{0,1\} *$/\1/p' "$spec" | head -1)
	echo "  -- $spec (rig: ${name:-?})"
	grep -q '^version: *"0.2"' "$spec" && ok "version 0.2" || fail "version must be \"0.2\""
	grep -nE 'runtime: *codex' "$spec" >/dev/null && fail "codex runtime at line(s) $(grep -nE 'runtime: *codex' "$spec" | cut -d: -f1 | paste -sd, -) — convert to claude-code"
	grep -nE 'runtime: *codex' "$spec" >/dev/null || ok "no codex seats"
	culture=$(sed -n 's/^culture_file: *"\{0,1\}\([^"]*\)"\{0,1\} *$/\1/p' "$spec")
	[ -n "$culture" ] && { [ -f "$dir/$culture" ] && ok "culture_file $culture" || fail "culture_file $culture missing next to the spec"; }
	while read -r ref; do
		case $ref in
			local:*) p="$dir/${ref#local:}" ;;
			path:*)  p="${ref#path:}" ;;
		esac
		[ -f "$p/agent.yaml" ] && ok "agent_ref $ref" || fail "agent_ref $ref → no agent.yaml at $p"
	done < <(grep -oE 'agent_ref: *"?(local|path):[^"]*' "$spec" | sed -E 's/agent_ref: *"?//' | sort -u)
	# cwd resolves against the spec's directory, not where `rig up` runs.
	# A Claude seat's cwd gets OpenRig's status line, hooks, settings and CLAUDE.md
	# blocks, so it must not be a directory you run your own sessions in.
	while IFS=$'\t' read -r member runtime cwd; do
		case $cwd in /*) p=$cwd ;; *) p="$dir/$cwd" ;; esac
		if [ ! -d "$p" ]; then fail "$member cwd \"$cwd\" → $p does not exist (relative to the spec's dir)"; continue; fi
		abs=$(cd "$p" && pwd)
		root=$(git -C "$abs" rev-parse --show-toplevel 2>/dev/null)
		if [ "$runtime" = claude-code ] && [ -n "$root" ] && [ "$abs" = "$root" ]; then
			warn "$member (claude-code) cwd is the repo root $root — OpenRig replaces the status line and hooks there for your own sessions too; use the rig's folder (cwd: \".\") with permissions.additionalDirectories"
		else ok "$member cwd → $abs"; fi
	done < <(awk '
		function flush() { if (rt != "") printf "%s\t%s\t%s\n", id, rt, (cwd == "" ? "." : cwd) }
		/^ *- id:/ { flush(); id = $3; rt = ""; cwd = "" }
		/^ *runtime:/ { rt = $2 }
		/^ *cwd:/ { cwd = $2; gsub(/"/, "", cwd) }
		END { flush() }' "$spec")
	# A terminal seat is a shell: its send_text runs as a command, so it must start with one.
	while read -r first; do
		command -v "$first" >/dev/null && ok "terminal seat launches $first" ||
			fail "terminal seat send_text starts with \"$first\", not a command — prose is run by the shell (launch the agent: pi --model omlx/code \"<brief>\")"
	done < <(awk '/- id:/ { term = 0 } /runtime: *terminal/ { term = 1 }
		term && /value:/ { sub(/.*value: *["'"'"']?/, ""); split($0, w, " "); print w[1] }' "$spec")
	if [ "$daemon" = 1 ]; then
		plan=$(rig up "$spec" --plan 2>&1); rc=$?
		[ $rc = 0 ] && ok "rig up --plan validates" || { fail "rig up --plan failed:"; sed 's/^/        /' <<<"$plan" | head -15; }
		if [ -n "$name" ] && grep -qx "$name" <<<"$rig_names"; then
			rig doctor --spec "$spec" 2>&1 | grep -E 'spec_live' | sed 's/^/  /'
		fi
	fi
done

echo "== Rigs (running and stopped)"
[ -z "$rigs" ] && echo "  (none)"
[ -n "$rigs" ] && column -t -s $'\t' <<<"$rigs" | sed 's/^/  /'
for dup in $(cut -f1 <<<"$rigs" | sort | uniq -d); do
	warn "$(grep -c "^$dup	" <<<"$rigs") rigs named '$dup' — rig up $dup is ambiguous; keep one, rig archive the rest by id"
done

echo "== Summary: $fails FAIL, $warns WARN"
[ "$fails" = 0 ]
