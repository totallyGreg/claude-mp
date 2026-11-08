#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""devloop: the loop's one entry point, run from the plugin, configured by loop.toml.

    devloop.py check [--only NAME …]     the gate's checks (exit 1 on any failure)
    devloop.py capture <text>            a line into INBOX § Open, committed alone
    devloop.py rank                      the ranked "what next"
    devloop.py nudge                     due reviews and evals (session start; exit 0 always)
    devloop.py review-needed <base> <tip>   exit 0 and the reasons when a review is due
    devloop.py review [<base> <tip>]     an independent read-only review of the branch
    devloop.py commit-msg <file>         the commit-msg hook's review gate
    devloop.py evals [<id> …]            replay past fixes under today's configuration (slow)
    devloop.py init …                    write loop.toml and the documents (see init --help)

Global: --root <repo> (default: the enclosing git repository) and
--config <loop.toml> (default: <root>/loop.toml, or $DEVLOOP_CONFIG), which
lets the checks read a repository they must not write to.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402

CORE = ("docs", "loop")
SOFTWARE = ("red-first", "backlog-closed")


def cmd_check(cfg: config.Config, only: list[str]) -> int:
    import check_docs
    import check_loop
    import software

    checks = {"docs": check_docs.check, "loop": check_loop.check,
              "red-first": software.red_first, "backlog-closed": software.backlog_closed}
    names = list(CORE) + (list(SOFTWARE) if cfg.software else [])
    if only:
        unknown = [n for n in only if n not in checks]
        if unknown:
            print(f"check: unknown check {', '.join(unknown)} — known: {', '.join(checks)}", file=sys.stderr)
            return 2
        names = only
    total = 0
    for i, name in enumerate(names, 1):
        print(f"[{i}/{len(names)}] {name}")
        for failure in checks[name](cfg):
            print(f"  FAIL  {failure}")
            total += 1
    print(f"\n{total} failure(s)." if total else "\nAll devloop checks passed.")
    return 1 if total else 0


def cmd_rank(cfg: config.Config) -> int:
    import ranking

    if cfg.tier < 1:
        print("rank: tier 0 has no BACKLOG or PLAN to rank")
        return 0
    read = lambda rel: (cfg.root / rel).read_text(encoding="utf-8") if (cfg.root / rel).is_file() else None  # noqa: E731
    backlog, plan = read(cfg.docname("backlog")) or "", read(cfg.docname("plan")) or ""
    cap = cfg["docs"]["caps"].get(cfg.docname("backlog"), cfg["docs"]["cap_bytes"])
    pressed = ranking.under_pressure(backlog, cap, cfg["loop"]["backlog_pressure"])
    ranked = ranking.candidates(plan, backlog, read, stages_dir=cfg["docs"]["stages_dir"],
                                cap=cap, pressure=cfg["loop"]["backlog_pressure"])
    if pressed:
        print(f"(under pressure: {cfg.docname('backlog')} is near its cap, so groups with bugs lead)")
    for n, c in enumerate(ranked, 1):
        extra = f" — step {c.step.number}: {c.step.title}" if c.step else \
            (f" — {c.bugs} bug(s), {c.items} item(s)" if c.kind == "group" else "")
        print(f"{n:2}. {c.priority} {c.kind:5} {c.key}{'' if c.key == c.title else ' — ' + c.title}{extra}")
    if not ranked:
        print("Nothing queued: PLAN and BACKLOG § Work are empty.")
    return 0


def cmd_nudge(args) -> int:
    """Session start: point git at this plugin, then say what is due. Never fails."""
    try:
        if not config.exists(args.root):
            return 0
        cfg = config.load(args.root, args.config)
        import subprocess

        here = str(Path(__file__).resolve().parents[3])
        subprocess.run(["git", "-C", str(cfg.root), "config", "devloop.root", here], capture_output=True)
        import nudges

        for message in nudges.messages(cfg):
            print(message)
    except Exception as error:  # a hook must never fail a session start
        print(f"devloop nudge: {error}", file=sys.stderr)
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="devloop", description=__doc__.split("\n")[0])
    parser.add_argument("--root", type=Path)
    parser.add_argument("--config", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check")
    p.add_argument("--only", nargs="+", default=[])
    p = sub.add_parser("capture")
    p.add_argument("text", nargs="*")
    sub.add_parser("rank")
    sub.add_parser("nudge")
    p = sub.add_parser("review-needed")
    p.add_argument("base")
    p.add_argument("tip")
    p = sub.add_parser("review")
    p.add_argument("base", nargs="?")
    p.add_argument("tip", nargs="?")
    p = sub.add_parser("commit-msg")
    p.add_argument("file")
    p = sub.add_parser("evals")
    p.add_argument("ids", nargs="*")
    p = sub.add_parser("init")
    import init

    init.arguments(p)
    args = parser.parse_args(argv)

    if args.command == "nudge":
        return cmd_nudge(args)
    if args.command == "init":
        return init.run(args)
    try:
        cfg = config.load(args.root, args.config)
    except config.ConfigError as error:
        if args.command == "commit-msg":
            print(f"devloop commit-msg: {error}; review gate not checked", file=sys.stderr)
            return 0
        print(f"devloop: {error}", file=sys.stderr)
        return 2

    if args.command == "check":
        return cmd_check(cfg, args.only)
    if args.command == "capture":
        import capture

        text = " ".join(args.text) if args.text else sys.stdin.read()
        return capture.capture(cfg, text)
    if args.command == "rank":
        return cmd_rank(cfg)
    import software

    if args.command == "review-needed":
        due = software.review_reasons(cfg, args.base, args.tip)
        print("\n".join(due) if due else "No review needed.")
        return 0 if due else 1
    if args.command == "review":
        return software.review(cfg, args.base, args.tip)
    if args.command == "commit-msg":
        return software.commit_msg(cfg, args.file)
    if args.command == "evals":
        import evals

        return evals.run(cfg, args.ids)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
