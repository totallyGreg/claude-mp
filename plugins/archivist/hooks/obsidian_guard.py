#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
PreToolUse guard for Bash: stops destructive vault operations that permission rules can't
match reliably (a `*` in the middle of a rule spans one token, so argument order defeats it).

- obsidian delete, eval, dev:cdp           -> deny, except K-Plex API calls of an exact shape:
    obsidian vault=<config vault> eval code=JSON.stringify(window.kplexApi.v1.<read>({...}))
    or the documented async form (async()=>JSON.stringify(await window.kplexApi.v1.<m>({...})))().
    The argument must be plain data (keys, JSON strings, numbers, true/false/null, [], {}).
    Reads and previews defer to the normal permission flow; applyOntologyConfiguration asks.
- obsidian create ... overwrite            -> deny (use `vault-write apply`)
- obsidian create/append/prepend/property:set/property:remove/task <update>
    without an explicit path=              -> deny (a missing or mistyped target acts on
                                              whatever note is open in Obsidian)
    without vault=<config vault name>      -> deny. It must come before the subcommand: the CLI
      before the subcommand                   silently ignores a vault= after it and acts on the
                                              cwd's vault or the focused one (daily:* too)
    with path= outside the write zones     -> deny
- templater:create-from-template file=…   -> the same vault= rule, and file= zone-checked
- quickadd:run / quickadd:run-template     -> vars.path zone-checked when given, else ask
- obsidian move/rename/command/template:insert/history:restore/sync:restore,
  base:create, plugin and theme installs   -> ask (move/rename warn when Obsidian won't
                                              update links on its own: it would wait on a dialog)
- rm / mv on a path inside the vault       -> ask

Archivist agents (agent_type archivist:archivist = curator, archivist:archivist-architect =
architect) get their role's zones (vault-write's role_zones) and a closed list in the vault:
- allowed: obsidian, vault-write, and scripts inside this plugin (run directly, by python or uv run)
- anything else is denied if it runs from a working directory in the vault (the payload's cwd,
  then any `cd` in the command) or names a path into it, including redirection targets
- denied outright: $(…) and backticks, an ARCHIVIST_ROLE= or --role naming another role, and a
  shell variable the guard can't expand in a non-archivist command
- obsidian delete asks (to the trash); delete permanent is denied
Other callers (the user's own session) keep the rules above unchanged.

Wrappers (timeout, env, nice, nohup, command, exec, sudo, xargs, time) and `sh|bash|zsh -c`
are unwrapped before matching. Prints a hookSpecificOutput decision, or nothing to defer to
the normal permission flow.
"""

import json
import os
import re
import shlex
import sys
import unicodedata
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
KPLEX_READS = {
    "capabilities", "status", "coverage", "ontology", "ontologyGuide", "search", "node", "neighbors",
    "evidence", "ontologyDocuments", "inspectOntologyOccurrences", "previewOntologyConfiguration",
}
KPLEX_ASK = {"applyOntologyConfiguration": "K-Plex applyOntologyConfiguration saves a previewed ontology "
             "change to K-Plex's settings; confirm the reviewed preview."}
_CALL = r"window\.kplexApi\.v1\.([A-Za-z]+)\((.*)\)"
KPLEX_SYNC = re.compile(rf"JSON\.stringify\({_CALL}\)", re.S)
KPLEX_ASYNC = re.compile(rf"\(async\(\)=>JSON\.stringify\(await {_CALL}\)\)\(\)", re.S)
# Plain data only: JSON strings, numbers, literals, punctuation, and bare keys (checked below)
DATA_TOKEN = re.compile(r'\s+|"(?:[^"\\\x00-\x1f]|\\["\\/bfnrt]|\\u[0-9a-fA-F]{4})*"'
                        r"|-?\d+(?:\.\d+)?|true|false|null|[{}\[\],:]|[A-Za-z_][A-Za-z0-9_]*")
WRITES = {"create", "append", "prepend", "property:set", "property:remove"}
TEMPLATER_CREATE = "templater:create-from-template"
PLUGIN_WRITES = {TEMPLATER_CREATE, "quickadd:run", "quickadd:run-template"}
# The archivist's agents, by hook agent_type (Pi's guard.ts sends the same names).
ROLES = {"archivist:archivist": "curator", "archivist:archivist-architect": "architect"}
PLUGIN = Path(__file__).resolve().parent.parent
UV_VALUE_OPTS = {"--with", "--with-requirements", "--with-editable", "--python", "-p", "--project",
                 "--directory", "--from", "--index", "--extra", "--group", "--env-file"}
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


HEREDOC = re.compile(r"<<-?\s*(['\"])(\w+)\1")
# A heredoc fed to one of these is code, not text: keep its body so it is checked.
CODE_RUNNERS = re.compile(r"(ba|z)?sh|python3?(\.\d+)?|node|perl|ruby|osascript|uv|uvx|deno|bun")


def strip_quoted_heredocs(command: str) -> str:
    """Drop the bodies of quoted heredocs (<<'EOF'): the shell neither expands nor runs them, so
    note text with backticks or `rm` in it isn't mistaken for commands. A body fed to a shell or
    interpreter stays, because there it is code."""
    lines, out, i = command.split("\n"), [], 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        i += 1
        for m in HEREDOC.finditer(line):
            head = re.split(r"[;&|(]", line[: m.start()])[-1].split()
            head = unwrap(head)
            if head and CODE_RUNNERS.fullmatch(os.path.basename(head[0])):
                continue
            while i < len(lines) and lines[i].lstrip("\t") != m.group(2):
                i += 1
            i += 1  # the terminator line
    return "\n".join(out)


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


def _vault_key(name: str) -> str:
    """Obsidian matches vault names case-insensitively; macOS may hand us NFD."""
    return unicodedata.normalize("NFC", name).casefold()


def vault_first(sub: str, vault: str | None, cfg) -> tuple[str, str] | None:
    """`vault` is the vault= given before the subcommand (the only place the CLI reads it)."""
    if cfg and _vault_key(vault or "") != _vault_key(cfg["root"].name):
        return "deny", (f"Archivist policy: start the command with obsidian vault=\"{cfg['root'].name}\" {sub} …. "
                        "Without it, or with vault= after the subcommand (which the CLI silently ignores), "
                        "it writes to the working directory's vault or whichever vault is focused in Obsidian.")
    return None


def zone_check(sub: str, target: str, vw, cfg, role: str | None) -> tuple[str, str] | None:
    """Is vault path `target` inside the caller's zones? A role gets its own zones (vault-write's
    role_zones); without a role, the union of all zones."""
    if vw is None:
        return "ask", f"obsidian {sub} writes to {target}, but no archivist config was found to check write zones; confirm."
    try:
        _, rel = vw.resolve_note(cfg, target)
    except Exception as e:
        return "deny", f"Archivist policy: {e}"
    zones = vw.role_zones(cfg, role) if role else cfg["zones"]
    if not vw.in_zone(rel, zones):
        whose = f"the {role}'s write zones" if role else "the configured write zones"
        return "deny", f"Archivist policy: {rel} is outside {whose} ({', '.join(zones) or 'none'})."
    return None


def check_write(sub: str, args: list[str], vault: str | None, vw, cfg, role: str | None = None) -> tuple[str, str] | None:
    params = kv(args)
    if sub == "task" and not (TASK_UPDATES & set(args) or "status" in params):
        return None  # a read
    if d := vault_first(sub, vault, cfg):
        return d
    if sub in DAILY_WRITES or (sub == "task" and "daily" in args):
        return None  # the daily note: Obsidian resolves the path
    target = params.get("path", "")
    if sub == "task" and not target:
        target = params.get("ref", "").rsplit(":", 1)[0]
    if not target:
        return "deny", (f"Archivist policy: obsidian {sub} needs an explicit path= (exact vault path). "
                        "Without it, or with a mistyped parameter, the CLI writes to whatever note is open in Obsidian.")
    return zone_check(sub, target, vw, cfg, role)


def check_plugin_write(sub: str, args: list[str], vault: str | None, vw, cfg, role: str | None) -> tuple[str, str] | None:
    """Writes registered by Templater and QuickAdd: zone-check the target when the command names it."""
    if d := vault_first(sub, vault, cfg):
        return d
    params = kv(args)
    if sub == TEMPLATER_CREATE:
        if not params.get("file"):
            return "deny", f"Archivist policy: obsidian {sub} needs file= (the new note's vault path)."
        return zone_check(sub, params["file"], vw, cfg, role)
    try:  # QuickAdd: a choice like logEntries is told its target in vars.path
        target = json.loads(params.get("vars", "{}")).get("path")
    except (json.JSONDecodeError, AttributeError):
        target = None
    if isinstance(target, str) and target:
        return zone_check(sub, target, vw, cfg, role)
    return "ask", (f"obsidian {sub} writes wherever the QuickAdd choice or template decides, which the guard "
                   "can't zone-check; confirm. (Pass the target as vars.path to have it checked.)")


def links_auto_update(cfg) -> bool:
    """Settings → Files and links → Automatically update internal links. Obsidian leaves the key
    out of app.json until it's switched on, so a missing key means off."""
    try:
        return json.loads((cfg["root"] / ".obsidian" / "app.json").read_text()).get("alwaysUpdateLinks") is True
    except (OSError, ValueError, TypeError, KeyError):
        return False


def plain_data(arg: str) -> bool:
    """True when `arg` is empty or a JS literal of plain data: no calls, no identifiers as values."""
    tokens, pos = [], 0
    while pos < len(arg):
        m = DATA_TOKEN.match(arg, pos)
        if not m:
            return False
        if not m.group().isspace():
            tokens.append(m.group())
        pos = m.end()
    depth = 0
    for i, t in enumerate(tokens):
        if t in "{[":
            depth += 1
        elif t in "}]":
            depth -= 1
            if depth < 0:
                return False
        elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", t) and t not in ("true", "false", "null"):
            # a bare identifier is only allowed as an object key: `{key:` or `,key:`
            if not (0 < i < len(tokens) - 1 and tokens[i - 1] in "{," and tokens[i + 1] == ":"):
                return False
    return depth == 0 and (not tokens or tokens[0] == "{")


REDIRECT = re.compile(r"[<>&]*[<>][<>&]*")  # >, >>, <, >&, &>, 2> once split by shlex


def strip_redirects(args: list[str]) -> list[str]:
    """Drop shell redirections (`2>&1`, `> out.json`): they change where output goes, not the call."""
    out, i = [], 0
    while i < len(args):
        if REDIRECT.fullmatch(args[i]):
            if out and out[-1].isdigit():  # the fd number of `2>&1`
                out.pop()
            i += 2  # the operator and its target
            continue
        out.append(args[i])
        i += 1
    return out


def check_kplex(args: list[str], vault: str | None, cfg) -> tuple[str, str] | None:
    """`obsidian eval` is denied unless it is one K-Plex API call of an exact shape."""
    args = strip_redirects(args)
    code = args[0][len("code="):] if len(args) == 1 and args[0].startswith("code=") else None
    if code and ("$" in code or "`" in code):
        # The guard sees the text before the shell expands it: `$(…)`, `${…}` or backticks inside a
        # double-quoted code= would be replaced by arbitrary text that then runs as JavaScript.
        return "deny", ("Archivist policy: K-Plex eval code must not contain $ or backticks; the shell "
                        "would expand them after this check. Single-quote the code= argument.")
    m = code and (KPLEX_SYNC.fullmatch(code) or KPLEX_ASYNC.fullmatch(code))
    method = m.group(1) if m else None
    if not m or not plain_data(m.group(2)) or (method not in KPLEX_READS and method not in KPLEX_ASK):
        return "deny", DENY["eval"] + " Only single K-Plex API calls of the documented shape are allowed (see kplex-ontology.md)."
    if cfg and _vault_key(vault or "") != _vault_key(cfg["root"].name):
        return "deny", (f"Archivist policy: start K-Plex calls with obsidian vault=\"{cfg['root'].name}\" eval …, "
                        "so they reach the configured vault.")
    if method in KPLEX_ASK:
        return "ask", KPLEX_ASK[method]
    return None


def check_obsidian(rest: list[str], vw, cfg, role: str | None = None) -> tuple[str, str] | None:
    i = next((k for k, t in enumerate(rest) if "=" not in t), None)  # skip vault=… style options
    sub, args = (rest[i], rest[i + 1:]) if i is not None else ("", [])
    vault = kv(rest[:i] if i is not None else rest).get("vault")
    if sub == "eval":
        return check_kplex(args, kv(rest[:i]).get("vault"), cfg)
    if sub == "delete" and role:
        if "permanent" in args:
            return "deny", "Archivist policy: obsidian delete permanent skips Obsidian's trash; delete to the trash instead."
        return "ask", "obsidian delete moves a note to Obsidian's trash; confirm the delete."
    if sub in DENY:
        return "deny", DENY[sub]
    if sub == "create" and "overwrite" in args:
        return "deny", "obsidian create … overwrite is blocked by the archivist guard; use `vault-write apply --base <hash>`."
    if sub in ("move", "rename") and cfg and not links_auto_update(cfg):
        return "ask", (ASK[sub] + " Settings → Files and links → Automatically update internal links is off, so "
                       "Obsidian will ask about link updates in a dialog and the command waits until someone answers.")
    if sub in ASK:
        return "ask", ASK[sub]
    if sub in WRITES or sub in DAILY_WRITES or sub == "task":
        return check_write(sub, args, vault, vw, cfg, role)
    if sub in PLUGIN_WRITES:
        return check_plugin_write(sub, args, vault, vw, cfg, role)
    return None


def cli_targets(rest: list[str], vw, cfg) -> list[str]:
    """Vault paths an allowed `obsidian` call writes, moves or deletes, for the ledger
    (`vault-write audit`). Paths a QuickAdd choice picks itself aren't known and aren't listed."""
    i = next((k for k, t in enumerate(rest) if "=" not in t), None)
    if i is None or not cfg:
        return []
    sub, args = rest[i], rest[i + 1:]
    params = kv(args)
    path = params.get("path", "").lstrip("/")
    if sub in DAILY_WRITES or (sub == "task" and "daily" in args):
        today = (vw.daily_notes(cfg["root"]) or {}).get("today")
        return [today] if today else []
    if sub in WRITES or sub == "task" or sub == "delete":
        return [path or params.get("ref", "").rsplit(":", 1)[0]]
    if sub == TEMPLATER_CREATE:
        return [params.get("file", "").lstrip("/")]
    if sub in ("quickadd:run", "quickadd:run-template"):
        try:
            target = json.loads(params.get("vars", "{}")).get("path")
        except (json.JSONDecodeError, AttributeError):
            target = None
        return [target.lstrip("/")] if isinstance(target, str) and target else []
    if sub == "move" and path and params.get("to"):
        to = params["to"].strip("/")
        return [path, to if to.endswith(".md") else f"{to}/{os.path.basename(path)}"]
    if sub == "rename" and path and params.get("name"):
        name = params["name"] if os.path.splitext(params["name"])[1] else params["name"] + os.path.splitext(path)[1]
        return [path, Path(path).with_name(name).as_posix()]
    return []


def record_cli_writes(targets: list[str], vw, cfg) -> None:
    for rel in dict.fromkeys(t for t in targets if t):
        vw.record(cfg["root"], {"via": "obsidian", "path": vw.nfc(rel)})


def _inside(p: Path, root: Path) -> bool:
    return p == root or root in p.parents


def _expand(tok: str) -> str:
    """The plugin root is known even when the hook's environment doesn't carry it."""
    for var in ("${CLAUDE_PLUGIN_ROOT}", "$CLAUDE_PLUGIN_ROOT"):
        tok = tok.replace(var, str(PLUGIN))
    return os.path.expanduser(os.path.expandvars(tok))


def plugin_program(toks: list[str], cwd: Path) -> str | None:
    """The archivist program this segment runs: `vault-write` (on PATH or the plugin's bin/), or a
    script inside the plugin run directly, by python, or by `uv run`. None for anything else."""
    args, prog = toks, os.path.basename(toks[0])
    if prog in ("uv", "uvx"):
        args = args[1:]
        if args[:1] == ["run"]:
            args = args[1:]
        while args and args[0].startswith("-"):
            args = args[2:] if args[0] in UV_VALUE_OPTS else args[1:]
    elif re.fullmatch(r"python3?(\.\d+)?", prog):
        args = args[1:]
        while args and args[0].startswith("-"):
            if args[0] in ("-c", "-m"):
                return None  # code given on the command line, not a plugin file
            args = args[1:]
    if not args:
        return None
    if args is toks and args[0] == "vault-write":
        return "vault-write"
    p = (cwd / _expand(args[0])).resolve()
    return str(p) if p.is_file() and _inside(p, PLUGIN) else None


def check_role_flag(toks: list[str], role: str) -> tuple[str, str] | None:
    """A role can't run vault-write as another role."""
    for i, t in enumerate(toks):
        val = toks[i + 1] if t == "--role" and i + 1 < len(toks) else t[len("--role="):] if t.startswith("--role=") else None
        if val is not None and val != role:
            return "deny", f"Archivist policy: the {role} can't run vault-write as --role {val}."
    return None


def check_role_shell(toks: list[str], role: str, cwd: Path, root: Path) -> tuple[str, str] | None:
    """For an archivist role, a command that isn't obsidian, vault-write or an archivist script
    may not touch the vault: not from a working directory inside it, not with a path into it."""
    deny = ("deny", f"Archivist policy: the {role} works on the vault only through `obsidian` and `vault-write` "
            "(and the archivist's scripts), so Obsidian can track every change. Read notes with your read/grep/find "
            "tools; write with `vault-write`; move, rename and set properties with `obsidian`.")
    if _inside(cwd, root):
        return deny
    # The vault's path inside a longer argument (code for -c, a --flag=… value). A path the code builds
    # at run time can't be seen here; vault-write audit (task 4) is what catches that.
    if any(str(root) in t for t in toks):
        return deny
    for tok in toks:  # the program too: a script inside the vault is a path into it
        for part in (tok, tok.split("=", 1)[1] if "=" in tok else None):
            if not part or REDIRECT.fullmatch(part):
                continue
            expanded = _expand(part)
            if "$" in expanded:
                return "deny", (f"Archivist policy: the {role} can't run `{toks[0]}` with a shell variable the guard "
                                f"can't expand ({part}); it might point into the vault. Use the literal path.")
            try:
                if _inside((cwd / expanded).resolve(), root):
                    return deny
            except (OSError, RuntimeError, ValueError):
                continue
    return None


def check(command: str, vw, cfg, depth: int = 0, role: str | None = None, cwd: Path | None = None,
          writes: list[str] | None = None) -> tuple[str, str] | None:
    """The decision for `command`; `writes` collects the vault paths its `obsidian` calls write."""
    root = cfg["root"] if cfg else None
    cwd = cwd or Path.cwd()
    command = strip_quoted_heredocs(command)
    # Command substitution runs a command the guard can't see whole. Checked on the text, because
    # shlex splits an unquoted `$(` into separate tokens.
    if role and root and ("$(" in command or "`" in command):
        return "deny", (f"Archivist policy: the {role} can't use $(…) or backticks; the guard can't check "
                        "the command they run. Run it as its own command (note text in a quoted <<'EOF' heredoc is fine).")
    for raw in segments(command):
        toks = unwrap(raw)
        if role and root:
            for t in raw:  # an inline or exported ARCHIVIST_ROLE would change vault-write's role
                if t.startswith("ARCHIVIST_ROLE=") and t.split("=", 1)[1] not in ("", role):
                    return "deny", f"Archivist policy: the {role} can't set {t}."
        if not toks:
            continue
        prog = os.path.basename(toks[0])
        if prog in SHELLS and "-c" in toks[1:-1] and depth < 3:
            decision = check(toks[toks.index("-c") + 1], vw, cfg, depth + 1, role, cwd, writes)
        elif prog == "eval" and depth < 3:
            decision = check(" ".join(toks[1:]), vw, cfg, depth + 1, role, cwd, writes)
        elif prog.lower() in OBSIDIAN:
            decision = check_obsidian(toks[1:], vw, cfg, role)
            if writes is not None and not (decision and decision[0] == "deny"):
                writes += cli_targets(toks[1:], vw, cfg)
        elif role and root and prog in ("cd", "pushd"):
            target = toks[1] if len(toks) > 1 else "~"
            cwd = (cwd / _expand(target)).resolve()  # later segments run there
            decision = None
        elif role and root and plugin_program(toks, cwd):
            decision = check_role_flag(toks, role)
        elif role and root:
            decision = check_role_shell(toks, role, cwd, root)
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
    role = ROLES.get(payload.get("agent_type") or "")
    if not role and "obsidian" not in command and not any(w in command for w in ("rm", "mv")):
        return 0
    vw, cfg = load_vault_write()
    cwd = Path(payload["cwd"]).expanduser().resolve() if payload.get("cwd") else None
    writes: list[str] = []
    decision = check(command, vw, cfg, role=role, cwd=cwd, writes=writes)
    if cfg and writes and not (decision and decision[0] == "deny"):
        record_cli_writes(writes, vw, cfg)  # an "ask" the user declines leaves an entry; the audit errs lenient there
    if decision:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision[0],
            "permissionDecisionReason": decision[1],
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
