#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
PreToolUse guard for Bash: stops destructive vault operations that permission rules can't
match reliably (a `*` in the middle of a rule spans one token, so argument order defeats it).

- obsidian delete                      -> deny
- obsidian create ... overwrite        -> deny (use `vault-write apply`)
- obsidian move                        -> ask
- rm / mv on a path inside the vault   -> ask

Options before the subcommand (`obsidian vault=X delete`) are handled. Prints a
hookSpecificOutput decision, or nothing to defer to the normal permission flow.
"""

import json
import os
import re
import shlex
import sys
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

OPERATORS = {";", "&", "&&", "|", "||", "\n", "(", ")"}


def vault_root() -> Path | None:
    try:
        path = str(Path(__file__).resolve().parent.parent / "bin" / "vault-write")
        loader = SourceFileLoader("vault_write", path)
        spec = importlib.util.spec_from_loader("vault_write", loader)
        vw = importlib.util.module_from_spec(spec)
        loader.exec_module(vw)
        return vw.load_config()["root"]
    except Exception:
        return None


def segments(command: str) -> list[list[str]]:
    """Split into simple commands, respecting quotes (an operator inside quotes stays literal)."""
    lex = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    out, cur = [], []
    try:
        for tok in lex:
            if tok in OPERATORS or set(tok) <= set(";&|()"):
                out.append(cur)
                cur = []
            else:
                cur.append(tok)
    except ValueError:  # unbalanced quotes: fall back to whitespace tokens of the whole command
        return [command.split()]
    out.append(cur)
    return [c for c in out if c]


def check(command: str, root: Path | None) -> tuple[str, str] | None:
    for toks in segments(command):
        while toks and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0]):  # leading VAR=value
            toks = toks[1:]
        if not toks:
            continue
        prog = os.path.basename(toks[0])
        if prog == "obsidian":
            rest = toks[1:]
            i = next((k for k, t in enumerate(rest) if "=" not in t), None)  # skip vault=… style options
            sub, args = (rest[i], rest[i:]) if i is not None else ("", [])
            if sub == "delete":
                return "deny", "obsidian delete is blocked by the archivist guard; delete notes yourself in Obsidian."
            if sub == "create" and "overwrite" in args[1:]:
                return "deny", "obsidian create … overwrite is blocked by the archivist guard; use `vault-write apply --base <hash>`."
            if sub == "move":
                return "ask", "obsidian move renames a note and rewrites links; confirm the move."
        elif prog in ("rm", "mv") and root:
            for t in toks[1:]:
                if t.startswith("-"):
                    continue
                try:
                    p = Path(t).expanduser().resolve()
                except (OSError, RuntimeError):
                    continue
                if p == root or root in p.parents:
                    return "ask", f"{prog} touches the Obsidian vault ({t}); confirm, or use Obsidian / vault-write."
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if "obsidian" not in command and not any(w in command for w in ("rm", "mv")):
        return 0
    decision = check(command, vault_root())
    if decision:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision[0],
            "permissionDecisionReason": decision[1],
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
