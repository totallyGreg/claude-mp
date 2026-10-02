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
#USAGE flag "--pi <mode>" help="How the coder runs Pi: terminal (default) or native (OpenRig's pi runtime)"
#USAGE flag "--dry-run" help="Show what would be created without writing anything"
"""Scaffold an OpenRig rig into a git repo.

Writes <repo>/openrig-specs/<prefix>-<shape>/ (rig.yaml + seat briefs), creates
the coder's worktree at <repo>/.worktrees/<rig> on experiment/<rig>-<date>, and
validates with `rig up --plan`. Boot it with `rig up <spec>`.

Shapes:
  claude-pi  dev-lead (Claude Code, cwd = the rig folder) delegates to dev-coder
             (Pi on oMLX) by rig send
  pi-solo    dev-coder (Pi on oMLX) alone; the human gives it tasks directly

Pi modes (--pi):
  terminal   a terminal seat whose send_text launches `pi --append-system-prompt <brief>`;
             Pi uses your ~/.pi/agent config and extensions
  native     OpenRig's pi runtime: it tracks Pi's state, session and restore. Pi
             gets a per-seat agent dir, so this links your models.json into it;
             the brief ships as a slim AgentSpec (agents/pi-coder) merged into
             AGENTS.md in the worktree. Your Pi extensions are not loaded.

The things this gets right that hand-written specs got wrong: member cwd is
relative to the spec's directory; a Claude seat must not share a cwd with your
own sessions (OpenRig takes over its status line, hooks and CLAUDE.md); a terminal seat's send_text must launch Pi,
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
PI_MODES = ("terminal", "native")
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


def native_member(member_id: str, label: str, cwd: str, tier: str) -> str:
    return f"""      - id: {member_id}
        label: {label}
        agent_ref: "local:agents/pi-coder"
        profile: default
        runtime: pi
        model: omlx/{tier}
        cwd: "{cwd}"
"""


PI_CODER_AGENT = """name: pi-coder
version: "1.0"
description: Slim Pi coder; its brief is merged into AGENTS.md in the seat's cwd

profiles:
  default:
    uses:
      skills: []
      guidance: [brief]
      subagents: []
      plugins: []
      runtime_resources: []

resources:
  guidance:
    - id: brief
      path: brief.md

startup:
  files:
    - path: brief.md
      delivery_hint: guidance_merge
      required: true
  actions: []
"""


def coder(pi: str, tier: str, wt_rel: str, brief_text: str, spec_dir: Path, kick: str) -> tuple[str, dict[str, str]]:
    """The coder member's YAML and the brief files it needs, for either Pi mode."""
    label = f"Coder (Pi omlx/{tier}{', native' if pi == 'native' else ''})"
    if pi == "native":
        return native_member("coder", label, wt_rel, tier), {
            "agents/pi-coder/agent.yaml": PI_CODER_AGENT,
            "agents/pi-coder/brief.md": brief_text,
        }
    return (terminal_member("coder", label, wt_rel, pi_command(tier, spec_dir / "coder-brief.md", kick)),
            {"coder-brief.md": brief_text})


def render(shape: str, rig: str, repo: Path, spec_dir: Path, worktree: Path, branch: str, tier: str, pi: str) -> dict[str, str]:
    wt_rel = f"../../.worktrees/{worktree.name}"
    head = f'version: "0.2"\nname: {rig}\npermission_policy: builtin:standard\n'
    if shape == "claude-pi":
        lead_brief = spec_dir / "lead-brief.md"
        coder_yaml, coder_files = coder(pi, tier, wt_rel, f"""# OpenRig seat: dev-coder@{rig}

You are the coder seat in the OpenRig rig `{rig}`, running on a local model.
Your lead is `dev-lead@{rig}`.

- Tasks arrive as typed messages from the lead. Act only on those.
- Work only inside your current directory (a git worktree on `{branch}`). Use
  relative paths. Never touch the main checkout at {repo}.
- Change only what the task asks. Don't commit; the lead reviews `git diff`.
- When a task is done or blocked, report with your bash tool, one command:
  `rig send dev-lead@{rig} "<what you changed, files touched, anything unverified>"`
  A task isn't finished until that command succeeds.
""", spec_dir, "Wait for tasks from the lead.")
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
        # The rig's own folder, not the repo root: OpenRig writes its status
        # line, hooks, settings and CLAUDE.md blocks into the lead's cwd.
        cwd: "."
        startup:
          actions:
            - type: send_text
              value: "Read {lead_brief} and follow it. Then wait for the human's goal."
              phase: after_ready
              applies_on: [fresh_start]
              idempotent: true
""" + coder_yaml + """    edges:
      - kind: delegates_to
        from: lead
        to: coder

edges: []
"""
        files = {
            "rig.yaml": spec,
            "lead-brief.md": f"""# OpenRig seat: dev-lead@{rig}

You lead the OpenRig rig `{rig}` for {repo.name}. You start in the rig's own
folder ({spec_dir}); the repo is {repo} — use absolute paths or `git -C {repo}`.
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
            **coder_files,
        }
    else:
        coder_yaml, coder_files = coder(pi, tier, wt_rel, f"""# OpenRig seat: dev-coder@{rig}

You are the only seat in the OpenRig rig `{rig}`, running on a local model.
The human gives you tasks directly in this terminal.

- Work only inside your current directory (a git worktree on `{branch}`). Use
  relative paths. Never touch the main checkout at {repo}.
- Change only what the task asks. Don't commit; the human reviews `git diff`.
- End each task with: what you changed, the files touched, how you verified
  it, and anything you couldn't verify.
""", spec_dir, "Wait for the human's first task.")
        spec = head + f"""summary: >
  {repo.name}: one Pi coder (omlx/{tier}) in the worktree {worktree.name};
  the human gives it tasks directly.

pods:
  - id: dev
    label: {repo.name}
    members:
""" + coder_yaml + """    edges: []

edges: []
"""
        files = {"rig.yaml": spec, **coder_files}
    return files


def link_pi_models(session: str) -> Path:
    """Native pi seats run with PI_CODING_AGENT_DIR=<OPENRIG_HOME>/state/pi/<seat>/agent,
    which has no models.json, so `omlx/<tier>` wouldn't resolve. OpenRig has no
    resource for it; link the user's models.json in (the runner only mkdirs)."""
    openrig_home = Path(os.environ.get("OPENRIG_HOME", Path.home() / ".openrig"))
    pi_dir = Path(os.path.expanduser(os.environ.get("PI_CODING_AGENT_DIR", "~/.pi/agent")))
    link = openrig_home / "state" / "pi" / session / "agent" / "models.json"
    link.parent.mkdir(parents=True, exist_ok=True)
    if not link.is_symlink():
        link.unlink(missing_ok=True)
        link.symlink_to(pi_dir / "models.json")
    return link


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("shape", choices=SHAPES)
    p.add_argument("project", nargs="?", default=os.environ.get("MISE_ORIGINAL_CWD", "."))
    p.add_argument("--prefix")
    p.add_argument("--tier", choices=TIERS, default="code")
    p.add_argument("--pi", choices=PI_MODES, default="terminal")
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
    files = render(a.shape, rig, repo, spec_dir, worktree, branch, a.tier, a.pi)

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
        (spec_dir / name).parent.mkdir(parents=True, exist_ok=True)
        (spec_dir / name).write_text(text)
    if a.pi == "native":
        print(f"linked    {link_pi_models(f'dev-coder@{rig}')} -> your Pi models.json")
    if a.shape == "claude-pi":
        # The lead works from the rig folder; let it read and edit the repo.
        # OpenRig merges its own keys into this file and keeps ours.
        settings = spec_dir / ".claude" / "settings.local.json"
        settings.parent.mkdir(exist_ok=True)
        settings.write_text(json.dumps({"permissions": {"additionalDirectories": [str(repo)]}}, indent=2) + "\n")
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
