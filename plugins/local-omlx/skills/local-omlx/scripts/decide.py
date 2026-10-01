#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Ask the local `decide` tier one constrained question; print only the answer.

    decide.py --choices fast,code,deep "Which tier fits: rename 40 test files?"
    decide.py --schema schema.json "Extract the version and date from: ..."
    cat item.txt | decide.py --choices bug,improvement --system "Classify the backlog item."

The output is grammar-constrained by oMLX: with --choices it is exactly one of
the choices; with --schema it is JSON matching the schema. Exit 1 on error.
"""

import argparse
import json
import os
import sys
import urllib.request

BASE = "http://127.0.0.1:8000/v1"
TIER = ":decide"  # the exposed oMLX profile; which model backs it is in references/tiers.md


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


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    shape = p.add_mutually_exclusive_group(required=True)
    shape.add_argument("--choices", help="comma-separated allowed answers")
    shape.add_argument("--schema", help="path to a JSON Schema file")
    p.add_argument("--system", default="Answer the question.", help="instruction for the model")
    p.add_argument("question", nargs="?", help="the question; read from stdin when omitted")
    a = p.parse_args()

    question = a.question if a.question is not None else sys.stdin.read()
    if a.choices:
        constraint = {"choice": [c.strip() for c in a.choices.split(",") if c.strip()]}
    else:
        with open(a.schema) as f:
            constraint = {"json": json.load(f)}

    try:
        key = api_key()
        body = {
            "model": decide_model(key),
            "messages": [{"role": "system", "content": a.system}, {"role": "user", "content": question}],
            "structured_outputs": constraint,
        }
        print(call("/chat/completions", key, body)["choices"][0]["message"]["content"].strip())
    except Exception as e:  # noqa: BLE001 — one line for the caller, not a traceback
        print(f"decide: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
