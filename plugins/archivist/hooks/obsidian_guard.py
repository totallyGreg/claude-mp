#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
PreToolUse guard for Bash: stops destructive vault operations that permission rules can't
match reliably (a `*` in the middle of a rule spans one token, so argument order defeats it).

- obsidian delete, eval, dev:cdp           -> deny
- obsidian create ... overwrite            -> deny (use `vault-write apply`)
- obsidian create/append/prepend/property:set/property:remove/task <update>
    without an explicit path=              -> deny (a missing or mistyped target acts on
                                              whatever note is open in Obsidian)
    without vault=<config vault name>      -> deny (the CLI targets the focused vault;
                                              daily:append/prepend need it too)
    with path= outside the write zones     -> deny
- obsidian move/rename/command/template:insert/history:restore/sync:restore,
  base:create, plugin and theme installs   -> ask
- rm / mv on a path inside the vault       -> ask

Wrappers (timeout, env, nice, nohup, command, exec, sudo, xargs, time) and `sh|bash|zsh -c`
are unwrapped before matching. Prints a hookSpecificOutput decision, or nothing to defer to
the normal permission flow.
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
OBSIDIAN = {"obsidian", "obsidian-cli"}
SHELLS = {"sh", "bash", "zsh"}
WRAPPERS = {"timeout", "env", "nice", "nohup", "command", "exec", "sudo", "xargs", "time"}
# Wrapper options that take a separate value (`nice -n 5`, `xargs -I {}`, `sudo -u bob`)
VALUE_OPTS = {"-n", "-I", "-L", "-P", "-d", "-s", "-E", "-u", "-g", "-k"}
DENY = {
    "delete": "obsidian delete is blocked by the archivist guard; delete notes yourself in Obsidian.",
    "eval": "obsidian eval runs arbitrary JavaScript in the vault and bypasses every write rule; it is blocked by the archivist guard.",
    "dev:cdp": "obsidian dev:cdp drives the app through DevTools and bypasses every write rule; it is blocked by the archivist guard.",
}
ASK = {
    "move": "obsidian move renames a note and rewrites links; confirm the move.",
    "rename": "obsidian rename renames a note and rewrites links; confirm the rename.",
    "command": "obsidian command runs an arbitrary Obsidian command (some delete or edit the open note); confirm.",
    "template:insert": "obsidian template:insert writes into whatever note is open in Obsidian; confirm.",
    "base:create": "obsidian base:create writes a new note where the base decides, outside the zone check; confirm.",
    "history:restore": "obsidian history:restore replaces a note with an older version; confirm.",
    "sync:restore": "obsidian sync:restore replaces a note with a Sync version; confirm.",
    "plugin:install": "Installing an Obsidian plugin runs third-party code in the vault; confirm.",
    "plugin:uninstall": "Uninstalling an Obsidian plugin removes its settings; confirm.",
    "theme:install": "Installing an Obsidian theme changes vault config; confirm.",
    "theme:uninstall": "Uninstalling an Obsidian theme changes vault config; confirm.",
}
WRITES = {"create", "append", "prepend", "property:set", "property:remove"}
TASK_UPDATES = {"toggle", "done", "todo"}
DAILY_WRITES = {"daily:append", "daily:prepend"}


def load_vault_write():
    try:
        path = str(Path(__file__).resolve().parent.parent / "bin" / "vault-write")
        loader = SourceFileLoader("vault_write", path)
        spec = importlib.util.spec_from_loader("vault_write", loader)
        vw = importlib.util.module_from_spec(spec)
        loader.exec_module(vw)
        return vw, vw.load_config()
    except Exception:
        return None, None


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


def unwrap(toks: list[str]) -> list[str]:
    """Strip leading VAR=value assignments and wrapper commands with their options."""
    while toks:
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0]):
            toks = toks[1:]
            continue
        prog = os.path.basename(toks[0])
        if prog not in WRAPPERS:
            return toks
        toks = toks[1:]
        while toks and (toks[0].startswith("-") or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0])):
            toks = toks[2:] if toks[0] in VALUE_OPTS else toks[1:]
        if prog == "timeout" and toks:  # the duration
            toks = toks[1:]
    return toks


def kv(args: list[str]) -> dict[str, str]:
    return dict(a.split("=", 1) for a in args if "=" in a)


def check_write(sub: str, args: list[str], vw, cfg) -> tuple[str, str] | None:
    params = kv(args)
    if sub == "task" and not (TASK_UPDATES & set(args) or "status" in params):
        return None  # a read
    if cfg and params.get("vault") != cfg["root"].name:
        return "deny", (f"Archivist policy: obsidian {sub} needs vault=\"{cfg['root'].name}\". Without it the CLI "
                        "writes to whichever vault is focused in Obsidian, not the configured one.")
    if sub in DAILY_WRITES or (sub == "task" and "daily" in args):
        return None  # the daily note: Obsidian resolves the path
    target = params.get("path", "")
    if sub == "task" and not target:
        target = params.get("ref", "").rsplit(":", 1)[0]
    if not target:
        return "deny", (f"Archivist policy: obsidian {sub} needs an explicit path= (exact vault path). "
                        "Without it, or with a mistyped parameter, the CLI writes to whatever note is open in Obsidian.")
    if vw is None:
        return "ask", f"obsidian {sub} writes to {target}, but no archivist config was found to check write zones; confirm."
    try:
        _, rel = vw.resolve_note(cfg, target)
    except Exception as e:
        return "deny", f"Archivist policy: {e}"
    if not vw.in_zone(rel, cfg["zones"]):
        return "deny", f"Archivist policy: {rel} is outside the configured write zones ({', '.join(cfg['zones']) or 'none'})."
    return None


def check_obsidian(rest: list[str], vw, cfg) -> tuple[str, str] | None:
    i = next((k for k, t in enumerate(rest) if "=" not in t), None)  # skip vault=… style options
    sub, args = (rest[i], rest[i + 1:]) if i is not None else ("", [])
    if sub in DENY:
        return "deny", DENY[sub]
    if sub == "create" and "overwrite" in args:
        return "deny", "obsidian create … overwrite is blocked by the archivist guard; use `vault-write apply --base <hash>`."
    if sub in ASK:
        return "ask", ASK[sub]
    if sub in WRITES or sub in DAILY_WRITES or sub == "task":
        return check_write(sub, rest, vw, cfg)  # rest: vault= may come before the subcommand
    return None


def check(command: str, vw, cfg, depth: int = 0) -> tuple[str, str] | None:
    root = cfg["root"] if cfg else None
    for toks in segments(command):
        toks = unwrap(toks)
        if not toks:
            continue
        prog = os.path.basename(toks[0])
        if prog in SHELLS and "-c" in toks[1:-1] and depth < 3:
            decision = check(toks[toks.index("-c") + 1], vw, cfg, depth + 1)
        elif prog == "eval" and depth < 3:
            decision = check(" ".join(toks[1:]), vw, cfg, depth + 1)
        elif prog.lower() in OBSIDIAN:
            decision = check_obsidian(toks[1:], vw, cfg)
        elif prog in ("rm", "mv") and root:
            decision = None
            for t in toks[1:]:
                if t.startswith("-"):
                    continue
                try:
                    p = Path(t).expanduser().resolve()
                except (OSError, RuntimeError):
                    continue
                if p == root or root in p.parents:
                    decision = "ask", f"{prog} touches the Obsidian vault ({t}); confirm, or use Obsidian / vault-write."
                    break
        else:
            decision = None
        if decision:
            return decision
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if "obsidian" not in command and not any(w in command for w in ("rm", "mv")):
        return 0
    vw, cfg = load_vault_write()
    decision = check(command, vw, cfg)
    if decision:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision[0],
            "permissionDecisionReason": decision[1],
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
