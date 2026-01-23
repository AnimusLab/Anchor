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
        Walks backwards through git history to find the first meaningful commit
        where this symbol existed.
        """
        # FIX: Normalize Windows paths to Git paths (forward slashes)
        git_path = symbol.file_path.replace("\\", "/")
        
        print(f"DEBUG: Hunting for origin of {symbol.name} in {git_path}...")
        
        # 1. Get all commits that touched this file, oldest first
        try:
            # We assume the file history might contain renames, but we start simple
            commits = list(self.repo.iter_commits(paths=git_path))
            commits.reverse() # Oldest first
            
            if not commits:
                print(f"⚠️  Git returned 0 commits for {git_path}. Check path casing?")
                return None
                
        except Exception as e:
            print(f"❌ Git error for {git_path}: {e}")
            return None

        first_occurrence: Optional[Commit] = None
        
        # 2. Walk forward from the beginning of time
        for commit in commits:
            try:
                # FIX: Use the normalized git_path for tree lookups too
                blob = commit.tree / git_path
                file_content = blob.data_stream.read().decode('utf-8')
                
                # 3. Check if the symbol exists in this version
                if self._symbol_exists_in_source(symbol.name, symbol.type, file_content):
                    first_occurrence = commit
                    break
            except KeyError:
                # File didn't exist at this path in this commit (maybe before a rename)
                continue
            except Exception:
                continue

        if not first_occurrence:
            print(f"⚠️ Could not find origin for {symbol.name}")
            return None

        # 4. Extract the intent (docstring) from that first version
        # FIX: Pass git_path here too
        intent_desc = self._extract_docstring(symbol.name, first_occurrence, git_path)

        print(f"✅ FOUND ANCHOR: {first_occurrence.hexsha[:7]} ({datetime.fromtimestamp(first_occurrence.committed_date).date()})")

        return IntentAnchor(
            symbol=symbol.name,
            commit_sha=first_occurrence.hexsha,
            commit_date=datetime.fromtimestamp(first_occurrence.committed_date),
            intent_description=intent_desc or "No docstring found in original commit.",
            original_assumptions=[],
            source_code_snapshot="",
            confidence=AnchorConfidence.HIGH,
            confidence_reason="Inferred from first appearance in git history",
        )
    
    def _symbol_exists_in_source(self, name: str, sym_type: str, source: str) -> bool:
        """Prases the historical source code to see if the class/function is defined."""
        try:
            tree= ast.parse(source)
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
            source = bolb.data_stream.read().decode('utf-8')
            tree= ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name:
                    return ast.get_docstring(node) or ""
        except Exception:
            return ""
        return ""
