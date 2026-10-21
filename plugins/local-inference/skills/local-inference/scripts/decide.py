#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Ask the local `decide` tier one constrained question; print only the answer.

    decide.py --choices fast,code,deep "Which tier fits: rename 40 test files?"
    decide.py --schema schema.json "Extract the version and date from: ..."
    cat item.txt | decide.py --choices bug,improvement --system "Classify the backlog item."

With --choices the answer is exactly one of the choices: oMLX's decision model
(d3-flash, `/v1/decisions`) picks it, or — when that model isn't installed,
fails, or --chat is given — the `:decide` chat model under a choice grammar.
With --schema it is JSON matching the schema, always from the chat model.
Exit 1 on error.

**Guardrails:**
- Rejects >20 choices (the model's accuracy drops sharply with many options).
- Requires --system with a criterion when using --choices (no bare "pick one").
- If --choices has an "other" option, the model can abstain instead of guessing.
- The grammar guarantees the *shape* of the answer, not its correctness.
  When in doubt, run again with a sharper criterion or fall back to the cloud model.
"""

import argparse
import json
import os
import sys
import urllib.request

BASE = "http://127.0.0.1:8000/v1"
TIER = ":decide"  # the exposed oMLX profile; which model backs it is in references/tiers.md
DECISION_MODEL = "d3-flash-oQ8e"  # labels via /v1/decisions; references/tiers.md derivation 15


def api_key() -> str:
    with open(os.path.expanduser("~/.omlx/settings.json")) as f:
        return json.load(f)["auth"]["api_key"]


def call(path: str, key: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        BASE + path, json.dumps(body).encode() if body else None,
        {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def decide_model(key: str) -> str:
    """The served ID ending in :decide, so swapping its model needs no edit here.

    Resolved from /v1/models rather than configurable: oMLX's model_fallback
    answers an unknown model name with some other model, silently.
    """
    ids = [m["id"] for m in call("/models", key)["data"] if m["id"].endswith(TIER)]
    if len(ids) != 1:
        raise RuntimeError(f"expected one oMLX model ending in {TIER}, found {ids}")
    return ids[0]


def chat(key: str, system: str, question: str, constraint: dict) -> str:
    body = {
        "model": decide_model(key),
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": question}],
        "structured_outputs": constraint,
    }
    return call("/chat/completions", key, body)["choices"][0]["message"]["content"].strip()


def decision(key: str, system: str, question: str, choices: list[str]) -> str:
    """One `choice` question to the decision model; its answer is always one of the choices."""
    body = {"model": DECISION_MODEL, "input": question,
            "questions": [{"type": "choice", "name": "answer", "instructions": system, "choices": choices}]}
    return call("/decisions", key, body)["answers"][0]["choice"]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    shape = p.add_mutually_exclusive_group(required=True)
    shape.add_argument("--choices", help="comma-separated allowed answers")
    shape.add_argument("--schema", help="path to a JSON Schema file")
    p.add_argument("--system", default="Answer the question.", help="instruction for the model")
    p.add_argument("--chat", action="store_true", help="--choices on the :decide chat model, not the decision model")
    p.add_argument("question", nargs="?", help="the question; read from stdin when omitted")
    a = p.parse_args()

    question = a.question if a.question is not None else sys.stdin.read()
    if a.choices:
        choices = [c.strip() for c in a.choices.split(",") if c.strip()]
        if len(choices) > 20:
            print(f"decide: too many choices ({len(choices)}); cap is 20 — split the question or narrow the options", file=sys.stderr)
            return 1
        if a.system.strip() == "Answer the question.":
            print("decide: --choices requires --system with a criterion (e.g. 'Classify this as bug or improvement')", file=sys.stderr)
            return 1
        constraint = {"choice": choices}
    else:
        with open(a.schema) as f:
            constraint = {"json": json.load(f)}

    try:
        key = api_key()
        if a.choices and not a.chat and any(m["id"] == DECISION_MODEL for m in call("/models", key)["data"]):
            try:
                print(decision(key, a.system, question, constraint["choice"]))
                return 0
            except Exception as e:  # noqa: BLE001
                print(f"decide: {DECISION_MODEL} failed ({e}); using the chat model", file=sys.stderr)
        print(chat(key, a.system, question, constraint))
    except Exception as e:  # noqa: BLE001 — one line for the caller, not a traceback
        print(f"decide: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
