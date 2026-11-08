"""loop.toml: the one place a repository says how its loop is shaped.

Every check reads this instead of carrying its own copy of a name, a cap
or a list. AudiobookOCD kept the Areas in three places and needed a check
just to keep them in step; here they live once, in `areas`.

The checks run from the plugin, so a plugin update changes them while a
repository's documents stay as they were. `schema` is the grammar version
the documents were written to; a check refuses a schema it doesn't know
rather than misreading the documents (lesson: checking-script versions
must travel with the documents they check).
"""

from __future__ import annotations

import copy
import os
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA = 1
FILE = "loop.toml"

DEFAULTS: dict = {
    "schema": SCHEMA,
    "kind": "none",
    "tier": 1,
    "main": "main",
    "gate": "",
    "areas": [],
    "docs": {
        "agents": "AGENTS.md",
        "loop": "LOOP.md",
        "backlog": "BACKLOG.md",
        "inbox": "INBOX.md",
        "plan": "PLAN.md",
        "decisions": "DECISIONS.md",
        "stages_dir": "stages",
        "backlog_dir": "backlog",
        "decisions_dir": "decisions",
        "cap_bytes": 20000,
        "caps": {"BACKLOG.md": 30000, "PLAN.md": 24000, "DECISIONS.md": 40000},
        "exclude": [],
        "stage_terminal": ["shipped", "superseded", "deferred", "won't fix", "reference"],
        "area_exempt": [],
    },
    "loop": {
        "max_now": 3,
        "max_blocked_age_days": 14,
        "backlog_pressure": 0.6,
        "placement": False,
    },
    "review_due": {
        "max_age_days": 7,
        "max_inbox": 5,
        "release_tags": "v[0-9]*",
    },
    "software": {
        "bugfix_prefix": "bugfix/",
        "tests": ["tests/"],
        "build": "",
        "test": "",
        "target_pattern": "",
        "review_lines": 150,
        "review_code": [],
        "review_risk_paths": [],
        "review_risk_content": [],
        "review_content_globs": [],
        "evals_cases": "evals/cases.json",
        "evals_overlay": [],
        "evals_prose": [],
        "evals_threshold": 60,
        "evals_allowed_tools": [],
        "evals_skip_arg": "",
        "command_prefixes": ["rtk"],
    },
}


class ConfigError(Exception):
    """loop.toml is missing, unreadable, or written to an unknown schema."""


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict) and key != "caps":
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def git_root(start: Path | None = None) -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=start or Path.cwd(), capture_output=True, text=True
    )
    if out.returncode != 0:
        raise ConfigError("not inside a git repository — devloop works on git repositories")
    return Path(out.stdout.strip())


def cache_dir(root: Path) -> Path:
    """Per-repository scratch outside the working tree: worktrees, reviews,
    eval results. Never under the repository, where a project's own build
    scratch goes (lesson: eval worktrees must not sit there)."""
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "devloop" / root.name


@dataclass
class Config:
    root: Path
    data: dict = field(default_factory=dict)

    def __getitem__(self, key: str):
        return self.data[key]

    def doc(self, name: str) -> Path:
        return self.root / self.data["docs"][name]

    def docname(self, name: str) -> str:
        return self.data["docs"][name]

    @property
    def software(self) -> bool:
        return self.data["kind"] == "software"

    @property
    def tier(self) -> int:
        return int(self.data["tier"])

    @property
    def cache(self) -> Path:
        return cache_dir(self.root)


def load(root: Path | None = None, path: Path | None = None) -> Config:
    """The repository's loop.toml over the defaults.

    `root` defaults to the enclosing git repository; `path` (or
    $DEVLOOP_CONFIG) points at a loop.toml kept outside the repository,
    which lets the checks read a repository without writing to it."""
    root = Path(root) if root else git_root()
    path = Path(path or os.environ.get("DEVLOOP_CONFIG") or root / FILE)
    if not path.exists():
        raise ConfigError(f"no {path.name} at {path.parent} — run /devloop-init")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"{path}: {error}") from error
    schema = data.get("schema", SCHEMA)
    if schema != SCHEMA:
        raise ConfigError(
            f"{path}: schema {schema}, and this devloop reads schema {SCHEMA} — "
            "update the plugin, or migrate the documents and raise `schema`"
        )
    merged = _merge(DEFAULTS, data)
    if merged["kind"] not in ("none", "software"):
        raise ConfigError(f"{path}: kind must be \"software\" or \"none\", not {merged['kind']!r}")
    return Config(root=root, data=merged)


def exists(root: Path | None = None) -> bool:
    try:
        root = Path(root) if root else git_root()
    except ConfigError:
        return False
    return bool(os.environ.get("DEVLOOP_CONFIG")) or (root / FILE).exists()
