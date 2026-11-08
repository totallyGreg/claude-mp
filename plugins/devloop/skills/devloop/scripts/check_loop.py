"""Fail when the development loop is left half-done.

Each rule is a step that prose alone kept missing (AudiobookOCD,
Scripts/check-loop.py, where each one has its history):

1. BACKLOG § Work is groups of one-line items in a fixed grammar, so a
   script and an agent can rank it without reading paragraphs:
       ### <Group> — P<n> · since <YYYY-MM-DD>
       - **P<n>** bug|improvement `Area, Area` · <YYYY-MM-DD> · **Title** — sentence. [↗](backlog/x.md)
   Every Area is in loop.toml's `areas`; detail lives in backlog/, never on
   continuation lines.
2. Nothing sinks: a group's priority is its highest item's and its date its
   oldest item's; groups run by priority, then oldest first, and so do the
   items inside them. An appended list buries whatever has waited longest.
3. BACKLOG carries a `Reviewed:` date — review-due compares it with releases.
4. Every PLAN queued stage carries a priority.
5. BACKLOG § Now holds `max_now` items at most, and at most one **Itch**.
   Its first item is the ranking's top, or says why not — `**Itch** —` or
   `**Chosen** — <reason> —`.
6. No INBOX Open line is struck or says it is done — triage deletes the
   line, and what is left of finished work moves to BACKLOG.
7. No BACKLOG § Blocked row goes unchecked for more than
   `max_blocked_age_days`.
8. A stage's progress lives in one place, its file's `## Steps` checklist.
   PLAN's Why says why, never how far; a Status line carries no step
   progress; a Now line naming a stage with a checklist names an open step
   ("S72 step 2"); a stage whose steps are all done is `**Status:** shipped`
   and gone from PLAN and Now. With `loop.placement`, a stage in Now has a
   `**Placement:**` line saying where its code goes.
9. BACKLOG § Verify is one line per manual check, oldest first, each saying
   why no automated test can do it: `- **Subject** · <date> · what — no test: <why>.`
10. Every stage file declares an `**Area:**` from `areas`.
"""

from __future__ import annotations

import re
from datetime import date

import ranking
from config import Config

PRIORITY = re.compile(r"^P[0-3]$")
PROGRESS = re.compile(r"\b(steps? \d|shipped|remains?|in progress|next the)\b", re.I)
GROUP = re.compile(r"^### (.+) — (P[0-3]) · since (20\d\d-\d\d-\d\d)$")
ITEM = re.compile(r"^- \*\*(P[0-3])\*\* (bug|improvement) `([^`]+)` · (20\d\d-\d\d-\d\d) · \*\*[^*]+\*\* — \S")
VERIFY = re.compile(r"^- \*\*[^*]+\*\* · (20\d\d-\d\d-\d\d) · \S.* — no test: \S")


class Loop:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.failures: list[str] = []
        self.backlog_name = cfg.docname("backlog")
        self.plan_name = cfg.docname("plan")
        self.inbox_name = cfg.docname("inbox")
        self.stages = cfg["docs"]["stages_dir"]

    def fail(self, message: str) -> None:
        self.failures.append(message)

    def read_optional(self, rel: str) -> str | None:
        path = self.cfg.root / rel
        return path.read_text(encoding="utf-8") if path.is_file() else None

    def section_lines(self, text: str, name: str, heading: str):
        body, start = ranking.section(text, heading)
        if not re.search(rf"^## {re.escape(heading)}\s*$", text, re.M):
            self.fail(f"{name}: no '## {heading}' section")
        return enumerate(body.splitlines(), start)

    def table_rows(self, text: str, name: str, heading: str):
        rows = [(n, [c.strip() for c in l.strip().strip("|").split("|")])
                for n, l in self.section_lines(text, name, heading)
                if l.startswith("|") and not re.match(r"^\|[-\s|]+\|$", l)]
        return rows[1:]  # drop the header row

    def stage_path(self, sid: str) -> str | None:
        found = sorted((self.cfg.root / self.stages).glob(f"s{sid[1:].lower()}-*.md"))
        return f"{self.stages}/{found[0].name}" if found else None

    # Rules 1 and 2
    def check_work(self, backlog: str) -> None:
        areas, b = set(self.cfg["areas"]), self.backlog_name
        groups: list[dict] = []
        for n, line in self.section_lines(backlog, b, "Work"):
            if line.startswith("### "):
                m = GROUP.match(line)
                if not m:
                    self.fail(f"{b}:{n}: group heading must be '### Name — P0-3 · since YYYY-MM-DD'")
                    groups.append({"n": n, "p": "P9", "since": "9999-99-99", "items": []})
                    continue
                groups.append({"n": n, "p": m.group(2), "since": m.group(3), "items": []})
            elif line.startswith("- "):
                m = ITEM.match(line)
                if not m:
                    self.fail(f"{b}:{n}: item must be '- **P0-3** bug|improvement `Area` · YYYY-MM-DD · **Title** — …'")
                    continue
                if not groups:
                    self.fail(f"{b}:{n}: item outside a group — put it under a '### ' heading")
                    continue
                for area in (a.strip() for a in m.group(3).split(",")):
                    if area not in areas:
                        self.fail(f"{b}:{n}: unknown Area '{area}' — loop.toml `areas` lists the known ones")
                groups[-1]["items"].append({"p": m.group(1), "date": m.group(4)})
            elif line.startswith("  ") and line.strip() and groups:
                self.fail(f"{b}:{n}: one line per item — move the detail to "
                          f"{self.cfg['docs']['backlog_dir']}/<slug>.md and link it")
        for g in groups:
            items = g["items"]
            if not items:
                self.fail(f"{b}:{g['n']}: group has no items — delete it")
                continue
            top, oldest = min(i["p"] for i in items), min(i["date"] for i in items)
            if g["p"] != top or g["since"] != oldest:
                self.fail(f"{b}:{g['n']}: group heading should read '{top} · since {oldest}' (its items)")
            order = [(i["p"], i["date"]) for i in items]
            if order != sorted(order):
                self.fail(f"{b}:{g['n']}: items out of order — by priority, then oldest first")
        if [(g["p"], g["since"]) for g in groups] != sorted((g["p"], g["since"]) for g in groups):
            self.fail(f"{b} § Work: groups out of order — by priority, then oldest first")

    # Rule 9
    def check_verify(self, backlog: str) -> None:
        b, dates = self.backlog_name, []
        for n, line in self.section_lines(backlog, b, "Verify"):
            if line.startswith("- "):
                m = VERIFY.match(line)
                if not m:
                    self.fail(f"{b}:{n}: check must be '- **Subject** · YYYY-MM-DD · what to check — no test: <why>' "
                              "— if a test can do it, write the test instead")
                    continue
                dates.append(m.group(1))
            elif line.startswith("  ") and not line.startswith("    ") and line.strip():
                self.fail(f"{b}:{n}: one line per check — the detail belongs in its stage file")
        if dates != sorted(dates):
            self.fail(f"{b} § Verify: checks out of order — oldest first")

    # Rules 8 and 10
    def check_stages(self, plan: str, backlog: str) -> None:
        p, b = self.plan_name, self.backlog_name
        planned: set[str] = set()
        for cells, n in ranking.plan_rows(plan):
            planned.add(ranking.stage_id(cells[2]))
            if PROGRESS.search(cells[4]):
                self.fail(f"{p}:{n}: the Why column says how far the stage has got — say why it exists; "
                          "progress lives in the stage file's ## Steps")
        areas = set(self.cfg["areas"])
        exempt = set(self.cfg["docs"]["area_exempt"])
        for path in sorted((self.cfg.root / self.stages).glob("*.md")):
            name = f"{self.stages}/{path.name}"
            text = path.read_text(encoding="utf-8")
            if name not in exempt:
                area = re.search(r"^\*\*Area:\*\* (.+)$", text, re.M)
                if not area:
                    self.fail(f"{name} has no **Area:** line — loop.toml `areas` lists the vocabulary")
                else:
                    for a in (x.strip() for x in area.group(1).split(",")):
                        if a not in areas:
                            self.fail(f"{name} declares unknown Area '{a}' — loop.toml `areas`")
            steps = ranking.stage_steps(text)
            if steps is None:
                continue
            sid = re.search(r"^# (S[\d.]+):", text, re.M)
            status = re.search(r"^\*\*Status:\*\*(.*)$", text, re.M)
            status_text = status.group(1) if status else ""
            if not steps:
                self.fail(f"{name}: ## Steps has no '- [ ] N. Title' lines")
                continue
            if re.search(r"\bsteps? \d", status_text, re.I):
                self.fail(f"{name}: the Status line carries step progress — ## Steps is the record")
            shipped = status_text.strip().lower().startswith("shipped")
            if all(s.done for s in steps):
                if not shipped:
                    self.fail(f"{name}: every step is done — set **Status:** shipped, and drop its {p} row and Now item")
                if sid and sid.group(1) in planned:
                    self.fail(f"{p}: {sid.group(1)} is finished — remove its row")
            elif shipped:
                open_steps = ", ".join(str(s.number) for s in steps if not s.done)
                self.fail(f"{name}: Status says shipped but step {open_steps} is open")

        for text, n in ranking.now_items(backlog):
            for sid in dict.fromkeys(re.findall(r"\bS\d+(?:\.\d+)?\b", text)):
                path = self.stage_path(sid)
                stage = self.read_optional(path) if path else None
                steps = ranking.stage_steps(stage or "")
                if not steps:
                    continue
                number = ranking.named_step(text, sid)
                step = next((s for s in steps if s.number == number), None)
                if number is None:
                    self.fail(f"{b}:{n}: Now names {sid} without a step — say which: '{sid} step N'")
                elif step is None:
                    self.fail(f"{b}:{n}: {sid} has no step {number}")
                elif step.done:
                    self.fail(f"{b}:{n}: {sid} step {number} is done — take it out of Now")
                elif self.cfg["loop"]["placement"] and not re.search(r"^\*\*Placement:\*\* \S", stage or "", re.M):
                    self.fail(f"{path}: {sid} is in Now with no **Placement:** line — say where its code goes "
                              "before writing it")

    def run(self) -> list[str]:
        cfg, b = self.cfg, self.backlog_name
        texts = {}
        for key in ("backlog", "plan", "inbox"):
            text = self.read_optional(cfg.docname(key))
            if text is None:
                self.fail(f"{cfg.docname(key)} is missing — tier {cfg.tier} needs it (loop.toml `tier`)")
            texts[key] = text or ""
        backlog, plan, inbox = texts["backlog"], texts["plan"], texts["inbox"]
        if self.failures:
            return self.failures
        loop = cfg["loop"]

        self.check_work(backlog)
        self.check_verify(backlog)
        if not re.search(r"^Reviewed: 20\d\d-\d\d-\d\d$", backlog, re.M):
            self.fail(f"{b} has no 'Reviewed: YYYY-MM-DD' line — /review-backlog sets it")

        for n, row in self.table_rows(plan, self.plan_name, "Remaining work"):
            if not PRIORITY.match(row[0]):
                self.fail(f"{self.plan_name}:{n}: queued stage has no priority (first column, P0-3)")

        now_lines = [l for _, l in self.section_lines(backlog, b, "Now") if re.match(r"^\d+\.\s", l)]
        if len(now_lines) > loop["max_now"]:
            self.fail(f"{b} § Now has {len(now_lines)} items — {loop['max_now']} at most")
        itches = [l for l in now_lines if "**Itch**" in l]
        if len(itches) > 1:
            self.fail(f"{b} § Now has {len(itches)} Itch items — one at most; the rest follow priority")
        self.check_stages(plan, backlog)

        cap = cfg["docs"]["caps"].get(b, cfg["docs"]["cap_bytes"])
        ranked = ranking.candidates(plan, backlog, self.read_optional, stages_dir=self.stages,
                                    cap=cap, pressure=loop["backlog_pressure"])
        now = ranking.now_items(backlog)
        if ranked and now:
            top, (first, n) = ranked[0], now[0]
            if not ranking.names(first, top) and not ranking.override(first):
                self.fail(f"{b}:{n}: Now #1 isn't the ranked next ({top.priority} {top.key} — {top.title[:60]}); "
                          "make it that, or start the line '**Chosen** — <reason> —' or '**Itch** —'")

        for n, line in self.section_lines(inbox, self.inbox_name, "Open"):
            if line.startswith("- ~~") or (line.startswith("- ") and re.search(r"\*\*done\b", line)):
                self.fail(f"{self.inbox_name}:{n}: triaged or done but still here — delete it; "
                          f"move any remainder to {b}")

        today = date.today()
        for n, row in self.table_rows(backlog, b, "Blocked"):
            m = re.search(r"(20\d\d-\d\d-\d\d)", row[-1])
            if not m:
                self.fail(f"{b}:{n}: Blocked row has no 'Last checked' date")
            elif (today - date.fromisoformat(m.group(1))).days > loop["max_blocked_age_days"]:
                self.fail(f"{b}:{n}: Blocked row last checked {m.group(1)} — re-read it (unblock, split, or drop)")
        return self.failures


def check(cfg: Config) -> list[str]:
    if cfg.tier < 1:
        return []
    return Loop(cfg).run()
