#!/usr/bin/env python3
"""Compute rule counts from the repo and write docs/stats.json (single source of truth)."""
import json, pathlib, re
import tomllib

root = pathlib.Path(__file__).resolve().parent.parent / "anchor" / "governance"
ID = re.compile(r'^\s*-?\s*id:\s*"?([A-Za-z0-9_.-]+)', re.M)


def ids(d):
    return [i for f in (root / d).rglob("*.anchor") for i in ID.findall(f.read_text(encoding="utf-8-sig"))]


stats = {
    "version": tomllib.loads((root.parent.parent / "pyproject.toml").read_text())["project"]["version"],
    "rules": len(set(ids("domains"))),
    "framework_entries": len(ids("frameworks")),
    "government_entries": len(ids("government")),
}
out = root.parent.parent / "docs" / "stats.json"
out.write_text(json.dumps(stats, indent=2) + "\n")
print(stats)
