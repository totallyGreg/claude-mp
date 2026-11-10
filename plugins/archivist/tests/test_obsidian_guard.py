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
    ('obsidian vault=vault create path="Notes/x.md" content="please overwrite this"', None),
    ('obsidian vault=vault create path=Notes/x content="a | b && c"', None),
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
    ("obsidian vault=vault task daily toggle", None),
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
    ('obsidian vault=vault append path="Notes/a.md" content="x"', None),
    ('obsidian vault=vault property:set path="Notes/a.md" name=status value=done', None),
    ('obsidian vault=vault property:remove path="Notes/a.md" name=status', None),
    ('obsidian vault=vault create path="Notes/new.md" content="x"', None),
    ("obsidian vault=vault task ref=Notes/a.md:3 done", None),
    # the CLI targets the focused vault unless vault= names the configured one
    ('obsidian append path="Notes/a.md" content="x"', "deny"),
    ('obsidian vault=Sandbox append path="Notes/a.md" content="x"', "deny"),
    # vault= after the subcommand is silently ignored by the CLI
    ('obsidian append vault=vault path="Notes/a.md" content="x"', "deny"),
    ('obsidian property:set vault=vault path="Notes/a.md" name=a value=b', "deny"),
    # vault names match case-insensitively, like Obsidian
    ('obsidian vault=VAULT append path="Notes/a.md" content="x"', None),
    ('obsidian vault=vault append path="Templates/t.md" content="x"', "deny"),
    ('obsidian vault=vault property:set path="../outside.md" name=a value=b', "deny"),
    ("obsidian vault=vault task ref=Templates/t.md:3 toggle", "deny"),
])
def test_cli_writes_are_zone_checked(vault, command, expected):
    assert decide(command) == expected


def test_cli_write_without_config_asks(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCHIVIST_LOCAL_MD", str(tmp_path / "missing.md"))
    assert decide('obsidian append path="Notes/a.md" content="x"') == "ask"


# -- K-Plex API through obsidian eval (#246) ---------------------------------

def kplex(code, vault_arg="vault=vault"):
    return f"obsidian {vault_arg} eval 'code={code}'"


@pytest.mark.parametrize("code", [
    "JSON.stringify(window.kplexApi.v1.capabilities())",
    "JSON.stringify(window.kplexApi.v1.ontology())",
    'JSON.stringify(window.kplexApi.v1.ontologyGuide({format:"markdown"}))',
    'JSON.stringify(window.kplexApi.v1.search({query:"Agentic Coding",limit:10}))',
    'JSON.stringify(window.kplexApi.v1.neighbors({id:"note:a/b.md",role:"parent",limit:20}))',
    '(async()=>JSON.stringify(await window.kplexApi.v1.ontologyDocuments({field:"Parent",limit:20})))()',
    '(async()=>JSON.stringify(await window.kplexApi.v1.inspectOntologyOccurrences({path:"Notes/x.md",fields:["Parent","parent"]})))()',
    'JSON.stringify(window.kplexApi.v1.previewOntologyConfiguration({edits:[{kind:"assign",field:"parent",role:"parent",partner:null}]}))',
    'JSON.stringify(window.kplexApi.v1.search({query:"a ) ; fetch(\\"x\\")",limit:1}))',
])
def test_kplex_reads_defer(vault, code):
    assert decide(kplex(code)) is None


def test_kplex_apply_asks(vault):
    code = '(async()=>JSON.stringify(await window.kplexApi.v1.applyOntologyConfiguration({previewId:"p1",confirm:true})))()'
    assert decide(kplex(code)) == "ask"


@pytest.mark.parametrize("code", [
    "app.vault.adapter.remove(\"x.md\")",                                              # not K-Plex
    "JSON.stringify(window.kplexApi.v1.ontology());app.vault.adapter.remove(\"x\")",  # extra statement
    "JSON.stringify(window.kplexApi.v1.ontology({a:fetch(\"http://x\")}))",            # call in argument
    "JSON.stringify(window.kplexApi.v1.ontology({a:b}))",                              # identifier value
    "JSON.stringify(window.kplexApi.v1.ontology({a:`x${1}`}))",                        # template string
    "JSON.stringify(window.kplexApi.v1.ontology({a:'x'}))",                            # single quotes
    "JSON.stringify(window.kplexApi.v1.ontology({get a(){return 1}}))",                # getter
    "JSON.stringify(window.kplexApi.v1.ontology({a:1})+app.vault.getName())",           # concatenation
    "JSON.stringify(window.kplexApi.v1.ontology.call(null))",                          # property chain
    "JSON.stringify(window.kplexApi.v1.configuration.apply({previewId:\"p\",confirm:true}))",  # unlisted
    "JSON.stringify(window.kplexApi.v1.navigate({canvasId:\"c\",path:\"x.md\"}))",     # canvas action
    "JSON.stringify(window.kplexApi.v1.ontology({a:1}}))",                             # unbalanced
    "JSON.stringify(window.kplexApi.v1.ontology([1]))",                                # not an object
])
def test_kplex_other_eval_denied(vault, code):
    assert decide(kplex(code)) == "deny"


def test_kplex_needs_config_vault_first(vault):
    code = "JSON.stringify(window.kplexApi.v1.ontology())"
    assert decide(kplex(code, vault_arg="")) == "deny"
    assert decide(kplex(code, vault_arg="vault=Other")) == "deny"
    assert decide(f"obsidian eval vault=vault 'code={code}'") == "deny"


def test_kplex_extra_eval_args_denied(vault):
    assert decide("obsidian vault=vault eval 'code=JSON.stringify(window.kplexApi.v1.ontology())' extra=1") == "deny"
