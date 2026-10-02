#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
#MISE description="Scaffold an OpenRig rig in a repo: claude-pi or pi-solo, worktree + briefs"
#USAGE arg "<shape>" help="claude-pi (Claude lead + Pi coder) or pi-solo (one Pi coder)"
#USAGE arg "[project]" help="Git repo to scaffold into (default: where mise run was invoked)"
#USAGE flag "--prefix <prefix>" help="Rig name prefix (default: the repo's directory name)"
#USAGE flag "--tier <tier>" help="Pi tier for the coder: fast, code (default) or deep"
#USAGE flag "--dry-run" help="Show what would be created without writing anything"
"""Scaffold an OpenRig rig into a git repo.

Writes <repo>/openrig-specs/<prefix>-<shape>/ (rig.yaml + seat briefs), creates
the coder's worktree at <repo>/.worktrees/<rig> on experiment/<rig>-<date>, and
validates with `rig up --plan`. Boot it with `rig up <spec>`.

Shapes:
  claude-pi  dev-lead (Claude Code) delegates to dev-coder (Pi on oMLX) by rig send
  pi-solo    dev-coder (Pi on oMLX) alone; the human gives it tasks directly

The things this gets right that hand-written specs got wrong: member cwd is
relative to the spec's directory; a terminal seat's send_text must launch Pi,
not be prose; rig names must be unique; seat addresses in the briefs must
match the rig name.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SHAPES = ("claude-pi", "pi-solo")
TIERS = ("fast", "code", "deep")
ORCHESTRATOR_REF = "path:/opt/homebrew/lib/node_modules/@openrig/cli/daemon/specs/agents/orchestration/orchestrator"


def run(*cmd: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def existing_rig_names() -> set[str]:
    names = set()
    for extra in ([], ["--filter", "status=stopped"]):
        out = run("rig", "ps", "--json", *extra)
        if out.returncode:
            continue
        data = json.loads(out.stdout or "[]")
        names |= {r["name"] for r in (data["entries"] if isinstance(data, dict) else data)}
    return names


def pi_command(tier: str, brief: Path, kick: str) -> str:
    return f'pi --model omlx/{tier} --append-system-prompt {brief} "{kick}"'


def terminal_member(member_id: str, label: str, cwd: str, command: str) -> str:
    command = command.replace("'", "''")  # YAML single-quoted scalar escape
    return f"""      - id: {member_id}
        label: {label}
        agent_ref: "builtin:terminal"
        runtime: terminal
        profile: none
        cwd: "{cwd}"
        startup:
          actions:
            # Terminal seat: this is typed into a shell, so it must launch Pi.
            - type: send_text
              value: '{command}'
              phase: after_ready
              applies_on: [fresh_start]
              idempotent: true
"""


def render(shape: str, rig: str, repo: Path, spec_dir: Path, worktree: Path, branch: str, tier: str) -> dict[str, str]:
    wt_rel = f"../../.worktrees/{worktree.name}"
    coder_brief = spec_dir / "coder-brief.md"
    head = f'version: "0.2"\nname: {rig}\npermission_policy: builtin:standard\n'
    if shape == "claude-pi":
        lead_brief = spec_dir / "lead-brief.md"
        spec = head + f"""summary: >
  {repo.name}: Claude Code lead delegates exact tasks to a Pi coder
  (omlx/{tier}) in the worktree {worktree.name}.

pods:
  - id: dev
    label: {repo.name}
    members:
      - id: lead
        label: Lead (Claude Code)
        agent_ref: "{ORCHESTRATOR_REF}"
        runtime: claude-code
        profile: default
        cwd: "../.."
        startup:
          actions:
            - type: send_text
              value: "Read {lead_brief} and follow it. Then wait for the human's goal."
              phase: after_ready
              applies_on: [fresh_start]
              idempotent: true
""" + terminal_member("coder", f"Coder (Pi omlx/{tier})", wt_rel,
                      pi_command(tier, coder_brief, "Wait for tasks from the lead.")) + """    edges:
      - kind: delegates_to
        from: lead
        to: coder

edges: []
"""
        files = {
            "rig.yaml": spec,
            "lead-brief.md": f"""# OpenRig seat: dev-lead@{rig}

You lead the OpenRig rig `{rig}` for {repo.name} ({repo}).
Your coder is `dev-coder@{rig}`: Pi on a local model (omlx/{tier}), working in
the git worktree {worktree} on branch `{branch}`.

- The human gives you goals. Turn them into small, exact tasks: which files,
  what change, how to verify it.
- Delegate one task at a time:
  `rig send dev-coder@{rig} "<task>" --verify`
- The coder reports back to you with `rig send`. Then review its work with
  `git -C {worktree} diff` and run the project's checks in the worktree.
  A local model is wrong more often than you are; verify before accepting.
- Don't edit files in the worktree yourself. Send a corrected task instead.
- Nothing is committed or merged without the human's go-ahead.
""",
            "coder-brief.md": f"""# OpenRig seat: dev-coder@{rig}

You are the coder seat in the OpenRig rig `{rig}`, running on a local model.
Your lead is `dev-lead@{rig}`.

- Tasks arrive as typed messages from the lead. Act only on those.
- Work only inside your current directory (a git worktree on `{branch}`). Use
  relative paths. Never touch the main checkout at {repo}.
- Change only what the task asks. Don't commit; the lead reviews `git diff`.
- When a task is done or blocked, report with your bash tool, one command:
  `rig send dev-lead@{rig} "<what you changed, files touched, anything unverified>"`
  A task isn't finished until that command succeeds.
""",
        }
    else:
        spec = head + f"""summary: >
  {repo.name}: one Pi coder (omlx/{tier}) in the worktree {worktree.name};
  the human gives it tasks directly.

pods:
  - id: dev
    label: {repo.name}
    members:
""" + terminal_member("coder", f"Coder (Pi omlx/{tier})", wt_rel,
                      pi_command(tier, coder_brief, "Wait for the human's first task.")) + """    edges: []

edges: []
"""
        files = {
            "rig.yaml": spec,
            "coder-brief.md": f"""# OpenRig seat: dev-coder@{rig}

You are the only seat in the OpenRig rig `{rig}`, running on a local model.
The human gives you tasks directly in this terminal.

- Work only inside your current directory (a git worktree on `{branch}`). Use
  relative paths. Never touch the main checkout at {repo}.
- Change only what the task asks. Don't commit; the human reviews `git diff`.
- End each task with: what you changed, the files touched, how you verified
  it, and anything you couldn't verify.
""",
        }
    return files


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("shape", choices=SHAPES)
    p.add_argument("project", nargs="?", default=os.environ.get("MISE_ORIGINAL_CWD", "."))
    p.add_argument("--prefix")
    p.add_argument("--tier", choices=TIERS, default="code")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    top = run("git", "rev-parse", "--show-toplevel", cwd=Path(a.project).resolve())
    if top.returncode:
        sys.exit(f"{a.project} is not inside a git repo")
    repo = Path(top.stdout.strip())
    prefix = (a.prefix or repo.name).lower()
    rig = f"{prefix}-{a.shape}"
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", rig):
        sys.exit(f"rig name {rig!r} must be lowercase letters, digits and dashes (no dots)")
    if rig in existing_rig_names():
        sys.exit(f"a rig named {rig} already exists (rig ps --filter status=stopped); "
                 f"archive it (rig archive <rigId>) or pick another --prefix")
    spec_dir = repo / "openrig-specs" / rig
    if (spec_dir / "rig.yaml").exists():
        sys.exit(f"{spec_dir}/rig.yaml exists; not overwriting")
    worktree = repo / ".worktrees" / rig
    branch = f"experiment/{rig}-{datetime.date.today():%Y-%m-%d}"
    files = render(a.shape, rig, repo, spec_dir, worktree, branch, a.tier)

    print(f"rig       {rig}")
    print(f"spec      {spec_dir}/  ({', '.join(files)})")
    print(f"worktree  {worktree}  ({'exists, reused' if worktree.exists() else 'new, branch ' + branch})")
    if a.dry_run:
        print("(dry run; nothing written)")
        return

    if not worktree.exists():
        has_branch = run("git", "rev-parse", "--verify", "--quiet", branch, cwd=repo).returncode == 0
        add = ["git", "worktree", "add", str(worktree)] + ([branch] if has_branch else ["-b", branch])
        out = run(*add, cwd=repo)
        if out.returncode:
            sys.exit(f"git worktree add failed:\n{out.stderr}")
    # A worktree inside the repo shows up as untracked unless it's ignored.
    if run("git", "check-ignore", "-q", ".worktrees/x", cwd=repo).returncode:
        exclude = Path(run("git", "rev-parse", "--path-format=absolute", "--git-common-dir", cwd=repo).stdout.strip()) / "info" / "exclude"
        with exclude.open("a") as f:
            f.write("\n.worktrees/\n")
        print(f"added .worktrees/ to {exclude}")

    spec_dir.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (spec_dir / name).write_text(text)
    print(f"wrote     {spec_dir}/")

    plan = run("rig", "up", str(spec_dir / "rig.yaml"), "--plan")
    print("\n" + (plan.stdout + plan.stderr).strip())
    if plan.returncode:
        sys.exit("rig up --plan failed; fix the spec before booting")
    if run("git", "check-ignore", "-q", f"openrig-specs/{rig}/rig.yaml", cwd=repo).returncode:
        print("\nnote: openrig-specs/ is tracked by git here; commit it, or add it to .git/info/exclude")
    print(f"\nnext: mise run openrig:check {repo}\n      rig up {spec_dir / 'rig.yaml'}")


if __name__ == "__main__":
    main()
