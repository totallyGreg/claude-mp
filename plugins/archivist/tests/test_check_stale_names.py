"""check_stale_names.py: registry from `formerly:`, history exemptions, and a baseline that only falls."""

import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "vault-curator" / "scripts" / "check_stale_names.py"


@pytest.fixture
def vault(tmp_path):
    root = tmp_path / "vault"
    for d in ("Agents", "Notes", "Archived Notes", "Days"):
        (root / d).mkdir(parents=True)
    (root / "Agents" / "archivist.md").write_text(
        "---\ntitle: archivist\nformerly: [pkm-manager]\naliases: [pkm-manager]\n---\n# archivist\nSee pkm-manager history.\n"
    )
    (root / "Notes" / "Ownership.md").write_text("| Vault notes | Librarian | pkm-manager |\nThe pkm-manager-plus tool is different.\n")
    (root / "Notes" / "Changes.md").write_text("| 1.2.0 | renamed pkm-manager |\n")
    (root / "Archived Notes" / "Old.md").write_text("pkm-manager everywhere\n")
    (root / "Days" / "2026-01-01.md").write_text("used pkm-manager today\n")
    (root / "Notes" / "Review answers.md").write_text("---\nhistorical: true\n---\nI used pkm-manager all year\n")
    return root


def run(vault, tmp_path, *args):
    p = subprocess.run(
        ["uv", "run", "-q", str(SCRIPT), str(vault), "--baseline", str(tmp_path / "base.json"), *args],
        capture_output=True, text=True,
    )
    return p.returncode, json.loads(p.stdout)


def test_counts_only_live_mentions(vault, tmp_path):
    code, out = run(vault, tmp_path)
    assert code == 0
    assert out["status"] == "first-run"
    hits = out["names"]["pkm-manager"]
    # Ownership.md line 1 and the canonical note's body; not its frontmatter, the version row,
    # the archive, the dated daily note, the note marked historical, or the longer word pkm-manager-plus.
    assert sorted((m["path"], m["line"]) for m in hits["mentions"]) == [("Agents/archivist.md", 7), ("Notes/Ownership.md", 1)]
    assert hits["canonical"] == "Agents/archivist.md"


def test_baseline_only_falls(vault, tmp_path):
    assert run(vault, tmp_path, "--update-baseline")[1]["total_hits"] == 2
    (vault / "Notes" / "New.md").write_text("pkm-manager again\n")
    code, out = run(vault, tmp_path, "--update-baseline")
    assert (code, out["status"], out["baseline"]) == (1, "regressed", 2)
    (vault / "Notes" / "New.md").unlink()
    (vault / "Notes" / "Ownership.md").write_text("| Vault notes | Librarian | archivist |\n")
    code, out = run(vault, tmp_path, "--update-baseline")
    assert (code, out["status"]) == (0, "improved")
    assert json.loads((tmp_path / "base.json").read_text()) == {str(vault.resolve()): 1}


def test_no_registry_is_not_an_error(tmp_path):
    root = tmp_path / "empty"
    root.mkdir()
    (root / "Note.md").write_text("nothing renamed here\n")
    code, out = run(root, tmp_path)
    assert (code, out["status"], out["total_hits"]) == (0, "no-registry", 0)


def test_exempt_prefix_and_repo_scan(vault, tmp_path):
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "README.md").write_text("Install pkm-manager\n")
    (repo / "docs" / "notes.md").write_text("pkm-manager\n")
    _, out = run(vault, tmp_path, "--repo", repo, "--exempt", "Notes/", "--exempt", "docs/")
    paths = {m["path"] for m in out["names"]["pkm-manager"]["mentions"]}
    assert paths == {"Agents/archivist.md", "repo:README.md"}
