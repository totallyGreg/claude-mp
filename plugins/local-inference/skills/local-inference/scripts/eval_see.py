#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Score the `see` tier backends on an image set with ground truth.

    eval_see.py <image-dir> fm omlx

Runs each case through scripts/see.sh with --fm or --omlx (oMLX's :fast
profile), so it measures the shipped code. --omlx refuses codes (they always
go to fm), which shows as an error row. Make a set with see_eval_images.py.

<image-dir>/truth.json lists cases: file, kind (text | pixels | code, the
see.sh mode), schema (JSON Schema or null), prompt, expect. Each field is
scored exact after normalizing (case, whitespace, currency symbols and
thousands separators in numbers). Prints one row per case per backend, then
fields correct, cases fully correct, refusals/errors, median and p90 latency.
"""
import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SEE = Path(__file__).resolve().parent / "see.sh"


def norm(v):
    if isinstance(v, (int, float)):
        return round(float(v), 2)
    s = str(v).strip()
    try:
        return round(float(s.replace(",", "").lstrip("$€¥£")), 2)
    except ValueError:
        return " ".join(s.lower().split())


def run(backend: str, case: dict, img: Path) -> dict:
    cmd = [str(SEE), f"--{backend}"]
    if case["kind"] == "code":
        cmd += ["--code", str(img)]
    else:
        schema = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(case["schema"], schema)
        schema.close()
        cmd += (["--text"] if case["kind"] == "text" else []) + ["--schema", schema.name, str(img), case["prompt"]]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout).strip().splitlines()[-1][:120])
    return {"payload": p.stdout.strip()} if case["kind"] == "code" else json.loads(p.stdout)


cases = json.loads((Path(sys.argv[1]) / "truth.json").read_text())
for backend in sys.argv[2:]:
    fields = ok_fields = full = failed = 0
    times = []
    for case in cases:
        img = Path(sys.argv[1]) / case["file"]
        start = time.time()
        try:
            got = run(backend, case, img)
            err = ""
        except Exception as e:
            got, err = {}, f"ERROR {e}"
            failed += 1
        times.append(time.time() - start)
        wrong = {k: got.get(k) for k, v in case["expect"].items() if norm(got.get(k, "")) != norm(v)}
        fields += len(case["expect"])
        ok_fields += len(case["expect"]) - len(wrong)
        full += not wrong
        print(f"{backend} | {case['id']}: {times[-1]:.1f}s {'OK' if not wrong else err or f'wrong {wrong}'}", flush=True)
    times.sort()
    print(f"== {backend}: fields {ok_fields}/{fields}, cases {full}/{len(cases)}, errors/refusals {failed}, "
          f"median {statistics.median(times):.1f}s, p90 {times[int(len(times) * 0.9) - 1]:.1f}s\n", flush=True)
