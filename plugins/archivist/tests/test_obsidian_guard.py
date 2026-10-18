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
    ('obsidian create vault=vault path="Notes/x.md" content="please overwrite this"', None),
    ('obsidian create vault=vault path=Notes/x content="a | b && c"', None),
    ('obsidian read path="x.md"', None),
    ('obsidian search query="delete me"', None),
    ("git status", None),
    # wrappers and nested shells don't hide the subcommand
    ('timeout 5 obsidian delete path="x.md"', "deny"),
    ('timeout -k 2 10 obsidian delete path="x.md"', "deny"),
    ('env FOO=1 obsidian delete path="x.md"', "deny"),
    ('nice -n 5 obsidian delete path="x.md"', "deny"),
    ('bash -c "obsidian delete path=x.md"', "deny"),
    ("sh -c 'cd /tmp && obsidian eval code=1'", "deny"),
    ('eval "obsidian delete path=x.md"', "deny"),
    ('echo x.md | xargs -I {} obsidian delete path={}', "deny"),
    ('/opt/homebrew/bin/obsidian-cli delete path="x.md"', "deny"),
    ('timeout 5 obsidian read path="x.md"', None),
    # code execution and high-impact subcommands
    ("obsidian eval code=\"app.vault.getFiles()\"", "deny"),
    ("obsidian dev:cdp method=Runtime.evaluate", "deny"),
    ('obsidian rename path="a.md" name=b', "ask"),
    ("obsidian command id=app:delete-file", "ask"),
    ("obsidian template:insert name=Meeting", "ask"),
    ('obsidian history:restore path="a.md" version=2', "ask"),
    ("obsidian plugin:install id=foo", "ask"),
    # writes need an explicit path= (a typo'd target writes to the open note)
    ('obsidian append content="x"', "deny"),
    ('obsidian append pth="Notes/a.md" content="x"', "deny"),
    ('obsidian property:set file=a name=status value=done', "deny"),
    ("obsidian task toggle", "deny"),
    ("obsidian task vault=vault daily toggle", None),
    ("obsidian task ref=a.md:3", None),
    ('obsidian vault=vault daily:append content="- did a thing"', None),
    ('obsidian daily:append content="- did a thing"', "deny"),
    ("obsidian base:create file=Things name=new", "ask"),
])
def test_obsidian_decisions(vault, command, expected):
    assert decide(command) == expected


def test_rm_in_vault_asks(vault):
    assert decide(f'rm -f "{vault}/Notes/a.md"') == "ask"
    assert decide(f'mv "{vault}/a.md" /tmp/a.md') == "ask"
    assert decide("rm /tmp/unrelated") is None


@pytest.mark.parametrize("command,expected", [
    ('obsidian append vault=vault path="Notes/a.md" content="x"', None),
    ('obsidian vault=vault property:set path="Notes/a.md" name=status value=done', None),
    ('obsidian property:remove vault=vault path="Notes/a.md" name=status', None),
    ('obsidian create vault=vault path="Notes/new.md" content="x"', None),
    ("obsidian task vault=vault ref=Notes/a.md:3 done", None),
    # the CLI targets the focused vault unless vault= names the configured one
    ('obsidian append path="Notes/a.md" content="x"', "deny"),
    ('obsidian append vault=Sandbox path="Notes/a.md" content="x"', "deny"),
    ('obsidian append vault=vault path="Templates/t.md" content="x"', "deny"),
    ('obsidian property:set vault=vault path="../outside.md" name=a value=b', "deny"),
    ("obsidian task vault=vault ref=Templates/t.md:3 toggle", "deny"),
])
def test_cli_writes_are_zone_checked(vault, command, expected):
    assert decide(command) == expected


def test_cli_write_without_config_asks(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCHIVIST_LOCAL_MD", str(tmp_path / "missing.md"))
    assert decide('obsidian append path="Notes/a.md" content="x"') == "ask"
