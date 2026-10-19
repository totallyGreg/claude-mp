"""End-to-end tests for bin/vault-write against a throwaway git-backed vault."""

import json
import os
import subprocess
import unicodedata
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parent.parent / "bin" / "vault-write"
NOTE = "Notes/a.md"
ORIGINAL = "---\ntitle: A\ndate modified: 2026-10-16T20:00Z\n---\n# A\n\n## One\nold one\n\n## Two\n```bash\n# not a heading\n```\nold two\n"


def git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


@pytest.fixture
def vault(tmp_path, monkeypatch):
    root = tmp_path / "vault"
    (root / "Notes").mkdir(parents=True)
    (root / "Private").mkdir()
    (root / "500 ♽ Cycles").mkdir()
    (root / NOTE).write_text(ORIGINAL)
    (root / "Notes" / "Linked.md").write_text("x\n")
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "t")
    git(root, "config", "commit.gpgsign", "false")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    cfg = tmp_path / "local.md"
    # NFD zone spelling must still match the NFC folder name.
    cycles = unicodedata.normalize("NFD", "500 ♽ Cycles")
    cfg.write_text(
        f"<!-- comment -->\nvault_path: {root}\ncurator_write_zones: Notes/, {cycles}, Missing Zone\n"
    )
    monkeypatch.setenv("ARCHIVIST_LOCAL_MD", str(cfg))
    return root


def run(*args, stdin=None):
    p = subprocess.run([str(BIN), *args], input=stdin, capture_output=True, text=True, env=os.environ)
    return p.returncode, json.loads(p.stdout)


def staged(tmp_path, text, name="new.md"):
    f = tmp_path / name
    f.write_text(text)
    return str(f)


def base_of(note=NOTE):
    return run("stat", note)[1]["hash"]


def test_stat(vault):
    code, out = run("stat", NOTE)
    assert code == 0 and out["exists"] and out["in_zone"] and len(out["hash"]) == 64


def test_apply_requires_base_for_existing(vault, tmp_path):
    code, out = run("apply", NOTE, "--from", staged(tmp_path, "# A\n"))
    assert code == 2 and "--base" in out["detail"]
    assert (vault / NOTE).read_text() == ORIGINAL


def test_apply_with_base_writes_and_verifies(vault, tmp_path):
    code, out = run("apply", NOTE, "--from", staged(tmp_path, "# A\nnew\n"), "--base", base_of())
    assert code == 0, out
    assert (vault / NOTE).read_text() == "# A\nnew\n"
    assert out["hash_before"] and out["hash"] != out["hash_before"]
    assert "Missing Zone" in " ".join(out["warnings"])


def test_drift_refused(vault, tmp_path):
    base = base_of()
    (vault / NOTE).write_text(ORIGINAL.replace("old one", "user edit"))
    code, out = run("apply", NOTE, "--from", staged(tmp_path, "# A\n"), "--base", base)
    assert code == 2 and "drift" in out["detail"]
    assert "user edit" in (vault / NOTE).read_text()


def test_linter_noise_is_not_drift(vault, tmp_path):
    stable = run("stat", NOTE)[1]["stable"]
    noisy = ORIGINAL.replace("2026-10-16T20:00Z", "2026-10-17T09:00Z").replace("# A\n", "# A   \n")
    (vault / NOTE).write_text(noisy)
    code, out = run("apply", NOTE, "--from", staged(tmp_path, "# A\n"), "--base", stable)
    assert code == 0, out


def test_outside_zone_refused_but_force_allowed(vault, tmp_path):
    code, out = run("apply", "Private/p.md", "--from", staged(tmp_path, "# P\n"))
    assert code == 2 and "outside the write zones" in out["detail"]
    code, out = run("force", "Private/p.md", "--from", staged(tmp_path, "# P\n"))
    assert code == 0 and out["created"]


def test_unicode_zone_matches(vault, tmp_path):
    code, out = run("apply", "500 ♽ Cycles/day.md", "--from", staged(tmp_path, "# D\n"))
    assert code == 0, out


def test_path_escape_refused(vault, tmp_path):
    code, out = run("force", "../escape.md", "--from", staged(tmp_path, "x\n"))
    assert code == 2 and "outside the vault" in out["detail"]


def test_dataview_inline_code_blocks(vault, tmp_path):
    code, out = run("apply", "Notes/n.md", "--from", staged(tmp_path, "use `==>` here\n"))
    assert code == 3 and "equals sign" in out["errors"][0]
    code, out = run("apply", "Notes/n.md", "--from", staged(tmp_path, "use `A ==> B` here\n"))
    assert code == 0


def test_unclosed_fence_blocks(vault, tmp_path):
    code, out = run("apply", "Notes/n.md", "--from", staged(tmp_path, "```bash\necho hi\n"))
    assert code == 3 and "unclosed" in out["errors"][0]


def test_preexisting_lint_errors_do_not_block(vault, tmp_path):
    (vault / NOTE).write_text(ORIGINAL + "\nlegacy `=bad`\n")
    code, out = run("apply", NOTE, "--from", staged(tmp_path, "## One\nfixed one\n"), "--base", base_of(), "--section", "## One")
    assert code == 0, out


def test_unresolved_wikilink_warns_only(vault, tmp_path):
    code, out = run("apply", "Notes/n.md", "--from", staged(tmp_path, "[[Linked]] [[Nope]] `[[InCode]]`\n"))
    assert code == 0
    assert out["warnings"] == [w for w in out["warnings"] if "Nope" in w or "zone" in w]
    assert any("Nope" in w for w in out["warnings"])


def test_section_replace_ignores_hash_in_fence(vault, tmp_path):
    code, out = run("apply", NOTE, "--from", staged(tmp_path, "## Two\nnew two\n"), "--base", base_of(), "--section", "## Two")
    assert code == 0, out
    text = (vault / NOTE).read_text()
    assert "new two" in text and "old two" not in text and "# not a heading" not in text
    assert "old one" in text


def test_section_must_start_with_heading(vault, tmp_path):
    code, out = run("apply", NOTE, "--from", staged(tmp_path, "no heading\n"), "--base", base_of(), "--section", "## One")
    assert code == 2


def test_snapshot_commits_dirty_note(vault, tmp_path):
    (vault / NOTE).write_text(ORIGINAL + "uncommitted user text\n")
    code, out = run("apply", NOTE, "--from", staged(tmp_path, "# A\n"), "--base", base_of())
    assert code == 0 and out["snapshot"] and "restore" in out
    shown = subprocess.run(["git", "-C", str(vault), "show", f"{out['snapshot']}:{NOTE}"], capture_output=True, text=True)
    assert "uncommitted user text" in shown.stdout
    # Only the target note was committed.
    files = subprocess.run(["git", "-C", str(vault), "show", "--name-only", "--format=", out["snapshot"]], capture_output=True, text=True)
    assert files.stdout.split() == [NOTE]


def test_no_git_refuses_apply(vault, tmp_path):
    subprocess.run(["rm", "-rf", str(vault / ".git")], check=True)
    code, out = run("apply", "Notes/n.md", "--from", staged(tmp_path, "x\n"))
    assert code == 0  # new note: nothing to snapshot
    code, out = run("apply", NOTE, "--from", staged(tmp_path, "x\n"), "--base", base_of())
    assert code == 2 and "not a git repository" in out["detail"]


def test_stdin_source(vault):
    code, out = run("apply", "Notes/s.md", "--from", "-", stdin="# S\n")
    assert code == 0 and (vault / "Notes/s.md").read_text() == "# S\n"


def test_check(vault, tmp_path):
    assert run("check", staged(tmp_path, "fine\n"))[0] == 0
    assert run("check", staged(tmp_path, "`=x`\n"))[0] == 3


def test_config_suggests_real_folder_for_missing_zone(vault):
    code, out = run("config")
    assert code == 0
    assert out["curator_write_zones"][0] == "Notes"
    assert out["missing_zones"] == [{"zone": "Missing Zone", "did_you_mean": None}]
    (vault / "Missing ♽ Zone").mkdir()
    assert run("config")[1]["missing_zones"][0]["did_you_mean"] == "Missing ♽ Zone"


def test_config_discovers_daily_notes(vault):
    obs = vault / ".obsidian"
    (obs / "plugins" / "periodic-notes").mkdir(parents=True)
    assert run("config")[1]["daily_notes"] is None
    (obs / "core-plugins.json").write_text('{"daily-notes": true}')
    (obs / "daily-notes.json").write_text('{"folder": "500 ♽ Cycles", "format": ""}')
    daily = run("config")[1]["daily_notes"]
    assert (daily["source"], daily["folder"], daily["format"], daily["exists"], daily["in_zone"]) == (
        "daily-notes", "500 ♽ Cycles", "YYYY-MM-DD", True, True)
    assert daily["today"].startswith("500 ♽ Cycles/") and daily["today"].endswith(".md")
    # Periodic Notes wins when it is enabled.
    (obs / "community-plugins.json").write_text('["periodic-notes"]')
    (obs / "plugins" / "periodic-notes" / "data.json").write_text('{"daily": {"enabled": true, "folder": "Private", "format": "YYYY/MM-DD"}}')
    daily = run("config")[1]["daily_notes"]
    assert (daily["source"], daily["folder"], daily["format"], daily["in_zone"]) == ("periodic-notes", "Private", "YYYY/MM-DD", False)


def test_config_location_order(vault, tmp_path, monkeypatch):
    cfg = Path(os.environ["ARCHIVIST_LOCAL_MD"])
    monkeypatch.delenv("ARCHIVIST_LOCAL_MD")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    code, out = run("config")  # no user config: refused (a pre-2.0 .local.md is never read)
    assert code == 2 and out["error"] == "refused" and "no archivist config" in out["detail"]
    user = tmp_path / "xdg" / "archivist" / "local.md"
    user.parent.mkdir(parents=True)
    user.write_text(cfg.read_text())
    code, out = run("config")
    assert code == 0 and out["config"] == str(user)


def test_config_reports_vault_name(vault):
    code, out = run("config")
    assert code == 0 and out["vault_name"] == "vault"


def test_canvas_must_be_valid_json(vault):
    code, out = run("apply", "Notes/map.canvas", "--from", "-", stdin='{"nodes": [], "edges": []')
    assert code == 3 and "not valid JSON" in out["errors"][0]
    code, out = run("apply", "Notes/map.canvas", "--from", "-", stdin='{"nodes": [{"text": "```"}], "edges": []}')
    assert code == 0, out  # a fence inside canvas JSON isn't a markdown lint error


def _journals(obs, folder):
    (obs / "plugins" / "journals").mkdir(parents=True, exist_ok=True)
    (obs / "plugins" / "journals" / "data.json").write_text(json.dumps({"journals": {
        "Daily": {"write": {"type": "day"}, "nameTemplate": "{{date}}", "dateFormat": "YYYY-MM-DD", "folder": folder},
        "Meeting": {"write": {"type": "day"}, "nameTemplate": "{{date}} {{index}}", "dateFormat": "YYYY-MM-DD", "folder": "Notes/M"}}}))


def test_daily_notes_follow_the_evidence(vault):
    """A stale Periodic Notes folder loses to a Journals year template that matches real notes."""
    import datetime
    obs = vault / ".obsidian"
    (obs / "plugins" / "periodic-notes").mkdir(parents=True)
    (obs / "community-plugins.json").write_text('["periodic-notes", "journals"]')
    (obs / "plugins" / "periodic-notes" / "data.json").write_text('{"daily": {"enabled": true, "folder": "Notes/Days/2019"}}')
    _journals(obs, "Notes/Days/{{date:YYYY}}")
    old = datetime.date.today() - datetime.timedelta(days=40)  # outside 14 days: the one-year fallback decides
    (vault / "Notes" / "Days" / f"{old:%Y}").mkdir(parents=True)
    (vault / "Notes" / "Days" / f"{old:%Y}" / f"{old:%Y-%m-%d}.md").write_text("x\n")
    daily = run("config")[1]["daily_notes"]
    today = datetime.date.today()
    assert daily["source"] == "journals:Daily"
    assert daily["today"] == f"Notes/Days/{today:%Y}/{today:%Y-%m-%d}.md"
    assert daily["disagree"][0]["source"] == "periodic-notes"  # the indexed Meeting journal isn't a candidate


def test_render_moment():
    import datetime
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader("vw", str(BIN))
    vw = importlib.util.module_from_spec(importlib.util.spec_from_loader("vw", loader))
    loader.exec_module(vw)
    d = datetime.date(2026, 10, 3)
    assert vw.render_moment("YYYY-MM-DD", d) == "2026-10-03"
    assert vw.render_moment("dddd MMMM Do, YYYY", d) == "Saturday October 3rd, 2026"
    assert vw.render_moment("YYYY-[W]WW", d) == "2026-W40"
    assert vw._render_template("Days/{{date:YYYY}}/{{Date}}", "YYYY-MM-DD", d) == "Days/2026/2026-10-03"


def test_profile_drift(vault):
    import datetime
    obs = vault / ".obsidian"
    (obs / "plugins" / "dataview").mkdir(parents=True)
    (obs / "plugins" / "dataview" / "manifest.json").write_text('{"name": "Dataview"}')
    (obs / "plugins" / "waypoint").mkdir(parents=True)
    (obs / "community-plugins.json").write_text('["dataview", "waypoint"]')
    (vault / "Templates").mkdir()
    (vault / "Templates" / "Meeting.md").write_text("x\n")
    (vault / "Templates" / "Book.md").write_text("x\n")
    (obs / "templates.json").write_text('{"folder": "Templates"}')
    assert run("config")[1]["profile_drift"] is None  # no profile yet
    old = (datetime.date.today() - datetime.timedelta(days=45)).isoformat()
    (vault / "_vault-profile.md").write_text(
        f"---\nlast_updated: {old}\n---\n# Vault Profile\n## Installed Plugins\n- Dataview\n"
        "## Directory Trust Levels\n| Notes | personal |\n| 500 Cycles | personal |\n| Templates | infrastructure |\n"
        "## Template Inventory\nMeeting\n")
    drift = run("config")[1]["profile_drift"]
    assert drift["age_days"] == 45 and drift["stale"] is True
    assert drift["new_folders"] == ["Private"]  # "500 Cycles" in prose matches the "500 ♽ Cycles" folder
    assert drift["new_plugins"] == ["waypoint"]  # Dataview matched by manifest name
    assert drift["new_templates"] == ["Book"]
    assert drift["drifted"] is True
