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
    assert daily == {"source": "daily-notes", "folder": "500 ♽ Cycles", "format": "YYYY-MM-DD", "exists": True, "in_zone": True}
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
    code, out = run("config")  # no user config; the source tree has no .local.md
    if code == 0:  # a developer's checkout may have a legacy .local.md beside the plugin
        assert "legacy" in out
    else:
        assert out["error"] == "refused"
    user = tmp_path / "xdg" / "archivist" / "local.md"
    user.parent.mkdir(parents=True)
    user.write_text(cfg.read_text())
    code, out = run("config")
    assert code == 0 and out["config"] == str(user) and "legacy" not in out


def test_config_reports_vault_name(vault):
    code, out = run("config")
    assert code == 0 and out["vault_name"] == "vault"


def test_canvas_must_be_valid_json(vault):
    code, out = run("apply", "Notes/map.canvas", "--from", "-", stdin='{"nodes": [], "edges": []')
    assert code == 3 and "not valid JSON" in out["errors"][0]
    code, out = run("apply", "Notes/map.canvas", "--from", "-", stdin='{"nodes": [{"text": "```"}], "edges": []}')
    assert code == 0, out  # a fence inside canvas JSON isn't a markdown lint error
