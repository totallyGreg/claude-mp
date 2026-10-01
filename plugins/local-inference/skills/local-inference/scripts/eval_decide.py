#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Compare candidate decide-tier models on real labelled data: AudiobookOCD BACKLOG.md items.

    eval_decide.py <BACKLOG.md> <model-id> [<model-id> ...]

Each Work line carries its true type (bug|improvement) and Area(s); the model sees
only the title and sentence. Prints type and area accuracy and latency per model.
"""
import json, os, re, sys, time, urllib.request

KEY = json.load(open(os.path.expanduser("~/.omlx/settings.json")))["auth"]["api_key"]
AREAS = ["Identity", "Sources", "Metadata", "Chapters", "Transcript", "Audio",
         "Playback", "Library", "Presentation", "Safety", "Platform"]
AREA_DOC = """Identity: which book this is across files/sources/formats. Sources: where books come from (folders, AudiobookShelf, Plex, iCloud, credentials). Metadata: tags, sidecars, artwork, naming. Chapters: detection, naming, editing. Transcript: transcription, read-along, search. Audio: merge, convert, recover, verify bytes. Playback: engine, transport, Now Playing. Library: many books at once, browsing, batch operations. Presentation: theming, layout, accessibility. Safety: what the app may change and how it asks. Platform: iOS, iCloud, Spotlight, CLI, packaging, CI, test infrastructure."""

LINE = re.compile(r"^- \*\*P[0-3]\*\* (bug|improvement) `([^`]+)` · [0-9-]+ · (.*)$")
items = []
for line in open(sys.argv[1]):
    m = LINE.match(line.strip())
    if m:
        text = re.sub(r"\s*↗.*$", "", m.group(3)).replace("**", "")
        items.append((m.group(1), {a.strip() for a in m.group(2).split(",")}, text))


def ask(model, system, user, choices):
    body = {"model": model, "temperature": 0, "max_tokens": 16,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "structured_outputs": {"choice": choices},
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request("http://127.0.0.1:8000/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    t = time.time()
    out = json.load(urllib.request.urlopen(req, timeout=300))["choices"][0]["message"]["content"].strip()
    return out, time.time() - t


for model in sys.argv[2:]:
    ask(model, "Answer yes or no.", "Is water wet?", ["yes", "no"])  # load + warm
    kind_ok = area_ok = 0
    lat = []
    for kind, areas, text in items:
        k, t1 = ask(model, "Classify the backlog item. bug = something behaves wrongly; improvement = new or better capability, cleanup, or tooling.",
                    text, ["bug", "improvement"])
        a, t2 = ask(model, "Classify the backlog item by the one area it is most about.\n" + AREA_DOC, text, AREAS)
        kind_ok += k == kind
        area_ok += a in areas
        lat += [t1, t2]
    lat.sort()
    print(f"{model}: type {kind_ok}/{len(items)}  area {area_ok}/{len(items)}  "
          f"median {lat[len(lat)//2]*1000:.0f}ms  p90 {lat[int(len(lat)*.9)]*1000:.0f}ms", flush=True)
