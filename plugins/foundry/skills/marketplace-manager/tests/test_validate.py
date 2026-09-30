#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pytest>=7.0",
# ]
# ///
"""Tests for repo/validate.py version-bump enforcement.

Each test builds a throwaway git repo with a marketplace on `main`, branches
off it, and checks what check_versions() reports against the merge-base.

Run: uv run --with pytest pytest plugins/foundry/skills/marketplace-manager/tests
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "repo"))

from validate import (  # noqa: E402
    Snapshot,
    _parse_frontmatter_stdlib,
    check_duplicate_metadata,
    check_versions,
    resolve_base,
    skill_version,
)

SKILL_MD = """---
name: {name}
description: >-
  Use when testing: a description with a colon.
metadata:
  version: "{version}"
---

# {name}

{body}
"""


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def write(repo: Path, rel: str, text: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def set_plugin_version(repo: Path, version: str, description: str = "Demo plugin") -> None:
    write(repo, "plugins/demo/.claude-plugin/plugin.json",
          json.dumps({"name": "demo", "version": version, "description": description}))


def set_skill(repo: Path, version: str, body: str = "Body.") -> None:
    write(repo, "plugins/demo/skills/alpha/SKILL.md",
          SKILL_MD.format(name="alpha", version=version, body=body))


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A marketplace with one plugin (demo 1.0.0, skill alpha 1.0.0) on main,
    checked out on branch 'work'."""
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "commit.gpgsign", "false")
    write(tmp_path, ".claude-plugin/marketplace.json", json.dumps({
        "name": "test-mp", "owner": {"name": "T"},
        "plugins": [{"name": "demo", "source": "./plugins/demo"}],
    }))
    set_plugin_version(tmp_path, "1.0.0")
    set_skill(tmp_path, "1.0.0")
    write(tmp_path, "plugins/demo/commands/run.md", "Run it.\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "init")
    git(tmp_path, "checkout", "-qb", "work")
    return tmp_path


def config(repo: Path) -> dict:
    return json.loads((repo / ".claude-plugin/marketplace.json").read_text())


def errors(repo: Path, staged: bool = False) -> list[str]:
    base = resolve_base(repo, "main")
    errs, _ = check_versions(config(repo), Snapshot(repo, base, staged=staged))
    return errs


def commit_all(repo: Path, msg: str = "change") -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", msg)


# -- Plugin rule -------------------------------------------------------------

def test_no_changes_passes(repo):
    assert errors(repo) == []


def test_plugin_change_without_bump_fails(repo):
    write(repo, "plugins/demo/commands/run.md", "Run it faster.\n")
    errs = errors(repo)
    assert len(errs) == 1
    assert "Plugin 'demo'" in errs[0] and "not greater than 1.0.0" in errs[0]


def test_plugin_change_with_bump_passes(repo):
    write(repo, "plugins/demo/commands/run.md", "Run it faster.\n")
    set_plugin_version(repo, "1.0.1")
    assert errors(repo) == []


def test_later_commits_on_bumped_branch_pass(repo):
    write(repo, "plugins/demo/commands/run.md", "v2\n")
    set_plugin_version(repo, "1.1.0")
    commit_all(repo)
    write(repo, "plugins/demo/commands/run.md", "v3\n")
    assert errors(repo) == []


def test_version_decrease_fails(repo):
    write(repo, "plugins/demo/commands/run.md", "x\n")
    set_plugin_version(repo, "0.9.0")
    assert "not greater" in errors(repo)[0]


def test_non_semver_fails(repo):
    write(repo, "plugins/demo/commands/run.md", "x\n")
    set_plugin_version(repo, "next")
    assert "not MAJOR.MINOR.PATCH" in errors(repo)[0]


def test_changes_outside_plugins_are_ignored(repo):
    write(repo, "README.md", "docs\n")
    assert errors(repo) == []


def test_changed_plugin_with_long_description_fails(repo):
    set_plugin_version(repo, "1.0.1", description="x" * 201)
    errs = errors(repo)
    assert len(errs) == 1 and "description is 201 characters" in errs[0]


def test_unchanged_plugin_with_long_description_is_not_checked(repo):
    set_plugin_version(repo, "1.0.0", description="x" * 300)
    commit_all(repo)
    git(repo, "branch", "-f", "main", "HEAD")  # long description is already on main
    write(repo, "README.md", "unrelated\n")
    assert errors(repo) == []


# -- Skill rule --------------------------------------------------------------

def test_skill_change_requires_skill_and_plugin_bump(repo):
    set_skill(repo, "1.0.0", body="New body.")
    errs = errors(repo)
    assert any("Plugin 'demo'" in e for e in errs)
    assert any("Skill 'demo:alpha'" in e for e in errs)


def test_skill_bump_alone_still_requires_plugin_bump(repo):
    set_skill(repo, "1.1.0", body="New body.")
    errs = errors(repo)
    assert len(errs) == 1 and "Plugin 'demo'" in errs[0]


def test_skill_file_change_requires_skill_bump(repo):
    write(repo, "plugins/demo/skills/alpha/references/guide.md", "ref\n")
    set_plugin_version(repo, "1.0.1")
    errs = errors(repo)
    assert len(errs) == 1 and "Skill 'demo:alpha'" in errs[0]


def test_skill_and_plugin_bumped_passes(repo):
    set_skill(repo, "1.1.0", body="New body.")
    set_plugin_version(repo, "1.1.0")
    assert errors(repo) == []


def test_new_skill_with_version_passes(repo):
    write(repo, "plugins/demo/skills/beta/SKILL.md",
          SKILL_MD.format(name="beta", version="0.1.0", body="b"))
    set_plugin_version(repo, "1.1.0")
    assert errors(repo) == []


def test_new_skill_without_version_fails(repo):
    write(repo, "plugins/demo/skills/beta/SKILL.md", "---\nname: beta\n---\n")
    set_plugin_version(repo, "1.1.0")
    assert "no version" in errors(repo)[0]


def test_removed_skill_only_requires_plugin_bump(repo):
    git(repo, "rm", "-rq", "plugins/demo/skills/alpha")
    set_plugin_version(repo, "2.0.0")
    assert errors(repo) == []


# -- Staged mode -------------------------------------------------------------

def test_staged_mode_ignores_unstaged_bump(repo):
    write(repo, "plugins/demo/commands/run.md", "x\n")
    git(repo, "add", "plugins/demo/commands/run.md")
    set_plugin_version(repo, "1.0.1")  # bumped on disk but not staged
    assert "Plugin 'demo'" in errors(repo, staged=True)[0]
    git(repo, "add", "plugins/demo/.claude-plugin/plugin.json")
    assert errors(repo, staged=True) == []


def test_merging_main_moves_the_base(repo):
    # main gets a release of demo 1.1.0 while 'work' is open
    git(repo, "checkout", "-q", "main")
    write(repo, "plugins/demo/commands/run.md", "main change\n")
    set_plugin_version(repo, "1.1.0")
    commit_all(repo, "release on main")
    git(repo, "checkout", "-q", "work")
    git(repo, "merge", "-q", "--no-edit", "main")
    assert errors(repo) == []  # main's release isn't this branch's change


# -- Manifest and parsing ----------------------------------------------------

def test_entry_version_is_rejected():
    cfg = {"plugins": [{"name": "demo", "source": "./plugins/demo", "version": "1.0.0"}]}
    assert "remove 'version'" in check_duplicate_metadata(cfg)[0]


def test_stdlib_parser_reads_metadata_version():
    raw = SKILL_MD.format(name="alpha", version="3.2.1", body="")
    fm = _parse_frontmatter_stdlib(raw[3:raw.find("\n---", 3)])
    assert fm["metadata"]["version"] == "3.2.1"
    assert skill_version(raw) == "3.2.1"
