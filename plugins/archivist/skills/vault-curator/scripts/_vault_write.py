"""Write vault notes through bin/vault-write, the plugin's one guarded write path.

Scripts import this instead of writing files themselves, so every write gets the same
zone check, compare-and-swap, lint, git snapshot and verified atomic write as the CLI.
"""

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

_BIN = Path(__file__).resolve().parents[3] / "bin" / "vault-write"


def load(vault_path):
    """Return (vault_write module, config). The config's vault must be the one the script was given."""
    loader = SourceFileLoader("vault_write", str(_BIN))
    vw = importlib.util.module_from_spec(importlib.util.spec_from_loader("vault_write", loader))
    loader.exec_module(vw)
    cfg = vw.load_config()
    if Path(vault_path).expanduser().resolve() != cfg["root"]:
        raise vw.Refused(f"{vault_path} is not the configured vault {cfg['root']}")
    return vw, cfg


def write(vw, cfg, rel, text, original=None):
    """Guarded write of `text` to vault-relative `rel`. `original` is the bytes the script read
    (None for a new file), used as the compare-and-swap base. Returns vault-write's result dict,
    or {"ok": False, "path": rel, "refused": reason} instead of raising."""
    base = vw.sha(original) if original is not None else None
    try:
        return vw.write_note(cfg, rel, text, base=base)
    except vw.LintFailed as e:
        return {"ok": False, "path": rel, "refused": "lint: " + "; ".join(e.errors)}
    except vw.Refused as e:
        return {"ok": False, "path": rel, "refused": str(e)}
