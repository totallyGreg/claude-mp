"""check_merge_preserved.py: a restructured merge passes; a dropped or reworded line fails."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "vault-curator" / "scripts" / "check_merge_preserved.py"

A = """---
title: A
---
# A
## **Tools**
- **Harbor**: runs multiple AI services. See [[Harbor]].
| Tool | Use |
| ---- | --- |
| Ollama | serving |
"""

B = """# B
Intro from [docs](https://example.com/b).
"""

# Restructured: new H1, heading level and bold changed, table re-padded with an NBSP, sections reordered.
MERGED_OK = """---
title: A
aliases: [B]
---
# A
Intro from [docs](https://example.com/b).
### Tools
- **Harbor**: runs multiple AI services. See [[Harbor]].
| Tool   | Use     |
|--------|---------|
| Ollama | serving |
"""


def run(tmp_path, merged):
    files = {}
    for name, text in {"a.md": A, "b.md": B, "merged.md": merged}.items():
        files[name] = tmp_path / name
        files[name].write_text(text)
    proc = subprocess.run([sys.executable, SCRIPT, "--merged", files["merged.md"], files["a.md"], files["b.md"]],
                          capture_output=True, text=True)
    return proc.returncode, json.loads(proc.stdout)


def test_restructured_merge_passes(tmp_path):
    code, out = run(tmp_path, MERGED_OK)
    assert code == 0 and out["ok"]
    assert [h["line"] for h in out["missing_headings"]] == ["# B"]  # reported, not failing


def test_reworded_line_fails(tmp_path):
    code, out = run(tmp_path, MERGED_OK.replace("multiple AI services", "multiple LLM services"))
    assert code == 1 and not out["ok"]
    assert [m["line"] for m in out["missing_lines"]] == ["- **Harbor**: runs multiple AI services. See [[Harbor]]."]


def test_dropped_url_and_wikilink_fail(tmp_path):
    code, out = run(tmp_path, MERGED_OK.replace("(https://example.com/b)", "").replace("[[Harbor]]", "Harbor"))
    assert code == 1
    assert out["missing_urls"] == ["https://example.com/b"]
    assert out["missing_wikilinks"] == ["[[Harbor]]"]
