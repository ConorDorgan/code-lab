import gzip
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
FIX = Path(__file__).parent / "fixtures"


def read_fixture(name: str) -> str:
    p = FIX / name
    if name.endswith(".gz"):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            return f.read()
    return p.read_text(encoding="utf-8")


@pytest.fixture
def fixture_text():
    return read_fixture


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    """Keep tests from touching the real cache, output folder or BLOCKERS.md."""
    from vintedtool import config
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path / "output")
    monkeypatch.setattr(config, "BLOCKERS_FILE", tmp_path / "BLOCKERS.md")
