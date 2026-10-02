#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
#MISE description="Copy an OpenRig library starter into a project as a Claude-only rig spec"
#USAGE arg "<starter>" help="Library rig name, e.g. first-project or conveyor (rig specs ls)"
#USAGE arg "<dest>" help="Directory to write rig.yaml into, e.g. <repo>/openrig-specs/<rig-name>"
#USAGE arg "<rig_name>" help="Name for the new rig (no dots)"
#USAGE flag "--dry-run" help="Print the changes without writing"
"""Copy an OpenRig library rig spec into a project as a Claude-Code-only spec.

Usage: mise run openrig:convert <library-rig> <dest-dir> <rig-name> [--dry-run]

  - copies the starter's directory (rig.yaml, CULTURE.md, docs) to <dest-dir>
  - rewrites relative `local:` agent_refs to absolute `path:` refs, so the
    library AgentSpecs still resolve from the new location
  - sets `runtime: codex` members to `runtime: claude-code` and drops their
    `model:` line (built-in Claude seats leave the model to the harness)
  - sets `name:` to <rig-name>
  - points `cwd: "."` at the git repo containing <dest-dir> (member cwd
    resolves against the spec's directory, not where `rig up` runs)

Then: rig up <dest-dir>/rig.yaml --plan
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def library_spec_path(name: str) -> Path:
    out = subprocess.run(["rig", "specs", "show", name], capture_output=True, text=True)
    m = re.search(r"^Path:\s+(\S+)", out.stdout, re.M)
    if out.returncode or not m:
        sys.exit(f"rig specs show {name} failed:\n{out.stdout}{out.stderr}")
    return Path(m.group(1))


def repo_cwd(dest: Path) -> str:
    """Relative path from dest to its git repo root, or "." outside a repo."""
    probe = dest
    while not probe.exists():
        probe = probe.parent
    out = subprocess.run(["git", "-C", str(probe), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True)
    if out.returncode:
        return "."
    return os.path.relpath(out.stdout.strip(), dest)


def convert(text: str, src_dir: Path, rig_name: str, cwd: str) -> tuple[str, list[str]]:
    changes, out = [], []
    lines = text.splitlines(keepends=True)
    in_codex_member = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- id:"):
            in_codex_member = False
        if re.match(r"^name:\s", line):
            line = f"name: {rig_name}\n"
            changes.append(f"name -> {rig_name}")
        m = re.match(r'^(\s*agent_ref:\s*)"?local:([^"\s]+)"?\s*$', line)
        if m:
            abs_ref = (src_dir / m.group(2)).resolve()
            line = f'{m.group(1)}"path:{abs_ref}"\n'
            changes.append(f"agent_ref local:{m.group(2)} -> path:{abs_ref}")
        m = re.match(r'^(\s*cwd:\s*)"\."\s*$', line)
        if m and cwd != ".":
            line = f'{m.group(1)}"{cwd}"\n'
            changes.append(f'cwd "." -> "{cwd}"')
        if re.match(r"^\s*runtime:\s*codex\s*$", line):
            line = line.replace("codex", "claude-code")
            in_codex_member = True
            changes.append("runtime codex -> claude-code")
        if in_codex_member and re.match(r"^\s*model:\s", line):
            changes.append(f"dropped {stripped}")
            continue
        out.append(line)
    return "".join(out), changes


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry = "--dry-run" in sys.argv
    if len(args) != 3:
        sys.exit(__doc__)
    # Under mise the task runs elsewhere; resolve a relative dest where it was invoked.
    base = Path(os.environ.get("MISE_ORIGINAL_CWD", "."))
    starter, dest, rig_name = args[0], (base / args[1]).resolve(), args[2]
    if "." in rig_name:
        sys.exit("rig name must not contain dots")
    spec = library_spec_path(starter)
    src_dir = spec.parent
    if (dest / "rig.yaml").exists():
        sys.exit(f"{dest}/rig.yaml exists; not overwriting")
    text, changes = convert(spec.read_text(), src_dir, rig_name, repo_cwd(dest))
    print(f"from {spec}")
    for c in changes:
        print(f"  {c}")
    if dry:
        print("(dry run; nothing written)")
        return
    shutil.copytree(src_dir, dest, dirs_exist_ok=True)
    (dest / "rig.yaml").write_text(text)
    print(f"wrote {dest}/rig.yaml\nnext: rig up {dest}/rig.yaml --plan")


if __name__ == "__main__":
    main()
