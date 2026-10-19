#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
PreToolUse guard for Write/Edit/NotebookEdit on files inside the Obsidian vault.

Plugin agents can't carry their own hooks, so the role split is enforced here by agent_type:
- archivist:archivist-architect, inside the write zones   -> no decision (normal flow)
- archivist:archivist-architect, outside the write zones  -> deny
- any other caller (main thread, other agents)           -> ask (vault notes go through the
                                                             archivist and `vault-write`)
Files outside the vault, or no archivist config: no decision.
"""

import json
import sys
from pathlib import Path

from obsidian_guard import load_vault_write

ARCHITECT = "archivist:archivist-architect"


def decide(payload: dict, vw, cfg) -> tuple[str, str] | None:
    tool_input = payload.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not target or vw is None:
        return None
    root: Path = cfg["root"]
    p = Path(target).expanduser().resolve()
    if p != root and root not in p.parents:
        return None
    _, rel = vw.resolve_note(cfg, str(p))
    if payload.get("agent_type") == ARCHITECT:
        if vw.in_zone(rel, cfg["zones"]):
            return None
        return "deny", f"Archivist policy: {rel} is outside the configured write zones ({', '.join(cfg['zones']) or 'none'})."
    return "ask", (f"{rel} is a vault note. Vault writes go through the archivist agent and `vault-write` "
                   "(zones, drift check, lint, git snapshot); confirm a direct edit.")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    vw, cfg = load_vault_write()
    try:
        decision = decide(payload, vw, cfg)
    except Exception:  # an unresolvable path: leave it to the normal permission flow
        decision = None
    if decision:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision[0],
            "permissionDecisionReason": decision[1],
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
