"""The curator scripts write through vault-write: zones, drift check, lint, git snapshot."""

import json
import subprocess
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "vault-curator" / "scripts"


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout


@pytest.fixture
def vault(tmp_path, monkeypatch):
    root = tmp_path / "vault"
    (root / "Notes").mkdir(parents=True)
    (root / "Private").mkdir()
    (root / "Notes" / "Old.md").write_text("# Old\n")
    (root / "Notes" / "New.md").write_text("---\ntitle: New\n---\n# New\nbody\n")
    (root / "Notes" / "A.md").write_text("see [[Old]] and [[Old|alias]]\n")
    (root / "Private" / "B.md").write_text("also [[Old]]\n")
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "t")
    git(root, "config", "commit.gpgsign", "false")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    cfg = tmp_path / "local.md"
    cfg.write_text(f"vault_path: {root}\ncurator_write_zones: Notes\n")
    monkeypatch.setenv("ARCHIVIST_LOCAL_MD", str(cfg))
    return root


def run(script, *args):
    p = subprocess.run(["uv", "run", "-q", str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True)
    return p.returncode, json.loads(p.stdout)


def test_redirect_links_skips_files_outside_zones(vault):
    code, out = run("redirect_links.py", vault, "--old", "Old", "--new", "New")
    assert code == 0, out
    assert [f["path"] for f in out["affected_files"]] == ["Notes/A.md"]
    assert out["skipped"][0]["path"] == "Private/B.md"
    assert (vault / "Notes" / "A.md").read_text() == "see [[New]] and [[New|alias]]\n"
    assert (vault / "Private" / "B.md").read_text() == "also [[Old]]\n"  # untouched


def test_merge_notes_writes_target_with_snapshot(vault):
    code, out = run("merge_notes.py", vault, "--source", "Notes/Old.md", "--target", "Notes/New.md")
    assert code == 0, out
    assert out["written"] == "Notes/New.md" and out["snapshot"]
    assert "body" in (vault / "Notes" / "New.md").read_text()


def test_merge_notes_refuses_target_outside_zones(vault):
    (vault / "Private" / "T.md").write_text("# T\n")
    code, out = run("merge_notes.py", vault, "--source", "Notes/Old.md", "--target", "Private/T.md")
    assert code == 2 and out["status"] == "refused"
    assert (vault / "Private" / "T.md").read_text() == "# T\n"


def test_generate_canvas_writes_valid_json_in_zone(vault):
    code, out = run("generate_canvas.py", vault, "--scope", "Notes", "--output", "map.canvas")
    assert code == 0, out
    assert json.loads((vault / out["canvas_path"]).read_text())["nodes"]


def test_scripts_refuse_a_vault_that_is_not_configured(vault, tmp_path):
    other = tmp_path / "other"
    (other / "Notes").mkdir(parents=True)
    (other / "Notes" / "A.md").write_text("[[Old]]\n")
    code, out = run("redirect_links.py", other, "--old", "Old", "--new", "New")
    assert code != 0 and "not the configured vault" in json.dumps(out)
