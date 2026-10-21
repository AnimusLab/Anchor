import tomllib
from pathlib import Path

import anchor

ROOT = Path(__file__).resolve().parents[2]


def _v(name, *keys):
    d = tomllib.loads((ROOT / name).read_text(encoding="utf-8"))
    for k in keys:
        d = d[k]
    return d


def test_python_and_cargo_versions_match():
    assert _v("pyproject.toml", "project", "version") == _v("Cargo.toml", "package", "version") == anchor.__version__


def test_engine_reports_package_version():
    from anchor_core_rs import AnchorEngine
    assert AnchorEngine().version() == anchor.__version__
