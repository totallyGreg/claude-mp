#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Make a Claude Code plugin's agents available to Pi as pi-subagents agents.

    pi_agents.py <plugin-dir> [--model splash/code] [--check]

Reads <plugin-dir>/agents/*.md (Claude Code agent files) and writes one
pi-subagents agent per file to ${PI_CODING_AGENT_DIR:-~/.pi/agent}/agents/<plugin>/,
which pi-subagents discovers by itself. The Claude files stay the single source:
re-run this after the plugin changes. --check reports what would change.

Translation:
- name, body (the system prompt) — kept; a "Running in Pi" note is appended.
- description — its first paragraph (the <example> blocks are for Claude's router).
- tools — Read→read, Grep→grep, Glob→find,ls, Edit→edit, Write→write.
  Agent → nested `subagent` runs, limited to this plugin's other agents.
  Bash, AskUserQuestion, SendMessage — no Pi equivalent here; dropped and named
  in the note. (Bash for Pi goes through pi_sandboxed.sh, never a plain tool.)
- skills — "plugin:skill" → `skills: skill` + `skillPath: <plugin>/skills`.
- model — --model (a tier, default splash/code), not the Claude model.
- extensions — <plugin>/pi/extensions/<agent>.ts when it exists. A first line
  "Tools it adds: a, b" puts those tools on the allowlist.
"""
import argparse
import os
import re
import sys
from pathlib import Path

import yaml

TOOLS = {"Read": ["read"], "Grep": ["grep"], "Glob": ["find", "ls"], "Edit": ["edit"], "Write": ["write"]}
DROPPED = {"Bash", "AskUserQuestion", "SendMessage", "NotebookEdit", "WebFetch", "WebSearch"}


def split(text: str) -> tuple[dict, str]:
    m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
    if not m:
        raise ValueError("no YAML frontmatter")
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def first_paragraph(description: str) -> str:
    return " ".join(description.strip().split("\n\n")[0].split())


def extension_tools(path: Path) -> list[str]:
    m = re.search(r"Tools it adds:\s*(.+)", path.read_text().splitlines()[0])
    return [t.strip() for t in m.group(1).split(",")] if m else []


def translate(plugin: Path, src: Path, model: str, siblings: list[str]) -> str:
    fm, body = split(src.read_text())
    name = fm["name"]
    claude_tools = fm.get("tools") or []
    tools, dropped = [], []
    for t in claude_tools:
        if t in TOOLS:
            tools += [x for x in TOOLS[t] if x not in tools]
        elif t != "Agent":
            dropped.append(t)
    unknown = [t for t in dropped if t not in DROPPED]
    if unknown:
        print(f"warning: {src.name}: no Pi mapping for {', '.join(unknown)}; dropped", file=sys.stderr)

    ext = plugin / "pi" / "extensions" / f"{name}.ts"
    ext_tools = extension_tools(ext) if ext.exists() else []
    tools += [t for t in ext_tools if t not in tools]

    skills = [s.split(":", 1)[-1] for s in fm.get("skills") or []]
    out = {
        "name": name,
        "description": first_paragraph(fm.get("description", "")),
        "model": model,
        "tools": ", ".join(tools),
        "systemPromptMode": "append",
        "inheritProjectContext": False,
        "inheritSkills": False,
    }
    if skills:
        out["skills"] = ", ".join(skills)
        out["skillPath"] = str(plugin / "skills")
    if ext.exists():
        out["extensions"] = str(ext)
    others = [s for s in siblings if s != name]
    if "Agent" in claude_tools:
        out["allowNestedSubagents"] = True
        out["allowedAgents"] = ", ".join(others)
    else:
        out["allowedAgents"] = ""

    note = ["", "## Running in Pi", "",
            f"You run in Pi on a local model, generated from the Claude Code agent `{src.relative_to(plugin.parent)}`. "
            "Where the instructions above name a tool you don't have, adapt:"]
    if dropped:
        note.append(f"- Not available here: {', '.join(dropped)}. Skip a step that needs one and say so in your final report; "
                    "if a step needs the user's decision, stop and report the options instead of guessing.")
    if "Bash" in dropped:
        note.append("- No shell: the skill's scripts and CLIs can't run. Read and search files directly.")
    if ext_tools:
        note.append(f"- Extension tools: {', '.join(ext_tools)}. Use them for the writes the instructions do through the CLI.")
    if "Agent" in claude_tools:
        note.append(f"- To hand work to another agent, use the subagent tool with one of: {', '.join(others)}.")
    note.append("- A blocked tool call is a policy decision, not an error to work around: report it.")
    header = yaml.safe_dump(out, sort_keys=False, allow_unicode=True, width=10_000)
    return f"---\n{header}---\n{body.rstrip()}\n" + "\n".join(note) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("plugin", type=Path)
    ap.add_argument("--model", default="splash/code")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    plugin = a.plugin.expanduser().resolve()
    sources = sorted((plugin / "agents").glob("*.md"))
    if not sources:
        print(f"no agents in {plugin}/agents", file=sys.stderr)
        return 1
    siblings = [split(s.read_text())[0]["name"] for s in sources]
    dest = Path(os.environ.get("PI_CODING_AGENT_DIR", "~/.pi/agent")).expanduser() / "agents" / plugin.name
    if not a.check:
        dest.mkdir(parents=True, exist_ok=True)
    for src in sources:
        text = translate(plugin, src, a.model, siblings)
        target = dest / src.name
        state = "new" if not target.exists() else "same" if target.read_text() == text else "changed"
        print(f"{state:8} {target}")
        if not a.check and state != "same":
            target.write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
