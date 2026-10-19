"""Tests for hooks/vault_file_guard.py: Write/Edit on vault files, by calling agent."""

import json
import subprocess
from pathlib import Path

import pytest

GUARD = Path(__file__).resolve().parent.parent / "hooks" / "vault_file_guard.py"


@pytest.fixture
def vault(tmp_path, monkeypatch):
    root = tmp_path / "vault"
    (root / "Notes").mkdir(parents=True)
    (root / "Templates").mkdir()
    cfg = tmp_path / "local.md"
    cfg.write_text(f"vault_path: {root}\narchitect_write_zones: Templates\ncurator_write_zones: Notes\n")
    monkeypatch.setenv("ARCHIVIST_LOCAL_MD", str(cfg))
    return root


def decide(path, agent_type=None, tool="Write"):
    payload = {"tool_name": tool, "tool_input": {"file_path": str(path)}}
    if agent_type:
        payload["agent_type"] = agent_type
    p = subprocess.run(["python3", str(GUARD)], input=json.dumps(payload), capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"] if p.stdout.strip() else None


def test_architect_inside_zones_passes(vault):
    assert decide(vault / "Templates" / "t.md", "archivist:archivist-architect") is None
    assert decide(vault / "Notes" / "Folder.md", "archivist:archivist-architect", "Edit") is None


def test_architect_outside_zones_denied(vault):
    assert decide(vault / "Private" / "x.md", "archivist:archivist-architect") == "deny"


def test_other_callers_asked(vault):
    assert decide(vault / "Notes" / "a.md") == "ask"
    assert decide(vault / "Notes" / "a.md", "archivist:archivist") == "ask"


def test_outside_vault_untouched(vault, tmp_path):
    assert decide(tmp_path / "elsewhere.md") is None
    assert decide(tmp_path / "elsewhere.md", "archivist:archivist-architect") is None


def test_no_config_untouched(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCHIVIST_LOCAL_MD", str(tmp_path / "missing.md"))
    assert decide(tmp_path / "vault" / "Notes" / "a.md") is None
