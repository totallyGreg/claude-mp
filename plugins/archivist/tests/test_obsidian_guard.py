"""Tests for hooks/obsidian_guard.py: decisions for destructive vault commands."""

import json
import os
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


# -- shell expansion and redirection around K-Plex eval ---------------------

@pytest.mark.parametrize("command", [
    "obsidian vault=vault eval 'code=JSON.stringify(window.kplexApi.v1.status())' 2>&1",
    "obsidian vault=vault eval 'code=JSON.stringify(window.kplexApi.v1.ontology())' > /tmp/out.json",
    "obsidian vault=vault eval 'code=JSON.stringify(window.kplexApi.v1.ontology())' >> out.json 2> err.log",
    "obsidian vault=vault eval 'code=JSON.stringify(window.kplexApi.v1.ontology())' &>/dev/null",
])
def test_kplex_redirects_defer(vault, command):
    assert decide(command) is None


@pytest.mark.parametrize("command", [
    'obsidian vault=vault eval "code=JSON.stringify(window.kplexApi.v1.search({query:\\"$(cat payload)\\"}))"',
    'obsidian vault=vault eval "code=JSON.stringify(window.kplexApi.v1.search({query:\\"${X}\\"}))"',
    'obsidian vault=vault eval "code=JSON.stringify(window.kplexApi.v1.search({query:\\"`cat payload`\\"}))"',
    "obsidian vault=vault eval 'code=JSON.stringify(window.kplexApi.v1.search({query:\"$HOME\"}))'",
])
def test_kplex_shell_expansion_denied(vault, command):
    assert decide(command) == "deny"


def test_redirect_does_not_hide_extra_args(vault):
    assert decide("obsidian vault=vault eval 'code=JSON.stringify(window.kplexApi.v1.ontology())' extra=1 2>&1") == "deny"


# -- archivist roles (#258 task 2) -------------------------------------------

CURATOR, ARCHITECT = "archivist:archivist", "archivist:archivist-architect"


@pytest.fixture
def zoned(tmp_path, monkeypatch):
    """A vault with a curator zone (Notes) and an architect zone (Templates)."""
    root = tmp_path / "vault"
    (root / "Notes").mkdir(parents=True)
    (root / "Templates").mkdir()
    cfg = tmp_path / "local.md"
    cfg.write_text(f"vault_path: {root}\ncurator_write_zones: Notes\narchitect_write_zones: Templates\n")
    monkeypatch.setenv("ARCHIVIST_LOCAL_MD", str(cfg))
    return root


def decision(command, agent_type=None, cwd=None):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    if agent_type:
        payload["agent_type"] = agent_type
    if cwd:
        payload["cwd"] = str(cwd)
    p = subprocess.run(["python3", str(GUARD)], input=json.dumps(payload), capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)["hookSpecificOutput"] if p.stdout.strip() else {}
    return out.get("permissionDecision"), out.get("permissionDecisionReason", "")


@pytest.mark.parametrize("command,agent,expected", [
    ('obsidian vault=vault append path="Notes/a.md" content="x"', CURATOR, None),
    ('obsidian vault=vault append path="Templates/t.md" content="x"', CURATOR, "deny"),
    ('obsidian vault=vault append path="Templates/t.md" content="x"', ARCHITECT, None),
    ('obsidian vault=vault property:set path="Templates/t.md" name=a value=b', CURATOR, "deny"),
    # no role: the union of zones, as before
    ('obsidian vault=vault append path="Templates/t.md" content="x"', None, None),
])
def test_cli_writes_use_the_roles_zones(zoned, command, agent, expected):
    assert decision(command, agent)[0] == expected


def test_role_refusal_names_the_role(zoned):
    d, reason = decision('obsidian vault=vault append path="Templates/t.md" content="x"', CURATOR)
    assert d == "deny" and "curator" in reason


@pytest.mark.parametrize("command,agent,expected", [
    ('obsidian vault=vault templater:create-from-template template="Templates/t.md" file="Notes/new.md"', None, None),
    ('obsidian vault=vault templater:create-from-template template="Templates/t.md" file="Elsewhere/new.md"', None, "deny"),
    ('obsidian vault=vault templater:create-from-template template="Templates/t.md" file="Templates/new.md"', CURATOR, "deny"),
    ('obsidian vault=vault templater:create-from-template template="Templates/t.md" file="Templates/new.md"', ARCHITECT, None),
    ('obsidian templater:create-from-template template="Templates/t.md" file="Notes/new.md"', None, "deny"),  # no vault=
    ('obsidian vault=vault templater:create-from-template template="Templates/t.md"', None, "deny"),  # no file=
    ("""obsidian vault=vault quickadd:run choice=logEntries vars='{"action":"create","path":"Notes/log.md"}'""", CURATOR, None),
    ("""obsidian vault=vault quickadd:run choice=logEntries vars='{"action":"create","path":"Templates/log.md"}'""", CURATOR, "deny"),
    ('obsidian vault=vault quickadd:run choice="Close Log"', CURATOR, "ask"),
    ('obsidian vault=vault quickadd:run-template path="Templates/t.md"', None, "ask"),  # path= is the template
])
def test_plugin_writes_are_zone_checked(zoned, command, agent, expected):
    assert decision(command, agent)[0] == expected


@pytest.mark.parametrize("template", [
    "sed -i 's/a/b/' {v}/Notes/a.md",
    "echo hi > {v}/Notes/a.md",
    "echo hi >> {v}/Notes/a.md",
    "cat > {v}/Notes/a.md <<'EOF'\nnew text\nEOF",
    "cat /tmp/x | tee {v}/Notes/a.md",
    "cp /tmp/x {v}/Notes/",
    "rm {v}/Notes/a.md",
    "mv {v}/Notes/a.md {v}/Notes/b.md",
    "cd {v} && cat Notes/a.md",
    "cd {v}/Notes; ls",
    'bash -c "sed -i s/a/b/ {v}/Notes/a.md"',
    "python3 -c \"open('{v}/Notes/a.md','w').write('x')\"",
    "uv run /tmp/not-the-plugin.py {v}",
    "git -C {v} status",
    "cat {v}/Notes/a.md",  # reads go through the read tools
])
def test_role_shell_into_the_vault_denied(zoned, template):
    for agent in (CURATOR, ARCHITECT):
        assert decision(template.replace("{v}", str(zoned)), agent)[0] == "deny", template


def test_role_cwd_in_vault_denies_plain_commands(zoned):
    assert decision("ls", CURATOR, cwd=zoned)[0] == "deny"
    assert decision("cat a.md", CURATOR, cwd=zoned / "Notes")[0] == "deny"
    assert decision('obsidian vault=vault read path="Notes/a.md"', CURATOR, cwd=zoned)[0] is None


@pytest.mark.parametrize("command", ["git status", "ls /tmp", "jq . /tmp/x.json", "date", "echo $HOME"])
def test_role_commands_outside_the_vault_defer(zoned, command):
    assert decision(command, CURATOR)[0] is None


@pytest.mark.parametrize("command", [
    'obsidian vault=vault read path="$(sed -i s/a/b/ x.md)"',
    "obsidian vault=vault read path=`rm x.md`",
    'cat "$NO_SUCH_VAR_XYZ/Notes/a.md"',
])
def test_role_expansions_denied(zoned, command):
    assert decision(command, CURATOR)[0] == "deny"


def test_expansions_unchanged_without_a_role(zoned):
    assert decision('obsidian vault=vault read path="$(echo Notes/a.md)"')[0] is None


@pytest.mark.parametrize("command,agent,expected", [
    ("vault-write apply Notes/a.md --from -", CURATOR, None),
    ("vault-write apply Templates/t.md --from - --role architect", ARCHITECT, None),
    ("vault-write apply Templates/t.md --from - --role architect", CURATOR, "deny"),
    ("vault-write apply Templates/t.md --from - --role=architect", CURATOR, "deny"),
    ("ARCHIVIST_ROLE=architect vault-write apply Templates/t.md --from -", CURATOR, "deny"),
    ("export ARCHIVIST_ROLE=architect; vault-write apply Templates/t.md --from -", CURATOR, "deny"),
    ("ARCHIVIST_ROLE=curator vault-write apply Notes/a.md --from -", CURATOR, None),
    ("uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/merge_notes.py --vault {v} a b", CURATOR, None),
    ("uv run --with pyyaml ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/merge_notes.py --vault {v}", CURATOR, None),
    ("ARCHIVIST_ROLE=architect uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/merge_notes.py --vault {v}", CURATOR, "deny"),
    ("python3 ${CLAUDE_PLUGIN_ROOT}/bin/vault-write apply Notes/a.md --from -", CURATOR, None),
])
def test_role_archivist_programs(zoned, command, agent, expected):
    assert decision(command.replace("{v}", str(zoned)), agent)[0] == expected


def test_role_delete_asks_permanent_denied(zoned):
    assert decision('obsidian vault=vault delete path="Notes/a.md"', CURATOR)[0] == "ask"
    assert decision('obsidian vault=vault delete path="Notes/a.md" permanent', CURATOR)[0] == "deny"
    assert decision('obsidian vault=vault delete path="Notes/a.md"')[0] == "deny"  # no role: unchanged


def test_move_warns_when_links_dont_update(zoned):
    d, reason = decision('obsidian vault=vault move path="Notes/a.md" to="Notes/b.md"')
    assert d == "ask" and "dialog" in reason
    (zoned / ".obsidian").mkdir()
    (zoned / ".obsidian" / "app.json").write_text('{"alwaysUpdateLinks": true}')
    d, reason = decision('obsidian vault=vault move path="Notes/a.md" to="Notes/b.md"')
    assert d == "ask" and "dialog" not in reason


# -- heredocs ------------------------------------------------------------------

NOTE_WITH_CODE = "# Title\n\nRun `rm -rf x` or $(date) — just text.\nobsidian delete path=x.md\n"


def test_quoted_heredoc_body_is_text(zoned):
    cmd = f"vault-write apply Notes/a.md --from - <<'EOF'\n{NOTE_WITH_CODE}EOF"
    assert decision(cmd, CURATOR)[0] is None
    assert decision(cmd)[0] is None  # and the old guard's false "deny" on the body's text is gone


@pytest.mark.parametrize("template", [
    "bash <<'EOF'\nsed -i s/a/b/ {v}/Notes/a.md\nEOF",
    "python3 - <<'EOF'\nopen('{v}/Notes/a.md','w').write('x')\nEOF",
    "cat > {v}/Notes/a.md <<'EOF'\nhello\nEOF",
    "vault-write apply Notes/a.md --from - <<EOF\n$(rm -rf x)\nEOF",  # unquoted: the shell runs $(…)
])
def test_heredocs_that_run_or_write_are_checked(zoned, template):
    assert decision(template.replace("{v}", str(zoned)), CURATOR)[0] == "deny", template


def test_heredoc_bash_body_checked_without_role(zoned):
    assert decision("bash <<'EOF'\nobsidian delete path=x.md\nEOF")[0] == "deny"


# -- ledger: the guard records the CLI writes it lets through ---------------------

VAULT_WRITE = Path(__file__).resolve().parent.parent / "bin" / "vault-write"


def ledger_paths():
    p = Path(os.environ["XDG_STATE_HOME"]) / "archivist" / "ledger.jsonl"
    return [json.loads(l)["path"] for l in p.read_text().splitlines()] if p.exists() else []


@pytest.mark.parametrize("command,recorded", [
    ("obsidian vault=vault property:set path=Notes/a.md name=x value=y", ["Notes/a.md"]),
    ("obsidian vault=vault templater:create-from-template template=T.md file=Notes/new.md", ["Notes/new.md"]),
    ("""obsidian vault=vault quickadd:run choice=Entries vars='{"action":"close","path":"Notes/log.md"}'""", ["Notes/log.md"]),
    ("obsidian vault=vault move path=Notes/a.md to=Notes/Archive", ["Notes/a.md", "Notes/Archive/a.md"]),
    ("obsidian vault=vault rename path=Notes/a.md name=b", ["Notes/a.md", "Notes/b.md"]),
    ("obsidian vault=vault search query=x", []),  # a read
    ("obsidian vault=vault property:set path=Templates/a.md name=x value=y", []),  # denied for the curator
    ("obsidian vault=vault property:set path=Notes/a.md name=x value=y; sed -i s/a/b/ {v}/Notes/a.md", []),  # whole command denied
])
def test_cli_writes_recorded(zoned, command, recorded):
    decision(command.replace("{v}", str(zoned)), CURATOR)
    assert ledger_paths() == recorded


def test_recorded_cli_write_explains_the_change(zoned):
    (zoned / "Notes" / "a.md").write_text("by obsidian\n")
    (zoned / "Notes" / "b.md").write_text("by a bypass\n")
    decision("obsidian vault=vault property:set path=Notes/a.md name=x value=y", CURATOR)
    p = subprocess.run([str(VAULT_WRITE), "audit", "--since", "1h"], capture_output=True, text=True, env=os.environ)
    out = json.loads(p.stdout)
    assert [u["path"] for u in out["unexplained"]] == ["Notes/b.md"] and out["explained"] == 1
