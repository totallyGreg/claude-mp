#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Compare candidate decide-tier models on real labelled data: AudiobookOCD BACKLOG.md items.

    eval_decide.py <BACKLOG.md> <model-id> [<model-id> ...]

<model-id> is an oMLX model, or `fm` for Apple's on-device model (macOS 27; the
choices become an enum in fm's schema dialect). Each Work line carries its true type (bug|improvement) and Area(s); the model sees
only the title and sentence. Prints type and area accuracy and latency per model.
"""
import json, os, re, subprocess, sys, time, urllib.request
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


def ask_fm(system, user, choices):
    schema = {"title": "Answer", "type": "object", "additionalProperties": False, "x-order": ["answer"],
              "required": ["answer"], "properties": {"answer": {"type": "string", "enum": choices}}}
    path = f"/tmp/eval_decide_fm_{os.getpid()}.json"
    json.dump(schema, open(path, "w"))
    t = time.time()
    r = subprocess.run(["fm", "respond", "--no-stream", "-g", "-i", system, "--schema", path],
                       input=user, capture_output=True, text=True)  # item on stdin, as the oMLX user message
    try:
        out = json.loads(r.stdout)["answer"]
    except (ValueError, KeyError):  # refusals and errors count as wrong
        out = "ERROR"
        print(f"fm error: {(r.stderr.strip() or r.stdout.strip())[:100]} <- {user[:60]}", file=sys.stderr)
    return out, time.time() - t


def ask(model, system, user, choices):
    if model == "fm":
        return ask_fm(system, user, choices)
    key = json.load(open(os.path.expanduser("~/.omlx/settings.json")))["auth"]["api_key"]
    body = {"model": model, "temperature": 0, "max_tokens": 16,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "structured_outputs": {"choice": choices},
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request("http://127.0.0.1:8000/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
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
