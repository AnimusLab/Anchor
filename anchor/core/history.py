import ast
from typing import Optional, List
from datetime import datetime
from git import Repo, Commit
from anchor.core.models import IntentAnchor, CodeSymbol, AnchorConfidence


def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        replacements = {
            "⚠️": "[WARNING]",
            "❌": "[ERROR]",
            "✅": "[SUCCESS]",
            "⚓": "[ANCHOR]",
        }
        for k, v in replacements.items():
            msg = msg.replace(k, v)
        print(msg.encode('ascii', errors='replace').decode('ascii'))


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
                safe_print(f"❌ Git error for {git_path}: Dubious ownership detected.")
                safe_print(f"   To fix this, run:")
                safe_print(f"   git config --global --add safe.directory {self.repo.working_dir}")
            else:
                safe_print(f"❌ Git error for {git_path}: {error_msg}")
            return None

        first_occurrence: Optional[Commit] = None
        final_docstring = ""

        # 1. Find Creation
        for i, commit in enumerate(commits):
            try:
                blob = commit.tree / git_path
                file_content = blob.data_stream.read().decode('utf-8')

                # Check if symbol exists in this version
                if self._symbol_exists_in_source(symbol.name, symbol.type, file_content, git_path):
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
            safe_print(f"⚠️ Could not find origin for {symbol.name}")
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

    def _symbol_exists_in_source(self, name: str, sym_type: str, source: str, file_path: str) -> bool:
        """Parses the historical source code using the correct adapter to see if the class/function is defined."""
        from anchor.core.registry import LanguageRegistry
        adapter = LanguageRegistry.get_adapter_for_file(file_path)
        if not adapter:
            return False
        try:
            source_bytes = source.encode('utf-8', errors='ignore') if isinstance(source, str) else source
            symbols = adapter.extract_symbols(source_bytes)
            for sym in symbols:
                if sym['name'] == name and sym['type'] == sym_type:
                    return True
        except Exception:
            return False
        return False

    def _extract_docstring(self, name: str, commit: Commit, file_path: str) -> str:
        """Extracts the docstring or preceding comments for a symbol in a historical commit."""
        from anchor.core.registry import LanguageRegistry
        adapter = LanguageRegistry.get_adapter_for_file(file_path)
        if not adapter:
            return ""
            
        try:
            blob = commit.tree / file_path.replace("\\", "/")
            source = blob.data_stream.read().decode('utf-8', errors='ignore')
            
            # 1. If Python, try standard AST docstring extraction first
            if adapter.language_id == 'python':
                try:
                    import ast as py_ast
                    tree = py_ast.parse(source)
                    for node in py_ast.walk(tree):
                        if isinstance(node, (py_ast.FunctionDef, py_ast.ClassDef)) and node.name == name:
                            doc = py_ast.get_docstring(node)
                            if doc:
                                return doc
                except Exception:
                    pass
            
            # 2. Find the symbol's start line in this historical version using the adapter
            source_bytes = source.encode('utf-8', errors='ignore')
            symbols = adapter.extract_symbols(source_bytes)
            start_line = None
            for sym in symbols:
                if sym['name'] == name:
                    start_line = sym['line_number']
                    break
                    
            if start_line is not None:
                return extract_comments_above(source, start_line, adapter.language_id)
        except Exception:
            return ""
        return ""


def extract_comments_above(source: str, start_line: int, lang_id: str) -> str:
    lines = source.splitlines()
    idx = start_line - 2
    comment_lines = []
    
    while idx >= 0:
        line = lines[idx].strip()
        if not line:
            break
        
        is_comment = False
        comment_text = ""
        if lang_id == 'python' and line.startswith('#'):
            is_comment = True
            comment_text = line.lstrip('#').strip()
        elif lang_id in ('go', 'typescript', 'java', 'rust'):
            if line.startswith('//'):
                is_comment = True
                comment_text = line.lstrip('/').strip()
            elif line.startswith('/*'):
                is_comment = True
                comment_text = line.lstrip('/*').rstrip('*/').strip()
            elif line.startswith('*'):
                is_comment = True
                comment_text = line.lstrip('*').strip()
            elif line.endswith('*/'):
                is_comment = True
                comment_text = line.rstrip('*/').strip()
        
        if is_comment:
            comment_lines.append(comment_text)
            idx -= 1
        else:
            break
            
    comment_lines.reverse()
    return "\n".join(comment_lines)
