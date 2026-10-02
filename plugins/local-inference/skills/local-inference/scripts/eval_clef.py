#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mlx-vlm>=0.7.4,<0.8", "huggingface_hub"]
# ///
"""Clef (open Jev/SystemOne) vs the oMLX :decide tier on AudiobookOCD BACKLOG items, Jev-style usage. Same plain-language definitions for both engines.

    eval_clef.py clef <BACKLOG.md> <hf-repo> <out.json>   # choice + noul fan-out, one call per item
    eval_clef.py qwen <BACKLOG.md> <out.json>              # oMLX :decide, two calls per item
    eval_clef.py cascade <clef.json> <qwen.json>          # clef if confident, else qwen
"""
import json, os, re, sys, time, urllib.request

AREAS = {
    "Identity": "Which book this is — one book across many files, sources, formats, locations",
    "Sources": "Where books come from — folders, AudiobookShelf, Plex, iCloud, credentials",
    "Metadata": "What the app claims about a book — tags, sidecars, artwork, naming",
    "Chapters": "A book's structure — chapter detection, chapter naming, chapter editing",
    "Transcript": "A book's text — transcription, read-along, search, retrieval, answers",
    "Audio": "A book's bytes — merge, convert, recover, verify, format",
    "Playback": "Listening — the playback engine, transport, Now Playing",
    "Library": "Many books at once — browsing, batch and long-running operations",
    "Presentation": "How the app looks and reads — theming, layout, accessibility, localization",
    "Safety": "What the app is permitted to change, and how it asks",
    "Platform": "iOS/watchOS, iCloud, Spotlight/Siri, CLI, packaging, CI, test infrastructure",
}
CONTEXT = "A backlog item for AudiobookOCD, a macOS audiobook manager and player."
TYPE = {"bug": "The item reports something that is wrong today, even when it also describes the fix",
        "improvement": "The item asks for a new or better capability, a cleanup, or tooling; nothing is broken today"}
AREA_Q = "Which one area is this backlog item most about?"
TYPE_Q = "Is this backlog item a bug or an improvement?"

LINE = re.compile(r"^- \*\*P[0-3]\*\* (bug|improvement) `([^`]+)` · [0-9-]+ · (.*)$")


def items(path):
    out = []
    for line in open(path):
        m = LINE.match(line.strip())
        if m:
            text = re.sub(r"\s*↗.*$", "", m.group(3)).replace("**", "")
            out.append({"kind": m.group(1), "areas": [a.strip() for a in m.group(2).split(",")], "text": text})
    return out


def run_clef(backlog, repo, out):
    from huggingface_hub import snapshot_download
    path = snapshot_download(repo)
    sys.path.insert(0, path)
    import clef_mlx
    model = clef_mlx.load(path)
    qs = {"type": {"type": "choice", "instructions": TYPE_Q, "criteria": TYPE},
          "area": {"type": "choice", "instructions": AREA_Q, "criteria": AREAS}}
    for a, d in AREAS.items():
        qs[f"is_{a}"] = {"type": "noul", "instructions": f"This backlog item is about the {a} area: {d}"}
    model.systemone({"model": "clef", "state": "warm", "questions": {"w": {"type": "noul"}}})
    rows = []
    for it in items(backlog):
        t = time.time()
        ans = model.systemone({"model": "clef", "state": {"context": CONTEXT, "item": it["text"]}, "questions": qs})["answers"]
        rows.append({**it, "ms": (time.time() - t) * 1000, "answers": ans})
    json.dump(rows, open(out, "w"), indent=1)


def run_qwen(backlog, out):
    key = json.load(open(os.path.expanduser("~/.omlx/settings.json")))["auth"]["api_key"]
    hdr = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    ids = json.load(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8000/v1/models", headers=hdr)))
    model = next(m["id"] for m in ids["data"] if m["id"].endswith(":decide"))

    def ask(system, user, choices):
        body = {"model": model, "temperature": 0, "max_tokens": 16,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "structured_outputs": {"choice": choices}, "chat_template_kwargs": {"enable_thinking": False}}
        req = urllib.request.Request("http://127.0.0.1:8000/v1/chat/completions", json.dumps(body).encode(), hdr)
        t = time.time()
        return json.load(urllib.request.urlopen(req, timeout=300))["choices"][0]["message"]["content"].strip(), (time.time() - t) * 1000

    def doc(criteria):
        return "\n".join(f"{k}: {v}" for k, v in criteria.items())

    ask("Answer yes or no.", "Is water wet?", ["yes", "no"])
    rows = []
    for it in items(backlog):
        k, t1 = ask(f"{CONTEXT}\n{TYPE_Q}\n{doc(TYPE)}", it["text"], list(TYPE))
        a, t2 = ask(f"{CONTEXT}\n{AREA_Q}\n{doc(AREAS)}", it["text"], list(AREAS))
        rows.append({**it, "ms": t1 + t2, "type": k, "area": a})
    json.dump(rows, open(out, "w"), indent=1)


def cascade(clef_path, qwen_path):
    c, q = json.load(open(clef_path)), json.load(open(qwen_path))
    n = len(c)
    ms = sorted(r["ms"] for r in c)
    print(f"clef: median {ms[n//2]:.0f} ms/item (all 13 questions)   qwen: median {sorted(r['ms'] for r in q)[n//2]:.0f} ms/item (2 calls)")
    fan = lambda r: max(AREAS, key=lambda a: r["answers"][f"is_{a}"]["noul"])
    print(f"clef area via noul fan-out (argmax): {sum(fan(r) in r['areas'] for r in c)}/{n}")
    for qn, right_c, right_q in (("type", lambda r: r["answers"]["type"]["choice"] == r["kind"], lambda r: r["type"] == r["kind"]),
                                 ("area", lambda r: r["answers"]["area"]["choice"] in r["areas"], lambda r: r["area"] in r["areas"])):
        print(f"\n{qn}: clef alone {sum(map(right_c, c))}/{n}   qwen alone {sum(map(right_q, q))}/{n}")
        print("  threshold  clef-answered  clef-right  cascade-total")
        for t in (0.5, 0.6, 0.7, 0.8, 0.9, 0.95):
            took = [i for i in range(n) if c[i]["answers"][qn]["confidence"] >= t]
            cr = sum(right_c(c[i]) for i in took)
            total = cr + sum(right_q(q[i]) for i in range(n) if i not in took)
            print(f"  {t:>9}  {len(took):>13}  {cr:>10}  {total:>8}/{n}")


if __name__ == "__main__":
    {"clef": lambda: run_clef(*sys.argv[2:5]), "qwen": lambda: run_qwen(*sys.argv[2:4]),
     "cascade": lambda: cascade(*sys.argv[2:4])}[sys.argv[1]]()
