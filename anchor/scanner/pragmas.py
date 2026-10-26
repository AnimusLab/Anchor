"""
anchor/scanner/pragmas.py

Correct `# anchor: ignore` semantics for the static scanner.

The native engine treats the pragma as "skip this line and the next one, for
every rule", whatever rule IDs are written after it. A reviewed
``os.system(...)  # anchor: ignore SEC-007`` therefore also hid an ``eval`` or
a hard-coded secret on the following line. The engine cannot be changed from
Python, so the check command does this instead:

1. files that contain a pragma are re-scanned from a scratch copy in which the
   pragma text is neutralised (same length, so line/column positions hold);
2. the findings are filtered here with the documented semantics:

   * a pragma that trails code on a line applies to that line only;
   * a comment-only pragma line applies to the next line only;
   * ``# anchor: ignore SEC-007 RI-08`` suppresses only those rule IDs;
   * a pragma without rule IDs (``# anchor: ignore -- reason``) suppresses
     every rule on its target line.
"""

from __future__ import annotations

import os
import re
import tempfile
from typing import Dict, FrozenSet, Iterable, Iterator, List, Optional, Set, Tuple

PRAGMA_RE = re.compile(r"anchor\s*:\s*ignore\b(?P<rest>[^\n]*)", re.IGNORECASE)
_NEUTRALISE_RE = re.compile(r"(anchor\s*:\s*)ignore", re.IGNORECASE)
_RULE_ID_RE = re.compile(r"\b[A-Z]{2,6}-[A-Z0-9]{1,4}\b")
_REASON_SPLIT_RE = re.compile(r"\s--(?:\s|$)")
_COMMENT_ONLY_RE = re.compile(r"^\s*(?:#|//|/\*|\*|--|<!--|;)")

# Legacy rule IDs that older pragmas (and `anchor heal`) use for the engine rules
# that now carry SEC-* IDs. A pragma naming the legacy ID still covers the new one.
LEGACY_ALIASES: Dict[str, FrozenSet[str]] = {
    "ANC-018": frozenset({"SEC-007"}),
    "RI-12": frozenset({"SEC-007"}),
    "ANC-030": frozenset({"SEC-010"}),
    "ANC-031": frozenset({"SEC-010"}),
}

SKIP_DIRS = {
    ".git", ".hg", ".anchor", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build", "site-packages",
}
MAX_FILE_BYTES = 2_000_000


def iter_text_files(root: str) -> Iterator[Tuple[str, str]]:
    """Yield ``(absolute_path, path_relative_to_root)`` for readable text files under ``root``."""
    root = os.path.abspath(root)
    if os.path.isfile(root):
        yield root, os.path.basename(root)
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            try:
                if os.path.islink(full) or os.path.getsize(full) > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield full, os.path.relpath(full, root)


def read_text(path: str) -> Optional[str]:
    try:
        with open(path, "rb") as fh:
            data = fh.read(MAX_FILE_BYTES + 1)
    except OSError:
        return None
    if b"\x00" in data[:4096]:  # binary
        return None
    return data.decode("utf-8", errors="replace")


def parse_pragma(line: str) -> Optional[Tuple[FrozenSet[str], bool]]:
    """``(rule_ids, comment_only)`` if the line carries a pragma, else None."""
    match = PRAGMA_RE.search(line)
    if not match:
        return None
    ids_part = _REASON_SPLIT_RE.split(match.group("rest"), maxsplit=1)[0]
    ids = frozenset(_RULE_ID_RE.findall(ids_part.upper()))
    return ids, bool(_COMMENT_ONLY_RE.match(line))


def suppressions(lines: List[str]) -> Dict[int, List[FrozenSet[str]]]:
    """Map 1-based target line number -> list of rule-id sets (empty set = every rule)."""
    out: Dict[int, List[FrozenSet[str]]] = {}
    for idx, line in enumerate(lines, start=1):
        parsed = parse_pragma(line)
        if parsed is None:
            continue
        ids, comment_only = parsed
        out.setdefault(idx + 1 if comment_only else idx, []).append(ids)
    return out


def _expand(ids: Iterable[str]) -> Set[str]:
    out: Set[str] = set()
    for rule_id in ids:
        out.add(rule_id)
        out.update(LEGACY_ALIASES.get(rule_id, ()))
    return out


def _rules_of(violation: dict) -> Set[str]:
    return {r.strip().upper() for r in str(violation.get("aggregated_rule_ids", "")).split(",") if r.strip()}


def filter_violations(violations: Iterable[dict]) -> List[dict]:
    """Drop findings covered by a correctly scoped pragma."""
    cache: Dict[str, Dict[int, List[FrozenSet[str]]]] = {}
    kept: List[dict] = []
    for v in violations:
        path = v.get("file", "")
        if path not in cache:
            text = read_text(path)
            cache[path] = suppressions(text.splitlines()) if text and PRAGMA_RE.search(text) else {}
        sets = cache[path].get(int(v.get("line", 0) or 0), [])
        rules = _rules_of(v)
        if any((not ids) or (_expand(ids) & rules) for ids in sets):
            continue
        kept.append(v)
    return kept


def _has_pragma(path: str) -> bool:
    text = read_text(path)
    return bool(text and PRAGMA_RE.search(text))


def legacy_pragmas_enabled() -> bool:
    """ANCHOR_LEGACY_PRAGMAS=1 keeps the native engine's pragma behaviour (line + next line, any rule)."""
    return os.environ.get("ANCHOR_LEGACY_PRAGMAS", "").strip().lower() in {"1", "true", "on", "yes"}


def apply_pragmas(engine, target: str, violations: List[dict]) -> List[dict]:
    """Re-scan pragma-bearing files without the engine's pragma handling, then filter correctly."""
    if legacy_pragmas_enabled():
        return violations
    target = os.path.abspath(target)
    pragma_files = {full: rel for full, rel in iter_text_files(target) if _has_pragma(full)}
    if not pragma_files:
        return violations

    real = os.path.realpath
    originals = {real(p): p for p in pragma_files}
    rescanned: List[dict] = []

    with tempfile.TemporaryDirectory(prefix="anchor-pragma-") as scratch:
        mirror_to_original: Dict[str, str] = {}
        for full, rel in pragma_files.items():
            text = read_text(full) or ""
            dest = os.path.join(scratch, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8", newline="") as fh:
                fh.write(_NEUTRALISE_RE.sub(lambda m: m.group(1) + "ignorx", text))
            mirror_to_original[real(dest)] = full

        detail = engine.scan_directory_detailed(scratch)
        source_lines: Dict[str, List[str]] = {}
        for v in detail.get("violations", []):
            original = mirror_to_original.get(real(v.get("file", "")))
            if original is None:
                continue
            if original not in source_lines:
                source_lines[original] = (read_text(original) or "").splitlines()
            lines = source_lines[original]
            line_no = int(v.get("line", 0) or 0)
            mapped = dict(v)
            mapped["file"] = original
            if 1 <= line_no <= len(lines):
                mapped["line_content"] = lines[line_no - 1].strip()
            rescanned.append(mapped)

    untouched = [v for v in violations if real(v.get("file", "")) not in originals]
    return untouched + filter_violations(rescanned)
