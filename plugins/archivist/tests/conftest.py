"""Keep every test's ledger writes (vault-write, the guard hook) out of the real
${XDG_STATE_HOME:-~/.local/state}/archivist/ledger.jsonl."""
import pytest


@pytest.fixture(autouse=True)
def _isolated_ledger(tmp_path_factory, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path_factory.mktemp("state")))
