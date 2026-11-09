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
    (root / "Agents" / "new-tool.md").write_text(
        "---\ntitle: new-tool\nformerly: [old-tool]\naliases: [old-tool]\n---\n# new-tool\nSee old-tool history.\n"
    )
    (root / "Notes" / "Ownership.md").write_text("| Vault notes | Librarian | old-tool |\nThe old-tool-plus tool is different.\n")
    (root / "Notes" / "Changes.md").write_text("| 1.2.0 | renamed old-tool |\n")
    (root / "Archived Notes" / "Old.md").write_text("old-tool everywhere\n")
    (root / "Days" / "2026-01-01.md").write_text("used old-tool today\n")
    (root / "Notes" / "Review answers.md").write_text("---\nhistorical: true\n---\nI used old-tool all year\n")
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
    hits = out["names"]["old-tool"]
    # Ownership.md line 1 and the canonical note's body; not its frontmatter, the version row,
    # the archive, the dated daily note, the note marked historical, or the longer word old-tool-plus.
    assert sorted((m["path"], m["line"]) for m in hits["mentions"]) == [("Agents/new-tool.md", 7), ("Notes/Ownership.md", 1)]
    assert hits["canonical"] == "Agents/new-tool.md"


def test_baseline_only_falls(vault, tmp_path):
    assert run(vault, tmp_path, "--update-baseline")[1]["total_hits"] == 2
    (vault / "Notes" / "New.md").write_text("old-tool again\n")
    code, out = run(vault, tmp_path, "--update-baseline")
    assert (code, out["status"], out["baseline"]) == (1, "regressed", 2)
    (vault / "Notes" / "New.md").unlink()
    (vault / "Notes" / "Ownership.md").write_text("| Vault notes | Librarian | new-tool |\n")
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
    (repo / "README.md").write_text("Install old-tool\n")
    (repo / "docs" / "notes.md").write_text("old-tool\n")
    _, out = run(vault, tmp_path, "--repo", repo, "--exempt", "Notes/", "--exempt", "docs/")
    paths = {m["path"] for m in out["names"]["old-tool"]["mentions"]}
    assert paths == {"Agents/new-tool.md", "repo:README.md"}


def run_registry(reg, *args):
    p = subprocess.run(["uv", "run", "-q", str(SCRIPT), "--registry", str(reg), *args], capture_output=True, text=True)
    return p.returncode, json.loads(p.stdout)


def test_registry_mode_ratchets_in_the_committed_file(tmp_path):
    repo = tmp_path / "repo"
    (repo / "docs" / "lessons").mkdir(parents=True)
    (repo / "README.md").write_text("Install old-tool\n")
    (repo / "docs" / "lessons" / "why.md").write_text("old-tool was renamed\n")
    reg = repo / ".stale-names.json"
    reg.write_text(json.dumps({"names": {"old-tool": "new-tool"}, "exempt": ["docs/lessons/"]}))
    code, out = run_registry(reg, "--update-baseline")
    # The registry file itself names old-tool but is never counted.
    assert (code, out["status"], out["total_hits"]) == (0, "first-run", 1)
    assert json.loads(reg.read_text())["baseline"] == 1
    (repo / "NEW.md").write_text("old-tool again\n")
    code, out = run_registry(reg, "--update-baseline")
    assert (code, out["status"]) == (1, "regressed")
    assert json.loads(reg.read_text())["baseline"] == 1


def test_vault_and_registry_are_exclusive(vault, tmp_path):
    code, out = run_registry(tmp_path / "x.json", str(vault))
    assert code == 2 and "error" in out


def test_repo_scan_counts_tracked_files_only(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "tracked.md").write_text("old-tool\n")
    (repo / ".stale-names.json").write_text(json.dumps({"names": {"old-tool": "new-tool"}}))
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "tracked.md", ".stale-names.json"], check=True)
    (repo / "untracked copy.md").write_text("old-tool\n")
    _, out = run_registry(repo / ".stale-names.json")
    assert [m["path"] for m in out["names"]["old-tool"]["mentions"]] == ["repo:tracked.md"]
