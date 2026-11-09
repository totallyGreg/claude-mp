"""noise_counts.py: counts from a fixture vault, baselines read from and rendered into the profile."""

import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "vault-curator" / "scripts" / "noise_counts.py"

ORPHANS = "\n".join([
    "Notes/Lonely.md",
    "Notes/Also lonely.md",
    "Templates/New Day.md",
    "Days/2026/2026-01-02.md",
    "Notes/picture.png",
    "Maps/map.canvas",
])


@pytest.fixture
def vault(tmp_path):
    root = tmp_path / "vault"
    for d in ("Notes", "Templates", "Days/2026", "Weeks"):
        (root / d).mkdir(parents=True)
    (root / "Weeks" / "2026-W01.md").write_text("# week\n")
    (root / "Days/2026/2026-01-01.md").write_text('---\nWeek: "[[2026-W01]]"\n---\n')
    (root / "Days/2026/2026-01-02.md").write_text('---\nWeek: "[[2026-W02|Week 2]]"\n---\n')
    (root / "Days/2026/2026-01-03.md").write_text("no frontmatter\n")
    (root / "Days/2026/2026-01-04.md").write_text(
        '---\nWeek: "[[<% tp.date.now("YYYY-[W]WW", +0, tp.file.title, "YYYY-MM-DD")%>]]"\n---\n'
    )
    (root / "Notes" / "new-tool.md").write_text("---\nformerly: [old-tool]\n---\n# new-tool\n")
    (root / "Notes" / "Usage.md").write_text("still says old-tool here\n")
    return root


def run(vault, *args, orphans=ORPHANS):
    p = subprocess.run(
        ["uv", "run", "-q", str(SCRIPT), str(vault), "--orphans", "-", "--today", "2026-11-09", *args],
        input=orphans, capture_output=True, text=True,
    )
    return p.returncode, json.loads(p.stdout)


def write_profile(vault, section):
    (vault / "_vault-profile.md").write_text(f"# Profile\n\n## Noise\n\n{section}\n## Other\n\nkept\n")


def test_first_run_counts_and_renders(vault):
    code, out = run(vault, "--exclude", "Templates", "--days", "Days")
    assert code == 0
    counts = {k: v["count"] for k, v in out["counts"].items()}
    assert counts == {"orphans": 2, "broken_week_links": 2, "stale_names": 1}
    assert all(v["status"] == "first-run" for v in out["counts"].values())
    assert "Orphans exclude: `Templates`" in out["section"]
    assert "| orphans | 2 | 2 | 2026-11-09 |" in out["section"]


def test_profile_settings_and_baselines_are_read(vault):
    _, first = run(vault, "--exclude", "Templates", "--days", "Days")
    write_profile(vault, first["section"])
    code, out = run(vault)
    assert code == 0 and out["status"] == "ok"
    assert {v["status"] for v in out["counts"].values()} == {"ok"}


def test_lower_count_becomes_baseline(vault):
    _, first = run(vault, "--exclude", "Templates", "--days", "Days")
    write_profile(vault, first["section"])
    (vault / "Notes" / "Usage.md").write_text("fixed: new-tool\n")
    code, out = run(vault)
    assert code == 0
    assert out["counts"]["stale_names"] == {"count": 0, "baseline": 0, "status": "improved"}


def test_rise_is_a_regression_and_keeps_the_baseline(vault):
    _, first = run(vault, "--exclude", "Templates", "--days", "Days")
    write_profile(vault, first["section"])
    code, out = run(vault, orphans=ORPHANS + "\nNotes/Third.md")
    assert code == 1 and out["regressed"] == ["orphans"]
    assert out["counts"]["orphans"] == {"count": 3, "baseline": 2, "status": "regressed"}
    assert "| orphans | 2 | 3 |" in out["section"]


def test_tracked_orphans_need_input(vault):
    _, first = run(vault, "--exclude", "Templates", "--days", "Days")
    write_profile(vault, first["section"])
    p = subprocess.run(["uv", "run", "-q", str(SCRIPT), str(vault)], capture_output=True, text=True)
    assert p.returncode == 2 and "--orphans" in json.loads(p.stdout)["error"]
