#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Aggregate throughput of N concurrent oMLX requests at a given prompt size.

    bench_parallel.py <file> <model> <prompt-tokens-approx> <n> [<n> ...]

Each request gets its own nonce (no prefix-cache hits), thinking off, greedy,
max_tokens 400. Reports wall time, aggregate completion tok/s over the wall
time, and median per-request decode tok/s (first content chunk to end).
"""
import concurrent.futures as cf
import json
import os
import statistics
import sys
import time
import urllib.request
import uuid

KEY = json.load(open(os.path.expanduser("~/.omlx/settings.json")))["auth"]["api_key"]


def run(model: str, text: str) -> tuple[int, float, float]:
    body = {"model": model, "temperature": 0, "max_tokens": 400, "stream": True,
            "stream_options": {"include_usage": True},
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": [{"role": "user", "content": f"[run {uuid.uuid4()}] Explain what this file does, section by section:\n\n" + text}]}
    req = urllib.request.Request("http://127.0.0.1:8000/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    start, first, usage = time.time(), 0.0, {}
    with urllib.request.urlopen(req, timeout=1800) as r:
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
    end = time.time()
    tokens = usage.get("completion_tokens", 0)
    return tokens, (tokens - 1) / (end - first), first - start


src = open(sys.argv[1]).read()
model, approx = sys.argv[2], int(sys.argv[3])
text = (src * (approx * 4 // len(src) + 1))[: approx * 3]  # ~3 chars/token for this code
run(model, "warm up")
for n in map(int, sys.argv[4:]):
    start = time.time()
    with cf.ThreadPoolExecutor(n) as pool:
        results = list(pool.map(lambda _: run(model, text), range(n)))
    wall = time.time() - start
    total = sum(r[0] for r in results)
    print(f"{model} ~{approx // 1000}K x{n}: wall {wall:.1f}s, aggregate {total / wall:.1f} tok/s, "
          f"per-request decode median {statistics.median(r[1] for r in results):.1f} tok/s, "
          f"TTFT median {statistics.median(r[2] for r in results):.1f}s", flush=True)
