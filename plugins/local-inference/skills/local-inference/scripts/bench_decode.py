#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Prefill and decode speed of oMLX models on one real file, thinking off, greedy.

    bench_decode.py <file-to-explain> <model-id> [<model-id> ...]

Prefill tok/s = prompt tokens / time to the first content chunk; each run
starts with a different nonce so the prefix cache can't serve it.
Decode tok/s = (completion tokens - 1) / (time from first content chunk to the
end), so prefill is excluded. Token counts come from the streamed usage, not
the chunk count: oMLX's burst decode can pack several tokens into a chunk.
Runs three times per model and reports the medians. Use a large file (30K+
characters) so prefill is measured on a code-sized prompt.
"""
import json
import os
import statistics
import sys
import time
import urllib.request
import uuid

KEY = json.load(open(os.path.expanduser("~/.omlx/settings.json")))["auth"]["api_key"]


def run(model: str, text: str) -> tuple[float, float, int]:
    """(prefill tok/s, decode tok/s, prompt tokens) for one streamed request."""
    body = {"model": model, "temperature": 0, "max_tokens": 400, "stream": True,
            "stream_options": {"include_usage": True},
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": [{"role": "user", "content": f"[run {uuid.uuid4()}] Explain what this file does, section by section:\n\n" + text}]}
    req = urllib.request.Request("http://127.0.0.1:8000/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    start = time.time()
    first = 0.0
    usage: dict = {}
    with urllib.request.urlopen(req, timeout=900) as r:
        for raw in r:
            line = raw.decode().strip()
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            event = json.loads(line[6:])
            if event.get("usage"):
                usage = event["usage"]
            choices = event.get("choices") or [{}]
            if choices[0].get("delta", {}).get("content") and not first:
                first = time.time()
    tokens = usage.get("completion_tokens", 0)
    if not first or tokens < 2:
        raise RuntimeError(f"{model}: no content or usage in the stream")
    prompt = usage.get("prompt_tokens", 0)
    return prompt / (first - start), (tokens - 1) / (time.time() - first), prompt


text = open(sys.argv[1]).read()
for model in sys.argv[2:]:
    run(model, "warm up")
    runs = [run(model, text) for _ in range(3)]
    pre = statistics.median(r[0] for r in runs)
    dec = statistics.median(r[1] for r in runs)
    print(f"{model}: prefill {pre:.0f} tok/s on {runs[0][2]} tokens, decode {dec:.1f} tok/s "
          f"(decode runs {', '.join(f'{r[1]:.1f}' for r in runs)})", flush=True)
