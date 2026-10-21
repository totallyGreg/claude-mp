#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""One long request through a tier per KV-compression setting, model reloaded each time.

    kv_probe.py <model> <profile-id> <target-tokens> <corpus-dir> <scheme> [<scheme> ...]
    scheme: off | affine4 | affine8 | turboquant8

Unloads every model, applies the setting, sends one streamed request of
~target tokens of the *.md and *.py files under corpus-dir (unique nonce,
thinking off, greedy, 300 output tokens; prose runs ~4 chars/token) with a
needle fact placed near the start, and polls the admin stats for peak memory.
Prints TTFT, decode tok/s, peak memory, and whether the needle came back.
Turns compression off at the end.
"""
import glob
import json
import os
import threading
import time
import urllib.request
import uuid

KEY = json.load(open(os.path.expanduser("~/.omlx/settings.json")))["auth"]["api_key"]
BASE = "http://127.0.0.1:8000"
HDR = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
SETTINGS = {"off": {"turboquant_kv_enabled": False},
            "affine4": {"turboquant_kv_enabled": True, "turboquant_kv_scheme": "affine4", "turboquant_kv_bits": 4},
            "affine8": {"turboquant_kv_enabled": True, "turboquant_kv_scheme": "affine8", "turboquant_kv_bits": 8},
            "turboquant8": {"turboquant_kv_enabled": True, "turboquant_kv_scheme": "turboquant", "turboquant_kv_bits": 8}}


def call(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(BASE + path, json.dumps(body).encode() if body is not None else None, HDR, method=method)
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read()
    return json.loads(raw) if raw else {}


def memory() -> tuple[int, list[str]]:
    s = call("GET", "/admin/api/stats")["active_models"]
    return s["memory_pressure"]["current_bytes"], [m["id"] for m in s["models"]]


def corpus(root: str, target_chars: int) -> str:
    parts, size = [], 0
    for path in sorted(glob.glob(f"{root}/**/*.md", recursive=True) + glob.glob(f"{root}/**/*.py", recursive=True)):
        text = open(path, errors="ignore").read()
        parts.append(f"\n\n===== {path} =====\n{text}")
        size += len(parts[-1])
        if size >= target_chars:
            break
    return "".join(parts)[:target_chars]


def probe(profile: str, body_text: str) -> dict:
    needle = f"The maintenance passphrase for the archive server is {uuid.uuid4().hex[:8]}."
    prompt = (f"[run {uuid.uuid4()}]\n{needle}\n{body_text}\n\n"
              "First, state the maintenance passphrase for the archive server exactly. "
              "Then summarize what these files are for in five bullets.")
    body = {"model": profile, "temperature": 0, "max_tokens": 300, "stream": True,
            "stream_options": {"include_usage": True},
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": [{"role": "user", "content": prompt}]}
    peak, stop = [0], threading.Event()

    def poll():
        while not stop.is_set():
            try:
                peak[0] = max(peak[0], memory()[0])
            except Exception:
                pass
            time.sleep(0.5)

    threading.Thread(target=poll, daemon=True).start()
    req = urllib.request.Request(BASE + "/v1/chat/completions", json.dumps(body).encode(), HDR)
    start, first, usage, out = time.time(), 0.0, {}, []
    with urllib.request.urlopen(req, timeout=3600) as r:
        for raw in r:
            line = raw.decode().strip()
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            event = json.loads(line[6:])
            if event.get("usage"):
                usage = event["usage"]
            delta = (event.get("choices") or [{}])[0].get("delta", {}).get("content")
            if delta:
                first = first or time.time()
                out.append(delta)
    end = time.time()
    time.sleep(1)
    stop.set()
    text = "".join(out)
    code = needle.split()[-1].rstrip(".")
    return {"prompt": usage.get("prompt_tokens"), "ttft": first - start,
            "decode": (usage.get("completion_tokens", 0) - 1) / (end - first),
            "peak_gb": peak[0] / 1e9, "needle": code in text, "head": text[:120].replace("\n", " ")}


if __name__ == "__main__":
    import sys
    model, profile, target = sys.argv[1], sys.argv[2], int(sys.argv[3])
    body_text = corpus(sys.argv[4], target * 4)
    try:
        for scheme in sys.argv[5:]:
            for m in memory()[1]:
                call("POST", f"/admin/api/models/{m}/unload")
            time.sleep(3)
            call("PUT", f"/admin/api/models/{model}/settings", SETTINGS[scheme])
            idle = memory()[0]
            r = probe(profile, body_text)
            print(f"{scheme}: prompt {r['prompt']} tok, TTFT {r['ttft']:.0f}s, decode {r['decode']:.1f} tok/s, "
                  f"peak {r['peak_gb']:.1f} GB (idle before load {idle / 1e9:.1f} GB), needle {'OK' if r['needle'] else 'MISSED'} | {r['head']}",
                  flush=True)
    finally:
        call("PUT", f"/admin/api/models/{model}/settings", SETTINGS["off"])
        print("restored: KV compression off", flush=True)
