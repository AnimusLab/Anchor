import ast
import os
from typing import Iterator, Optional
from anchor.core.models import CodeSymbol


class SymbolVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.symbols: list[CodeSymbol] = []
        self.current_class: Optional[str] = None

    def visit_ClassDef(self, node):
        # Register the class
        self.symbols.append(CodeSymbol(
            name=node.name,
            type='class',
            file_path=self.file_path,
            line_number=node.lineno,
            parent=None
        ))

        # Enter the class context to find methods
        previous_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = previous_class

    def visit_FunctionDef(self, node):
        # Filter out private helpers (starts with _) but keep __init__
        if node.name.startswith("_") and node.name != "__init__":
            return

        symbol_type = 'method' if self.current_class else 'function'

        self.symbols.append(CodeSymbol(
            name=node.name,
            type=symbol_type,
            file_path=self.file_path,
            line_number=node.lineno,
            parent=self.current_class
        ))
        # We generally don't want nested functions inside functions, so we stop recursing here
        # unless you specifically need them.


def walk_repo(root_path: str) -> Iterator[CodeSymbol]:
    """Recursively parses all Python files in the directory."""
    print(f"DEBUG: Walking {root_path}")

    for root, dirs, files in os.walk(root_path):
        # Optimization: Skip standard ignore folders
        dirs[:] = [d for d in dirs if d not in {
            '.git', '__pycache__', 'venv', 'env', 'node_modules', 'migrations'}]

        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                # Store relative path for cleaner display
                rel_path = os.path.relpath(full_path, root_path)

                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())

                    visitor = SymbolVisitor(rel_path)
                    visitor.visit(tree)

                    for sym in visitor.symbols:
                        yield sym

                except Exception:
                    # If a file has syntax errors or encoding issues, skip it
                    continue
