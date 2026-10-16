"""Tests for hooks/obsidian_guard.py: decisions for destructive vault commands."""

import json
import subprocess
from pathlib import Path

import pytest

GUARD = Path(__file__).resolve().parent.parent / "hooks" / "obsidian_guard.py"


@pytest.fixture
def vault(tmp_path, monkeypatch):
    root = tmp_path / "vault"
    root.mkdir()
    cfg = tmp_path / "local.md"
    cfg.write_text(f"vault_path: {root}\ncurator_write_zones: Notes\n")
    monkeypatch.setenv("ARCHIVIST_LOCAL_MD", str(cfg))
    return root


def decide(command):
    p = subprocess.run(["python3", str(GUARD)], input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
                       capture_output=True, text=True)
    assert p.returncode == 0
    return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"] if p.stdout.strip() else None


@pytest.mark.parametrize("command,expected", [
    ('obsidian delete path="x.md"', "deny"),
    ("obsidian vault=Notes delete", "deny"),
    ('obsidian create path="x.md" content="a b" overwrite', "deny"),
    ('obsidian vault=X create path="x.md" overwrite content="y"', "deny"),
    ('obsidian create path=x content="a;b" overwrite', "deny"),
    ('echo hi && obsidian delete path="x"', "deny"),
    ("cd /tmp; obsidian move file=a to=b", "ask"),
    ('obsidian create path="x.md" content="please overwrite this"', None),
    ('obsidian create path=x content="a | b && c"', None),
    ('obsidian read path="x.md"', None),
    ('obsidian search query="delete me"', None),
    ("git status", None),
])
def test_obsidian_decisions(vault, command, expected):
    assert decide(command) == expected


def test_rm_in_vault_asks(vault):
    assert decide(f'rm -f "{vault}/Notes/a.md"') == "ask"
    assert decide(f'mv "{vault}/a.md" /tmp/a.md') == "ask"
    assert decide("rm /tmp/unrelated") is None
