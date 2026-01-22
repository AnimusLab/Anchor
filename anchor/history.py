"""Git history extraction and analysis."""

import ast
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from git import Repo
from .symbols import IntentAnchor


class HistoryAnalyzer:
    """Extract intent anchors and evolution metrics from git history."""

    def __init__(self, repo_path: str):
        self.repo = Repo(repo_path)
        self.repo_path = Path(repo_path)

    def find_intent_anchor(
        self,
        file_path: str,
        symbol_name: str
    ) -> Optional[IntentAnchor]:
        """
        Find the first meaningful commit introducing a symbol.

        Skips spike commits:
        - More than 50 files changed
        - Message contains: WIP, spike, temp, test, experiment
        """
        # Get all commits
        commits = list(self.repo.iter_commits(paths=file_path))

        if not commits:
            return None

        # Reverse to get oldest first
        commits.reverse()

        for commit in commits:
            # Skip spike commits
            if self._is_spike_commit(commit):
                continue

            try:
                # Get file content at this commit
                blob = commit.tree / file_path
                content = blob.data_stream.read().decode('utf-8', errors='ignore')

                # Check if symbol exists in this version
                result = self._find_symbol_in_source(content, symbol_name)

                if result:
                    symbol_type, docstring, source, loc = result

                    return IntentAnchor(
                        commit_sha=commit.hexsha,
                        commit_date=datetime.fromtimestamp(
                            commit.committed_date),
                        commit_message=commit.message.strip(),
                        docstring=docstring,
                        source=source,
                        lines_of_code=loc,
                        confidence=self._assess_anchor_confidence(
                            docstring, source, commit
                        )
                    )

            except (KeyError, UnicodeDecodeError, AttributeError):
                continue

        return None

    def count_meaningful_changes(
        self,
        file_path: str,
        symbol_name: str,
        years: int = 5
    ) -> int:
        """
        Count non-trivial changes to a symbol in the last N years.

        Excludes:
        - Documentation-only changes
        - Security patches (commit message contains 'security', 'CVE')
        - Formatting changes (whitespace only)
        """
        cutoff_date = datetime.now() - timedelta(days=years * 365)
        commits = list(self.repo.iter_commits(paths=file_path))

        meaningful_count = 0

        for commit in commits:
            commit_date = datetime.fromtimestamp(commit.committed_date)

            # Skip commits before cutoff
            if commit_date < cutoff_date:
                continue

            # Skip non-meaningful changes
            if self._is_documentation_only(commit):
                continue
            if self._is_security_patch(commit):
                continue
            if self._is_formatting_only(commit):
                continue

            # Count all meaningful commits to the file
            meaningful_count += 1

        return meaningful_count

    def get_history_depth(self, file_path: str) -> int:
        """Get total number of commits for a file."""
        return len(list(self.repo.iter_commits(paths=file_path)))

    def _is_spike_commit(self, commit) -> bool:
        """Detect spike/WIP commits."""
        message = commit.message.lower()
        spike_indicators = ['wip', 'spike', 'temp',
                            'temporary', 'experiment', 'test']

        if any(indicator in message for indicator in spike_indicators):
            return True

        # Check if commit touched too many files
        if len(commit.stats.files) > 50:
            return True

        return False

    def _is_documentation_only(self, commit) -> bool:
        """Check if commit only changes documentation."""
        message = commit.message.lower()
        doc_indicators = ['doc', 'comment', 'docstring', 'readme', 'changelog']

        return any(indicator in message for indicator in doc_indicators)

    def _is_security_patch(self, commit) -> bool:
        """Check if commit is a security patch."""
        message = commit.message.lower()
        return 'security' in message or 'cve' in message or 'vulnerability' in message

    def _is_formatting_only(self, commit) -> bool:
        """Check if commit only changes formatting."""
        message = commit.message.lower()
        format_indicators = ['format', 'whitespace',
                             'indent', 'style', 'black', 'isort']

        return any(indicator in message for indicator in format_indicators)

    def _find_symbol_in_source(self, source: str, symbol_name: str):
        """Find a symbol in source code using AST."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                if node.name == symbol_name:
                    # Extract source
                    lines = source.split('\n')
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if hasattr(
                        node, 'end_lineno') else start_line + 20
                    symbol_source = '\n'.join(lines[start_line:end_line])

                    symbol_type = 'class' if isinstance(
                        node, ast.ClassDef) else 'function'
                    docstring = ast.get_docstring(node)
                    loc = end_line - start_line

                    return (symbol_type, docstring, symbol_source, loc)

        return None

    def _assess_anchor_confidence(
        self,
        docstring: Optional[str],
        source: str,
        commit
    ) -> str:
        """Assess confidence in intent anchor."""
        score = 0

        # Docstring quality
        if docstring and len(docstring) > 50:
            score += 2
        elif docstring:
            score += 1

        # Commit message quality
        if len(commit.message.strip()) > 30:
            score += 1

        # Source complexity (not a stub)
        if len(source.split('\n')) > 10:
            score += 1

        if score >= 4:
            return "high"
        elif score >= 2:
            return "medium"
        else:
            return "low"
