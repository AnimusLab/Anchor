import ast
from typing import Optional, List
from datetime import datetime
from git import Repo, Commit
from anchor.core.models import IntentAnchor, CodeSymbol, AnchorConfidence


class HistoryEngine:
    def __init__(self, repo_path: str):
        self.repo = Repo(repo_path)

    def find_anchor(self, symbol: CodeSymbol) -> Optional[IntentAnchor]:
        """
        Finds the first meaningful commit. If the first commit has no docstring,
        it scans forward (up to 10 commits) to find when the intent was documented.
        """
        # Normalize Windows paths to Git paths
        git_path = symbol.file_path.replace("\\", "/")

        # print(f"DEBUG: Hunting for origin of {symbol.name} in {git_path}...")

        try:
            commits = list(self.repo.iter_commits(paths=git_path))
            commits.reverse()  # Oldest first
        except Exception as e:
            error_msg = str(e)
            if "dubious ownership" in error_msg:
                print(f"❌ Git error for {git_path}: Dubious ownership detected.")
                print(f"   To fix this, run:")
                print(f"   git config --global --add safe.directory {self.repo.working_dir}")
            else:
                print(f"❌ Git error for {git_path}: {error_msg}")
            return None

        first_occurrence: Optional[Commit] = None
        final_docstring = ""

        # 1. Find Creation
        for i, commit in enumerate(commits):
            try:
                blob = commit.tree / git_path
                file_content = blob.data_stream.read().decode('utf-8')

                # Check if symbol exists in this version
                if self._symbol_exists_in_source(symbol.name, symbol.type, file_content):
                    if not first_occurrence:
                        first_occurrence = commit

                    # 2. Scan Forward for Docstring (Max 10 commits deep)
                    doc = self._extract_docstring(
                        symbol.name, commit, git_path)
                    if doc:
                        final_docstring = doc
                        # Found a documented intent! We stop here.
                        break

                    # Stop scanning if we drift too far from creation without finding docs
                    if first_occurrence and (i - commits.index(first_occurrence) > 10):
                        break
            except KeyError:
                # File didn't exist at this path in this commit
                continue
            except Exception:
                continue

        if not first_occurrence:
            print(f"⚠️ Could not find origin for {symbol.name}")
            return None

        # print(f"✅ FOUND ANCHOR: {first_occurrence.hexsha[:7]} ({datetime.fromtimestamp(first_occurrence.committed_date).date()})")

        return IntentAnchor(
            symbol=symbol.name,
            commit_sha=first_occurrence.hexsha,
            commit_date=datetime.fromtimestamp(
                first_occurrence.committed_date),
            intent_description=final_docstring or "No docstring found in early history.",
            original_assumptions=[],
            source_code_snapshot="",
            confidence=AnchorConfidence.HIGH if final_docstring else AnchorConfidence.LOW,
            confidence_reason="Inferred from first documented appearance in git history"
        )

    def _symbol_exists_in_source(self, name: str, sym_type: str, source: str) -> bool:
        """Parses the historical source code to see if the class/function is defined."""
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and sym_type == 'class' and node.name == name:
                    return True
                if isinstance(node, ast.FunctionDef) and sym_type in ('function', 'method') and node.name == name:
                    return True
        except SyntaxError:
            return False
        return False

    def _extract_docstring(self, name: str, commit: Commit, file_path: str) -> str:
        """Extracts the docstring from the AST of the historical commit."""
        try:
            blob = commit.tree / file_path
            source = blob.data_stream.read().decode('utf-8')
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name:
                    return ast.get_docstring(node) or ""
        except Exception:
            return ""
        return ""
