"""pi_agents.py: Bash maps to Pi bash only when the agent's extension adds a guarded bash."""
import importlib.util
from pathlib import Path

import yaml

SCRIPT = Path(__file__).resolve().parents[1] / "skills/local-inference/scripts/pi_agents.py"
spec = importlib.util.spec_from_file_location("pi_agents", SCRIPT)
pa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pa)

AGENT = "---\nname: {n}\ndescription: |\n  Does things.\n\n  More.\ntools: [\"Read\", \"Bash\", \"Agent\"]\n---\nBody.\n"


def make(tmp_path, ext_line=None):
    plugin = tmp_path / "plug"
    (plugin / "agents").mkdir(parents=True)
    for n in ("one", "two"):
        (plugin / "agents" / f"{n}.md").write_text(AGENT.format(n=n))
    if ext_line:
        (plugin / "pi" / "extensions").mkdir(parents=True)
        (plugin / "pi" / "extensions" / "one.ts").write_text(ext_line + "\nexport default () => {};\n")
    text = pa.translate(plugin, plugin / "agents" / "one.md", "omlx/code", ["one", "two"])
    fm = yaml.safe_load(text.split("---\n")[1])
    return fm, text


def test_bash_dropped_without_guarded_extension(tmp_path):
    fm, text = make(tmp_path)
    assert "bash" not in fm["tools"].split(", ")
    assert "Not available here: Bash" in text and "No shell" in text


def test_bash_kept_when_extension_adds_it(tmp_path):
    fm, text = make(tmp_path, "// entry. Tools it adds: bash")
    assert fm["tools"].split(", ") == ["read", "bash"]
    assert fm["extensions"].endswith("pi/extensions/one.ts")
    assert "No shell" not in text and "runs through the plugin's guard" in text
    assert "Not available here: Bash" not in text


def test_nested_agents_limited_to_plugin(tmp_path):
    fm, _ = make(tmp_path)
    assert fm["allowNestedSubagents"] is True and fm["allowedAgents"] == "two"
