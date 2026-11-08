#!/usr/bin/env python3
"""PreToolUse hook: an agent stages files by name, never all at once.

`git add .`, `-A` and `-u` (and `git commit -a`, which is `-u`) sweep in
whatever else is in the tree — a scratch file, another session's half-done
edit, a regenerated artifact. The rule was marked IMPORTANT in prose and
enforced by nothing; this makes it hold.

Reads the hook payload on stdin; exits 2 (blocking, with the reason on
stderr) when a Bash command stages or commits without naming files. Any
other failure exits 0: a broken hook must not block work.
Standard library only, and Python 3.9-safe: it runs on every Bash call.
"""

import json
import re
import shlex
import sys

AT_COMMAND = r"(?:^|[;&|(]\s*|\$\(\s*|\b(?:do|then|else|exec|time)\s+)(?:\w+=\S*\s+)*"
# git's own options before the verb: -C <dir>, -c <key=value>, --no-pager …
GIT = re.compile(AT_COMMAND + r"(?:rtk\s+)?git\s+(?:-[Cc]\s+\S+\s+|--[\w-]+(?:=\S+)?\s+)*(add|commit)\b([^;&|\n]*)")
BLANKET_ADD = {".", "./", ":/", "*", "-A", "--all", "-u", "--update"}
# Short options of `git commit` that take a value: what follows them in a
# cluster is that value, not more flags (`-m"a fix"`).
COMMIT_VALUED = set("mFCct")


def blanket(verb, args):
    try:
        tokens = shlex.split(args)
    except ValueError:
        tokens = args.split()
    for token in tokens:
        if token == "--":
            continue
        if verb == "add" and (token in BLANKET_ADD or re.fullmatch(r"-[a-zA-Z]*[Au][a-zA-Z]*", token)):
            return True
        if verb == "commit":
            if token == "--all":
                return True
            if re.fullmatch(r"-[a-zA-Z].*", token):
                for flag in token[1:]:
                    if flag == "a":
                        return True
                    if flag in COMMIT_VALUED:
                        break
    return False


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    command = (payload.get("tool_input") or {}).get("command", "")
    if payload.get("tool_name") == "Bash" and any(blanket(m.group(1), m.group(2)) for m in GIT.finditer(command)):
        print(
            "Blocked: stage files by name — never `git add .`, `-A`, `-u`, or `git commit -a`. "
            "`git status --short` lists what changed; `git add <file> <file>` the ones this change owns.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
