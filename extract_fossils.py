#!/usr/bin/env python3
"""
Django Intent Fossil Extractor

Finds the earliest meaningful commits introducing key Django symbols
and extracts their original intent.

Usage:
    python extract_fossils.py /path/to/django/repo
"""

import sys
import ast
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
from datetime import datetime
import json

try:
    from git import Repo
except ImportError:
    print("Error: gitpython not installed")
    print("Install with: pip install gitpython")
    sys.exit(1)


@dataclass
class IntentFossil:
    """Represents the original intent of a symbol."""
    symbol_name: str
    symbol_type: str  # 'function', 'class', 'method'
    file_path: str
    first_commit_sha: str
    first_commit_date: str
    first_commit_message: str
    original_docstring: Optional[str]
    original_source: str
    lines_of_code: int

    def to_dict(self):
        return asdict(self)


class DjangoFossilExtractor:
    """Extracts intent fossils from Django's git history."""

    TARGET_PATHS = [
        "django/contrib/auth/__init__.py",
        "django/contrib/auth/models.py",
        "django/forms/forms.py",
        "django/forms/models.py",
        "django/db/models/manager.py",
    ]

    TARGET_SYMBOLS = {
        "django/contrib/auth/__init__.py": ["authenticate", "login", "logout"],
        "django/contrib/auth/models.py": ["User", "AbstractUser", "UserManager"],
        "django/forms/forms.py": ["Form", "BaseForm"],
        "django/forms/models.py": ["ModelForm"],
        "django/db/models/manager.py": ["Manager", "BaseManager"],
    }

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo = Repo(repo_path)
        self.fossils: List[IntentFossil] = []

    def extract_docstring(self, node) -> Optional[str]:
        """Extract docstring from an AST node."""
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node)
            return docstring
        return None

    def find_symbol_in_ast(self, source: str, symbol_name: str) -> Optional[tuple]:
        """Find a symbol in AST and return (node, source_lines)."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                if node.name == symbol_name:
                    # Extract just this symbol's source
                    lines = source.split('\n')
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if hasattr(
                        node, 'end_lineno') else start_line + 20
                    symbol_source = '\n'.join(lines[start_line:end_line])

                    symbol_type = 'class' if isinstance(
                        node, ast.ClassDef) else 'function'
                    docstring = self.extract_docstring(node)

                    return (symbol_type, docstring, symbol_source, end_line - start_line)
        return None

    def find_first_appearance(self, file_path: str, symbol_name: str) -> Optional[IntentFossil]:
        """Find the first commit where a symbol appears."""
        print(f"  Searching for {symbol_name} in {file_path}...")

        # Get all commits that touched this file, in reverse chronological order
        commits = list(self.repo.iter_commits(paths=file_path, reverse=True))

        if not commits:
            print(f"    No commits found for {file_path}")
            return None

        # Check commits from oldest to newest
        for commit in commits:
            try:
                # Get file content at this commit
                blob = commit.tree / file_path
                content = blob.data_stream.read().decode('utf-8', errors='ignore')

                # Try to find the symbol in this version
                result = self.find_symbol_in_ast(content, symbol_name)

                if result:
                    symbol_type, docstring, source, loc = result

                    # Skip if this looks like a spike commit
                    if self._is_spike_commit(commit):
                        print(
                            f"    Skipping spike commit: {commit.hexsha[:8]}")
                        continue

                    fossil = IntentFossil(
                        symbol_name=symbol_name,
                        symbol_type=symbol_type,
                        file_path=file_path,
                        first_commit_sha=commit.hexsha,
                        first_commit_date=datetime.fromtimestamp(
                            commit.committed_date).isoformat(),
                        first_commit_message=commit.message.strip(),
                        original_docstring=docstring,
                        original_source=source,
                        lines_of_code=loc
                    )

                    print(
                        f"    ✓ Found in commit {commit.hexsha[:8]} ({fossil.first_commit_date})")
                    return fossil

            except (KeyError, UnicodeDecodeError, AttributeError) as e:
                # File didn't exist in this commit or couldn't be read
                continue

        print(f"    ✗ Symbol not found in history")
        return None

    def _is_spike_commit(self, commit) -> bool:
        """Heuristic to detect spike/WIP commits."""
        message = commit.message.lower()
        spike_indicators = ['wip', 'spike', 'temp',
                            'temporary', 'experiment', 'test']

        if any(indicator in message for indicator in spike_indicators):
            return True

        # Check if commit touched too many files (likely a reorganization)
        if len(commit.stats.files) > 50:
            return True

        return False

    def extract_all_fossils(self):
        """Extract fossils for all target symbols."""
        print(f"Extracting intent fossils from {self.repo_path}\n")

        for file_path, symbols in self.TARGET_SYMBOLS.items():
            print(f"\nProcessing {file_path}:")
            for symbol in symbols:
                fossil = self.find_first_appearance(file_path, symbol)
                if fossil:
                    self.fossils.append(fossil)

        return self.fossils

    def save_fossils(self, output_path: str = "django_fossils.json"):
        """Save extracted fossils to JSON."""
        output = {
            "extraction_date": datetime.now().isoformat(),
            "repository": str(self.repo_path),
            "total_fossils": len(self.fossils),
            "fossils": [f.to_dict() for f in self.fossils]
        }

        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n✓ Saved {len(self.fossils)} fossils to {output_path}")

    def print_summary(self):
        """Print a human-readable summary."""
        print("\n" + "="*80)
        print("INTENT FOSSIL EXTRACTION SUMMARY")
        print("="*80)

        for fossil in self.fossils:
            print(f"\n{fossil.symbol_name} ({fossil.symbol_type})")
            print(f"  File: {fossil.file_path}")
            print(f"  First appeared: {fossil.first_commit_date}")
            print(f"  Commit: {fossil.first_commit_sha[:8]}")
            print(f"  Message: {fossil.first_commit_message[:60]}...")

            if fossil.original_docstring:
                doc = fossil.original_docstring.replace('\n', ' ')[:100]
                print(f"  Docstring: {doc}...")
            else:
                print(f"  Docstring: (none)")

            print(f"  Original LOC: {fossil.lines_of_code}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_fossils.py /path/to/django/repo")
        sys.exit(1)

    repo_path = sys.argv[1]

    if not Path(repo_path).exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        sys.exit(1)

    extractor = DjangoFossilExtractor(repo_path)
    extractor.extract_all_fossils()
    extractor.print_summary()
    extractor.save_fossils()

    print("\nNext steps:")
    print("1. Review django_fossils.json")
    print("2. For each fossil, examine the original source code")
    print("3. Begin manual audit to identify current semantic roles")


if __name__ == "__main__":
    main()
