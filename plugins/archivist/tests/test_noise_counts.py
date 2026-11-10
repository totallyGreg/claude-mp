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


def add_kplex(vault, **lists):
    d = vault / ".obsidian" / "plugins" / "k-plex"
    d.mkdir(parents=True)
    (d / "data.json").write_text(json.dumps({"hierarchy": lists}))


def test_unmapped_link_fields(vault):
    add_kplex(vault, parents=["Parent", "Week", "based on"], previous=["Yesterday"], hidden=[""])
    (vault / "Notes" / "a.md").write_text(
        '---\nparent: "[[Top]]"\nBased-On: "[[Src]]"\nreplies to: "[[Other]]"\nprocessed: "[[Log]]"\n'
        'related:\n  - "[[X]]"\n  - "[[Y]]"\ntitle: plain text\n---\nbody has weird:: [[Z]]\n'
    )
    (vault / "Notes" / "b.md").write_text('---\nrelated: ["[[X]]"]\n---\n')
    (vault / "Notes" / "c.md").write_text('---\nOwner: "[[P]]"\n---\n')
    (vault / "Notes" / "d.md").write_text('---\nowner: "[[Q]]"\n---\n')
    (vault / "Templates" / "t.md").write_text('---\nunknown: "[[<% tp.file.title %>]]"\n---\n')
    code, out = run(vault, "--exclude", "Templates", "--days", "Days", "--link-exempt", "processed")
    assert code == 0
    # a.md: replies to, related; b.md: related. parent/Based-On normalize to K-Plex fields;
    # processed is exempt; the template folder is excluded; inline fields don't count.
    assert out["counts"]["unmapped_link_fields"]["count"] == 5
    # Owner and owner are one field to K-Plex, so they list once with the combined count
    assert sorted(out["unmapped_link_fields_top"]) == [["Owner", 2], ["related", 2], ["replies to", 1]] or \
        sorted(out["unmapped_link_fields_top"]) == [["owner", 2], ["related", 2], ["replies to", 1]]
    assert "Link fields exempt: `processed`" in out["section"]


def test_unmapped_link_fields_skipped_without_kplex(vault):
    _, out = run(vault, "--exclude", "Templates", "--days", "Days")
    assert "unmapped_link_fields" not in out["counts"]
