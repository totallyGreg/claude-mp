Moving from standard `pip` and `python3` to **`uv`** is a massive upgrade for agentic workflows. In the context of an `agentskill`, the primary goals are speed, hermetic execution (no dependency bleeding), and minimizing the "token tax" (lengthy setup logs or complex CLI commands).

Using `uv` allows you to treat your scripts as self-contained tools rather than components of a fragile global environment.

---

## Why `uv` is Superior for AgentSkills

When an agent calls a script, you want the lowest possible latency and the highest reliability.

| Feature | Standard `pip` / `venv` | `uv` / `uvx` | Benefit for Agents |
| --- | --- | --- | --- |
| **Speed** | Slow (minutes for heavy libs) | Near-instant (milliseconds) | Faster agent response times. |
| **Isolation** | Shared or manually managed | Ephemeral / Automated | No "dependency hell" between skills. |
| **Overhead** | High (many commands/files) | Low (single binary) | Fewer tokens used for environment setup. |
| **Portability** | Requires `requirements.txt` | Inline Metadata | Everything the agent needs is in one file. |

---

## The "Best" Pattern: Inline Metadata + `uv run`

The most efficient way to run scripts within an `agentskill` is to use **PEP 723 (Inline Script Metadata)**. This allows you to define dependencies directly inside the Python script file.

Instead of managing a `requirements.txt` and a `venv` separately, your agent simply executes:

`uv run script_name.py`

### 1. The Script Format (PEP 723)

The agent (or you) writes the script with a special comment block at the top. `uv` reads this and creates a hidden, cached environment on the fly.

```python
# /// script
# dependencies = [
#   "requests",
#   "pandas",
# ]
# ///

import requests
import pandas as pd

def main():
    # Skill logic here
    print("Success")

if __name__ == "__main__":
    main()

```

### 2. The Execution Command

The `agentskill` only needs to run a single command. You don't need to check if dependencies are installed; `uv` handles it.

* **`uv run script.py`**: Best for scripts stored locally. It manages the environment automatically.
* **`uvx package@version`**: Best if the "skill" is actually a published CLI tool. It downloads, runs, and deletes (or caches) the tool in one go.

---

## Minimizing Token Usage

To keep your prompt-to-token ratio lean, you can simplify the interaction between the LLM and the shell:

1. **Skip the `pip install` logs**: You no longer need to show the agent the output of `pip install -r requirements.txt`. `uv run` handles this silently or with a very brief "Resolving..." line.
2. **Stateless Execution**: Since `uv` is so fast, you can treat every script execution as a fresh environment. This prevents the agent from getting confused by state left over from previous skill calls.
3. **Standardized Tool Call**: Define the agent's "Shell Tool" to always prepend `uv run` to Python files.

> **Note:** If your environment is extremely resource-constrained, `uv`'s global cache (located at `~/.cache/uv`) ensures that if two different skills use `pandas`, the disk space is shared via hardlinks, saving space and time.

---

## Comparison of Workflow Logic

* **Traditional:** `Check venv` → `Activate` → `Pip install` → `Python run` → `Deactivate`.
* **`uv` Pattern:** `uv run script.py`.

### Recommendation

Replace your current logic with **`uv run`**.

1. Ensure `uv` is installed in the agent's base environment.
2. Instruct the agent to include the `# /// script` metadata block when it generates or edits skills.
3. Execute using `uv run --quiet` to keep the logs clean and save tokens on the return trip.

Would you like me to provide a boilerplate `agentskill` definition that implements this `uv run` pattern?