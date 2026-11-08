"""One answer to "what next", shared by the loop check and `devloop rank`.

The candidates are PLAN's unblocked stages and BACKLOG § Work's groups,
ranked by priority. Within a priority, stages come first in PLAN's order
(it encodes dependencies), then groups, oldest first. The top candidate is
the suggestion. BACKLOG § Now's first item must name it, or say why not:
`**Itch** —` or `**Chosen** — <reason> —` (a single next suggestion,
unless blockers, priority or plain choice reorganize the plan).

**Under pressure the backlog comes first.** With a stage always queued,
stages-first meant bug groups moved only when someone overrode the
ranking, and BACKLOG kept meeting its size cap. So when BACKLOG is at
`pressure` of its cap, groups holding bugs rank ahead of stages at the same
priority — most bugs first, then most items, since the improvements beside
a bug share its context — and groups with no bugs follow the stages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Step:
    """One line of a stage file's `## Steps` checklist — the only record of
    how far a stage has got, so a finished stage isn't left around causing
    confusion."""

    number: int
    title: str
    done: bool
    note: str  # after " — ": where it shipped, for a done step


STEP = re.compile(r"^- \[( |x)\] (\d+)\. (.+?)(?: — (.+))?$")


def stage_steps(stage: str) -> list[Step] | None:
    """A stage file's `## Steps`, or None when it has no such section."""
    m = re.search(r"^## Steps\s*$(.*?)(?=^## |\Z)", stage, re.M | re.S)
    if not m:
        return None
    steps = []
    for line in m.group(1).splitlines():
        s = STEP.match(line.strip())
        if s:
            steps.append(Step(int(s.group(2)), s.group(3), s.group(1) == "x", s.group(4) or ""))
    return steps


def stage_file(cell: str, stages_dir: str = "stages") -> str | None:
    """The stages/… path a PLAN row's Stage cell links to."""
    m = re.search(rf"\(({re.escape(stages_dir)}/[^)]+)\)", cell)
    return m.group(1) if m else None


def next_step(steps: list[Step] | None) -> Step | None:
    return next((s for s in steps or [] if not s.done), None)


@dataclass(frozen=True)
class Candidate:
    """A stage or a Work group that could be next."""

    priority: str  # "P0"–"P3"
    kind: str  # "stage" or "group"
    key: str  # "S72", or the group's name — what Now #1 must mention
    title: str
    order: tuple  # tie-break within a priority
    file: str | None = None  # a stage's stages/… file
    step: Step | None = None  # a stage's first open step
    bugs: int = 0  # a group's bugs
    items: int = 0  # a group's items, bugs and improvements

    @property
    def rank(self) -> tuple:
        return (self.priority, 0 if self.kind == "stage" else 1, self.order)

    @property
    def pressured_rank(self) -> tuple:
        """The rank when the backlog is near its cap: groups with bugs first,
        most bugs then most items, then stages, then groups without bugs."""
        if self.kind == "stage":
            return (self.priority, 1, (), self.order)
        if self.bugs:
            return (self.priority, 0, (-self.bugs, -self.items), self.order)
        return (self.priority, 2, (), self.order)


def under_pressure(backlog: str, cap: int, pressure: float) -> bool:
    """Whether BACKLOG is near enough its cap that its bugs come first."""
    return cap > 0 and len(backlog.encode("utf-8")) >= pressure * cap


def section(text: str, heading: str) -> tuple[str, int]:
    """The body of `## heading` and the 1-based line it starts on."""
    m = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |^---\s*$|\Z)", text, re.M | re.S)
    if not m:
        return "", 1
    return m.group(1), text[: m.start(1)].count("\n") + 1


def plan_rows(plan: str) -> list[tuple[list[str], int]]:
    """PLAN § Remaining work's stage rows (P, Area, Stage, Title, Why), with line numbers."""
    body, start = section(plan, "Remaining work")
    rows = []
    for n, line in enumerate(body.splitlines(), start):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 5 and re.fullmatch(r"P[0-3]", cells[0]):
            rows.append((cells, n))
    return rows


def stage_id(cell: str) -> str:
    return re.sub(r"\[([^\]]+)\].*", r"\1", cell)


def plan_stages(plan: str, read=None, stages_dir: str = "stages") -> list[Candidate]:
    """PLAN's rows that aren't **Blocked**, in file order, each with its
    first open step when its stage file keeps a `## Steps` checklist.
    `read(path) -> str | None` supplies the stage file."""
    stages = []
    for index, (cells, _) in enumerate(plan_rows(plan)):
        if "**Blocked**" in cells[4]:
            continue
        path = stage_file(cells[2], stages_dir)
        text = read(path) if read and path else None
        step = next_step(stage_steps(text)) if text else None
        stages.append(Candidate(cells[0], "stage", stage_id(cells[2]), cells[3], (index,), path, step))
    return stages


GROUP = re.compile(r"^### (.+) — (P[0-3]) · since (\S+)$")
ITEM = re.compile(r"^- \*\*(P[0-3])\*\* (bug|improvement) `([^`]+)` · (\S+) · (.*)$")


def work_groups(backlog: str) -> list[dict]:
    """BACKLOG § Work's groups in file order, each with its items and line numbers."""
    body, start = section(backlog, "Work")
    groups: list[dict] = []
    for n, line in enumerate(body.splitlines(), start):
        g = GROUP.match(line)
        if g:
            groups.append({"name": g.group(1), "p": g.group(2), "since": g.group(3), "line": n, "items": []})
            continue
        i = ITEM.match(line)
        if i and groups:
            groups[-1]["items"].append({
                "p": i.group(1), "kind": i.group(2), "areas": [a.strip() for a in i.group(3).split(",")],
                "date": i.group(4), "text": i.group(5), "line": n,
            })
    return groups


def candidates(plan: str, backlog: str, read=None, *, stages_dir: str = "stages",
               cap: int = 0, pressure: float = 0.6) -> list[Candidate]:
    groups = [
        Candidate(
            g["p"], "group", g["name"], g["name"], (g["since"],),
            bugs=sum(i["kind"] == "bug" for i in g["items"]), items=len(g["items"]),
        )
        for g in work_groups(backlog)
    ]
    pressed = under_pressure(backlog, cap, pressure)
    key = (lambda c: c.pressured_rank) if pressed else (lambda c: c.rank)
    return sorted(plan_stages(plan, read, stages_dir) + groups, key=key)


def named_step(text: str, sid: str) -> int | None:
    """The step number a Now line gives for a stage: "S72 step 2" → 2."""
    m = re.search(rf"\b{re.escape(sid)} step (\d+)\b", text)
    return int(m.group(1)) if m else None


def now_items(backlog: str) -> list[tuple[str, int]]:
    """BACKLOG § Now's numbered items, continuation lines folded in, with line numbers."""
    body, start = section(backlog, "Now")
    items: list[tuple[str, int]] = []
    for n, line in enumerate(body.splitlines(), start):
        m = re.match(r"^\d+\.\s+(.*)", line)
        if m:
            items.append((m.group(1).strip(), n))
        elif line.startswith("   ") and items:
            items[-1] = (items[-1][0] + " " + line.strip(), items[-1][1])
    return items


def names(text: str, candidate: Candidate) -> bool:
    """Whether a Now line is about this candidate. A group is named by its
    bold title: a bare substring let one group's words mark another group
    as being in Now."""
    if candidate.kind == "stage":
        return re.search(rf"\b{re.escape(candidate.key)}\b", text) is not None
    return f"**{candidate.key}**" in text


def override(text: str) -> str | None:
    """The reason Now #1 departs from the ranking, if it declares one."""
    if text.startswith("**Itch**"):
        return "itch"
    m = re.match(r"\*\*Chosen\*\* — (.+?)(?: — |$)", text)
    return m.group(1) if m else None
